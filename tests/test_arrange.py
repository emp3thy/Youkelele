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


def test_choose_capo_zero_for_c_g_am_f(db):
    assert choose_capo(["C:maj", "G:maj", "A:min", "F:maj"] * 4, db) == (0, 0)


def test_choose_capo_moves_eb_bb_cm_ab_to_capo_3(db):
    assert choose_capo(EB_LABELS, db) == (3, -3)
    assert [transpose_label(lab, -3) for lab in EB_LABELS[:4]] == ["C:maj", "G:maj", "A:min", "F:maj"]


@pytest.mark.parametrize(
    "labels,capo",
    [(S69_LABELS, 0), (PSSOM_LABELS, 4), (RIPTIDE_LABELS, 0), (RAINBOW_LABELS, 0), (SEVENTHS_LABELS, 0)],
)
def test_choose_capo_matches_published_charts(db, labels, capo):
    assert choose_capo(labels, db) == (capo, -capo)


def test_score_capo_uses_mean_and_penalties(db):
    assert score_capo(["C:maj"] * 3, 0, db) == pytest.approx(0.4)
    # C:maj down 3 is A:maj (open 2100, cost 1.3) plus the capo penalty 0.9
    assert score_capo(["C:maj"] * 3, 3, db) == pytest.approx(1.3 + 0.9)
    # an event with no shape costs 5.0
    assert score_capo(["E:maj(9)"], 0, db) == pytest.approx(5.0)


def test_score_capo_extra_penalty_above_capo_3(db):
    # C down 4 is Ab (cost known from chords-db); compare against shape-only cost
    from youkelele.music.shapes import harte_to_db, shape_cost

    root, suffix = harte_to_db("G#:maj")
    best = min(shape_cost(s) for s in db.shapes(root, suffix))
    assert score_capo(["C:maj"], 4, db) == pytest.approx(best + 0.3 * 4 + 0.3 * 1)


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


def test_simplify_left_blank_when_nothing_found(db):
    assert simplify_for_tier("Q:weird", "full", db) == ("N", "no shape; left blank")


def test_display_names_for_full_tier_sevenths(db):
    names = [display_name_for(lab, db) for lab in ("C:maj7", "A:min7", "D:min7", "G:7")]
    assert names == ["Cmaj7", "Am7", "Dm7", "G7"]
