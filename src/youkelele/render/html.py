"""Render a Score into a self-contained sheet page (HTML, CSS and inline SVG): a box per bar."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from youkelele.music.arrange import _SHARPS
from youkelele.music.score_builder import STATE_NO_INSTRUMENT, STATE_UNCERTAIN
from youkelele.render.bar_svg import bar_svg, slot_px
from youkelele.render.diagrams import NC, chord_diagram_svg, fret_notation
from youkelele.render.lines import fold_repeats, line_width, pack_lines, repeat_text
from youkelele.schemas import Score, ScoreBar, ScoreSection, Stroke

_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

CAPO_NOTE = "Shapes are relative to the capo"
POWER_LEGEND = "{name} is a power chord on the record"
POWER_LEGEND_EASY = "{name} is a power chord (root and fifth) on the record; this sheet prints the triad."
FILLED_NOTE = "Italic chords were inferred where the recording had no clear chord"
TAB_LEGEND = "Tab: A E C G top to bottom; numbers are frets. Re-entrant tuning: G is the high string."
# the two editorial legend lines every sheet prints (1.8 spec 3.1), verbatim
STROKE_LEGEND = "Stroke length is not measured: hold or damp each stroke as the record does."
DIRECTION_LEGEND = "Arrows follow the hand: down on the beat, up between. Direction is not read from the recording."
_OCTAVES = {1: "an octave", 2: "two octaves", 3: "three octaves"}


def display_names(labels: Sequence[str]) -> list[str]:
    """Section names as printed: `Verse 1`, `Verse 2`, `Chorus`, `Instrumental 1`, `Bridge`.

    A label that occurs once carries no number; one that recurs is numbered by occurrence,
    in order, ignoring case. The first letter is capitalised and the rest left as written.
    """
    totals = Counter(label.casefold() for label in labels)
    seen: Counter[str] = Counter()
    names: list[str] = []
    for label in labels:
        key = label.casefold()
        seen[key] += 1
        name = label[:1].upper() + label[1:]
        names.append(f"{name} {seen[key]}" if totals[key] > 1 else name)
    return names


def _capo(capo: int) -> str:
    return "none" if capo <= 0 else f"fret {capo}"


def _shape_key(key: str, capo: int) -> str:
    """The key the capo player's shapes are in: the tonic moved down by the capo, in sharps."""
    tonic, _, mode = key.partition(" ")
    flats = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
    pitch = _SHARPS.index(tonic) if tonic in _SHARPS else flats.index(tonic) if tonic in flats else None
    if pitch is None:
        return key
    shaped = _SHARPS[(pitch - capo) % 12]
    return f"{shaped} {mode}".strip()


def _key_fact(key: str, hedge: str | None, capo: int = 0) -> str:
    """The key as printed, `G major (or D major)` when hedged; both moved by the capo."""
    shaped = _shape_key(key, capo) if capo > 0 else key
    if hedge is None:
        return shaped
    return f"{shaped} (or {_shape_key(hedge, capo) if capo > 0 else hedge})"


def octave_phrase(shift: int) -> str | None:
    """The header's octave note (spec 3.2): "written an octave up", "written two octaves down"."""
    if shift == 0:
        return None
    size = abs(shift)
    return f"written {_OCTAVES.get(size, f'{size} octaves')} {'up' if shift > 0 else 'down'}"


def _derived_strokes(bar: ScoreBar) -> list[Stroke]:
    """A 1.5 bar's strokes: each chord's slot letters from its start slot, each flagged ``rings`` for the schema (the sheet draws no
    sustain lines)."""
    return [
        Stroke(slot=chord.start_slot + j, kind=cell, rings=True)
        for chord in sorted(bar.chords, key=lambda c: c.start_slot)
        for j, cell in enumerate(chord.slots)
        if cell != "-"
    ]


def _state_from_flags(section: ScoreSection) -> str:
    """A 1.5 section's header phrase: no instrument first, then an uncertain pattern."""
    if section.no_instrument:
        return STATE_NO_INSTRUMENT
    if section.uncertain:
        return STATE_UNCERTAIN
    return ""


def _with_strokes(score: Score) -> list[ScoreSection]:
    """The score's sections, a 1.5 file's bars given strokes from their chords' slots.

    A 1.5 score.json has no bar strokes at all; its uncertain sections then print their guess
    greyed, as a 1.6 score's do (spec 4.5), and a section without a state phrase gets the one
    its flags imply. A 1.6 score is returned as it is.
    """
    if any(bar.strokes for section in score.sections for bar in section.bars):
        return list(score.sections)
    return [
        section.model_copy(
            update={
                "state": section.state or _state_from_flags(section),
                "bars": [
                    bar.model_copy(
                        update={"strokes": _derived_strokes(bar), "grey": bar.grey or section.uncertain}
                    )
                    for bar in section.bars
                ]
            }
        )
        for section in score.sections
    ]


def _section_lines(section: ScoreSection, score: Score, power_badge: bool) -> list[dict]:
    """The section's lines, identical neighbours folded, each bar drawn as its box.

    A line's slot width follows how many bars its kind of line holds (four or eight), so a
    short last line keeps its section's bar size; a line with any tab bar draws the tab block
    on all its bars, so they stand level. The count row goes under the line's first full bar,
    so a line that starts with a partial pickup still counts from "1" (1.8 spec 3.2).
    """
    spb, meter = score.slots_per_bar, score.meter
    lines = pack_lines(section, spb, meter)
    widths: dict[int, int] = {}
    start = 0
    for line in lines:
        widths[id(line.bars)] = line_width(section.bars, start, spb, meter)
        start += len(line.bars)
    shown = []
    for line in fold_repeats(lines):
        per_slot = slot_px(spb, widths[id(line.bars)])
        tab_rows = any(bar.tab is not None for bar in line.bars)
        count_index = next((i for i, bar in enumerate(line.bars) if bar.pickup_slots is None), 0)
        svgs = [
            Markup(
                bar_svg(
                    bar, meter, spb, per_slot, first_in_line=i == count_index, grey=bar.grey,
                    tab_rows=tab_rows, power_badge=power_badge, pickup_slots=bar.pickup_slots,
                )
            )
            for i, bar in enumerate(line.bars)
        ]
        shown.append({"svgs": svgs, "repeat": repeat_text(line.repeat) if line.repeat > 1 else None})
    return shown


def render_html(score: Score) -> str:
    labels = [p[0].upper() for p in score.instrument.tuning]
    diagrams = [
        Markup(chord_diagram_svg(d.name, d.shape, string_labels=labels))
        for d in score.chord_diagrams
        if not d.passing
    ]
    passing = ", ".join(
        f"{d.name} {fret_notation(d.shape)}" for d in score.chord_diagrams if d.passing
    )
    # the shapes without the capo: only under one, each shape in fret notation, barres marked
    without_capo = ", ".join(
        f"{d.name} {fret_notation(d.shape)}{' (barre)' if d.shape.barres else ''}"
        for d in score.alternative_diagrams
    )
    # the badge belongs to the full tier; the easy tier prints the plain name and a legend line
    # saying the sheet prints the triad
    power_badge = score.tier == "full"
    legend = POWER_LEGEND if power_badge else POWER_LEGEND_EASY
    # one line per name: two shapes of one chord would otherwise print it twice
    power_names = dict.fromkeys(d.name for d in score.chord_diagrams if d.power)
    power_lines = [legend.format(name=name) for name in power_names]
    shown_sections = _with_strokes(score)
    bars = [bar for section in shown_sections for bar in section.bars]
    any_filled = any(chord.filled and chord.name != NC for bar in bars for chord in bar.chords)
    any_tab = any(bar.tab is not None for bar in bars)
    names = display_names([s.label for s in shown_sections])
    sections = [
        {
            "label": name,
            "state": section.state or None,
            "octave": octave_phrase(section.octave_shift),
            "lines": _section_lines(section, score, power_badge),
        }
        for name, section in zip(names, shown_sections)
    ]
    capo = score.instrument.capo
    return _ENV.get_template("sheet.html.j2").render(
        score=score,
        capo=_capo(capo),
        capo_note=CAPO_NOTE if capo > 0 else None,
        filled_note=FILLED_NOTE if any_filled else None,
        key_fact=(
            f"{_key_fact(score.key, score.key_hedge, capo)} (shapes)"
            if capo > 0
            else _key_fact(score.key, score.key_hedge)
        ),
        sounding_key=_key_fact(score.key, score.key_hedge) if capo > 0 else None,
        tempo=round(score.bpm),
        tuning=" ".join(score.instrument.tuning),
        diagrams=diagrams,
        passing=passing or None,
        without_capo=without_capo if capo > 0 and without_capo else None,
        power_badge=power_badge,
        power_lines=power_lines,
        tab_legend=TAB_LEGEND if any_tab else None,
        editorial_legend=[STROKE_LEGEND, DIRECTION_LEGEND],  # on every sheet (1.8 spec 3.1)
        sections=sections,
    )
