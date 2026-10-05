"""A member's figures against its own vote (spec 1.6, sections 4.1 to 4.3).

A planned section's members are whole grid sections. Each member votes its own
pattern, which may be one bar long or two (unit 2); a bar is always compared with
the bar of the vote at its own offset from the member's first bar. Pure numpy.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from youkelele.music.as_played import bar_repeat, explained_onsets, jaccard
from youkelele.music.onsets import StrikeClass


def vector_bar(
    vector: Sequence[StrikeClass], unit: int, slots_per_bar: int, offset: int
) -> list[StrikeClass]:
    """The bar of a `unit`-bar vector that the bar `offset` bars into the member plays against."""
    k = offset % unit
    return list(vector[k * slots_per_bar : (k + 1) * slots_per_bar])


def member_figures(
    bars: Sequence[Sequence[StrikeClass]], vector: Sequence[StrikeClass], unit: int, slots_per_bar: int
) -> tuple[float, float, float]:
    """(confidence, bar_repeat, explained) of a member's bars against its vote.

    Confidence is the mean Jaccard of each bar with the vote's matching bar (spec 4.1:
    agreement with the printed candidate); explained is the share of the bars' strikes
    on a slot the matching bar strikes. Both are 0.0 with no bars.
    """
    if not bars:
        return 0.0, 0.0, 0.0
    halves = [vector_bar(vector, unit, slots_per_bar, i) for i in range(len(bars))]
    confidence = float(np.mean([jaccard(bar, half) for bar, half in zip(bars, halves)]))
    # one long bar against one long vector keeps every strike paired with its own half
    flat_bars = [cell for bar in bars for cell in bar]
    flat_halves = [cell for half in halves for cell in half]
    return confidence, bar_repeat(bars), explained_onsets([flat_bars], flat_halves)


def first_bar_agreement(a: Sequence[StrikeClass], b: Sequence[StrikeClass], slots_per_bar: int) -> float:
    """Jaccard of the first bars of two votes: the representative bar of a unit-2 vote."""
    return jaccard(a[:slots_per_bar], b[:slots_per_bar])
