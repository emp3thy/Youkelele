"""Bars at the end of a song after the last chord: silence or noise, not music."""

from __future__ import annotations

from collections.abc import Sequence

from youkelele.schemas import Bar, Chords

NO_CHORD = "N"
_EPS = 1e-6


def trailing_silent_bars(chords: Chords, bars: Sequence[Bar], cap: int) -> int:
    """How many whole bars at the end start at or after the last chord has ended.

    The last chord is the last event whose label is not "N"; a filled event counts as a chord.
    A song with no such event drops nothing. `cap` is the length of the last section: the
    result never exceeds `cap - 1`, so the section is never emptied.
    """
    ends = [e.end for e in chords.events if e.label != NO_CHORD]
    if not ends:
        return 0
    last_end = max(ends)
    count = 0
    for bar in reversed(bars):
        if bar.start < last_end - _EPS:
            break
        count += 1
    return min(count, max(cap - 1, 0))
