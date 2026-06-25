"""
base_screen.py
Classe abstraite Screen dont héritent tous les écrans Pygame.
"""

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game import GameManager


class Screen:
    """
    Interface commune pour tous les écrans du jeu.

    Chaque écran implémente :
      handle_event(event)  – gestion des événements clavier/souris
      update(dt)           – logique de mise à jour
      draw(surface)        – rendu sur la surface Pygame
    """

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        self.game    = game
        self.display = display

    def handle_event(self, event: pygame.event.Event) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    # ── Utilitaires de rendu ──────────────────────────────────────────────────

    @staticmethod
    def draw_text(
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple = (255, 255, 255),
        center: bool = False,
    ) -> pygame.Rect:
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        surface.blit(img, rect)
        return rect

    @staticmethod
    def draw_panel(
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple,
        border_color: tuple = (80, 80, 130),
        border_width: int = 2,
        radius: int = 10,
    ) -> None:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border_width > 0:
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)

    @staticmethod
    def draw_stars(
        surface: pygame.Surface,
        x: int,
        y: int,
        count: int,
        max_stars: int = 3,
        size: int = 18,
        color_full: tuple = (255, 215, 0),
        color_empty: tuple = (60, 60, 80),
    ) -> None:
        """Dessine des étoiles pleines/vides."""
        for i in range(max_stars):
            cx = x + i * (size + 4)
            clr = color_full if i < count else color_empty
            # Étoile simplifiée : cercle + polygone étoile
            Screen._draw_star_shape(surface, cx, y, size // 2, clr)

    @staticmethod
    def _draw_star_shape(surface: pygame.Surface, cx: int, cy: int, r: int, color: tuple) -> None:
        import math
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * 2 * math.pi / 10
            radius = r if i % 2 == 0 else r // 2
            points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)
