"""
village.py
Le village d'une équipe : bâtiments, ressources, troupes, historique.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from core.economy import Resources
from entities.buildings import Building, Headquarters, Mine, Wall, Barracks
from entities.defenses import Defense, Canon, ArcherTower, Mortar, defense_from_dict
from entities.troops import TroopType


# ── Enregistrement d'une attaque ──────────────────────────────────────────────

@dataclass
class AttackRecord:
    day:            int
    attacker_id:    str   # empire_key de l'attaquant
    defender_id:    str   # empire_key du défenseur
    stars_attacker: int   # étoiles obtenues par l'attaquant (0-3)
    stars_defender: int   # étoiles défensives du défenseur (0-3)
    destruction_pct: float  # 0.0 – 1.0

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "AttackRecord":
        return cls(**d)


# ── Village ───────────────────────────────────────────────────────────────────

class Village:
    """
    Représente le village d'une équipe.

    Attributs principaux :
        empire_key  – clé dans EMPIRES ("rouge", "vert", …)
        resources   – stock de ressources (Resources)
        buildings   – liste ordonnée des bâtiments (hors défenses)
        defenses    – liste des bâtiments défensifs
        troop_types – dict {troop_id: TroopType} (améliorations disponibles)
        army        – dict {troop_id: count} armée entraînée en attente
        attack_history – liste d'AttackRecord
    """

    def __init__(self, empire_key: str) -> None:
        self.empire_key:     str = empire_key
        self.resources:      Resources = Resources()
        self.buildings:      list[Building] = []
        self.defenses:       list[Defense] = []
        self.troop_types:    dict[str, TroopType] = {}
        self.army:           dict[str, int] = {}
        self.attack_history: list[AttackRecord] = []

    # ── Initialisation d'un village neuf ─────────────────────────────────────

    @classmethod
    def new(cls, empire_key: str) -> "Village":
        """
        Crée un village de départ avec la disposition par défaut.
        Le QG est placé au centre de la grille (10, 7).
        """
        from core.constants import GRID_COLS, GRID_ROWS
        v = cls(empire_key)
        cx, cy = GRID_COLS // 2, GRID_ROWS // 2

        # Bâtiments de base
        v.buildings.append(Headquarters(building_id="headquarters", col=cx,     row=cy))
        v.buildings.append(Mine(building_id="gold_mine",   col=cx - 4, row=cy - 2, resource="gold"))
        v.buildings.append(Mine(building_id="elixir_mine", col=cx + 4, row=cy - 2, resource="elixir"))
        v.buildings.append(Barracks(building_id="barracks", col=cx - 4, row=cy + 2))

        # ── Anneau de remparts ──────────────────────────────────────────────
        # Bord supérieur (row=cy-4)
        for wc in range(cx - 6, cx + 7, 2):
            v.buildings.append(Wall(building_id="wall", col=wc, row=cy - 4))
        # Bord inférieur (row=cy+4)
        for wc in range(cx - 6, cx + 7, 2):
            v.buildings.append(Wall(building_id="wall", col=wc, row=cy + 4))
        # Bord gauche (col=cx-7, rows intermédiaires)
        for wr in range(cy - 2, cy + 4, 2):
            v.buildings.append(Wall(building_id="wall", col=cx - 7, row=wr))
        # Bord droit (col=cx+5, rows intermédiaires)
        for wr in range(cy - 2, cy + 4, 2):
            v.buildings.append(Wall(building_id="wall", col=cx + 5, row=wr))

        # Défenses de base (à l'intérieur des remparts)
        v.defenses.append(Canon(building_id="cannon",             col=cx - 2, row=cy))
        v.defenses.append(ArcherTower(building_id="archer_tower", col=cx + 2, row=cy))
        v.defenses.append(Mortar(building_id="mortar",            col=cx,     row=cy + 2))

        # Troupes de départ (débloquées par caserne niv 1)
        v.troop_types["soldier"] = TroopType("soldier")

        # Ressources de départ
        v.resources.earn(gold=500, elixir=500)
        return v

    # ── Accès aux bâtiments ───────────────────────────────────────────────────

    @property
    def headquarters(self) -> Optional[Headquarters]:
        for b in self.buildings:
            if isinstance(b, Headquarters):
                return b
        return None

    @property
    def mines(self) -> list[Mine]:
        return [b for b in self.buildings if isinstance(b, Mine)]

    @property
    def barracks(self) -> Optional[Barracks]:
        for b in self.buildings:
            if isinstance(b, Barracks):
                return b
        return None

    def all_buildings(self) -> list[Building | Defense]:
        """Tous les bâtiments (constructions + défenses) pour le calcul de destruction."""
        return list(self.buildings) + list(self.defenses)

    # ── Troupes ───────────────────────────────────────────────────────────────

    def get_troop_type(self, troop_id: str) -> Optional[TroopType]:
        return self.troop_types.get(troop_id)

    def unlock_troop(self, troop_id: str) -> None:
        """Débloque un type de troupe s'il ne l'est pas encore."""
        if troop_id not in self.troop_types:
            self.troop_types[troop_id] = TroopType(troop_id)

    def sync_unlocked_troops(self) -> None:
        """Synchronise les troupes débloquées avec le niveau de la caserne."""
        bar = self.barracks
        if bar:
            for tid in bar.unlocked_troops:
                self.unlock_troop(tid)

    # ── Statistiques ─────────────────────────────────────────────────────────

    @property
    def total_attack_stars(self) -> int:
        return sum(r.stars_attacker for r in self.attack_history if r.attacker_id == self.empire_key)

    @property
    def total_defense_stars(self) -> int:
        return sum(r.stars_defender for r in self.attack_history if r.defender_id == self.empire_key)

    @property
    def total_stars(self) -> int:
        return self.total_attack_stars + self.total_defense_stars

    # ── Sérialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "empire_key": self.empire_key,
            "resources":  self.resources.to_dict(),
            "buildings":  [b.to_dict() for b in self.buildings],
            "defenses":   [d.to_dict() for d in self.defenses],
            "troop_types": {tid: tt.to_dict() for tid, tt in self.troop_types.items()},
            "army":        dict(self.army),
            "attack_history": [r.to_dict() for r in self.attack_history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Village":
        v = cls(data["empire_key"])
        v.resources = Resources.from_dict(data.get("resources", {}))

        # Reconstruction des bâtiments
        from entities.buildings import BALANCE
        _BUILDING_CLS = {
            "headquarters": Headquarters,
            "gold_mine":    lambda d: Mine(building_id=d["building_id"], col=d["col"], row=d["row"], level=d["level"], resource=d.get("resource","gold")),
            "elixir_mine":  lambda d: Mine(building_id=d["building_id"], col=d["col"], row=d["row"], level=d["level"], resource=d.get("resource","elixir")),
            "wall":         Wall,
            "barracks":     Barracks,
        }
        for bdata in data.get("buildings", []):
            bid = bdata["building_id"]
            factory = _BUILDING_CLS.get(bid)
            if factory:
                if callable(factory) and not isinstance(factory, type):
                    b = factory(bdata)
                else:
                    b = factory.__new__(factory)
                    b.building_id = bdata["building_id"]
                    b.col   = bdata["col"]
                    b.row   = bdata["row"]
                    b.level = bdata["level"]
                    b._category = "buildings"
                    b._sync_stats()
                    b.current_hp = bdata.get("current_hp", b.max_hp)
            else:
                b = Building.from_dict(bdata)
            v.buildings.append(b)

        # Défenses
        for ddata in data.get("defenses", []):
            v.defenses.append(defense_from_dict(ddata))

        # Troupes
        for tid, tdata in data.get("troop_types", {}).items():
            v.troop_types[tid] = TroopType.from_dict(tdata)

        v.army = data.get("army", {})

        for rdata in data.get("attack_history", []):
            v.attack_history.append(AttackRecord.from_dict(rdata))

        return v
