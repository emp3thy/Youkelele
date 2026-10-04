"""The strum box: a section's pattern drawn once per example bar, its chords laid beneath.

Each bar is one column per slot with beat labels and arrows, over a chord row that puts every
chord name on the stroke it starts on.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from youkelele.render.grid import NC
from youkelele.schemas import Meter, ScoreBar, ScoreSection, Slot

_PER_SLOT = 28
_NARROW_SLOT = 20  # sixteenths: a two-bar example of 16 slots must fit the 688 px text width
_H = 60
_INK = "#111"
_BAR_GAP = 12  # between the bars of the worked example, with the bar line in the middle
_CHORD_H = 30  # the chord row under the example's strokes
_CHORD_INSET = 3  # a chord name starts this far right of its slot's left edge
_CHAR_PX = 9  # rough advance of a 14 px bold Arial character, for keeping dots clear of names
_SUBDIVISIONS = {1: ("",), 2: ("", "&"), 3: ("", "&", "a"), 4: ("", "e", "&", "a")}


def _label(index: int, per_beat: int) -> str:
    sub = index % per_beat
    if sub == 0:
        return str(index // per_beat + 1)
    return _SUBDIVISIONS.get(per_beat, ("",) * per_beat)[sub]


def _down(x: int) -> str:
    return (
        f'<g class="arrow down"><line x1="{x}" y1="22" x2="{x}" y2="46" stroke="{_INK}" stroke-width="2"/>'
        f'<path d="M{x - 5},42 L{x},50 L{x + 5},42" fill="none" stroke="{_INK}" stroke-width="2"/></g>'
    )


def _up(x: int) -> str:
    return (
        f'<g class="arrow up"><line x1="{x}" y1="52" x2="{x}" y2="28" stroke="{_INK}" stroke-width="2"/>'
        f'<path d="M{x - 5},32 L{x},24 L{x + 5},32" fill="none" stroke="{_INK}" stroke-width="2"/></g>'
    )


def _muted(x: int) -> str:
    return (
        f'<g class="arrow muted"><line x1="{x}" y1="22" x2="{x}" y2="46" stroke="{_INK}" stroke-width="2"/>'
        f'<path d="M{x - 5},42 L{x},50 L{x + 5},42" fill="none" stroke="{_INK}" stroke-width="2"/>'
        f'<line x1="{x - 5}" y1="30" x2="{x + 5}" y2="40" stroke="{_INK}" stroke-width="2"/>'
        f'<line x1="{x + 5}" y1="30" x2="{x - 5}" y2="40" stroke="{_INK}" stroke-width="2"/></g>'
    )


_ARROWS = {"D": _down, "U": _up, "x": _muted}


def slot_px(slots_per_bar: int) -> int:
    """Pixels per slot for a song: the box width up to eighths, narrower for sixteenths."""
    return _PER_SLOT if slots_per_bar <= 8 else _NARROW_SLOT


def _stroke_parts(slots: Sequence[Slot], meter: Meter, per_slot: int, ox: int = 0) -> list[str]:
    """One bar of the pattern: a framed row of beat labels and arrows, starting at x = ``ox``."""
    n = len(slots)
    width = n * per_slot
    per_beat = max(1, n // meter.numerator)
    parts = [
        f'<rect x="{ox + 0.5}" y="0.5" width="{width - 1}" height="{_H - 1}" fill="none" stroke="#bbb"/>'
    ]
    for i, slot in enumerate(slots):
        left = ox + i * per_slot
        x = left + per_slot // 2
        on_beat = i % per_beat == 0
        parts.append('<g class="slot">')
        if on_beat and i > 0:
            parts.append(
                f'<line x1="{left}" y1="4" x2="{left}" y2="{_H - 4}" stroke="#ddd"/>'
            )
        style = 'font-size="10" font-weight="bold" fill="#111"' if on_beat else 'font-size="9" fill="#666"'
        kind = "beat" if on_beat else "sub"
        parts.append(
            f'<text x="{x}" y="13" text-anchor="middle" {style} class="beat-label {kind}">'
            f"{_label(i, per_beat)}</text>"
        )
        draw = _ARROWS.get(slot)
        if draw is not None:
            parts.append(draw(x))
        parts.append("</g>")
    return parts


def _svg_open(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Arial, Helvetica, sans-serif">'
    )


def example_bars(section: ScoreSection) -> list[ScoreBar]:
    """The bars the worked example shows: the first two full bars (a leading pickup is skipped),
    unless neither changes chord mid-bar and a later bar does, which then replaces the second;
    one bar if the section has one. A section that is only a pickup shows the pickup."""
    full = section.bars[1:] if section.bars and section.bars[0].pickup else section.bars
    if not full:
        return list(section.bars)
    bars = full[:2]
    if len(bars) == 2 and all(len(b.chords) <= 1 for b in bars):
        change = next((b for b in full[2:] if len(b.chords) > 1), None)
        if change is not None:
            bars = [bars[0], change]
    return list(bars)


def _chord_parts(bar: ScoreBar, n: int, per_slot: int, ox: int) -> list[str]:
    """One bar's chord row under its strokes: each name on its start slot, a dot per held slot."""
    y = _H + 20
    parts = [
        f'<rect x="{ox + 0.5}" y="{_H + 0.5}" width="{n * per_slot - 1}" height="{_CHORD_H - 1}" '
        'fill="none" stroke="#bbb"/>'
    ]
    chords = sorted(bar.chords, key=lambda c: c.start_slot)
    spans = [(c.name, c.start_slot) for c in chords] or [(NC, 0)]  # a bar with no chord prints as N.C.
    for k, (name, start) in enumerate(spans):
        start = min(max(start, 0), n - 1)
        end = spans[k + 1][1] if k + 1 < len(spans) else n
        x = ox + start * per_slot
        if k > 0:
            parts.append(
                f'<line x1="{x}" y1="{_H + 2}" x2="{x}" y2="{_H + _CHORD_H - 2}" stroke="#ddd" '
                'class="change"/>'
            )
        parts.append(
            f'<text x="{x + _CHORD_INSET}" y="{y}" font-size="14" font-weight="bold" fill="{_INK}" '
            f'class="chord">{escape(name)}</text>'
        )
        name_end = x + _CHORD_INSET + _CHAR_PX * len(name)
        for slot in range(start + 1, min(end, n)):
            cx = ox + slot * per_slot + per_slot // 2
            if cx - 3 > name_end:  # a long name covers the first held slots; no dot under it
                parts.append(
                    f'<text x="{cx}" y="{y}" text-anchor="middle" font-size="14" fill="#666" '
                    'class="held">·</text>'
                )
    return parts


def worked_example_svg(
    pattern: Sequence[Slot], bars: Sequence[ScoreBar], meter: Meter, per_slot: int
) -> str:
    """The section's pattern once per bar with the bar's chords beneath, so each change sits
    under the stroke it falls on; bars are 12 px apart with a bar line between them. With no bars
    the pattern is still drawn once, over an N.C. row."""
    bars = list(bars) or [ScoreBar(index=0, chords=[])]
    n = len(pattern)
    bar_w = n * per_slot
    width = len(bars) * bar_w + _BAR_GAP * (len(bars) - 1)
    height = _H + _CHORD_H
    parts = [_svg_open(width, height)]
    for b, bar in enumerate(bars):
        ox = b * (bar_w + _BAR_GAP)
        if b > 0:
            lx = ox - _BAR_GAP // 2
            parts.append(
                f'<line x1="{lx}" y1="2" x2="{lx}" y2="{height - 2}" stroke="{_INK}" stroke-width="2" '
                'class="bar-line"/>'
            )
        parts.append('<g class="bar">')
        parts.extend(_stroke_parts(pattern, meter, per_slot, ox))
        parts.extend(_chord_parts(bar, n, per_slot, ox))
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)
