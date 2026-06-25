"""
constants.py
Constantes globales du jeu : couleurs, dimensions, config.
"""

from typing import Final

# ── Fenêtre ─────────────────────────────────────────────────────────────────
SCREEN_WIDTH:  Final[int] = 1280
SCREEN_HEIGHT: Final[int] = 720
FPS:           Final[int] = 60
TITLE:         Final[str] = "Camp Napoléon – Clash of Clans"

# ── Durée d'une attaque (secondes) ──────────────────────────────────────────
ATTACK_DURATION: Final[int] = 120  # 2 minutes

# ── Durée du camp (jours) ───────────────────────────────────────────────────
CAMP_DAYS: Final[int] = 10

# ── Empires napoléoniens ─────────────────────────────────────────────────────
# Chaque clé correspond à une équipe (sizaine)
EMPIRES: Final[dict] = {
    "rouge":  {"name": "Empire britannique",         "color": (200,  50,  50)},
    "vert":   {"name": "Empire russe",               "color": ( 60, 160,  60)},
    "bleu":   {"name": "Empire d'Autriche-Hongrie",  "color": ( 50,  80, 200)},
    "jaune":  {"name": "Empire prussien",            "color": (220, 200,  30)},
    "gris":   {"name": "Empire ottoman",             "color": (140, 140, 140)},
    "noir":   {"name": "Empire espagnol",            "color": ( 30,  30,  30)},
}

# ── Palette UI ───────────────────────────────────────────────────────────────
COLOR_BG:         Final = ( 20,  20,  35)
COLOR_PANEL:      Final = ( 35,  35,  55)
COLOR_HIGHLIGHT:  Final = ( 80,  80, 130)
COLOR_GOLD:       Final = (255, 215,   0)
COLOR_ELIXIR:     Final = (180,   0, 255)
COLOR_WHITE:      Final = (255, 255, 255)
COLOR_TEXT_DARK:  Final = ( 15,  15,  25)
COLOR_SUCCESS:    Final = ( 50, 200,  80)
COLOR_DANGER:     Final = (220,  60,  60)
COLOR_STAR:       Final = (255, 215,   0)

# ── Grille de village (cellules en pixels) ────────────────────────────────────
GRID_COLS: Final[int] = 20
GRID_ROWS: Final[int] = 15
CELL_SIZE: Final[int] = 40  # px

# ── Niveaux maximaux ─────────────────────────────────────────────────────────
MAX_BUILDING_LEVEL: Final[int] = 5
MAX_TROOP_LEVEL:    Final[int] = 5
MAX_WALL_LEVEL:     Final[int] = 5
