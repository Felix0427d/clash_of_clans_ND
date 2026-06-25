"""
recap_screen.py
Écran de récapitulatif après un combat.
Affiche les étoiles, la destruction, les pertes et guide vers la prochaine action.

Pipeline de jeu :
  COMBAT → DAY_SUMMARY (recap) → OVERVIEW (changer de sizaine ou passer au jour suivant)
"""

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG, COLOR_PANEL, COLOR_HIGHLIGHT,
    COLOR_GOLD, COLOR_ELIXIR, COLOR_WHITE,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_STAR,
)
from core.game import GameState
from ui.base_screen import Screen

if TYPE_CHECKING:
    from core.game import GameManager
    from core.village import AttackRecord


class DaySummaryScreen(Screen):
    """
    Récapitulatif post-combat.

    Affiche :
      - Attaquant et défenseur (noms + couleurs)
      - Étoiles attaquant (0-3) et étoiles défensives (0-3)
      - Pourcentage de destruction
      - Troupes perdues
      - Classement rapide en bas

    Boutons :
      - "Jouer une autre sizaine"  → OVERVIEW  (pipeline principal)
      - "Revoir le village"        → VILLAGE   (facultatif)
    """

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_big    = pygame.font.SysFont("segoeuibold", 44, bold=True)
        self._font_title  = pygame.font.SysFont("segoeuibold", 28, bold=True)
        self._font_info   = pygame.font.SysFont("segoeui", 22)
        self._font_small  = pygame.font.SysFont("segoeui", 17)
        self._font_btn    = pygame.font.SysFont("segoeui", 20)

        cx = SCREEN_WIDTH // 2
        self._btn_overview = pygame.Rect(cx - 260, SCREEN_HEIGHT - 80, 240, 52)
        self._btn_village  = pygame.Rect(cx + 20,  SCREEN_HEIGHT - 80, 240, 52)

    # ── Événements ────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos

        if self._btn_overview.collidepoint(pos):
            # Retour à la vue globale pour jouer avec une autre sizaine
            self.game.state = GameState.OVERVIEW
            return

        if self._btn_village.collidepoint(pos):
            # Revenir sur le village de l'attaquant
            self.game.state = GameState.VILLAGE
            return

    def update(self, dt: float) -> None:
        pass

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        record = self.game.last_attack_record
        if record is None:
            self.draw_text(surface, "Aucun combat enregistré.",
                           SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                           self._font_title, COLOR_WHITE, center=True)
            self._draw_buttons(surface)
            return

        atk_team = self.game.get_team(record.attacker_id)
        def_team = self.game.get_team(record.defender_id)
        atk_name = atk_team.name if atk_team else record.attacker_id
        def_name = def_team.name if def_team else record.defender_id
        atk_color = atk_team.color if atk_team else COLOR_WHITE
        def_color = def_team.color if def_team else COLOR_WHITE

        # ── Titre ────────────────────────────────────────────────────────────
        self.draw_text(surface, "Résultat du combat",
                       SCREEN_WIDTH // 2, 20, self._font_title, COLOR_GOLD, center=True)

        # ── Bannières Attaquant / Défenseur ───────────────────────────────────
        banner_y   = 68
        banner_h   = 70
        mid        = SCREEN_WIDTH // 2

        # Attaquant
        atk_rect = pygame.Rect(60, banner_y, mid - 80, banner_h)
        self.draw_panel(surface, atk_rect, COLOR_PANEL, border_color=atk_color, border_width=3)
        self.draw_text(surface, "ATTAQUANT", atk_rect.x + 12, banner_y + 6,
                       self._font_small, (180, 180, 180))
        self.draw_text(surface, atk_name, atk_rect.x + 12, banner_y + 26,
                       self._font_info, atk_color)

        # Défenseur
        def_rect = pygame.Rect(mid + 20, banner_y, mid - 80, banner_h)
        self.draw_panel(surface, def_rect, COLOR_PANEL, border_color=def_color, border_width=3)
        self.draw_text(surface, "DÉFENSEUR", def_rect.x + 12, banner_y + 6,
                       self._font_small, (180, 180, 180))
        self.draw_text(surface, def_name, def_rect.x + 12, banner_y + 26,
                       self._font_info, def_color)

        # VS
        self.draw_text(surface, "VS", mid, banner_y + banner_h // 2,
                       self._font_big, COLOR_WHITE, center=True)

        # ── Étoiles ───────────────────────────────────────────────────────────
        star_y = banner_y + banner_h + 20

        # Étoiles attaquant
        self.draw_text(surface, "Étoiles obtenues :", 60, star_y,
                       self._font_info, COLOR_WHITE)
        self.draw_stars(surface, 60, star_y + 32, record.stars_attacker, max_stars=3, size=28)

        # Étoiles défenseur
        self.draw_text(surface, "Étoiles défensives :", mid + 20, star_y,
                       self._font_info, COLOR_WHITE)
        self.draw_stars(surface, mid + 20, star_y + 32, record.stars_defender, max_stars=3, size=28)

        # ── Barre de destruction ──────────────────────────────────────────────
        dest_y = star_y + 82
        pct    = record.destruction_pct
        pct_pct = int(pct * 100)
        self.draw_text(surface, f"Destruction : {pct_pct} %",
                       SCREEN_WIDTH // 2, dest_y, self._font_title, COLOR_WHITE, center=True)

        bar_rect = pygame.Rect(100, dest_y + 36, SCREEN_WIDTH - 200, 28)
        pygame.draw.rect(surface, (50, 20, 20), bar_rect, border_radius=8)
        fill_w = int(bar_rect.w * pct)
        if fill_w > 0:
            fill_color = COLOR_SUCCESS if pct < 0.5 else (COLOR_GOLD if pct < 1.0 else COLOR_DANGER)
            pygame.draw.rect(surface, fill_color,
                             pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_rect.h),
                             border_radius=8)
        pygame.draw.rect(surface, (100, 80, 60), bar_rect, 2, border_radius=8)

        # ── Résumé des étoiles ────────────────────────────────────────────────
        summary_y = dest_y + 80
        summary_box = pygame.Rect(100, summary_y, SCREEN_WIDTH - 200, 96)
        self.draw_panel(surface, summary_box, COLOR_PANEL, border_width=0, radius=10)

        outcome_lines = self._outcome_text(record)
        for i, (line, color) in enumerate(outcome_lines):
            self.draw_text(surface, line,
                           SCREEN_WIDTH // 2, summary_y + 12 + i * 30,
                           self._font_info, color, center=True)

        # ── Mini classement ───────────────────────────────────────────────────
        rank_y = summary_y + 112
        self.draw_text(surface, "Classement actuel :",
                       SCREEN_WIDTH // 2, rank_y, self._font_small, (180, 180, 180), center=True)

        board = self.game.leaderboard()
        for rank, team in enumerate(board):
            lx = 100 + rank * ((SCREEN_WIDTH - 200) // 6)
            ly = rank_y + 26
            lw = (SCREEN_WIDTH - 200) // 6 - 4
            lr = pygame.Rect(lx, ly, lw, 50)
            # Surligner attaquant et défenseur
            if team.empire_key in (record.attacker_id, record.defender_id):
                self.draw_panel(surface, lr, COLOR_HIGHLIGHT, border_color=team.color, border_width=3)
            else:
                self.draw_panel(surface, lr, COLOR_PANEL, border_color=team.color, border_width=2)
            self.draw_text(surface, f"#{rank+1}", lr.centerx, lr.y + 4,
                           self._font_small, (180, 180, 180), center=True)
            self.draw_text(surface, f"⭐{team.total_stars}", lr.centerx, lr.y + 24,
                           self._font_small, COLOR_STAR, center=True)

        # ── Boutons ───────────────────────────────────────────────────────────
        self._draw_buttons(surface)

    def _outcome_text(self, record) -> list[tuple[str, tuple]]:
        """Génère les lignes de résumé selon les étoiles obtenues."""
        stars = record.stars_attacker
        if stars == 3:
            return [
                ("Victoire totale ! Village entièrement détruit.", COLOR_DANGER),
                (f"+3 étoiles attaquant  |  +0 étoile défensive", COLOR_GOLD),
            ]
        elif stars == 2:
            return [
                ("Belle attaque ! QG détruit + 50% de destruction.", COLOR_SUCCESS),
                (f"+2 étoiles attaquant  |  +1 étoile défensive", COLOR_GOLD),
            ]
        elif stars == 1:
            return [
                ("QG détruit. Village partiellement résistant.", COLOR_WHITE),
                (f"+1 étoile attaquant  |  +2 étoiles défensives", (200, 200, 200)),
            ]
        else:
            return [
                ("Défense réussie ! Le QG est intact.", COLOR_SUCCESS),
                (f"+0 étoile attaquant  |  +3 étoiles défensives", (200, 200, 200)),
            ]

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        self.draw_panel(surface, self._btn_overview, COLOR_SUCCESS)
        self.draw_text(surface, "⚔ Autre sizaine",
                       self._btn_overview.centerx, self._btn_overview.centery,
                       self._font_btn, COLOR_WHITE, center=True)

        self.draw_panel(surface, self._btn_village, COLOR_PANEL)
        self.draw_text(surface, "🏰 Revoir le village",
                       self._btn_village.centerx, self._btn_village.centery,
                       self._font_btn, COLOR_WHITE, center=True)
