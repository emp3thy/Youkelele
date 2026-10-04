"""Render a Score into a self-contained chord-grid sheet page (HTML, CSS and inline SVG)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
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
POWER_LEGEND = "{name} is a power chord on the record"
FILLED_NOTE = "Italic chords were inferred where the recording had no clear chord"


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
    # the shapes without the capo: only under one, each shape in fret notation, barres marked
    without_capo = ", ".join(
        f"{d.name} {fret_notation(d.shape)}{' (barre)' if d.shape.barres else ''}"
        for d in score.alternative_diagrams
    )
    # the badge and its legend line belong to the full tier; the easy tier prints the plain name
    power_badge = score.tier == "full"
    # one line per name: two shapes of one chord would otherwise print it twice
    power_names = dict.fromkeys(d.name for d in score.chord_diagrams if d.power)
    power_lines = [POWER_LEGEND.format(name=name) for name in power_names] if power_badge else []
    sections = []
    any_filled = False
    per_slot = slot_px(score.slots_per_bar)
    names = display_names([s.label for s in score.sections])
    for name, section in zip(names, score.sections):
        source = section.inherited_from
        inherited = names[source] if source is not None and 0 <= source < len(names) else None
        show_box = not (section.uncertain or section.no_instrument)
        grid = section_grid(section)
        any_filled = any_filled or any(cell.filled for cell in _shown_cells(grid))
        sections.append(
            {
                "label": name,
                "uncertain": section.uncertain,
                # truncated, not rounded, so 0.597 never prints as 60% beside a 60 percent threshold;
                # the epsilon keeps 0.29 (0.28999... in binary) at 29
                "explained_pct": int(section.explained * 100 + 1e-9),
                # a pre-1.3 score.json has no explained figure: a certain section then omits it
                "show_covers": section.explained > 0 or section.uncertain,
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
        sections=sections,
    )
