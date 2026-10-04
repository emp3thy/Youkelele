from __future__ import annotations

from pathlib import Path

import json

import numpy as np
import pytest
import soundfile as sf

from tests.audio_fixtures import write_chord_loop, write_click_track, write_drum_stem
from youkelele.jsonio import load_model
from youkelele.layout import RunLayout
from youkelele.models.beats import BeatResult
from youkelele.options import RunOptions
from youkelele.schemas import Grid
from youkelele.stage import StageContext
from youkelele.music.tempo import mean_bpm
from youkelele.stages import grid as grid_module
from youkelele.stages.grid import MIN_SECTION_BARS, GridStage


def _fake_detector(period: float, beats_per_bar: int, seconds: float):
    def detect(wav: Path) -> BeatResult:
        beats = [round(i * period, 6) for i in range(int(seconds / period))]
        return BeatResult(beats=beats, downbeats=beats[::beats_per_bar])

    return detect


def _write_vocals(path: Path, seconds: float, silent_until: float | None, sr: int = 22050) -> None:
    """A vocals stem: digital silence, or silence then a 330 Hz tone from `silent_until` on."""
    y = np.zeros(int(seconds * sr), dtype=np.float32)
    if silent_until is not None:
        t = np.arange(len(y)) / sr
        y = np.where(t >= silent_until, 0.3 * np.sin(2 * np.pi * 330.0 * t), 0.0).astype(np.float32)
    sf.write(str(path), y, sr, subtype="PCM_16")


def _ctx(
    tmp_path: Path,
    stage: GridStage,
    options: RunOptions,
    write_audio,
    hit_beats: tuple[int, ...] = (),
    bpm: float = 150,
    seconds: float = 24.0,
    vocals_silent_until: float | None = None,
) -> tuple[StageContext, list[str]]:
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid"])
    audio = layout.path("ingest/audio.wav")
    audio.parent.mkdir(parents=True)
    write_audio(audio)
    write_drum_stem(layout.path("separate/stems/drums.wav"), seconds, bpm, hit_beats)
    _write_vocals(layout.path("separate/stems/vocals.wav"), seconds, vocals_silent_until)
    out = tmp_path / "out"
    out.mkdir()
    messages: list[str] = []
    return StageContext(layout, options, out, messages.append, stage), messages


def test_grid_stage_writes_valid_grid_with_fake_detector(tmp_path):
    stage = GridStage(detector=_fake_detector(0.5, 3, 24.0))
    options = RunOptions(source="x.mp3", meter="3/4")
    ctx, messages = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.bpm == pytest.approx(120)
    assert grid.meter.numerator == 3
    assert grid.octave_decision == "none"
    assert len(grid.bars) == 16
    assert all(len(bar.beats) == 3 for bar in grid.bars)
    assert np.median([b.end - b.start for b in grid.bars]) == pytest.approx(1.5)
    assert grid.bars[-1].end == pytest.approx(24.0)
    assert len(grid.bar_loudness_db) == 16
    assert grid.sections[0].start_bar == 0 and grid.sections[-1].end_bar == 16
    assert 1 <= grid.sections_k <= 6
    log = "\n".join(messages)
    assert "median bar 1.50 s" in log
    assert "octave none" in log


def test_grid_stage_writes_beats_raw_with_insertions(tmp_path):
    from youkelele.schemas import BeatsRaw

    base = _fake_detector(0.5, 4, 24.0)

    def detect(wav: Path) -> BeatResult:
        found = base(wav)
        gone = found.beats[10]  # one missing beat; a bar start stays detected
        return BeatResult(beats=[b for b in found.beats if b != gone], downbeats=found.downbeats)

    stage = GridStage(detector=detect)
    ctx, _ = _ctx(tmp_path, stage, RunOptions(source="x.mp3"), lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    raw = load_model(ctx.output("grid/beats_raw.json"), BeatsRaw)
    assert "grid/beats_raw.json" in GridStage.produces
    assert raw.inserted_beats == [pytest.approx(5.0)]
    assert raw.dropped_beats == []
    assert 5.0 not in raw.detected_beats and len(raw.detected_beats) == 47
    assert raw.detected_downbeats == [pytest.approx(i * 2.0) for i in range(12)]


def test_grid_stage_beats_raw_lists_dropped_beats_on_halving(tmp_path):
    from youkelele.schemas import BeatsRaw

    stage = GridStage(detector=_fake_detector(0.25, 8, 24.0))  # a doubled-up detector
    options = RunOptions(source="x.mp3", beat_octave="half")
    ctx, _ = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    raw = load_model(ctx.output("grid/beats_raw.json"), BeatsRaw)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert len(raw.detected_beats) == 96 and raw.inserted_beats == []
    assert len(raw.dropped_beats) == 96 - len(grid.beats) > 0
    assert not set(raw.dropped_beats) & set(grid.beats)


def test_grid_stage_sections_k_override(tmp_path):
    stage = GridStage(detector=_fake_detector(0.5, 4, 32.0))
    options = RunOptions(source="x.mp3", sections_k=2)
    labels = ["C"] * 4 + ["F#"] * 4

    def audio(path: Path) -> None:
        write_chord_loop(path, labels, 2.0, bars=16)

    ctx, _ = _ctx(tmp_path, stage, options, audio)
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.sections_k == 2
    assert len(grid.bars) == 16
    assert grid.largest_cluster_share == pytest.approx(0.5)


def test_grid_stage_halves_a_double_tempo_detection(tmp_path):
    # 240 bpm detection; auto would keep it (120 is outside 60..95), so halve explicitly
    stage = GridStage(detector=_fake_detector(0.25, 8, 24.0))
    options = RunOptions(source="x.mp3", beat_octave="half")
    ctx, messages = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.octave_decision == "half"
    assert grid.bpm == pytest.approx(120)
    assert "octave half" in "\n".join(messages)


@pytest.mark.slow
def test_grid_stage_real_beat_this_on_click_track(tmp_path):
    stage = GridStage()
    options = RunOptions(source="x.mp3")
    ctx, _ = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 20.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert 118 <= grid.bpm <= 122
    assert grid.octave_decision == "none"  # 120 bpm is below the 140 halving threshold


def test_grid_stage_pickup_comes_from_bar_flag(tmp_path):
    def detect(wav: Path) -> BeatResult:
        beats = [round(0.5 + i * 0.5, 6) for i in range(11)]  # 0.5 .. 5.5 s
        return BeatResult(beats=beats, downbeats=[beats[1], beats[5], beats[9]])

    # 1-beat pickup (beat 0), then full bars starting at beats 1, 5, 9
    stage = GridStage(detector=detect)
    options = RunOptions(source="x.mp3", meter="4/4")
    ctx, _ = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 6.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.bars[0].pickup is True and grid.bars[0].beats == [0]
    assert all(not bar.pickup for bar in grid.bars[1:])
    assert grid.downbeats == [1, 5, 9]


def test_grid_stage_requires_drums_stem_and_records_backbeat(tmp_path):
    assert "separate/stems/drums.wav" in GridStage.requires
    stage = GridStage(detector=_fake_detector(0.4, 4, 24.0))  # 150 bpm
    options = RunOptions(source="x.mp3")
    ctx, messages = _ctx(
        tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 150), hit_beats=(1, 3)
    )
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.octave_decision == "none"
    assert grid.backbeat_ratio is not None and grid.backbeat_ratio > 1
    assert grid.drums_silent is False
    assert "backbeat ratio" in "\n".join(messages)


def test_grid_stage_halves_when_drums_stem_silent(tmp_path):
    stage = GridStage(detector=_fake_detector(0.4, 4, 24.0))
    options = RunOptions(source="x.mp3")
    ctx, messages = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 150))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.octave_decision == "half"
    assert grid.drums_silent is True
    assert "drums silent" in "\n".join(messages)


def test_grid_stage_backbeat_uses_modal_downbeat_phase(tmp_path):
    def detect(wav: Path) -> BeatResult:
        beats = [round(i * 0.4, 6) for i in range(60)]
        downbeats = [beats[i] for i in range(0, 60, 4)]
        downbeats[0] = beats[1]  # first detected downbeat is one beat off
        return BeatResult(beats=beats, downbeats=downbeats)

    stage = GridStage(detector=detect)
    ctx, _ = _ctx(
        tmp_path,
        stage,
        RunOptions(source="x.mp3"),
        lambda p: write_click_track(p, 24.0, 150),
        hit_beats=(1, 3),
    )
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.backbeat_ratio is not None and grid.backbeat_ratio > 1
    assert grid.octave_decision == "none"


def test_grid_stage_sections_are_at_least_four_bars(tmp_path, monkeypatch):
    # 24 s at 0.5 s per beat in 4/4 is 12 bars; clusters make a 2-bar middle segment
    clusters = [0] * 4 + [1] * 2 + [2] * 6
    monkeypatch.setattr(
        grid_module, "segment_bars", lambda features, k=None: (clusters, 3, 0.5)
    )
    stage = GridStage(detector=_fake_detector(0.5, 4, 24.0))
    ctx, _ = _ctx(tmp_path, stage, RunOptions(source="x.mp3"), lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert MIN_SECTION_BARS == 4
    assert len(grid.bars) == 12
    assert all(s.end_bar - s.start_bar >= 4 for s in grid.sections)
    assert [(s.start_bar, s.end_bar) for s in grid.sections] == [(0, 4), (4, 12)]


def test_grid_stage_bpm_is_mean_interval_octave_uses_median(tmp_path):
    # 0.4 s beats (150 bpm median) with every eighth interval stretched to 0.5 s
    beats = [0.0]
    for i in range(1, 60):
        beats.append(round(beats[-1] + (0.5 if i % 8 == 0 else 0.4), 6))

    def detect(wav: Path) -> BeatResult:
        return BeatResult(beats=beats, downbeats=beats[::4])

    stage = GridStage(detector=detect)
    ctx, messages = _ctx(
        tmp_path,
        stage,
        RunOptions(source="x.mp3"),
        lambda p: write_click_track(p, 26.0, 150),
        hit_beats=(1, 3),
        seconds=26.0,
    )
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.octave_decision == "none"
    assert grid.bpm == pytest.approx(mean_bpm(beats))
    assert grid.bpm < 150 - 1  # the median would read 150
    log = " ".join(messages)
    assert "150.0 bpm detected" in log
    assert f"{grid.bpm:.1f} bpm;" in log


def test_grid_stage_requires_vocals_and_stores_bar_vocal_db(tmp_path, monkeypatch):
    assert "separate/stems/vocals.wav" in GridStage.requires
    # 12 bars of 2 s; one cluster throughout; the vocals come in at 10 s (bar 5)
    monkeypatch.setattr(grid_module, "segment_bars", lambda features, k=None: ([0] * 12, 3, 1.0))
    stage = GridStage(detector=_fake_detector(0.5, 4, 24.0))
    ctx, messages = _ctx(
        tmp_path, stage, RunOptions(source="x.mp3"), lambda p: write_click_track(p, 24.0, 120),
        vocals_silent_until=10.0,
    )
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert len(grid.bar_vocal_db) == 12
    assert grid.bar_vocal_db[:5] == [-120.0] * 5
    tone_db = 20 * np.log10(0.3 / np.sqrt(2))
    assert all(abs(db - tone_db) < 0.1 for db in grid.bar_vocal_db[5:])
    # the run (0, 5) ends at bar 5, which becomes a boundary; the vocal-free start is the intro
    assert [(s.label, s.start_bar, s.end_bar) for s in grid.sections] == [
        ("intro", 0, 5), ("verse", 5, 12),
    ]
    assert "  vocal runs (0, 5)" in messages  # no trailing run here


def test_grid_stage_silent_vocals_stem_changes_nothing(tmp_path, monkeypatch):
    clusters = [0] * 4 + [1] * 4 + [0] * 4
    monkeypatch.setattr(grid_module, "segment_bars", lambda features, k=None: (clusters, 3, 0.67))
    stage = GridStage(detector=_fake_detector(0.5, 4, 24.0))
    ctx, messages = _ctx(
        tmp_path, stage, RunOptions(source="x.mp3"), lambda p: write_click_track(p, 24.0, 120)
    )
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.bar_vocal_db == [-120.0] * 12
    assert [(s.start_bar, s.end_bar) for s in grid.sections] == [(0, 4), (4, 8), (8, 12)]
    assert [s.label for s in grid.sections] == ["verse", "chorus", "verse"]
    assert "vocal runs none" in "\n".join(messages)


def test_grid_json_without_bar_vocal_db_loads(tmp_path):
    bars = [{"index": i, "start": 2.0 * i, "end": 2.0 * i + 2.0, "beats": [4 * i + j for j in range(4)]}
            for i in range(4)]
    data = {
        "schema": 1, "bpm": 120.0, "meter": {"numerator": 4, "denominator": 4},
        "beats": [0.5 * i for i in range(16)], "downbeats": [0, 4, 8, 12], "bars": bars,
        "sections": [{"label": "verse", "start_bar": 0, "end_bar": 4, "confidence": 0.5}],
        "octave_decision": "none", "bar_loudness_db": [-20.0] * 4, "sections_k": 1,
        "largest_cluster_share": 1.0, "chorus_margin_db": None, "labels_low_confidence": False,
    }
    path = tmp_path / "grid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    grid = load_model(path, Grid)
    assert grid.bar_vocal_db == []
    with pytest.raises(ValueError, match="bar_vocal_db"):
        Grid.model_validate({**data, "bar_vocal_db": [-20.0] * 3})
