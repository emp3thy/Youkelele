"""Snap free-running chord spans onto the beat grid."""

from __future__ import annotations

from collections.abc import Sequence

from youkelele.models.chords import LabelSpan
from youkelele.music.triads import to_triad
from youkelele.schemas import ChordEvent, Grid


def _beat_label(spans: Sequence[LabelSpan], start: float, end: float) -> tuple[str, float]:
    shares: dict[str, float] = {}
    for span in spans:
        overlap = min(end, span.end) - max(start, span.start)
        if overlap > 0:
            shares[span.label] = shares.get(span.label, 0.0) + overlap
    if not shares:
        return "N", 0.0
    label = max(shares, key=lambda k: shares[k])
    return label, min(1.0, shares[label] / (end - start))


def snap_to_beats(spans: Sequence[LabelSpan], grid: Grid) -> list[ChordEvent]:
    position: dict[int, tuple[int, int]] = {}
    for bar in grid.bars:
        for slot, beat_index in enumerate(bar.beats):
            position[beat_index] = (bar.index, slot)
    ends = [*grid.beats[1:], grid.bars[-1].end if grid.bars else grid.beats[-1]]

    runs: list[list] = []  # label, first beat, last beat, shares
    for i, (start, end) in enumerate(zip(grid.beats, ends)):
        if end <= start:
            continue
        label, share = _beat_label(spans, start, end)
        if runs and runs[-1][0] == label:
            runs[-1][2] = i
            runs[-1][3].append(share)
        else:
            runs.append([label, i, i, [share]])

    events: list[ChordEvent] = []
    for label, first, last, shares in runs:
        bar, slot = position.get(first, (0, 0))
        events.append(
            ChordEvent(
                bar=bar,
                beat=slot,
                start=grid.beats[first],
                end=ends[last],
                label=label,
                triad=to_triad(label),
                confidence=sum(shares) / len(shares),
            )
        )
    return events
