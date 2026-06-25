"""
game.py
GameManager : orchestre les équipes, la progression journalière et les transitions d'état.
"""

from __future__ import annotations
from typing import Optional

from core.constants import EMPIRES, CAMP_DAYS
from core.player import Team
from core.economy import Economy
from core import save as save_module


class GameState:
    """Constantes d'état de la machine à états du jeu."""
    MAIN_MENU    = "main_menu"
    OVERVIEW     = "overview"       # Écran principal 6 villages
    VILLAGE      = "village"        # Vue détaillée d'un village
    UPGRADE      = "upgrade"        # Menu d'amélioration
    ATTACK_SETUP = "attack_setup"   # Sélection de la cible + troupes
    COMBAT       = "combat"         # Écran de combat temps-réel
    DAY_SUMMARY  = "day_summary"    # Résumé de la journée
    RESULTS      = "results"        # Classement final


class GameManager:
    """
    Cœur du jeu.

    Responsabilités :
      - maintenir la liste des équipes
      - gérer le jour courant
      - orchestrer les transitions d'état
      - déléguer la sauvegarde/chargement
    """

    def __init__(self) -> None:
        self.teams:             list[Team]     = []
        self.current_day:       int            = 1
        self.state:             str            = GameState.MAIN_MENU
        self.active_team:       Optional[Team] = None   # équipe sélectionnée
        self.combat_session:    Optional[object] = None  # CombatSession en cours
        self.last_attack_record: Optional[object] = None # dernier AttackRecord pour le récap

    # ── Initialisation d'une nouvelle partie ─────────────────────────────────

    def new_game(self) -> None:
        """Crée les 6 équipes avec des villages de départ."""
        self.teams       = [Team(k) for k in EMPIRES]
        self.current_day = 1
        self.state       = GameState.OVERVIEW
        self.active_team = None
        save_module.save_game(self)

    # ── Progression journalière ───────────────────────────────────────────────

    def advance_day(self) -> dict[str, dict[str, int]]:
        """
        Passe au jour suivant :
          1. Applique la production des mines pour toutes les équipes.
          2. Incrémente le compteur de jours.
          3. Sauvegarde automatiquement.
        Retourne un dict {empire_key: {gold: x, elixir: y}} des productions.
        """
        production_report: dict[str, dict[str, int]] = {}
        for team in self.teams:
            eco = Economy(team.village)
            produced = eco.apply_daily_production()
            production_report[team.empire_key] = produced

        self.current_day = min(self.current_day + 1, CAMP_DAYS)
        save_module.save_game(self)
        return production_report

    def award_resources(self, empire_key: str, gold: int = 0, elixir: int = 0) -> bool:
        """Attribue des ressources à une équipe (action animateur)."""
        team = self.get_team(empire_key)
        if team is None:
            return False
        Economy(team.village).award_resources(gold=gold, elixir=elixir)
        save_module.save_game(self)
        return True

    # ── Accès aux équipes ─────────────────────────────────────────────────────

    def get_team(self, empire_key: str) -> Optional[Team]:
        for t in self.teams:
            if t.empire_key == empire_key:
                return t
        return None

    def leaderboard(self) -> list[Team]:
        """Retourne les équipes triées par étoiles totales décroissantes."""
        return sorted(self.teams, key=lambda t: t.total_stars, reverse=True)

    # ── Transitions d'état ────────────────────────────────────────────────────

    def select_team(self, empire_key: str) -> bool:
        team = self.get_team(empire_key)
        if team is None:
            return False
        self.active_team = team
        self.state = GameState.VILLAGE
        return True

    def start_combat(self, attacker_key: str, defender_key: str) -> bool:
        """Initialise une CombatSession et passe en état COMBAT."""
        from core.combat import CombatSession
        attacker = self.get_team(attacker_key)
        defender = self.get_team(defender_key)
        if attacker is None or defender is None:
            return False
        self.combat_session = CombatSession(
            attacker_village=attacker.village,
            defender_village=defender.village,
            attacker_key=attacker_key,
            day=self.current_day,
        )
        self.state = GameState.COMBAT
        return True

    def end_combat(self) -> Optional[object]:
        """Finalise le combat et retourne l'AttackRecord."""
        if self.combat_session is None:
            return None
        record = self.combat_session.finalize()
        self.last_attack_record = record
        self.combat_session = None
        self.state = GameState.DAY_SUMMARY
        save_module.save_game(self)
        return record

    # ── Sauvegarde / chargement ────────────────────────────────────────────────

    def save(self, slot: str = "autosave") -> None:
        save_module.save_game(self, slot)

    def load(self, slot: str = "autosave") -> bool:
        data = save_module.load_game(slot)
        if data is None:
            return False
        self.current_day = data["meta"]["current_day"]
        self.teams = [Team.from_dict(t) for t in data["teams"]]
        self.state = GameState.OVERVIEW
        return True
