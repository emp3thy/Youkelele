from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.music.onsets import Onsets
from youkelele.music.recall import HIGH_BAND_FMIN
from youkelele.options import RunOptions
from youkelele.schemas import Bar, ChordEvent, Chords, Grid, Key, Meter, Section, Strums
from youkelele.stage import StageContext
import youkelele.stages.strums as strums_module
from youkelele.stages.strums import StrumsStage

SR = 8000
BAR_SECONDS = 2.0  # 4/4 at 120 bpm
ISLAND = (0, 2, 3, 5, 6, 7)


def _grid(section_bars: Sequence[int], numerator: int = 4) -> Grid:
    n_bars = sum(section_bars)
    beat = 0.5
    bar_seconds = beat * numerator
    beats = [i * beat for i in range(n_bars * numerator)]
    bars = [
        Bar(
            index=i, start=i * bar_seconds, end=(i + 1) * bar_seconds,
            beats=list(range(numerator * i, numerator * (i + 1))),
        )
        for i in range(n_bars)
    ]
    sections, start = [], 0
    for k, n in enumerate(section_bars):
        sections.append(Section(label=f"s{k}", start_bar=start, end_bar=start + n, confidence=0.5))
        start += n
    return Grid(
        bpm=120.0, meter=Meter(numerator=numerator, denominator=4), beats=beats,
        downbeats=[numerator * i for i in range(n_bars)], bars=bars, sections=sections,
        octave_decision="none", bar_loudness_db=[-20.0] * n_bars, sections_k=len(sections),
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _chords(grid: Grid, *spans: tuple[int, int, str]) -> Chords:
    """Chords over the grid; spans are (first bar, end bar, label), default one C over every bar."""
    spans = spans or ((0, len(grid.bars), "C"),)
    events = [
        ChordEvent(
            bar=a, beat=0, start=grid.bars[a].start, end=grid.bars[b - 1].end, label=lab, triad=lab, confidence=0.9
        )
        for a, b, lab in spans
    ]
    return Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=events)


def _tone(seconds: float, amp: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return amp * np.sin(2 * np.pi * 220.0 * t)


def _write(path: Path, mono: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.tile(mono[:, None], (1, 2)).astype(np.float32), SR, subtype="PCM_16")


def _ctx(
    tmp_path, stage, grid: Grid, guitar: np.ndarray, other: np.ndarray, mix: np.ndarray, options=None, log=None,
    chords: Chords | None = None,
):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony", "strums"])
    _write(layout.path("separate/stems/guitar.wav"), guitar)
    _write(layout.path("separate/stems/other.wav"), other)
    _write(layout.path("ingest/audio.wav"), mix)
    grid_path = layout.path("grid/grid.json")
    grid_path.parent.mkdir(parents=True)
    save_model(grid_path, grid)
    chords_path = layout.path("harmony/chords.json")
    chords_path.parent.mkdir(parents=True)
    save_model(chords_path, chords or _chords(grid))
    out = tmp_path / "out"
    out.mkdir()
    ctx = StageContext(layout, options or RunOptions(source="x.mp3"), out, log or (lambda m: None), stage)
    return ctx, out


def _detector(times: Sequence[float], muted_every: int = 0, high: Sequence[float] = ()):
    """Fake onset detector; every `muted_every`-th onset gets a low centroid and zcr.

    With `fmin` (the recall gate's high-band list) it returns `high` instead.
    """
    times = np.asarray(times, dtype=float)
    centroid = np.full(len(times), 2000.0)
    zcr = np.full(len(times), 0.1)
    if muted_every:
        centroid[::muted_every] = 500.0
        zcr[::muted_every] = 0.01
    high = np.asarray(high, dtype=float)
    calls: list[tuple[int, float | None]] = []

    def detect(y: np.ndarray, sr: int, fmin: float | None = None) -> Onsets:
        calls.append((sr, fmin))
        if fmin is not None:
            return Onsets(times=high.copy(), centroid=np.full(len(high), 2000.0), zcr=np.full(len(high), 0.1))
        return Onsets(times=times.copy(), centroid=centroid.copy(), zcr=zcr.copy())

    detect.calls = calls
    return detect


def _bar_times(bar: int, slots: Sequence[int], numerator: int = 4, n_slots: int = 8) -> list[float]:
    bar_seconds = 0.5 * numerator
    return [bar * bar_seconds + k * bar_seconds / n_slots for k in slots]


def _island(n_bars: int) -> list[float]:
    return [t for b in range(n_bars) for t in _bar_times(b, ISLAND)]


def _run(
    tmp_path, grid, detector, guitar_amp=0.0, other_amp=0.3, mix_amp=0.5, other=None, options=None, log=None,
    chords=None,
):
    seconds = grid.bars[-1].end
    stage = StrumsStage(onset_detector=detector)
    other_wave = _tone(seconds, other_amp) if other is None else other
    ctx, out = _ctx(
        tmp_path, stage, grid, _tone(seconds, guitar_amp), other_wave, _tone(seconds, mix_amp), options, log, chords
    )
    stage.run(ctx)
    return load_model(ctx.output("strums/strums.json"), Strums), ctx, out


def test_strums_stage_writes_onsets_txt_only_with_debug(tmp_path):
    times = _island(2)
    _, _, out = _run(tmp_path / "plain", _grid([2]), _detector(times, muted_every=6))
    assert not list(out.rglob("onsets.txt"))
    assert "strums/onsets.txt" not in StrumsStage.produces

    _, ctx, out = _run(
        tmp_path / "dbg", _grid([2]), _detector(times, muted_every=6),
        options=RunOptions(source="x.mp3", debug=True),
    )
    lines = (out / "onsets.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(times)
    rows = [line.split("\t") for line in lines]
    assert all(r[0] == r[1] and len(r) == 3 for r in rows)
    assert [float(r[0]) for r in rows] == pytest.approx(times, abs=1e-3)
    assert rows[0][0] == f"{times[0]:.3f}"
    assert [r[2] for r in rows] == ["x" if i % 6 == 0 else "S" for i in range(len(times))]


def test_strums_stage_uses_other_stem_when_louder(tmp_path):
    strums, ctx, _ = _run(tmp_path, _grid([8]), _detector(_island(8)), guitar_amp=0.05, other_amp=0.3)
    assert strums.source == "other_stem"
    assert abs(strums.source_ratio - 0.6) < 0.01
    assert ctx.notes["source"] == "other_stem"


def test_strums_stage_uses_mix_when_both_stems_silent_and_emits_no_x(tmp_path):
    detector = _detector(_island(8), muted_every=2)
    strums, ctx, _ = _run(tmp_path, _grid([8]), detector, guitar_amp=0.0, other_amp=0.0)
    assert strums.source == "mix"
    assert ctx.notes["source"] == "mix"
    assert all("x" not in bar for bar in strums.bar_onsets)
    assert all("x" not in p.slots for p in strums.patterns)
    assert "".join(strums.patterns[0].slots) == "D-DU-UDU"


def test_strums_stage_marks_muted_strikes_on_a_stem(tmp_path):
    # muted onsets (every 6th: slot 0 of each bar) on the other stem become x
    strums, _, _ = _run(tmp_path, _grid([8]), _detector(_island(8), muted_every=6))
    assert "".join(strums.patterns[0].slots) == "x-DU-UDU"


def test_strums_stage_flags_no_instrument_section(tmp_path):
    other = np.concatenate([_tone(8 * BAR_SECONDS, 0.3), np.zeros(int(8 * BAR_SECONDS * SR))])
    strums, _, _ = _run(tmp_path, _grid([8, 8]), _detector(_island(16)), other=other)
    first, second = strums.patterns
    assert not first.no_instrument
    assert "".join(first.slots) == "D-DU-UDU"
    assert second.no_instrument
    assert second.slots == ["-"] * 8
    assert second.confidence == 0.0
    assert second.bar_repeat == 0.0
    assert second.uncertain


def test_strums_stage_short_section_inherits_and_is_uncertain(tmp_path):
    # sections: 4 bars island, 2 bars of downbeats only, 6 bars of straight eighths
    times = (
        [t for b in range(4) for t in _bar_times(b, ISLAND)]
        + [t for b in range(4, 6) for t in _bar_times(b, (0,))]
        + [t for b in range(6, 12) for t in _bar_times(b, range(8))]
    )
    strums, _, _ = _run(tmp_path, _grid([4, 2, 6]), _detector(times))
    first, short, last = strums.patterns
    assert "".join(first.slots) == "D-DU-UDU"
    assert first.inherited_from is None
    assert "".join(last.slots) == "DUDUDUDU"
    assert short.slots == last.slots
    assert short.inherited_from == 2
    assert short.uncertain
    assert not short.no_instrument
    assert "".join(strums.bar_onsets[4]) == "D-------"


def test_strums_stage_short_section_without_long_neighbour_uses_its_own_vector(tmp_path):
    strums, _, _ = _run(tmp_path, _grid([2, 3]), _detector(_island(5)))
    for p in strums.patterns:
        assert "".join(p.slots) == "D-DU-UDU"
        assert p.inherited_from is None
        assert p.uncertain


def test_strums_stage_passes_grid_bpm_to_slot_choice(tmp_path):
    heavy = (0, 2, 4, 6, 8, 10, 3, 7, 11, 13)
    times = [t for b in range(8) for t in _bar_times(b, heavy, n_slots=16)]
    grid = _grid([8]).model_copy(update={"bpm": 158.0})
    strums, _, _ = _run(tmp_path, grid, _detector(times))
    assert strums.slots_per_bar == 8
    strums, _, _ = _run(tmp_path / "slow", _grid([8]), _detector(times))
    assert strums.slots_per_bar == 16


def test_strums_stage_one_pattern_per_section_and_valid_schema(tmp_path):
    detector = _detector(_island(12))
    strums, ctx, out = _run(tmp_path, _grid([4, 8]), detector)
    assert detector.calls == [(SR, None), (SR, HIGH_BAND_FMIN)]
    assert strums.slots_per_bar == 8
    assert strums.grid_fit == 1.0
    assert not strums.uncertain
    assert [p.section for p in strums.patterns] == [0, 1]
    for p in strums.patterns:
        assert "".join(p.slots) == "D-DU-UDU"
        assert p.confidence == 1.0
        assert p.bar_repeat == 1.0
        assert not p.uncertain
        assert not p.no_instrument
        assert p.inherited_from is None
    assert len(strums.bar_onsets) == 12
    assert all("".join(bar) == "D-DU-UDU" for bar in strums.bar_onsets)
    assert ctx.notes["grid_fit"] == "1.00"
    assert [p.name for p in out.rglob("*") if p.is_file()] == ["strums.json"]


def test_strums_stage_3_4_meter_gives_six_slots(tmp_path):
    times = [t for b in range(6) for t in _bar_times(b, (0, 2, 3, 5), numerator=3, n_slots=6)]
    strums, _, _ = _run(tmp_path, _grid([6], numerator=3), _detector(times))
    assert strums.slots_per_bar == 6
    assert "".join(strums.patterns[0].slots) == "D-DU-U"
    assert all(len(bar) == 6 for bar in strums.bar_onsets)


def test_strums_stage_marks_stage_uncertain_on_poor_grid_fit(tmp_path):
    width = BAR_SECONDS / 8
    times = [b * BAR_SECONDS + (k + 0.3) * width for b in range(8) for k in range(8)]
    strums, ctx, _ = _run(tmp_path, _grid([8]), _detector(times))
    assert strums.grid_fit < 0.6
    assert strums.uncertain
    assert float(ctx.notes["grid_fit"]) < 0.6


def _with_explained(monkeypatch, explained_for_bars):
    """Run the real section summary but replace its explained figure by section length."""
    real = strums_module.section_summary

    def fake(bars, slots_per_bar, meter):
        rendered, confidence, repeat, _ = real(bars, slots_per_bar, meter)
        return rendered, confidence, repeat, explained_for_bars(len(bars))

    monkeypatch.setattr(strums_module, "section_summary", fake)


def test_strums_stage_records_explained_on_each_pattern(tmp_path):
    strums, _, _ = _run(tmp_path, _grid([4, 8]), _detector(_island(12)))
    assert [p.explained for p in strums.patterns] == [1.0, 1.0]


def test_strums_stage_no_instrument_section_has_zero_explained(tmp_path):
    other = np.concatenate([_tone(8 * BAR_SECONDS, 0.3), np.zeros(int(8 * BAR_SECONDS * SR))])
    strums, _, _ = _run(tmp_path, _grid([8, 8]), _detector(_island(16)), other=other)
    assert strums.patterns[1].explained == 0.0


def test_stage_marks_uncertain_when_explained_low(tmp_path, monkeypatch):
    _with_explained(monkeypatch, lambda n: 0.59)
    strums, _, _ = _run(tmp_path, _grid([8]), _detector(_island(8)))
    pattern = strums.patterns[0]
    assert pattern.confidence == 1.0
    assert pattern.explained == 0.59
    assert pattern.uncertain


def test_stage_explained_at_the_threshold_is_not_uncertain(tmp_path, monkeypatch):
    _with_explained(monkeypatch, lambda n: 0.6)
    strums, _, _ = _run(tmp_path, _grid([8]), _detector(_island(8)))
    assert not strums.patterns[0].uncertain


def test_inherited_pattern_copies_explained(tmp_path, monkeypatch):
    _with_explained(monkeypatch, lambda n: 0.7 if n == 6 else 0.2)
    times = (
        [t for b in range(4) for t in _bar_times(b, ISLAND)]
        + [t for b in range(4, 6) for t in _bar_times(b, (0,))]
        + [t for b in range(6, 12) for t in _bar_times(b, range(8))]
    )
    strums, _, _ = _run(tmp_path, _grid([4, 2, 6]), _detector(times))
    first, short, last = strums.patterns
    assert (first.explained, last.explained) == (0.2, 0.7)
    assert short.inherited_from == 2
    assert short.explained == 0.7


def test_strums_stage_keeps_a_strike_played_in_half_the_bars(tmp_path):
    # slot 4 is struck in 4 of 8 bars: the old more-than-half vote erased it
    times = [t for b in range(8) for t in _bar_times(b, ISLAND + ((4,) if b % 2 == 0 else ()))]
    strums, _, _ = _run(tmp_path, _grid([8]), _detector(times))
    assert strums.patterns[0].slots[4] != "-"


def test_stage_sets_recall_boost_and_marks_added_onsets(tmp_path):
    # section 0: two strikes per bar today, the high band hears five; section 1: the island, dense
    base = [t for b in range(8) for t in _bar_times(b, (0, 4))] + [t for b in range(8, 16) for t in _bar_times(b, ISLAND)]
    high = [t for b in range(16) for t in _bar_times(b, (0, 2, 4, 5, 6))]
    lines: list[str] = []
    strums, _, out = _run(
        tmp_path, _grid([8, 8]), _detector(base, high=high),
        options=RunOptions(source="x.mp3", debug=True), log=lines.append,
    )
    sparse, dense = strums.patterns
    assert sparse.recall_boost
    assert "".join(sparse.slots) == "D-D-DUD-"
    assert all("".join(bar) == "D-D-DUD-" for bar in strums.bar_onsets[:8])
    assert not dense.recall_boost
    assert "".join(dense.slots) == "D-DU-UDU"
    assert all("".join(bar) == "D-DU-UDU" for bar in strums.bar_onsets[8:])
    assert strums.grid_fit == 1.0
    assert any("recall boost: section 0, 2.0 -> 5.0 strikes per bar" in line for line in lines)
    assert not any("recall boost: section 1" in line for line in lines)

    rows = [line.split("\t") for line in (out / "onsets.txt").read_text(encoding="utf-8").splitlines()]
    added = sorted(t for b in range(8) for t in _bar_times(b, (2, 5, 6)))
    assert len(rows) == len(base) + len(added)
    assert [float(r[0]) for r in rows if r[2] == "S+"] == pytest.approx(added, abs=1e-3)
    assert {r[2] for r in rows} == {"S", "S+"}
    assert [float(r[0]) for r in rows] == sorted(float(r[0]) for r in rows)


def test_stage_marks_a_muted_added_onset_x_plus():
    assert strums_module._onset_label(True, added=True) == "x+"
    assert strums_module._onset_label(False, added=True) == "S+"
    assert strums_module._onset_label(True) == "x"
    assert strums_module._onset_label(False) == "S"


def test_strums_stage_without_gain_leaves_recall_boost_off(tmp_path):
    strums, _, _ = _run(tmp_path, _grid([8]), _detector(_island(8), high=_island(8)))
    assert not strums.patterns[0].recall_boost
    assert all("".join(bar) == "D-DU-UDU" for bar in strums.bar_onsets)


def test_strums_stage_requires_the_chords():
    assert "harmony/chords.json" in StrumsStage.requires


def _noisy_tail():
    """Four bars of the island, then four bars of dense eighths that are not music."""
    return (
        [t for b in range(4) for t in _bar_times(b, ISLAND)]
        + [t for b in range(4, 8) for t in _bar_times(b, range(8))]
    )


def test_strums_stage_ignores_trailing_bars_in_last_section(tmp_path):
    grid = _grid([8])
    lines: list[str] = []
    strums, _, _ = _run(
        tmp_path, grid, _detector(_noisy_tail()), log=lines.append,
        chords=_chords(grid, (0, 4, "C"), (4, 8, "N")),
    )
    assert "".join(strums.patterns[0].slots) == "D-DU-UDU"
    assert strums.patterns[0].confidence == 1.0
    # the bar list still has one entry per grid bar, the trailing ones included
    assert len(strums.bar_onsets) == 8
    assert all("".join(bar) == "D-DU-UDU" for bar in strums.bar_onsets[:4])
    assert all("".join(bar) == "DUDUDUDU" for bar in strums.bar_onsets[4:])
    assert any("trailing" in line and "4" in line for line in lines)

    # with the noise counted as music the pattern is different, so the drop is what protects it
    noisy, _, _ = _run(tmp_path / "all", grid, _detector(_noisy_tail()))
    assert "".join(noisy.patterns[0].slots) != "D-DU-UDU"


def test_strums_stage_recall_gate_sees_only_the_music_bars(tmp_path, monkeypatch):
    seen: list[int] = []
    real = strums_module.gate_section

    def spy(today, high, y, sr, bars, *args, **kwargs):
        seen.append(len(bars))
        return real(today, high, y, sr, bars, *args, **kwargs)

    monkeypatch.setattr(strums_module, "gate_section", spy)
    grid = _grid([8])
    _run(tmp_path, grid, _detector(_noisy_tail()), chords=_chords(grid, (0, 4, "C"), (4, 8, "N")))
    assert seen == [4]


def test_strums_stage_logs_nothing_about_trailing_bars_when_none_dropped(tmp_path):
    lines: list[str] = []
    _run(tmp_path, _grid([8]), _detector(_island(8)), log=lines.append)
    assert not any("trailing" in line for line in lines)
