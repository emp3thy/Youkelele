from __future__ import annotations

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.options import RunOptions
from youkelele.schemas import Arrangement, ChordEvent, Chords, Key
from youkelele.stage import StageContext
from youkelele.stages.arrange import ArrangeStage


def _event(i: int, label: str) -> ChordEvent:
    return ChordEvent(
        bar=i, beat=0, start=float(i), end=float(i + 1), label=label, triad=label, confidence=0.9
    )


def _run(tmp_path, labels, tier="easy"):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony", "arrange"])
    chords_path = layout.path("harmony/chords.json")
    chords_path.parent.mkdir(parents=True)
    save_model(
        chords_path,
        Chords(
            key=Key(tonic="C", mode="major", confidence=0.9),
            events=[_event(i, lab) for i, lab in enumerate(labels)],
        ),
    )
    grid_path = layout.path("grid/grid.json")
    grid_path.parent.mkdir(parents=True)
    grid_path.write_text("{}", encoding="utf-8")  # declared input; this stage does not read it
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
