"""Turn a score section into chord-grid rows: four bars per row, identical rows collapsed."""

from __future__ import annotations

from dataclasses import dataclass

from youkelele.schemas import ScoreBar, ScoreSection

NC = "N.C."


@dataclass
class Cell:
    text: str
    nc: bool
    pickup: bool


@dataclass
class Row:
    cells: list[Cell]
    repeat: int


def cell_for(bar: ScoreBar) -> Cell:
    """One bar's cell: chord names in time order joined by " / ", or N.C. when it has none."""
    names = [c.name for c in sorted(bar.chords, key=lambda c: c.start_slot)]
    if all(n == NC for n in names):
        return Cell(text=NC, nc=True, pickup=bar.pickup)
    return Cell(text=" / ".join(names), nc=False, pickup=bar.pickup)


def grid_rows(section: ScoreSection, per_row: int = 4) -> list[Row]:
    """Rows of ``per_row`` cells; a leading pickup bar is a row of its own.

    Consecutive rows with the same cell texts and the same length collapse into one row whose
    ``repeat`` counts them; a short final row therefore never merges with a full row.
    """
    cells = [cell_for(bar) for bar in section.bars]
    rows: list[Row] = []
    if cells and cells[0].pickup:
        rows.append(Row(cells=[cells.pop(0)], repeat=1))
    lead = len(rows)
    for i in range(0, len(cells), per_row):
        chunk = cells[i : i + per_row]
        last = rows[-1] if len(rows) > lead else None
        if last is not None and [c.text for c in last.cells] == [c.text for c in chunk]:
            last.repeat += 1
        else:
            rows.append(Row(cells=chunk, repeat=1))
    return rows
