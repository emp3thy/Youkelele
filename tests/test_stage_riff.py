from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.music.pitch import PitchTrack
from youkelele.options import RunOptions
from youkelele.profiles.base import Tuning
from youkelele.schemas import Bar, BarStrums, Grid, Meter, PlannedSection, Riffs, Section, Stroke, Strums
from youkelele.stage import StageContext
from youkelele.stages.riff import RiffStage

SR = 22050
BAR_SECONDS = 4.0
SLOTS = 16
N_BARS = 4
TUNING = Tuning("gCEA", ("G4", "C4", "E4", "A4"), reentrant=True)
# the verified riff: nine notes on the C string, frets 0 0 2 2 0 2 3 2 0
RIFF_SLOTS = [0, 2, 3, 5, 6, 8, 10, 12, 14]
RIFF_MIDIS = [60, 60, 62, 62, 60, 62, 63, 62, 60]


def _grid() -> Grid:
    bars = [
        Bar(index=i, start=i * BAR_SECONDS, end=(i + 1) * BAR_SECONDS, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(N_BARS)
    ]
    return Grid(
        bpm=60.0, meter=Meter(numerator=4, denominator=4), beats=[float(i) for i in range(4 * N_BARS)],
        downbeats=[4 * i for i in range(N_BARS)], bars=bars,
        sections=[Section(label="verse", start_bar=0, end_bar=N_BARS, confidence=0.5)],
        octave_decision="none", bar_loudness_db=[-20.0] * N_BARS, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _strums(riff: bool, slots_per_bar: list[list[int]] | None = None) -> Strums:
    per_bar = slots_per_bar or [RIFF_SLOTS] * N_BARS
    bars = [
        BarStrums(
            index=i, member=0, strokes=[Stroke(slot=s, kind="D") for s in slots],
            pattern=["-"] * SLOTS, riff=riff, uncertain=False,
        )
        for i, slots in enumerate(per_bar)
    ]
    return Strums(
        slots_per_bar=SLOTS, source="guitar_stem", source_ratio=1.0, grid_fit=1.0, uncertain=False,
        patterns=[], bar_onsets=[["-"] * SLOTS for _ in range(N_BARS)],
        plan=[PlannedSection(start_bar=0, end_bar=N_BARS, label="verse", members=[0])], bars=bars,
    )


def _stem(per_bar_midis: list[list[int]], per_bar_slots: list[list[int]], silent: bool = False) -> np.ndarray:
    slot_s = BAR_SECONDS / SLOTS
    y = np.zeros(int(SR * BAR_SECONDS * N_BARS), dtype=np.float32)
    if silent:
        return y
    for b, (midis, slots) in enumerate(zip(per_bar_midis, per_bar_slots)):
        ends = slots[1:] + [SLOTS]
        for m, s, e in zip(midis, slots, ends):
            lo = int(SR * (b * BAR_SECONDS + s * slot_s))
            hi = int(SR * (b * BAR_SECONDS + e * slot_s))
            t = np.arange(hi - lo) / SR
            y[lo:hi] = 0.5 * np.sin(2 * np.pi * librosa.midi_to_hz(m) * t)
    return y


def _run(tmp_path, strums: Strums, stem: np.ndarray, log=None):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony", "strums", "riff"])
    for key in ("separate/stems/guitar.wav", "separate/stems/other.wav", "ingest/audio.wav"):
        path = layout.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), stem, SR)
    for key, model in (("grid/grid.json", _grid()), ("strums/strums.json", strums)):
        path = layout.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_model(path, model)
    out = tmp_path / "out"
    out.mkdir()
    stage = RiffStage(TUNING)
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, log or (lambda m: None), stage)
    stage.run(ctx)
    return load_model(ctx.output("riff/riff.json"), Riffs)


def test_riff_stage_writes_tab_for_a_steady_single_note_line(tmp_path):
    logs: list[str] = []
    r = _run(tmp_path, _strums(True), _stem([RIFF_MIDIS] * N_BARS, [RIFF_SLOTS] * N_BARS), logs.append)
    sec = r.sections[0]
    assert sec.printable and sec.octave_shift == 0 and sec.reason is None
    assert (sec.section, sec.start_bar, sec.end_bar) == (0, 0, N_BARS)
    assert [n.fret for n in sec.riff] == [0, 0, 2, 2, 0, 2, 3, 2, 0]
    assert all(n.string == 1 for n in sec.riff)
    assert len(sec.onsets) == N_BARS and [n.midi for n in sec.onsets[0]] == RIFF_MIDIS
    assert any(line.endswith(": printable") and line.startswith("section 0 bars 0-3:") for line in logs)


def test_riff_stage_marks_unsteady_or_unvoiced_sections_not_transcribed(tmp_path):
    silent = _run(tmp_path / "a", _strums(True), _stem([], [], silent=True))
    sec = silent.sections[0]
    assert sec.named_share == 0.0
    assert not sec.printable and sec.riff == [] and sec.reason is not None
    assert sec.reason.startswith("named")

    rng = np.random.default_rng(3)
    midis = [[int(m) for m in rng.integers(55, 80, len(RIFF_SLOTS))] for _ in range(N_BARS)]
    logs: list[str] = []
    noisy = _run(tmp_path / "b", _strums(True), _stem(midis, [RIFF_SLOTS] * N_BARS), logs.append)
    sec = noisy.sections[0]
    assert not sec.printable and sec.riff == [] and sec.reason is not None
    assert sec.reason.startswith("agreement")
    assert any(": not transcribed (agreement" in line for line in logs)


def test_riff_stage_writes_an_empty_file_when_no_section_is_a_riff(tmp_path):
    r = _run(tmp_path, _strums(False), _stem([RIFF_MIDIS] * N_BARS, [RIFF_SLOTS] * N_BARS))
    assert r.sections == []


def test_riff_stage_reads_a_v15_strums_file_through_its_backfilled_bars(tmp_path):
    # a 1.5 folder resumed from the riff stage: strums.json has no bar records, only patterns
    fixtures = Path(__file__).parent / "fixtures"
    strums = load_model(fixtures / "v15_strums.json", Strums)
    grid = load_model(fixtures / "v15_grid.json", Grid)
    assert strums.bars == []
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony", "strums", "riff"])
    for key in ("separate/stems/guitar.wav", "separate/stems/other.wav", "ingest/audio.wav"):
        path = layout.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), np.zeros(SR, dtype=np.float32), SR)
    for key, model in (("grid/grid.json", grid), ("strums/strums.json", strums)):
        path = layout.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_model(path, model)
    out = tmp_path / "out"
    out.mkdir()

    def steady_c(y: np.ndarray, sr: int) -> PitchTrack:
        times = np.arange(0.0, grid.bars[-1].end, 0.01)
        return PitchTrack(times=times, midi=np.full(times.shape, 60.0))

    stage = RiffStage(TUNING, pitch_tracker=steady_c)
    stage.run(StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage))
    r = load_model(out / "riff.json", Riffs)

    riff_sections = {k for k, p in enumerate(strums.patterns) if p.riff}
    assert riff_sections  # the fixture flags riffs on its patterns
    expected = [
        (k, grid.sections[m].start_bar, grid.sections[m].end_bar)
        for k in sorted(riff_sections)
        for m in strums.plan[k].members
    ]
    assert [(s.section, s.start_bar, s.end_bar) for s in r.sections] == expected
