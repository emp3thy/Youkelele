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
    bar_vocal_db: list[float] = []  # vocals-stem level per bar; empty in files before 1.4

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
        if self.bar_vocal_db and len(self.bar_vocal_db) != len(self.bars):
            raise ValueError("bar_vocal_db must be empty or have one value per bar")
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


class BeatsRaw(_Artifact):
    """The beat detector's output before gap filling and octave normalisation."""

    detected_beats: list[float]  # taken after the end-of-clip filter: a beat at the clip's end is not kept
    detected_downbeats: list[float]  # likewise filtered
    inserted_beats: list[float]  # added by fill_gaps
    dropped_beats: list[float]  # removed by normalise_octave (empty unless the octave is halved)


class TonicVotes(_Artifact):
    """The three tonic estimates a chords_stems key weighed, and which decided."""

    score: str | None = None  # the tonic by chord-stream score
    pair: str | None = None  # the tonic by the pair rule
    mix: str | None = None  # the tonic of the mix estimate
    decided_by: Literal["agreement", "pair rule", "mix", "score"] | None = None  # the rule that settled it


class Key(_Artifact):
    tonic: str
    mode: Literal["major", "minor"]
    confidence: float  # the mode margin for a chords_stems key
    # chords_stems: tonic from the chord stream, mode from the harmonic stems (1.4);
    # mix_krumhansl: the 24-way profile search on the mix (1.3 files, or too few chords)
    method: Literal["mix_krumhansl", "chords_stems"] = "mix_krumhansl"
    margin: float | None = None  # the score's margin, or the pair rule's when it decided a close score (decided_by "pair rule")
    mode_margin: float | None = None  # major minus minor correlation at the tonic, absolute
    runner_up: str | None = None  # the runner-up tonic under the deciding rule
    mix: Key | None = None  # the mix estimate, kept for comparison
    # the mode of the other tonic a hedged key names, from the chroma at that tonic; None
    # when not hedged and in files written before it was stored
    hedge_mode: Literal["major", "minor"] | None = None
    pair_tonic: str | None = None  # the tonic the pair rule names; None in files before 1.5
    tonic_votes: TonicVotes | None = None  # the votes behind the tonic; None in files before 1.5


class ChordEvent(_Artifact):
    bar: int
    beat: int
    start: float
    end: float
    label: str
    triad: str
    confidence: float
    filled: bool = False  # inferred from the harmonic stems for a bar the recogniser left N
    power: bool = False  # the minor tonic played as root and fifth: label `X:5`, triad the key's

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
    explained: float = 0.0  # share of the section's detected strokes on struck slots
    recall_boost: bool = False  # the recall gate kept high-band onsets for this section
    chance_p: float | None = None  # share of shuffled copies scoring at least this section's confidence; low means structured; None before 1.5
    strike_density: float | None = None  # share of the section's cells that are not rests, mutes counted as strikes; None before 1.5
    riff: bool = False  # the section's guitar plays single notes rather than chords (a riff, not a strum)
    riff_entropy: float | None = None  # median over the section's onsets of each onset's normalised chroma entropy; low means single notes; None before 1.5
    riff_single_share: float | None = None  # share of onsets with a single pitch class at half the maximum or more; None before 1.5
    riff_onsets: int | None = None  # the detector's own onsets (before the recall gate) the riff features rest on; None before 1.5


class PlannedSection(_Artifact):
    start_bar: int
    end_bar: int  # exclusive
    label: str
    members: list[int] = []  # grid section indices merged into this section, in order


class Strums(_Artifact):
    slots_per_bar: int
    source: Literal["guitar_stem", "other_stem", "mix"]
    source_ratio: float
    grid_fit: float
    uncertain: bool
    patterns: list[SectionPattern]
    bar_onsets: list[list[Slot]]
    plan: list[PlannedSection] = []  # the section plan the patterns follow; empty before 1.5

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
    power: bool = False  # copied from the chord event: a power chord on the record


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
    passing: bool = False  # every use of this chord is a passing chord
    power: bool = False  # some use of this chord is a power chord on the record


class ScoreChord(_Artifact):
    name: str
    diagram: int
    start_slot: int
    slots: list[Slot]
    filled: bool = False  # copied from the chord event
    passing: bool = False  # copied from the arranged chord
    power: bool = False  # copied from the arranged chord


class ScoreBar(_Artifact):
    index: int
    chords: list[ScoreChord]
    pickup: bool = False
    struck: bool = False  # at least one strike was detected in the bar; the worked example prefers these


class ScoreSection(_Artifact):
    label: str
    pattern: list[Slot]
    uncertain: bool
    bars: list[ScoreBar]
    bar_repeat: float
    no_instrument: bool
    inherited_from: int | None = None
    explained: float = 0.0
    shifted: int = 0  # bars the start moved from grid.json to sit in phase with the chords
    riff: bool = False  # copied from the pattern: the section's guitar plays single notes rather than chords (a riff, not a strum)
    members: list[int] = []  # copied from the plan: grid section indices merged into this section


class Score(_Artifact):
    instrument: Instrument
    title: str
    artist: str | None
    key: str
    key_hedge: str | None = None  # "D major" when the key is a close call: printed "(or D major)"
    bpm: float
    meter: Meter
    tier: str
    slots_per_bar: int
    strum_source: Literal["guitar_stem", "other_stem", "mix"]
    strums_uncertain: bool
    chord_diagrams: list[ChordDiagram]
    alternative_diagrams: list[ChordDiagram] = []  # the no-capo shapes, only under a capo
    sections: list[ScoreSection]
    trailing_bars_dropped: int = 0  # bars after the last chord left off the sheet
