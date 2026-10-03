from __future__ import annotations

from youkelele.render.grid import Cell, Row, cell_for, grid_rows
from youkelele.schemas import ScoreBar, ScoreChord, ScoreSection

ISLAND = list("D-DU-UDU")


def _chord(name: str, start: int = 0, end: int = 8) -> ScoreChord:
    return ScoreChord(
        name=name, diagram=-1 if name == "N.C." else 0, start_slot=start, slots=ISLAND[start:end]
    )


def _bar(index: int, *names: str, pickup: bool = False) -> ScoreBar:
    return ScoreBar(index=index, chords=[_chord(n) for n in names], pickup=pickup)


def _section(bars: list[ScoreBar]) -> ScoreSection:
    return ScoreSection(
        label="Verse", pattern=ISLAND, uncertain=False, bars=bars, bar_repeat=1.0,
        no_instrument=False,
    )


def _cycle(names: str, count: int, start: int = 0) -> list[ScoreBar]:
    seq = names.split()
    return [_bar(start + i, seq[i % len(seq)]) for i in range(count)]


def _texts(row: Row) -> list[str]:
    return [c.text for c in row.cells]


def test_cell_single_chord_name():
    assert cell_for(_bar(0, "Am")) == Cell(text="Am", nc=False, pickup=False)


def test_cell_mid_bar_change_joins_names_with_slash():
    # listed out of order to prove the cell sorts by start_slot
    bar = ScoreBar(index=0, chords=[_chord("G", 4, 8), _chord("C", 0, 4)])
    assert cell_for(bar).text == "C / G"
    assert cell_for(bar).nc is False


def test_cell_nc_bar():
    cell = cell_for(_bar(3, "N.C."))
    assert cell == Cell(text="N.C.", nc=True, pickup=False)
    empty = cell_for(ScoreBar(index=4, chords=[]))
    assert empty.text == "N.C." and empty.nc is True


def test_cell_copies_pickup_flag():
    assert cell_for(_bar(0, "C", pickup=True)).pickup is True


def test_grid_rows_chunks_into_fours():
    rows = grid_rows(_section(_cycle("C G Am F E7", 10)))
    assert [len(r.cells) for r in rows] == [4, 4, 2]
    assert [r.repeat for r in rows] == [1, 1, 1]
    assert _texts(rows[0]) == ["C", "G", "Am", "F"]


def test_grid_rows_collapses_identical_consecutive_rows():
    rows = grid_rows(_section(_cycle("G D", 12)))
    assert len(rows) == 1
    assert rows[0].repeat == 3
    assert _texts(rows[0]) == ["G", "D", "G", "D"]


def test_grid_rows_collapses_only_consecutive_rows():
    bars = _cycle("G D", 8) + _cycle("C F", 4, start=8) + _cycle("G D", 4, start=12)
    rows = grid_rows(_section(bars))
    assert [(_texts(r), r.repeat) for r in rows] == [
        (["G", "D", "G", "D"], 2),
        (["C", "F", "C", "F"], 1),
        (["G", "D", "G", "D"], 1),
    ]


def test_grid_rows_does_not_merge_short_final_row_into_full_row():
    rows = grid_rows(_section(_cycle("G D", 10)))
    assert [(_texts(r), r.repeat) for r in rows] == [
        (["G", "D", "G", "D"], 2),
        (["G", "D"], 1),
    ]


def test_grid_rows_one_bar_section():
    rows = grid_rows(_section([_bar(7, "F")]))
    assert rows == [Row(cells=[Cell(text="F", nc=False, pickup=False)], repeat=1)]


def test_grid_rows_empty_section():
    assert grid_rows(_section([])) == []


def test_grid_rows_pickup_bar_is_its_own_cell():
    bars = [_bar(0, "N.C.", pickup=True)] + _cycle("C G", 8, start=1)
    rows = grid_rows(_section(bars))
    assert len(rows[0].cells) == 1
    assert rows[0].cells[0].pickup is True and rows[0].repeat == 1
    assert [(_texts(r), r.repeat) for r in rows[1:]] == [(["C", "G", "C", "G"], 2)]


def test_grid_rows_pickup_only_when_first():
    bars = _cycle("C G", 2) + [_bar(2, "F", pickup=True)]
    rows = grid_rows(_section(bars))
    assert [len(r.cells) for r in rows] == [3]


def test_grid_rows_per_row_argument():
    rows = grid_rows(_section(_cycle("C G Am", 6)), per_row=3)
    assert [(_texts(r), r.repeat) for r in rows] == [(["C", "G", "Am"], 2)]
