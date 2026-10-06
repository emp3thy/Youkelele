from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.music.as_played import CHANCE_ALPHA
from youkelele.music.onsets import Onsets
import youkelele.music.pitch as pitch_module
from youkelele.music.pitch import PITCH_CHANGE_MIN, PitchTrack
from youkelele.music.recall import HIGH_BAND_FMIN
from youkelele.music.riff import is_riff, riff_features
from youkelele.music.ring import RING_SECTION_DB
from youkelele.options import RunOptions
from youkelele.schemas import Bar, ChordEvent, Chords, Grid, Key, Meter, Section, Strums
from youkelele.stage import StageContext
import youkelele.stages.strums as strums_module
from youkelele.stages.strums import StrumsStage

SR = 8000
BAR_SECONDS = 2.0  # 4/4 at 120 bpm
ISLAND = (0, 2, 3, 5, 6, 7)


@pytest.fixture(autouse=True)
def _quick_pitch(request, monkeypatch):
    """Skip pyin (seconds per run) unless the test asks for `real_pitch`.

    The test tones are single sines, so nearly every run passes the chroma features and
    would start the pitch tracker; the stub names no note, so no section is a riff.
    """
    if "real_pitch" not in request.fixturenames:
        monkeypatch.setattr(
            strums_module, "track_pitch", lambda y, sr: PitchTrack(times=np.zeros(0), midi=np.zeros(0))
        )


@pytest.fixture
def real_pitch():
    """The real pitch tracker (librosa pyin) for the tests about the riff flag."""
    return pitch_module.track_pitch


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


def test_strums_stage_short_section_keeps_its_own_vote_and_is_uncertain(tmp_path):
    # sections: 4 bars island, 2 bars of downbeats only, 6 bars of straight eighths.
    # Spec 4.5 (1.6): a short section no longer inherits a neighbour's pattern; it prints its
    # own vote, greyed when the chance test cannot pass (two one-strike bars: p near 0.13)
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
    assert "".join(short.slots) == "D-------"
    assert short.inherited_from is None
    assert short.uncertain
    assert not short.no_instrument
    assert "".join(strums.bar_onsets[4]) == "D-------"


def test_strums_stage_short_sections_use_their_own_vector_and_the_chance_test(tmp_path):
    # spec 4.5 (1.6): no section inherits and length alone does not grey a pattern; the
    # chance test decides (two identical island bars already pass it at p near 0.036)
    strums, _, _ = _run(tmp_path, _grid([2, 3]), _detector(_island(5)))
    for p in strums.patterns:
        assert "".join(p.slots) == "D-DU-UDU"
        assert p.inherited_from is None
        assert p.chance_p is not None and p.chance_p <= CHANCE_ALPHA
        assert not p.uncertain


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
    """Run the real member figures but replace the explained figure by member length."""
    real = strums_module.member_figures

    def fake(bars, vector, unit, slots_per_bar):
        confidence, repeat, _ = real(bars, vector, unit, slots_per_bar)
        return confidence, repeat, explained_for_bars(len(bars))

    monkeypatch.setattr(strums_module, "member_figures", fake)


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


def test_short_section_keeps_its_own_explained(tmp_path, monkeypatch):
    # spec 4.5 (1.6): nothing is copied from a neighbour, the short section's figures are its own
    _with_explained(monkeypatch, lambda n: {4: 0.2, 2: 0.4, 6: 0.7}[n])
    times = (
        [t for b in range(4) for t in _bar_times(b, ISLAND)]
        + [t for b in range(4, 6) for t in _bar_times(b, (0,))]
        + [t for b in range(6, 12) for t in _bar_times(b, range(8))]
    )
    strums, _, _ = _run(tmp_path, _grid([4, 2, 6]), _detector(times))
    first, short, last = strums.patterns
    assert (first.explained, last.explained) == (0.2, 0.7)
    assert short.inherited_from is None
    assert short.explained == 0.4


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


def _with_confidence(monkeypatch, confidence):
    """Run the real member figures but replace the confidence; explained stays the real 1.0."""
    real = strums_module.member_figures

    def fake(bars, vector, unit, slots_per_bar):
        _, repeat, explained = real(bars, vector, unit, slots_per_bar)
        return confidence, repeat, explained

    monkeypatch.setattr(strums_module, "member_figures", fake)


def _sixteenths(n_bars: int) -> list[float]:
    heavy = (0, 2, 4, 6, 8, 10, 3, 7, 11, 13)  # 120 bpm: chosen as 16 slots per bar
    return [t for b in range(n_bars) for t in _bar_times(b, heavy, n_slots=16)]


def test_confidence_floor_depends_on_the_grid(tmp_path, monkeypatch):
    _with_confidence(monkeypatch, 0.47)
    eighths, _, _ = _run(tmp_path / "eighths", _grid([8]), _detector(_island(8)))
    assert eighths.slots_per_bar == 8
    assert eighths.patterns[0].explained == 1.0
    assert not eighths.patterns[0].uncertain  # 0.47 clears the eighth-grid floor of 0.45
    sixteenths, _, _ = _run(tmp_path / "sixteenths", _grid([8]), _detector(_sixteenths(8)))
    assert sixteenths.slots_per_bar == 16
    assert sixteenths.patterns[0].explained == 1.0
    assert sixteenths.patterns[0].uncertain  # 0.47 is under the sixteenth-grid floor of 0.53


def test_strums_stage_skips_the_high_band_on_the_sixteenth_grid(tmp_path):
    detector = _detector(_sixteenths(8))
    strums, _, _ = _run(tmp_path, _grid([8]), detector)
    assert strums.slots_per_bar == 16
    assert detector.calls == [(SR, None)]  # the gate is off, so no second librosa pass
    assert not strums.patterns[0].recall_boost


def test_no_instrument_section_is_never_gated(tmp_path, monkeypatch):
    seen: list[int] = []
    real = strums_module.gate_section

    def spy(today, high, y, sr, bars, *args, **kwargs):
        seen.append(bars[0].index)
        return real(today, high, y, sr, bars, *args, **kwargs)

    monkeypatch.setattr(strums_module, "gate_section", spy)
    other = np.concatenate([_tone(8 * BAR_SECONDS, 0.3), np.zeros(int(8 * BAR_SECONDS * SR))])
    strums, _, _ = _run(tmp_path, _grid([8, 8]), _detector(_island(16)), other=other)
    assert strums.patterns[1].no_instrument
    assert seen == [0]  # only the first section, which has an instrument, reaches the gate


def test_trimmed_last_section_under_four_bars_votes_on_its_analysed_bars(tmp_path):
    # the outro is 5 bars, but its last 3 come after the last chord: 2 bars are analysed.
    # Spec 4.5 (1.6): it no longer takes the verse's pattern; it votes on its own two bars
    # (the island, so the same slots) and the chance test decides its certainty
    grid = _grid([8, 5])
    times = _island(10) + [t for b in range(10, 13) for t in _bar_times(b, range(8))]
    strums, _, _ = _run(
        tmp_path, grid, _detector(times), chords=_chords(grid, (0, 10, "C"), (10, 13, "N"))
    )
    verse, outro = strums.patterns
    assert not verse.uncertain and verse.inherited_from is None
    assert outro.inherited_from is None
    assert not outro.no_instrument
    assert outro.slots == verse.slots  # the trailing dense bars are not in its vote
    assert outro.strike_density == 0.75
    # two identical island bars pass the chance test (p near 0.036), so the outro is certain
    assert outro.chance_p <= CHANCE_ALPHA and not outro.uncertain


def test_strums_stage_logs_nothing_about_trailing_bars_when_none_dropped(tmp_path):
    lines: list[str] = []
    _run(tmp_path, _grid([8]), _detector(_island(8)), log=lines.append)
    assert not any("trailing" in line for line in lines)


def _wet_leg_outro(strike_in_outro: bool):
    # an 8-bar verse, then a 4-bar outro whose first bar is the only one analysed: the chords stop
    # at the end of the verse, so the outro is N and its last 3 bars are trimmed
    grid = _grid([8, 4])
    times = _island(8)
    if strike_in_outro:
        times = times + _bar_times(8, (0, 4))
    chords = _chords(grid, (0, 8, "C"), (8, 12, "N"))
    return grid, times, chords


def test_trimmed_all_n_outro_is_no_instrument(tmp_path):
    grid, times, chords = _wet_leg_outro(strike_in_outro=False)
    strums, _, _ = _run(tmp_path, grid, _detector(times), chords=chords)
    verse, outro = strums.patterns
    assert outro.no_instrument
    assert outro.inherited_from is None
    assert outro.slots == ["-"] * 8
    assert not verse.no_instrument


def test_trimmed_n_outro_with_a_strike_prints_its_own_vote_greyed(tmp_path):
    # spec 4.5 (1.6): the one analysed bar votes its own pattern; one bar cannot pass the
    # chance test, so it prints greyed rather than taking the verse's pattern
    grid, times, chords = _wet_leg_outro(strike_in_outro=True)
    strums, _, _ = _run(tmp_path / "struck", grid, _detector(times), chords=chords)
    outro = strums.patterns[1]
    assert not outro.no_instrument
    assert outro.inherited_from is None
    assert "".join(outro.slots) == "D---D---"
    assert outro.uncertain


# version 1.5: the section plan, the structure test and the riff marker (spec 3.3, 4.1, 4.3)


def _labelled_grid(spans: Sequence[tuple[str, int]]) -> Grid:
    """A grid whose sections carry the given labels and lengths in bars."""
    grid = _grid([n for _, n in spans])
    sections = [s.model_copy(update={"label": label}) for s, (label, _) in zip(grid.sections, spans)]
    return grid.model_copy(update={"sections": sections})


def _grid_with_fragment() -> Grid:
    # verse 0-16 and a six-bar verse 16-22 on the same chords: the plan makes them one verse
    return _labelled_grid([("verse", 16), ("verse", 6)])


def _per_bar(bar_slots: Sequence[Sequence[int]], n_slots: int = 8) -> list[float]:
    """Onset times striking the given slots in each bar, bar by bar."""
    return [t for b, slots in enumerate(bar_slots) for t in _bar_times(b, slots, n_slots=n_slots)]


# eight bars of four random strikes each (random.Random(0)): a vote that is not full and a chance p near 0.45
SPRAY = [(0, 3, 6, 7), (3, 4, 5, 7), (2, 3, 4, 7), (1, 2, 3, 4), (0, 2, 4, 6), (4, 5, 6, 7), (0, 2, 5, 7), (0, 3, 4, 5)]


def _notes(freqs_per_onset: Sequence[Sequence[float]], onsets: Sequence[float], seconds: float) -> np.ndarray:
    """Decaying sines (six harmonics at 1/k) from each onset, as tests/test_riff.py's `tone` builds them."""
    y = np.zeros(int(seconds * SR))
    t = np.arange(int(0.2 * SR)) / SR
    env = np.exp(-6.0 * t)
    for freqs, onset in zip(freqs_per_onset, onsets, strict=True):
        start = int(round(onset * SR))
        for f in freqs:
            for k in range(1, 7):
                y[start : start + t.size] += env * np.sin(2 * np.pi * f * k * t) / k
    return 0.5 * y / max(1.0, float(np.abs(y).max()))


def _run_notes(tmp_path, grid, detector, chords=None, other=None, mix_amp=0.5):
    lines: list[str] = []
    strums, ctx, _ = _run(
        tmp_path, grid, detector, chords=chords, other=other, mix_amp=mix_amp, log=lines.append
    )
    return strums, ctx.notes, lines


def test_strums_stage_writes_the_plan_and_one_pattern_per_planned_section(tmp_path):
    strums, _, _ = _run_notes(tmp_path, _grid_with_fragment(), _detector(_island(22)))
    assert [p.members for p in strums.plan] == [[0, 1]] and len(strums.patterns) == 1
    assert strums.patterns[0].section == 0
    assert (strums.plan[0].start_bar, strums.plan[0].end_bar, strums.plan[0].label) == (0, 22, "verse")
    assert len(strums.bar_onsets) == 22  # still one entry per grid bar


def test_merged_section_pattern_comes_from_its_longest_member(tmp_path):
    # member 0-16 strikes every eighth, member 16-22 only downbeats: the pattern is the 0-16 vote
    eighths_then_downbeats = _per_bar([range(8)] * 16 + [(0,)] * 6)
    strums, _, _ = _run_notes(tmp_path, _grid_with_fragment(), _detector(eighths_then_downbeats))
    assert strums.patterns[0].slots == ["D", "U"] * 4
    # a vote over all 22 bars prints the same slots, but the downbeat bars would lower these
    assert strums.patterns[0].confidence == 1.0 and strums.patterns[0].strike_density == 1.0
    assert "".join(strums.bar_onsets[16]) == "D-------"


def test_patterns_record_chance_p_and_density_and_a_random_section_is_uncertain(tmp_path):
    pattern_then_spray = _per_bar([ISLAND] * 8 + SPRAY)
    strums, _, _ = _run_notes(tmp_path, _grid([8, 8]), _detector(pattern_then_spray))
    certain, spray = strums.patterns
    assert certain.chance_p is not None and certain.chance_p <= 0.05 and not certain.uncertain
    assert certain.strike_density == 0.75
    assert spray.chance_p is not None and spray.chance_p > 0.05 and spray.uncertain
    assert spray.strike_density == 0.5


def test_full_vote_section_records_density_and_no_p(tmp_path):
    every_eighth = _per_bar([range(8)] * 8)
    strums, _, _ = _run_notes(tmp_path, _grid([8]), _detector(every_eighth))
    assert strums.patterns[0].chance_p is None and strums.patterns[0].strike_density == 1.0
    assert not strums.patterns[0].uncertain


def test_full_vote_below_the_density_floor_is_uncertain(tmp_path):
    # half the bars strike every eighth, the other half only the downbeat: the vote is full,
    # the density (8 + 1) / 16 = 0.5625 is under FULL_VOTE_DENSITY
    sparse_full = _per_bar([range(8), (0,)] * 4)
    strums, _, _ = _run_notes(tmp_path, _grid([8]), _detector(sparse_full))
    pattern = strums.patterns[0]
    assert pattern.slots == ["D", "U"] * 4
    assert pattern.chance_p is None and pattern.strike_density == 0.5625
    assert pattern.uncertain


def test_riff_flag_and_features_are_recorded_per_section(tmp_path, real_pitch):
    times = _island(16)
    seconds = 16 * BAR_SECONDS
    half = len(times) // 2
    g7 = [196.0, 246.9, 293.7, 349.2]  # four pitch classes, no doubled root
    # a line moving G, A, B flat (1.6 also needs the pitch to change, spec 5.1)
    line = [[(196.0, 220.0, 233.1)[i % 3]] for i in range(half)]
    # each half is scaled on its own, so the single notes are as loud as the chords
    single_notes_then_chords = (
        _notes(line, times[:half], seconds) + _notes([g7] * half, times[half:], seconds)
    )
    strums, _, _ = _run_notes(
        tmp_path, _grid([8, 8]), _detector(times), other=single_notes_then_chords, mix_amp=0.1
    )
    assert not any(p.no_instrument for p in strums.patterns)
    riff, strum = strums.patterns
    assert riff.riff and not strum.riff
    assert riff.pitch_change_share >= PITCH_CHANGE_MIN and strum.pitch_change_share is None
    assert riff.riff_entropy is not None and riff.riff_single_share is not None
    assert strum.riff_entropy is not None and strum.riff_entropy > riff.riff_entropy


def test_riff_features_rest_on_the_detectors_own_onsets_not_the_recall_gates(tmp_path, real_pitch):
    # the detector hears single notes on slots 0 and 4; the high band adds chords on 2, 5 and 6,
    # which the gate accepts (2 -> 5 strikes per bar). Read over the spliced list the chords
    # would be the majority and the section would lose its riff flag (spec 4.3).
    grid = _grid([8])
    seconds = 8 * BAR_SECONDS
    own = [t for b in range(8) for t in _bar_times(b, (0, 4))]
    gate = [t for b in range(8) for t in _bar_times(b, (2, 5, 6))]
    g7 = [196.0, 246.9, 293.7, 349.2]
    other = _notes([[196.0]] * len(own), own, seconds) + _notes([g7] * len(gate), gate, seconds)
    lines: list[str] = []
    strums, ctx, _ = _run(
        tmp_path, grid, _detector(own, high=sorted(own + gate)), other=other, mix_amp=0.1,
        log=lines.append,
    )
    (pattern,) = strums.patterns
    assert pattern.recall_boost and any("recall boost: section 0" in line for line in lines)
    assert "".join(pattern.slots) == "D-D-DUD-"  # the strum still counts the gate's onsets

    y, sr = strums_module._read_mono(ctx.input("separate/stems/other.wav"))
    expected = riff_features(strums_module._onset_chroma_at_riff_rate(y, sr, np.asarray(own)))
    spliced = riff_features(strums_module._onset_chroma_at_riff_rate(y, sr, np.asarray(sorted(own + gate))))
    assert not is_riff(*spliced)  # the post-gate list would hide the riff
    assert (pattern.riff_entropy, pattern.riff_single_share) == pytest.approx(expected)
    assert is_riff(*expected)
    assert pattern.riff_onsets == len(own)
    # spec 5.1 (1.6): the features pass, but no note is named: each 0.2 s note covers less than
    # half of the window to the next pre-gate onset (one second away), so the share is None
    assert not pattern.riff and pattern.pitch_change_share is None


def test_riff_onsets_count_only_the_longest_members_bars(tmp_path):
    # a 16-bar verse and a 6-bar fragment merged into it: the features rest on bars 0 to 16 only
    strums, _, _ = _run_notes(tmp_path, _grid_with_fragment(), _detector(_island(22)))
    assert strums.patterns[0].riff_onsets == 16 * len(ISLAND)


def test_no_instrument_section_has_no_riff_features_and_no_p(tmp_path):
    other = np.concatenate([_tone(8 * BAR_SECONDS, 0.3), np.zeros(int(8 * BAR_SECONDS * SR))])
    strums, _, _ = _run_notes(tmp_path, _grid([8, 8]), _detector(_island(16)), other=other)
    silent = next(p for p in strums.patterns if p.no_instrument)
    assert (silent.riff, silent.riff_entropy, silent.chance_p) == (False, None, None)
    assert (silent.riff_single_share, silent.strike_density, silent.riff_onsets) == (None, None, None)


def test_short_section_records_its_own_riff_features_and_p(tmp_path):
    # spec 4.5 (1.6): nothing is inherited, so a short section's chance test and riff
    # features describe its own bars
    times = (
        [t for b in range(4) for t in _bar_times(b, ISLAND)]
        + [t for b in range(4, 6) for t in _bar_times(b, (0,))]
        + [t for b in range(6, 12) for t in _bar_times(b, range(8))]
    )
    strums, _, _ = _run_notes(tmp_path, _grid([4, 2, 6]), _detector(times))
    short = strums.patterns[1]
    assert short.inherited_from is None
    assert short.riff_entropy is not None and short.riff_single_share is not None
    assert short.chance_p is not None and short.strike_density == 0.125 and short.riff_onsets == 2
    assert strums.patterns[2].strike_density == 1.0


def test_manifest_notes_merged_and_one_loop(tmp_path):
    _, notes, lines = _run_notes(tmp_path, _grid_with_fragment(), _detector(_island(22)))
    assert notes["merged"] == "2 grid sections into 1" and float(notes["one_loop"]) >= 0.85
    assert any("verse and chorus share their chords (share 1.00)" in line for line in lines)


def test_manifest_notes_no_merge_and_no_one_loop_line(tmp_path):
    grid = _labelled_grid([("verse", 8), ("chorus", 8)])
    chords = _chords(grid, (0, 8, "C"), (8, 16, "G"))
    strums, notes, lines = _run_notes(tmp_path, grid, _detector(_island(16)), chords=chords)
    assert [p.members for p in strums.plan] == [[0], [1]]
    assert notes["merged"] == "none" and notes["one_loop"] == "0.50"
    assert not any("share their chords" in line for line in lines)


# version 1.6: per-member votes, a record for every bar, the ring flag and the riff test
# (spec 4.1 to 4.5 and 5.1)

RINGING_TAU = 1.0  # seconds: about 2 dB lost per slot, well under RING_SECTION_DB
MUTED_TAU = 0.02  # seconds: the burst is gone within a slot


def _bar_patterns_times(bar_patterns: Sequence[str], first_bar: int = 0) -> list[float]:
    """Onset times, one per `S` cell of each bar's pattern string, from `first_bar` on."""
    return [
        t
        for b, pattern in enumerate(bar_patterns, start=first_bar)
        for t in _bar_times(b, [j for j, c in enumerate(pattern) if c == "S"], n_slots=len(pattern))
    ]


def _bursts_bars(
    bar_patterns: Sequence[str], bar_seconds: float = BAR_SECONDS, tau: float = RINGING_TAU,
    freqs: Sequence[float] = (220.0,),
) -> np.ndarray:
    """One decaying sine burst per `S` cell, each cut where the next begins (a new stroke damps the last).

    `tau` is the decay time constant in seconds; the bursts take `freqs` in turn, one per burst.
    """
    y = np.zeros(int(round(len(bar_patterns) * bar_seconds * SR)))
    starts = [
        int(round((b + j / len(pattern)) * bar_seconds * SR))
        for b, pattern in enumerate(bar_patterns)
        for j, c in enumerate(pattern)
        if c == "S"
    ]
    for i, start in enumerate(starts):
        stop = starts[i + 1] if i + 1 < len(starts) else len(y)
        t = np.arange(stop - start) / SR
        y[start:stop] = 0.5 * np.exp(-t / tau) * np.sin(2 * np.pi * freqs[i % len(freqs)] * t)
    return y


def _bursts(pattern: str, bars: int, bar_seconds: float = BAR_SECONDS, tau: float = RINGING_TAU) -> np.ndarray:
    """`bars` bars of the same pattern of 220 Hz bursts decaying with time constant `tau`."""
    return _bursts_bars([pattern] * bars, bar_seconds, tau)


def _midi_hz(midi: int) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def _run_bursts(tmp_path, grid, bar_patterns: Sequence[str], stem: np.ndarray, chords=None) -> Strums:
    strums, _, _ = _run(
        tmp_path, grid, _detector(_bar_patterns_times(bar_patterns)), other=stem, mix_amp=0.1, chords=chords
    )
    return strums


def test_bars_record_every_bar_with_its_pattern_and_strokes(tmp_path):
    s = _run_bursts(tmp_path, _grid([8]), ["S-S-S-SS"] * 8, _bursts("S-S-S-SS", 8, tau=RINGING_TAU))
    assert s.source == "other_stem"
    assert s.schema_version == 2 and len(s.bars) == 8
    assert [b.index for b in s.bars] == list(range(8))
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars) and all(b.member == 0 for b in s.bars)
    assert [k.slot for k in s.bars[0].strokes] == [0, 2, 4, 6, 7] and all(k.rings for k in s.bars[0].strokes)
    assert [k.kind for k in s.bars[0].strokes] == ["D", "D", "D", "D", "U"]
    # strokes two slots apart are measured; the next stroke one slot later cuts the last two short
    assert all(k.decay_db is not None and k.decay_db < RING_SECTION_DB for k in s.bars[0].strokes[:3])
    assert all(k.decay_db is None for k in s.bars[0].strokes[3:])
    assert s.patterns[0].candidate == "majority" and s.patterns[0].unit == 1 and s.patterns[0].rings is True
    assert s.patterns[0].ring_decay_db < RING_SECTION_DB and s.patterns[0].inherited_from is None
    assert not any(b.uncertain for b in s.bars) and not s.patterns[0].uncertain


def test_muted_playing_marks_the_section_short(tmp_path):
    s = _run_bursts(tmp_path, _grid([8]), ["S-S-S-SS"] * 8, _bursts("S-S-S-SS", 8, tau=MUTED_TAU))
    assert s.source == "other_stem"
    assert s.patterns[0].rings is False and all(not k.rings for k in s.bars[0].strokes)
    assert s.patterns[0].ring_decay_db > RING_SECTION_DB
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars)


# a four-bar fragment whose vote is the downbeat alone (S-------) but whose bars each add a
# stray strike: four identical one-strike bars would pass the chance test (p near 0.004)
STRAY_FRAGMENT = ["S--S----", "S----S--", "SS------", "S-----S-"]


def test_member_prints_its_own_pattern_when_it_disagrees(tmp_path):
    # grid sections: verse 8 bars S-S-S-SS, verse 4 bars voting S------- (a fragment, same
    # chords, merges); the fragment's own vote agrees 0.2 with the section's, under MEMBER_AGREE
    grid = _labelled_grid([("verse", 8), ("verse", 4)])
    bar_patterns = ["S-S-S-SS"] * 8 + STRAY_FRAGMENT
    s = _run_bursts(tmp_path, grid, bar_patterns, _bursts_bars(bar_patterns))
    merged = s.plan[0]
    assert merged.members == [0, 1] and len(s.patterns) == 1 and len(s.bars) == 12
    assert s.patterns[0].slots == list("D-D-D-DU") and not s.patterns[0].uncertain
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars[:8]) and not any(b.uncertain for b in s.bars[:8])
    assert all(b.pattern == list("D-------") for b in s.bars[8:12]) and all(b.uncertain for b in s.bars[8:12])
    assert [b.member for b in s.bars] == [0] * 8 + [1] * 4
    # the strokes are still every detected strike of the bar, the stray ones included
    assert [k.slot for k in s.bars[8].strokes] == [0, 3]


def test_member_prints_the_sections_pattern_when_it_agrees(tmp_path):
    # the fragment plays S-S-S-S- (agreement with S-S-S-SS is 0.8)
    grid = _labelled_grid([("verse", 8), ("verse", 4)])
    bar_patterns = ["S-S-S-SS"] * 8 + ["S-S-S-S-"] * 4
    s = _run_bursts(tmp_path, grid, bar_patterns, _bursts_bars(bar_patterns))
    assert s.plan[0].members == [0, 1]
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars[8:12])
    assert all(b.member == 1 and b.uncertain == s.patterns[0].uncertain for b in s.bars[8:12])
    assert [k.slot for k in s.bars[8].strokes] == [0, 2, 4, 6]  # what was played, not the pattern


def test_short_section_keeps_its_own_vote_greyed_not_a_neighbours(tmp_path):
    # sections of 8, 2 and 8 bars with different chords (no merge): the 2-bar one is uncertain
    # and keeps its own slots (spec 4.5)
    grid = _grid([8, 2, 8])
    bar_patterns = ["S-S-S-SS"] * 8 + ["S-------"] * 2 + ["SSSSSSSS"] * 8
    chords = _chords(grid, (0, 8, "C"), (8, 10, "G"), (10, 18, "F"))
    s = _run_bursts(tmp_path, grid, bar_patterns, _bursts_bars(bar_patterns), chords=chords)
    assert len(s.plan) == 3
    assert s.patterns[1].inherited_from is None and s.patterns[1].uncertain and s.patterns[1].slots != s.patterns[0].slots
    assert s.patterns[1].slots == list("D-------")
    assert all(b.pattern == list("D-------") and b.uncertain for b in s.bars[8:10])


def test_riff_flag_needs_the_pitch_change_share(tmp_path, monkeypatch, real_pitch):
    # guitar stem: bursts of ONE pitch per section (a power-chord root) versus a line moving
    # through MIDI 60, 62 and 63; both pass the 1.5 chroma features
    calls: list[int] = []

    def counting(y, sr):
        calls.append(sr)
        return real_pitch(y, sr)

    monkeypatch.setattr(strums_module, "track_pitch", counting)
    grid = _grid([8, 8])
    chords = _chords(grid, (0, 8, "C"), (8, 16, "G"))
    root = _bursts_bars(["S-S-S-SS"] * 8, freqs=(_midi_hz(45),))
    line = _bursts_bars(["S-S-S-SS"] * 8, freqs=tuple(_midi_hz(m) for m in (60, 62, 63)))
    s = _run_bursts(tmp_path, grid, ["S-S-S-SS"] * 16, np.concatenate([root, line]), chords=chords)
    assert is_riff(s.patterns[0].riff_entropy, s.patterns[0].riff_single_share)
    assert s.patterns[0].riff is False and s.patterns[0].pitch_change_share == 0.0
    assert s.patterns[1].riff is True and s.patterns[1].pitch_change_share >= PITCH_CHANGE_MIN
    assert not any(b.riff for b in s.bars[:8]) and all(b.riff for b in s.bars[8:])
    assert len(calls) == 1  # one pitch track for the whole song


def test_pitch_is_not_tracked_when_no_member_passes_the_chroma_features(tmp_path, monkeypatch):
    monkeypatch.setattr(strums_module, "track_pitch", lambda y, sr: pytest.fail("pitch tracked"))
    times = _island(8)
    g7 = [196.0, 246.9, 293.7, 349.2]
    s, _, _ = _run_notes(tmp_path, _grid([8]), _detector(times), other=_notes([g7] * len(times), times, 16.0), mix_amp=0.1)
    assert not s.patterns[0].riff and s.patterns[0].pitch_change_share is None


def test_single_bar_and_all_rest_members_do_not_raise(tmp_path):
    # a 1-bar section and a silent section both produce bars records, with an own or an
    # all-rest pattern and uncertain True
    grid = _grid([8, 1, 8])
    bar_patterns = ["S-S-S-SS"] * 8 + ["S---S---"] + ["--------"] * 8
    chords = _chords(grid, (0, 8, "C"), (8, 9, "G"), (9, 17, "F"))
    stem = _bursts_bars(bar_patterns, tau=0.2)
    s = _run_bursts(tmp_path, grid, bar_patterns, stem, chords=chords)
    assert len(s.bars) == 17 and [b.index for b in s.bars] == list(range(17))
    one = s.bars[8]
    assert one.pattern == list("D---D---") and one.uncertain and [k.slot for k in one.strokes] == [0, 4]
    assert s.patterns[1].uncertain and s.patterns[1].inherited_from is None
    assert s.patterns[2].no_instrument
    assert all(b.pattern == ["-"] * 8 and b.uncertain and b.strokes == [] and not b.riff for b in s.bars[9:])


def test_mix_source_marks_every_section_ringing(tmp_path):
    # spec 4.4: on the full mix the decay is meaningless, so every section rings
    times = _bar_patterns_times(["S-S-S-SS"] * 8)
    s, _, _ = _run(tmp_path, _grid([8]), _detector(times), guitar_amp=0.0, other_amp=0.0)
    assert s.source == "mix"
    assert s.patterns[0].rings is True and all(k.rings for b in s.bars for k in b.strokes)


def test_unit_two_member_prints_alternating_bars(tmp_path):
    # bars alternate between two distinct figures: the vote's unit is two bars and each bar
    # prints the matching half
    bar_patterns = ["S-S-S-S-", "SS-SS-SS"] * 4
    s = _run_bursts(tmp_path, _grid([8]), bar_patterns, _bursts_bars(bar_patterns))
    assert s.patterns[0].unit == 2 and s.patterns[0].slots == list("D-D-D-D-")
    assert [b.pattern for b in s.bars[:2]] == [list("D-D-D-D-"), list("DU-UD-DU")]
    assert all(b.unit == 2 for b in s.bars)
    assert s.patterns[0].confidence == 1.0



def _member(position, start, end, vector, riff=False, rings=True, uncertain=False):
    from youkelele.music.vote import VoteResult

    m = strums_module._Member(position=position, start=start, end=end, analysed_end=end, silent=False)
    m.vote = VoteResult(list(vector), "majority", 0.5, 0.5, 1)
    m.riff, m.rings, m.uncertain = riff, rings, uncertain
    return m


def test_a_riff_member_prints_its_own_pattern_even_when_it_agrees_with_the_section():
    # the member's vote S-S-S-S- agrees 0.8 with the section's S-S-S-SS (above MEMBER_AGREE)
    longest = _member(0, 0, 8, "S-S-S-SS")
    plain = _member(1, 8, 12, "S-S-S-S-")
    riff = _member(1, 8, 12, "S-S-S-S-", riff=True, uncertain=True)
    assert strums_module._prints_section(plain, longest, 8) is True
    assert strums_module._prints_section(riff, longest, 8) is False
    rendered = [["-"] * 8 for _ in range(12)]
    records = strums_module._bar_records(
        riff, longest, 8, Meter(numerator=4, denominator=4), rendered, lambda b: [None] * 8, [],
    )
    assert all(r.pattern == list("D-D-D-D-") and r.uncertain and r.riff for r in records)


def test_bar_records_carry_the_members_ring_flag_without_strokes():
    longest = _member(0, 0, 4, "S-S-S-SS", rings=False)
    rendered = [["-"] * 8 for _ in range(4)]
    records = strums_module._bar_records(
        longest, longest, 8, Meter(numerator=4, denominator=4), rendered, lambda b: [None] * 8, [],
    )
    assert all(r.strokes == [] and r.rings is False for r in records)


def test_a_two_bar_vote_is_tested_the_same_whichever_bar_the_member_starts_on():
    # a full bar alternating with a sparse one: from bar 0 the vote's first bar is full, from
    # bar 1 it is not; the whole unit vector is the representative, so both take the shuffle test
    classes = [list("SSSSSSSS"), list("S-S-S---")] * 5
    for start in (0, 1):
        m = strums_module._Member(position=0, start=start, end=start + 8, analysed_end=start + 8, silent=False)
        strums_module._vote_member(m, classes, 8, 0.45)
        assert m.vote.unit == 2 and m.chance_p is not None


def test_a_member_playing_the_sections_two_bar_figure_from_its_second_bar_prints_it_aligned(tmp_path):
    # the section alternates A, B from bar 0; the three-bar fragment merged into it plays B, A, B.
    # Its own one-bar vote is B, which agrees 0.43 with A, so it prints the section's pattern,
    # and must print it aligned to its own bars, not A, B, A
    a, b = "S-S-S-S-", "SS-SS-SS"
    grid = _labelled_grid([("verse", 8), ("verse", 3)])
    bar_patterns = [a, b] * 4 + [b, a, b]
    lines: list[str] = []
    s, _, _ = _run(
        tmp_path, grid, _detector(_bar_patterns_times(bar_patterns)), other=_bursts_bars(bar_patterns),
        mix_amp=0.1, log=lines.append,
    )
    assert s.plan[0].members == [0, 1] and s.patterns[0].unit == 2
    assert [r.pattern for r in s.bars[8:11]] == [list("DU-UD-DU"), list("D-D-D-D-"), list("DU-UD-DU")]
    assert [r.pattern for r in s.bars[8:11]] == [s.bar_onsets[i] for i in range(8, 11)]  # what it plays
    assert all(r.member == 1 and r.unit == 2 for r in s.bars[8:11])
    assert any("member 8-11 aligns" in line for line in lines)
