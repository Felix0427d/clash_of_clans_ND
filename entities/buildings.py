"""
buildings.py
Hiérarchie des bâtiments du village.
Chaque bâtiment est défini par son type, son niveau et ses stats courantes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
import pathlib

# Chemin vers le fichier d'équilibrage
_BALANCE_PATH = pathlib.Path(__file__).parent.parent / "data" / "balance.json"


def _load_balance() -> dict:
    with open(_BALANCE_PATH, encoding="utf-8") as f:
        return json.load(f)


BALANCE: dict = _load_balance()


# ── Classe de base ────────────────────────────────────────────────────────────

@dataclass
class Building:
    """Représente un bâtiment du village."""
    building_id:  str            # ex. "headquarters", "cannon"
    col:          int            # position colonne sur la grille
    row:          int            # position ligne sur la grille
    level:        int = 1        # niveau actuel (1-indexed)
    current_hp:   int = field(init=False)
    max_hp:       int = field(init=False)

    # ── Catégorie de données (buildings ou defenses) ──────────────────────────
    _category: str = field(default="buildings", init=False, repr=False)

    def __post_init__(self) -> None:
        self._sync_stats()

    # ── Stats au niveau courant ───────────────────────────────────────────────

    @property
    def _level_data(self) -> dict:
        cat = BALANCE.get(self._category, {})
        entry = cat.get(self.building_id, {})
        levels = entry.get("levels", [])
        idx = max(0, min(self.level - 1, len(levels) - 1))
        return levels[idx]

    def _sync_stats(self) -> None:
        self.max_hp = self._level_data.get("hp", 500)
        self.current_hp = self.max_hp

    @property
    def name(self) -> str:
        cat = BALANCE.get(self._category, {})
        return cat.get(self.building_id, {}).get("name", self.building_id)

    @property
    def is_destroyed(self) -> bool:
        return self.current_hp <= 0

    # ── Coûts d'amélioration vers le prochain niveau ─────────────────────────

    def upgrade_cost(self) -> Optional[dict[str, int]]:
        """
        Retourne {'gold': x, 'elixir': y} pour passer au niveau suivant,
        ou None si déjà au niveau maximum.
        """
        from core.constants import MAX_BUILDING_LEVEL
        if self.level >= MAX_BUILDING_LEVEL:
            return None
        next_data = BALANCE[self._category][self.building_id]["levels"][self.level]
        return {
            "gold":   next_data.get("cost_gold", 0),
            "elixir": next_data.get("cost_elixir", 0),
        }

    def upgrade(self) -> bool:
        """
        Améliore le bâtiment d'un niveau sans vérifier les ressources.
        La vérification est faite par Economy.upgrade_building().
        Retourne True si l'amélioration a eu lieu.
        """
        from core.constants import MAX_BUILDING_LEVEL
        if self.level >= MAX_BUILDING_LEVEL:
            return False
        self.level += 1
        self._sync_stats()
        return True

    # ── Dégâts ────────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> None:
        """Applique des dégâts en tenant compte de la résistance éventuelle."""
        resistance = self._level_data.get("resistance", 1)
        actual = max(1, amount // resistance)
        self.current_hp = max(0, self.current_hp - actual)

    def repair(self) -> None:
        """Restaure complètement les PV (entre deux journées)."""
        self.current_hp = self.max_hp

    def to_dict(self) -> dict:
        return {
            "building_id": self.building_id,
            "col": self.col,
            "row": self.row,
            "level": self.level,
            "current_hp": self.current_hp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Building":
        obj = cls(
            building_id=data["building_id"],
            col=data["col"],
            row=data["row"],
            level=data["level"],
        )
        obj.current_hp = data.get("current_hp", obj.max_hp)
        return obj


# ── Sous-classes spécialisées ─────────────────────────────────────────────────

@dataclass
class Headquarters(Building):
    """Quartier Général – cible principale d'une attaque."""
    def __post_init__(self) -> None:
        self.building_id = "headquarters"
        super().__post_init__()


@dataclass
class Mine(Building):
    """Mine d'or ou d'élixir."""
    resource: str = "gold"  # "gold" | "elixir"

    def __post_init__(self) -> None:
        # building_id doit être défini avant super().__post_init__
        super().__post_init__()

    @property
    def daily_production(self) -> int:
        """Production journalière selon le niveau."""
        entry = BALANCE["buildings"].get(self.building_id, {})
        base = entry.get("base_production", 50)
        mult = self._level_data.get("production_mult", 1)
        return base * mult

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["resource"] = self.resource
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Mine":  # type: ignore[override]
        obj = cls(
            building_id=data["building_id"],
            col=data["col"],
            row=data["row"],
            level=data["level"],
            resource=data.get("resource", "gold"),
        )
        obj.current_hp = data.get("current_hp", obj.max_hp)
        return obj


@dataclass
class Wall(Building):
    """Remparts – résistance croissante selon le niveau."""
    def __post_init__(self) -> None:
        self.building_id = "wall"
        super().__post_init__()

    @property
    def resistance(self) -> int:
        return self._level_data.get("resistance", 1)


@dataclass
class Barracks(Building):
    """Caserne – débloque les types de troupes selon le niveau."""
    def __post_init__(self) -> None:
        self.building_id = "barracks"
        super().__post_init__()

    @property
    def unlocked_troops(self) -> list[str]:
        return self._level_data.get("unlock", ["soldier"])
