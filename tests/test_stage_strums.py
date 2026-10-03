from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.music.onsets import Onsets
from youkelele.options import RunOptions
from youkelele.schemas import Bar, Grid, Meter, Section, Strums
from youkelele.stage import StageContext
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


def _tone(seconds: float, amp: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return amp * np.sin(2 * np.pi * 220.0 * t)


def _write(path: Path, mono: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.tile(mono[:, None], (1, 2)).astype(np.float32), SR, subtype="PCM_16")


def _ctx(tmp_path, stage, grid: Grid, guitar: np.ndarray, other: np.ndarray, mix: np.ndarray):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony", "strums"])
    _write(layout.path("separate/stems/guitar.wav"), guitar)
    _write(layout.path("separate/stems/other.wav"), other)
    _write(layout.path("ingest/audio.wav"), mix)
    grid_path = layout.path("grid/grid.json")
    grid_path.parent.mkdir(parents=True)
    save_model(grid_path, grid)
    out = tmp_path / "out"
    out.mkdir()
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    return ctx, out


def _detector(times: Sequence[float], muted_every: int = 0):
    """Fake onset detector; every `muted_every`-th onset gets a low centroid and zcr."""
    times = np.asarray(times, dtype=float)
    centroid = np.full(len(times), 2000.0)
    zcr = np.full(len(times), 0.1)
    if muted_every:
        centroid[::muted_every] = 500.0
        zcr[::muted_every] = 0.01
    calls: list[int] = []

    def detect(y: np.ndarray, sr: int) -> Onsets:
        calls.append(sr)
        return Onsets(times=times.copy(), centroid=centroid.copy(), zcr=zcr.copy())

    detect.calls = calls
    return detect


def _bar_times(bar: int, slots: Sequence[int], numerator: int = 4, n_slots: int = 8) -> list[float]:
    bar_seconds = 0.5 * numerator
    return [bar * bar_seconds + k * bar_seconds / n_slots for k in slots]


def _island(n_bars: int) -> list[float]:
    return [t for b in range(n_bars) for t in _bar_times(b, ISLAND)]


def _run(tmp_path, grid, detector, guitar_amp=0.0, other_amp=0.3, mix_amp=0.5, other=None):
    seconds = grid.bars[-1].end
    stage = StrumsStage(onset_detector=detector)
    other_wave = _tone(seconds, other_amp) if other is None else other
    ctx, out = _ctx(tmp_path, stage, grid, _tone(seconds, guitar_amp), other_wave, _tone(seconds, mix_amp))
    stage.run(ctx)
    return load_model(ctx.output("strums/strums.json"), Strums), ctx, out


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


def test_strums_stage_one_pattern_per_section_and_valid_schema(tmp_path):
    detector = _detector(_island(12))
    strums, ctx, out = _run(tmp_path, _grid([4, 8]), detector)
    assert detector.calls == [SR]
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
