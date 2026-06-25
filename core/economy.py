"""
economy.py
Gestion des ressources, production quotidienne et améliorations.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.village import Village


@dataclass
class Resources:
    """Stock de ressources d'un village."""
    gold:   int = 0
    elixir: int = 0

    def can_afford(self, cost: dict[str, int]) -> bool:
        return self.gold >= cost.get("gold", 0) and self.elixir >= cost.get("elixir", 0)

    def spend(self, cost: dict[str, int]) -> None:
        """Déduit les ressources. Appeler can_afford() avant."""
        self.gold   -= cost.get("gold", 0)
        self.elixir -= cost.get("elixir", 0)

    def earn(self, gold: int = 0, elixir: int = 0) -> None:
        self.gold   += gold
        self.elixir += elixir

    def to_dict(self) -> dict:
        return {"gold": self.gold, "elixir": self.elixir}

    @classmethod
    def from_dict(cls, data: dict) -> "Resources":
        return cls(gold=data.get("gold", 0), elixir=data.get("elixir", 0))


class Economy:
    """
    Logique économique du village :
      - production journalière des mines
      - ajout de ressources par les animateurs
      - coût et exécution des améliorations
    """

    def __init__(self, village: "Village") -> None:
        self.village = village

    # ── Production journalière ────────────────────────────────────────────────

    def apply_daily_production(self) -> dict[str, int]:
        """
        Calcule et ajoute la production journalière des mines au stock.
        Retourne le dict des ressources produites {'gold': x, 'elixir': y}.
        """
        produced: dict[str, int] = {"gold": 0, "elixir": 0}
        for building in self.village.buildings:
            from entities.buildings import Mine
            if isinstance(building, Mine):
                qty = building.daily_production
                produced[building.resource] += qty
        self.village.resources.earn(**produced)
        return produced

    # ── Ajout manuel par les animateurs ──────────────────────────────────────

    def award_resources(self, gold: int = 0, elixir: int = 0) -> None:
        """Les animateurs attribuent des ressources suite à un défi."""
        self.village.resources.earn(gold=gold, elixir=elixir)

    # ── Améliorations de bâtiments ────────────────────────────────────────────

    def upgrade_building(self, building_index: int) -> tuple[bool, str]:
        """
        Tente d'améliorer le bâtiment à l'index donné dans village.buildings.
        Retourne (succès, message).
        """
        buildings = self.village.buildings
        if building_index < 0 or building_index >= len(buildings):
            return False, "Bâtiment introuvable."

        building = buildings[building_index]
        cost = building.upgrade_cost()
        if cost is None:
            return False, f"{building.name} est déjà au niveau maximum."

        if not self.village.resources.can_afford(cost):
            needed_g = cost.get("gold", 0)
            needed_e = cost.get("elixir", 0)
            return False, (
                f"Ressources insuffisantes. "
                f"Manque : {max(0, needed_g - self.village.resources.gold)} or, "
                f"{max(0, needed_e - self.village.resources.elixir)} élixir."
            )

        self.village.resources.spend(cost)
        building.upgrade()
        # Si c'est la caserne, synchroniser les troupes débloquées
        from entities.buildings import Barracks
        if isinstance(building, Barracks):
            self.village.sync_unlocked_troops()
        return True, f"{building.name} amélioré au niveau {building.level}."

    # ── Améliorations de troupes ──────────────────────────────────────────────

    def upgrade_troop(self, troop_id: str) -> tuple[bool, str]:
        """
        Tente d'améliorer la troupe dont l'id est troop_id.
        Les améliorations de troupes coûtent de l'élixir.
        """
        troop_type = self.village.get_troop_type(troop_id)
        if troop_type is None:
            return False, f"Troupe '{troop_id}' non disponible dans ce village."

        cost_elixir = troop_type.upgrade_cost()
        if cost_elixir is None:
            return False, f"{troop_type.name} est déjà au niveau maximum."

        cost = {"gold": 0, "elixir": cost_elixir}
        if not self.village.resources.can_afford(cost):
            return False, (
                f"Élixir insuffisant. Besoin : {cost_elixir}, "
                f"disponible : {self.village.resources.elixir}."
            )

        self.village.resources.spend(cost)
        troop_type.upgrade()
        return True, f"{troop_type.name} amélioré au niveau {troop_type.level}."

    # ── Entraînement de troupes ───────────────────────────────────────────────

    def train_troop(self, troop_id: str, count: int = 1) -> tuple[bool, str]:
        """
        Entraîne `count` unités du type troop_id.
        Les troupes entraînées sont stockées dans village.army.
        """
        troop_type = self.village.get_troop_type(troop_id)
        if troop_type is None:
            return False, f"Troupe '{troop_id}' non disponible."

        total_cost = {"gold": 0, "elixir": troop_type.training_cost * count}
        if not self.village.resources.can_afford(total_cost):
            return False, (
                f"Élixir insuffisant pour entraîner {count}× {troop_type.name}."
            )

        self.village.resources.spend(total_cost)
        self.village.army[troop_id] = self.village.army.get(troop_id, 0) + count
        return True, f"{count}× {troop_type.name} entraîné(s)."
