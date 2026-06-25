"""
save.py
Gestion de la persistance du jeu via des fichiers JSON.
Sauvegarde/charge l'état complet d'une partie.
"""

from __future__ import annotations
import json
import pathlib
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game import GameManager

SAVE_DIR = pathlib.Path(__file__).parent.parent / "data" / "save"


def _ensure_save_dir() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def save_game(game: "GameManager", slot: str = "autosave") -> pathlib.Path:
    """
    Sérialise l'état complet du jeu et l'écrit dans data/save/<slot>.json.
    Retourne le chemin du fichier sauvegardé.
    """
    _ensure_save_dir()
    payload = {
        "meta": {
            "slot": slot,
            "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "current_day": game.current_day,
        },
        "teams": [team.to_dict() for team in game.teams],
    }
    path = SAVE_DIR / f"{slot}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_game(slot: str = "autosave") -> dict | None:
    """
    Charge un fichier de sauvegarde.
    Retourne le dict brut, ou None si le fichier n'existe pas.
    """
    path = SAVE_DIR / f"{slot}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_saves() -> list[dict]:
    """
    Retourne la liste des sauvegardes disponibles avec leur métadonnée.
    """
    _ensure_save_dir()
    saves = []
    for p in sorted(SAVE_DIR.glob("*.json")):
        try:
            meta = json.loads(p.read_text(encoding="utf-8")).get("meta", {})
            meta["filename"] = p.name
            saves.append(meta)
        except (json.JSONDecodeError, OSError):
            pass
    return saves


def delete_save(slot: str) -> bool:
    """Supprime une sauvegarde. Retourne True si le fichier existait."""
    path = SAVE_DIR / f"{slot}.json"
    if path.exists():
        path.unlink()
        return True
    return False
