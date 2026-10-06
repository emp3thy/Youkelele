"""The riff line: per-bar note sequences reduced to a one- or two-bar riff, and the printable gate.

The reduction mirrors the strum vote (`vote.py`): a majority and a medoid candidate, the
hybrid rule between them, but with agreement measured on exact (slot, pitch) pairs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from youkelele.music.vote import HYBRID_DELTA, MEDOID_MIN_STROKES, _pairs, align_to_first_bar, unit_and_phase

RIFF_AGREE_MIN = 0.70
RIFF_SUPPORT_MIN = 0.75
RIFF_NAMED_MIN = 0.6

NoteBar = list[int | None]  # one entry per slot: a MIDI note starting there, or None


@dataclass(frozen=True)
class RiffChoice:
    unit: int
    notes: NoteBar
    candidate: Literal["majority", "medoid"]
    agreement: float
    support: float


def note_jaccard(a: NoteBar, b: NoteBar) -> float:
    """Over slots where either bar has a note: 1 for the same pitch, 0 otherwise; 1.0 if none."""
    union = 0
    same = 0
    for x, y in zip(a, b):
        if x is None and y is None:
            continue
        union += 1
        if x == y:
            same += 1
    return same / union if union else 1.0


def _majority(bars: Sequence[NoteBar]) -> NoteBar:
    """Per slot the most common pitch (lowest on a tie), if at least half of all bars have a note."""
    out: NoteBar = []
    for slot in range(len(bars[0])):
        pitches = [b[slot] for b in bars if b[slot] is not None]
        if pitches and len(pitches) * 2 >= len(bars):
            counts = Counter(pitches)
            out.append(min(counts, key=lambda p: (-counts[p], p)))
        else:
            out.append(None)
    return out


def _medoid(bars: Sequence[NoteBar]) -> tuple[NoteBar, float]:
    """The bar with the highest mean note_jaccard to the others (earliest on a tie)."""
    if len(bars) == 1:
        return list(bars[0]), 1.0
    best_i, best = 0, -1.0
    for i, bar in enumerate(bars):
        score = float(np.mean([note_jaccard(bar, o) for j, o in enumerate(bars) if j != i]))
        if score > best:
            best_i, best = i, score
    return list(bars[best_i]), best


def _majority_loo(bars: Sequence[NoteBar]) -> float:
    """Mean over bars of the agreement with the majority of the other bars."""
    if len(bars) == 1:
        return note_jaccard(bars[0], _majority(bars))
    scores = []
    for i, bar in enumerate(bars):
        rest = [b for j, b in enumerate(bars) if j != i]
        scores.append(note_jaccard(bar, _majority(rest)))
    return float(np.mean(scores))


def _support(notes: NoteBar, bars: Sequence[NoteBar]) -> float:
    """Mean over the notes of the share of bars with that pitch in that slot (0.0 with no notes)."""
    shares = [
        sum(1 for b in bars if b[slot] == pitch) / len(bars)
        for slot, pitch in enumerate(notes)
        if pitch is not None
    ]
    return float(np.mean(shares)) if shares else 0.0


def choose_riff(bars: Sequence[NoteBar]) -> RiffChoice:
    """The majority riff, or the medoid when it clearly represents the bars better.

    A two-bar riff is voted over pairs in the phase of the best pair (as the strum vote is)
    and returned aligned to the section's first bar.
    """
    shape = [["S" if n is not None else "-" for n in bar] for bar in bars]
    unit, phase = unit_and_phase(shape)  # type: ignore[arg-type]
    voted = _pairs(bars, phase) if unit == 2 else [list(b) for b in bars]
    med, score_medoid = _medoid(voted)
    score_majority = _majority_loo(voted)
    if (
        score_medoid - score_majority >= HYBRID_DELTA
        and sum(1 for n in med if n is not None) >= MEDOID_MIN_STROKES
    ):
        notes = align_to_first_bar(med, unit, phase)
        return RiffChoice(unit, notes, "medoid", score_medoid, _support(med, voted))
    maj = _majority(voted)
    notes = align_to_first_bar(maj, unit, phase)
    return RiffChoice(unit, notes, "majority", score_majority, _support(maj, voted))


def gate(choice: RiffChoice, named_share: float, riff_flag: bool) -> tuple[bool, str | None]:
    """(True, None) when the riff may print, else (False, the first failing reason)."""
    if choice.agreement < RIFF_AGREE_MIN:
        return False, f"agreement {choice.agreement:.2f} < {RIFF_AGREE_MIN:.2f}"
    if choice.support < RIFF_SUPPORT_MIN:
        return False, f"support {choice.support:.2f} < {RIFF_SUPPORT_MIN:.2f}"
    if named_share < RIFF_NAMED_MIN:
        return False, f"named {named_share:.2f} < {RIFF_NAMED_MIN:.2f}"
    if not riff_flag:
        return False, "not a riff"
    return True, None
