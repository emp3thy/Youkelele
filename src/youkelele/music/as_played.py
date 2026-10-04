"""The "as played" strum pattern of a section: slot-wise majority over its bars.

No pattern vocabulary: the spike found that records do not play the beginner
patterns chord sites publish, so the stage reports the strike grid it hears
with the share of detected strokes it explains (docs/superpowers/specs/2026-10-03-spike-audio-round2.md).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from youkelele.music.onsets import StrikeClass, render_directions
from youkelele.schemas import Meter, Slot

UNCERTAIN_BELOW = 0.45  # a section pattern with lower confidence is uncertain
MIN_SECTION_BARS = 4  # shorter sections inherit a neighbour's pattern
STAGE_UNCERTAIN_GRID_FIT = 0.6  # the whole stage is uncertain below this grid fit
STRIKE_SHARE = 1 / 3  # a slot struck in more than this share of a section's bars is kept
DENSITY_FLOOR = 0.6  # the pattern keeps at least this share of the median strikes per bar
EXPLAINED_BELOW = 0.6  # a section whose pattern explains less of its strokes is uncertain


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


def majority_vector(
    bars: Sequence[Sequence[StrikeClass]], threshold: float = STRIKE_SHARE
) -> list[StrikeClass]:
    """`S` where more than `threshold` of the bars strike, `x` when most of those strikes are muted."""
    if not bars:
        return []
    n = len(bars)
    out: list[StrikeClass] = []
    for j in range(len(bars[0])):
        strikes = sum(1 for bar in bars if bar[j] != "-")
        mutes = sum(1 for bar in bars if bar[j] == "x")
        if strikes > threshold * n:
            out.append("x" if mutes > strikes / 2 else "S")
        else:
            out.append("-")
    return out


def fill_to_floor(
    vector: Sequence[StrikeClass], rates: Sequence[float], floor: int
) -> list[StrikeClass]:
    """Add the highest-rate unstruck slots as `S` until `floor` slots are struck.

    Ties go to the earlier slot; a vector that already meets the floor is returned unchanged.
    """
    out = list(vector)
    missing = floor - sum(1 for c in out if c != "-")
    if missing <= 0:
        return out
    unstruck = sorted((j for j, c in enumerate(out) if c == "-"), key=lambda j: (-rates[j], j))
    for j in unstruck[:missing]:
        out[j] = "S"
    return out


def bar_repeat(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """Mean Jaccard between consecutive bars; 0.0 when there is no pair to compare."""
    if len(bars) < 2:
        return 0.0
    return float(np.mean([jaccard(a, b) for a, b in zip(bars, bars[1:])]))


def section_summary(
    bars: Sequence[Sequence[StrikeClass]], slots_per_bar: int, meter: Meter
) -> tuple[list[Slot], float, float, float]:
    """(rendered vector, confidence, bar_repeat, explained) for one section's bars.

    The vector is the third-share vote, topped up to a density floor so a busy
    section is never drawn much sparser than it is played.
    """
    if not bars:
        return ["-"] * slots_per_bar, 0.0, 0.0, 0.0
    n = len(bars)
    rates = [sum(1 for bar in bars if bar[j] != "-") / n for j in range(len(bars[0]))]
    median_strikes = float(np.median([sum(1 for c in bar if c != "-") for bar in bars]))
    vector = fill_to_floor(majority_vector(bars), rates, round(DENSITY_FLOOR * median_strikes))
    confidence = float(np.mean([jaccard(bar, vector) for bar in bars]))
    return (
        render_directions(vector, slots_per_bar, meter),
        confidence,
        bar_repeat(bars),
        explained_onsets(bars, vector),
    )


def explained_onsets(bars: Sequence[Sequence[str]], vector: Sequence[str]) -> float:
    """Share of the strikes in `bars` that land on a slot struck in `vector`.

    A strike is any entry other than `-` (`S`, `x`, `D`, `U`); 0.0 when the
    bars hold no strikes.
    """
    strikes = 0
    explained = 0
    for bar in bars:
        for j, cell in enumerate(bar):
            if cell == "-":
                continue
            strikes += 1
            if j < len(vector) and vector[j] != "-":
                explained += 1
    return explained / strikes if strikes else 0.0
