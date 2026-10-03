"""Strum pattern box SVG: one 28 px column per slot with beat labels and arrows."""

from __future__ import annotations

from collections.abc import Sequence

from youkelele.schemas import Meter, Slot

_PER_SLOT = 28
_H = 60
_INK = "#111"
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


def strum_pattern_svg(slots: Sequence[Slot], meter: Meter) -> str:
    n = len(slots)
    width = n * _PER_SLOT
    per_beat = max(1, n // meter.numerator)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{_H}" '
        f'viewBox="0 0 {width} {_H}" font-family="Arial, Helvetica, sans-serif">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{_H - 1}" fill="none" stroke="#bbb"/>',
    ]
    for i, slot in enumerate(slots):
        x = i * _PER_SLOT + _PER_SLOT // 2
        on_beat = i % per_beat == 0
        parts.append('<g class="slot">')
        if on_beat and i > 0:
            parts.append(
                f'<line x1="{i * _PER_SLOT}" y1="4" x2="{i * _PER_SLOT}" y2="{_H - 4}" stroke="#ddd"/>'
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
    parts.append("</svg>")
    return "".join(parts)
