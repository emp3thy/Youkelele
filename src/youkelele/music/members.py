"""A member's figures against its own vote (spec 1.6, sections 4.1 to 4.3).

A planned section's members are whole grid sections. Each member votes its own
pattern, which may be one bar long or two (unit 2); a bar is always compared with
the bar of the vote at its own offset from the member's first bar; a member printing its
section's two-bar vote adds the alignment that fits its own bars. Pure numpy.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from youkelele.music.as_played import bar_repeat, explained_onsets, jaccard
from youkelele.music.onsets import StrikeClass
from youkelele.schemas import Grid, PlannedSection


def member_spans(section: PlannedSection, grid: Grid) -> list[tuple[int, int]]:
    """Each member grid section's bar range, in order; a section with no members list is its own single member."""
    spans = [(grid.sections[m].start_bar, grid.sections[m].end_bar) for m in section.members]
    return spans or [(section.start_bar, section.end_bar)]


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


def section_offset(
    bars: Sequence[Sequence[StrikeClass]], vector: Sequence[StrikeClass], unit: int, slots_per_bar: int
) -> int:
    """The alignment, 0 or 1 bars, of a section's vote that best fits a member's own bars.

    A member's first bar is not always the bar the section's vote starts on: a member
    playing a two-bar figure from its second bar would print it swapped. Each alignment is
    scored by the mean Jaccard of the member's bars with the vote's bar at their offset plus
    the alignment; a one-bar vote, a tie or no bars gives 0.
    """
    if unit != 2 or not bars:
        return 0

    def fit(offset: int) -> float:
        return float(np.mean([
            jaccard(bar, vector_bar(vector, unit, slots_per_bar, i + offset)) for i, bar in enumerate(bars)
        ]))

    return 1 if fit(1) > fit(0) else 0


def aligned_agreement(
    own: Sequence[StrikeClass], section: Sequence[StrikeClass], section_unit: int, slots_per_bar: int, offset: int
) -> float:
    """Jaccard of a member vote's first bar with the section vote's bar at `offset`.

    The first bar is a vote's representative; at offset 0 this is the agreement of the two
    votes' first bars, as 1.6 measured `MEMBER_AGREE` on.
    """
    return jaccard(own[:slots_per_bar], vector_bar(section, section_unit, slots_per_bar, offset))
