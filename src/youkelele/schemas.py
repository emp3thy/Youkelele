"""Pydantic models for every JSON artifact passed between pipeline stages."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Slot = Literal["D", "U", "x", "-"]


class _Artifact(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: int = Field(1, alias="schema")


class Meter(_Artifact):
    numerator: int
    denominator: int

    @classmethod
    def parse(cls, text: str) -> Meter:
        num, sep, den = text.partition("/")
        if not sep:
            raise ValueError(f"meter must look like '4/4', got {text!r}")
        return cls(numerator=int(num), denominator=int(den))


class SourceInfo(_Artifact):
    url: str | None
    path: str | None
    video_id: str | None
    title: str
    raw_title: str | None = None
    artist: str | None
    duration: float
    sample_rate: int
    channels: int
    fetched_at: datetime


class Bar(_Artifact):
    index: int
    start: float
    end: float
    beats: list[int]
    pickup: bool = False


class Section(_Artifact):
    label: str
    start_bar: int
    end_bar: int  # exclusive
    confidence: float


class Grid(_Artifact):
    bpm: float
    meter: Meter
    beats: list[float]
    downbeats: list[int]
    bars: list[Bar]
    sections: list[Section]
    octave_decision: Literal["none", "half", "double"]
    bar_loudness_db: list[float]
    sections_k: int
    largest_cluster_share: float
    chorus_margin_db: float | None
    labels_low_confidence: bool
    backbeat_ratio: float | None = None
    drums_silent: bool = False

    @model_validator(mode="after")
    def _check_structure(self) -> Grid:
        if any(b <= a for a, b in zip(self.beats, self.beats[1:])):
            raise ValueError("beats must be strictly increasing")
        if any(not 0 <= d < len(self.beats) for d in self.downbeats):
            raise ValueError("downbeats must be indices into beats")
        if [bar.index for bar in self.bars] != list(range(len(self.bars))):
            raise ValueError("bars must be indexed 0..n-1 in order")
        if len(self.bar_loudness_db) != len(self.bars):
            raise ValueError("bar_loudness_db must have one value per bar")
        if self.sections:
            if self.sections[0].start_bar != 0:
                raise ValueError("sections must start at bar 0")
            if self.sections[-1].end_bar != len(self.bars):
                raise ValueError("sections must end at the last bar (end_bar == len(bars))")
            for prev, cur in zip(self.sections, self.sections[1:]):
                if cur.start_bar != prev.end_bar:
                    raise ValueError("sections must be in order and contiguous")
            if any(s.end_bar <= s.start_bar for s in self.sections):
                raise ValueError("sections must each span at least one bar")
        elif self.bars:
            raise ValueError("sections must cover every bar")
        return self


class Key(_Artifact):
    tonic: str
    mode: Literal["major", "minor"]
    confidence: float


class ChordEvent(_Artifact):
    bar: int
    beat: int
    start: float
    end: float
    label: str
    triad: str
    confidence: float
    filled: bool = False  # inferred from the harmonic stems for a bar the recogniser left N

    @field_validator("label", "triad")
    @classmethod
    def _check_harte(cls, value: str) -> str:
        if value in ("N", "X"):
            return value
        import mir_eval.chord

        try:
            mir_eval.chord.split(value)
        except mir_eval.chord.InvalidChordException:
            raise ValueError(
                f"{value!r} is not a chord label: expected Harte syntax such as A:min"
            ) from None
        return value


class Chords(_Artifact):
    key: Key
    events: list[ChordEvent]


class SectionPattern(_Artifact):
    section: int
    slots: list[Slot]
    confidence: float
    bar_repeat: float
    uncertain: bool
    no_instrument: bool
    inherited_from: int | None


class Strums(_Artifact):
    slots_per_bar: int
    source: Literal["guitar_stem", "other_stem", "mix"]
    source_ratio: float
    grid_fit: float
    uncertain: bool
    patterns: list[SectionPattern]
    bar_onsets: list[list[Slot]]

    @model_validator(mode="after")
    def _check_slot_lengths(self) -> Strums:
        n = self.slots_per_bar
        if any(len(p.slots) != n for p in self.patterns):
            raise ValueError(f"patterns: every slot list must have {n} slots")
        if any(len(bar) != n for bar in self.bar_onsets):
            raise ValueError(f"bar_onsets: every slot list must have {n} slots")
        return self


class Shape(_Artifact):
    """Frets (diagram order, G C E A for ukulele; -1 muted) and barres are relative to base_fret."""

    frets: list[int]
    fingers: list[int]
    base_fret: int
    barres: list[int]


class ArrangedChord(_Artifact):
    event: int
    name: str
    shape: Shape
    passing: bool = False  # rare and short: named in the grid, no full diagram


class Substitution(_Artifact):
    event: int
    original: str
    chosen: str
    reason: str


class Arrangement(_Artifact):
    capo: int
    transpose: int
    tier: Literal["easy", "full"]
    chords: list[ArrangedChord]
    substitutions: list[Substitution]
    no_capo_alternative: list[ArrangedChord] = []


class Instrument(_Artifact):
    name: str
    strings: int
    tuning: list[str]
    capo: int


class ChordDiagram(_Artifact):
    name: str
    shape: Shape


class ScoreChord(_Artifact):
    name: str
    diagram: int
    start_slot: int
    slots: list[Slot]


class ScoreBar(_Artifact):
    index: int
    chords: list[ScoreChord]
    pickup: bool = False


class ScoreSection(_Artifact):
    label: str
    pattern: list[Slot]
    uncertain: bool
    bars: list[ScoreBar]
    bar_repeat: float
    no_instrument: bool
    inherited_from: int | None = None


class Score(_Artifact):
    instrument: Instrument
    title: str
    artist: str | None
    key: str
    bpm: float
    meter: Meter
    tier: str
    slots_per_bar: int
    strum_source: Literal["guitar_stem", "other_stem", "mix"]
    strums_uncertain: bool
    chord_diagrams: list[ChordDiagram]
    sections: list[ScoreSection]
