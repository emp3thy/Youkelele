"""Turn a score section into chord-grid blocks: four bars per row, repeating rows collapsed."""

from __future__ import annotations

from dataclasses import dataclass

from youkelele.schemas import ScoreBar, ScoreSection, Shape

NC = "N.C."
MAX_UNIT = 4  # the longest run of rows a repeated block may span


@dataclass
class Cell:
    text: str
    nc: bool
    pickup: bool
    crowded: bool = False
    filled: bool = False  # every chord in the bar was inferred to fill a no-chord gap


@dataclass
class Block:
    rows: list[list[Cell]]
    repeat: int


@dataclass
class SectionGrid:
    pickup: Cell | None
    blocks: list[Block]


def cell_for(bar: ScoreBar) -> Cell:
    """One bar's cell: chord names in time order joined by " / ", or N.C. when it has none."""
    chords = sorted(bar.chords, key=lambda c: c.start_slot)
    names = [c.name for c in chords]
    if all(n == NC for n in names):
        return Cell(text=NC, nc=True, pickup=bar.pickup)
    return Cell(
        text=" / ".join(names),
        nc=False,
        pickup=bar.pickup,
        crowded=len(names) >= 3,
        filled=all(c.filled for c in chords),
    )


def _key(row: list[Cell]) -> tuple[str, ...]:
    """What makes two rows the same: their cell texts, which also fixes their length."""
    return tuple(c.text for c in row)


def _repeats(keys: list[tuple[str, ...]], start: int, unit: int) -> int:
    """How many times rows ``start:start+unit`` occur back to back from ``start``."""
    pattern = keys[start : start + unit]
    if len(pattern) < unit:
        return 0
    count = 1
    while keys[start + count * unit : start + (count + 1) * unit] == pattern:
        count += 1
    return count


def section_grid(section: ScoreSection, per_row: int = 4) -> SectionGrid:
    """A leading pickup bar, then rows of ``per_row`` cells grouped into repeating blocks.

    At each row, the unit of 1 to 4 rows and repeat count of at least 2 covering the most rows
    wins, ties going to the smaller unit; a row that starts no repeat is a block of its own.
    """
    cells = [cell_for(bar) for bar in section.bars]
    pickup = cells.pop(0) if cells and cells[0].pickup else None
    rows = [cells[i : i + per_row] for i in range(0, len(cells), per_row)]
    keys = [_key(r) for r in rows]
    blocks: list[Block] = []
    i = 0
    while i < len(rows):
        best_unit, best_count = 1, 1
        for unit in range(1, MAX_UNIT + 1):
            count = _repeats(keys, i, unit)
            if count >= 2 and unit * count > best_unit * best_count:
                best_unit, best_count = unit, count
        blocks.append(Block(rows=rows[i : i + best_unit], repeat=best_count))
        i += best_unit * best_count
    return SectionGrid(pickup=pickup, blocks=blocks)


def fret_notation(shape: Shape) -> str:
    """Absolute frets in diagram order, ``x`` for muted: "4322", or "9-9-10-12" past fret 9."""
    frets = [f if f <= 0 else f + shape.base_fret - 1 for f in shape.frets]
    marks = ["x" if f < 0 else str(f) for f in frets]
    return ("-" if any(f >= 10 for f in frets) else "").join(marks)
