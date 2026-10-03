from __future__ import annotations

from pathlib import Path

from youkelele.cli import main
from youkelele.evaluate import Report, evaluate_run, format_report
from youkelele.jsonio import save_model
from youkelele.schemas import Bar, ChordEvent, Chords, Grid, Key, Meter, Section

EXAMPLE = Path(__file__).parent / "fixtures" / "ground_truth" / "example"
LABELS = ["C:maj", "G:maj", "A:min", "F:maj"]


def _grid() -> Grid:
    beats = [i * 0.5 for i in range(16)]
    bars = [
        Bar(index=i, start=i * 2.0, end=(i + 1) * 2.0, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(4)
    ]
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=beats,
        downbeats=[0, 4, 8, 12], bars=bars,
        sections=[Section(label="s0", start_bar=0, end_bar=4, confidence=0.5)],
        octave_decision="none", bar_loudness_db=[-20.0] * 4, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _chords() -> Chords:
    events = [
        ChordEvent(
            bar=i, beat=0, start=i * 2.0, end=(i + 1) * 2.0, label=label,
            triad=label, confidence=0.9,
        )
        for i, label in enumerate(LABELS)
    ]
    return Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=events)


def _run(path: Path) -> Path:
    (path / "02_grid").mkdir(parents=True)
    (path / "03_harmony").mkdir(parents=True)
    save_model(path / "02_grid" / "grid.json", _grid())
    save_model(path / "03_harmony" / "chords.json", _chords())
    return path


def test_evaluate_perfect_match_scores_100(tmp_path):
    report = evaluate_run(_run(tmp_path), EXAMPLE)
    assert report == Report(1.0, 1.0, 1.0, 1.0, 1.0)


def test_evaluate_missing_truth_file_gives_none(tmp_path):
    truth = tmp_path / "truth"
    truth.mkdir()
    (truth / "beats.txt").write_text((EXAMPLE / "beats.txt").read_text())
    report = evaluate_run(_run(tmp_path / "run"), truth)
    assert report.beat_f == 1.0 and report.downbeat_f == 1.0
    assert report.chord_root is None and report.chord_majmin is None
    assert report.chord_triads is None
    text = format_report(report)
    assert "Beat F-measure: 100.0%" in text
    assert "Chord root: n/a" in text


def test_cli_evaluate_prints_report(tmp_path, capsys):
    _run(tmp_path / "runs" / "demo")
    code = main(["evaluate", "demo", "--truth", str(EXAMPLE), "--runs-dir", str(tmp_path / "runs")])
    out = capsys.readouterr().out.splitlines()
    assert code == 0
    assert out == [
        "Beat F-measure: 100.0%",
        "Downbeat F-measure: 100.0%",
        "Chord root: 100.0%",
        "Chord major/minor: 100.0%",
        "Chord triads: 100.0%",
    ]


def test_cli_evaluate_missing_run_returns_1(tmp_path, capsys):
    code = main(["evaluate", "nope", "--truth", str(EXAMPLE), "--runs-dir", str(tmp_path)])
    assert code == 1
    assert len(capsys.readouterr().out.strip().splitlines()) == 1
