"""Align section starts to the song's chord-change phrase.

Chords in most songs change on a two-bar rhythm. When a section boundary falls one bar
into that rhythm, every four-bar row of the section prints out of phase ("D A A D" instead
of "D D A A"). This module finds such sections from where the chords change and moves
their start one bar later. It never changes the number of sections.
"""

from __future__ import annotations

from collections.abc import Sequence

MIN_SECTION_BARS = 4  # matches stages/grid.py: no section is shifted below this
PHRASE_MIN_CHANGES = 4  # odd-offset changes needed before a section is shifted
PHRASE_MIN_SHARE = 0.75  # share of a section's changes that must sit at odd offsets

NO_CHORD = "N"


def bar_change_bars(bar_ends: Sequence[tuple[str, str]]) -> list[int]:
    """Bar indices whose first chord differs from the previous bar's last chord.

    `bar_ends` holds (first chord, last chord) per bar; a silent bar is ("N", "N").
    """
    return [
        i for i in range(1, len(bar_ends)) if bar_ends[i][0] != bar_ends[i - 1][1]
    ]


def change_bars(bar_labels: Sequence[str]) -> list[int]:
    """Bar indices whose chord differs from the previous bar's, one label per bar."""
    return bar_change_bars([(label, label) for label in bar_labels])


def aligned_starts(
    section_ranges: Sequence[tuple[int, int]], changes: Sequence[int]
) -> list[tuple[int, int, int]]:
    """(start, end, shifted) per section, with out-of-phase sections started a bar later.

    A section other than the first is shifted by +1 (and the previous section's end with
    it) when at least PHRASE_MIN_CHANGES of its chord changes, and at least
    PHRASE_MIN_SHARE of them, fall at odd offsets from its start, and both sections keep
    at least MIN_SECTION_BARS bars. Offsets are counted from the section's own start.
    """
    result = [[start, end, 0] for start, end in section_ranges]
    for k in range(1, len(result)):
        start, end = section_ranges[k]
        inside = [c - start for c in changes if start <= c < end]
        odd = sum(1 for offset in inside if offset % 2 == 1)
        if odd < PHRASE_MIN_CHANGES or odd / len(inside) < PHRASE_MIN_SHARE:
            continue
        prev = result[k - 1]
        if end - (start + 1) < MIN_SECTION_BARS or (start + 1) - prev[0] < MIN_SECTION_BARS:
            continue
        prev[1] = start + 1
        result[k] = [start + 1, end, 1]
    return [(start, end, shifted) for start, end, shifted in result]
