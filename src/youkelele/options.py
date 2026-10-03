"""Options for one pipeline run."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RunOptions(BaseModel):
    source: str
    instrument: str = "ukulele"
    tier: Literal["easy", "full"] = "easy"
    beat_octave: Literal["auto", "none", "half", "double"] = "auto"
    sections_k: int | None = None
    meter: str = "4/4"
    separator: Literal["demucs", "roformer-sw"] = "demucs"
    chord_model: Literal["cnn-lstm", "chordmini"] = "cnn-lstm"
