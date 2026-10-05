"""The hybrid vote: a section's printed strum pattern.

The slot-wise majority (as `_topped_vote` prints it) is the baseline. It flattens
syncopation that moves from bar to bar, so a real bar (the medoid) replaces it when that
bar represents the section clearly better. A section whose bars alternate in pairs is
voted over two-bar units instead.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from youkelele.music.as_played import _topped_vote, jaccard
from youkelele.music.onsets import StrikeClass

HYBRID_DELTA = 0.04  # the medoid must beat the majority by at least this mean agreement
MEDOID_MIN_STROKES = 2  # a medoid needs at least this many `S` cells (mutes do not count)
PERIOD2_MARGIN = 0.10  # lag-2 agreement must exceed lag-1 agreement by at least this
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


def period_margin(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """Mean agreement at lag 2 minus mean agreement at lag 1; 0.0 with fewer than 4 bars."""
    if len(bars) < 4:
        return 0.0
    lag1 = np.mean([jaccard(a, b) for a, b in zip(bars, bars[1:])])
    lag2 = np.mean([jaccard(a, b) for a, b in zip(bars, bars[2:])])
    return float(lag2 - lag1)


def _pairs(bars: Sequence[Sequence[StrikeClass]]) -> list[list[StrikeClass]]:
    """Consecutive pairs concatenated; an odd last bar is left out."""
    return [list(bars[i]) + list(bars[i + 1]) for i in range(0, len(bars) - 1, 2)]


def best_pair(bars: Sequence[Sequence[StrikeClass]]) -> tuple[int, float]:
    """(start index, score) of the consecutive pair agreeing best with the pairs at even offsets.

    Pairs starting an even number of bars away are the same phase of the two-bar cycle.
    A pair with no such partner scores 1.0, as a lone medoid does. With fewer than two
    bars there is no pair and the result is (0, 0.0).
    """
    if len(bars) < 2:
        return 0, 0.0
    starts = range(len(bars) - 1)
    pair = {i: list(bars[i]) + list(bars[i + 1]) for i in starts}
    best_i, best_score = 0, -1.0
    for i in starts:
        others = [jaccard(pair[i], pair[j]) for j in starts if j != i and (j - i) % 2 == 0]
        score = float(np.mean(others)) if others else 1.0
        if score > best_score:
            best_i, best_score = i, score
    return best_i, best_score


def choose_unit(bars: Sequence[Sequence[StrikeClass]]) -> int:
    """2 when the bars repeat every two bars and each bar of the best pair has real strikes."""
    if period_margin(bars) < PERIOD2_MARGIN:
        return 1
    start, _ = best_pair(bars)
    for bar in bars[start : start + 2]:
        if sum(1 for c in bar if c != "-") < PERIOD2_MIN_STRIKES:
            return 1
    return 2


def choose_pattern(bars: Sequence[Sequence[StrikeClass]]) -> VoteResult:
    """The majority, or the medoid when it is clearly better and has enough strokes."""
    unit = choose_unit(bars)
    voted = _pairs(bars) if unit == 2 else [list(b) for b in bars]
    med, score_medoid = medoid(voted)
    score_majority = majority_loo_score(voted)
    if (
        score_medoid - score_majority >= HYBRID_DELTA
        and sum(1 for c in med if c == "S") >= MEDOID_MIN_STROKES
    ):
        return VoteResult(med, "medoid", score_majority, score_medoid, unit)
    return VoteResult(_topped_vote(voted), "majority", score_majority, score_medoid, unit)
