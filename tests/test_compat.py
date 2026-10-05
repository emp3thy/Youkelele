from __future__ import annotations

from pathlib import Path

from youkelele.jsonio import load_model
from youkelele.music.compat import backfill_bars, with_bars
from youkelele.schemas import Grid, Strums

FIXTURES = Path(__file__).parent / "fixtures"


def _v15() -> tuple[Strums, Grid]:
    return load_model(FIXTURES / "v15_strums.json", Strums), load_model(FIXTURES / "v15_grid.json", Grid)


def _plan_index(strums: Strums, bar: int) -> int:
    return next(k for k, p in enumerate(strums.plan) if p.start_bar <= bar < p.end_bar)


def test_backfill_gives_a_v15_file_one_bar_record_per_bar_with_the_section_pattern():
    s, g = _v15()
    assert s.bars == []
    bars = backfill_bars(s, g)
    assert [b.index for b in bars] == list(range(len(g.bars)))
    assert all(b.pattern == s.patterns[_plan_index(s, b.index)].slots for b in bars)
    assert all(k.rings and k.decay_db is None for b in bars for k in b.strokes)


def test_backfill_strokes_come_from_the_bar_onsets_and_flags_from_the_pattern():
    s, g = _v15()
    bars = backfill_bars(s, g)
    for b in bars:
        onsets = s.bar_onsets[b.index]
        assert [(k.slot, k.kind) for k in b.strokes] == [(j, c) for j, c in enumerate(onsets) if c != "-"]
        pattern = s.patterns[_plan_index(s, b.index)]
        assert (b.uncertain, b.riff, b.confidence, b.chance_p, b.unit) == (
            pattern.uncertain, pattern.riff, pattern.confidence, pattern.chance_p, pattern.unit,
        )


def test_backfill_member_is_the_grid_section_position_within_the_planned_section():
    s, g = _v15()
    bars = backfill_bars(s, g)
    # planned section 3 is bars 55 to 110 over grid sections 4 to 8 (55, 61, 90, 97, 104)
    assert [bars[i].member for i in (55, 60, 61, 89, 90, 97, 104, 109)] == [0, 0, 1, 1, 2, 3, 4, 4]
    assert {bars[i].member for i in range(0, 28)} == {0}


def test_with_bars_fills_only_an_empty_bars_list():
    s, g = _v15()
    filled = with_bars(s, g)
    assert len(filled.bars) == len(g.bars) and s.bars == []
    assert with_bars(filled, g) is filled
