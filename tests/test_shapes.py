from __future__ import annotations

import json

import pytest

from youkelele.music.shapes import (
    HARTE_TO_SUFFIX,
    ROOT_TO_DB_KEY,
    ShapeDB,
    display_name_for,
    harte_to_db,
    shape_cost,
)
from youkelele.paths import package_data
from youkelele.schemas import Shape


@pytest.fixture(scope="module")
def db() -> ShapeDB:
    return ShapeDB.load()


def test_db_loads_552_chords_and_c_major_open_shape(db):
    raw = json.loads(package_data("chords-db", "ukulele.json").read_text(encoding="utf-8"))
    assert sum(len(v) for v in raw["chords"].values()) == 552
    assert db.shapes("C", "major")[0].frets == [0, 0, 0, 3]
    assert db.shapes("C", "nonsense") == []
    assert db.shapes("H", "major") == []


def test_harte_to_db_maps_inversion_and_7sus4():
    assert harte_to_db("A:min/b3") == ("A", "minor")
    assert harte_to_db("D:sus4(b7)") == ("D", "7sus4")
    assert harte_to_db("C#:maj") == ("Db", "major")
    assert harte_to_db("E:aug7") == ("E", "aug7")
    assert HARTE_TO_SUFFIX["aug7"] == "aug7"
    assert ROOT_TO_DB_KEY["A#"] == "Bb"


def test_harte_to_db_returns_none_for_unknown_quality_and_no_chord():
    assert harte_to_db("E:maj(9)") is None
    assert harte_to_db("N") is None
    assert harte_to_db("X") is None


def test_shape_cost_prefers_open_c_over_barre(db):
    shapes = db.shapes("C", "major")
    best = min(shapes, key=shape_cost)
    assert best.frets == [0, 0, 0, 3]
    assert shape_cost(best) == pytest.approx(0.4)
    barre = next(s for s in shapes if s.barres)
    assert shape_cost(barre) > shape_cost(best) + 1.5


def test_shape_cost_counts_fingers_above_three():
    four = Shape(frets=[1, 1, 1, 1], fingers=[1, 2, 3, 4], base_fret=1, barres=[])
    three = Shape(frets=[1, 1, 1, 1], fingers=[1, 2, 3, 3], base_fret=1, barres=[])
    assert shape_cost(four) - shape_cost(three) == pytest.approx(0.4)


def test_e_major_resolves_to_1402(db):
    best = min(db.shapes("E", "major"), key=shape_cost)
    assert best.frets == [1, 4, 0, 2]


def test_display_names(db):
    assert db.display_name("C", "major") == "C"
    assert db.display_name("C", "minor") == "Cm"
    assert db.display_name("C", "mmaj7") == "CmMaj7"
    assert db.display_name("C", "m7b5") == "Cm7b5"


def test_display_name_keeps_model_root_spelling(db):
    assert display_name_for("C#:min", db) == "C#m"
    assert display_name_for("Eb:7", db) == "Eb7"
    assert display_name_for("A:min/b3", db) == "Am"
