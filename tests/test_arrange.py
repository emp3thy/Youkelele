from __future__ import annotations

import pytest

from youkelele.music.arrange import (
    choose_capo,
    score_capo,
    select_voicings,
    simplify_for_tier,
    transpose_label,
)
from youkelele.music.shapes import ShapeDB, display_name_for

S69_LABELS = (
    ["D:maj", "A:maj"] * 6
    + ["B:min", "A:maj", "D:maj", "G:maj"] * 4
    + ["F:maj", "A#:maj", "C:maj", "A#:maj", "F:maj", "A#:maj", "C:maj", "C:maj"]
)
PSSOM_LABELS = (
    ["C#:min"] * 8
    + ["F#:maj", "C#:min", "B:maj"] * 2
    + ["E:maj", "B:maj", "A:maj", "E:maj", "A:maj", "B:maj"]
    + ["E:maj", "A:maj", "B:maj"] * 6
    + ["C#:min"] * 2
)
EB_LABELS = ["D#:maj", "A#:maj", "C:min", "G#:maj"] * 4
RIPTIDE_LABELS = ["A:min", "G:maj", "C:maj", "F:maj"] * 4
RAINBOW_LABELS = [
    "C:maj", "E:min", "F:maj", "C:maj", "F:maj", "E:maj", "A:min", "F:maj", "C:maj",
    "G:maj", "A:min", "F:maj", "C:maj", "E:7", "A:min", "F:maj", "D:7", "G:maj",
]
SEVENTHS_LABELS = ["C:maj7", "A:min7", "D:min7", "G:7", "E:7", "F:maj7"] * 2


@pytest.fixture(scope="module")
def db() -> ShapeDB:
    return ShapeDB.load()


def _fretstr(shape) -> str:
    base = shape.base_fret
    return "".join("x" if f < 0 else str(f if f == 0 else f + base - 1) for f in shape.frets)


def test_transpose_label():
    assert transpose_label("D#:maj", -3) == "C:maj"
    assert transpose_label("Eb:maj", -3) == "C:maj"
    assert transpose_label("C:maj", -1) == "B:maj"
    assert transpose_label("A:min/b3", 2) == "B:min/b3"
    assert transpose_label("C", 2) == "D:maj"
    assert transpose_label("N", 3) == "N"
    assert transpose_label("Eb:maj", 0) == "Eb:maj"
    assert transpose_label("Eb:maj", -3) == "C:maj"


def test_choose_capo_zero_for_c_g_am_f(db):
    assert choose_capo(["C:maj", "G:maj", "A:min", "F:maj"] * 4, db) == (0, 0)


def test_choose_capo_moves_eb_bb_cm_ab_to_capo_3(db):
    assert choose_capo(EB_LABELS, db) == (3, -3)
    assert [transpose_label(lab, -3) for lab in EB_LABELS[:4]] == ["C:maj", "G:maj", "A:min", "F:maj"]


PSSOM_RUN_LABELS = ["C#:maj"] * 6 + ["B:maj"] * 4 + ["E:maj"] * 3 + ["A:maj"] * 2 + ["F#:maj"]  # the run's label mix by frequency
PSSOM_SPIKE_LABELS = ["C#:min", "E:maj", "B:maj", "A:maj"]
CHELSEA_LABELS = ["G:maj"] * 7 + ["D:maj"] * 6 + ["E:min"] * 2 + ["B:min", "C:maj", "A:maj", "A:min", "B:maj"]


@pytest.mark.parametrize(
    "labels,capo",
    [
        (S69_LABELS, 0),
        (PSSOM_RUN_LABELS, 4),
        (PSSOM_SPIKE_LABELS, 4),
        (CHELSEA_LABELS, 0),
        (RIPTIDE_LABELS, 0),
        (["C:maj", "G:maj", "A:min", "F:maj"], 0),
    ],
)
def test_choose_capo_matches_published_charts_with_unique_label_mean(db, labels, capo):
    assert choose_capo(labels, db) == (capo, -capo), [round(score_capo(labels, c, db), 3) for c in range(6)]


@pytest.mark.parametrize("labels", [RAINBOW_LABELS, SEVENTHS_LABELS, PSSOM_LABELS])
def test_choose_capo_other_charts_unchanged(db, labels):
    expected = 4 if labels is PSSOM_LABELS else 0
    assert choose_capo(labels, db) == (expected, -expected)


def test_score_capo_is_mean_over_distinct_labels_plus_0_2_per_fret(db):
    from youkelele.music.arrange import CAPO_FRET_PENALTY

    assert CAPO_FRET_PENALTY == 0.2
    base = score_capo(["C:maj", "G:maj"], 0, db)
    # repeated labels do not change the mean
    assert score_capo(["C:maj"] * 5 + ["G:maj"] * 2 + ["C:maj"], 0, db) == pytest.approx(base)
    assert score_capo(["C:maj", "N", "G:maj", "X"], 0, db) == pytest.approx(base)
    # capo 4 adds exactly 0.8 to the cost of the transposed labels (G# and D#), with no extra term above fret 3
    shifted = score_capo(["C:maj", "G:maj"], 4, db)
    assert shifted == pytest.approx(score_capo(["G#:maj", "D#:maj"], 0, db) + 0.8)
    # an event with no shape costs 5.0
    assert score_capo(["E:maj(9)"], 0, db) == pytest.approx(5.0)


def test_choose_capo_tie_goes_to_lower_capo(db, monkeypatch):
    # real shapes make an exact capo 0 / capo 2 tie awkward to build, so equalise the scores directly
    from youkelele.music import arrange

    monkeypatch.setattr(arrange, "score_capo", lambda labels, capo, db: 1.0 if capo in (0, 2) else 9.0)
    assert choose_capo(["C:maj"], db) == (0, 0)


def test_s69_margin_at_least_0_3(db):
    assert score_capo(S69_LABELS, 2, db) - score_capo(S69_LABELS, 0, db) >= 0.3


def test_select_voicings_one_shape_per_label_and_canonical_shapes(db):
    voicings = select_voicings(S69_LABELS, db)
    assert set(voicings) == set(S69_LABELS)
    got = {lab: _fretstr(s) for lab, s in voicings.items()}
    assert got == {
        "D:maj": "2220",
        "A:maj": "2100",
        "B:min": "4222",
        "G:maj": "0232",
        "F:maj": "2010",
        "A#:maj": "3211",
        "C:maj": "0003",
    }
    assert voicings["B:min"].barres
    assert voicings["A#:maj"].barres


def test_select_voicings_pour_some_sugar_at_capo_4(db):
    played = [transpose_label(lab, -4) for lab in PSSOM_LABELS]
    got = {lab: _fretstr(s) for lab, s in select_voicings(played, db).items()}
    assert got["A:min"] == "2000"
    assert got["C:maj"] == "0003"
    assert got["G:maj"] == "0232"
    assert got["F:maj"] == "2010"


def test_select_voicings_riptide(db):
    got = {lab: _fretstr(s) for lab, s in select_voicings(RIPTIDE_LABELS, db).items()}
    assert got == {"A:min": "2000", "G:maj": "0232", "C:maj": "0003", "F:maj": "2010"}


def test_select_voicings_skips_labels_without_shape(db):
    assert set(select_voicings(["C:maj", "N", "E:maj(9)", "G:maj"], db)) == {"C:maj", "G:maj"}


def test_simplify_easy_reduces_seventh_and_records_reason(db):
    assert simplify_for_tier("G:7", "easy", db) == ("G:maj", "easy tier: reduced to triad")


def test_simplify_full_keeps_seventh(db):
    assert simplify_for_tier("G:7", "full", db) == ("G:7", None)


def test_simplify_passes_no_chord_through(db):
    assert simplify_for_tier("N", "easy", db) == ("N", None)
    assert simplify_for_tier("X", "full", db) == ("X", None)


def test_simplify_unknown_quality_falls_back_to_triad(db):
    assert simplify_for_tier("E:maj(9)", "full", db) == ("E:maj", "no shape in chords-db for maj(9)")


@pytest.mark.parametrize("tier", ["easy", "full"])
def test_simplify_for_tier_maps_power_to_key_quality(db, tier):
    assert simplify_for_tier("C#:5", tier, db) == ("C#:min", "power chord: quality from key")


def test_simplify_left_blank_when_nothing_found(db):
    assert simplify_for_tier("Q:weird", "full", db) == ("N", "no shape; left blank")


def test_display_names_for_full_tier_sevenths(db):
    names = [display_name_for(lab, db) for lab in ("C:maj7", "A:min7", "D:min7", "G:7")]
    assert names == ["Cmaj7", "Am7", "Dm7", "G7"]


def _ev(label: str, seconds: float, start: float = 0.0):
    from youkelele.schemas import ChordEvent

    return ChordEvent(
        bar=0, beat=0, start=start, end=start + seconds, label=label, triad=label, confidence=0.9
    )


def _timeline(spec):
    events, t = [], 0.0
    for label, seconds in spec:
        events.append(_ev(label, seconds, t))
        t += seconds
    return events


def test_passing_label_is_rare_and_short():
    from youkelele.music.arrange import passing_labels

    events = _timeline([("C:maj", 60.0), ("G:maj", 60.0), ("A:min", 40.0), ("B:maj", 0.9)])
    assert passing_labels(events, 2.0) == {"B:maj"}


def test_long_single_event_is_not_passing():
    from youkelele.music.arrange import passing_labels

    events = _timeline([("C:maj", 60.0), ("G:maj", 60.0), ("A:min", 40.0), ("B:maj", 3.0)])
    assert passing_labels(events, 2.0) == set()  # 3 s is 1.8% of the total, but it outlasts a bar


def test_common_label_is_not_passing():
    from youkelele.music.arrange import passing_labels

    events = _timeline(
        [("C:maj", 60.0), ("G:maj", 60.0), ("A:min", 40.0)] + [("F:maj", 1.5)] * 10
    )
    assert passing_labels(events, 2.0) == set()  # every F is short, but 15 s is about 8% of the song


def test_never_fewer_than_three_diagram_chords():
    from youkelele.music.arrange import MIN_DIAGRAM_CHORDS, passing_labels

    events = _timeline(
        [("C:maj", 50.0), ("G:maj", 50.0), ("A:min", 1.0), ("F:maj", 0.9), ("B:maj", 0.8)]
    )
    assert MIN_DIAGRAM_CHORDS == 3
    assert passing_labels(events, 2.0) == {"F:maj", "B:maj"}  # most used rare label keeps its diagram


def test_passing_ignores_blank_events_and_counts_filled_ones():
    from youkelele.music.arrange import passing_labels

    events = _timeline(
        [("C:maj", 60.0), ("G:maj", 60.0), ("A:min", 40.0), ("N", 500.0), ("X", 500.0), ("B:maj", 0.9)]
    )
    assert passing_labels(events, 2.0) == {"B:maj"}
    filled = events[-1].model_copy(update={"filled": True})
    assert passing_labels(events[:-1] + [filled], 2.0) == {"B:maj"}
