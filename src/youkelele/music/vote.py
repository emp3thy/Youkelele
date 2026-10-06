"""The hybrid vote: a section's printed strum pattern.

The slot-wise majority (as `_topped_vote` prints it) is the baseline. It flattens
syncopation that moves from bar to bar, so a real bar (the medoid) replaces it when that
bar represents the section clearly better. A section whose bars alternate in pairs is
voted over two-bar units instead.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypeVar

import numpy as np

from youkelele.music.as_played import _topped_vote, jaccard
from youkelele.music.onsets import StrikeClass

T = TypeVar("T")

HYBRID_DELTA = 0.04  # the medoid must beat the majority by at least this mean agreement
MEDOID_MIN_STROKES = 2  # a medoid needs at least this many `S` cells (mutes do not count)
PERIOD2_MARGIN = 0.10  # the two-bar medoid must beat the one-bar medoid by at least this
PERIOD2_MIN_STRIKES = 2  # each bar of the best pair needs this many non-rest cells


@dataclass(frozen=True)
class VoteResult:
    vector: list[StrikeClass]  # unit * slots_per_bar cells
    candidate: Literal["majority", "medoid"]
    score_majority: float
    score_medoid: float
    unit: int


def medoid(bars: Sequence[Sequence[StrikeClass]]) -> tuple[list[StrikeClass], float]:
    """The bar with the highest mean Jaccard to the others (earliest on a tie), and that score."""
    if len(bars) == 1:
        return list(bars[0]), 1.0
    best_i, best_score = 0, -1.0
    for i, bar in enumerate(bars):
        score = float(np.mean([jaccard(bar, other) for j, other in enumerate(bars) if j != i]))
        if score > best_score:
            best_i, best_score = i, score
    return list(bars[best_i]), best_score


def majority_loo_score(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """Mean over bars of the agreement with the topped vote of the other bars."""
    if len(bars) == 1:
        return jaccard(bars[0], _topped_vote(bars))
    scores = []
    for i, bar in enumerate(bars):
        rest = [b for j, b in enumerate(bars) if j != i]
        scores.append(jaccard(bar, _topped_vote(rest)))
    return float(np.mean(scores))


def best_pair(bars: Sequence[Sequence[StrikeClass]]) -> tuple[int, float]:
    """(start index, score) of the two-bar medoid: the consecutive pair that best represents
    the other bars when it alternates from its own start.

    Bar k (outside the pair) is scored against the pair's bar (k - start) % 2; the score is
    the mean Jaccard over those bars, the earliest pair winning a tie. With fewer than four
    bars there is no pair to judge and the result is (0, 0.0).
    """
    if len(bars) < 4:
        return 0, 0.0
    best_i, best_score = 0, -1.0
    for s in range(len(bars) - 1):
        pair = (bars[s], bars[s + 1])
        others = [jaccard(bars[k], pair[(k - s) % 2]) for k in range(len(bars)) if k not in (s, s + 1)]
        score = float(np.mean(others))
        if score > best_score:
            best_i, best_score = s, score
    return best_i, best_score


def period_margin(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """The two-bar medoid's score minus the one-bar medoid's score; 0.0 with fewer than 4 bars.

    This is the statistic the pattern-vote spike measured (spec 4.2, amended after the
    first validation: the spec had named lag-2 minus lag-1 agreement, which fires on far
    more sections).
    """
    if len(bars) < 4:
        return 0.0
    _, pair_score = best_pair(bars)
    _, bar_score = medoid(bars)
    return pair_score - bar_score


def unit_and_phase(bars: Sequence[Sequence[StrikeClass]]) -> tuple[int, int]:
    """(unit, phase): unit 2 when the two-bar medoid beats the one-bar medoid by the margin
    and each bar of that pair has real strikes; phase is the pair's start modulo 2 (0 for
    unit 1), so the vote pairs bars in the same phase as the pair the floor tested."""
    if period_margin(bars) < PERIOD2_MARGIN:
        return 1, 0
    start, _ = best_pair(bars)
    for bar in bars[start : start + 2]:
        if sum(1 for c in bar if c != "-") < PERIOD2_MIN_STRIKES:
            return 1, 0
    return 2, start % 2


def _pairs(bars: Sequence[Sequence[T]], phase: int = 0) -> list[list[T]]:
    """Consecutive pairs concatenated, starting at bar `phase`; a bar before the first pair
    or after the last is left out. Shared with the riff reduction (`riff_line.py`)."""
    return [list(bars[i]) + list(bars[i + 1]) for i in range(phase, len(bars) - 1, 2)]


def align_to_first_bar(vector: list, unit: int, phase: int) -> list:
    """A unit-2 vector voted from pairs starting at an odd bar, rotated so that its first half
    is the bar the section's first bar plays (as `members.vector_bar` reads it)."""
    if unit != 2 or phase == 0:
        return vector
    half = len(vector) // 2
    return vector[half:] + vector[:half]


def choose_pattern(bars: Sequence[Sequence[StrikeClass]]) -> VoteResult:
    """The majority, or the medoid when it is clearly better and has enough strokes.

    A unit-2 vector is returned aligned to the section's first bar: its first half is what
    bars at even offsets play.
    """
    unit, phase = unit_and_phase(bars)
    voted = _pairs(bars, phase) if unit == 2 else [list(b) for b in bars]
    med, score_medoid = medoid(voted)
    score_majority = majority_loo_score(voted)
    if (
        score_medoid - score_majority >= HYBRID_DELTA
        and sum(1 for c in med if c == "S") >= MEDOID_MIN_STROKES
    ):
        return VoteResult(align_to_first_bar(med, unit, phase), "medoid", score_majority, score_medoid, unit)
    vote = _topped_vote(voted)
    return VoteResult(align_to_first_bar(vote, unit, phase), "majority", score_majority, score_medoid, unit)
