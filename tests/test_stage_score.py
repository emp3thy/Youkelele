from __future__ import annotations

from datetime import datetime

from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.options import RunOptions
from youkelele.profiles.ukulele import UKULELE_TUNING
from youkelele.schemas import (
    ArrangedChord,
    Arrangement,
    Bar,
    ChordEvent,
    Chords,
    Grid,
    Key,
    Meter,
    Riffs,
    Score,
    Section,
    SectionPattern,
    Shape,
    SourceInfo,
    Strums,
)
from youkelele.stage import StageContext
from youkelele.stages.score import ScoreStage


def test_score_stage_writes_both_files_and_score_validates(tmp_path):
    layout = RunLayout(
        tmp_path / "run", ["ingest", "grid", "harmony", "strums", "riff", "arrange", "score"]
    )
    grid = Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4),
        beats=[i * 0.5 for i in range(8)], downbeats=[0, 4],
        bars=[Bar(index=i, start=2.0 * i, end=2.0 * (i + 1), beats=list(range(4 * i, 4 * i + 4)))
              for i in range(2)],
        sections=[Section(label="Verse", start_bar=0, end_bar=2, confidence=0.5)],
        octave_decision="none", bar_loudness_db=[-20.0, -20.0], sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )
    shape = Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[])
    chords = Chords(
        key=Key(tonic="C", mode="major", confidence=0.9),
        events=[ChordEvent(bar=0, beat=0, start=0.0, end=4.0, label="C", triad="C", confidence=0.9)],
    )
    strums = Strums(
        slots_per_bar=8, source="mix", source_ratio=0.0, grid_fit=0.9, uncertain=False,
        patterns=[SectionPattern(section=0, slots=list("D-DU-UDU"), confidence=0.8, bar_repeat=1.0,
                                 uncertain=False, no_instrument=False, inherited_from=None)],
        bar_onsets=[],
    )
    arrangement = Arrangement(
        capo=0, transpose=0, tier="easy",
        chords=[ArrangedChord(event=0, name="C", shape=shape)], substitutions=[],
    )
    source = SourceInfo(
        url=None, path="x.mp3", video_id=None, title="Song", artist=None, duration=4.0,
        sample_rate=44100, channels=2, fetched_at=datetime(2026, 1, 1),
    )
    for key, model in [
        ("ingest/source.json", source), ("grid/grid.json", grid), ("harmony/chords.json", chords),
        ("strums/strums.json", strums), ("arrange/arrangement.json", arrangement),
        ("riff/riff.json", Riffs()),
    ]:
        path = layout.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_model(path, model)

    out = tmp_path / "out"
    out.mkdir()
    stage = ScoreStage(UKULELE_TUNING, "Ukulele")
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    stage.run(ctx)

    score = load_model(out / "score.json", Score)
    assert score.instrument.name == "Ukulele"
    assert len(score.sections[0].bars) == 2
    assert score.schema_version == 2
    # a strums.json without bar records is backfilled: each bar prints its section's pattern
    assert [k.slot for k in score.sections[0].bars[0].strokes] == [0, 2, 3, 5, 6, 7]
    text = (out / "score.alphatex").read_text(encoding="utf-8")
    assert text.startswith('\\title "Song"')
    assert "\\tuning (A4 E4 C4 G4) { hide }" in text
