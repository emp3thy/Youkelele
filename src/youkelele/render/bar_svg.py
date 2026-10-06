"""The bar box: one inline SVG per bar (spec 3.1 to 3.4).

Top to bottom: the chord row (each name over the slot it starts on), the tab block on a riff
line (four string lines, A E C G from the top, a fret number where a note starts), the stroke
row (down, up and muted arrows, a sustain line where a ringing stroke is held over empty slots,
a faint dot on an empty slot), and, under the line's first bar only, the count row.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape

from youkelele.render.diagrams import NC
from youkelele.schemas import Meter, ScoreBar, ScoreChord

TEXT_WIDTH_PX = 688  # 182 mm at 96 px per inch: the printed page's text width
_MAX_SLOT = 28
_INK = "#111"
_GREY = "#999"
_FRAME = "#444"
_FAINT = "#bbb"

_CHORD_H = 18  # chord row; the name's baseline sits at 13
_CHORD_FONT = 13
_CHORD_INSET = 3  # a chord name starts this far right of its slot's left edge
_CHAR_PX = 8  # rough advance of a 13 px bold Arial character
_STRING_GAP = 9  # between the tab block's string lines
_TAB_H = 4 * _STRING_GAP + 2
_LABEL_W = 10  # the string-letter column left of a line's first tab bar
_STROKE_H = 30
_ARROW_TOP = 3  # the arrows' top inside the stroke row
_ARROW_LEN = 18
_PAD = 2.5  # the slot columns' inset from each side of the frame
_COUNT_H = 12
_SUBDIVISIONS = {1: ("",), 2: ("", "&"), 3: ("", "&", "a"), 4: ("", "e", "&", "a")}


def slot_px(slots_per_bar: int, bars_per_line: int) -> int:
    """Pixels per slot that fit ``bars_per_line`` bars in the page's text width."""
    return min(_MAX_SLOT, TEXT_WIDTH_PX // (bars_per_line * slots_per_bar))


def string_label_rows() -> list[str]:
    """The tab block's string letters from the top line down (re-entrant G is at the bottom)."""
    return ["A", "E", "C", "G"]


def _n(value: float) -> str:
    return f"{value:g}"


@dataclass(frozen=True)
class _Cols:
    """The bar's slot columns: ``n`` slots spread over the box less a ``_PAD`` inset each side,
    so the first and last arrows stand clear of the frame. Every row uses the same columns."""

    ox: float
    n: int
    box_w: float

    @property
    def pitch(self) -> float:
        return (self.box_w - 2 * _PAD) / self.n

    def left(self, slot: int) -> float:
        return self.ox + _PAD + slot * self.pitch

    def centre(self, slot: int) -> float:
        return self.left(slot) + self.pitch / 2


# the arrows of the 1.5 strum box, moved here: drawn from ``top`` in ``ink``, ``hw`` either side;
# down and up span the same height, top to top + _ARROW_LEN + 4
def _down(x: float, top: float, ink: str, hw: float, cw: float) -> str:
    end = top + _ARROW_LEN
    return (
        f'<g class="arrow down"><line x1="{_n(x)}" y1="{_n(top)}" x2="{_n(x)}" y2="{_n(end)}" stroke="{ink}" stroke-width="2"/>'
        f'<path d="M{_n(x - hw)},{_n(end - 4)} L{_n(x)},{_n(end + 4)} L{_n(x + hw)},{_n(end - 4)}" fill="none" stroke="{ink}" stroke-width="2"/></g>'
    )


def _up(x: float, top: float, ink: str, hw: float, cw: float) -> str:
    end = top + _ARROW_LEN
    return (
        f'<g class="arrow up"><line x1="{_n(x)}" y1="{_n(end + 4)}" x2="{_n(x)}" y2="{_n(top + 4)}" stroke="{ink}" stroke-width="2"/>'
        f'<path d="M{_n(x - hw)},{_n(top + 8)} L{_n(x)},{_n(top)} L{_n(x + hw)},{_n(top + 8)}" fill="none" stroke="{ink}" stroke-width="2"/></g>'
    )


def _muted(x: float, top: float, ink: str, hw: float, cw: float) -> str:
    """A down arrow crossed; the cross is ``cw`` either side, narrower than the head on narrow
    slots so neighbouring crosses stay apart."""
    end = top + _ARROW_LEN
    return (
        f'<g class="arrow muted"><line x1="{_n(x)}" y1="{_n(top)}" x2="{_n(x)}" y2="{_n(end)}" stroke="{ink}" stroke-width="2"/>'
        f'<path d="M{_n(x - hw)},{_n(end - 4)} L{_n(x)},{_n(end + 4)} L{_n(x + hw)},{_n(end - 4)}" fill="none" stroke="{ink}" stroke-width="2"/>'
        f'<line x1="{_n(x - cw)}" y1="{_n(top + 5)}" x2="{_n(x + cw)}" y2="{_n(top + 13)}" stroke="{ink}" stroke-width="2"/>'
        f'<line x1="{_n(x + cw)}" y1="{_n(top + 5)}" x2="{_n(x - cw)}" y2="{_n(top + 13)}" stroke="{ink}" stroke-width="2"/></g>'
    )


_ARROWS = {"D": _down, "U": _up, "x": _muted}


def _count_label(index: int, per_beat: int) -> str:
    sub = index % per_beat
    if sub == 0:
        return str(index // per_beat + 1)
    return _SUBDIVISIONS.get(per_beat, ("",) * per_beat)[sub]


def _held_until(start: int, starts: set[int], n: int) -> int:
    """The slot after the empty run following ``start``: the next start, or the bar end."""
    end = start + 1
    while end < n and end not in starts:
        end += 1
    return end


def _chord_row(chords: Sequence[ScoreChord], cols: _Cols, power_badge: bool, pickup: bool) -> list[str]:
    ordered = sorted(chords, key=lambda c: c.start_slot)
    n = cols.n
    parts: list[str] = []
    if not ordered or all(c.name == NC for c in ordered):
        parts.append(
            f'<text x="{_n(cols.ox + _CHORD_INSET)}" y="13" font-size="{_CHORD_FONT}" font-weight="bold" '
            f'fill="{_GREY}" class="chord nc">{NC}</text>'
        )
    else:
        for k, chord in enumerate(ordered):
            start = min(max(chord.start_slot, 0), n - 1)
            nxt = ordered[k + 1].start_slot if k + 1 < len(ordered) else n
            # the first name keeps the frame inset; a later one starts over its slot
            x = (cols.ox if start == 0 else cols.left(start)) + _CHORD_INSET
            room = cols.left(min(max(nxt, start + 1), n)) - x - 2
            nc = chord.name == NC
            badge = power_badge and chord.power and not nc
            style = ' font-style="italic"' if chord.filled and not nc else ""
            fill = _GREY if nc else _INK
            # a name wider than its room is squeezed, never run into the next chord's name
            est = _CHAR_PX * len(chord.name) + (6 if badge else 0)
            fit = (
                f' textLength="{_n(max(room, 6))}" lengthAdjust="spacingAndGlyphs"' if est > room else ""
            )
            text = escape(chord.name)
            if badge:
                text += '<tspan font-size="8" dy="-5" class="power">5</tspan>'
            parts.append(
                f'<text x="{_n(x)}" y="13" font-size="{_CHORD_FONT}" font-weight="bold"{style}{fit} '
                f'fill="{fill}" class="chord{" nc" if nc else ""}">{text}</text>'
            )
    if pickup:
        parts.append(
            f'<text x="{_n(cols.ox + cols.box_w - 2)}" y="8" text-anchor="end" font-size="7" font-style="italic" '
            f'fill="#666" class="pickup-label">pickup</text>'
        )
    return parts


def _tab_block(bar: ScoreBar, cols: _Cols, top: float, labels: bool) -> list[str]:
    letters = string_label_rows()
    n, ox = cols.n, cols.ox
    ys = [top + 5 + i * _STRING_GAP for i in range(4)]
    parts = ['<g class="tab">']
    for letter, y in zip(letters, ys):
        parts.append(
            f'<line x1="{_n(ox)}" y1="{_n(y)}" x2="{_n(ox + cols.box_w)}" y2="{_n(y)}" stroke="{_GREY}" '
            'stroke-width="0.8" class="string"/>'
        )
        if labels:
            parts.append(
                f'<text x="{_n(ox - 2)}" y="{_n(y + 3)}" text-anchor="end" font-size="8" fill="#666" '
                f'class="string-label">{letter}</text>'
            )
    notes = [t for t in (bar.tab or []) if 0 <= t.slot < n]
    starts = {t.slot for t in notes}
    for note in notes:
        row = 3 - note.string
        y = ys[row]
        x = cols.centre(note.slot)
        label = str(note.fret)
        half = 2.5 * len(label) + 1
        if note.rings:
            end = _held_until(note.slot, starts, n)
            if end > note.slot + 1:
                parts.append(
                    f'<line x1="{_n(x + half)}" y1="{_n(y)}" x2="{_n(cols.left(end) - 2)}" '
                    f'y2="{_n(y)}" stroke="{_INK}" stroke-width="2" class="sustain"/>'
                )
        parts.append(
            f'<rect x="{_n(x - half)}" y="{_n(y - 4.5)}" width="{_n(2 * half)}" height="9" fill="#fff"/>'
        )
        parts.append(
            f'<text x="{_n(x)}" y="{_n(y + 3)}" text-anchor="middle" font-size="9" font-weight="bold" '
            f'fill="{_INK}" class="fret" data-string="{letters[row]}">{label}</text>'
        )
    parts.append("</g>")
    return parts


def _stroke_row(bar: ScoreBar, cols: _Cols, top: float, ink: str) -> list[str]:
    n = cols.n
    strokes = {s.slot: s for s in bar.strokes if 0 <= s.slot < n}
    hw = min(5, (cols.pitch - 4) / 2)  # narrow slots keep a gap between neighbouring arrows
    cw = min(hw, max(2, (cols.pitch - 5) / 2))  # the muted cross: 2 to 2.5 px on narrow slots
    mid = top + _ARROW_TOP + 12
    held: set[int] = set()
    parts: list[str] = []
    for slot in sorted(strokes):
        stroke = strokes[slot]
        x = cols.centre(slot)
        parts.append(_ARROWS[stroke.kind](x, top + _ARROW_TOP, ink, hw, cw))
        end = _held_until(slot, set(strokes), n)
        # a muted strike is damped by definition: it never rings on, whatever its flag says
        if stroke.rings and stroke.kind != "x" and end > slot + 1:
            held.update(range(slot + 1, end))
            parts.append(
                f'<line x1="{_n(x + hw + 2)}" y1="{_n(mid)}" x2="{_n(cols.left(end) - 2)}" '
                f'y2="{_n(mid)}" stroke="{ink}" stroke-width="1.5" class="sustain"/>'
            )
    for slot in range(n):  # a faint dot on each slot nothing is played or held on
        if slot not in strokes and slot not in held:
            parts.append(
                f'<circle cx="{_n(cols.centre(slot))}" cy="{_n(mid)}" r="1.3" fill="{_FAINT}" class="rest"/>'
            )
    return parts


def _count_row(meter: Meter, cols: _Cols, top: float) -> list[str]:
    n = cols.n
    per_beat = max(1, n // meter.numerator)
    parts = []
    for i in range(n):
        x = cols.centre(i)
        beat = i % per_beat == 0
        style = f'font-size="9" font-weight="bold" fill="{_INK}"' if beat else 'font-size="8" fill="#777"'
        parts.append(
            f'<text x="{_n(x)}" y="{_n(top + 9)}" text-anchor="middle" {style} '
            f'class="count {"beat" if beat else "sub"}">{escape(_count_label(i, per_beat))}</text>'
        )
    return parts


def bar_svg(
    bar: ScoreBar,
    meter: Meter,
    slots_per_bar: int,
    per_slot: int,
    first_in_line: bool,
    grey: bool,
    tab_rows: bool,
    *,
    power_badge: bool = False,
) -> str:
    """One bar as an inline SVG.

    ``tab_rows`` draws the tab block (an empty one when the bar has no tab, so a line's bars
    stand level); ``first_in_line`` adds the string letters and the count row; ``grey`` draws
    the arrows and sustain lines in grey, the chord names staying black; ``power_badge`` raises
    a small 5 after a power chord's name (the full tier).
    """
    n = slots_per_bar
    ox = _LABEL_W if tab_rows and first_in_line else 0
    box_w = n * per_slot
    width = ox + box_w
    stroke_top = _CHORD_H + (_TAB_H if tab_rows else 0)
    box_h = stroke_top + _STROKE_H
    height = box_h + (_COUNT_H if first_in_line else 0)
    ink = _GREY if grey else _INK
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="bar" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Arial, Helvetica, sans-serif">'
    ]
    cols = _Cols(ox=ox, n=n, box_w=box_w)
    parts.extend(_chord_row(bar.chords, cols, power_badge, bar.pickup))
    if tab_rows:
        parts.extend(_tab_block(bar, cols, _CHORD_H, labels=first_in_line))
    parts.extend(_stroke_row(bar, cols, stroke_top, ink))
    parts.append(
        f'<rect x="{_n(ox + 0.5)}" y="0.5" width="{box_w - 1}" height="{box_h - 1}" fill="none" '
        f'stroke="{_FRAME}" stroke-width="1" rx="2" class="frame"/>'
    )
    if first_in_line:
        parts.extend(_count_row(meter, cols, box_h))
    parts.append("</svg>")
    return "".join(parts)
