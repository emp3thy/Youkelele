"""Chord diagram SVGs (80 x 100 px), strings left to right in diagram order."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from youkelele.schemas import Shape

NC = "N.C."
_W, _H = 80, 100
_X0, _DX = 20, 14  # first string x, string spacing
_Y_NUT, _DY = 30, 15  # top of the grid, fret spacing
_INK = "#111"


def _fmt(value: float) -> str:
    return f"{value:g}"


def chord_diagram_svg(
    name: str,
    shape: Shape,
    string_labels: Sequence[str] = ("G", "C", "E", "A"),
    frets_shown: int = 4,
) -> str:
    """Draw ``shape`` as a standalone SVG; frets are relative to ``base_fret`` (row 1)."""
    strings = len(shape.frets)
    xs = [_X0 + i * _DX for i in range(strings)]
    right = xs[-1] if xs else _X0
    bottom = _Y_NUT + frets_shown * _DY

    def row_y(fret: int) -> float:
        return _Y_NUT + (fret - 0.5) * _DY

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_W}" height="{_H}" '
        f'viewBox="0 0 {_W} {_H}" font-family="Arial, Helvetica, sans-serif">',
        f'<text class="name" x="{_fmt((_X0 + right) / 2)}" y="13" text-anchor="middle" '
        f'font-size="12" font-weight="bold">{escape(name)}</text>',
    ]
    for x, fret in zip(xs, shape.frets):
        if fret < 0:
            parts.append(
                f'<text x="{x}" y="26" text-anchor="middle" font-size="9" class="muted">x</text>'
            )
        elif fret == 0:
            parts.append(
                f'<text x="{x}" y="26" text-anchor="middle" font-size="9" class="open">o</text>'
            )
    if shape.base_fret == 1:
        parts.append(
            f'<rect class="nut" x="{_X0 - 1}" y="{_Y_NUT - 2.5:g}" width="{right - _X0 + 2}" '
            f'height="3" fill="{_INK}"/>'
        )
    else:
        parts.append(
            f'<text x="{_X0 - 7}" y="{_fmt(row_y(1) + 3.5)}" text-anchor="end" '
            f'font-size="9.5" class="base-fret">{shape.base_fret}</text>'
        )
    for r in range(frets_shown + 1):
        y = _Y_NUT + r * _DY
        parts.append(
            f'<line x1="{_X0}" y1="{y}" x2="{right}" y2="{y}" stroke="{_INK}" stroke-width="1"/>'
        )
    for x in xs:
        parts.append(
            f'<line x1="{x}" y1="{_Y_NUT}" x2="{x}" y2="{bottom}" stroke="{_INK}" stroke-width="1"/>'
        )
    for barre in shape.barres:
        covered = [x for x, fret in zip(xs, shape.frets) if fret == barre]
        if not covered:
            continue
        y = row_y(barre)
        parts.append(
            f'<rect class="barre" x="{covered[0] - 5}" y="{_fmt(y - 4.5)}" '
            f'width="{covered[-1] - covered[0] + 10}" height="9" rx="4.5" fill="{_INK}"/>'
        )
    for x, fret, finger in zip(xs, shape.frets, shape.fingers):
        if fret <= 0:
            continue
        y = row_y(fret)
        parts.append(f'<circle cx="{x}" cy="{_fmt(y)}" r="5" fill="{_INK}"/>')
        if finger > 0:
            parts.append(
                f'<text x="{x}" y="{_fmt(y + 3)}" text-anchor="middle" font-size="7.5" '
                f'fill="#fff" font-weight="bold" class="finger">{finger}</text>'
            )
    for x, label in zip(xs, string_labels):
        parts.append(
            f'<text x="{x}" y="{bottom + 9}" text-anchor="middle" font-size="7" fill="#666" '
            f'class="string-label">{escape(label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def fret_notation(shape: Shape) -> str:
    """Absolute frets in diagram order, ``x`` for muted: "4322", or "9-9-10-12" past fret 9."""
    frets = [f if f <= 0 else f + shape.base_fret - 1 for f in shape.frets]
    marks = ["x" if f < 0 else str(f) for f in frets]
    return ("-" if any(f >= 10 for f in frets) else "").join(marks)
