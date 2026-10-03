import json

import pytest
from pydantic import ValidationError

from youkelele.jsonio import ArtifactError, load_model, save_model
from youkelele.schemas import Chords, Grid, Key, Meter, Strums


def make_grid(n_bars=8):
    beats = [i * 0.5 for i in range(n_bars * 4)]
    return {
        "schema": 1,
        "bpm": 120.0,
        "meter": {"numerator": 4, "denominator": 4},
        "beats": beats,
        "downbeats": [i * 4 for i in range(n_bars)],
        "bars": [
            {"index": i, "start": i * 2.0, "end": (i + 1) * 2.0, "beats": [i * 4 + j for j in range(4)]}
            for i in range(n_bars)
        ],
        "sections": [{"label": "verse", "start_bar": 0, "end_bar": n_bars, "confidence": 1.0}],
        "octave_decision": "none",
        "bar_loudness_db": [-20.0] * n_bars,
        "sections_k": 1,
        "largest_cluster_share": 1.0,
        "chorus_margin_db": None,
        "labels_low_confidence": False,
    }


def _load_grid_error(tmp_path, grid):
    (tmp_path / "grid.json").write_text(json.dumps(grid))
    with pytest.raises(ArtifactError) as e:
        load_model(tmp_path / "grid.json", Grid)
    return str(e.value)


def test_valid_grid_loads(tmp_path):
    (tmp_path / "grid.json").write_text(json.dumps(make_grid()))
    assert len(load_model(tmp_path / "grid.json", Grid).bars) == 8


def test_grid_rejects_sections_that_do_not_cover_all_bars(tmp_path):
    grid = make_grid(n_bars=8)
    grid["sections"] = [{"label": "verse", "start_bar": 0, "end_bar": 6, "confidence": 1.0}]
    msg = _load_grid_error(tmp_path, grid)
    assert "grid.json" in msg and "sections" in msg


def test_grid_rejects_unsorted_beats(tmp_path):
    grid = make_grid()
    grid["beats"][:3] = [0.0, 1.0, 0.5]
    assert "beats" in _load_grid_error(tmp_path, grid)


def test_grid_rejects_loudness_length_mismatch(tmp_path):
    grid = make_grid()
    grid["bar_loudness_db"] = [-20.0]
    assert "bar_loudness_db" in _load_grid_error(tmp_path, grid)


def test_grid_rejects_downbeat_out_of_range(tmp_path):
    grid = make_grid()
    grid["downbeats"][-1] = 999
    assert "downbeats" in _load_grid_error(tmp_path, grid)


def test_grid_rejects_misindexed_bars(tmp_path):
    grid = make_grid()
    grid["bars"][2]["index"] = 5
    assert "bars" in _load_grid_error(tmp_path, grid)


def _strums(slots):
    return {
        "slots_per_bar": 8,
        "source": "mix",
        "source_ratio": 1.0,
        "grid_fit": 1.0,
        "uncertain": False,
        "patterns": [
            {
                "section": 0,
                "slots": slots,
                "confidence": 1.0,
                "bar_repeat": 1.0,
                "uncertain": False,
                "no_instrument": False,
                "inherited_from": None,
            }
        ],
        "bar_onsets": [["D", "-", "U", "-", "D", "-", "U", "-"]],
    }


def test_strums_accepts_correct_slot_length():
    Strums.model_validate(_strums(["D", "-", "U", "-", "D", "-", "U", "-"]))


def test_strums_rejects_wrong_slot_length():
    with pytest.raises(ValidationError):
        Strums.model_validate(_strums(["D", "-", "U", "-", "D", "-", "U"]))


def test_strums_rejects_wrong_bar_onsets_length():
    data = _strums(["D", "-", "U", "-", "D", "-", "U", "-"])
    data["bar_onsets"] = [["D"]]
    with pytest.raises(ValidationError):
        Strums.model_validate(data)


def test_meter_parse():
    assert Meter.parse("3/4") == Meter(numerator=3, denominator=4)


def test_round_trip_preserves_schema_alias(tmp_path):
    save_model(tmp_path / "k.json", Chords(key=Key(tonic="C", mode="major", confidence=1.0), events=[]))
    assert json.loads((tmp_path / "k.json").read_text())["schema"] == 1
    assert load_model(tmp_path / "k.json", Chords).key.tonic == "C"
    assert list(tmp_path.iterdir()) == [tmp_path / "k.json"]


def test_save_model_rejects_invalid_mutated_model(tmp_path):
    grid = Grid.model_validate(make_grid(n_bars=8))
    grid.sections = [grid.sections[0].model_copy(update={"end_bar": 6})]
    with pytest.raises(ArtifactError) as e:
        save_model(tmp_path / "grid.json", grid)
    assert "sections" in str(e.value)
    assert list(tmp_path.iterdir()) == []
