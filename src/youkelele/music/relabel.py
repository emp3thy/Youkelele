"""Name the bridge from the chord stream (version 1.4 spec, section 3.4 and assumption A5).

The grid stage cannot tell a bridge from a once-only verse: both are a segment whose
audio matches nothing else. The chords can. A bridge introduces chords the rest of the
song never plays; a once-only verse reuses the song's own. Measured on five songs, one
section had novelty 0.73 (Summer of '69's bridge) and the other 56 had 0.00 to 0.12.
"""

from __future__ import annotations

from youkelele.music.sections import vocal_flags
from youkelele.schemas import Chords, Grid

BRIDGE_NOVEL_CHORDS = 0.5  # share of a section's chord-bars on chords no other section plays
BRIDGE_MIN_VOCAL = 0.5  # the bridge is sung, not an instrumental break
BRIDGE_CANDIDATE_LABELS = frozenset({"verse", "chorus", "bridge"})
_EPS = 1e-6


def _bar_triads(grid: Grid, chords: Chords) -> list[set[str]]:
    """Per bar, the triads of the non-N events overlapping it."""
    per_bar: list[set[str]] = [set() for _ in grid.bars]
    events = [e for e in chords.events if e.triad not in ("N", "X")]
    for bar in grid.bars:
        per_bar[bar.index] = {
            e.triad for e in events if e.start < bar.end - _EPS and e.end > bar.start + _EPS
        }
    return per_bar


def section_novelty(grid: Grid, chords: Chords) -> list[float]:
    """Per section, the share of its chord-bars that hold a triad no other section plays.

    A chord-bar is a bar with at least one non-N event over it; it is novel when any of
    its triads occurs in no other section. A section with no chord-bars scores 0.
    """
    per_bar = _bar_triads(grid, chords)
    in_section = [
        set().union(*per_bar[s.start_bar : s.end_bar]) for s in grid.sections
    ]
    result: list[float] = []
    for i, section in enumerate(grid.sections):
        elsewhere: set[str] = set().union(*(t for j, t in enumerate(in_section) if j != i))
        bars = [t for t in per_bar[section.start_bar : section.end_bar] if t]
        novel = sum(1 for t in bars if t - elsewhere)
        result.append(novel / len(bars) if bars else 0.0)
    return result


def refine_labels(grid: Grid, chords: Chords) -> list[str]:
    """The section labels for the score: the grid's, with the bridge decided by the chords.

    Among sections labelled verse, chorus or bridge, the single section whose novelty is
    at least BRIDGE_NOVEL_CHORDS, that is neither first nor last, and whose vocal share
    is at least BRIDGE_MIN_VOCAL becomes `bridge` (the vocal test is skipped when the
    grid stored no vocal levels). Every other `bridge` becomes `verse`. `intro`,
    `instrumental`, `outro` and any hand-edited label pass through.
    """
    labels = [s.label for s in grid.sections]
    novelty = section_novelty(grid, chords)
    flags = vocal_flags(grid.bar_vocal_db) if grid.bar_vocal_db else None
    last = len(labels) - 1

    def is_candidate(i: int) -> bool:
        if i in (0, last) or labels[i] not in BRIDGE_CANDIDATE_LABELS:
            return False
        if novelty[i] < BRIDGE_NOVEL_CHORDS:
            return False
        if flags is None:
            return True
        section = grid.sections[i]
        sung = flags[section.start_bar : section.end_bar]
        return sum(sung) / len(sung) >= BRIDGE_MIN_VOCAL

    candidates = [i for i in range(len(labels)) if is_candidate(i)]
    bridge = candidates[0] if len(candidates) == 1 else None
    return [
        "bridge" if i == bridge else "verse" if label == "bridge" else label
        for i, label in enumerate(labels)
    ]
