"""The "as played" strum pattern of a section: slot-wise majority over its bars.

No pattern vocabulary: the spike found that records do not play the beginner
patterns chord sites publish, so the stage reports the strike grid it hears
with a repeatability score (docs/superpowers/specs/2026-10-03-spike-audio-round2.md).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from youkelele.music.onsets import StrikeClass, render_directions
from youkelele.schemas import Meter, Slot

UNCERTAIN_BELOW = 0.45  # a section pattern with lower confidence is uncertain
MIN_SECTION_BARS = 4  # shorter sections inherit a neighbour's pattern
STAGE_UNCERTAIN_GRID_FIT = 0.6  # the whole stage is uncertain below this grid fit


def jaccard(a: Sequence[StrikeClass], b: Sequence[StrikeClass]) -> float:
    """Agreement over positions struck in either vector; strike against mute earns half.

    Two all-rest vectors agree fully by convention.
    """
    union = 0
    score = 0.0
    for x, y in zip(a, b):
        if x == "-" and y == "-":
            continue
        union += 1
        if x == y:
            score += 1.0
        elif x != "-" and y != "-":
            score += 0.5
    return score / union if union else 1.0


def majority_vector(bars: Sequence[Sequence[StrikeClass]]) -> list[StrikeClass]:
    """`S` where more than half the bars strike, `x` when most of those strikes are muted."""
    if not bars:
        return []
    n = len(bars)
    out: list[StrikeClass] = []
    for j in range(len(bars[0])):
        strikes = sum(1 for bar in bars if bar[j] != "-")
        mutes = sum(1 for bar in bars if bar[j] == "x")
        if strikes > n / 2:
            out.append("x" if mutes > strikes / 2 else "S")
        else:
            out.append("-")
    return out


def bar_repeat(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """Mean Jaccard between consecutive bars; 0.0 when there is no pair to compare."""
    if len(bars) < 2:
        return 0.0
    return float(np.mean([jaccard(a, b) for a, b in zip(bars, bars[1:])]))


def section_summary(
    bars: Sequence[Sequence[StrikeClass]], slots_per_bar: int, meter: Meter
) -> tuple[list[Slot], float, float]:
    """(rendered majority vector, confidence, bar_repeat) for one section's bars."""
    if not bars:
        return ["-"] * slots_per_bar, 0.0, 0.0
    vector = majority_vector(bars)
    confidence = float(np.mean([jaccard(bar, vector) for bar in bars]))
    return render_directions(vector, slots_per_bar, meter), confidence, bar_repeat(bars)
