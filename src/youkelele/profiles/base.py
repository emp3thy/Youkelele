"""Instrument profile types."""

from __future__ import annotations

from dataclasses import dataclass

from youkelele.stage import Stage


@dataclass(frozen=True)
class Tuning:
    name: str
    pitches: tuple[str, ...]  # diagram order, left to right
    reentrant: bool


@dataclass(frozen=True)
class InstrumentProfile:
    name: str
    tuning: Tuning
    stages: tuple[Stage, ...]
