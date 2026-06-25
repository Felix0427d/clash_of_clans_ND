"""
village_screen.py
Écrans de vue du village et d'amélioration des bâtiments/troupes.

Fonctionnalités :
  - VillageScreen  : grille du village + drag-and-drop des bâtiments
  - UpgradeScreen  : deux onglets avec scroll à la molette
"""

from __future__ import annotations
import pygame
from typing import Optional, TYPE_CHECKING

from core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG, COLOR_PANEL, COLOR_HIGHLIGHT,
    COLOR_GOLD, COLOR_ELIXIR, COLOR_WHITE,
    COLOR_SUCCESS, COLOR_DANGER,
    GRID_COLS, GRID_ROWS, CELL_SIZE,
)
from core.game import GameState
from core.economy import Economy
from core.sprites import get_building_sprite, get_troop_sprite
from ui.base_screen import Screen

if TYPE_CHECKING:
    from core.game import GameManager


# ── Vue détaillée d'un village ────────────────────────────────────────────────

class VillageScreen(Screen):
    """
    Grille 2D du village avec :
      - sprites des bâtiments
      - drag-and-drop pour déplacer un bâtiment
        * clic + maintien → mode glisser
        * relâcher → pose sur la cellule snappée (rouge si invalide)
      - panneau latéral : ressources, info bâtiment, boutons animateur
    """

    PANEL_W = 300

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_title  = pygame.font.SysFont("segoeuibold", 28, bold=True)
        self._font_info   = pygame.font.SysFont("segoeui", 20)
        self._font_small  = pygame.font.SysFont("segoeui", 16)
        self._font_btn    = pygame.font.SysFont("segoeui", 18)

        # État de sélection (clic simple)
        self._selected_idx: Optional[int] = None

        # État drag-and-drop
        self._drag_idx:      Optional[int]          = None   # index dans all_buildings()
        self._drag_mouse:    tuple[int, int]         = (0, 0) # position souris courante
        self._drag_ghost_col: int                    = 0     # colonne snappée
        self._drag_ghost_row: int                    = 0     # ligne snappée
        self._drag_valid:    bool                    = False  # placement légal ?
        self._drag_offset:   tuple[int, int]         = (0, 0) # décalage souris/coin sprite

        # Boutons du panneau
        px = SCREEN_WIDTH - self.PANEL_W + 20
        bw = self.PANEL_W - 40
        self._btn_upgrade = pygame.Rect(px, 390, bw, 42)
        self._btn_attack  = pygame.Rect(px, 446, bw, 42)
        self._btn_back    = pygame.Rect(px, 502, bw, 42)

        half = (bw - 6) // 2
        self._btn_gold_100  = pygame.Rect(px,            290, half, 34)
        self._btn_gold_500  = pygame.Rect(px + half + 6, 290, half, 34)
        self._btn_elix_100  = pygame.Rect(px,            330, half, 34)
        self._btn_elix_500  = pygame.Rect(px + half + 6, 330, half, 34)

    # ── Helpers de grille ─────────────────────────────────────────────────────

    def _grid_offset(self) -> tuple[int, int]:
        zone_w = SCREEN_WIDTH - self.PANEL_W
        off_x  = (zone_w - GRID_COLS * CELL_SIZE) // 2
        off_y  = (SCREEN_HEIGHT - GRID_ROWS * CELL_SIZE) // 2
        return off_x, off_y

    def _building_rect(self, building) -> pygame.Rect:
        ox, oy = self._grid_offset()
        return pygame.Rect(
            ox + building.col * CELL_SIZE,
            oy + building.row * CELL_SIZE,
            CELL_SIZE * 2, CELL_SIZE * 2,
        )

    def _pixel_to_cell(self, px: int, py: int) -> tuple[int, int]:
        """Convertit des pixels en (col, row) snappé à la grille."""
        ox, oy = self._grid_offset()
        col = (px - ox) // CELL_SIZE
        row = (py - oy) // CELL_SIZE
        return col, row

    def _cell_in_bounds(self, col: int, row: int) -> bool:
        """Vérifie qu'un bâtiment 2×2 tient dans la grille."""
        return 0 <= col <= GRID_COLS - 2 and 0 <= row <= GRID_ROWS - 2

    def _cell_occupied(self, col: int, row: int, exclude_idx: int, all_b: list) -> bool:
        """
        Vérifie si les 4 cellules d'un bâtiment 2×2 sont libres,
        en ignorant le bâtiment lui-même (exclude_idx).
        """
        for c in (col, col + 1):
            for r in (row, row + 1):
                for i, b in enumerate(all_b):
                    if i == exclude_idx:
                        continue
                    # Chaque bâtiment occupe (b.col, b.row), (b.col+1, b.row),
                    # (b.col, b.row+1), (b.col+1, b.row+1)
                    if b.col <= c <= b.col + 1 and b.row <= r <= b.row + 1:
                        return True
        return False

    # ── Événements ────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        team = self.game.active_team

        # ── BOUTON ENFONCÉ ──────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Boutons du panneau (prioritaires)
            if self._btn_back.collidepoint(pos):
                self._cancel_drag()
                self.game.state = GameState.OVERVIEW
                return
            if self._btn_upgrade.collidepoint(pos):
                self._cancel_drag()
                self.game.state = GameState.UPGRADE
                return
            if self._btn_attack.collidepoint(pos):
                self._cancel_drag()
                self.game.state = GameState.ATTACK_SETUP
                return

            # Boutons animateur
            if team:
                eco = Economy(team.village)
                if self._btn_gold_100.collidepoint(pos):
                    eco.award_resources(gold=100); return
                if self._btn_gold_500.collidepoint(pos):
                    eco.award_resources(gold=500); return
                if self._btn_elix_100.collidepoint(pos):
                    eco.award_resources(elixir=100); return
                if self._btn_elix_500.collidepoint(pos):
                    eco.award_resources(elixir=500); return

            # Clic sur la grille : sélection + début de drag
            if team:
                all_b = team.village.all_buildings()
                ox, oy = self._grid_offset()
                grid_zone = pygame.Rect(ox, oy, GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE)
                if grid_zone.collidepoint(pos):
                    for i, b in enumerate(all_b):
                        rect = self._building_rect(b)
                        if rect.collidepoint(pos):
                            self._selected_idx = i
                            # Initialiser le drag
                            self._drag_idx    = i
                            self._drag_mouse  = pos
                            self._drag_offset = (pos[0] - rect.x, pos[1] - rect.y)
                            self._drag_ghost_col = b.col
                            self._drag_ghost_row = b.row
                            self._drag_valid     = True
                            return
                # Clic dans la zone grille mais sur aucun bâtiment
                if grid_zone.collidepoint(pos):
                    self._selected_idx = None

        # ── MOUVEMENT SOURIS (drag en cours) ───────────────────────────────
        elif event.type == pygame.MOUSEMOTION and self._drag_idx is not None:
            self._drag_mouse = event.pos
            mx, my = event.pos
            ox, oy = self._grid_offset()
            # Centre du ghost → snap
            snap_x = mx - self._drag_offset[0]
            snap_y = my - self._drag_offset[1]
            col = (snap_x - ox + CELL_SIZE // 2) // CELL_SIZE
            row = (snap_y - oy + CELL_SIZE // 2) // CELL_SIZE
            self._drag_ghost_col = col
            self._drag_ghost_row = row
            if team:
                all_b = team.village.all_buildings()
                in_bounds = self._cell_in_bounds(col, row)
                occupied  = self._cell_occupied(col, row, self._drag_idx, all_b) if in_bounds else True
                self._drag_valid = in_bounds and not occupied

        # ── BOUTON RELÂCHÉ (dépose) ────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._drag_idx is not None and team:
                if self._drag_valid:
                    all_b = team.village.all_buildings()
                    b = all_b[self._drag_idx]
                    b.col = self._drag_ghost_col
                    b.row = self._drag_ghost_row
            self._drag_idx = None

    def _cancel_drag(self) -> None:
        self._drag_idx = None

    def update(self, dt: float) -> None:
        pass

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        team = self.game.active_team
        if team is None:
            return

        ox, oy     = self._grid_offset()
        sprite_sz  = CELL_SIZE * 2   # 80 px
        all_b      = team.village.all_buildings()

        # ── Grille de fond ──────────────────────────────────────────────────
        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                rect  = pygame.Rect(ox + c * CELL_SIZE, oy + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = (28, 42, 28) if (c + r) % 2 == 0 else (24, 36, 24)
                pygame.draw.rect(surface, color, rect)

        # ── Cellule cible du drag ──────────────────────────────────────────
        if self._drag_idx is not None:
            gc = self._drag_ghost_col
            gr = self._drag_ghost_row
            cell_color = (0, 200, 80, 80) if self._drag_valid else (220, 40, 40, 80)
            overlay    = pygame.Surface((sprite_sz, sprite_sz), pygame.SRCALPHA)
            overlay.fill(cell_color)
            surface.blit(overlay, (ox + gc * CELL_SIZE, oy + gr * CELL_SIZE))

        # ── Bâtiments ──────────────────────────────────────────────────────
        for i, b in enumerate(all_b):
            if i == self._drag_idx:
                continue   # dessiné en ghost plus bas
            rect   = self._building_rect(b)
            sprite = get_building_sprite(b.building_id, sprite_sz, team.color)
            if b.is_destroyed:
                ghost = sprite.copy()
                ghost.fill((180, 60, 60, 160), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(ghost, rect.topleft)
            else:
                surface.blit(sprite, rect.topleft)
            if i == self._selected_idx and self._drag_idx is None:
                pygame.draw.rect(surface, (255, 255, 0), rect, 3, border_radius=4)
            # Barre de vie
            hp_pct = b.current_hp / b.max_hp if b.max_hp > 0 else 0
            bar = pygame.Rect(rect.x, rect.bottom + 2, rect.w, 5)
            pygame.draw.rect(surface, (60, 0, 0), bar, border_radius=2)
            if hp_pct > 0:
                pygame.draw.rect(surface, COLOR_SUCCESS,
                                 pygame.Rect(bar.x, bar.y, max(1, int(bar.w * hp_pct)), 5),
                                 border_radius=2)

        # ── Ghost du bâtiment en cours de déplacement ─────────────────────
        if self._drag_idx is not None:
            b      = all_b[self._drag_idx]
            sprite = get_building_sprite(b.building_id, sprite_sz, team.color)
            ghost  = sprite.copy()
            alpha  = (180, 200, 180, 180) if self._drag_valid else (200, 80, 80, 180)
            ghost.fill(alpha, special_flags=pygame.BLEND_RGBA_MULT)
            gx = ox + self._drag_ghost_col * CELL_SIZE
            gy = oy + self._drag_ghost_row * CELL_SIZE
            surface.blit(ghost, (gx, gy))
            # Indication visuelle "Déposer ici"
            label = "OK" if self._drag_valid else "Invalide"
            lcolor = COLOR_SUCCESS if self._drag_valid else COLOR_DANGER
            self.draw_text(surface, label, gx + sprite_sz // 2, gy - 14,
                           self._font_small, lcolor, center=True)

        # ── Panneau latéral ────────────────────────────────────────────────
        pr = pygame.Rect(SCREEN_WIDTH - self.PANEL_W, 0, self.PANEL_W, SCREEN_HEIGHT)
        self.draw_panel(surface, pr, COLOR_PANEL, border_width=0, radius=0)
        pygame.draw.line(surface, team.color, (pr.x, 0), (pr.x, SCREEN_HEIGHT), 3)

        px_p = pr.x + 18
        self.draw_text(surface, team.name, px_p, 18, self._font_title, team.color)
        self.draw_text(surface, f"Or :    {team.village.resources.gold}",
                       px_p, 64, self._font_info, COLOR_GOLD)
        self.draw_text(surface, f"Élixir : {team.village.resources.elixir}",
                       px_p, 90, self._font_info, COLOR_ELIXIR)
        self.draw_text(surface, f"Étoiles : ⭐ {team.total_stars}",
                       px_p, 116, self._font_info, COLOR_WHITE)
        self.draw_text(surface, f"  Atk {team.attack_stars} + Déf {team.defense_stars}",
                       px_p, 140, self._font_small, (200, 200, 200))

        # Hint drag-and-drop
        hint_y = 160
        pygame.draw.line(surface, (60, 60, 80), (px_p, hint_y), (pr.right - 10, hint_y))
        if self._drag_idx is not None:
            b = all_b[self._drag_idx]
            self.draw_text(surface, f"Déplacement : {b.name}", px_p, hint_y + 6,
                           self._font_small, (255, 220, 80))
            self.draw_text(surface, "Relâchez pour poser", px_p, hint_y + 24,
                           self._font_small, (200, 200, 200))
        elif self._selected_idx is not None and self._selected_idx < len(all_b):
            b = all_b[self._selected_idx]
            self.draw_text(surface, b.name,           px_p, hint_y + 6,  self._font_info, COLOR_WHITE)
            self.draw_text(surface, f"Nv {b.level}  PV {b.current_hp}/{b.max_hp}",
                           px_p, hint_y + 30, self._font_small, (200, 200, 200))
            cost = b.upgrade_cost()
            if cost:
                self.draw_text(surface,
                               f"Améliorer : {cost['gold']} or / {cost['elixir']} élix.",
                               px_p, hint_y + 52, self._font_small, COLOR_GOLD)
            else:
                self.draw_text(surface, "Niveau maximum", px_p, hint_y + 52,
                               self._font_small, COLOR_SUCCESS)
            self.draw_text(surface, "Cliquer-glisser pour déplacer",
                           px_p, hint_y + 74, self._font_small, (140, 140, 140))
        else:
            self.draw_text(surface, "Cliquer un bâtiment pour", px_p, hint_y + 6,
                           self._font_small, (140, 140, 140))
            self.draw_text(surface, "le sélectionner ou le déplacer.", px_p, hint_y + 24,
                           self._font_small, (140, 140, 140))

        # Boutons animateur
        anim_y = 268
        pygame.draw.line(surface, (60, 60, 80), (px_p, anim_y), (pr.right - 10, anim_y))
        self.draw_text(surface, "Animateur – ajouter :", px_p, anim_y + 4,
                       self._font_small, (160, 160, 160))
        for btn, label, color in [
            (self._btn_gold_100,  "+100 Or",    (160, 130, 0)),
            (self._btn_gold_500,  "+500 Or",    (200, 165, 0)),
            (self._btn_elix_100,  "+100 Élix.", (120, 0, 160)),
            (self._btn_elix_500,  "+500 Élix.", (150, 0, 200)),
        ]:
            self.draw_panel(surface, btn, color, border_width=1, radius=6)
            self.draw_text(surface, label, btn.centerx, btn.centery,
                           self._font_small, COLOR_WHITE, center=True)

        # Boutons d'action
        for btn, label, color in [
            (self._btn_upgrade, "Améliorations & Caserne", COLOR_HIGHLIGHT),
            (self._btn_attack,  "⚔ Lancer une attaque",   COLOR_DANGER),
            (self._btn_back,    "← Retour",               COLOR_PANEL),
        ]:
            self.draw_panel(surface, btn, color)
            self.draw_text(surface, label, btn.centerx, btn.centery,
                           self._font_btn, COLOR_WHITE, center=True)


# ── Écran d'amélioration avec scroll ─────────────────────────────────────────

class UpgradeScreen(Screen):
    """
    Deux onglets avec **scroll à la molette** :
      • Onglet 0 "Bâtiments & Défenses"
      • Onglet 1 "Caserne" (améliorer + entraîner)

    La zone de contenu est clippée entre CONTENT_Y et le bas des boutons.
    La molette déplace _scroll_y ; tous les rects tiennent compte de ce décalage.
    """

    ROW_H     = 56
    TROOP_H   = 80
    ICON_SZ   = 40
    CONTENT_Y = 96   # y de départ du contenu visible
    CONTENT_H = SCREEN_HEIGHT - 96 - 70  # hauteur de la zone scrollable
    TAB_BTN_H = 38
    SCROLL_SPD = 40  # pixels par cran de molette

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_title = pygame.font.SysFont("segoeuibold", 28, bold=True)
        self._font_row   = pygame.font.SysFont("segoeui", 19)
        self._font_small = pygame.font.SysFont("segoeui", 15)
        self._font_btn   = pygame.font.SysFont("segoeui", 17)
        self._tab:       int   = 0
        self._scroll_y:  int   = 0   # offset de scroll (positif = on a scrollé vers le bas)
        self._message:   str   = ""
        self._msg_timer: float = 0.0
        self._msg_ok:    bool  = True

        self._btn_back = pygame.Rect(30, SCREEN_HEIGHT - 58, 160, 42)
        tw = (SCREEN_WIDTH - 80) // 2
        self._tab_rects  = [
            pygame.Rect(40,          48, tw, self.TAB_BTN_H),
            pygame.Rect(40 + tw + 4, 48, tw, self.TAB_BTN_H),
        ]
        self._tab_labels = ["Bâtiments & Défenses", "Caserne"]

    # ── Helpers de layout (tiennent compte du scroll) ─────────────────────────

    def _row_y(self, idx: int, row_h: int) -> int:
        """Y absolu (en pixels) de la ligne idx, après application du scroll."""
        return self.CONTENT_Y + idx * row_h - self._scroll_y

    def _building_row_rect(self, idx: int) -> pygame.Rect:
        return pygame.Rect(30, self._row_y(idx, self.ROW_H), SCREEN_WIDTH - 60, self.ROW_H - 4)

    def _building_upgrade_btn(self, idx: int) -> pygame.Rect:
        row = self._building_row_rect(idx)
        return pygame.Rect(row.right - 140, row.y + 10, 128, 34)

    def _troop_row_rect(self, idx: int) -> pygame.Rect:
        return pygame.Rect(30, self._row_y(idx, self.TROOP_H), SCREEN_WIDTH - 60, self.TROOP_H - 4)

    def _troop_upgrade_btn(self, idx: int) -> pygame.Rect:
        row = self._troop_row_rect(idx)
        return pygame.Rect(row.right - 294, row.y + 8, 134, 32)

    def _troop_train1_btn(self, idx: int) -> pygame.Rect:
        row = self._troop_row_rect(idx)
        return pygame.Rect(row.right - 152, row.y + 8, 60, 32)

    def _troop_train5_btn(self, idx: int) -> pygame.Rect:
        row = self._troop_row_rect(idx)
        return pygame.Rect(row.right - 84, row.y + 8, 66, 32)

    def _max_scroll(self, team) -> int:
        """Calcule le scroll maximum selon le contenu de l'onglet actif."""
        if self._tab == 0:
            n = len(team.village.all_buildings())
            total_h = n * self.ROW_H
        else:
            n = len(team.village.troop_types)
            total_h = n * self.TROOP_H
        return max(0, total_h - self.CONTENT_H)

    def _in_content_area(self, pos: tuple[int, int]) -> bool:
        """Vrai si la position est dans la zone scrollable."""
        return self.CONTENT_Y <= pos[1] <= self.CONTENT_Y + self.CONTENT_H

    # ── Événements ────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        team = self.game.active_team

        # Molette de scroll
        if event.type == pygame.MOUSEWHEEL:
            if team:
                self._scroll_y -= event.y * self.SCROLL_SPD
                self._scroll_y  = max(0, min(self._scroll_y, self._max_scroll(team)))
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos

        if self._btn_back.collidepoint(pos):
            self._scroll_y = 0
            self.game.state = GameState.VILLAGE
            return

        # Onglets (réinitialise le scroll)
        for i, tr in enumerate(self._tab_rects):
            if tr.collidepoint(pos):
                if self._tab != i:
                    self._tab      = i
                    self._scroll_y = 0
                return

        if team is None or not self._in_content_area(pos):
            return

        eco = Economy(team.village)

        # ── Onglet 0 : Bâtiments & Défenses ──────────────────────────────
        if self._tab == 0:
            all_b = team.village.all_buildings()
            nb    = len(team.village.buildings)
            for i in range(len(all_b)):
                btn = self._building_upgrade_btn(i)
                if btn.collidepoint(pos):
                    if i < nb:
                        ok, msg = eco.upgrade_building(i)
                    else:
                        ok, msg = self._upgrade_defense(team, i - nb)
                    self._show_message(msg, ok)
                    return

        # ── Onglet 1 : Caserne ────────────────────────────────────────────
        else:
            troop_keys = list(team.village.troop_types.keys())
            for j, tid in enumerate(troop_keys):
                if self._troop_upgrade_btn(j).collidepoint(pos):
                    ok, msg = eco.upgrade_troop(tid)
                    self._show_message(msg, ok)
                    return
                if self._troop_train1_btn(j).collidepoint(pos):
                    ok, msg = eco.train_troop(tid, 1)
                    self._show_message(msg, ok)
                    return
                if self._troop_train5_btn(j).collidepoint(pos):
                    ok, msg = eco.train_troop(tid, 5)
                    self._show_message(msg, ok)
                    return

    def _show_message(self, msg: str, ok: bool) -> None:
        self._message   = msg
        self._msg_timer = 3.5
        self._msg_ok    = ok

    @staticmethod
    def _upgrade_defense(team, defense_idx: int) -> tuple[bool, str]:
        defenses = team.village.defenses
        if defense_idx < 0 or defense_idx >= len(defenses):
            return False, "Défense introuvable."
        d = defenses[defense_idx]
        cost = d.upgrade_cost()
        if cost is None:
            return False, f"{d.name} est déjà au niveau maximum."
        if not team.village.resources.can_afford(cost):
            return False, f"Ressources insuffisantes pour {d.name}."
        team.village.resources.spend(cost)
        d.upgrade()
        return True, f"{d.name} amélioré au niveau {d.level}."

    # ── Mise à jour ───────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._msg_timer > 0:
            self._msg_timer -= dt

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        team = self.game.active_team
        if team is None:
            return

        # En-tête (hors zone scrollable)
        self.draw_text(surface, f"Améliorations – {team.name}",
                       SCREEN_WIDTH // 2, 10, self._font_title, COLOR_WHITE, center=True)
        self.draw_text(surface,
                       f"Or : {team.village.resources.gold}    Élixir : {team.village.resources.elixir}",
                       SCREEN_WIDTH // 2, 34, self._font_small, COLOR_GOLD, center=True)

        # Onglets
        for i, (tr, label) in enumerate(zip(self._tab_rects, self._tab_labels)):
            active = (i == self._tab)
            bg = COLOR_HIGHLIGHT if active else COLOR_PANEL
            self.draw_panel(surface, tr, bg,
                            border_color=team.color if active else (60, 60, 80),
                            border_width=3 if active else 1)
            self.draw_text(surface, label, tr.centerx, tr.centery,
                           self._font_btn, COLOR_WHITE, center=True)

        pygame.draw.line(surface, (60, 60, 80),
                         (30, self.CONTENT_Y - 4), (SCREEN_WIDTH - 30, self.CONTENT_Y - 4))

        # ── Zone scrollable clippée ────────────────────────────────────────
        clip_rect = pygame.Rect(0, self.CONTENT_Y, SCREEN_WIDTH, self.CONTENT_H)
        surface.set_clip(clip_rect)

        if self._tab == 0:
            self._draw_buildings_tab(surface, team)
        else:
            self._draw_caserne_tab(surface, team)

        surface.set_clip(None)  # fin du clipping

        # Indicateur de scroll (barre latérale)
        self._draw_scrollbar(surface, team)

        # Message de feedback
        if self._msg_timer > 0:
            msg_color = COLOR_SUCCESS if self._msg_ok else COLOR_DANGER
            self.draw_text(surface, self._message,
                           SCREEN_WIDTH // 2, SCREEN_HEIGHT - 76,
                           self._font_row, msg_color, center=True)

        # Bouton retour
        self.draw_panel(surface, self._btn_back, COLOR_PANEL)
        self.draw_text(surface, "← Retour",
                       self._btn_back.centerx, self._btn_back.centery,
                       self._font_btn, COLOR_WHITE, center=True)

    def _draw_scrollbar(self, surface: pygame.Surface, team) -> None:
        """Mini barre de défilement sur le bord droit."""
        max_s = self._max_scroll(team)
        if max_s <= 0:
            return
        bar_x  = SCREEN_WIDTH - 12
        bar_y  = self.CONTENT_Y
        bar_h  = self.CONTENT_H
        thumb_h = max(30, int(bar_h * self.CONTENT_H / (self.CONTENT_H + max_s)))
        thumb_y = bar_y + int((bar_h - thumb_h) * self._scroll_y / max_s)
        pygame.draw.rect(surface, (50, 50, 70), pygame.Rect(bar_x, bar_y, 8, bar_h), border_radius=4)
        pygame.draw.rect(surface, (120, 120, 160), pygame.Rect(bar_x, thumb_y, 8, thumb_h), border_radius=4)
        # Hint molette
        self.draw_text(surface, "↕ molette pour défiler",
                       SCREEN_WIDTH // 2, SCREEN_HEIGHT - 54,
                       self._font_small, (100, 100, 130), center=True)

    # ── Onglet 0 : Bâtiments & Défenses ──────────────────────────────────────

    def _draw_buildings_tab(self, surface: pygame.Surface, team) -> None:
        all_b = team.village.all_buildings()
        for i, b in enumerate(all_b):
            row = self._building_row_rect(i)
            # Skip les lignes totalement hors de la zone visible
            if row.bottom < self.CONTENT_Y or row.y > self.CONTENT_Y + self.CONTENT_H:
                continue
            bg = COLOR_PANEL if i % 2 == 0 else (42, 42, 62)
            self.draw_panel(surface, row, bg, border_width=0, radius=6)
            icon = get_building_sprite(b.building_id, self.ICON_SZ, team.color)
            surface.blit(icon, (row.x + 6, row.y + (row.h - self.ICON_SZ) // 2))
            tx = row.x + self.ICON_SZ + 14
            self.draw_text(surface, b.name, tx, row.y + 4, self._font_row, COLOR_WHITE)
            self.draw_text(surface, f"Nv {b.level}  •  PV {b.current_hp}/{b.max_hp}",
                           tx, row.y + 26, self._font_small, (190, 190, 190))
            cost = b.upgrade_cost()
            if cost:
                self.draw_text(surface, f"Or {cost['gold']}  Elix {cost['elixir']}",
                               tx + 200, row.y + 4, self._font_small, COLOR_GOLD)
                btn = self._building_upgrade_btn(i)
                self.draw_panel(surface, btn, COLOR_SUCCESS, radius=6)
                self.draw_text(surface, "Améliorer ↑",
                               btn.centerx, btn.centery, self._font_btn, COLOR_WHITE, center=True)
            else:
                self.draw_text(surface, "NIVEAU MAX",
                               row.right - 100, row.y + 16, self._font_small, COLOR_SUCCESS, center=True)

    # ── Onglet 1 : Caserne ────────────────────────────────────────────────────

    def _draw_caserne_tab(self, surface: pygame.Surface, team) -> None:
        troop_keys = list(team.village.troop_types.keys())
        if not troop_keys:
            self.draw_text(surface, "Aucune troupe débloquée – améliore la Caserne.",
                           SCREEN_WIDTH // 2, self.CONTENT_Y + 40,
                           self._font_row, (180, 180, 180), center=True)
            return
        for j, tid in enumerate(troop_keys):
            tt    = team.village.troop_types[tid]
            count = team.village.army.get(tid, 0)
            row   = self._troop_row_rect(j)
            if row.bottom < self.CONTENT_Y or row.y > self.CONTENT_Y + self.CONTENT_H:
                continue
            bg = COLOR_PANEL if j % 2 == 0 else (42, 38, 58)
            self.draw_panel(surface, row, bg, border_width=0, radius=6)
            icon = get_troop_sprite(tid, self.ICON_SZ + 8, team.color)
            surface.blit(icon, (row.x + 4, row.y + (row.h - self.ICON_SZ - 8) // 2))
            tx = row.x + self.ICON_SZ + 18
            self.draw_text(surface, tt.name, tx, row.y + 4, self._font_row, COLOR_ELIXIR)
            self.draw_text(surface,
                           f"Nv {tt.level}  •  DMG {tt.damage}  PV {tt.hp}  VIT {tt.speed:.1f}",
                           tx, row.y + 27, self._font_small, (190, 190, 190))
            army_color = COLOR_SUCCESS if count > 0 else (120, 120, 120)
            self.draw_text(surface, f"Armée : {count} unité(s)", tx, row.y + 50,
                           self._font_small, army_color)
            # Bouton améliorer
            up_cost = tt.upgrade_cost()
            btn_up  = self._troop_upgrade_btn(j)
            if up_cost is not None:
                self.draw_panel(surface, btn_up, (100, 0, 180), radius=6)
                self.draw_text(surface, f"Nv ↑  {up_cost} élix.",
                               btn_up.centerx, btn_up.centery,
                               self._font_small, COLOR_WHITE, center=True)
            else:
                self.draw_panel(surface, btn_up, (50, 50, 60), radius=6)
                self.draw_text(surface, "Niv. MAX",
                               btn_up.centerx, btn_up.centery,
                               self._font_small, COLOR_SUCCESS, center=True)
            # Boutons entraîner
            train_cost = tt.training_cost
            btn1 = self._troop_train1_btn(j)
            self.draw_panel(surface, btn1, (0, 130, 80), radius=6)
            self.draw_text(surface, "×1",
                           btn1.centerx, btn1.y + 6,  self._font_small, COLOR_WHITE, center=True)
            self.draw_text(surface, f"{train_cost}e",
                           btn1.centerx, btn1.y + 18, self._font_small, COLOR_ELIXIR, center=True)
            btn5 = self._troop_train5_btn(j)
            self.draw_panel(surface, btn5, (0, 100, 60), radius=6)
            self.draw_text(surface, "×5",
                           btn5.centerx, btn5.y + 6,  self._font_small, COLOR_WHITE, center=True)
            self.draw_text(surface, f"{train_cost*5}e",
                           btn5.centerx, btn5.y + 18, self._font_small, COLOR_ELIXIR, center=True)

