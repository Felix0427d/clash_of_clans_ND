"""
main.py
Point d'entrée du jeu « Camp Napoléon – Clash of Clans ».

Lancement :
    python main.py

Dépendance :
    pip install pygame-ce
"""

import sys
import pygame

from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, COLOR_BG
from core.game import GameManager, GameState
from ui.menus import MainMenuScreen, OverviewScreen, ResultsScreen
from ui.village_screen import VillageScreen, UpgradeScreen
from ui.attack_screen import AttackSetupScreen, CombatScreen
from ui.recap_screen import DaySummaryScreen


def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    game = GameManager()

    # ── Police pour le titre permanent ───────────────────────────────────────
    _font_title = pygame.font.SysFont("segoeuibold", 22, bold=True)
    _TITLE_H    = 28  # hauteur réservée en haut (px)


    screens: dict[str, object] = {
        GameState.MAIN_MENU:    MainMenuScreen(game, screen),
        GameState.OVERVIEW:     OverviewScreen(game, screen),
        GameState.VILLAGE:      VillageScreen(game, screen),
        GameState.UPGRADE:      UpgradeScreen(game, screen),
        GameState.ATTACK_SETUP: AttackSetupScreen(game, screen),
        GameState.COMBAT:       CombatScreen(game, screen),
        GameState.DAY_SUMMARY:  DaySummaryScreen(game, screen),
        GameState.RESULTS:      ResultsScreen(game, screen),
    }

    # ── Boucle principale ─────────────────────────────────────────────────────
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # secondes

        current_screen = screens.get(game.state)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif current_screen:
                current_screen.handle_event(event)

        if current_screen:
            current_screen.update(dt)
            current_screen.draw(screen)

        # ── Bandeau "Clash of ND" en haut de chaque écran ────────────────────
        banner_surf = pygame.Surface((SCREEN_WIDTH, _TITLE_H), pygame.SRCALPHA)
        banner_surf.fill((0, 0, 0, 160))
        screen.blit(banner_surf, (0, 0))
        title_img = _font_title.render("⚔  Clash of ND  ⚔", True, (255, 215, 0))
        screen.blit(title_img, title_img.get_rect(center=(SCREEN_WIDTH // 2, _TITLE_H // 2)))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

