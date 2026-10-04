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


def _with_confidence(monkeypatch, confidence):
    """Run the real section summary but replace its confidence; explained stays the real 1.0."""
    real = strums_module.section_summary

    def fake(bars, slots_per_bar, meter):
        rendered, _, repeat, explained = real(bars, slots_per_bar, meter)
        return rendered, confidence, repeat, explained

    monkeypatch.setattr(strums_module, "section_summary", fake)


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


def test_trimmed_last_section_under_four_bars_is_short_uncertain_and_inherited(tmp_path):
    # the outro is 5 bars, but its last 3 come after the last chord: 2 bars are analysed, so it
    # is short and takes the verse's pattern, as Wet Leg's one-bar outro does
    grid = _grid([8, 5])
    times = _island(10) + [t for b in range(10, 13) for t in _bar_times(b, range(8))]
    strums, _, _ = _run(
        tmp_path, grid, _detector(times), chords=_chords(grid, (0, 10, "C"), (10, 13, "N"))
    )
    verse, outro = strums.patterns
    assert not verse.uncertain and verse.inherited_from is None
    assert outro.inherited_from == 0
    assert outro.uncertain
    assert not outro.no_instrument
    assert outro.slots == verse.slots


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


def test_trimmed_n_outro_with_a_strike_is_still_inherited(tmp_path):
    grid, times, chords = _wet_leg_outro(strike_in_outro=True)
    strums, _, _ = _run(tmp_path / "struck", grid, _detector(times), chords=chords)
    outro = strums.patterns[1]
    assert not outro.no_instrument
    assert outro.inherited_from == 0
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


def test_riff_flag_and_features_are_recorded_per_section(tmp_path):
    times = _island(16)
    seconds = 16 * BAR_SECONDS
    half = len(times) // 2
    g7 = [196.0, 246.9, 293.7, 349.2]  # four pitch classes, no doubled root
    # each half is scaled on its own, so the single notes are as loud as the chords
    single_notes_then_chords = (
        _notes([[196.0]] * half, times[:half], seconds) + _notes([g7] * half, times[half:], seconds)
    )
    strums, _, _ = _run_notes(
        tmp_path, _grid([8, 8]), _detector(times), other=single_notes_then_chords, mix_amp=0.1
    )
    assert not any(p.no_instrument for p in strums.patterns)
    riff, strum = strums.patterns
    assert riff.riff and not strum.riff
    assert riff.riff_entropy is not None and riff.riff_single_share is not None
    assert strum.riff_entropy is not None and strum.riff_entropy > riff.riff_entropy


def test_no_instrument_section_has_no_riff_features_and_no_p(tmp_path):
    other = np.concatenate([_tone(8 * BAR_SECONDS, 0.3), np.zeros(int(8 * BAR_SECONDS * SR))])
    strums, _, _ = _run_notes(tmp_path, _grid([8, 8]), _detector(_island(16)), other=other)
    silent = next(p for p in strums.patterns if p.no_instrument)
    assert (silent.riff, silent.riff_entropy, silent.chance_p) == (False, None, None)
    assert (silent.riff_single_share, silent.strike_density) == (None, None)


def test_inherited_section_has_no_riff_features_and_no_p(tmp_path):
    times = (
        [t for b in range(4) for t in _bar_times(b, ISLAND)]
        + [t for b in range(4, 6) for t in _bar_times(b, (0,))]
        + [t for b in range(6, 12) for t in _bar_times(b, range(8))]
    )
    strums, _, _ = _run_notes(tmp_path, _grid([4, 2, 6]), _detector(times))
    short = strums.patterns[1]
    assert short.inherited_from == 2
    assert (short.riff, short.riff_entropy, short.riff_single_share) == (False, None, None)
    assert (short.chance_p, short.strike_density) == (None, None)
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

