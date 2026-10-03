"""Locations of the cache and of data and vendored files shipped with the package."""

from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_DIR = Path(__file__).parent


def cache_dir() -> Path:
    override = os.environ.get("YOUKELELE_CACHE")
    return Path(override) if override else Path.home() / ".youkelele"


def package_data(*parts: str) -> Path:
    return _PACKAGE_DIR.joinpath("data", *parts)


def vendor_dir(*parts: str) -> Path:
    return _PACKAGE_DIR.joinpath("vendor", *parts)
