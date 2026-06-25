"""
player.py
Représente une équipe (sizaine) avec son empire et son village.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from core.constants import EMPIRES
from core.village import Village


@dataclass
class Team:
    """
    Une équipe de camp.

    Attributs :
        empire_key  – clé dans EMPIRES ("rouge", "vert", …)
        name        – nom de l'empire
        color       – tuple RGB
        village     – village associé
    """
    empire_key: str
    village:    Village = field(default_factory=lambda: None)  # type: ignore

    def __post_init__(self) -> None:
        info = EMPIRES.get(self.empire_key, {})
        self.name:  str        = info.get("name", self.empire_key)
        self.color: tuple      = info.get("color", (128, 128, 128))
        if self.village is None:
            self.village = Village.new(self.empire_key)

    # ── Délégation des stats ──────────────────────────────────────────────────

    @property
    def total_stars(self) -> int:
        return self.village.total_stars

    @property
    def attack_stars(self) -> int:
        return self.village.total_attack_stars

    @property
    def defense_stars(self) -> int:
        return self.village.total_defense_stars

    # ── Sérialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "empire_key": self.empire_key,
            "village":    self.village.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        team = cls.__new__(cls)
        team.empire_key = data["empire_key"]
        team.village    = Village.from_dict(data["village"])
        # Recalcule name/color depuis EMPIRES
        info = EMPIRES.get(team.empire_key, {})
        team.name  = info.get("name", team.empire_key)
        team.color = info.get("color", (128, 128, 128))
        return team
