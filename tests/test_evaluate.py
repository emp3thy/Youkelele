from __future__ import annotations

from pathlib import Path

from youkelele.cli import main
from youkelele.evaluate import (
    Report,
    compare_runs,
    evaluate_run,
    format_comparison,
    format_report,
)
from youkelele.jsonio import save_model
from youkelele.schemas import (
    Bar,
    ChordEvent,
    Chords,
    Grid,
    Key,
    Meter,
    Section,
    SectionPattern,
    Strums,
)

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


def test_evaluate_imperfect_estimate_is_scored_per_metric(tmp_path):
    grid = _grid()
    beats = list(grid.beats)
    beats[1] += 0.2  # a non-downbeat well outside the 70 ms window
    grid = grid.model_copy(update={"beats": beats})
    chords = _chords()
    events = list(chords.events)
    events[3] = events[3].model_copy(update={"label": "D:maj", "triad": "D:maj"})
    chords = chords.model_copy(update={"events": events})
    run = tmp_path / "run"
    (run / "02_grid").mkdir(parents=True)
    (run / "03_harmony").mkdir(parents=True)
    save_model(run / "02_grid" / "grid.json", grid)
    save_model(run / "03_harmony" / "chords.json", chords)
    report = evaluate_run(run, EXAMPLE)
    assert report.beat_f is not None and report.beat_f < 1.0
    assert report.downbeat_f == 1.0
    for score in (report.chord_root, report.chord_majmin, report.chord_triads):
        assert score is not None and abs(score - 0.75) < 1e-6


def _truth_cli(tmp_path, capsys, beats=None, lab=None):
    _run(tmp_path / "runs" / "demo")
    truth = tmp_path / "truth"
    truth.mkdir()
    if beats is not None:
        (truth / "beats.txt").write_text(beats)
    if lab is not None:
        (truth / "chords.lab").write_text(lab)
    code = main(["evaluate", "demo", "--truth", str(truth), "--runs-dir", str(tmp_path / "runs")])
    return code, capsys.readouterr().out.splitlines()


def test_cli_evaluate_malformed_beats_prints_one_line(tmp_path, capsys):
    code, out = _truth_cli(tmp_path, capsys, beats="0.0\t1\nabc\n")
    assert code == 1
    assert len(out) == 1
    assert "beats.txt:2" in out[0] and "'abc'" in out[0]


def test_cli_evaluate_short_lab_line_prints_one_line(tmp_path, capsys):
    code, out = _truth_cli(tmp_path, capsys, lab="0.0\t2.0\n")
    assert code == 1
    assert len(out) == 1 and "chords.lab:1" in out[0]


def test_cli_evaluate_accepts_space_separated_lab(tmp_path, capsys):
    lab = "0.0 2.0 C:maj\n2.0 4.0 G:maj\n4.0 6.0 A:min\n6.0 8.0 F:maj\n"
    code, out = _truth_cli(tmp_path, capsys, lab=lab)
    assert code == 0
    assert "Chord root: 100.0%" in out
    assert "Beat F-measure: n/a" in out


def _sectioned_grid() -> Grid:
    return _grid().model_copy(
        update={
            "sections": [
                Section(label="verse", start_bar=0, end_bar=2, confidence=0.5),
                Section(label="chorus", start_bar=2, end_bar=4, confidence=0.5),
            ]
        }
    )


def _pattern(section, slots, uncertain=False, no_instrument=False) -> SectionPattern:
    return SectionPattern(
        section=section, slots=slots, confidence=0.8, bar_repeat=0.8, uncertain=uncertain,
        no_instrument=no_instrument, inherited_from=None,
    )


def _strums(bar_onsets, patterns, slots_per_bar=4) -> Strums:
    return Strums(
        slots_per_bar=slots_per_bar, source="mix", source_ratio=1.0, grid_fit=0.9,
        uncertain=False, patterns=patterns, bar_onsets=bar_onsets,
    )


def _run_with(path: Path, grid=None, chords=None, strums=None) -> Path:
    (path / "02_grid").mkdir(parents=True)
    (path / "03_harmony").mkdir(parents=True)
    save_model(path / "02_grid" / "grid.json", grid or _grid())
    save_model(path / "03_harmony" / "chords.json", chords or _chords())
    if strums is not None:
        (path / "04_strums").mkdir()
        save_model(path / "04_strums" / "strums.json", strums)
    return path


def _event(bar, beat, start, end, label, filled=False) -> ChordEvent:
    return ChordEvent(
        bar=bar, beat=beat, start=start, end=end, label=label, triad=label,
        confidence=0.9, filled=filled,
    )


def test_evaluate_without_truth_reports_chord_diagnostics(tmp_path):
    events = [
        _event(0, 0, 0.0, 2.02, "C:maj"),
        _event(1, 0, 2.02, 3.0, "G:maj"),  # a change 20 ms off the bar start
        _event(1, 2, 3.0, 4.0, "A:min"),  # a change mid-bar
        _event(2, 0, 4.0, 6.0, "N", filled=True),
        _event(3, 0, 6.0, 8.0, "N"),
    ]
    chords = Chords(key=Key(tonic="C", mode="major", confidence=0.7), events=events)
    report = evaluate_run(_run_with(tmp_path / "run", chords=chords))
    assert abs(report.n_share - 0.5) < 1e-9  # 4 s of 8 s
    assert report.all_n_bars == 2
    assert report.filled_bars == 1
    # changes: C->G (on bar), G->A (mid-bar), A->N (4.0, on bar); N->N is not a change
    assert abs(report.changes_on_bar_share - 2 / 3) < 1e-9
    assert report.sub_beat_events == 0  # median beat interval 0.5 s; shortest event is ~1 s
    assert report.key_confidence == 0.7
    assert report.beat_f is None and report.chord_root is None


def test_evaluate_sub_beat_events_counts_events_shorter_than_a_beat(tmp_path):
    events = [_event(0, 0, 0.0, 0.25, "C:maj"), _event(0, 0, 0.25, 2.0, "G:maj")]
    chords = Chords(key=Key(tonic="C", mode="major", confidence=0.7), events=events)
    report = evaluate_run(_run_with(tmp_path / "run", chords=chords))
    assert report.sub_beat_events == 1


def test_evaluate_without_truth_reports_strum_diagnostics(tmp_path):
    bar_onsets = [
        ["D", "-", "U", "-"],
        ["D", "-", "U", "U"],  # the last strike is off the pattern
        ["D", "-", "-", "-"],
        ["-", "-", "-", "-"],
    ]
    patterns = [
        _pattern(0, ["D", "-", "U", "-"]),
        _pattern(1, ["D", "-", "-", "-"]),  # 0.75 rests, certain: a mostly-rest box
    ]
    run = _run_with(tmp_path / "run", grid=_sectioned_grid(),
                    strums=_strums(bar_onsets, patterns))
    report = evaluate_run(run)
    assert len(report.sections) == 2
    verse, chorus = report.sections
    assert (verse.index, verse.label) == (0, "verse")
    assert verse.strikes_per_bar == 2.5
    assert abs(verse.explained - 4 / 5) < 1e-9
    assert verse.rest_share == 0.5
    assert verse.uncertain is False and verse.recall_boost is False
    assert chorus.strikes_per_bar == 0.5
    assert chorus.explained == 1.0
    assert chorus.rest_share == 0.75
    assert report.boxes_mostly_rests == 1


def test_evaluate_boxes_mostly_rests_ignores_uncertain_and_no_instrument(tmp_path):
    bar_onsets = [["-", "-", "-", "-"]] * 4
    patterns = [
        _pattern(0, ["D", "-", "-", "-"], uncertain=True),
        _pattern(1, ["-", "-", "-", "-"], no_instrument=True),
    ]
    run = _run_with(tmp_path / "run", grid=_sectioned_grid(),
                    strums=_strums(bar_onsets, patterns))
    assert evaluate_run(run).boxes_mostly_rests == 0


def test_evaluate_without_strums_json_reports_na(tmp_path):
    report = evaluate_run(_run_with(tmp_path / "run"))
    assert report.sections == []
    assert report.boxes_mostly_rests is None
    text = format_report(report)
    assert "Boxes mostly rests: n/a" in text
    assert "Changes on bar: 100.0%" in text


def test_format_report_prints_na_for_missing():
    text = format_report(Report(None, None, None, None, None))
    assert "Changes on bar: n/a" in text
    assert "N share: n/a" in text
    assert "Key confidence: n/a" in text
    assert "Beat F-measure" not in text


def test_format_report_prints_section_lines(tmp_path):
    bar_onsets = [["D", "-", "U", "-"]] * 4
    patterns = [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])]
    run = _run_with(tmp_path / "run", grid=_sectioned_grid(),
                    strums=_strums(bar_onsets, patterns))
    text = format_report(evaluate_run(run))
    assert "verse" in text and "chorus" in text
    assert "strikes/bar 2.0" in text


def test_compare_identical_runs_is_identity(tmp_path):
    bar_onsets = [["D", "-", "U", "-"]] * 4
    patterns = [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])]
    strums = _strums(bar_onsets, patterns)
    a = _run_with(tmp_path / "a", grid=_sectioned_grid(), strums=strums)
    b = _run_with(tmp_path / "b", grid=_sectioned_grid(), strums=strums)
    comparison = compare_runs(a, b)
    assert comparison.seg == 1.0 and comparison.majmin == 1.0
    assert comparison.overseg == 1.0 and comparison.underseg == 1.0
    assert len(comparison.sections) == 2
    for left, right in comparison.sections:
        assert left == right
    assert comparison.notes == []
    assert "seg" in format_comparison(comparison)


def test_compare_mismatched_slots_notes_and_continues(tmp_path):
    a = _run_with(
        tmp_path / "a", grid=_sectioned_grid(),
        strums=_strums([["D", "-", "U", "-"]] * 4,
                       [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])]),
    )
    eight = ["D", "-", "U", "-", "D", "-", "U", "-"]
    b = _run_with(
        tmp_path / "b", grid=_sectioned_grid(),
        strums=_strums([eight] * 4, [_pattern(0, eight), _pattern(1, eight)], slots_per_bar=8),
    )
    comparison = compare_runs(a, b)
    assert comparison.seg == 1.0
    assert any("slots per bar" in note for note in comparison.notes)
    assert len(comparison.sections) == 2


def test_compare_without_strums_still_scores_chords(tmp_path):
    a = _run_with(tmp_path / "a")
    b = _run_with(tmp_path / "b", strums=_strums([["-"] * 4] * 4, [_pattern(0, ["-"] * 4)]))
    comparison = compare_runs(a, b)
    assert comparison.majmin == 1.0
    assert len(comparison.sections) == 1
    assert comparison.sections[0][0] is None and comparison.sections[0][1] is not None
    assert any("strums" in note for note in comparison.notes)


def test_cli_evaluate_without_truth_prints_diagnostics(tmp_path, capsys):
    _run_with(tmp_path / "runs" / "demo")
    code = main(["evaluate", "demo", "--runs-dir", str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert code == 0
    assert "Changes on bar" in out and "Beat F-measure" not in out


def test_cli_evaluate_compare_appends_comparison(tmp_path, capsys):
    _run_with(tmp_path / "runs" / "a")
    _run_with(tmp_path / "runs" / "b")
    code = main(["evaluate", "a", "--compare", "b", "--runs-dir", str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert code == 0
    assert "Changes on bar" in out
    assert "Compared with b" in out and "majmin 1.000" in out


def test_cli_evaluate_compare_missing_run_returns_1(tmp_path, capsys):
    _run_with(tmp_path / "runs" / "a")
    code = main(["evaluate", "a", "--compare", "nope", "--runs-dir", str(tmp_path / "runs")])
    assert code == 1
    assert len(capsys.readouterr().out.strip().splitlines()) == 1
