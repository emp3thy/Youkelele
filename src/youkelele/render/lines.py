"""Pack a score section's bars into lines and fold identical consecutive lines into a repeat."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from youkelele.music.as_played import eighth_grid
from youkelele.schemas import Meter, ScoreBar, ScoreSection

NARROW = 4
WIDE = 8
_REPEAT_WORDS = {2: "play twice", 3: "play three times"}


@dataclass
class Line:
    """Consecutive bars printed on one line; ``repeat`` is how many times the line is played.

    The count row and the tab string labels print once per line, on its first bar.
    """

    bars: list[ScoreBar]
    repeat: int = 1


def line_width(bars: Sequence[ScoreBar], start: int, slots_per_bar: int, meter: Meter) -> int:
    """Eight when the grid is eighths and the next eight bars hold at most one chord each and
    no pickup, else four."""
    if not eighth_grid(slots_per_bar, meter):
        return NARROW
    window = bars[start : start + WIDE]
    if any(len(b.chords) > 1 or b.pickup for b in window):
        return NARROW
    return WIDE


def pack_lines(section: ScoreSection, slots_per_bar: int, meter: Meter) -> list[Line]:
    """Greedy lines from the first bar; a leading pickup bar is the first cell of a four-bar
    line."""
    bars = section.bars
    lines: list[Line] = []
    i = 0
    while i < len(bars):
        width = line_width(bars, i, slots_per_bar, meter)
        lines.append(Line(bars=list(bars[i : i + width]), repeat=1))
        i += width
    return lines


def _bar_key(bar: ScoreBar) -> tuple:
    return (
        tuple((c.name, c.start_slot) for c in bar.chords),
        tuple((s.slot, s.kind, s.rings) for s in bar.strokes),
        bar.grey,
        None if bar.tab is None else tuple(
            (t.slot, t.midi, t.string, t.fret, t.rings) for t in bar.tab
        ),
    )


def _line_key(line: Line) -> tuple:
    return tuple(_bar_key(b) for b in line.bars)


def fold_repeats(lines: list[Line]) -> list[Line]:
    """Collapse runs of consecutive identical lines into one carrying the count.

    Identical means the same chord names and start slots, strokes (slot, kind, rings), grey
    flag and tab on every bar; keys include the bar count, so widths never mix.
    """
    folded: list[Line] = []
    last_key: tuple | None = None
    for line in lines:
        key = _line_key(line)
        if folded and key == last_key:
            folded[-1].repeat += line.repeat
        else:
            folded.append(Line(bars=line.bars, repeat=line.repeat))
        last_key = key
    return folded


def repeat_text(n: int) -> str:
    """The repeat count in words for two and three, digits from four."""
    return _REPEAT_WORDS.get(n, f"play {n} times")
