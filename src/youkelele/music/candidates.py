"""The candidate patterns for a section and the top-two margin (spec 1.8 section 5.5).

The margin between the printed pattern and its nearest different rival is measured
here for the harness report. It is written, not used: it does not decide certainty
and no threshold reads it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from youkelele.music.as_played import _topped_vote, jaccard
from youkelele.music.onsets import StrikeClass
from youkelele.music.vote import _pairs, medoid


@dataclass(frozen=True)
class Candidate:
    name: str
    vector: list[StrikeClass]
    score: float


def _mean_agreement(vector: Sequence[StrikeClass], units: Sequence[Sequence[StrikeClass]]) -> float:
    return float(np.mean([jaccard(vector, unit) for unit in units]))


def _two_best_units(units: Sequence[Sequence[StrikeClass]]) -> list[list[StrikeClass]]:
    """The best unit by mean Jaccard to the other units (earliest on a tie), then the best unit
    whose vector differs from it (the next best if all agree)."""
    if len(units) < 2:
        return [list(u) for u in units]
    means = [
        float(np.mean([jaccard(u, o) for j, o in enumerate(units) if j != i]))
        for i, u in enumerate(units)
    ]
    order = sorted(range(len(units)), key=lambda i: (-means[i], i))
    first = list(units[order[0]])
    rest = [list(units[i]) for i in order[1:]]
    differing = [v for v in rest if v != first]
    return [first] + (differing or rest)[:1]


def candidate_set(
    bars: Sequence[Sequence[StrikeClass]], allow_two_bar: bool, phase: int
) -> list[Candidate]:
    """Majority and medoid per unit length, then the two best voted units; `[]` with no bars."""
    if not bars:
        return []
    out: list[Candidate] = []
    unit_sets: list[tuple[str, list[Sequence[StrikeClass]]]] = [("1", list(bars))]
    if allow_two_bar:
        pairs = _pairs(bars, phase)
        if pairs:
            unit_sets.append(("2", pairs))
    for suffix, units in unit_sets:
        majority = _topped_vote(units)
        out.append(Candidate(f"majority_{suffix}", majority, _mean_agreement(majority, units)))
        vector, _ = medoid(units)
        out.append(Candidate(f"medoid_{suffix}", vector, _mean_agreement(vector, units)))
    voted = unit_sets[-1][1]
    for name, vector in zip(("bar_best", "bar_second"), _two_best_units(voted)):
        out.append(Candidate(name, vector, _mean_agreement(vector, voted)))
    return out


def top2(
    printed: Sequence[StrikeClass], cands: Sequence[Candidate]
) -> tuple[float | None, list[StrikeClass] | None]:
    """The printed vector's score minus the best score among candidates that differ from it.

    Returns `(margin, rival vector)`, or `(None, None)` when no candidate differs.
    The printed score is its candidate's, else its mean Jaccard to the candidates of its length.
    """
    rivals = [c for c in cands if list(c.vector) != list(printed)]
    if not rivals:
        return None, None
    same = [c for c in cands if list(c.vector) == list(printed)]
    if same:
        score = max(c.score for c in same)
    else:
        peers = [c.vector for c in cands if len(c.vector) == len(printed)] or [c.vector for c in cands]
        score = _mean_agreement(printed, peers)
    best = max(rivals, key=lambda c: c.score)
    return score - best.score, list(best.vector)
