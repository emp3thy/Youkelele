from __future__ import annotations

from datetime import datetime

import pytest

from youkelele.music import score_builder
from youkelele.music.score_builder import build_score
from youkelele.profiles.ukulele import UKULELE_TUNING
from youkelele.schemas import (
    ArrangedChord,
    Arrangement,
    Bar,
    ChordEvent,
    Chords,
    Grid,
    Key,
    Meter,
    ScoreBar,
    Section,
    SectionPattern,
    Shape,
    SourceInfo,
    Strums,
)

ISLAND = list("D-DU-UDU")
C = Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[])
G = Shape(frets=[0, 2, 3, 2], fingers=[0, 1, 3, 2], base_fret=1, barres=[])
F = Shape(frets=[2, 0, 1, 0], fingers=[2, 0, 1, 0], base_fret=1, barres=[])
BAR = 2.0  # 4/4 at 120 bpm


def _grid(n_bars: int) -> Grid:
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4),
        beats=[i * 0.5 for i in range(n_bars * 4)], downbeats=[4 * i for i in range(n_bars)],
        bars=[
            Bar(index=i, start=i * BAR, end=(i + 1) * BAR, beats=list(range(4 * i, 4 * i + 4)))
            for i in range(n_bars)
        ],
        sections=[Section(label="Verse", start_bar=0, end_bar=n_bars, confidence=0.5)],
        octave_decision="none", bar_loudness_db=[-20.0] * n_bars, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _source() -> SourceInfo:
    return SourceInfo(
        url=None, path="x.mp3", video_id=None, title="Song", artist="Band", duration=10.0,
        sample_rate=44100, channels=2, fetched_at=datetime(2026, 1, 1),
    )


def _strums(slots=ISLAND, explained=0.0) -> Strums:
    pattern = SectionPattern(
        section=0, slots=list(slots), confidence=0.8, bar_repeat=0.9, uncertain=False,
        no_instrument=False, inherited_from=None, explained=explained,
    )
    return Strums(
        slots_per_bar=len(slots), source="other_stem", source_ratio=0.6, grid_fit=0.9,
        uncertain=True, patterns=[pattern], bar_onsets=[],
    )


def _score(n_bars, events, shapes, capo=0, explained=0.0):
    """events: (start in bars, end in bars, label); shapes: label -> Shape (None for N)."""
    evs = [
        ChordEvent(bar=0, beat=0, start=s * BAR, end=e * BAR, label=lab, triad=lab, confidence=0.9)
        for s, e, lab in events
    ]
    arranged = [
        ArrangedChord(event=i, name=ev.label, shape=shapes[ev.label])
        for i, ev in enumerate(evs)
        if shapes.get(ev.label) is not None
    ]
    return build_score(
        _source(),
        _grid(n_bars),
        Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        _strums(explained=explained),
        Arrangement(capo=capo, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        UKULELE_TUNING,
        "Ukulele",
    )


def _chords(score, bar):
    return score.sections[0].bars[bar].chords


def test_pickup_flag_is_copied_from_the_grid_bar():
    grid = _grid(3)
    grid.bars[0] = grid.bars[0].model_copy(update={"pickup": True})
    score = build_score(
        _source(), grid,
        Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=[]),
        _strums(),
        Arrangement(capo=0, transpose=0, tier="easy", chords=[], substitutions=[]),
        UKULELE_TUNING, "Ukulele",
    )
    assert [b.pickup for b in score.sections[0].bars] == [True, False, False]


def test_diagrams_unique_in_first_appearance_order():
    score = _score(3, [(0, 1, "C"), (1, 2, "G"), (2, 3, "C")], {"C": C, "G": G})
    assert [d.name for d in score.chord_diagrams] == ["C", "G"]
    assert [_chords(score, b)[0].diagram for b in range(3)] == [0, 1, 0]
    assert score.key == "C major"
    assert score.tier == "easy"
    assert score.strum_source == "other_stem"
    assert score.strums_uncertain is True
    assert score.instrument.tuning == ["G4", "C4", "E4", "A4"]
    assert score.instrument.strings == 4
    section = score.sections[0]
    assert section.pattern == ISLAND
    assert section.bar_repeat == 0.9


def test_score_carries_key_hedge_from_chords_key():
    def build(key):
        return build_score(
            _source(), _grid(1), Chords(key=key, events=[]), _strums(),
            Arrangement(capo=0, transpose=0, tier="easy", chords=[], substitutions=[]),
            UKULELE_TUNING, "Ukulele",
        )

    close = Key(tonic="G", mode="major", confidence=0.3, method="chords_stems", margin=0.02,
                mode_margin=0.3, runner_up="D")
    score = build(close)
    assert (score.key, score.key_hedge) == ("G major", "D major")
    clear = close.model_copy(update={"margin": 0.2})
    assert build(clear).key_hedge is None
    assert build(Key(tonic="C", mode="major", confidence=0.9)).key_hedge is None
    # the hedge carries its own mode, not the key's
    a_minor = Key(tonic="A", mode="minor", confidence=0.3, method="chords_stems", margin=0.01,
                  mode_margin=0.3, runner_up="C", hedge_mode="major")
    assert (build(a_minor).key, build(a_minor).key_hedge) == ("A minor", "C major")
    mix = a_minor.model_copy(
        update={"margin": 0.2, "hedge_mode": None, "mix": Key(tonic="F", mode="major", confidence=0.1)}
    )
    assert build(mix).key_hedge == "F major"  # a file from before the stored mode: the mix's own


def test_score_copies_explained():
    score = _score(1, [(0, 1, "C")], {"C": C}, explained=0.85)
    assert score.sections[0].explained == 0.85


def test_chord_change_mid_bar_splits_slots():
    score = _score(1, [(0, 0.5, "C"), (0.5, 1, "G")], {"C": C, "G": G})
    c, g = _chords(score, 0)
    assert (c.name, c.start_slot, c.slots) == ("C", 0, list("D-DU"))
    assert (g.name, g.start_slot, g.slots) == ("G", 4, list("-UDU"))


def test_change_at_three_eighths_rounds_to_slot_3():
    score = _score(1, [(0, 0.375, "C"), (0.375, 1, "G")], {"C": C, "G": G})
    assert [(c.name, c.start_slot, len(c.slots)) for c in _chords(score, 0)] == [
        ("C", 0, 3),
        ("G", 3, 5),
    ]


def test_two_events_rounding_to_same_slot_later_wins():
    # 0.35 and 0.40 of the bar both round to slot 3 (2.8 and 3.2)
    score = _score(1, [(0, 0.35, "C"), (0.35, 0.4, "F"), (0.4, 1, "G")], {"C": C, "F": F, "G": G})
    assert [(c.name, c.start_slot) for c in _chords(score, 0)] == [("C", 0), ("G", 3)]
    assert [d.name for d in score.chord_diagrams] == ["C", "G"]


def test_event_rounding_to_bar_end_moves_to_next_bar_slot_0():
    # starts at 0.97 of bar 0 -> rounds to slot 8 -> bar 1 slot 0
    score = _score(2, [(0, 0.97, "C"), (0.97, 2, "G")], {"C": C, "G": G})
    assert [(c.name, c.start_slot, len(c.slots)) for c in _chords(score, 0)] == [("C", 0, 8)]
    assert [(c.name, c.start_slot, len(c.slots)) for c in _chords(score, 1)] == [("G", 0, 8)]


def test_continuing_event_repeats_at_slot_0_without_new_diagram():
    score = _score(2, [(0, 2, "C")], {"C": C})
    assert [c.name for c in _chords(score, 1)] == ["C"]
    assert _chords(score, 1)[0].diagram == 0
    assert len(score.chord_diagrams) == 1


def test_bar_without_chord_gets_nc():
    score = _score(3, [(0, 1, "C"), (1, 2, "N"), (2, 3, "C")], {"C": C, "N": None})
    (nc,) = _chords(score, 1)
    assert (nc.name, nc.diagram, nc.start_slot, nc.slots) == ("N.C.", -1, 0, ISLAND)


def test_leading_gap_in_bar_is_filled_with_nc():
    score = _score(1, [(0, 0.5, "N"), (0.5, 1, "C")], {"N": None, "C": C})
    chords = _chords(score, 0)
    assert [(c.name, c.diagram, c.start_slot) for c in chords] == [("N.C.", -1, 0), ("C", 0, 4)]
    assert sum(len(c.slots) for c in chords) == 8


def test_every_bar_has_exactly_slots_per_bar_slots():
    score = _score(
        4,
        [(0.5, 1, "C"), (1, 1.4, "N"), (1.4, 2.3, "G"), (2.3, 2.6, "N"), (3.5, 4, "C")],
        {"C": C, "G": G, "N": None},
    )
    for section in score.sections:
        for bar in section.bars:
            slots = [s for c in bar.chords for s in c.slots]
            assert len(slots) == score.slots_per_bar
            assert bar.chords[0].start_slot == 0


def _build(grid, strums):
    return build_score(
        _source(), grid, Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=[]),
        strums, Arrangement(capo=0, transpose=0, tier="easy", chords=[], substitutions=[]),
        UKULELE_TUNING, "Ukulele",
    )


def _split(grid: Grid) -> Grid:
    return grid.model_copy(
        update={
            "sections": [
                Section(label="Verse", start_bar=0, end_bar=1, confidence=0.5),
                Section(label="Chorus", start_bar=1, end_bar=2, confidence=0.5),
            ]
        }
    )


def test_split_section_without_rerunning_strums_is_a_clear_error():
    with pytest.raises(ValueError) as e:
        _build(_split(_grid(2)), _strums())
    assert str(e.value) == (
        "strums.json has 1 patterns for 2 sections in grid.json; re-run from strums"
    )


def test_pattern_section_indices_must_match_grid_sections():
    strums = _strums()
    strums.patterns[0] = strums.patterns[0].model_copy(update={"section": 3})
    with pytest.raises(ValueError) as e:
        _build(_grid(2), strums)
    assert "re-run from strums" in str(e.value) and "[3]" in str(e.value)


def test_slots_per_bar_must_fit_the_grid_meter():
    with pytest.raises(ValueError) as e:
        _build(_grid(2), _strums(slots=list("D-DU-U")))
    assert "slots_per_bar 6" in str(e.value) and "re-run from strums" in str(e.value)


def test_inherited_from_is_copied_into_the_score_section():
    strums = _strums()
    inherited = strums.patterns[0].model_copy(update={"section": 1, "inherited_from": 0})
    strums = strums.model_copy(update={"patterns": [strums.patterns[0], inherited]})
    score = _build(_split(_grid(2)), strums)
    assert [s.inherited_from for s in score.sections] == [None, 0]


CALYPSO = list("D-D-DUDU")


def _two_section_strums() -> Strums:
    verse = SectionPattern(
        section=0, slots=list(ISLAND), confidence=0.8, bar_repeat=0.9, uncertain=False,
        no_instrument=False, inherited_from=None,
    )
    chorus = SectionPattern(
        section=1, slots=list(CALYPSO), confidence=0.7, bar_repeat=0.8, uncertain=True,
        no_instrument=False, inherited_from=0,
    )
    return Strums(
        slots_per_bar=8, source="other_stem", source_ratio=0.6, grid_fit=0.9,
        uncertain=False, patterns=[verse, chorus], bar_onsets=[],
    )


def _mid_phrase_score():
    """24 bars, Verse 0-8 and Chorus 8-24; chords change every two bars from bar 9."""
    bounds = [0, 2, 4, 6, 9, 11, 13, 15, 17, 19, 21, 23, 24]
    labels = ["D", "A"] * 6
    evs = [
        ChordEvent(bar=a, beat=0, start=a * BAR, end=b * BAR, label=lab, triad=lab, confidence=0.9)
        for a, b, lab in zip(bounds, bounds[1:], labels)
    ]
    arranged = [
        ArrangedChord(event=i, name=ev.label, shape=C if ev.label == "D" else G)
        for i, ev in enumerate(evs)
    ]
    grid = _grid(24).model_copy(
        update={
            "sections": [
                Section(label="Verse", start_bar=0, end_bar=8, confidence=0.5),
                Section(label="Chorus", start_bar=8, end_bar=24, confidence=0.5),
            ]
        }
    )
    return build_score(
        _source(), grid,
        Chords(key=Key(tonic="D", mode="major", confidence=0.9), events=evs),
        _two_section_strums(),
        Arrangement(capo=0, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        UKULELE_TUNING, "Ukulele",
    )


def _build_events(n_bars, evs, arranged):
    return build_score(
        _source(), _grid(n_bars),
        Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        _strums(),
        Arrangement(capo=0, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        UKULELE_TUNING, "Ukulele",
    )


def _ev(start, end, label, filled=False):
    return ChordEvent(
        bar=int(start), beat=0, start=start * BAR, end=end * BAR, label=label, triad=label,
        confidence=0.9, filled=filled,
    )


def test_score_copies_filled_and_passing_flags():
    evs = [_ev(0, 1, "C"), _ev(1, 2, "G", filled=True), _ev(2, 2.5, "F"), _ev(2.5, 3, "C")]
    arranged = [
        ArrangedChord(event=0, name="C", shape=C),
        ArrangedChord(event=1, name="G", shape=G),
        ArrangedChord(event=2, name="F", shape=F, passing=True),
        ArrangedChord(event=3, name="C", shape=C),
    ]
    score = _build_events(3, evs, arranged)
    flags = [
        [(c.name, c.filled, c.passing) for c in bar.chords] for bar in score.sections[0].bars
    ]
    assert flags == [
        [("C", False, False)],
        [("G", True, False)],
        [("F", False, True), ("C", False, False)],
    ]


def test_passing_diagram_flagged():
    evs = [_ev(0, 1, "C"), _ev(1, 1.5, "F"), _ev(1.5, 2, "G")]
    arranged = [
        ArrangedChord(event=0, name="C", shape=C),
        ArrangedChord(event=1, name="F", shape=F, passing=True),
        ArrangedChord(event=2, name="G", shape=G),
    ]
    score = _build_events(2, evs, arranged)
    assert [(d.name, d.passing) for d in score.chord_diagrams] == [
        ("C", False), ("F", True), ("G", False),
    ]
    passing_cell = _chords(score, 1)[0]
    assert passing_cell.passing is True
    assert score.chord_diagrams[passing_cell.diagram].name == "F"


def test_diagram_used_both_passing_and_full_is_not_passing():
    evs = [_ev(0, 0.5, "F"), _ev(0.5, 1, "C"), _ev(1, 2, "F")]
    arranged = [
        ArrangedChord(event=0, name="F", shape=F, passing=True),
        ArrangedChord(event=1, name="C", shape=C),
        ArrangedChord(event=2, name="F", shape=F),
    ]
    score = _build_events(2, evs, arranged)
    assert [(d.name, d.passing) for d in score.chord_diagrams] == [("F", False), ("C", False)]


def test_score_sets_power_on_chord_and_diagram():
    evs = [_ev(0, 1, "C#:5"), _ev(1, 2, "G"), _ev(2, 3, "C#:5")]
    arranged = [
        ArrangedChord(event=0, name="C#m", shape=F, power=True),
        ArrangedChord(event=1, name="G", shape=G),
        ArrangedChord(event=2, name="C#m", shape=F, power=True),
    ]
    score = _build_events(3, evs, arranged)
    assert [[(c.name, c.power) for c in bar.chords] for bar in score.sections[0].bars] == [
        [("C#m", True)], [("G", False)], [("C#m", True)],
    ]
    assert [(d.name, d.power) for d in score.chord_diagrams] == [("C#m", True), ("G", False)]


def test_diagram_used_both_power_and_plain_is_power():
    # any use as a power chord gives the legend line; the badge stays on the power cells only
    evs = [_ev(0, 1, "C#:min"), _ev(1, 2, "G"), _ev(2, 3, "C#:5")]
    arranged = [
        ArrangedChord(event=0, name="C#m", shape=F),
        ArrangedChord(event=1, name="G", shape=G),
        ArrangedChord(event=2, name="C#m", shape=F, power=True),
    ]
    score = _build_events(3, evs, arranged)
    assert [(d.name, d.power) for d in score.chord_diagrams] == [("C#m", True), ("G", False)]
    assert [[(c.name, c.power) for c in bar.chords] for bar in score.sections[0].bars] == [
        [("C#m", False)], [("G", False)], [("C#m", True)],
    ]


def test_score_sections_use_aligned_starts_and_record_shift():
    score = _mid_phrase_score()
    verse, chorus = score.sections
    assert (verse.label, verse.bars[0].index, verse.bars[-1].index, verse.shifted) == (
        "Verse", 0, 8, 0,
    )
    assert (chorus.label, chorus.bars[0].index, chorus.bars[-1].index, chorus.shifted) == (
        "Chorus", 9, 23, 1,
    )
    assert [b.chords[0].name for b in chorus.bars[:4]] == ["D", "D", "A", "A"]
    # section fields still come from the grid section's own pattern
    assert verse.pattern == ISLAND and chorus.pattern == CALYPSO
    assert (chorus.uncertain, chorus.bar_repeat, chorus.inherited_from) == (True, 0.8, 0)
    assert verse.bars[-1].chords[0].slots == ISLAND  # bar 8 now plays the verse pattern


def test_in_phase_sections_are_not_shifted():
    score = _score(3, [(0, 1, "C"), (1, 2, "G"), (2, 3, "C")], {"C": C, "G": G})
    assert [s.shifted for s in score.sections] == [0]


def test_every_bar_still_has_slots_per_bar_slots_after_alignment():
    score = _mid_phrase_score()
    indices = [bar.index for section in score.sections for bar in section.bars]
    assert indices == list(range(24))
    for section in score.sections:
        for bar in section.bars:
            slots = [s for c in bar.chords for s in c.slots]
            assert len(slots) == score.slots_per_bar
            assert slots == section.pattern
            assert bar.chords[0].start_slot == 0


def test_score_json_without_new_fields_still_loads():
    score = _mid_phrase_score()
    data = score.model_dump(by_alias=True)
    for section in data["sections"]:
        del section["shifted"]
        for bar in section["bars"]:
            for chord in bar["chords"]:
                del chord["filled"], chord["passing"]
    for diagram in data["chord_diagrams"]:
        del diagram["passing"]
    loaded = type(score).model_validate(data)
    assert loaded.schema_version == 1
    assert [s.shifted for s in loaded.sections] == [0, 0]
    assert not any(
        c.filled or c.passing for s in loaded.sections for b in s.bars for c in b.chords
    )
    assert not any(d.passing for d in loaded.chord_diagrams)


def _verse_chorus_score(specs):
    """24 bars, Verse 0-8 and Chorus 8-24; specs are (start, end, label, passing) in bars."""
    shapes = {"D": C, "A": G, "F": F}
    evs = [_ev(s, e, lab) for s, e, lab, _ in specs]
    arranged = [
        ArrangedChord(event=i, name=lab, shape=shapes[lab], passing=passing)
        for i, (_, _, lab, passing) in enumerate(specs)
    ]
    grid = _grid(24).model_copy(
        update={
            "sections": [
                Section(label="Verse", start_bar=0, end_bar=8, confidence=0.5),
                Section(label="Chorus", start_bar=8, end_bar=24, confidence=0.5),
            ]
        }
    )
    return build_score(
        _source(), grid,
        Chords(key=Key(tonic="D", mode="major", confidence=0.9), events=evs),
        _two_section_strums(),
        Arrangement(capo=0, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        UKULELE_TUNING, "Ukulele",
    )


def test_passing_chords_do_not_count_as_phrase_changes():
    # chords change every two bars from bar 9, so the Chorus is one bar out of phase; a
    # passing F sits mid-bar on the first bar of each pair. Counting it as the bar's last
    # chord would add a change on the second bar of the pair (an even offset) and spoil
    # the odd-offset share, so the Chorus would not shift.
    bounds = [0, 2, 4, 6, 9, 11, 13, 15, 17, 19, 21, 23, 24]
    specs = []
    for a, b, lab in zip(bounds, bounds[1:], ["D", "A"] * 6):
        if a >= 9 and b - a == 2 and a < 21:
            specs += [(a, a + 0.5, lab, False), (a + 0.5, a + 1, "F", True), (a + 1, b, lab, False)]
        else:
            specs.append((a, b, lab, False))
    score = _verse_chorus_score(specs)
    chorus = score.sections[1]
    assert (chorus.bars[0].index, chorus.shifted) == (9, 1)
    assert [c.name for c in chorus.bars[0].chords] == ["D", "F"]
    assert [b.chords[0].name for b in chorus.bars[:4]] == ["D", "D", "A", "A"]


def test_mid_bar_change_followed_by_a_bar_holding_it_is_not_a_phrase_change():
    # every even-offset Chorus bar changes chord half way and the next bar holds the new
    # chord, so no bar starts on a chord other than the previous bar's last one. Comparing
    # first chords instead would flag every odd-offset bar and shift the Chorus.
    specs = [(0, 8, "D", False)]
    for k in range(8):
        first, last = ("D", "A") if k % 2 == 0 else ("A", "D")
        bar = 8 + 2 * k
        specs += [(bar, bar + 0.5, first, False), (bar + 0.5, bar + 2, last, False)]
    score = _verse_chorus_score(specs)
    chorus = score.sections[1]
    assert (chorus.bars[0].index, chorus.shifted) == (8, 0)
    assert [c.name for c in chorus.bars[0].chords] == ["D", "A"]


def _trailing_score(n_bars, evs):
    arranged = [
        ArrangedChord(event=i, name=ev.label, shape=C) for i, ev in enumerate(evs) if ev.label != "N"
    ]
    return _build_events(n_bars, evs, arranged)


def test_score_drops_trailing_bars_and_records_count():
    score = _trailing_score(8, [_ev(0, 6, "C"), _ev(6, 8, "N")])
    assert [b.index for b in score.sections[0].bars] == list(range(6))
    assert score.trailing_bars_dropped == 2
    assert not any(c.name == "N.C." for b in score.sections[0].bars for c in b.chords)


def test_score_drops_nothing_when_the_music_runs_to_the_end():
    score = _trailing_score(8, [_ev(0, 8, "C")])
    assert len(score.sections[0].bars) == 8
    assert score.trailing_bars_dropped == 0


def test_score_drops_nothing_for_an_all_n_song():
    score = _trailing_score(4, [_ev(0, 4, "N")])
    assert len(score.sections[0].bars) == 4
    assert score.trailing_bars_dropped == 0


def test_score_trailing_drop_is_capped_to_leave_the_last_section_a_bar():
    grid = _grid(10).model_copy(
        update={
            "sections": [
                Section(label="Verse", start_bar=0, end_bar=8, confidence=0.5),
                Section(label="Outro", start_bar=8, end_bar=10, confidence=0.5),
            ]
        }
    )
    evs = [_ev(0, 5, "C"), _ev(5, 10, "N")]
    score = build_score(
        _source(), grid,
        Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        _two_section_strums(),
        Arrangement(
            capo=0, transpose=0, tier="easy",
            chords=[ArrangedChord(event=0, name="C", shape=C)], substitutions=[],
        ),
        UKULELE_TUNING, "Ukulele",
    )
    assert [len(s.bars) for s in score.sections] == [8, 1]
    assert score.trailing_bars_dropped == 1


def test_score_trailing_drop_is_clamped_again_after_a_phrase_shift(monkeypatch):
    # the drop is capped on the grid's outro (6 bars, so at most 5); a phrase shift then starts
    # the outro a bar later, and the second clamp still leaves it one bar
    monkeypatch.setattr(score_builder, "aligned_starts", lambda ranges, changes: [(0, 7, 0), (7, 12, 1)])
    grid = _grid(12).model_copy(
        update={
            "sections": [
                Section(label="Verse", start_bar=0, end_bar=6, confidence=0.5),
                Section(label="Outro", start_bar=6, end_bar=12, confidence=0.5),
            ]
        }
    )
    evs = [_ev(0, 7, "C"), _ev(7, 12, "N")]
    score = build_score(
        _source(), grid,
        Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        _two_section_strums(),
        Arrangement(
            capo=0, transpose=0, tier="easy",
            chords=[ArrangedChord(event=0, name="C", shape=C)], substitutions=[],
        ),
        UKULELE_TUNING, "Ukulele",
    )
    verse, outro = score.sections
    assert [b.index for b in verse.bars] == list(range(7))
    assert [b.index for b in outro.bars] == [7]  # without the second clamp the outro would be empty
    assert score.trailing_bars_dropped == 4


def test_score_json_without_trailing_field_loads():
    score = _trailing_score(8, [_ev(0, 6, "C"), _ev(6, 8, "N")])
    data = score.model_dump(by_alias=True)
    del data["trailing_bars_dropped"]
    loaded = type(score).model_validate(data)
    assert loaded.schema_version == 1
    assert loaded.trailing_bars_dropped == 0


def test_score_uses_refined_labels():
    # the grid names the once-only middle section a verse; its chords are heard nowhere
    # else, so the score names it the bridge, and the grid keeps its own label
    labels = ["C", "G"] * 4 + ["F", "D"] * 4 + ["C", "G"] * 4
    evs = [_ev(i, i + 1, lab) for i, lab in enumerate(labels)]
    arranged = [ArrangedChord(event=i, name=ev.label, shape=C) for i, ev in enumerate(evs)]
    grid = _grid(24).model_copy(
        update={
            "sections": [
                Section(label="verse", start_bar=0, end_bar=8, confidence=0.5),
                Section(label="verse", start_bar=8, end_bar=16, confidence=0.5),
                Section(label="chorus", start_bar=16, end_bar=24, confidence=0.5),
            ]
        }
    )
    patterns = [
        SectionPattern(
            section=k, slots=list(ISLAND), confidence=0.8, bar_repeat=0.9, uncertain=False,
            no_instrument=False, inherited_from=None,
        )
        for k in range(3)
    ]
    strums = Strums(
        slots_per_bar=8, source="other_stem", source_ratio=0.6, grid_fit=0.9,
        uncertain=False, patterns=patterns, bar_onsets=[],
    )
    score = build_score(
        _source(), grid, Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        strums, Arrangement(capo=0, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        UKULELE_TUNING, "Ukulele",
    )
    assert [s.label for s in score.sections] == ["verse", "bridge", "chorus"]
    assert [s.label for s in grid.sections] == ["verse", "verse", "chorus"]


CSHARP = Shape(frets=[1, 1, 1, 4], fingers=[1, 1, 1, 4], base_fret=1, barres=[1])
FSHARP = Shape(frets=[3, 1, 2, 4], fingers=[3, 1, 2, 4], base_fret=1, barres=[])


def _capo_score(capo, alternative):
    evs = [
        ChordEvent(bar=i, beat=0, start=i * BAR, end=(i + 1) * BAR, label="C", triad="C", confidence=0.9)
        for i in range(4)
    ]
    shapes = [C, G, C, F]
    arranged = [
        ArrangedChord(event=i, name=name, shape=shape)
        for i, (name, shape) in enumerate(zip(["C", "G", "C", "F"], shapes))
    ]
    return build_score(
        _source(), _grid(4), Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        _strums(),
        Arrangement(
            capo=capo, transpose=-capo, tier="easy", chords=arranged, substitutions=[],
            no_capo_alternative=alternative,
        ),
        UKULELE_TUNING, "Ukulele",
    )


def test_score_alternative_diagrams_only_under_capo():
    alternative = [
        ArrangedChord(event=0, name="C#", shape=CSHARP),
        ArrangedChord(event=1, name="F#", shape=FSHARP),
        ArrangedChord(event=2, name="C#", shape=CSHARP),  # the same shape again: one diagram
        ArrangedChord(event=3, name="F#", shape=FSHARP, passing=True),
    ]
    score = _capo_score(3, alternative)
    assert [(d.name, d.shape) for d in score.alternative_diagrams] == [("C#", CSHARP), ("F#", FSHARP)]
    assert [d.passing for d in score.alternative_diagrams] == [False, False]  # one full use wins
    assert [d.name for d in score.chord_diagrams] == ["C", "G", "F"]  # the played diagrams are untouched
    assert _capo_score(0, alternative).alternative_diagrams == []
    assert _capo_score(3, []).alternative_diagrams == []


def test_score_bar_struck_flag_from_bar_onsets():
    strums = _strums()
    strums = strums.model_copy(
        update={"bar_onsets": [list("--------"), list("D-------"), list("-------U")]}
    )
    evs = [
        ChordEvent(bar=0, beat=0, start=0.0, end=4 * BAR, label="C", triad="C", confidence=0.9)
    ]
    score = build_score(
        _source(), _grid(4), Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        strums,
        Arrangement(
            capo=0, transpose=0, tier="easy", substitutions=[],
            chords=[ArrangedChord(event=0, name="C", shape=C)],
        ),
        UKULELE_TUNING, "Ukulele",
    )
    # bar 3 has no bar_onsets entry at all: not struck
    assert [b.struck for b in score.sections[0].bars] == [False, True, True, False]
    assert ScoreBar(index=0, chords=[]).struck is False
