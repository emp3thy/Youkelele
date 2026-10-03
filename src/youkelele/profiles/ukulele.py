"""The ukulele profile."""

from __future__ import annotations

from youkelele.profiles.base import InstrumentProfile, Tuning

UKULELE_TUNING = Tuning("gCEA", ("G4", "C4", "E4", "A4"), reentrant=True)


def ukulele_profile() -> InstrumentProfile:
    return InstrumentProfile("ukulele", UKULELE_TUNING, ())
