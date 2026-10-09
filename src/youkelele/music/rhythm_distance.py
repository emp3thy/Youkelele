"""Swap distance between two strike patterns (spec 1.8 section 5.5).

Toussaint's swap distance: the cost of sliding the onsets of one pattern onto the
other. It is written to the harness report only; the margin it helps to explain is
written, not used, and decides nothing.
"""

from __future__ import annotations

from collections.abc import Sequence

from youkelele.music.onsets import StrikeClass


def swap_distance(a: Sequence[StrikeClass], b: Sequence[StrikeClass]) -> int:
    """Sum of absolute position differences between sorted onsets; mutes count as strikes.

    Patterns with unequal onset counts are as far apart as the slot count, `len(a)`.
    """
    pa = [i for i, c in enumerate(a) if c != "-"]
    pb = [i for i, c in enumerate(b) if c != "-"]
    if len(pa) != len(pb):
        return len(a)
    return sum(abs(x - y) for x, y in zip(pa, pb))
