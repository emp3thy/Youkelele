"""Render a Score into a self-contained chord-grid sheet page (HTML, CSS and inline SVG)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from youkelele.render.diagrams import chord_diagram_svg
from youkelele.music.arrange import _SHARPS
from youkelele.render.grid import Cell, SectionGrid, fret_notation, section_grid
from youkelele.render.strum_box import example_bars, slot_px, worked_example_svg
from youkelele.schemas import Score

_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

CAPO_NOTE = "Shapes are relative to the capo"
FILLED_NOTE = "Italic chords were inferred where the recording had no clear chord"


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


def _shown_cells(grid: SectionGrid) -> list[Cell]:
    """Every cell the sheet prints for a section: the pickup, then each block's rows once."""
    lead = [grid.pickup] if grid.pickup is not None else []
    return lead + [cell for block in grid.blocks for row in block.rows for cell in row]


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
    sections = []
    any_filled = False
    per_slot = slot_px(score.slots_per_bar)
    for section in score.sections:
        source = section.inherited_from
        inherited = (
            score.sections[source].label
            if source is not None and 0 <= source < len(score.sections)
            else None
        )
        show_box = not (section.uncertain or section.no_instrument)
        grid = section_grid(section)
        any_filled = any_filled or any(cell.filled for cell in _shown_cells(grid))
        sections.append(
            {
                "label": section.label,
                "uncertain": section.uncertain,
                "explained": section.explained,
                "no_instrument": section.no_instrument,
                "inherited_from": inherited,
                "example": (
                    Markup(
                        worked_example_svg(section.pattern, example_bars(section), score.meter, per_slot)
                    )
                    if show_box
                    else None
                ),
                "grid": grid,
            }
        )
    capo = score.instrument.capo
    return _ENV.get_template("sheet.html.j2").render(
        score=score,
        capo=_capo(capo),
        capo_note=CAPO_NOTE if capo > 0 else None,
        filled_note=FILLED_NOTE if any_filled else None,
        key_fact=f"{_shape_key(score.key, capo)} (shapes)" if capo > 0 else score.key,
        sounding_key=score.key if capo > 0 else None,
        tempo=round(score.bpm),
        tuning=" ".join(score.instrument.tuning),
        diagrams=diagrams,
        passing=passing or None,
        sections=sections,
    )
