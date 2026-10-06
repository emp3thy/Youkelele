import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from youkelele.jsonio import ArtifactError, load_model, save_model
from youkelele.schemas import (
    BarStrums,
    Chords,
    Grid,
    Key,
    Meter,
    PlannedSection,
    RiffNote,
    RiffSection,
    Riffs,
    Score,
    ScoreBar,
    ScoreSection,
    SectionPattern,
    SourceInfo,
    Stroke,
    Strums,
    TabNote,
    TonicVotes,
)

FIXTURES = Path(__file__).parent / "fixtures"


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


def _chords_json(label, triad="A:min"):
    event = {
        "bar": 0, "beat": 0, "start": 0.0, "end": 2.0, "label": label, "triad": triad,
        "confidence": 0.9,
    }
    return {"schema": 1, "key": {"tonic": "A", "mode": "minor", "confidence": 0.9}, "events": [event]}


@pytest.mark.parametrize("label", ["Am", "F#m7", ""])
def test_chords_reject_non_harte_label(tmp_path, label):
    (tmp_path / "chords.json").write_text(json.dumps(_chords_json(label)))
    with pytest.raises(ArtifactError) as e:
        load_model(tmp_path / "chords.json", Chords)
    message = str(e.value)
    assert "events" in message and "label" in message
    assert "Harte" in message and "A:min" in message


def test_chords_reject_non_harte_triad(tmp_path):
    (tmp_path / "chords.json").write_text(json.dumps(_chords_json("A:min", triad="Am")))
    with pytest.raises(ArtifactError) as e:
        load_model(tmp_path / "chords.json", Chords)
    assert "events.0.triad" in str(e.value) and "Harte" in str(e.value)


@pytest.mark.parametrize("label", ["N", "X", "A:min", "C#:min7", "C:maj/3", "G"])
def test_chords_accept_harte_labels(tmp_path, label):
    (tmp_path / "chords.json").write_text(json.dumps(_chords_json(label, triad=label)))
    assert load_model(tmp_path / "chords.json", Chords).events[0].label == label


def test_bar_pickup_defaults_false_so_version_1_files_load():
    from youkelele.schemas import Bar

    assert Bar(index=0, start=0, end=1, beats=[0]).pickup is False


def test_version_1_grid_and_score_bar_without_newer_fields_load(tmp_path):
    from youkelele.schemas import ScoreBar

    grid = make_grid()
    for key in ("backbeat_ratio", "drums_silent"):
        assert key not in grid
    assert all("pickup" not in bar for bar in grid["bars"])
    (tmp_path / "grid.json").write_text(json.dumps(grid))
    assert len(load_model(tmp_path / "grid.json", Grid).bars) == 8
    assert ScoreBar.model_validate({"index": 0, "chords": []}).pickup is False


def test_source_info_without_raw_title_loads(tmp_path):
    path = tmp_path / "source.json"
    path.write_text(
        json.dumps(
            {
                "schema": 1,
                "url": None,
                "path": "a.mp3",
                "video_id": None,
                "title": "T",
                "artist": None,
                "duration": 1.0,
                "sample_rate": 44100,
                "channels": 2,
                "fetched_at": "2026-01-01T00:00:00Z",
            }
        )
    )
    info = load_model(path, SourceInfo)
    assert info.raw_title is None and info.title == "T"


def _fixture(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


def test_strums_plan_defaults_empty_and_round_trips():
    s = Strums.model_validate_json(_fixture("v14/strums.json"))
    assert s.plan == []
    s2 = s.model_copy(update={"plan": [PlannedSection(start_bar=0, end_bar=8, label="verse", members=[0, 1])]})
    assert Strums.model_validate_json(s2.model_dump_json()).plan[0].members == [0, 1]


def test_section_pattern_new_fields_default():
    p = SectionPattern(
        section=0, slots=["-"] * 8, confidence=0.0, bar_repeat=0.0,
        uncertain=True, no_instrument=True, inherited_from=None,
    )
    assert (p.chance_p, p.strike_density, p.riff, p.riff_entropy, p.riff_single_share) == (None, None, False, None, None)
    assert p.riff_onsets is None


def test_1_4_strums_patterns_load_without_riff_onsets():
    s = Strums.model_validate_json(_fixture("v14/strums.json"))
    assert all(p.riff_onsets is None for p in s.patterns)


def test_key_votes_default_none_and_load_1_3_and_1_4_keys():
    for fixture in ("v13/chords.json", "v14/chords.json"):
        key = Chords.model_validate_json(_fixture(fixture)).key
        assert key.pair_tonic is None and key.tonic_votes is None
    votes = TonicVotes(score="C", pair="F", mix="F", decided_by="mix")
    assert Key(tonic="F", mode="major", confidence=0.1, tonic_votes=votes).tonic_votes.decided_by == "mix"


def test_score_section_riff_and_members_default():
    sec = ScoreSection(
        label="verse", pattern=["-"] * 8, uncertain=False, bars=[], bar_repeat=0.0, no_instrument=False
    )
    assert sec.riff is False and sec.members == []


def test_strums_v15_fixture_loads_with_empty_bars_and_defaults():
    s = load_model(FIXTURES / "v15_strums.json", Strums)
    assert s.bars == [] and s.patterns[0].candidate == "majority" and s.patterns[0].rings is True


def test_bar_strums_round_trips_and_checks_slot_length():
    bar = BarStrums(index=3, member=0, strokes=[Stroke(slot=0, kind="D", rings=False, decay_db=12.5)], pattern=list("D-D-D-DU"))
    s = Strums(slots_per_bar=8, source="guitar_stem", source_ratio=0.4, grid_fit=0.9, uncertain=False, patterns=[], bar_onsets=[], bars=[bar])
    assert Strums.model_validate_json(s.model_dump_json()).bars[0].strokes[0].decay_db == 12.5
    with pytest.raises(ValidationError):
        Strums(slots_per_bar=8, source="guitar_stem", source_ratio=0.4, grid_fit=0.9, uncertain=False, patterns=[], bar_onsets=[], bars=[bar.model_copy(update={"pattern": list("D-D-")})])


def test_bar_strums_rejects_stroke_slot_out_of_range():
    bar = BarStrums(index=0, member=0, strokes=[Stroke(slot=8, kind="D")], pattern=list("D-------"))
    with pytest.raises(ValidationError):
        Strums(slots_per_bar=8, source="guitar_stem", source_ratio=0.4, grid_fit=0.9, uncertain=False, patterns=[], bar_onsets=[], bars=[bar])


def test_riffs_round_trip_and_reject_negative_fret():
    note = TabNote(slot=2, midi=62, string=1, fret=2)
    sec = RiffSection(section=1, start_bar=13, end_bar=24, unit=1, onsets=[[RiffNote(slot=0, midi=60)]], riff=[note], agreement=0.74, support=0.8, named_share=0.91, candidate="medoid", octave_shift=0, printable=True)
    assert Riffs.model_validate_json(Riffs(sections=[sec]).model_dump_json()).sections[0].riff[0].fret == 2
    with pytest.raises(ValidationError):
        TabNote(slot=2, midi=62, string=1, fret=-1)


def test_riffs_reject_string_out_of_range():
    sec = dict(section=1, start_bar=0, end_bar=4, unit=1, onsets=[], agreement=0.7, support=0.8, named_share=0.9, candidate="majority", octave_shift=0, printable=True)
    with pytest.raises(ValidationError):
        Riffs(sections=[RiffSection(riff=[TabNote(slot=0, midi=60, string=4, fret=0)], **sec)])


def test_score_v15_fixture_loads_with_empty_strokes_and_state():
    sc = load_model(FIXTURES / "v15_score.json", Score)
    bar = sc.sections[0].bars[0]
    assert bar.strokes == [] and bar.tab is None and bar.grey is False and sc.sections[0].state == ""


def test_v16_strums_and_score_load_with_1_7_defaults():
    strums = load_model(FIXTURES / "v16_strums.json", Strums)
    assert all(not b.rests and b.energy_ratio is None and b.low_share is None for b in strums.bars)
    assert all(p.root_share is None and p.named_share is None and p.riff_rule is None for p in strums.patterns)
    score = load_model(FIXTURES / "v16_score.json", Score)
    assert all(b.label == "" and not b.rests for s in score.sections for b in s.bars)


def test_1_7_fields_round_trip():
    bar = BarStrums(index=0, member=0, strokes=[], pattern=["-"] * 8, rests=True, energy_ratio=0.01, low_share=0.0002)
    assert BarStrums.model_validate_json(bar.model_dump_json()).rests
    pattern = SectionPattern(section=0, slots=["-"] * 8, confidence=0, bar_repeat=0, uncertain=True,
                             no_instrument=False, inherited_from=None, root_share=0.9, named_share=0.5, riff_rule="A")
    assert SectionPattern.model_validate_json(pattern.model_dump_json()).riff_rule == "A"
    assert ScoreBar(index=0, chords=[], label="riff heard", rests=False).label == "riff heard"
