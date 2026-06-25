"""
combat.py
Moteur de combat temps-réel simplifié pour les attaques.

Fonctionnement :
  1. CombatSession est créée avec attaquant et défenseur.
  2. Le joueur déploie ses unités (deploy_troop).
  3. update(dt) fait avancer le temps : troupes se déplacent,
     défenses ripostent, bâtiments prennent des dégâts.
  4. is_over() détecte la fin (QG détruit ou timer expiré).
  5. finalize() calcule les étoiles et produit un AttackRecord.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional

from core.constants import ATTACK_DURATION
from core.village import Village, AttackRecord
from entities.troops import TroopInstance, TroopType
from entities.buildings import Building
from entities.defenses import Defense


# ── Projectile ────────────────────────────────────────────────────────────────

@dataclass
class Projectile:
    """
    Un obus en vol entre une défense et une troupe.
    Voyage en ligne droite vers la position de la cible au moment du tir.
    Applique les dégâts à l'arrivée.
    """
    col:      float         # position courante (cellules)
    row:      float
    dest_col: float         # destination fixe
    dest_row: float
    damage:   int
    splash:   float         # rayon de zone (0 = direct)
    speed:    float = 9.0   # cellules/seconde
    def_id:   str   = ""   # building_id de la défense source (pour la couleur)


# ── Résultat intermédiaire ────────────────────────────────────────────────────

@dataclass
class CombatResult:
    stars_attacker: int
    stars_defender: int
    destruction_pct: float


# ── Session de combat ─────────────────────────────────────────────────────────

class CombatSession:
    """
    Gère une attaque complète.

    Paramètres :
        attacker_village  – village de l'attaquant (pour les troupes disponibles)
        defender_village  – village cible (bâtiments, défenses)
        attacker_key      – empire_key de l'attaquant
    """

    def __init__(
        self,
        attacker_village: Village,
        defender_village: Village,
        attacker_key: str,
        day: int,
    ) -> None:
        self.attacker_village = attacker_village
        self.defender_village = defender_village
        self.attacker_key     = attacker_key
        self.defender_key     = defender_village.empire_key
        self.day              = day

        # Copie défensive des bâtiments pour ne pas altérer l'original pendant le combat
        # Les PV sont réinitialisés après le combat dans finalize()
        self._def_buildings: list[Building]  = list(defender_village.buildings)
        self._def_defenses:  list[Defense]   = list(defender_village.defenses)

        # Réinitialise les cooldowns des défenses
        for d in self._def_defenses:
            d.reset_cooldown()
            d.repair()
        for b in self._def_buildings:
            b.repair()

        # Total HP pour le calcul de destruction
        self._total_hp: int = sum(b.max_hp for b in self._all_defender_buildings())

        # Armée déployée
        self.troops:      list[TroopInstance] = []
        # Projectiles en vol
        self.projectiles: list[Projectile]    = []

        # Timer (secondes)
        self.time_left:  float = float(ATTACK_DURATION)
        self._finished:  bool  = False

        # Ressources de l'armée disponibles (copie)
        self._army_pool: dict[str, int] = dict(attacker_village.army)

    # ── Déploiement ───────────────────────────────────────────────────────────

    def deploy_troop(self, troop_id: str, col: float, row: float) -> bool:
        """
        Déploie une unité de troop_id à la position (col, row).
        Retourne False si le pool est vide ou le type inconnu.
        """
        if self._army_pool.get(troop_id, 0) <= 0:
            return False
        tt = self.attacker_village.get_troop_type(troop_id)
        if tt is None:
            return False
        self.troops.append(TroopInstance(troop_type=tt, col=col, row=row))
        self._army_pool[troop_id] -= 1
        return True

    # ── Boucle de jeu ─────────────────────────────────────────────────────────

    # Nombre max de projectiles simultanés (perf)
    _MAX_PROJECTILES: int = 40

    def update(self, dt: float) -> None:
        """Avance la simulation d'un pas de temps dt (secondes)."""
        if self._finished:
            return

        self.time_left -= dt
        if self.time_left <= 0:
            self._finished = True
            return

        # ── Pré-calcul une seule fois par frame ──────────────────────────────
        alive_troops   = [t for t in self.troops if t.is_alive]
        alive_buildings = [b for b in self._def_buildings  if not b.is_destroyed]
        alive_defenses  = [d for d in self._def_defenses   if not d.is_destroyed]
        all_alive       = alive_buildings + alive_defenses   # liste combinée réutilisée

        # ── Mise à jour de chaque troupe ─────────────────────────────────────
        for troop in alive_troops:
            if not all_alive:
                break
            target = min(all_alive,
                         key=lambda b, t=troop: math.hypot(t.col - b.col, t.row - b.row))

            target_col = float(target.col)
            target_row = float(target.row)
            dist = troop.distance_to(target_col, target_row)

            if dist > troop.troop_type.range_cells:
                troop.move_towards(target_col, target_row, dt)
            else:
                if troop.can_attack(dt):
                    dmg    = troop.troop_type.damage
                    splash = troop.troop_type.splash_radius
                    if splash > 0:
                        self._apply_splash_damage(target_col, target_row, splash, dmg, all_alive)
                    else:
                        target.take_damage(dmg)

        # ── Tirs des défenses → crée des projectiles ───────────────────────
        if len(self.projectiles) < self._MAX_PROJECTILES:
            for defense in alive_defenses:
                if len(self.projectiles) >= self._MAX_PROJECTILES:
                    break
                if not alive_troops:
                    break
                # Troupe la plus proche dans la portée
                best = None
                best_d = float("inf")
                for t in alive_troops:
                    d = math.hypot(t.col - defense.col, t.row - defense.row)
                    if d <= defense.range_cells and d < best_d:
                        best_d, best = d, t
                if best is None:
                    continue
                if defense.can_shoot(dt):
                    self.projectiles.append(Projectile(
                        col      = float(defense.col) + 1.0,
                        row      = float(defense.row) + 1.0,
                        dest_col = best.col,
                        dest_row = best.row,
                        damage   = defense.damage,
                        splash   = defense.splash_radius,
                        speed    = 9.0,
                        def_id   = defense.building_id,
                    ))

        # ── Déplacement et impact des projectiles ─────────────────────────────
        remaining: list[Projectile] = []
        for proj in self.projectiles:
            dx   = proj.dest_col - proj.col
            dy   = proj.dest_row - proj.row
            dist = math.hypot(dx, dy)
            step = proj.speed * dt
            if dist <= step or dist == 0:
                # Arrivé à destination – applique les dégâts
                if proj.splash > 0:
                    self._apply_troop_splash(proj.dest_col, proj.dest_row,
                                             proj.splash, proj.damage, alive_troops)
                else:
                    # Touche la troupe vivante la plus proche du point d'impact
                    best, best_d = None, float("inf")
                    for t in alive_troops:
                        d = math.hypot(t.col - proj.dest_col, t.row - proj.dest_row)
                        if d < best_d:
                            best_d, best = d, t
                    if best is not None and best_d < 2.0:
                        best.take_damage(proj.damage)
            else:
                proj.col += dx / dist * step
                proj.row += dy / dist * step
                remaining.append(proj)
        self.projectiles = remaining

        # ── Fin si QG détruit ────────────────────────────────────────────────
        for b in alive_buildings:
            if b.building_id == "headquarters":
                # alive_buildings contient seulement les vivants, donc si le QG
                # n'est plus dans alive_buildings il est détruit → vérifier dans
                # _def_buildings directement
                break
        for b in self._def_buildings:
            if b.building_id == "headquarters" and b.is_destroyed:
                self._finished = True
                return

    # ── Ciblage IA (simplifié) ────────────────────────────────────────────────

    def _all_defender_buildings(self) -> list[Building | Defense]:
        return list(self._def_buildings) + list(self._def_defenses)

    # ── Dégâts de zone ────────────────────────────────────────────────────────

    def _apply_splash_damage(
        self, center_col: float, center_row: float, radius: float, damage: int,
        alive_buildings: list,
    ) -> None:
        """Applique des dégâts de zone aux bâtiments défenseurs vivants."""
        for b in alive_buildings:
            if math.hypot(b.col - center_col, b.row - center_row) <= radius:
                b.take_damage(damage)

    def _apply_troop_splash(
        self, center_col: float, center_row: float, radius: float, damage: int,
        alive_troops: list,
    ) -> None:
        """Applique des dégâts de zone aux troupes vivantes."""
        for t in alive_troops:
            if math.hypot(t.col - center_col, t.row - center_row) <= radius:
                t.take_damage(damage)

    # ── Fin de combat ─────────────────────────────────────────────────────────

    def is_over(self) -> bool:
        return self._finished or self.time_left <= 0

    def destruction_percentage(self) -> float:
        """Pourcentage de HP détruits parmi tous les bâtiments défenseurs."""
        if self._total_hp == 0:
            return 0.0
        destroyed_hp = sum(
            b.max_hp - b.current_hp
            for b in self._all_defender_buildings()
        )
        return min(1.0, destroyed_hp / self._total_hp)

    def _hq_destroyed(self) -> bool:
        for b in self._def_buildings:
            if b.building_id == "headquarters" and b.is_destroyed:
                return True
        return False

    def finalize(self) -> AttackRecord:
        """
        Calcule les étoiles et enregistre l'AttackRecord dans les deux villages.

        Système d'étoiles attaquant :
          ⭐  1 : QG détruit
          ⭐⭐ 2 : QG détruit + ≥50 % destruction
          ⭐⭐⭐3 : 100 % destruction

        Système d'étoiles défenseur (étoiles inversées) :
          3 étoiles déf si attaquant obtient 0
          2 étoiles déf si attaquant obtient 1
          1 étoile  déf si attaquant obtient 2
          0 étoile  déf si attaquant obtient 3
        """
        pct = self.destruction_percentage()
        hq_down = self._hq_destroyed()

        if pct >= 1.0:
            stars_atk = 3
        elif pct >= 0.5 and hq_down:
            stars_atk = 2
        elif hq_down:
            stars_atk = 1
        else:
            stars_atk = 0

        stars_def = max(0, 3 - stars_atk)

        record = AttackRecord(
            day=self.day,
            attacker_id=self.attacker_key,
            defender_id=self.defender_key,
            stars_attacker=stars_atk,
            stars_defender=stars_def,
            destruction_pct=round(pct, 3),
        )

        # Enregistrement dans les deux villages
        self.attacker_village.attack_history.append(record)
        self.defender_village.attack_history.append(record)

        # Répare les bâtiments du défenseur après le combat
        for b in self.defender_village.buildings:
            b.repair()
        for d in self.defender_village.defenses:
            d.repair()

        return record
