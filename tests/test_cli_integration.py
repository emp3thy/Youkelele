"""The CLI driven end to end: run, hand-edit the JSON, resume with --from.

The audio stages (ingest, separate, grid, harmony, strums) are replaced by stages that
write fixed artifacts; arrange, score and render are the real ukulele stages, with only
the Chromium PDF step faked. This is the seam between hand edits, saved options and the
downstream stages that the per-stage tests cannot see.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

from youkelele import commands
from youkelele.cli import main
from youkelele.jsonio import load_model, save_model
from youkelele.manifest import load_manifest
from youkelele.profiles.ukulele import ukulele_profile
from youkelele.schemas import (
    Arrangement,
    Bar,
    ChordEvent,
    Chords,
    Grid,
    Key,
    Meter,
    Score,
    Section,
    SectionPattern,
    SourceInfo,
    Strums,
)
from youkelele.stage import Stage, StageContext
from youkelele.stages.render import RenderStage
from youkelele.stages.separate import STEMS

BAR = 2.0


def _grid() -> Grid:
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4),
        beats=[i * 0.5 for i in range(16)], downbeats=[0, 4, 8, 12],
        bars=[
            Bar(index=i, start=i * BAR, end=(i + 1) * BAR, beats=list(range(4 * i, 4 * i + 4)))
            for i in range(4)
        ],
        sections=[
            Section(label="Verse", start_bar=0, end_bar=2, confidence=0.6),
            Section(label="Chorus", start_bar=2, end_bar=4, confidence=0.6),
        ],
        octave_decision="half", bar_loudness_db=[-20.0] * 4, sections_k=2,
        largest_cluster_share=0.5, chorus_margin_db=1.0, labels_low_confidence=False,
    )


def _chords() -> Chords:
    spans = [(0, 2, "C:maj"), (2, 3, "G:maj"), (3, 4, "A:min")]
    return Chords(
        key=Key(tonic="C", mode="major", confidence=0.9),
        events=[
            ChordEvent(
                bar=s, beat=0, start=s * BAR, end=e * BAR, label=label, triad=label, confidence=0.9
            )
            for s, e, label in spans
        ],
    )


def _strums() -> Strums:
    patterns = [
        SectionPattern(
            section=k, slots=list("D-DU-UDU"), confidence=0.8, bar_repeat=0.9, uncertain=False,
            no_instrument=False, inherited_from=None,
        )
        for k in range(2)
    ]
    return Strums(
        slots_per_bar=8, source="other_stem", source_ratio=0.4, grid_fit=0.9, uncertain=False,
        patterns=patterns, bar_onsets=[list("D-DU-UDU")] * 4,
    )


def _source() -> SourceInfo:
    return SourceInfo(
        url=None, path="song.wav", video_id=None, title="Song", artist="Band", duration=8.0,
        sample_rate=44100, channels=2, fetched_at=datetime(2026, 1, 1),
    )


class _FixedStage(Stage):
    """Writes fixed artifacts: models as JSON, anything else as placeholder bytes."""

    def __init__(self, name: str, requires: tuple[str, ...], outputs: dict[str, BaseModel | None]):
        self.name = name
        self.requires = requires
        self.produces = tuple(outputs)
        self.outputs = outputs
        self.seen_options = []

    def run(self, ctx: StageContext) -> None:
        self.seen_options.append(ctx.options)
        for key, model in self.outputs.items():
            path = ctx.output(key)
            if model is None:
                path.write_bytes(b"RIFF")
            else:
                save_model(path, model)


def _fake_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.write_bytes(b"%PDF-fake")


@pytest.fixture
def chain(monkeypatch):
    stems = {f"separate/stems/{s}.wav": None for s in STEMS}
    profile_stages = list(ukulele_profile().stages)
    assert [s.name for s in profile_stages] == ["strums", "arrange", "score"]
    stages = [
        _FixedStage("ingest", (), {"ingest/audio.wav": None, "ingest/source.json": _source()}),
        _FixedStage("separate", ("ingest/audio.wav",), stems),
        _FixedStage("grid", ("ingest/audio.wav",), {"grid/grid.json": _grid()}),
        _FixedStage("harmony", ("ingest/audio.wav", "grid/grid.json"), {"harmony/chords.json": _chords()}),
        _FixedStage("strums", profile_stages[0].requires, {"strums/strums.json": _strums()}),
        profile_stages[1],
        profile_stages[2],
        RenderStage(pdf_writer=_fake_pdf),
    ]
    monkeypatch.setattr(commands, "_chain", lambda instrument: stages)
    monkeypatch.setattr(commands, "check_environment", lambda *a, **k: [])
    return stages


def _bar_chord_names(score: Score) -> list[list[str]]:
    return [[c.name for c in bar.chords] for section in score.sections for bar in section.bars]


def test_hand_edits_flow_downstream_and_saved_options_survive_resume(tmp_path, chain, capsys):
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", "--tier", "full", "--beat-octave", "half", *runs]) == 0
    run_dir = tmp_path / "song"
    score_path = run_dir / "06_score" / "score.json"
    first = load_model(score_path, Score)
    assert [s.label for s in first.sections] == ["Verse", "Chorus"]
    assert _bar_chord_names(first) == [["C"], ["C"], ["G"], ["Am"]]

    grid_path = run_dir / "02_grid" / "grid.json"
    grid = load_model(grid_path, Grid)
    grid.sections[1].label = "Big Chorus"
    save_model(grid_path, grid)
    chords_path = run_dir / "03_harmony" / "chords.json"
    chords = load_model(chords_path, Chords)
    chords.events[2].label = chords.events[2].triad = "F:maj"
    save_model(chords_path, chords)

    capsys.readouterr()
    assert main(["run", "song.wav", "--from", "arrange", *runs]) == 0
    out = capsys.readouterr().out
    assert "will be overwritten" not in out
    assert "[00] ingest" not in out and "[05] arrange" in out

    score = load_model(score_path, Score)
    assert [s.label for s in score.sections] == ["Verse", "Big Chorus"]
    assert _bar_chord_names(score) == [["C"], ["C"], ["G"], ["F"]]
    assert [d.name for d in score.chord_diagrams] == ["C", "G", "F"]
    assert score.tier == "full"
    arrangement = load_model(run_dir / "05_arrange" / "arrangement.json", Arrangement)
    assert arrangement.tier == "full"
    html = (run_dir / "07_render" / "sheet.html").read_text(encoding="utf-8")
    assert "<h2>Big Chorus</h2>" in html and "<h2>Chorus</h2>" not in html
    assert '"F"' in (run_dir / "06_score" / "score.alphatex").read_text(encoding="utf-8")

    options = load_manifest(run_dir).options
    assert (options.tier, options.beat_octave) == ("full", "half")
    assert chain[0].seen_options[0].tier == "full"
    # harmony and strums read the edited grid.json and were not re-run, so they are stale
    stale = [name for name, state in commands.status(run_dir, chain) if state != "done"]
    assert stale == ["harmony", "strums"]


def test_splitting_a_section_and_resuming_past_strums_explains_the_fix(tmp_path, chain, capsys):
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", *runs]) == 0
    grid_path = tmp_path / "song" / "02_grid" / "grid.json"
    grid = load_model(grid_path, Grid)
    verse = grid.sections[0]
    grid.sections[0:1] = [
        verse.model_copy(update={"end_bar": 1}),
        verse.model_copy(update={"label": "Verse 2", "start_bar": 1}),
    ]
    save_model(grid_path, grid)

    capsys.readouterr()
    assert main(["run", "song.wav", "--from", "arrange", *runs]) == 1
    out = capsys.readouterr().out
    assert (
        "stage score (06) failed: strums.json has 2 patterns for 3 sections in grid.json; "
        "re-run from strums"
    ) in out
    assert f'resume with: youkelele run "song.wav" --from 6 --runs-dir "{tmp_path}"' in out


def test_non_harte_hand_edit_fails_with_the_field_path(tmp_path, chain, capsys):
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", *runs]) == 0
    chords_path = tmp_path / "song" / "03_harmony" / "chords.json"
    text = chords_path.read_text(encoding="utf-8").replace('"A:min"', '"Am"')
    chords_path.write_text(text, encoding="utf-8")

    capsys.readouterr()
    assert main(["run", "song.wav", "--from", "arrange", *runs]) == 1
    out = capsys.readouterr().out
    assert "stage arrange (05) failed" in out
    assert "events.2.label" in out and "expected Harte syntax such as A:min" in out
