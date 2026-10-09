from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from youkelele.cli import main
from youkelele.evaluate import (
    Report,
    SectionDiag,
    _key_line,
    _ranges,
    _section_diags,
    _section_line,
    compare_runs,
    evaluate_run,
    format_comparison,
    format_report,
)
from youkelele.jsonio import save_model
from youkelele.schemas import (
    Bar,
    BarStrums,
    ChordEvent,
    Chords,
    Grid,
    Key,
    Meter,
    PlannedSection,
    Riffs,
    RiffSection,
    Section,
    SectionPattern,
    SourceInfo,
    Strums,
    TonicVotes,
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
    truth = (
        report.beat_f, report.downbeat_f, report.chord_root, report.chord_majmin,
        report.chord_triads,
    )
    assert truth == (1.0, 1.0, 1.0, 1.0, 1.0)
    assert report.changes_on_bar_share == 1.0  # diagnostics accompany the truth scores


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
    assert out[:9] == [
        "N share: 0.0%",
        "All-N bars: 0",
        "Filled bars: 0",
        "Changes on bar: 100.0%",
        "Sub-beat events: 0",
        "Key: C major (mix_krumhansl, score margin n/a, mode margin n/a, runner-up n/a)",
        "Key confidence: 0.90",
        "Boxes mostly rests: n/a",
        "Vocal runs: n/a",
    ]
    assert out[9:] == [
        "Beat F-measure: 100.0%",
        "Downbeat F-measure: 100.0%",
        "Chord root: 100.0%",
        "Chord major/minor: 100.0%",
        "Chord triads: 100.0%",
        "Patterns: n/a",  # the run has no strums.json to score
        "Riffs: n/a",
        "Rests: n/a",
        "Key vs truth: 100.0% (same), hedge none",
        "Credits: n/a",  # nor a source.json
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


def _pattern(section, slots, uncertain=False, no_instrument=False, **fields) -> SectionPattern:
    return SectionPattern(
        section=section, slots=slots, confidence=0.8, bar_repeat=0.8, uncertain=uncertain,
        no_instrument=no_instrument, inherited_from=None, **fields,
    )


def _strums(bar_onsets, patterns, slots_per_bar=4, plan=()) -> Strums:
    return Strums(
        slots_per_bar=slots_per_bar, source="mix", source_ratio=1.0, grid_fit=0.9,
        uncertain=False, patterns=patterns, bar_onsets=bar_onsets, plan=list(plan),
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


def test_evaluate_leaves_trailing_no_chord_bars_out_of_the_last_section(tmp_path):
    # bar 3 starts after the last chord ends: the strums stage ignores it, and so does the harness
    events = [
        _event(0, 0, 0.0, 2.0, "C:maj"),
        _event(1, 0, 2.0, 4.0, "G:maj"),
        _event(2, 0, 4.0, 6.0, "A:min"),
        _event(3, 0, 6.0, 8.0, "N"),
    ]
    chords = Chords(key=Key(tonic="C", mode="major", confidence=0.7), events=events)
    bar_onsets = [["D", "-", "U", "-"]] * 2 + [["D", "-", "-", "-"], ["D", "D", "D", "D"]]
    patterns = [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "-", "-"])]
    run = _run_with(tmp_path / "run", grid=_sectioned_grid(), chords=chords,
                    strums=_strums(bar_onsets, patterns))
    verse, chorus = evaluate_run(run).sections
    assert verse.strikes_per_bar == 2.0 and verse.explained == 1.0
    assert chorus.strikes_per_bar == 1.0  # bar 2 only; with bar 3 it would be 2.5
    assert chorus.explained == 1.0  # with bar 3 it would be 2 of 5


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


def test_evaluate_prints_key_method_and_margins(tmp_path):
    key = Key(
        tonic="D", mode="major", confidence=0.302, method="chords_stems", margin=0.052,
        mode_margin=0.302, runner_up="A", mix=Key(tonic="A", mode="major", confidence=0.05),
    )
    chords = _chords().model_copy(update={"key": key})
    text = format_report(evaluate_run(_run_with(tmp_path / "new", chords=chords)))
    assert "Key: D major (chords_stems, score margin 0.052, mode margin 0.302, runner-up A, mix A major)" in text
    old = format_report(evaluate_run(_run_with(tmp_path / "old")))
    assert "Key: C major (mix_krumhansl, score margin n/a, mode margin n/a, runner-up n/a)" in old
    # under the pair rule (a close score) the margin is the pair rule's
    paired = key.model_copy(
        update={"tonic_votes": TonicVotes(score="A", pair="D", mix="A", decided_by="pair rule")}
    )
    assert _key_line(paired).startswith("Key: D major (chords_stems, pair margin 0.052, ")
    assert "Key: n/a" in format_report(Report(None, None, None, None, None))


def test_format_report_prints_section_lines(tmp_path):
    bar_onsets = [["D", "-", "U", "-"]] * 4
    patterns = [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])]
    run = _run_with(tmp_path / "run", grid=_sectioned_grid(),
                    strums=_strums(bar_onsets, patterns))
    text = format_report(evaluate_run(run))
    assert "  0 Verse bars 0-2: D-U-, conf 0.80, strikes/bar 2.0" in text
    assert "  1 Chorus bars 2-4: D-U-, conf 0.80, strikes/bar 2.0" in text


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


def test_compare_reports_section_deltas_and_flags(tmp_path):
    a = _run_with(
        tmp_path / "a", grid=_sectioned_grid(),
        strums=_strums(
            [["D", "-", "U", "-"]] * 2 + [["D", "-", "-", "-"]] * 2,
            [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "-", "-"])],
        ),
    )
    b = _run_with(
        tmp_path / "b", grid=_sectioned_grid(),
        strums=_strums(
            [["D", "-", "U", "U"]] * 2 + [["D", "D", "U", "-"]] * 2,
            [_pattern(0, ["D", "-", "U", "-"]),
             _pattern(1, ["D", "D", "U", "-"], uncertain=True)],
        ),
    )
    comparison = compare_runs(a, b)
    verse, chorus = comparison.deltas
    assert verse.strikes_per_bar == 1.0
    assert abs(verse.explained - (4 / 6 - 1.0)) < 1e-9
    assert verse.rest_share == 0.0
    assert chorus.strikes_per_bar == 2.0
    assert chorus.explained == 0.0
    assert chorus.rest_share == -0.5
    text = format_comparison(comparison)
    assert "+1.0/-33.3pp/+0.0pp" in text
    assert "+2.0/+0.0pp/-50.0pp" in text
    legend, verse_line, chorus_line = text.splitlines()[1:4]
    assert legend == (
        "  sections: strikes per bar/explained/rests; unc = uncertain, boost = recall boost, "
        "p = the structure test's chance p, riff = a riff section"
    )
    assert text.count("strikes per bar/explained/rests") == 1  # the legend is printed once
    assert "25.0% unc" in chorus_line and "% unc" not in verse_line


def test_compare_delta_is_none_when_a_side_is_missing(tmp_path):
    a = _run_with(tmp_path / "a")
    b = _run_with(tmp_path / "b", strums=_strums([["-"] * 4] * 4, [_pattern(0, ["-"] * 4)]))
    comparison = compare_runs(a, b)
    assert comparison.deltas == [None]
    assert "B-A n/a" in format_comparison(comparison)


def test_compare_pins_run_a_as_reference(tmp_path):
    one = Chords(
        key=Key(tonic="C", mode="major", confidence=0.9),
        events=[_event(0, 0, 0.0, 8.0, "C:maj")],
    )
    coarse = _run_with(tmp_path / "coarse", chords=one)
    fine = _run_with(tmp_path / "fine")  # four two-second chords
    coarse_as_ref = compare_runs(coarse, fine)
    fine_as_ref = compare_runs(fine, coarse)
    assert coarse_as_ref.overseg < 1.0 and coarse_as_ref.underseg == 1.0
    assert fine_as_ref.underseg < 1.0 and fine_as_ref.overseg == 1.0
    assert coarse_as_ref.majmin == 0.25 and fine_as_ref.majmin == 0.25


def test_evaluate_with_empty_truth_dir_prints_na_truth_lines(tmp_path):
    truth = tmp_path / "truth"
    truth.mkdir()
    report = evaluate_run(_run_with(tmp_path / "run"), truth)
    lines = format_report(report).splitlines()
    assert "Changes on bar: 100.0%" in lines
    assert lines[-10:] == [
        "Beat F-measure: n/a",
        "Downbeat F-measure: n/a",
        "Chord root: n/a",
        "Chord major/minor: n/a",
        "Chord triads: n/a",
        "Patterns: n/a",
        "Riffs: n/a",
        "Rests: n/a",
        "Key vs truth: n/a",
        "Credits: n/a",
    ]


def test_evaluate_prints_vocal_runs_and_labels(tmp_path):
    # 12 bars: no vocals in bars 0-4, vocals from bar 5 on
    beats = [i * 0.5 for i in range(48)]
    bars = [
        Bar(index=i, start=i * 2.0, end=(i + 1) * 2.0, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(12)
    ]
    grid = Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=beats,
        downbeats=list(range(0, 48, 4)), bars=bars,
        sections=[
            Section(label="intro", start_bar=0, end_bar=5, confidence=0.5),
            Section(label="verse", start_bar=5, end_bar=12, confidence=0.5),
        ],
        octave_decision="none", bar_loudness_db=[-20.0] * 12, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
        bar_vocal_db=[-120.0] * 5 + [-20.0] * 7,
    )
    bar_onsets = [["D", "-", "U", "-"]] * 12
    patterns = [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])]
    text = format_report(evaluate_run(_run_with(tmp_path / "run", grid=grid,
                                                strums=_strums(bar_onsets, patterns))))
    assert "Vocal runs: (0, 5)" in text
    assert "  0 Intro bars 0-5: D-U-, conf 0.80, strikes/bar 2.0" in text
    assert "  1 Verse bars 5-12: D-U-, conf 0.80, strikes/bar 2.0" in text
    # a 1.3 grid has no vocal levels
    assert "Vocal runs: n/a" in format_report(evaluate_run(_run_with(tmp_path / "old")))
    sung = grid.model_copy(update={"bar_vocal_db": [-20.0] * 12})
    assert "Vocal runs: none" in format_report(evaluate_run(_run_with(tmp_path / "all", grid=sung)))
    # a trailing run is listed and marked, not silently left out
    faded = grid.model_copy(update={"bar_vocal_db": [-120.0] * 5 + [-20.0] * 3 + [-120.0] * 4})
    text = format_report(evaluate_run(_run_with(tmp_path / "fade", grid=faded)))
    assert "Vocal runs: (0, 5), (8, 12) trailing" in text.splitlines()


def _power_chords() -> Chords:
    # the C:maj tonic relabelled as a power chord: label C:5, the key's quality as its triad
    events = list(_chords().events)
    events[0] = events[0].model_copy(update={"label": "C:5", "triad": "C:min", "power": True})
    return Chords(key=Key(tonic="C", mode="minor", confidence=0.9), events=events)


def test_power_events_are_scored_by_their_triad(tmp_path):
    truth = tmp_path / "truth"
    truth.mkdir()
    (truth / "chords.lab").write_text("0.0 2.0 C:min\n2.0 4.0 G:maj\n4.0 6.0 A:min\n6.0 8.0 F:maj\n")
    report = evaluate_run(_run_with(tmp_path / "run", chords=_power_chords()), truth)
    assert (report.chord_root, report.chord_majmin, report.chord_triads) == (1.0, 1.0, 1.0)


def test_compare_scores_power_events_by_their_triad(tmp_path):
    plain = list(_chords().events)
    plain[0] = plain[0].model_copy(update={"label": "C:min", "triad": "C:min"})
    power = _run_with(tmp_path / "a", chords=_power_chords())
    minor = _run_with(tmp_path / "b", chords=_chords().model_copy(update={"events": plain}))
    assert compare_runs(power, minor).majmin == 1.0  # a power run as the reference
    assert compare_runs(minor, power).majmin == 1.0


def test_section_lines_print_the_planned_sections_display_name(tmp_path):
    # the middle verse plays chords no other section plays: the sheet calls it the bridge
    bars = [
        Bar(index=i, start=i * 2.0, end=(i + 1) * 2.0, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(6)
    ]
    grid = _grid().model_copy(
        update={
            "beats": [i * 0.5 for i in range(24)], "downbeats": list(range(0, 24, 4)),
            "bars": bars, "bar_loudness_db": [-20.0] * 6,
            "sections": [
                Section(label="verse", start_bar=0, end_bar=2, confidence=0.5),
                Section(label="verse", start_bar=2, end_bar=4, confidence=0.5),
                Section(label="chorus", start_bar=4, end_bar=6, confidence=0.5),
            ],
        }
    )
    labels = ["C:maj", "G:maj", "D:min", "E:min", "C:maj", "G:maj"]
    chords = Chords(
        key=Key(tonic="C", mode="major", confidence=0.9),
        events=[_event(i, 0, i * 2.0, (i + 1) * 2.0, label) for i, label in enumerate(labels)],
    )
    patterns = [_pattern(i, ["D", "-", "U", "-"]) for i in range(3)]
    run = _run_with(tmp_path / "run", grid=grid, chords=chords,
                    strums=_strums([["D", "-", "U", "-"]] * 6, patterns))
    lines = format_report(evaluate_run(run)).splitlines()
    assert any(line.startswith("  0 Verse bars 0-2:") for line in lines)
    assert any(line.startswith("  1 Bridge bars 2-4:") for line in lines)
    assert any(line.startswith("  2 Chorus bars 4-6:") for line in lines)
    text = format_comparison(compare_runs(run, run))
    assert "  1 Bridge: A " in text


def test_section_line_prints_members_p_density_and_riff():
    d = SectionDiag(
        index=2, label="verse", strikes_per_bar=3.1, explained=1.0, rest_share=0.25,
        uncertain=False, recall_boost=False, start_bar=55, end_bar=110, members=[4, 5, 6],
        member_labels=["verse"] * 3, chance_p=0.003, strike_density=0.58, riff=True,
        riff_entropy=0.66, riff_single_share=0.58, riff_onsets=8, name="Verse 2",
        pattern=list("D-DU-UDU"), confidence=0.55,
    )
    assert _section_line(d) == (
        "  2 Verse 2 (grid 4, 5, 6: verse, verse, verse) bars 55-110: D-DU-UDU, conf 0.55, strikes/bar 3.1, "
        "explained 100.0%, rests 25.0%, p 0.003, density 0.58, riff 0.66/0.58 (8 onsets) riff, pcs n/a, root n/a, named n/a, rings n/a"
    )
    one = SectionDiag(**{**d.__dict__, "riff_onsets": 1, "riff": False})
    assert "riff 0.66/0.58 (1 onset), pcs" in _section_line(one)
    # a 1.5 file written before the count was stored prints the pair alone
    assert "riff 0.66/0.58 riff, pcs" in _section_line(SectionDiag(**{**d.__dict__, "riff_onsets": None}))


def test_section_line_prints_na_for_a_1_4_section_and_no_group_for_one_member():
    d = SectionDiag(
        index=0, label="verse", strikes_per_bar=2.0, explained=1.0, rest_share=0.5,
        uncertain=True, recall_boost=False, start_bar=0, end_bar=2, members=[0],
        member_labels=["verse"], name="Verse", pattern=list("D-U-"), confidence=0.4,
    )
    assert _section_line(d) == (
        "  0 Verse bars 0-2: D-U-, conf 0.40, strikes/bar 2.0, explained 100.0%, rests 50.0%, "
        "p n/a, density n/a, riff n/a uncertain, pcs n/a, root n/a, named n/a, rings n/a"
    )


def _plan_run(tmp_path, riff=False, uncertain=False):
    """A two-grid-section run whose plan merges both into one verse (members 0 and 1)."""
    plan = [PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0, 1])]
    patterns = [
        _pattern(0, ["D", "-", "U", "-"], uncertain=uncertain, chance_p=0.02, strike_density=0.5,
                 riff=riff, riff_entropy=0.4, riff_single_share=0.7, riff_onsets=12)
    ]
    strums = _strums([["D", "-", "U", "-"]] * 4, patterns, plan=plan)
    return _run_with(tmp_path, grid=_sectioned_grid(), strums=strums)


def test_section_diags_follow_the_plan_and_a_1_4_file_has_one_per_grid_section(tmp_path):
    grid, chords = _sectioned_grid(), _chords()
    plan = [PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0, 1])]
    with_plan = _strums([["D", "-", "U", "-"]] * 4, [_pattern(0, ["D", "-", "U", "-"])], plan=plan)
    diags = _section_diags(grid, with_plan, chords)
    assert [d.members for d in diags] == [[0, 1]]
    assert diags[0].member_labels == ["verse", "chorus"]
    assert (diags[0].label, diags[0].start_bar, diags[0].end_bar) == ("verse", 0, 4)
    old = _strums(
        [["D", "-", "U", "-"]] * 4,
        [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])],
    )
    assert [d.members for d in _section_diags(grid, old, chords)] == [[0], [1]]
    assert all(d.chance_p is None and d.riff is False for d in _section_diags(grid, old, chords))


def test_section_diags_measure_the_longest_member_with_the_trailing_drop(tmp_path):
    # members 0 (bars 0-1) and 1 (bars 1-4); bar 3 follows the last chord, so the drop is 1 bar
    grid = _grid().model_copy(
        update={
            "sections": [
                Section(label="verse", start_bar=0, end_bar=1, confidence=0.5),
                Section(label="verse", start_bar=1, end_bar=4, confidence=0.5),
            ]
        }
    )
    events = [
        _event(0, 0, 0.0, 2.0, "C:maj"), _event(1, 0, 2.0, 4.0, "G:maj"),
        _event(2, 0, 4.0, 6.0, "A:min"), _event(3, 0, 6.0, 8.0, "N"),
    ]
    chords = Chords(key=Key(tonic="C", mode="major", confidence=0.7), events=events)
    bar_onsets = [["D", "D", "D", "D"], ["D", "-", "U", "-"], ["D", "-", "U", "-"], ["D", "D", "D", "D"]]
    plan = [PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0, 1])]
    strums = _strums(bar_onsets, [_pattern(0, ["D", "-", "U", "-"])], plan=plan)
    (diag,) = _section_diags(grid, strums, chords)
    assert diag.strikes_per_bar == 2.0 and diag.explained == 1.0


def test_section_diags_drop_nothing_when_the_longest_member_is_not_the_grids_last_section():
    # members 0 (bars 0-3) and 1 (bar 3); bar 3 follows the last chord, so the song drops 1 bar,
    # but the figures are read over member 0, which does not end the song: bar 2 still counts
    grid = _grid().model_copy(
        update={
            "sections": [
                Section(label="verse", start_bar=0, end_bar=3, confidence=0.5),
                Section(label="verse", start_bar=3, end_bar=4, confidence=0.5),
            ]
        }
    )
    events = [
        _event(0, 0, 0.0, 2.0, "C:maj"), _event(1, 0, 2.0, 4.0, "G:maj"),
        _event(2, 0, 4.0, 6.0, "A:min"), _event(3, 0, 6.0, 8.0, "N"),
    ]
    chords = Chords(key=Key(tonic="C", mode="major", confidence=0.7), events=events)
    bar_onsets = [["D", "-", "U", "-"], ["D", "-", "U", "-"], ["D", "D", "D", "D"], ["-", "-", "-", "-"]]
    plan = [PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0, 1])]
    strums = _strums(bar_onsets, [_pattern(0, ["D", "-", "U", "-"])], plan=plan)
    (diag,) = _section_diags(grid, strums, chords)
    assert diag.analysed_start == 0
    assert diag.strikes_per_bar == 8 / 3  # with bar 2 dropped it would be 2.0


def test_key_line_prints_the_votes():
    key = Key(tonic="F", mode="major", confidence=0.1,
              tonic_votes=TonicVotes(score="C", pair="F", mix="F", decided_by="mix"))
    assert _key_line(key).endswith("votes score C pair F mix F (mix))")
    none = Key(tonic="F", mode="major", confidence=0.1,
               tonic_votes=TonicVotes(score="C", pair=None, mix="F", decided_by="score"))
    assert _key_line(none).endswith("votes score C pair none mix F (score))")
    assert "votes" not in _key_line(Key(tonic="F", mode="major", confidence=0.1))


def test_key_line_prints_the_set_votes():
    key = Key(tonic="G", mode="major", confidence=0.1, tonic_votes=TonicVotes(
        score="E", pair="E", mix="E", decided_by="set", set_tonic="G", set_share_best=0.82,
        set_share_decided=0.82,
    ))
    assert _key_line(key).endswith("votes score E pair E mix E set G best 0.82 decided 0.82 (set))")


def test_comparison_cell_shows_p_and_riff_and_flags_a_change(tmp_path):
    a = _plan_run(tmp_path / "a", riff=False)
    b = _plan_run(tmp_path / "b", riff=True)
    c = compare_runs(a, b)
    text = format_comparison(c)
    assert "p 0.020" in text and "riff" in text
    assert [delta.changed for delta in c.deltas] == [True]
    same = compare_runs(a, a)
    assert [delta.changed for delta in same.deltas] == [False]
    certain = compare_runs(a, _plan_run(tmp_path / "c", uncertain=True))
    assert [delta.changed for delta in certain.deltas] == [True]


def _short_then_long_grid() -> Grid:
    """Two verses: bars 0-1 and 1-4, so the second is a merged plan's longest member."""
    return _grid().model_copy(
        update={
            "sections": [
                Section(label="verse", start_bar=0, end_bar=1, confidence=0.5),
                Section(label="verse", start_bar=1, end_bar=4, confidence=0.5),
            ]
        }
    )


def test_compare_pairs_a_merged_section_with_its_longest_members_counterpart(tmp_path):
    # run A merged both grid sections into one verse, read over bars 1-4; run B kept them apart
    merged = _strums(
        [["D", "-", "U", "-"]] * 4,
        [_pattern(0, ["D", "-", "U", "-"], riff=True, uncertain=False)],
        plan=[PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0, 1])],
    )
    apart = _strums(
        [["D", "-", "U", "-"]] * 4,
        [_pattern(0, ["D", "-", "-", "-"], riff=False, uncertain=True),
         _pattern(1, ["D", "-", "U", "-"], riff=True, uncertain=False)],
        plan=[
            PlannedSection(start_bar=0, end_bar=1, label="verse", members=[0]),
            PlannedSection(start_bar=1, end_bar=4, label="verse", members=[1]),
        ],
    )
    a = _run_with(tmp_path / "a", grid=_short_then_long_grid(), strums=merged)
    b = _run_with(tmp_path / "b", grid=_short_then_long_grid(), strums=apart)
    c = compare_runs(a, b)
    assert [(left and left.index, right and right.index) for left, right in c.sections] == [(None, 0), (0, 1)]
    assert c.deltas[0] is None
    assert not c.deltas[1].riff_changed and not c.deltas[1].certainty_changed
    assert not c.deltas[1].changed
    assert not any("position" in note for note in c.notes)
    # by position the merged verse would meet B's one-bar verse: both marks would flip
    text = format_comparison(c)
    assert "riff flag changed" not in text and "certainty changed" not in text


def test_compare_falls_back_to_position_when_the_grids_differ(tmp_path):
    strums = _strums(
        [["D", "-", "U", "-"]] * 4,
        [_pattern(0, ["D", "-", "U", "-"]), _pattern(1, ["D", "-", "U", "-"])],
    )
    a = _run_with(tmp_path / "a", grid=_sectioned_grid(), strums=strums)
    b = _run_with(tmp_path / "b", grid=_short_then_long_grid(), strums=strums)
    c = compare_runs(a, b)
    assert [(left.index, right.index) for left, right in c.sections] == [(0, 0), (1, 1)]
    assert any("pairs matched by position" in note for note in c.notes)
    fewer = _strums([["D", "-", "U", "-"]] * 4, [_pattern(0, ["D", "-", "U", "-"])])
    one = _run_with(tmp_path / "one", grid=_grid(), strums=fewer)
    assert "section counts differ (2 vs 1); pairs matched by position" in compare_runs(a, one).notes


def test_evaluate_prints_the_plan_section_line_and_the_votes(tmp_path):
    key = Key(tonic="C", mode="major", confidence=0.4,
              tonic_votes=TonicVotes(score="C", pair="C", mix="G", decided_by="agreement"))
    run = _plan_run(tmp_path / "run", riff=True)
    chords = _chords().model_copy(update={"key": key})
    save_model(run / "03_harmony" / "chords.json", chords)
    lines = format_report(evaluate_run(run)).splitlines()
    assert any(line.endswith("votes score C pair C mix G (agreement))") for line in lines)
    assert (
        "  0 Verse (grid 0, 1: verse, chorus) bars 0-4: D-U-, conf 0.80, strikes/bar 2.0, "
        "explained 100.0%, rests 50.0%, p 0.020, density 0.50, riff 0.40/0.70 (12 onsets) riff, pcs n/a, root n/a, named n/a, rings n/a"
    ) in lines


def test_section_diags_carry_the_pattern_confidence_and_the_sheets_numbered_names():
    grid = _grid().model_copy(
        update={
            "sections": [
                Section(label="verse", start_bar=0, end_bar=1, confidence=0.5),
                Section(label="chorus", start_bar=1, end_bar=2, confidence=0.5),
                Section(label="verse", start_bar=2, end_bar=4, confidence=0.5),
            ]
        }
    )
    plan = [
        PlannedSection(start_bar=s.start_bar, end_bar=s.end_bar, label=s.label, members=[i])
        for i, s in enumerate(grid.sections)
    ]
    patterns = [_pattern(i, ["D", "-", "U", "-"]) for i in range(3)]
    diags = _section_diags(grid, _strums([["D", "-", "U", "-"]] * 4, patterns, plan=plan), _chords())
    assert [d.name for d in diags] == ["Verse 1", "Chorus", "Verse 2"]
    assert [d.label for d in diags] == ["verse", "chorus", "verse"]
    assert all(d.pattern == ["D", "-", "U", "-"] and d.confidence == 0.8 for d in diags)


# ---- 1.6: the vote, the ring flag, member patterns, the riff gate, bars in compare ----

SECTION_SLOTS = ["D", "-", "U", "-", "D", "-", "U", "-"]
OWN_SLOTS = ["D", "-", "-", "-", "-", "-", "-", "-"]


def _wide_grid() -> Grid:
    bars = [
        Bar(index=i, start=i * 2.0, end=(i + 1) * 2.0, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(12)
    ]
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=[i * 0.5 for i in range(48)],
        downbeats=[4 * i for i in range(12)], bars=bars,
        sections=[
            Section(label="verse", start_bar=0, end_bar=8, confidence=0.5),
            Section(label="verse", start_bar=8, end_bar=12, confidence=0.5),
        ],
        octave_decision="none", bar_loudness_db=[-20.0] * 12, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _wide_chords() -> Chords:
    events = [_event(i, 0, i * 2.0, (i + 1) * 2.0, "C:maj") for i in range(12)]
    return Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=events)


def _bar(index, member, slots, uncertain=False, rests=False) -> BarStrums:
    return BarStrums(
        index=index, member=member, strokes=[], pattern=slots, uncertain=uncertain, rests=rests
    )


def _wide_strums(candidate="medoid", changed=(), with_bars=True, rests=(), **fields) -> Strums:
    """One planned section over two members (bars 0-8 and 8-12); `changed` bars print their own."""
    pattern = _pattern(0, SECTION_SLOTS, candidate=candidate, **fields)
    bars = [
        _bar(i, 0 if i < 8 else 1, OWN_SLOTS if i in changed else SECTION_SLOTS,
             uncertain=i in changed, rests=i in rests)
        for i in range(12)
    ]
    return Strums(
        slots_per_bar=8, source="mix", source_ratio=1.0, grid_fit=0.9, uncertain=False,
        patterns=[pattern], bar_onsets=[SECTION_SLOTS] * 12,
        plan=[PlannedSection(start_bar=0, end_bar=12, label="verse", members=[0, 1])],
        bars=bars if with_bars else [],
    )


def _wide_run(path, strums) -> Path:
    return _run_with(path, grid=_wide_grid(), chords=_wide_chords(), strums=strums)


def test_section_line_prints_the_vote_the_ring_and_member_patterns(tmp_path):
    strums = _wide_strums(
        changed=(8, 9, 10, 11), score_medoid=0.63, score_majority=0.58,
        pitch_change_share=0.72, rings=True, ring_decay_db=2.1,
    )
    text = format_report(evaluate_run(_wide_run(tmp_path / "run", strums)))
    assert "vote medoid (0.63 vs 0.58)" in text and "rings 2.1dB" in text
    assert "pcs 0.72" in text
    assert "    member 8-12 prints own D------- (uncertain)" in text
    assert "member 0-8" not in text  # that member prints the section's own pattern
    assert "unit 2" not in text


def test_section_line_prints_short_unit_and_na_figures(tmp_path):
    strums = _wide_strums(
        candidate="majority", score_medoid=0.54, score_majority=0.55, unit=2,
        rings=False, ring_decay_db=13.5,
    )
    text = format_report(evaluate_run(_wide_run(tmp_path / "run", strums)))
    assert "vote majority (0.55 vs 0.54)" in text and "unit 2" in text
    assert "short 13.5dB" in text and "pcs n/a" in text
    unknown = format_report(evaluate_run(_wide_run(tmp_path / "other", _wide_strums())))
    assert "rings n/a" in unknown


def test_section_line_prints_the_riff_gate(tmp_path):
    run = _wide_run(tmp_path / "run", _wide_strums())
    (run / "05_riff").mkdir()
    gate = dict(
        section=0, start_bar=0, end_bar=12, unit=1, onsets=[], riff=[], candidate="medoid",
        octave_shift=0,
    )
    save_model(run / "05_riff" / "riff.json", Riffs(sections=[
        RiffSection(agreement=0.74, support=0.80, named_share=0.91, printable=True, **gate)
    ]))
    text = format_report(evaluate_run(run))
    assert "    riff gate: agreement 0.74 support 0.80 named 0.91 printable" in text
    save_model(run / "05_riff" / "riff.json", Riffs(sections=[
        RiffSection(agreement=0.52, support=0.80, named_share=0.91, printable=False,
                    reason="agreement 0.52 < 0.70", **gate)
    ]))
    text = format_report(evaluate_run(run))
    assert "riff gate: agreement 0.52 support 0.80 named 0.91 not transcribed (agreement 0.52 < 0.70)" in text


def test_compare_counts_bars_whose_pattern_changed_and_the_vote_switch(tmp_path):
    a = _wide_run(tmp_path / "a", _wide_strums(candidate="majority"))
    b = _wide_run(tmp_path / "b", _wide_strums(candidate="medoid", changed=(2, 3, 9, 10)))
    c = compare_runs(a, b)
    assert c.deltas[0].pattern_changes == 4 and c.deltas[0].candidate_changed
    text = format_comparison(c)
    assert "patterns changed in 4 bars" in text and "vote: majority -> medoid" in text
    same = compare_runs(a, a)
    assert same.deltas[0].pattern_changes == 0 and not same.deltas[0].candidate_changed
    assert not same.deltas[0].changed
    assert "patterns changed" not in format_comparison(same)


def test_compare_backfills_a_v15_run(tmp_path):
    a = _wide_run(tmp_path / "a", _wide_strums(with_bars=False))
    b = _wide_run(tmp_path / "b", _wide_strums(changed=(1, 5)))
    c = compare_runs(a, b)
    assert c.deltas[0].pattern_changes == 2
    assert "patterns changed in 2 bars" in format_comparison(c)


def test_evaluate_tolerates_a_1_5_file_with_more_patterns_than_plan_entries(tmp_path):
    strums = _wide_strums(with_bars=False)
    strums = strums.model_copy(update={"patterns": [strums.patterns[0], _pattern(1, SECTION_SLOTS)]})
    text = format_report(evaluate_run(_wide_run(tmp_path / "run", strums)))
    assert "  0 Verse" in text and "member" not in text


def test_report_lists_resting_bars_as_ranges(tmp_path):
    report = evaluate_run(_wide_run(tmp_path / "run", _wide_strums(rests={0, 1, 2, 3, 10, 11})))
    assert report.resting_bars == [0, 1, 2, 3, 10, 11]
    assert "6 bars rest: 0-3, 10, 11" in format_report(report)
    assert report.sections[0].resting_bars == [0, 1, 2, 3, 10, 11]
    quiet = evaluate_run(_wide_run(tmp_path / "quiet", _wide_strums()))
    assert quiet.resting_bars == [] and "bars rest" not in format_report(quiet)


def test_section_line_prints_the_rule_and_the_shares():
    d = SectionDiag(
        index=0, label="verse", strikes_per_bar=3.0, explained=1.0, rest_share=0.0,
        uncertain=False, recall_boost=False, riff=True, riff_rule="A", root_share=0.25,
        named_share=0.6,
    )
    line = _section_line(d)
    assert "rule A" in line and "root 0.25" in line and "named 0.60" in line
    plain = _section_line(SectionDiag(**{**d.__dict__, "riff_rule": None, "root_share": None, "named_share": None}))
    assert "rule A" not in plain and "root n/a" in plain and "named n/a" in plain


def test_section_diag_reads_the_rule_and_shares_from_the_pattern(tmp_path):
    strums = _wide_strums(riff=True, riff_rule="A", root_share=0.3, named_share=0.7)
    diag = evaluate_run(_wide_run(tmp_path / "run", strums)).sections[0]
    assert (diag.riff_rule, diag.root_share, diag.named_share) == ("A", 0.3, 0.7)


def test_compare_counts_rest_changes_and_names_the_rule(tmp_path):
    a = _wide_run(tmp_path / "a", _wide_strums())
    b = _wide_run(tmp_path / "b", _wide_strums(rests={0, 1}, riff=True, riff_rule="A"))
    c = compare_runs(a, b)
    text = format_comparison(c)
    assert c.deltas[0].rest_changes == 2 and c.deltas[0].riff_rule_b == "A"
    assert "rests changed in 2 bars" in text and "(rule A)" in text
    assert c.deltas[0].changed
    same = compare_runs(a, a)
    assert same.deltas[0].rest_changes == 0 and "rests changed" not in format_comparison(same)


def test_ranges():
    assert _ranges([0, 1, 2, 3, 10, 11]) == "0-3, 10, 11" and _ranges([]) == ""
    assert _ranges([5]) == "5" and _ranges([4, 5]) == "4, 5" and _ranges([4, 5, 6]) == "4-6"


HEARD = list("D-DU-UDU")  # the example fixture's figure for bars 0-2


def _truth_run(path: Path) -> Path:
    """The example clip with eight-slot strums: bars 0-1 print the heard figure, bar 2 a
    wrong one, both certain; bar 3 rests. The source carries the credits with upload tags."""
    bars = [
        BarStrums(index=i, member=0, strokes=[], pattern=slots, uncertain=False, rests=i == 3)
        for i, slots in enumerate([HEARD, HEARD, list("D-D-D-DU"), list("--------")])
    ]
    pattern = _pattern(0, HEARD, voted_bars=[0, 1, 2], dropped_bars=[3], top2_margin=0.12)
    strums = Strums(
        slots_per_bar=8, source="mix", source_ratio=1.0, grid_fit=0.9, uncertain=False,
        patterns=[pattern], bar_onsets=[HEARD] * 4,
        plan=[PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0])], bars=bars,
    )
    run = _run_with(path, strums=strums)
    (run / "00_ingest").mkdir()
    save_model(run / "00_ingest" / "source.json", SourceInfo(
        url=None, path=None, video_id=None, title="Example Song (Official Video)",
        artist="THE EXAMPLE BAND", duration=8.0, sample_rate=44100, channels=2,
        fetched_at=datetime(2026, 10, 9, tzinfo=timezone.utc), title_source="credited",
        artist_source="channel",
    ))
    return run


def test_evaluate_with_truth_prints_the_five_blocks_and_na_for_missing_files(tmp_path, capsys):
    _truth_run(tmp_path / "runs" / "demo")
    code = main(["evaluate", "demo", "--truth", str(EXAMPLE), "--runs-dir", str(tmp_path / "runs")])
    out = capsys.readouterr().out.splitlines()
    assert code == 0
    start = out.index("Chord triads: 100.0%") + 1
    assert out[start:] == [
        "Patterns:",
        "  bars 0-2 YES: printed D-DU-UDU, heard D-DU-UDU, jaccard 1.00, swap 0, voted 2, margin 0.12, certain",
        "  bars 2-3 NO: printed D-D-D-DU, heard n/a, jaccard n/a, swap n/a, voted 1, margin 0.12, certain",
        "  false certain 1, false grey 0, discontinuity 0.50",
        "Riffs: precision n/a, recall n/a; baseline not-riff 100.0%, riff 0.0%",
        "Rests: precision 100.0%, recall 100.0%, false rests 0, false holds 0, event F 100.0%",
        "Key vs truth: 100.0% (same), hedge none",
        "Credits: title yes (credited), artist yes (channel)",
    ]
    report = evaluate_run(tmp_path / "runs" / "demo", EXAMPLE)
    assert report.false_certain == 1 and report.false_grey == 0 and report.discontinuity == 0.5
    assert report.riff_scores == (None, None, 1.0, 0.0)
    assert report.rest_scores == (1.0, 1.0, 0, 0, 1.0)
    assert report.key_score == (1.0, "same", None) and report.credits_match == (True, True)

    # a missing file and a file with no record line both print n/a
    truth = tmp_path / "truth"
    shutil.copytree(EXAMPLE, truth)
    (truth / "rests.txt").unlink()
    (truth / "key.txt").write_text("# the sources settle no key\n")
    (truth / "patterns.txt").write_text("\n# nothing judged\n")
    report = evaluate_run(tmp_path / "runs" / "demo", truth)
    assert report.rest_scores is None and report.key_score is None
    assert report.pattern_scores is None and report.false_certain is None
    lines = format_report(report).splitlines()
    assert "Rests: n/a" in lines and "Key vs truth: n/a" in lines and "Patterns: n/a" in lines
    assert "Credits: title yes (credited), artist yes (channel)" in lines
    # without truth no truth block prints at all
    plain = format_report(evaluate_run(tmp_path / "runs" / "demo"))
    assert "Patterns" not in plain and "Credits" not in plain


def test_section_line_prints_voted_rival_all_bars_and_bass_gate(tmp_path):
    fields = dict(
        voted_bars=list(range(8)), dropped_bars=[8, 9], top2_margin=0.08,
        runner_up_vector=list("S-S-S-SS"), confidence_all_bars=0.61, chance_p_all_bars=0.004,
        low_mix_share_bass=0.01, low_mix_share_source=0.82, low_own_share=0.55,
        bass_stem_ratio=0.0012,
    )
    fired = evaluate_run(_wide_run(tmp_path / "fired", _wide_strums(bass_on_stem=True, **fields)))
    diag = fired.sections[0]
    assert diag.voted_bars == list(range(8)) and diag.dropped_bars == [8, 9]
    assert diag.runner_up_vector == list("S-S-S-SS") and diag.bass_on_stem
    assert (diag.low_own_share, diag.bass_stem_ratio) == (0.55, 0.0012)
    line = format_report(fired)
    assert ", voted 8 (dropped 2), rival S-S-S-SS margin 0.08, all-bars conf 0.61 p 0.004" in line
    assert ", bass-on-stem mix-bass 0.010 mix-source 0.820 own 0.550 ratio 0.0012" in line
    held = format_report(evaluate_run(_wide_run(tmp_path / "held", _wide_strums(**fields))))
    assert ", bass gate off mix-bass 0.010 mix-source 0.820 own 0.550 ratio 0.0012" in held
    # a 1.7 run: the fields default and its line prints as 1.7's did
    old = format_report(evaluate_run(_wide_run(tmp_path / "old", _wide_strums())))
    assert "rings n/a\n" in old or old.endswith("rings n/a")
    assert not any(word in old for word in ("voted", "rival", "all-bars", "bass"))


def test_compare_reports_voted_bars_and_bass_gate_changes(tmp_path):
    a = _wide_run(tmp_path / "a", _wide_strums(voted_bars=list(range(8))))
    b = _wide_run(tmp_path / "b", _wide_strums(
        voted_bars=list(range(6)), dropped_bars=[6, 7], bass_on_stem=True, uncertain=True,
    ))
    c = compare_runs(a, b)
    (delta,) = c.deltas
    assert delta.voted_bars_changed and delta.bass_gate_changed and delta.changed
    assert delta.certainty_changed and delta.certainty_readings == (True, False)
    text = format_comparison(c)
    assert "certainty changed (certain -> grey)" in text
    assert "voted bars changed" in text and "bass gate changed (off -> on)" in text
    same = compare_runs(a, a)
    (delta,) = same.deltas
    assert not (delta.voted_bars_changed or delta.bass_gate_changed or delta.changed)
    assert delta.certainty_readings == (True, True)
    assert "voted bars" not in format_comparison(same) and "bass gate" not in format_comparison(same)
