"""
sprites.py
Génère dynamiquement les sprites de bâtiments et de troupes avec pygame.draw.
Aucune image externe requise — tout est dessiné par code.

Usage :
    from core.sprites import get_building_sprite, get_troop_sprite
    surf = get_building_sprite("headquarters", size=80, team_color=(200, 50, 50))
    surf = get_troop_sprite("soldier", size=48, team_color=(200, 50, 50))
"""

from __future__ import annotations
import math
import pygame

# ── Cache ─────────────────────────────────────────────────────────────────────
_cache: dict[str, pygame.Surface] = {}


def get_building_sprite(
    building_id: str,
    size: int = 80,
    team_color: tuple = (100, 100, 120),
) -> pygame.Surface:
    """Retourne la surface du bâtiment, générée et mise en cache."""
    r, g, b = int(team_color[0]), int(team_color[1]), int(team_color[2])
    key = f"b_{building_id}_{size}_{r}_{g}_{b}"
    if key not in _cache:
        _cache[key] = _render_building(building_id, size, (r, g, b))
    return _cache[key]


def get_troop_sprite(
    troop_id: str,
    size: int = 48,
    team_color: tuple = (100, 100, 120),
) -> pygame.Surface:
    """Retourne la surface de la troupe, générée et mise en cache."""
    r, g, b = int(team_color[0]), int(team_color[1]), int(team_color[2])
    key = f"t_{troop_id}_{size}_{r}_{g}_{b}"
    if key not in _cache:
        _cache[key] = _render_troop(troop_id, size, (r, g, b))
    return _cache[key]


def clear_cache() -> None:
    """Vide le cache (utile lors d'un changement d'équipe)."""
    _cache.clear()


# ── Palettes ──────────────────────────────────────────────────────────────────
STONE  = (110, 100, 90)
STONE2 = (88,  80,  72)
DARK   = (38,  30,  22)
WOOD   = (120, 85,  50)
EARTH  = (90,  65,  38)
GRASS  = (52,  80,  42)
GOLD   = (255, 210,  10)
ELIXIR = (200,  70, 255)
STEEL  = (80,   80,  90)
CREAM  = (240, 235, 220)
SKY    = (72,  82,  92)


# ─────────────────────────────────────────────────────────────────────────────
# BÂTIMENTS
# ─────────────────────────────────────────────────────────────────────────────

def _render_building(bid: str, s: int, tc: tuple) -> pygame.Surface:
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    {
        "headquarters": _hq,
        "gold_mine":    _gold_mine,
        "elixir_mine":  _elixir_mine,
        "wall":         _wall,
        "barracks":     _barracks,
        "cannon":       _cannon,
        "archer_tower": _archer_tower,
        "mortar":       _mortar,
    }.get(bid, _generic_building)(surf, s, tc)
    return surf


def _hq(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Quartier Général – château-fort napoléonien."""
    surf.fill(STONE)
    lw = max(4, s // 6)

    # Tours latérales
    pygame.draw.rect(surf, STONE2, (2, s // 3, lw, s * 2 // 3))
    pygame.draw.rect(surf, STONE2, (s - lw - 2, s // 3, lw, s * 2 // 3))

    # Corps central
    kx, ky, kw = s // 4, s // 5, s // 2
    pygame.draw.rect(surf, STONE2, (kx, ky, kw, s - ky))

    # Porte arquée
    dw = max(4, s // 5)
    dx = s // 2 - dw // 2
    pygame.draw.rect(surf, DARK, (dx, s - s // 3, dw, s // 3 + 2))
    pygame.draw.circle(surf, DARK, (s // 2, s - s // 3), dw // 2)

    # Fenêtre
    pygame.draw.rect(surf, (220, 195, 120, 200), (s // 2 - 3, s * 2 // 5, 6, 9))

    # Créneaux keep
    ch = max(3, s // 12)
    for i in range(3):
        cx = kx + 4 + i * (kw // 3)
        pygame.draw.rect(surf, STONE2, (cx, ky - ch, max(3, kw // 7), ch))

    # Créneaux tours
    pygame.draw.rect(surf, STONE2, (2, s // 3 - ch, lw, ch))
    pygame.draw.rect(surf, STONE2, (s - lw - 2, s // 3 - ch, lw, ch))

    # Mât + drapeau couleur équipe
    mt = max(0, ky - ch - 2)
    mx = s // 2
    pygame.draw.line(surf, CREAM, (mx, ky - ch), (mx, mt), 2)
    fw = min(14, s // 5)
    fh = min(8,  s // 10)
    pygame.draw.polygon(surf, tc, [(mx, mt), (mx + fw, mt + fh // 2), (mx, mt + fh)])

    pygame.draw.rect(surf, DARK, (0, 0, s, s), 2)


def _gold_mine(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Mine d'or – colline brune avec pépites dorées."""
    surf.fill(EARTH)
    pts = [(0, s), (s // 5, s // 2), (s // 2, s // 4), (4 * s // 5, s // 2), (s, s)]
    pygame.draw.polygon(surf, (72, 52, 30), pts)

    # Entrée
    ew = s // 3
    ex = s // 2 - ew // 2
    ey = s // 2
    pygame.draw.rect(surf, DARK, (ex, ey, ew, s // 4))
    pygame.draw.circle(surf, DARK, (s // 2, ey), ew // 2)

    # Pépites
    for gx, gy, gr in [(s//5, s*3//5, 5), (3*s//4, s//2, 5), (s//3, 3*s//4, 6), (2*s//3, 2*s//3, 4)]:
        pygame.draw.circle(surf, GOLD, (gx, gy), gr)
        pygame.draw.circle(surf, (255, 240, 100), (gx - 1, gy - 1), max(1, gr - 2))

    # Badge "OR"
    pygame.draw.rect(surf, (200, 160, 0), (3, 3, 22, 13), border_radius=3)
    pygame.draw.rect(surf, DARK, (3, 3, 22, 13), 1, border_radius=3)

    pygame.draw.rect(surf, (55, 38, 20), (0, 0, s, s), 2)


def _elixir_mine(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Mine d'élixir – grande fiole violette."""
    surf.fill((50, 20, 68))

    # Corps
    bx, by, bw, bh = s // 3, s // 3, s // 3, s // 2
    pygame.draw.rect(surf, (130, 40, 195), (bx, by, bw, bh), border_radius=8)

    # Liquide
    pygame.draw.rect(surf, (220, 90, 255, 220),
                     pygame.Rect(bx + 3, by + bh // 3, bw - 6, bh * 2 // 3 - 2),
                     border_radius=6)

    # Col + bouchon
    nw = bw // 2
    nx = s // 2 - nw // 2
    pygame.draw.rect(surf, (155, 65, 220), (nx, s // 5, nw, s // 7))
    pygame.draw.rect(surf, (200, 200, 210), (nx + 1, s // 5 - 4, nw - 2, 6), border_radius=2)

    # Bulles
    for px, py, pr in [(bx + 5, by + bh - 8, 3), (bx + bw - 6, by + bh - 14, 2)]:
        pygame.draw.circle(surf, (230, 160, 255, 180), (px, py), pr)

    # Étoiles
    for ex, ey in [(s // 7, s // 4), (5 * s // 6, s // 3)]:
        pygame.draw.circle(surf, (255, 200, 255), (ex, ey), 2)

    pygame.draw.rect(surf, (180, 80, 240), (0, 0, s, s), 2)


def _wall(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Remparts – mur de pierres à créneaux."""
    surf.fill((135, 125, 112))

    bh = max(4, s // 6)
    bw = max(8, s // 4)
    colors = [(120, 110, 98), (108, 98, 86)]
    for row in range(s // bh + 2):
        off = (row % 2) * (bw // 2)
        y = row * bh
        for col in range(-1, s // bw + 2):
            rx = col * bw + off
            rect = pygame.Rect(rx + 1, y + 1, bw - 2, bh - 2)
            if rect.right > 0 and rect.left < s:
                pygame.draw.rect(surf, colors[row % 2], rect)

    # Créneaux
    nb = max(2, s // 20)
    cw = max(4, s // (nb * 2))
    ch = max(3, s // 10)
    gap = (s - nb * cw) // (nb + 1)
    for i in range(nb):
        pygame.draw.rect(surf, (150, 140, 126), (gap + i * (cw + gap), 0, cw, ch))

    # Bandeau couleur équipe
    pygame.draw.rect(surf, tc, (0, 0, s, 3))
    pygame.draw.rect(surf, (60, 54, 46), (0, 0, s, s), 2)


def _barracks(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Caserne – bâtiment militaire avec épées croisées."""
    surf.fill(GRASS)

    # Bâtiment
    bx, by, bw = s // 6, s // 3, s * 2 // 3
    bh = s * 2 // 3
    pygame.draw.rect(surf, WOOD, (bx, by, bw, bh))

    # Toit
    pygame.draw.polygon(surf, (85, 58, 32), [(s // 10, by), (s // 2, s // 8), (9 * s // 10, by)])

    # Porte
    dw = max(4, s // 5)
    dx = s // 2 - dw // 2
    pygame.draw.rect(surf, DARK, (dx, by + bh - s // 3, dw, s // 3 + 2))
    pygame.draw.circle(surf, DARK, (s // 2, by + bh - s // 3), dw // 2)

    # Épées croisées
    cx, cy = s // 2, s // 2
    sw = max(2, s // 28)
    pygame.draw.line(surf, (215, 215, 225), (cx - s//7, cy + s//7), (cx + s//7, cy - s//7), sw)
    pygame.draw.line(surf, (185, 160, 100), (cx - s//10, cy - s//10), (cx, cy), sw + 1)
    pygame.draw.line(surf, (215, 215, 225), (cx + s//7, cy + s//7), (cx - s//7, cy - s//7), sw)
    pygame.draw.line(surf, (185, 160, 100), (cx + s//10, cy - s//10), (cx, cy), sw + 1)

    # Drapeau
    mt = max(0, s // 8 - 4)
    mx = s // 2
    pygame.draw.line(surf, CREAM, (mx, s // 8), (mx, mt), 2)
    fw, fh = min(12, s // 6), min(7, s // 10)
    pygame.draw.polygon(surf, tc, [(mx, mt), (mx + fw, mt + fh // 2), (mx, mt + fh)])

    pygame.draw.rect(surf, (38, 28, 18), (0, 0, s, s), 2)


def _cannon(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Canon défensif sur roues."""
    surf.fill((82, 82, 86))

    # Base
    pygame.draw.rect(surf, (98, 92, 84), (s // 6, s // 2, s * 2 // 3, s // 3))
    pygame.draw.rect(surf, (72, 68, 60), (s // 6, s // 2, s * 2 // 3, s // 3), 2)

    # Roues avec rayons
    rr = max(5, s // 8)
    for rx_w in [s // 4, 3 * s // 4]:
        ry_w = 3 * s // 4
        pygame.draw.circle(surf, (60, 55, 48), (rx_w, ry_w), rr)
        pygame.draw.circle(surf, (40, 36, 30), (rx_w, ry_w), rr, 2)
        for angle in range(0, 360, 90):
            rad = math.radians(angle)
            pygame.draw.line(surf, (50, 45, 38), (rx_w, ry_w),
                             (rx_w + int(rr * 0.7 * math.cos(rad)),
                              ry_w + int(rr * 0.7 * math.sin(rad))), 1)

    # Affût + bouche
    pygame.draw.rect(surf, (55, 55, 62), (s // 4, s // 3, s // 2, s // 4), border_radius=4)
    pygame.draw.rect(surf, (38, 38, 44), (s // 2, s // 3 + 2, s // 3, s // 4 - 4), border_radius=3)

    # Boulet
    pygame.draw.circle(surf, (35, 35, 42), (s // 5, s // 3 - 2), max(3, s // 10))

    pygame.draw.rect(surf, (50, 50, 55), (0, 0, s, s), 2)


def _archer_tower(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Tour d'archers avec meurtrières."""
    surf.fill(SKY)

    tx, ty, tw = s // 4, s // 6, s // 2
    pygame.draw.rect(surf, (92, 102, 112), (tx, ty, tw, s - ty))

    # Créneaux
    nb, ch = 3, max(3, s // 10)
    cw = max(3, tw // (nb * 2))
    gap = (tw - nb * cw) // (nb + 1)
    for i in range(nb):
        cx = tx + gap + i * (cw + gap)
        pygame.draw.rect(surf, (105, 115, 125), (cx, ty - ch, cw, ch))

    # Meurtrières (croix)
    sc = (32, 32, 38)
    for my in [s // 3, s // 2]:
        pygame.draw.rect(surf, sc, (s // 2 - 2, my, 4, 10))
        pygame.draw.rect(surf, sc, (s // 2 - 5, my + 3, 10, 4))

    # Flèche
    ax, ay = 3 * s // 4 + 4, 5 * s // 12
    pygame.draw.line(surf, (190, 175, 140), (s // 2 + 4, ay), (ax, ay), 2)
    arw = max(5, s // 12)
    pygame.draw.polygon(surf, (190, 175, 140),
                        [(ax, ay), (ax - arw, ay - arw // 2), (ax - arw, ay + arw // 2)])

    # Drapeau
    mt = max(0, ty - ch - 2)
    mx = s // 2
    pygame.draw.line(surf, CREAM, (mx, ty - ch), (mx, mt), 2)
    fw, fh = min(12, s // 6), min(7, s // 10)
    pygame.draw.polygon(surf, tc, [(mx, mt), (mx + fw, mt + fh // 2), (mx, mt + fh)])

    pygame.draw.rect(surf, (52, 62, 70), (0, 0, s, s), 2)


def _mortar(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Mortier – obusier court à tir vertical."""
    surf.fill((78, 78, 76))

    # Base circulaire
    cx, cy = s // 2, 2 * s // 3
    pygame.draw.circle(surf, (102, 96, 86), (cx, cy), s // 3)
    pygame.draw.circle(surf, (78, 73, 65), (cx, cy), s // 3, 2)

    # Plateforme
    pygame.draw.rect(surf, (90, 85, 75), (s // 4, s // 2, s // 2, s // 8))

    # Canon vertical court
    bw = max(4, s // 5)
    bx, by = s // 2 - bw // 2, s // 6
    bh = s // 3
    pygame.draw.rect(surf, STEEL, (bx, by, bw, bh), border_radius=4)
    pygame.draw.rect(surf, (42, 42, 48), (bx - 2, by, bw + 4, s // 10), border_radius=3)

    # Boulet en l'air + traînée
    ball_y = max(4, by - 8)
    pygame.draw.circle(surf, (35, 35, 42), (s // 2, ball_y), max(4, s // 10))
    pygame.draw.line(surf, (150, 130, 100), (s // 2, ball_y + 4), (s // 2, by + 2), 2)

    # Pierres décoratives
    for px, py in [(s // 5, 3 * s // 4), (3 * s // 4, 3 * s // 4)]:
        pygame.draw.circle(surf, (42, 42, 48), (px, py), max(3, s // 14))

    pygame.draw.rect(surf, (52, 52, 50), (0, 0, s, s), 2)


def _generic_building(surf: pygame.Surface, s: int, tc: tuple) -> None:
    surf.fill((78, 78, 86))
    pygame.draw.rect(surf, tc, (s // 4, s // 4, s // 2, s // 2), border_radius=4)
    pygame.draw.rect(surf, (55, 55, 62), (0, 0, s, s), 2)


# ─────────────────────────────────────────────────────────────────────────────
# TROUPES
# ─────────────────────────────────────────────────────────────────────────────

def _render_troop(troop_id: str, s: int, tc: tuple) -> pygame.Surface:
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    {
        "soldier":     _troop_soldier,
        "archer":      _troop_archer,
        "grenadier":   _troop_grenadier,
        "cannon_cart": _troop_cannon_cart,
    }.get(troop_id, _troop_generic)(surf, s, tc)
    return surf


def _troop_soldier(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Soldat napoléonien – uniforme couleur équipe, shako noir, mousquet."""
    cx = s // 2

    # Fond transparent
    # Jambes
    lg = max(2, s // 10)
    pygame.draw.rect(surf, (50, 40, 60), (cx - lg - 1, s * 3 // 5, lg, s * 2 // 5))
    pygame.draw.rect(surf, (50, 40, 60), (cx + 1, s * 3 // 5, lg, s * 2 // 5))

    # Corps (uniforme)
    bw = max(6, s // 3)
    by = s * 2 // 5
    bh = s // 4
    pygame.draw.rect(surf, tc, (cx - bw // 2, by, bw, bh), border_radius=2)

    # Ceinture
    belt_y = by + bh - 2
    pygame.draw.rect(surf, (180, 155, 90), (cx - bw // 2, belt_y, bw, 3))

    # Tête
    hr = max(4, s // 7)
    hy = s // 5
    pygame.draw.circle(surf, (210, 175, 130), (cx, hy), hr)

    # Shako (chapeau cylindrique)
    sh = max(3, s // 8)
    sw = max(5, s // 5)
    pygame.draw.rect(surf, (25, 22, 20), (cx - sw // 2, hy - hr - sh, sw, sh))
    pygame.draw.rect(surf, (35, 30, 28), (cx - sw // 2 - 2, hy - hr - 2, sw + 4, 4))

    # Cocarde
    pygame.draw.circle(surf, tc, (cx + sw // 2 - 3, hy - hr - sh + 3), 2)

    # Mousquet (ligne diagonale droite)
    ml = max(8, s // 3)
    pygame.draw.line(surf, (160, 130, 90), (cx + bw // 2, by), (cx + bw // 2 + ml // 3, by - ml), 2)
    pygame.draw.circle(surf, (80, 75, 70), (cx + bw // 2 + ml // 3, by - ml), 2)

    pygame.draw.rect(surf, (40, 40, 50, 80), (0, 0, s, s), 1)


def _troop_archer(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Fusilier/tirailleur napoléonien – tenue verte, arc."""
    cx = s // 2

    # Jambes
    lg = max(2, s // 10)
    pygame.draw.rect(surf, (40, 55, 35), (cx - lg - 1, s * 3 // 5, lg, s * 2 // 5))
    pygame.draw.rect(surf, (40, 55, 35), (cx + 1, s * 3 // 5, lg, s * 2 // 5))

    # Corps (tenue tirailleur – vert foncé)
    bw = max(6, s // 3)
    by = s * 2 // 5
    bh = s // 4
    body_color = (60, 95, 50) if tc == (0, 0, 0) else tc
    # Fond vert tirailleur + accent équipe
    pygame.draw.rect(surf, (55, 85, 45), (cx - bw // 2, by, bw, bh), border_radius=2)
    pygame.draw.rect(surf, tc, (cx - bw // 2, by, 3, bh), border_radius=2)

    # Tête
    hr = max(4, s // 7)
    hy = s // 5
    pygame.draw.circle(surf, (210, 175, 130), (cx, hy), hr)

    # Bonnet de police (petite casquette)
    pygame.draw.rect(surf, (50, 70, 40), (cx - hr, hy - hr - 3, hr * 2, 5))
    pygame.draw.rect(surf, (40, 58, 32), (cx - hr + 1, hy - hr - 6, hr * 2 - 2, 4))

    # Arc (arc courbe avec pygame.draw.arc)
    arc_rect = pygame.Rect(cx - bw // 2 - s // 6, by - s // 8, s // 4, s // 2)
    pygame.draw.arc(surf, (160, 120, 70), arc_rect, math.radians(-60), math.radians(240), 2)

    # Corde de l'arc
    pygame.draw.line(surf, (220, 205, 180),
                     (cx - bw // 2 - 2, by - s // 8 + s // 6),
                     (cx - bw // 2 - 2, by + s // 3), 1)

    # Flèche
    pygame.draw.line(surf, (170, 140, 90),
                     (cx - bw // 2 + 2, by + s // 12),
                     (cx + bw, by + s // 12), 2)
    pygame.draw.polygon(surf, (190, 165, 110), [
        (cx + bw, by + s // 12),
        (cx + bw - 4, by + s // 12 - 3),
        (cx + bw - 4, by + s // 12 + 3),
    ])

    pygame.draw.rect(surf, (40, 40, 50, 80), (0, 0, s, s), 1)


def _troop_grenadier(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Grenadier à pied – bonnet d'ourson, grenade."""
    cx = s // 2

    # Jambes (larges)
    lg = max(3, s // 8)
    pygame.draw.rect(surf, (50, 40, 55), (cx - lg - 1, s * 3 // 5, lg, s * 2 // 5))
    pygame.draw.rect(surf, (50, 40, 55), (cx + 1, s * 3 // 5, lg, s * 2 // 5))

    # Corps (plus large – grenadier costaud)
    bw = max(8, s * 2 // 5)
    by = s * 2 // 5
    bh = s // 4
    pygame.draw.rect(surf, tc, (cx - bw // 2, by, bw, bh), border_radius=2)

    # Bandoulière blanche
    pygame.draw.line(surf, CREAM,
                     (cx - bw // 2, by + 2),
                     (cx + bw // 2, by + bh - 2), 2)

    # Tête
    hr = max(5, s // 6)
    hy = s // 5
    pygame.draw.circle(surf, (210, 175, 130), (cx, hy), hr)

    # Bonnet d'ourson (toque haute noire)
    bh2 = max(6, s // 5)
    bw2 = max(6, hr * 2 + 2)
    pygame.draw.rect(surf, (20, 18, 16), (cx - bw2 // 2, hy - hr - bh2, bw2, bh2))
    # Plaque de métal sur le bonnet
    pygame.draw.rect(surf, (180, 160, 80), (cx - bw2 // 2, hy - hr - bh2, bw2, 4))

    # Grenade dans la main (cercle orange avec mèche)
    gx, gy = cx + bw // 2 + 2, by + bh // 2
    gr_r = max(3, s // 10)
    pygame.draw.circle(surf, (200, 100, 30), (gx, gy), gr_r)
    pygame.draw.circle(surf, (220, 130, 50), (gx - 1, gy - 1), max(1, gr_r - 2))
    pygame.draw.line(surf, (255, 200, 50), (gx, gy - gr_r), (gx + 3, gy - gr_r - 5), 2)

    pygame.draw.rect(surf, (40, 40, 50, 80), (0, 0, s, s), 1)


def _troop_cannon_cart(surf: pygame.Surface, s: int, tc: tuple) -> None:
    """Canon roulant d'artillerie de campagne."""
    # Fond
    surf.fill((0, 0, 0, 0))

    # Roues grandes
    rr = max(6, s // 4)
    for rx in [s // 4, 3 * s // 4]:
        ry = 3 * s // 4
        pygame.draw.circle(surf, (70, 60, 48), (rx, ry), rr)
        pygame.draw.circle(surf, (45, 38, 28), (rx, ry), rr, 3)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            pygame.draw.line(surf, (55, 46, 35), (rx, ry),
                             (rx + int(rr * 0.8 * math.cos(rad)),
                              ry + int(rr * 0.8 * math.sin(rad))), 1)

    # Affût (bois)
    pygame.draw.rect(surf, (110, 80, 45), (s // 5, s // 2, s * 3 // 5, s // 6))

    # Corps du canon
    cannon_y = s // 3
    cannon_h = s // 5
    pygame.draw.rect(surf, (55, 55, 62), (s // 4, cannon_y, s // 2, cannon_h), border_radius=5)

    # Bouche
    mouth_w = max(4, s // 4)
    pygame.draw.rect(surf, (38, 38, 45),
                     (s // 2, cannon_y + 2, mouth_w, cannon_h - 4), border_radius=3)

    # Bandeau couleur équipe
    pygame.draw.rect(surf, tc, (s // 4, cannon_y, s // 2, 4), border_radius=3)

    # Boulet
    pygame.draw.circle(surf, (35, 35, 42), (s // 6, cannon_y - 2), max(3, s // 10))

    # Servants (2 petites silhouettes derrière)
    for srv_x in [s // 6, s * 5 // 6]:
        sh = max(4, s // 5)
        pygame.draw.circle(surf, (190, 160, 120), (srv_x, s // 3 - sh // 2), max(2, s // 14))
        pygame.draw.rect(surf, tc, (srv_x - 2, s // 3, 4, sh // 2))

    pygame.draw.rect(surf, (40, 40, 50, 80), (0, 0, s, s), 1)


def _troop_generic(surf: pygame.Surface, s: int, tc: tuple) -> None:
    cx, cy = s // 2, s // 2
    pygame.draw.circle(surf, tc, (cx, cy), s // 3)
    pygame.draw.circle(surf, CREAM, (cx, cy - s // 5), s // 6)
    pygame.draw.rect(surf, (40, 40, 50, 80), (0, 0, s, s), 1)
