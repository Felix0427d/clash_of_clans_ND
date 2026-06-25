"""
defenses.py
Bâtiments défensifs du village : Canon, Tour d'archers, Mortier.
Héritent de Building (catégorie "defenses").
"""

from __future__ import annotations
from dataclasses import dataclass, field
from entities.buildings import Building, BALANCE


# ── Classe de base défense ────────────────────────────────────────────────────

@dataclass
class Defense(Building):
    """
    Bâtiment défensif.  Ajoute damage, range, attack_speed.
    La boucle de combat interroge ces propriétés pour simuler les tirs.
    """

    # Temps avant le prochain tir (géré par le moteur de combat)
    _cooldown: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._category = "defenses"
        super().__post_init__()

    @property
    def damage(self) -> int:
        return self._level_data.get("damage", 10)

    @property
    def range_cells(self) -> float:
        """Portée en cellules de grille."""
        return self._level_data.get("range", 4)

    @property
    def attack_speed(self) -> float:
        """Secondes entre deux tirs."""
        return self._level_data.get("attack_speed", 2.0)

    @property
    def splash_radius(self) -> float:
        """Rayon d'explosion (0 = pas de splash)."""
        return self._level_data.get("splash", 0.0)

    def can_shoot(self, dt: float) -> bool:
        """
        Décrément du cooldown.
        Retourne True si la défense peut tirer ce frame.
        """
        self._cooldown -= dt
        if self._cooldown <= 0:
            self._cooldown = self.attack_speed
            return True
        return False

    def reset_cooldown(self) -> None:
        self._cooldown = 0.0

    def upgrade_cost(self):  # type: ignore[override]
        from core.constants import MAX_BUILDING_LEVEL
        if self.level >= MAX_BUILDING_LEVEL:
            return None
        next_data = BALANCE["defenses"][self.building_id]["levels"][self.level]
        return {
            "gold":   next_data.get("cost_gold", 0),
            "elixir": next_data.get("cost_elixir", 0),
        }

    def upgrade(self) -> bool:
        from core.constants import MAX_BUILDING_LEVEL
        if self.level >= MAX_BUILDING_LEVEL:
            return False
        self.level += 1
        self._sync_stats()
        return True


# ── Sous-classes concrètes ────────────────────────────────────────────────────

@dataclass
class Canon(Defense):
    """Canon – dégâts élevés, tir direct, pas de splash."""
    def __post_init__(self) -> None:
        self.building_id = "cannon"
        super().__post_init__()


@dataclass
class ArcherTower(Defense):
    """Tour d'archers – cadence rapide, portée longue."""
    def __post_init__(self) -> None:
        self.building_id = "archer_tower"
        super().__post_init__()


@dataclass
class Mortar(Defense):
    """Mortier – tir indirect avec splash, cadence lente."""
    def __post_init__(self) -> None:
        self.building_id = "mortar"
        super().__post_init__()


# ── Mapping id → classe ───────────────────────────────────────────────────────

DEFENSE_CLASSES: dict[str, type[Defense]] = {
    "cannon":        Canon,
    "archer_tower":  ArcherTower,
    "mortar":        Mortar,
}


def defense_from_dict(data: dict) -> Defense:
    """Reconstruit une défense depuis un dict (chargement JSON)."""
    cls = DEFENSE_CLASSES.get(data["building_id"], Defense)
    obj = cls.__new__(cls)
    obj.building_id = data["building_id"]
    obj.col = data["col"]
    obj.row = data["row"]
    obj.level = data["level"]
    obj._category = "defenses"
    obj._cooldown = 0.0
    obj._sync_stats()
    obj.current_hp = data.get("current_hp", obj.max_hp)
    return obj
