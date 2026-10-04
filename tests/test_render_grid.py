from __future__ import annotations

from youkelele.render.grid import Block, Cell, SectionGrid, cell_for, fret_notation, section_grid
from youkelele.schemas import ScoreBar, ScoreChord, ScoreSection, Shape

ISLAND = list("D-DU-UDU")


def _chord(name: str, start: int = 0, end: int = 8, filled: bool = False) -> ScoreChord:
    return ScoreChord(
        name=name, diagram=-1 if name == "N.C." else 0, start_slot=start, slots=ISLAND[start:end],
        filled=filled,
    )


def _bar(index: int, *names: str, pickup: bool = False, filled: bool = False) -> ScoreBar:
    return ScoreBar(index=index, chords=[_chord(n, filled=filled) for n in names], pickup=pickup)


def _section(bars: list[ScoreBar]) -> ScoreSection:
    return ScoreSection(
        label="Verse", pattern=ISLAND, uncertain=False, bars=bars, bar_repeat=1.0,
        no_instrument=False,
    )


def _cycle(names: str, count: int, start: int = 0) -> list[ScoreBar]:
    seq = names.split()
    return [_bar(start + i, seq[i % len(seq)]) for i in range(count)]


def _texts(row: list[Cell]) -> list[str]:
    return [c.text for c in row]


def _row_bars(spec: str, start: int = 0) -> list[ScoreBar]:
    """Bars for rows written as "G D G D" -> four G bars then four D bars (one name per row)."""
    bars: list[ScoreBar] = []
    for name in spec.split():
        bars += [_bar(start + len(bars), name) for _ in range(4)]
    return bars


def _shape(grid: SectionGrid) -> list[tuple[list[list[str]], int]]:
    return [([_texts(r) for r in b.rows], b.repeat) for b in grid.blocks]


def test_cell_single_chord_name():
    assert cell_for(_bar(0, "Am")) == Cell(text="Am", nc=False, pickup=False)


def test_cell_mid_bar_change_joins_names_with_slash():
    # listed out of order to prove the cell sorts by start_slot
    bar = ScoreBar(index=0, chords=[_chord("G", 4, 8), _chord("C", 0, 4)])
    assert cell_for(bar).text == "C / G"
    assert cell_for(bar).nc is False


def test_cell_with_three_or_more_chords_is_crowded_and_cells_wrap():
    from pathlib import Path

    import youkelele

    assert cell_for(_bar(0, "C", "G", "Am", "F")).crowded is True
    assert cell_for(_bar(0, "C", "G")).crowded is False
    template = (Path(youkelele.__file__).parent / "render" / "templates" / "sheet.html.j2").read_text(
        encoding="utf-8"
    )
    assert "text-overflow: ellipsis" not in template
    assert ".cell.crowded" in template


def test_cell_power_marks_the_power_chords_of_the_bar():
    bar = ScoreBar(
        index=0,
        chords=[
            ScoreChord(name="G", diagram=0, start_slot=4, slots=list("DUDU")),
            ScoreChord(name="C#m", diagram=1, start_slot=0, slots=list("DUDU"), power=True),
        ],
    )
    cell = cell_for(bar)
    assert cell.text == "C#m / G" and cell.power is True and cell.badges == (True, False)
    assert cell_for(_bar(0, "Am")).power is False and cell_for(_bar(0, "Am")).badges == ()


def test_rows_with_the_same_names_but_a_different_power_flag_do_not_collapse():
    plain, power = _bar(0, "C#m"), ScoreBar(
        index=1, chords=[ScoreChord(name="C#m", diagram=0, start_slot=0, slots=list("DUDU"), power=True)]
    )
    section = ScoreSection(
        label="Verse", pattern=list("DUDU"), uncertain=False, bars=[plain] * 4 + [power] * 4,
        bar_repeat=1.0, no_instrument=False,
    )
    assert [b.repeat for b in section_grid(section).blocks] == [1, 1]


def test_cell_nc_bar():
    cell = cell_for(_bar(3, "N.C."))
    assert cell == Cell(text="N.C.", nc=True, pickup=False)
    empty = cell_for(ScoreBar(index=4, chords=[]))
    assert empty.text == "N.C." and empty.nc is True


def test_cell_copies_pickup_flag():
    assert cell_for(_bar(0, "C", pickup=True)).pickup is True


def test_section_grid_chunks_into_fours():
    grid = section_grid(_section(_cycle("C G Am F E7", 10)))
    assert grid.pickup is None
    assert [[len(r) for r in b.rows] for b in grid.blocks] == [[4], [4], [2]]
    assert [b.repeat for b in grid.blocks] == [1, 1, 1]
    assert _texts(grid.blocks[0].rows[0]) == ["C", "G", "Am", "F"]


def test_section_grid_single_identical_rows_still_collapse():
    grid = section_grid(_section(_cycle("G D", 12)))
    assert _shape(grid) == [([["G", "D", "G", "D"]], 3)]


def test_section_grid_collapses_alternating_two_row_block():
    grid = section_grid(_section(_row_bars("G D G D G D G D G D")))
    assert _shape(grid) == [([["G"] * 4, ["D"] * 4], 5)]


def test_section_grid_prefers_larger_coverage_then_smaller_unit():
    # A A B A A B: u=1 covers 2 rows, u=3 covers 6, so the three-row unit wins
    grid = section_grid(_section(_row_bars("A A B A A B")))
    assert _shape(grid) == [([["A"] * 4, ["A"] * 4, ["B"] * 4], 2)]
    # A A A A: u=1 x4 and u=2 x2 both cover 4 rows; the tie goes to the smaller unit
    grid = section_grid(_section(_row_bars("A A A A")))
    assert _shape(grid) == [([["A"] * 4], 4)]


def test_section_grid_remainder_after_block():
    grid = section_grid(_section(_row_bars("G D G D C")))
    assert _shape(grid) == [([["G"] * 4, ["D"] * 4], 2), ([["C"] * 4], 1)]


def test_section_grid_collapses_only_consecutive_rows():
    bars = _cycle("G D", 8) + _cycle("C F", 4, start=8) + _cycle("G D", 4, start=12)
    assert _shape(section_grid(_section(bars))) == [
        ([["G", "D", "G", "D"]], 2),
        ([["C", "F", "C", "F"]], 1),
        ([["G", "D", "G", "D"]], 1),
    ]


def test_section_grid_does_not_merge_short_final_row_into_full_row():
    assert _shape(section_grid(_section(_cycle("G D", 10)))) == [
        ([["G", "D", "G", "D"]], 2),
        ([["G", "D"]], 1),
    ]


def test_section_grid_short_final_row_never_joins_a_block():
    # G-row, D-row, G-row, then a two-bar D row: lengths differ so [G, D] repeats only once
    bars = _row_bars("G D G") + [_bar(12 + i, "D") for i in range(2)]
    assert _shape(section_grid(_section(bars))) == [
        ([["G"] * 4], 1),
        ([["D"] * 4], 1),
        ([["G"] * 4], 1),
        ([["D"] * 2], 1),
    ]


def test_section_grid_compares_text_not_filled_flag():
    bars = _row_bars("G") + [_bar(4 + i, "G", filled=True) for i in range(4)]
    grid = section_grid(_section(bars))
    assert _shape(grid) == [([["G"] * 4], 2)]


def test_section_grid_one_bar_section():
    grid = section_grid(_section([_bar(7, "F")]))
    assert grid == SectionGrid(
        pickup=None, blocks=[Block(rows=[[Cell(text="F", nc=False, pickup=False)]], repeat=1)]
    )


def test_section_grid_empty_section():
    assert section_grid(_section([])) == SectionGrid(pickup=None, blocks=[])


def test_section_grid_pickup_is_separate_from_blocks():
    bars = [_bar(0, "N.C.", pickup=True)] + _cycle("C G", 8, start=1)
    grid = section_grid(_section(bars))
    assert grid.pickup == Cell(text="N.C.", nc=True, pickup=True)
    # block detection runs after the pickup is taken off, so the two C G rows collapse
    assert _shape(grid) == [([["C", "G", "C", "G"]], 2)]
    assert all(not c.pickup for b in grid.blocks for r in b.rows for c in r)


def test_section_grid_pickup_only_section():
    grid = section_grid(_section([_bar(0, "C", pickup=True)]))
    assert grid.pickup is not None and grid.pickup.text == "C"
    assert grid.blocks == []


def test_section_grid_pickup_only_when_first():
    bars = _cycle("C G", 2) + [_bar(2, "F", pickup=True)]
    grid = section_grid(_section(bars))
    assert grid.pickup is None
    assert [[len(r) for r in b.rows] for b in grid.blocks] == [[3]]


def test_section_grid_per_row_argument():
    grid = section_grid(_section(_cycle("C G Am", 6)), per_row=3)
    assert _shape(grid) == [([["C", "G", "Am"]], 2)]


def test_cell_filled_when_all_chords_filled():
    both = ScoreBar(index=0, chords=[_chord("C", 0, 4, filled=True), _chord("G", 4, 8, filled=True)])
    assert cell_for(both).filled is True
    mixed = ScoreBar(index=0, chords=[_chord("C", 0, 4, filled=True), _chord("G", 4, 8)])
    assert cell_for(mixed).filled is False
    assert cell_for(_bar(0, "C")).filled is False
    assert cell_for(ScoreBar(index=0, chords=[])).filled is False


def test_fret_notation():
    assert fret_notation(Shape(frets=[4, 3, 2, 2], fingers=[3, 2, 1, 1], base_fret=1, barres=[2])) == "4322"


def test_fret_notation_muted_open_and_base_fret():
    # frets are relative to base_fret: row 1 at base_fret 5 is fret 5; open stays 0
    assert fret_notation(Shape(frets=[-1, 0, 1, 3], fingers=[0, 0, 1, 3], base_fret=5, barres=[])) == "x057"


def test_fret_notation_dashes_when_any_fret_reaches_ten():
    shape = Shape(frets=[1, 1, 2, 4], fingers=[1, 1, 2, 4], base_fret=9, barres=[1])
    assert fret_notation(shape) == "9-9-10-12"
