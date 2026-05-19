from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image


def _base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def asset_path(name: str) -> Path:
    return _base_dir() / "assets" / name


def app_icon_ico_path() -> Path:
    return asset_path("app_icon.ico")


def app_icon_png_path() -> Path:
    return asset_path("app_icon.png")


@lru_cache(maxsize=1)
def load_app_icon_image() -> Image.Image:
    with Image.open(app_icon_png_path()) as image:
        return image.copy()
