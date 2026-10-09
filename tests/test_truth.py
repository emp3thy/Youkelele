from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from youkelele.schemas import (
    Bar,
    BarStrums,
    Grid,
    Key,
    Meter,
    PlannedSection,
    Section,
    SectionPattern,
    SourceInfo,
    Strums,
    TonicVotes,
)
from youkelele.truth import (
    CreditsTruth,
    KeyTruth,
    PatternTruth,
    RangeLabel,
    TruthFormatError,
    discontinuity,
    false_certain,
    false_grey,
    read_credits,
    read_key,
    read_labels,
    read_patterns,
    score_credits,
    score_flags,
    score_key,
    score_patterns,
    score_rests,
)

EXAMPLE = Path(__file__).parent / "fixtures" / "ground_truth" / "example"
HEARD = list("D-DU-UDU")  # the example fixture's figure for bars 0-2
OTHER = list("D-D-UUDU")  # one onset slid by one slot from HEARD
WRONG = list("D-D-D-DU")
REST = list("--------")


def _grid(n: int = 4) -> Grid:
    bars = [
        Bar(index=i, start=i * 2.0, end=(i + 1) * 2.0, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(n)
    ]
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=[i * 0.5 for i in range(4 * n)],
        downbeats=[4 * i for i in range(n)], bars=bars,
        sections=[Section(label="verse", start_bar=0, end_bar=n, confidence=0.5)],
        octave_decision="none", bar_loudness_db=[-20.0] * n, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _bar(index, slots, uncertain=False, riff=False, rests=False) -> BarStrums:
    return BarStrums(
        index=index, member=0, strokes=[], pattern=slots, uncertain=uncertain, riff=riff,
        rests=rests,
    )


def _strums(bars: list[BarStrums], riff: bool = False) -> Strums:
    """One planned section over every bar; bars 0-2 voted, the last bar dropped."""
    n = len(bars)
    pattern = SectionPattern(
        section=0, slots=HEARD, confidence=0.8, bar_repeat=0.8, uncertain=False,
        no_instrument=False, inherited_from=None, riff=riff, voted_bars=[0, 1, 2],
        dropped_bars=[n - 1], top2_margin=0.12,
    )
    return Strums(
        slots_per_bar=8, source="mix", source_ratio=1.0, grid_fit=0.9, uncertain=False,
        patterns=[pattern], bar_onsets=[HEARD] * n,
        plan=[PlannedSection(start_bar=0, end_bar=n, label="verse", members=[0])], bars=bars,
    )


def test_read_patterns_parses_ranges_verdicts_and_optional_figures(tmp_path):
    assert read_patterns(EXAMPLE / "patterns.txt") == [
        PatternTruth(0, 2, "YES", ["D-DU-UDU"]),
        PatternTruth(2, 3, "NO", None),
    ]
    two = tmp_path / "patterns.txt"
    two.write_text("# a comment line\n\n4 6 MOSTLY D-D-D-DU DUDUDUDU  # a two-bar figure\n")
    assert read_patterns(two) == [PatternTruth(4, 6, "MOSTLY", ["D-D-D-DU", "DUDUDUDU"])]
    assert read_labels(EXAMPLE / "riffs.txt") == [RangeLabel(0, 3, "strum")]
    assert read_labels(EXAMPLE / "rests.txt") == [RangeLabel(3, 4, "rest")]
    assert read_key(EXAMPLE / "key.txt") == KeyTruth("C", "major", "fixture", ("A", "minor"))
    assert read_credits(EXAMPLE / "credits.txt") == CreditsTruth("Example Song", "The Example Band")


def test_hash_starts_a_comment_only_at_line_start_or_after_whitespace(tmp_path):
    key = tmp_path / "key.txt"
    key.write_text("#C major old  # a commented-out line\nC# minor https://example.org/a#b   # sharp\n")
    assert read_key(key) == KeyTruth("C#", "minor", "https://example.org/a#b", None)
    empty = tmp_path / "empty.txt"
    empty.write_text("# no record line here\n\n   # nor here\n")
    assert read_key(empty) is None and read_credits(empty) is None
    assert read_patterns(empty) == [] and read_labels(empty) == []


@pytest.mark.parametrize(
    ("name", "text", "detail"),
    [
        ("patterns.txt", "0 2 YES D-DU-UDU\n2 x NO\n", "start and end"),
        ("patterns.txt", "0 2 PERHAPS\n", "verdict"),
        ("patterns.txt", "0 2 YES D-DQ-UDU\n", "figure"),
        ("patterns.txt", "3 2 NO\n", "end"),
        ("riffs.txt", "0 3 chords\n", "label"),
        ("rests.txt", "0 3\n", "start end label"),
        ("key.txt", "H major src\n", "key"),
        ("key.txt", "C dorian src\n", "key"),
        ("key.txt", "C major\n", "tonic mode source"),
        ("key.txt", "C major a\nA minor b\nG major c\n", "two"),
        ("credits.txt", "Only A Title\n", "artist"),
    ],
)
def test_malformed_truth_line_raises_truth_format_error(tmp_path, name, text, detail):
    path = tmp_path / name
    path.write_text(text)
    reader = {
        "patterns.txt": read_patterns, "riffs.txt": read_labels, "rests.txt": read_labels,
        "key.txt": read_key, "credits.txt": read_credits,
    }[name]
    with pytest.raises(TruthFormatError) as raised:
        reader(path)
    assert raised.value.path == path and detail in raised.value.detail
    assert raised.value.line_number == len(text.splitlines())


def test_score_patterns_reports_jaccard_swap_and_false_certain():
    truth = read_patterns(EXAMPLE / "patterns.txt")
    strums = _strums([_bar(0, HEARD), _bar(1, HEARD), _bar(2, WRONG), _bar(3, REST, rests=True)])
    yes, no = score_patterns(truth, strums, _grid())
    assert (yes.start, yes.end, yes.verdict) == (0, 2, "YES")
    assert yes.printed == ["D-DU-UDU"] and yes.figure == ["D-DU-UDU"]
    assert (yes.jaccard, yes.swap, yes.certain) == (1.0, 0, True)
    assert (yes.voted_bars, yes.top2_margin) == (2, 0.12)  # bars 0 and 1 voted
    assert no.printed == ["D-D-D-DU"] and no.figure is None
    assert (no.jaccard, no.swap, no.certain, no.voted_bars) == (None, None, True, 1)
    assert false_certain([yes, no]) == 1 and false_grey([yes, no]) == 0
    assert discontinuity(strums) == 0.5  # two changes (1 to 2, 2 to 3) over four bars

    # bar 0 prints one onset a slot late, grey: Jaccard 5/7, swap 1, a false grey
    grey = _strums([_bar(0, OTHER, uncertain=True), _bar(1, HEARD), _bar(2, WRONG), _bar(3, REST)])
    yes, no = score_patterns(truth, grey, _grid())
    assert yes.printed == ["D-D-UUDU"] and abs(yes.jaccard - 5 / 7) < 1e-9 and yes.swap == 1
    assert yes.certain is False
    assert false_certain([yes, no]) == 1 and false_grey([yes, no]) == 1

    # a two-bar figure reads the range's first two printed bars
    two = [PatternTruth(0, 2, "YES", ["D-D-UUDU", "D-DU-UDU"])]
    (score,) = score_patterns(two, grey, _grid())
    assert score.printed == ["D-D-UUDU", "D-DU-UDU"] and score.jaccard == 1.0 and score.swap == 0


def test_score_flags_counts_mixed_as_a_hit_and_prints_both_baselines():
    truth = [RangeLabel(0, 2, "mixed"), RangeLabel(2, 3, "strum"), RangeLabel(3, 4, "bleed")]
    member_riff = _strums([_bar(0, HEARD, riff=True), _bar(1, HEARD, riff=True), _bar(2, HEARD),
                           _bar(3, HEARD)])
    precision, recall, not_riff, riff = score_flags(truth, member_riff, _grid())
    assert (precision, recall) == (1.0, 1.0)  # the mixed range flagged by its bar records
    assert abs(not_riff - 2 / 3) < 1e-9 and abs(riff - 1 / 3) < 1e-9
    # every bar a riff (as the stage writes a riff section's members): the strum and the bleed
    # are false flags
    all_riff = _strums([_bar(i, HEARD, riff=True) for i in range(4)], riff=True)
    precision, recall, _, _ = score_flags(truth, all_riff, _grid())
    assert abs(precision - 1 / 3) < 1e-9 and recall == 1.0
    # the section is a riff (its longest member's flag) but the strum's and the bleed's own
    # bars are not: those ranges are not flagged
    member_strum = _strums([_bar(0, HEARD, riff=True), _bar(1, HEARD, riff=True), _bar(2, HEARD),
                            _bar(3, HEARD)], riff=True)
    assert score_flags(truth, member_strum, _grid())[:2] == (1.0, 1.0)
    assert score_flags([RangeLabel(2, 3, "strum")], member_strum, _grid())[:2] == (None, None)
    # a range the run records no bar of falls back to its planned section's pattern
    no_records = _strums([_bar(0, HEARD), _bar(1, HEARD)], riff=True)
    no_records = no_records.model_copy(update={
        "plan": [PlannedSection(start_bar=0, end_bar=4, label="verse", members=[0])],
    })
    assert score_flags([RangeLabel(2, 4, "riff")], no_records, _grid())[:2] == (1.0, 1.0)
    # the example's one strum range: nothing flagged, no riff to find
    example = read_labels(EXAMPLE / "riffs.txt")
    assert score_flags(example, _strums([_bar(i, HEARD) for i in range(4)]), _grid()) == (
        None, None, 1.0, 0.0,
    )


def test_score_rests_counts_deletions_and_insertions_apart_and_skips_contested():
    truth = [
        RangeLabel(0, 1, "play"), RangeLabel(1, 3, "rest"), RangeLabel(3, 4, "tail"),
        RangeLabel(4, 5, "contested"), RangeLabel(5, 7, "play"), RangeLabel(7, 8, "rest"),
    ]
    resting = {0, 1, 2, 4, 7}
    strums = _strums([_bar(i, HEARD, rests=i in resting) for i in range(8)])
    precision, recall, deletions, insertions, event_f = score_rests(truth, strums)
    assert (precision, recall) == (0.75, 0.75)  # bars 1, 2 and 7 of 0, 1, 2, 7 and 1, 2, 3, 7
    assert deletions == 1  # bar 0 plays and is rested; bar 4 is contested and not counted
    assert insertions == 1  # bar 3 is a tail and is held
    assert event_f == 1.0  # 0-2 meets 1-3 within one bar at each edge; 7 meets 7
    # beyond the collar: a rest region two bars short at its end does not match
    late = _strums([_bar(i, HEARD, rests=i in {1, 7}) for i in range(8)])
    assert score_rests(truth, late)[4] == 0.5  # one of two regions matched on each side
    example = read_labels(EXAMPLE / "rests.txt")
    held = _strums([_bar(i, HEARD) for i in range(4)])
    assert score_rests(example, held) == (None, 0.0, 0, 1, 0.0)


def test_score_key_takes_the_better_of_truth_and_alternative():
    truth = read_key(EXAMPLE / "key.txt")  # C major, or A minor
    lead = Key(tonic="A", mode="minor", confidence=0.9)
    assert score_key(truth, lead) == (1.0, "same", None)  # the alternative, exactly; no hedge
    assert score_key(truth, Key(tonic="G", mode="major", confidence=0.9)) == (0.5, "fifth", None)
    assert score_key(truth, Key(tonic="C", mode="minor", confidence=0.9)) == (0.2, "parallel", None)
    assert score_key(KeyTruth("C#", "minor", "src", None), Key(tonic="C#", mode="minor", confidence=1.0))[0] == 1.0
    # the chord set replaced the tonic: hedged with the relative key, A minor, which is the truth's
    by_set = Key(tonic="C", mode="major", confidence=0.9, method="chords_stems", margin=0.4,
                 tonic_votes=TonicVotes(decided_by="set"))
    assert score_key(truth, by_set) == (1.0, "same", True)
    # a close margin names an unrelated runner-up: the hedge names no related key
    close = Key(tonic="C", mode="major", confidence=0.9, method="chords_stems", margin=0.01,
                runner_up="F#", hedge_mode="major")
    assert score_key(truth, close) == (1.0, "same", False)


def _source(title: str, artist: str | None) -> SourceInfo:
    return SourceInfo(
        url=None, path=None, video_id=None, title=title, artist=artist, duration=8.0,
        sample_rate=44100, channels=2, fetched_at=datetime(2026, 10, 9, tzinfo=timezone.utc),
    )


def test_score_credits_ignores_case_and_tags():
    truth = read_credits(EXAMPLE / "credits.txt")
    assert score_credits(truth, _source("EXAMPLE SONG (Official Video)", "the example band")) == (True, True)
    assert score_credits(truth, _source("“Example Song” [HD]", "The Example Band")) == (True, True)
    assert score_credits(truth, _source("Example Song Two", None)) == (False, False)
    assert score_credits(truth, _source("Example Song", "Example Band")) == (True, False)
