"""Registry of instrument profiles."""

from __future__ import annotations

from collections.abc import Callable

from youkelele.profiles.base import InstrumentProfile, Tuning
from youkelele.profiles.ukulele import UKULELE_TUNING, ukulele_profile

PROFILES: dict[str, Callable[[], InstrumentProfile]] = {"ukulele": ukulele_profile}


def get_profile(name: str) -> InstrumentProfile:
    try:
        factory = PROFILES[name]
    except KeyError:
        raise KeyError(
            f"unknown instrument {name!r}; known: {', '.join(sorted(PROFILES))}"
        ) from None
    return factory()


__all__ = [
    "InstrumentProfile",
    "PROFILES",
    "Tuning",
    "UKULELE_TUNING",
    "get_profile",
    "ukulele_profile",
]
