"""The "as played" strum pattern of a section: slot-wise majority over its bars.

No pattern vocabulary: the spike found that records do not play the beginner
patterns chord sites publish, so the stage reports the strike grid it hears
with the share of detected strokes it explains (docs/superpowers/specs/2026-10-03-spike-audio-round2.md).
"""

from __future__ import annotations

import random
from collections.abc import Sequence

import numpy as np

from youkelele.music.onsets import StrikeClass, render_directions
from youkelele.schemas import Meter, Slot

UNCERTAIN_BELOW = 0.45  # on the eighth-note grid, a section pattern with lower confidence is uncertain
# On the sixteenth grid a dense two-part section strikes many slots, which inflates the mean
# Jaccard. The band is (0.504, 0.552): Pour Some Sugar On Me's instrumental 67 to 77 sits at 0.504
# and Fame 47 to 61 at 0.552, and 0.53 is centred between them and flips nothing. The earlier reason
# for 0.55, rejecting random sprays, is now the chance test's job (spec 1.5, section 4.1).
UNCERTAIN_BELOW_SIXTEENTH = 0.53
# Shorter sections inherited a neighbour's pattern up to 1.5; 1.6 votes them on their own bars
# (spec 4.5). No code reads it any more: it is kept so that what `inherited_from` meant in a
# 1.5 file stays documented.
MIN_SECTION_BARS = 4
STAGE_UNCERTAIN_GRID_FIT = 0.6  # the whole stage is uncertain below this grid fit
STRIKE_SHARE = 1 / 3  # a slot struck in more than this share of a section's bars is kept
DENSITY_FLOOR = 0.6  # the pattern keeps at least this share of the median strikes per bar
EXPLAINED_BELOW = 0.6  # a section whose pattern explains less of its strokes is uncertain
# The chance test (spec 1.5, section 4.1).
CHANCE_ALPHA = 0.05  # a pattern is structured when its chance p is at most this; band (0.021, 0.064)
CHANCE_SHUFFLES = 1000  # slot-shuffled copies per section; Monte Carlo error near 0.05 is about 0.007
FULL_VOTE_DENSITY = 0.6  # a full vote needs at least this strike density; band (0.547, 0.625)


def eighth_grid(slots_per_bar: int, meter: Meter) -> bool:
    """Two slots per beat; any finer grid is the sixteenth grid."""
    return slots_per_bar == meter.numerator * 2


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
    vector = _topped_vote(bars)
    return (
        render_directions(vector, slots_per_bar, meter),
        vote_confidence(bars),
        bar_repeat(bars),
        explained_onsets(bars, vector),
    )


def _topped_vote(bars: Sequence[Sequence[StrikeClass]]) -> list[StrikeClass]:
    """The third-share vote, topped up to the density floor."""
    n = len(bars)
    rates = [sum(1 for bar in bars if bar[j] != "-") / n for j in range(len(bars[0]))]
    median_strikes = float(np.median([sum(1 for c in bar if c != "-") for bar in bars]))
    return fill_to_floor(majority_vector(bars), rates, round(DENSITY_FLOOR * median_strikes))


def vote_confidence(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """Mean Jaccard of the bars against their topped-up vote; 0.0 with no bars."""
    if not bars:
        return 0.0
    vector = _topped_vote(bars)
    return float(np.mean([jaccard(bar, vector) for bar in bars]))


def full_vote(vector: Sequence[StrikeClass]) -> bool:
    """True when every slot of the vote is struck (no rest)."""
    return all(c != "-" for c in vector)


def strike_density(bars: Sequence[Sequence[StrikeClass]]) -> float:
    """Share of the cells that are not rests, mutes counted as strikes; 0.0 with no bars."""
    cells = sum(len(bar) for bar in bars)
    if not cells:
        return 0.0
    return sum(1 for bar in bars for c in bar if c != "-") / cells


def chance_p(
    bars: Sequence[Sequence[StrikeClass]], seed: int, shuffles: int = CHANCE_SHUFFLES
) -> float:
    """Chance of a section this repetitive from slot-shuffled copies, never zero.

    `(b + 1) / (shuffles + 1)`, b the number of copies whose `vote_confidence` is at
    least the section's own (Phipson and Smyth). Each bar's cells are permuted on
    their own, so it keeps its strikes and mutes.
    """
    observed = vote_confidence(bars)
    rng = random.Random(seed)
    at_least = 0
    for _ in range(shuffles):
        copy = []
        for bar in bars:
            cells = list(bar)
            rng.shuffle(cells)
            copy.append(cells)
        if vote_confidence(copy) >= observed:
            at_least += 1
    return (at_least + 1) / (shuffles + 1)


def structure_test(
    bars: Sequence[Sequence[StrikeClass]], vector: Sequence[StrikeClass], seed: int
) -> tuple[bool, float | None, float]:
    """(structured, chance_p or None when the vote is full, strike_density).

    A full vote gives a shuffled baseline equal to the bar density, so it is tested
    as a claim about density; any other vote is tested against the shuffles. `vector`
    is the whole vote: a two-bar vote (spec 1.6, 4.2) is full only when both its bars
    are, so the test never depends on which bar a section starts on.
    """
    density = strike_density(bars)
    if full_vote(vector):
        return density >= FULL_VOTE_DENSITY, None, density
    p = chance_p(bars, seed)
    return p <= CHANCE_ALPHA, p, density


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
