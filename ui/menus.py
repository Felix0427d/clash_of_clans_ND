"""
menus.py
Écrans de menu principal et vue d'ensemble des 6 villages.
"""

from __future__ import annotations
import pygame
from typing import Optional, TYPE_CHECKING

from core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG, COLOR_PANEL, COLOR_HIGHLIGHT,
    COLOR_GOLD, COLOR_ELIXIR, COLOR_WHITE, COLOR_TEXT_DARK,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_STAR,
    EMPIRES,
)
from core.game import GameState
from ui.base_screen import Screen

if TYPE_CHECKING:
    from core.game import GameManager


# ── Écran principal (menu titre) ──────────────────────────────────────────────

class MainMenuScreen(Screen):
    """Menu titre avec options Nouvelle partie / Charger / Quitter."""

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_title = pygame.font.SysFont("segoeuibold", 56, bold=True)
        self._font_sub   = pygame.font.SysFont("segoeui", 28)
        self._font_btn   = pygame.font.SysFont("segoeui", 24)

        btn_w, btn_h = 280, 52
        cx = SCREEN_WIDTH // 2
        self._buttons = [
            {"label": "Nouvelle partie", "action": "new",  "rect": pygame.Rect(cx - btn_w//2, 320, btn_w, btn_h)},
            {"label": "Charger partie",  "action": "load", "rect": pygame.Rect(cx - btn_w//2, 390, btn_w, btn_h)},
            {"label": "Quitter",         "action": "quit", "rect": pygame.Rect(cx - btn_w//2, 460, btn_w, btn_h)},
        ]
        self._hovered: Optional[int] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._hovered = None
            for i, btn in enumerate(self._buttons):
                if btn["rect"].collidepoint(event.pos):
                    self._hovered = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self._buttons:
                if btn["rect"].collidepoint(event.pos):
                    self._handle_action(btn["action"])

    def _handle_action(self, action: str) -> None:
        if action == "new":
            self.game.new_game()
        elif action == "load":
            self.game.load()
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        # Titre
        self.draw_text(surface, "Camp Napoléon", SCREEN_WIDTH // 2, 140,
                       self._font_title, COLOR_GOLD, center=True)
        self.draw_text(surface, "Clash of Clans – Édition camp", SCREEN_WIDTH // 2, 210,
                       self._font_sub, COLOR_WHITE, center=True)

        # Boutons
        for i, btn in enumerate(self._buttons):
            color = COLOR_HIGHLIGHT if i == self._hovered else COLOR_PANEL
            self.draw_panel(surface, btn["rect"], color)
            self.draw_text(surface, btn["label"],
                           btn["rect"].centerx, btn["rect"].centery,
                           self._font_btn, COLOR_WHITE, center=True)


# ── Vue d'ensemble des 6 villages ────────────────────────────────────────────

class OverviewScreen(Screen):
    """
    Écran principal montrant les 6 villages disposés en grille 2×3.
    Chaque carte affiche : empire, ressources, étoiles.
    """
    CARD_W, CARD_H = 360, 200
    COLS, ROWS     = 3, 2
    PAD_X, PAD_Y   = 60, 80

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_title  = pygame.font.SysFont("segoeuibold", 32, bold=True)
        self._font_empire = pygame.font.SysFont("segoeuibold", 22, bold=True)
        self._font_info   = pygame.font.SysFont("segoeui", 18)
        self._font_day    = pygame.font.SysFont("segoeui", 22)
        self._font_btn    = pygame.font.SysFont("segoeui", 18)
        self._hovered_idx: Optional[int] = None

        # Bouton "Jour suivant"
        self._btn_next_day = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60, 200, 42)
        # Bouton "Classement"
        self._btn_rank = pygame.Rect(SCREEN_WIDTH - 450, SCREEN_HEIGHT - 60, 200, 42)

    def _card_rect(self, idx: int) -> pygame.Rect:
        col = idx % self.COLS
        row = idx // self.COLS
        x = self.PAD_X + col * (self.CARD_W + 24)
        y = self.PAD_Y + 60 + row * (self.CARD_H + 20)
        return pygame.Rect(x, y, self.CARD_W, self.CARD_H)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._hovered_idx = None
            for i in range(len(self.game.teams)):
                if self._card_rect(i).collidepoint(event.pos):
                    self._hovered_idx = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, team in enumerate(self.game.teams):
                if self._card_rect(i).collidepoint(event.pos):
                    self.game.select_team(team.empire_key)
                    return

            if self._btn_next_day.collidepoint(event.pos):
                self.game.advance_day()

            if self._btn_rank.collidepoint(event.pos):
                self.game.state = GameState.RESULTS

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        # En-tête
        self.draw_text(surface, "Camp Napoléon – Vue d'ensemble",
                       SCREEN_WIDTH // 2, 18, self._font_title, COLOR_GOLD, center=True)
        self.draw_text(surface, f"Jour {self.game.current_day} / 10",
                       SCREEN_WIDTH // 2, 52, self._font_day, COLOR_WHITE, center=True)

        for i, team in enumerate(self.game.teams):
            rect = self._card_rect(i)
            bg = COLOR_HIGHLIGHT if i == self._hovered_idx else COLOR_PANEL
            # Fond teinté couleur empire
            empire_color = team.color
            tinted = tuple(min(255, c + 30) for c in empire_color)
            self.draw_panel(surface, rect, bg, border_color=empire_color, border_width=3)

            # Barre de couleur empire en haut de la carte
            top_bar = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, 10)
            pygame.draw.rect(surface, empire_color, top_bar, border_radius=8)

            # Nom de l'empire
            self.draw_text(surface, team.name, rect.x + 12, rect.y + 20,
                           self._font_empire, COLOR_WHITE)

            # Ressources
            v = team.village
            self.draw_text(surface, f"Or: {v.resources.gold}",
                           rect.x + 12, rect.y + 52, self._font_info, COLOR_GOLD)
            self.draw_text(surface, f"Élixir: {v.resources.elixir}",
                           rect.x + 12, rect.y + 76, self._font_info, COLOR_ELIXIR)

            # Étoiles
            self.draw_text(surface, "Étoiles:", rect.x + 12, rect.y + 110,
                           self._font_info, COLOR_WHITE)
            self.draw_stars(surface, rect.x + 90, rect.y + 112,
                            team.total_stars, max_stars=min(team.total_stars + 1, 30),
                            size=16)
            self.draw_text(surface, str(team.total_stars),
                           rect.x + 94 + min(team.total_stars + 1, 30) * 20,
                           rect.y + 110, self._font_info, COLOR_STAR)

            # Attaque/Défense
            self.draw_text(surface, f"Atk ⭐ {team.attack_stars}  Déf ⭐ {team.defense_stars}",
                           rect.x + 12, rect.y + 140, self._font_info, (200, 200, 200))

        # Boutons en bas
        self.draw_panel(surface, self._btn_next_day, COLOR_SUCCESS)
        self.draw_text(surface, "Jour suivant →",
                       self._btn_next_day.centerx, self._btn_next_day.centery,
                       self._font_btn, COLOR_WHITE, center=True)

        self.draw_panel(surface, self._btn_rank, COLOR_PANEL)
        self.draw_text(surface, "Classement",
                       self._btn_rank.centerx, self._btn_rank.centery,
                       self._font_btn, COLOR_WHITE, center=True)


# ── Classement final ──────────────────────────────────────────────────────────

class ResultsScreen(Screen):
    """Affiche le classement des équipes par étoiles."""

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_title = pygame.font.SysFont("segoeuibold", 42, bold=True)
        self._font_row   = pygame.font.SysFont("segoeui", 28)
        self._font_btn   = pygame.font.SysFont("segoeui", 22)
        self._btn_back   = pygame.Rect(30, SCREEN_HEIGHT - 60, 160, 42)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_back.collidepoint(event.pos):
                self.game.state = GameState.OVERVIEW

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        self.draw_text(surface, "Classement", SCREEN_WIDTH // 2, 40,
                       self._font_title, COLOR_GOLD, center=True)

        board = self.game.leaderboard()
        medals = ["🥇", "🥈", "🥉", "", "", ""]
        for rank, team in enumerate(board):
            y = 120 + rank * 72
            row_rect = pygame.Rect(SCREEN_WIDTH // 2 - 380, y, 760, 58)
            self.draw_panel(surface, row_rect, COLOR_PANEL, border_color=team.color, border_width=3)
            label = f"  #{rank+1}  {team.name}"
            self.draw_text(surface, label, row_rect.x + 10, row_rect.y + 14,
                           self._font_row, team.color)
            stars_text = f"⭐ {team.total_stars}  (Atk {team.attack_stars} + Déf {team.defense_stars})"
            self.draw_text(surface, stars_text, row_rect.right - 380, row_rect.y + 14,
                           self._font_row, COLOR_GOLD)

        self.draw_panel(surface, self._btn_back, COLOR_PANEL)
        self.draw_text(surface, "← Retour", self._btn_back.centerx, self._btn_back.centery,
                       self._font_btn, COLOR_WHITE, center=True)
