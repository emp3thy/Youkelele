from __future__ import annotations

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.options import RunOptions
from youkelele.schemas import Arrangement, Bar, ChordEvent, Chords, Grid, Key, Meter, Section
from youkelele.stage import StageContext
from youkelele.stages.arrange import ArrangeStage


def _event(i: int, label: str) -> ChordEvent:
    return ChordEvent(
        bar=i, beat=0, start=float(i), end=float(i + 1), label=label, triad=label, confidence=0.9
    )


def _grid(bar_seconds: float = 2.0, n_bars: int = 8, pickup: bool = False) -> Grid:
    bars = [
        Bar(index=i, start=i * bar_seconds, end=(i + 1) * bar_seconds, beats=[])
        for i in range(n_bars)
    ]
    if pickup:  # a short first bar: only the full bars should set the bar length
        bars[0] = bars[0].model_copy(update={"end": bars[0].start + 0.5, "pickup": True})
    beats = [i * bar_seconds / 4 for i in range(n_bars * 4 + 1)]
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=beats, downbeats=[0],
        bars=bars, sections=[Section(label="A", start_bar=0, end_bar=n_bars, confidence=1.0)],
        octave_decision="none", bar_loudness_db=[0.0] * n_bars, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _events(labels, durations):
    if durations is None:
        return [_event(i, lab) for i, lab in enumerate(labels)]
    events, t = [], 0.0
    for i, (lab, seconds) in enumerate(zip(labels, durations)):
        events.append(
            ChordEvent(bar=i, beat=0, start=t, end=t + seconds, label=lab, triad=lab, confidence=0.9)
        )
        t += seconds
    return events


def _run(tmp_path, labels, tier="easy", durations=None, grid=None):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony", "arrange"])
    chords_path = layout.path("harmony/chords.json")
    chords_path.parent.mkdir(parents=True)
    save_model(
        chords_path,
        Chords(
            key=Key(tonic="C", mode="major", confidence=0.9),
            events=_events(labels, durations),
        ),
    )
    grid_path = layout.path("grid/grid.json")
    grid_path.parent.mkdir(parents=True)
    save_model(grid_path, grid or _grid())
    out = tmp_path / "out"
    out.mkdir()
    stage = ArrangeStage()
    ctx = StageContext(layout, RunOptions(source="x.mp3", tier=tier), out, lambda m: None, stage)
    stage.run(ctx)
    return ctx, load_model(ctx.output("arrange/arrangement.json"), Arrangement)


def test_arrange_stage_writes_shapes_and_substitutions(tmp_path):
    ctx, arr = _run(tmp_path, ["C:maj", "G:7", "A:min", "F:maj"], tier="easy")
    assert arr.capo == 0 and arr.transpose == 0 and arr.tier == "easy"
    assert [c.name for c in arr.chords] == ["C", "G", "Am", "F"]
    assert [c.event for c in arr.chords] == [0, 1, 2, 3]
    assert len(arr.substitutions) == 1
    sub = arr.substitutions[0]
    assert (sub.event, sub.original, sub.chosen) == (1, "G:7", "G:maj")
    assert sub.reason == "easy tier: reduced to triad"
    assert arr.no_capo_alternative == []
    assert ctx.notes["capo"] == "0" and ctx.notes["tier"] == "easy"


def test_arrange_stage_keeps_flat_spelling_at_capo_0(tmp_path):
    _, arr = _run(tmp_path, ["C:maj", "F:maj", "G:maj", "A:min"] * 3 + ["Bb:maj", "Eb:7"], tier="full")
    assert arr.capo == 0
    assert [c.name for c in arr.chords][-2:] == ["Bb", "Eb7"]


def test_arrange_stage_full_tier_keeps_seventh(tmp_path):
    _, arr = _run(tmp_path, ["G:7", "C:maj"], tier="full")
    assert [c.name for c in arr.chords] == ["G7", "C"]
    assert arr.substitutions == []


def test_arrange_stage_capo_fills_no_capo_alternative(tmp_path):
    ctx, arr = _run(tmp_path, ["D#:maj", "A#:maj", "C:min", "G#:maj"] * 2)
    assert arr.capo == 3 and arr.transpose == -3
    assert [c.name for c in arr.chords[:4]] == ["C", "G", "Am", "F"]
    assert len(arr.no_capo_alternative) == len(arr.chords)
    assert arr.no_capo_alternative[0].name == "D#"
    assert arr.no_capo_alternative[0].shape.frets != arr.chords[0].shape.frets
    assert ctx.notes["capo"] == "3"


def test_arrange_stage_never_crashes_on_inversion_or_unknown(tmp_path):
    _, arr = _run(tmp_path, ["N", "A:min/b3", "E:maj(9)", "C##:maj", "X", "C:maj"], tier="full")
    assert [c.event for c in arr.chords] == [1, 2, 5]
    assert [c.name for c in arr.chords] == ["Am", "E", "C"]
    reasons = {s.event: s.reason for s in arr.substitutions}
    assert reasons[2] == "no shape in chords-db for maj(9)"
    assert reasons[3] == "no shape; left blank"


def test_arrange_stage_flags_passing_chords(tmp_path):
    _, arr = _run(
        tmp_path, ["C:maj", "G:maj", "A:min", "F:maj"], tier="full", durations=[60.0, 60.0, 40.0, 0.9]
    )
    assert [c.name for c in arr.chords] == ["C", "G", "Am", "F"]
    assert [c.passing for c in arr.chords] == [False, False, False, True]


def test_arrange_stage_passing_follows_the_capo_transposition(tmp_path):
    _, arr = _run(
        tmp_path, ["D#:maj", "A#:maj", "C:min", "G#:maj"], durations=[60.0, 60.0, 40.0, 0.9]
    )
    assert arr.capo == 3
    assert [c.passing for c in arr.chords] == [False, False, False, True]
    assert [c.passing for c in arr.no_capo_alternative] == [False, False, False, True]


def test_arrange_stage_passing_judged_after_tier_simplification(tmp_path):
    # G:7 is rare on its own, but easy tier plays it as G, which is common: it keeps its diagram
    _, arr = _run(
        tmp_path, ["C:maj", "G:maj", "A:min", "G:7"], tier="easy", durations=[60.0, 60.0, 40.0, 0.9]
    )
    assert [c.passing for c in arr.chords] == [False, False, False, False]


def test_arrange_stage_passing_uses_full_bar_median_not_pickup(tmp_path):
    # one 0.5 s pickup and one 2 s bar: bar length is 2 s, so a 1.6 s chord is within a bar and
    # passing; counting the pickup would give a 1.25 s median and wrongly keep its diagram
    grid = _grid(bar_seconds=2.0, n_bars=2, pickup=True)
    _, arr = _run(
        tmp_path, ["C:maj", "G:maj", "A:min", "F:maj"], tier="full",
        durations=[60.0, 60.0, 40.0, 1.6], grid=grid,
    )
    assert [c.passing for c in arr.chords] == [False, False, False, True]
