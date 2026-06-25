"""
troops.py
Définition des types de troupes et instances en combat.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
import pathlib

_BALANCE_PATH = pathlib.Path(__file__).parent.parent / "data" / "balance.json"


def _load_balance() -> dict:
    with open(_BALANCE_PATH, encoding="utf-8") as f:
        return json.load(f)


BALANCE: dict = _load_balance()


# ── Type de troupe (méta-donnée par niveau) ───────────────────────────────────

@dataclass
class TroopType:
    """
    Représente un type de troupe et son niveau d'amélioration actuel.
    Appartient au village (lié à la caserne).
    """
    troop_id:   str       # "soldier", "archer", …
    level:      int = 1   # 1-indexed

    @property
    def _data(self) -> dict:
        levels = BALANCE["troops"][self.troop_id]["levels"]
        idx = max(0, min(self.level - 1, len(levels) - 1))
        return levels[idx]

    @property
    def name(self) -> str:
        return BALANCE["troops"][self.troop_id]["name"]

    @property
    def theme(self) -> str:
        return BALANCE["troops"][self.troop_id].get("theme", "")

    @property
    def hp(self) -> int:
        return self._data["hp"]

    @property
    def damage(self) -> int:
        return self._data["damage"]

    @property
    def speed(self) -> float:
        """Cellules par seconde."""
        return self._data["speed"]

    @property
    def range_cells(self) -> float:
        return self._data.get("range", 1)

    @property
    def splash_radius(self) -> float:
        return self._data.get("splash", 0.0)

    @property
    def training_cost(self) -> int:
        return self._data.get("training_cost_elixir", 20)

    def upgrade_cost(self) -> Optional[int]:
        """Coût en élixir pour passer au niveau suivant, ou None si max."""
        from core.constants import MAX_TROOP_LEVEL
        if self.level >= MAX_TROOP_LEVEL:
            return None
        return BALANCE["troops"][self.troop_id]["levels"][self.level].get(
            "training_cost_elixir", 0
        ) * 5  # coût d'amélioration = 5× coût d'entraînement du prochain niveau

    def upgrade(self) -> bool:
        from core.constants import MAX_TROOP_LEVEL
        if self.level >= MAX_TROOP_LEVEL:
            return False
        self.level += 1
        return True

    def to_dict(self) -> dict:
        return {"troop_id": self.troop_id, "level": self.level}

    @classmethod
    def from_dict(cls, data: dict) -> "TroopType":
        return cls(troop_id=data["troop_id"], level=data["level"])


# ── Instance de troupe (entité vivante pendant le combat) ─────────────────────

@dataclass
class TroopInstance:
    """
    Instance d'une troupe déployée sur la carte de combat.
    Possède une position en grille (float pour le déplacement fluide).
    """
    troop_type:  TroopType
    col:         float          # position colonne (float pour déplacement)
    row:         float          # position ligne (float pour déplacement)
    current_hp:  int = field(init=False)
    target:      Optional[object] = field(default=None, repr=False)
    _atk_cooldown: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.current_hp = self.troop_type.hp

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def take_damage(self, amount: int) -> None:
        self.current_hp = max(0, self.current_hp - amount)

    def can_attack(self, dt: float) -> bool:
        """
        Gestion du cooldown d'attaque.
        Vitesse → 1 attaque toutes que (1 / speed) secondes.
        """
        self._atk_cooldown -= dt
        if self._atk_cooldown <= 0:
            self._atk_cooldown = 1.0 / max(0.1, self.troop_type.speed)
            return True
        return False

    def move_towards(self, target_col: float, target_row: float, dt: float) -> None:
        """Déplace la troupe vers la cible à sa vitesse."""
        import math
        dx = target_col - self.col
        dy = target_row - self.row
        dist = math.hypot(dx, dy)
        if dist < 0.01:
            return
        speed = self.troop_type.speed
        step = speed * dt
        if step >= dist:
            self.col, self.row = target_col, target_row
        else:
            self.col += dx / dist * step
            self.row += dy / dist * step

    def distance_to(self, col: float, row: float) -> float:
        import math
        return math.hypot(self.col - col, self.row - row)
