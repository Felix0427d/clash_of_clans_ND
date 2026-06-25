"""
attack_screen.py
Écrans de préparation et de combat temps-réel.
"""

from __future__ import annotations
import pygame
from typing import Optional, TYPE_CHECKING

from core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG, COLOR_PANEL, COLOR_HIGHLIGHT,
    COLOR_GOLD, COLOR_ELIXIR, COLOR_WHITE,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_STAR,
    GRID_COLS, GRID_ROWS, CELL_SIZE,
    EMPIRES,
)
from core.game import GameState
from core.sprites import get_building_sprite, get_troop_sprite
from ui.base_screen import Screen

if TYPE_CHECKING:
    from core.game import GameManager
    from core.combat import CombatSession


# ── Écran de préparation d'attaque ────────────────────────────────────────────

class AttackSetupScreen(Screen):
    """
    Sélection de la cible + composition de l'armée avant le combat.
    """

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_title = pygame.font.SysFont("segoeuibold", 30, bold=True)
        self._font_info  = pygame.font.SysFont("segoeui", 20)
        self._font_btn   = pygame.font.SysFont("segoeui", 18)
        self._font_small = pygame.font.SysFont("segoeui", 16)
        self._selected_target: Optional[str] = None  # empire_key de la cible
        self._btn_back  = pygame.Rect(30, SCREEN_HEIGHT - 60, 160, 42)
        self._btn_start = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60, 190, 42)
        self._message: str = ""

    def _target_rect(self, idx: int) -> pygame.Rect:
        x = 60 + idx * 180
        return pygame.Rect(x, 180, 160, 90)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            if self._btn_back.collidepoint(pos):
                self.game.state = GameState.VILLAGE
                return

            if self._btn_start.collidepoint(pos):
                if self._selected_target is None:
                    self._message = "Sélectionne une cible !"
                elif self.game.active_team is None:
                    self._message = "Aucune équipe active."
                else:
                    ok = self.game.start_combat(
                        attacker_key=self.game.active_team.empire_key,
                        defender_key=self._selected_target,
                    )
                    if not ok:
                        self._message = "Impossible de lancer le combat."
                return

            # Sélection de la cible
            eligible = [
                t for t in self.game.teams
                if self.game.active_team and t.empire_key != self.game.active_team.empire_key
            ]
            for i, team in enumerate(eligible):
                if self._target_rect(i).collidepoint(pos):
                    self._selected_target = team.empire_key
                    return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        team = self.game.active_team
        if team is None:
            return

        self.draw_text(surface, f"Attaque – {team.name}",
                       SCREEN_WIDTH // 2, 30, self._font_title, COLOR_WHITE, center=True)
        self.draw_text(surface, "Choisis ta cible :",
                       SCREEN_WIDTH // 2, 140, self._font_info, (200, 200, 200), center=True)

        eligible = [t for t in self.game.teams if t.empire_key != team.empire_key]
        for i, target in enumerate(eligible):
            rect = self._target_rect(i)
            selected = target.empire_key == self._selected_target
            border = (255, 255, 0) if selected else target.color
            bw = 4 if selected else 2
            self.draw_panel(surface, rect, COLOR_PANEL, border_color=border, border_width=bw)
            self.draw_text(surface, target.name[:14], rect.centerx, rect.y + 14,
                           self._font_small, target.color, center=True)
            self.draw_text(surface, f"⭐ {target.total_stars}",
                           rect.centerx, rect.y + 50, self._font_info, COLOR_STAR, center=True)

        # Armée disponible
        self.draw_text(surface, "Armée disponible :",
                       80, 310, self._font_info, (200, 200, 200))
        if team.village.army:
            x = 80
            for tid, count in team.village.army.items():
                tt = team.village.get_troop_type(tid)
                name = tt.name if tt else tid
                self.draw_text(surface, f"{name} ×{count}", x, 342, self._font_small, COLOR_ELIXIR)
                x += 180
        else:
            self.draw_text(surface, "(Aucune troupe entraînée — va dans Améliorations > Entraîner)",
                           80, 342, self._font_small, COLOR_DANGER)

        if self._message:
            self.draw_text(surface, self._message, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                           self._font_info, COLOR_DANGER, center=True)

        # Boutons
        self.draw_panel(surface, self._btn_back, COLOR_PANEL)
        self.draw_text(surface, "← Retour", self._btn_back.centerx, self._btn_back.centery,
                       self._font_btn, COLOR_WHITE, center=True)

        color_start = COLOR_SUCCESS if self._selected_target else (80, 100, 80)
        self.draw_panel(surface, self._btn_start, color_start)
        self.draw_text(surface, "Attaquer ! ⚔",
                       self._btn_start.centerx, self._btn_start.centery,
                       self._font_btn, COLOR_WHITE, center=True)


# ── Écran de combat temps-réel ────────────────────────────────────────────────

class CombatScreen(Screen):
    """
    Affiche le village défenseur sur la grille, les troupes en mouvement,
    le chronomètre et le pourcentage de destruction.

    Interaction : clic gauche sur la grille pour déployer la prochaine troupe.
    """

    PANEL_W = 280

    def __init__(self, game: "GameManager", display: pygame.Surface) -> None:
        super().__init__(game, display)
        self._font_timer  = pygame.font.SysFont("segoeuibold", 36, bold=True)
        self._font_info   = pygame.font.SysFont("segoeui", 20)
        self._font_small  = pygame.font.SysFont("segoeui", 16)
        self._font_btn    = pygame.font.SysFont("segoeui", 18)
        self._selected_troop_id: Optional[str] = None
        self._btn_end     = pygame.Rect(SCREEN_WIDTH - self.PANEL_W + 20,
                                        SCREEN_HEIGHT - 60, self.PANEL_W - 40, 42)
        self._result_displayed = False

    def _grid_offset(self) -> tuple[int, int]:
        zone_w = SCREEN_WIDTH - self.PANEL_W
        off_x = (zone_w - GRID_COLS * CELL_SIZE) // 2
        off_y = (SCREEN_HEIGHT - GRID_ROWS * CELL_SIZE) // 2
        return off_x, off_y

    def _pos_to_cell(self, px: int, py: int) -> tuple[float, float]:
        ox, oy = self._grid_offset()
        col = (px - ox) / CELL_SIZE
        row = (py - oy) / CELL_SIZE
        return col, row

    def _troop_selector_rect(self, idx: int) -> pygame.Rect:
        px = SCREEN_WIDTH - self.PANEL_W + 10
        y  = 100 + idx * 56
        return pygame.Rect(px, y, self.PANEL_W - 20, 48)

    def handle_event(self, event: pygame.event.Event) -> None:
        session: Optional["CombatSession"] = self.game.combat_session
        if session is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Bouton fin de combat
            if self._btn_end.collidepoint(pos):
                self.game.end_combat()
                return

            # Sélection du type de troupe dans le panneau
            troop_keys = list(session.attacker_village.army.keys())
            for i, tid in enumerate(troop_keys):
                if self._troop_selector_rect(i).collidepoint(pos):
                    self._selected_troop_id = tid
                    return

            # Déploiement sur la grille
            ox, oy = self._grid_offset()
            grid_area = pygame.Rect(ox, oy, GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE)
            if grid_area.collidepoint(pos) and self._selected_troop_id:
                col, row = self._pos_to_cell(*pos)
                # Interdit de poser sur un bâtiment (zone 2×2)
                all_b = session._def_buildings + list(session._def_defenses)
                on_building = any(
                    b.col <= col < b.col + 2 and b.row <= row < b.row + 2
                    for b in all_b
                )
                if not on_building:
                    session.deploy_troop(self._selected_troop_id, col, row)

    def update(self, dt: float) -> None:
        session = self.game.combat_session
        if session is None:
            return
        session.update(dt)
        if session.is_over() and not self._result_displayed:
            self._result_displayed = True
            # La fin formelle est déclenchée par le bouton "Terminer"

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        session: Optional["CombatSession"] = self.game.combat_session
        if session is None:
            return

        ox, oy = self._grid_offset()

        # ── Grille ──────────────────────────────────────────────────────────
        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                rect = pygame.Rect(ox + c * CELL_SIZE, oy + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = (28, 42, 28) if (c + r) % 2 == 0 else (24, 36, 24)
                pygame.draw.rect(surface, color, rect)

        # ── Bâtiments défenseurs avec sprites ───────────────────────────────
        def_team = self.game.get_team(session.defender_key)
        def_color = def_team.color if def_team else (120, 120, 120)

        for b in session._def_buildings + list(session._def_defenses):
            rect = pygame.Rect(
                ox + int(b.col) * CELL_SIZE,
                oy + int(b.row) * CELL_SIZE,
                CELL_SIZE * 2, CELL_SIZE * 2,
            )
            sprite = get_building_sprite(b.building_id, CELL_SIZE * 2, def_color)
            if b.is_destroyed:
                ghost = sprite.copy()
                ghost.fill((80, 30, 30, 140), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(ghost, rect.topleft)
            else:
                surface.blit(sprite, rect.topleft)
            # Barre de vie
            hp_pct = b.current_hp / b.max_hp if b.max_hp > 0 else 0
            bar = pygame.Rect(rect.x, rect.y - 6, rect.w, 4)
            pygame.draw.rect(surface, (80, 0, 0), bar)
            if hp_pct > 0:
                pygame.draw.rect(surface, COLOR_SUCCESS,
                                 pygame.Rect(bar.x, bar.y, int(bar.w * hp_pct), 4))

        # ── Projectiles en vol ───────────────────────────────────────────────
        PROJ_COLORS = {
            "cannon":       (200, 200, 80),   # jaune-gris (boulet)
            "archer_tower": (255, 200, 50),   # jaune (flèche)
            "mortar":       (255, 100, 30),   # orange (obus)
        }
        for proj in session.projectiles:
            px_p = int(ox + proj.col * CELL_SIZE)
            py_p = int(oy + proj.row * CELL_SIZE)
            pdx  = int(ox + proj.dest_col * CELL_SIZE)
            pdy  = int(oy + proj.dest_row * CELL_SIZE)
            pc   = PROJ_COLORS.get(proj.def_id, (220, 220, 220))
            r    = 5 if proj.def_id == "cannon" else (4 if proj.def_id == "mortar" else 3)
            # Traînée
            pygame.draw.line(surface, (pc[0]//2, pc[1]//2, pc[2]//2), (px_p, py_p), (pdx, pdy), 1)
            # Boulet / flèche
            pygame.draw.circle(surface, pc, (px_p, py_p), r)
            pygame.draw.circle(surface, COLOR_WHITE, (px_p, py_p), r, 1)

        # ── Troupes attaquantes ──────────────────────────────────────────────
        atk_team = self.game.get_team(session.attacker_key)
        troop_color = atk_team.color if atk_team else COLOR_WHITE
        for troop in session.troops:
            if not troop.is_alive:
                continue
            tx = int(ox + troop.col * CELL_SIZE)
            ty = int(oy + troop.row * CELL_SIZE)
            pygame.draw.circle(surface, troop_color, (tx, ty), CELL_SIZE // 3)
            pygame.draw.circle(surface, COLOR_WHITE, (tx, ty), CELL_SIZE // 3, 1)
            # HP troupe
            hp_pct = troop.current_hp / troop.troop_type.hp
            pygame.draw.rect(surface, (80, 0, 0), pygame.Rect(tx - 10, ty - 16, 20, 3))
            pygame.draw.rect(surface, COLOR_SUCCESS,
                             pygame.Rect(tx - 10, ty - 16, int(20 * hp_pct), 3))

        # ── Panneau latéral ──────────────────────────────────────────────────
        panel_rect = pygame.Rect(SCREEN_WIDTH - self.PANEL_W, 0, self.PANEL_W, SCREEN_HEIGHT)
        self.draw_panel(surface, panel_rect, COLOR_PANEL, radius=0)

        px = panel_rect.x + 14

        # Chronomètre
        remaining = max(0, session.time_left)
        mins = int(remaining) // 60
        secs = int(remaining) % 60
        timer_color = COLOR_DANGER if remaining < 30 else COLOR_WHITE
        self.draw_text(surface, f"{mins}:{secs:02d}", px + 60, 20,
                       self._font_timer, timer_color, center=True)

        # Destruction
        pct = session.destruction_percentage()
        self.draw_text(surface, f"Destruction : {pct*100:.1f}%",
                       px, 72, self._font_info, COLOR_WHITE)

        # Étoiles estimées
        hq_dead = any(b.building_id == "headquarters" and b.is_destroyed
                      for b in session._def_buildings)
        if pct >= 1.0:
            est_stars = 3
        elif pct >= 0.5 and hq_dead:
            est_stars = 2
        elif hq_dead:
            est_stars = 1
        else:
            est_stars = 0
        self.draw_text(surface, "Étoiles :", px, 98, self._font_small, (200, 200, 200))
        self.draw_stars(surface, px + 80, 100, est_stars, max_stars=3, size=16)

        # Sélecteur de troupes avec icônes sprites
        self.draw_text(surface, "Troupes à déployer :", px, 155, self._font_small, (200, 200, 200))
        troop_keys = list(session.attacker_village.army.keys())
        for i, tid in enumerate(troop_keys):
            count = session._army_pool.get(tid, 0)
            tt = session.attacker_village.get_troop_type(tid)
            name = tt.name if tt else tid
            btn_rect = self._troop_selector_rect(i)
            selected = self._selected_troop_id == tid
            bg = COLOR_HIGHLIGHT if selected else (50, 40, 70)
            self.draw_panel(surface, btn_rect, bg,
                            border_color=(255, 255, 0) if selected else (80, 80, 120))
            # Icône troupe
            icon = get_troop_sprite(tid, 36, atk_team.color if atk_team else (150, 150, 200))
            surface.blit(icon, (btn_rect.x + 4, btn_rect.y + (btn_rect.h - 36) // 2))
            self.draw_text(surface, name, btn_rect.x + 44, btn_rect.y + 6,
                           self._font_small, COLOR_ELIXIR)
            self.draw_text(surface, f"×{count}", btn_rect.x + 44, btn_rect.y + 24,
                           self._font_small, COLOR_WHITE if count > 0 else COLOR_DANGER)

        # Bouton terminer
        end_label = "Terminer le combat" if session.is_over() else "Abandonner"
        end_color = COLOR_SUCCESS if session.is_over() else COLOR_DANGER
        self.draw_panel(surface, self._btn_end, end_color)
        self.draw_text(surface, end_label, self._btn_end.centerx, self._btn_end.centery,
                       self._font_btn, COLOR_WHITE, center=True)
