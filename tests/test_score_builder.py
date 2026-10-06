from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from youkelele.jsonio import ArtifactError
from youkelele.music import score_builder
from youkelele.music.alphatex import score_to_alphatex
from youkelele.music.score_builder import _labels, build_score, check_strums_match_grid
from youkelele.profiles.ukulele import UKULELE_TUNING
from youkelele.schemas import (
    ArrangedChord,
    Arrangement,
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
    ScoreBar,
    Section,
    SectionPattern,
    Shape,
    SourceInfo,
    Stroke,
    Strums,
    TabNote,
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
        Riffs(),
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
        Riffs(), UKULELE_TUNING, "Ukulele",
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
            Riffs(), UKULELE_TUNING, "Ukulele",
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
        Riffs(), UKULELE_TUNING, "Ukulele",
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


def test_inherited_from_is_always_none_in_the_score_section():
    # spec 4.5: no section inherits a neighbour's pattern from 1.6, even when a 1.5 file says so
    strums = _strums()
    inherited = strums.patterns[0].model_copy(update={"section": 1, "inherited_from": 0})
    strums = strums.model_copy(update={"patterns": [strums.patterns[0], inherited]})
    score = _build(_split(_grid(2)), strums)
    assert [s.inherited_from for s in score.sections] == [None, None]


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
        Riffs(), UKULELE_TUNING, "Ukulele",
    )


def _build_events(n_bars, evs, arranged):
    return build_score(
        _source(), _grid(n_bars),
        Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=evs),
        _strums(),
        Arrangement(capo=0, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        Riffs(), UKULELE_TUNING, "Ukulele",
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
    assert (chorus.uncertain, chorus.bar_repeat, chorus.inherited_from) == (True, 0.8, None)
    # bar 8 moved into the verse but keeps its own record: the chorus pattern its grid section plays
    assert verse.bars[-1].chords[0].slots == CALYPSO


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
            # each bar plays its own grid section's pattern, wherever alignment placed it
            assert slots == (ISLAND if bar.index < 8 else CALYPSO)
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
    data["schema"] = 1  # as a file written before 1.6 says
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
        Riffs(), UKULELE_TUNING, "Ukulele",
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
        Riffs(), UKULELE_TUNING, "Ukulele",
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
        Riffs(), UKULELE_TUNING, "Ukulele",
    )
    verse, outro = score.sections
    assert [b.index for b in verse.bars] == list(range(7))
    assert [b.index for b in outro.bars] == [7]  # without the second clamp the outro would be empty
    assert score.trailing_bars_dropped == 4


def test_score_json_without_trailing_field_loads():
    score = _trailing_score(8, [_ev(0, 6, "C"), _ev(6, 8, "N")])
    data = score.model_dump(by_alias=True)
    del data["trailing_bars_dropped"]
    data["schema"] = 1  # as a file written before 1.6 says
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
        Riffs(), UKULELE_TUNING, "Ukulele",
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
        Riffs(), UKULELE_TUNING, "Ukulele",
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
        Riffs(), UKULELE_TUNING, "Ukulele",
    )
    # bar 3 has no bar_onsets entry at all: not struck
    assert [b.struck for b in score.sections[0].bars] == [False, True, True, False]
    assert ScoreBar(index=0, chords=[]).struck is False


# the section plan (spec 3.3): the score follows the plan strums.json carries


def _pattern(section=0, riff=False) -> SectionPattern:
    return SectionPattern(
        section=section, slots=list(ISLAND), confidence=0.8, bar_repeat=0.9, uncertain=False,
        no_instrument=False, inherited_from=None, riff=riff,
    )


def _strums_with_plan(plan, patterns) -> Strums:
    return Strums(
        slots_per_bar=8, source="other_stem", source_ratio=0.6, grid_fit=0.9,
        uncertain=False, patterns=patterns, bar_onsets=[], plan=plan,
    )


def _sectioned(n_bars, bounds, labels=None) -> Grid:
    """A grid of n_bars with sections at the given (start, end) bars, labelled verse by default."""
    labels = labels or ["verse"] * len(bounds)
    return _grid(n_bars).model_copy(
        update={
            "sections": [
                Section(label=label, start_bar=a, end_bar=b, confidence=0.5)
                for (a, b), label in zip(bounds, labels, strict=True)
            ]
        }
    )


_THREE = [(0, 8), (8, 14), (14, 16)]  # a verse, then a chorus whose last two bars are a fragment
_THREE_LABELS = ["verse", "chorus", "chorus"]
_CHORDS = Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=[])
_ARRANGEMENT = Arrangement(capo=0, transpose=0, tier="easy", chords=[], substitutions=[])


def _plan_score(grid, chords, strums, arrangement=_ARRANGEMENT):
    return build_score(_source(), grid, chords, strums, arrangement, Riffs(), UKULELE_TUNING, "Ukulele")


def test_build_score_follows_the_plan_and_records_members():
    # a six-bar verse fragment after a ten-bar verse on the same (no) chords: the plan merges them
    grid_two_sections = _sectioned(16, [(0, 10), (10, 16)])
    strums = _strums_with_plan(
        [PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])], patterns=[_pattern()]
    )
    score = _plan_score(grid_two_sections, _CHORDS, strums)
    assert len(score.sections) == 1 and score.sections[0].members == [0, 1]
    assert [b.index for b in score.sections[0].bars] == list(range(16))
    assert score.sections[0].label == "verse"


def test_build_score_takes_the_label_from_the_plan():
    # grid.json calls all three verse; the middle one plays chords no other plays, so the plan
    # calls it the bridge, and the score follows the plan
    grid = _sectioned(24, [(0, 8), (8, 16), (16, 24)])
    chords = Chords(
        key=Key(tonic="C", mode="major", confidence=0.9),
        events=[_ev(0, 8, "C"), _ev(8, 16, "F#"), _ev(16, 24, "C")],
    )
    plan = [
        PlannedSection(start_bar=0, end_bar=8, label="verse", members=[0]),
        PlannedSection(start_bar=8, end_bar=16, label="bridge", members=[1]),
        PlannedSection(start_bar=16, end_bar=24, label="verse", members=[2]),
    ]
    score = _plan_score(grid, chords, _strums_with_plan(plan, [_pattern(0), _pattern(1), _pattern(2)]))
    assert [s.label for s in score.sections] == ["verse", "bridge", "verse"]
    assert [s.members for s in score.sections] == [[0], [1], [2]]


def _fixture(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


def test_build_score_without_a_plan_uses_one_section_per_grid_section():
    strums_14 = Strums.model_validate_json(_fixture("v14/strums.json"))
    chords_for_fixture = Chords.model_validate_json(_fixture("v14/chords.json"))
    assert strums_14.plan == []
    n_bars, n_sections = len(strums_14.bar_onsets), len(strums_14.patterns)
    cuts = [round(k * n_bars / n_sections) for k in range(n_sections + 1)]
    grid_for_fixture = _sectioned(n_bars, list(zip(cuts, cuts[1:])))
    score = _plan_score(grid_for_fixture, chords_for_fixture, strums_14)
    assert [s.members for s in score.sections] == [[i] for i in range(len(grid_for_fixture.sections))]
    assert not any(s.riff for s in score.sections)


def test_check_strums_match_grid_compares_against_the_plan():
    grid_two_sections = _sectioned(16, [(0, 8), (8, 16)])
    strums = _strums_with_plan(
        [PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])],
        patterns=[_pattern(0), _pattern(1)],
    )
    with pytest.raises(ValueError, match="re-run from strums"):
        check_strums_match_grid(grid_two_sections, strums, _CHORDS)


def test_check_strums_match_grid_rejects_a_plan_span_outside_the_grid():
    grid = _sectioned(16, [(0, 8), (8, 16)])
    strums = _strums_with_plan(
        [PlannedSection(start_bar=0, end_bar=20, label="verse", members=[0, 1])], patterns=[_pattern()]
    )
    with pytest.raises(ValueError, match="re-run from strums"):
        check_strums_match_grid(grid, strums, _CHORDS)


def test_riff_flag_reaches_the_score_section():
    grid_one_section = _grid(4)
    strums = _strums_with_plan([], patterns=[_pattern(riff=True)])
    score = _plan_score(grid_one_section, _CHORDS, strums)
    assert score.sections[0].riff
    assert not _plan_score(grid_one_section, _CHORDS, _strums()).sections[0].riff


def test_trailing_drop_falls_on_the_last_planned_section_capped_by_the_grid_section():
    # the grid's last section (14 to 16) is a fragment merged into the planned chorus; the drop
    # is capped by that grid section's length (2 bars, so at most 1), as the strums stage caps it
    grid = _sectioned(16, _THREE, _THREE_LABELS)
    plan = [
        PlannedSection(start_bar=0, end_bar=8, label="verse", members=[0]),
        PlannedSection(start_bar=8, end_bar=16, label="chorus", members=[1, 2]),
    ]
    chords = Chords(
        key=Key(tonic="C", mode="major", confidence=0.9), events=[_ev(0, 13, "C"), _ev(13, 16, "N")]
    )
    arrangement = Arrangement(
        capo=0, transpose=0, tier="easy",
        chords=[ArrangedChord(event=0, name="C", shape=C)], substitutions=[],
    )
    score = _plan_score(grid, chords, _strums_with_plan(plan, [_pattern(0), _pattern(1)]), arrangement)
    assert [b.index for b in score.sections[1].bars] == list(range(8, 15))
    assert score.trailing_bars_dropped == 1


def _three_section_plan_strums() -> Strums:
    """The plan `section_plan` makes from `_THREE`: the two-bar chorus joins the six-bar one."""
    plan = [
        PlannedSection(start_bar=0, end_bar=8, label="verse", members=[0]),
        PlannedSection(start_bar=8, end_bar=16, label="chorus", members=[1, 2]),
    ]
    return _strums_with_plan(plan, [_pattern(0), _pattern(1)])


def test_check_strums_match_grid_accepts_the_grid_the_plan_was_made_from():
    grid = _sectioned(16, _THREE, _THREE_LABELS)
    check_strums_match_grid(grid, _three_section_plan_strums(), _CHORDS)


def test_check_strums_match_grid_catches_a_grid_section_split_after_strums_ran():
    # the plan was made from three grid sections; grid.json now splits the chorus at bar 11
    split = _sectioned(16, [(0, 8), (8, 11), (11, 14), (14, 16)], ["verse", "chorus", "chorus", "chorus"])
    with pytest.raises(
        ValueError,
        match=(
            r"^strums.json's section plan no longer matches grid.json and chords.json: planned section 1 is "
            r"bars 8 to 16, chorus, grid sections \[1, 2\] in strums.json but bars 8 to 16, chorus, "
            r"grid sections \[1, 2, 3\] now; re-run from strums$"
        ),
    ):
        check_strums_match_grid(split, _three_section_plan_strums(), _CHORDS)


def test_check_strums_match_grid_catches_a_moved_boundary():
    # same section count, but a boundary moved: grid section 0 now ends at bar 10
    moved = _sectioned(16, [(0, 10), (10, 14), (14, 16)], _THREE_LABELS)
    with pytest.raises(
        ValueError, match=r"planned section 0 is bars 0 to 8, verse, grid sections \[0\] in strums.json but bars "
        r"0 to 10, verse, grid sections \[0\] now; re-run from strums"
    ):
        check_strums_match_grid(moved, _three_section_plan_strums(), _CHORDS)


def test_check_strums_match_grid_catches_a_label_only_grid_edit():
    # bars and members unchanged; only the first section's label was edited in grid.json
    relabelled = _sectioned(16, _THREE, ["intro", "chorus", "chorus"])
    with pytest.raises(
        ValueError, match=r"planned section 0 is bars 0 to 8, verse, .* but bars 0 to 8, intro, .*re-run from strums"
    ):
        check_strums_match_grid(relabelled, _three_section_plan_strums(), _CHORDS)


def test_check_strums_match_grid_names_a_changed_section_count():
    # strums.json planned one verse; grid.json now has a verse and a chorus, which never merge
    unmerged = _sectioned(16, [(0, 8), (8, 16)], ["verse", "chorus"])
    one = _strums_with_plan(
        [PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])], [_pattern(0)]
    )
    with pytest.raises(ValueError, match=r"strums.json plans 1 sections but grid.json and chords.json give 2"):
        check_strums_match_grid(unmerged, one, _CHORDS)


def test_plan_pattern_count_mismatch_names_the_planned_sections():
    strums = _three_section_plan_strums()
    strums = strums.model_copy(update={"patterns": strums.patterns[:1]})
    with pytest.raises(ValueError) as e:
        check_strums_match_grid(_sectioned(16, _THREE, _THREE_LABELS), strums, _CHORDS)
    assert str(e.value) == "strums.json has 1 patterns for 2 planned sections in strums.json; re-run from strums"


# version 1.6: every bar carries its own strokes, grey flag and tab; each section a state phrase


def _bars(*runs) -> list[BarStrums]:
    """BarStrums from bar 0 on; each run is (bars, pattern, member, rings, uncertain, riff[, rests]).

    A bar's strokes are its pattern's non-rest cells, each carrying the run's ring flag. A run
    with rests True is resting bars: no strokes and an all-rest pattern.
    """
    records: list[BarStrums] = []
    for count, pattern, member, rings, uncertain, riff, *rest in runs:
        rests = bool(rest and rest[0])
        if rests:
            pattern = "-" * len(pattern)
        for _ in range(count):
            strokes = [Stroke(slot=j, kind=c, rings=rings) for j, c in enumerate(pattern) if c != "-"]
            records.append(
                BarStrums(
                    index=len(records), member=member, strokes=strokes, pattern=list(pattern),
                    uncertain=uncertain, riff=riff, rings=rings, rests=rests,
                )
            )
    return records


_C_CHORDS = Chords(
    key=Key(tonic="C", mode="major", confidence=0.9), events=[_ev(i, i + 1, "C") for i in range(6)]
)
_C_ARRANGEMENT = Arrangement(
    capo=0, transpose=0, tier="easy", chords=[ArrangedChord(event=i, name="C", shape=C) for i in range(6)],
    substitutions=[],
)
_FOUR_TWO = [(0, 4), (4, 6)]  # a four-bar verse and a two-bar fragment the plan merges into it


def _merged_strums(bars: list[BarStrums], pattern: SectionPattern) -> Strums:
    plan = [PlannedSection(start_bar=0, end_bar=6, label="verse", members=[0, 1])]
    return _strums_with_plan(plan, [pattern]).model_copy(update={"bars": bars})


def _riff_strums(n_bars: int, riff: bool, unit: int = 1) -> Strums:
    """One grid section, one planned section of one member, every bar flagged riff."""
    plan = [PlannedSection(start_bar=0, end_bar=n_bars, label="Verse", members=[0])]
    pattern = _pattern(riff=riff).model_copy(update={"unit": unit})
    bars = _bars((n_bars, "D-D-D-D-", 0, True, False, riff))
    return _strums_with_plan(plan, [pattern]).model_copy(update={"bars": bars})


def _riff_section(start=0, end=4, unit=1, notes=((0, 0), (2, 2)), printable=True, section=0, shift=1):
    """notes: (slot, fret) on the C string (diagram string 1)."""
    return RiffSection(
        section=section, start_bar=start, end_bar=end, unit=unit, onsets=[],
        riff=[TabNote(slot=s, midi=60 + f, string=1, fret=f) for s, f in notes] if printable else [],
        agreement=0.8, support=0.9, named_share=0.9, candidate="medoid",
        octave_shift=shift if printable else 0, printable=printable,
        reason=None if printable else "agreement 0.40 < 0.60",
    )


def _riff_score(n_bars, strums, riffs):
    chords = Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=[])
    return build_score(_source(), _grid(n_bars), chords, strums, _ARRANGEMENT, riffs, UKULELE_TUNING, "Ukulele")


def test_bars_carry_strokes_grey_and_state_from_strums_bars():
    section_pattern = SectionPattern(
        section=0, slots=list("D-D-D-DU"), confidence=0.8, bar_repeat=0.9, uncertain=False,
        no_instrument=False, inherited_from=None,
    )
    bars = _bars((4, "D-D-D-DU", 0, False, False, False), (2, "D-------", 1, True, True, False))
    score = build_score(
        _source(), _sectioned(6, _FOUR_TWO), _C_CHORDS, _merged_strums(bars, section_pattern),
        _C_ARRANGEMENT, Riffs(), UKULELE_TUNING, "Ukulele",
    )
    out = score.sections[0].bars
    assert [k.slot for k in out[0].strokes] == [0, 2, 4, 6, 7]
    assert [k.kind for k in out[0].strokes] == list("DDDDU")
    assert not out[0].strokes[0].rings and not out[0].grey and out[0].tab is None
    assert [k.slot for k in out[4].strokes] == [0] and out[4].strokes[0].rings and out[4].grey
    # the chord's slots are its share of the bar's own pattern
    assert out[4].chords[0].slots == list("D-------") and out[0].chords[0].slots == list("D-D-D-DU")
    assert score.sections[0].state == "" and score.sections[0].octave_shift == 0
    assert score.schema_version == 2


def test_a_bar_without_detected_strokes_takes_its_members_ring_flag():
    # a short member (rings False) with a strokeless bar: the bar prints its pattern with no
    # sustain, as the member's other bars do (spec 4.4: the flag is the member's)
    bars = _bars((4, "D-D-D-DU", 0, False, False, False))
    bars[1] = bars[1].model_copy(update={"strokes": []})
    plan = [PlannedSection(start_bar=0, end_bar=4, label="Verse", members=[0])]
    strums = _strums_with_plan(plan, [_pattern()]).model_copy(update={"bars": bars})
    score = _riff_score(4, strums, Riffs())
    assert [k.slot for k in score.sections[0].bars[1].strokes] == [0, 2, 4, 6, 7]
    assert not any(k.rings for b in score.sections[0].bars for k in b.strokes)


def test_a_strokeless_bar_of_a_ringing_member_rings():
    bars = _bars((4, "D-D-D-DU", 0, True, False, False))
    bars[2] = bars[2].model_copy(update={"strokes": []})
    plan = [PlannedSection(start_bar=0, end_bar=4, label="Verse", members=[0])]
    strums = _strums_with_plan(plan, [_pattern()]).model_copy(update={"bars": bars})
    score = _riff_score(4, strums, Riffs())
    assert all(k.rings for k in score.sections[0].bars[2].strokes)


def test_printable_riff_puts_tab_on_every_bar_and_sets_state_riff():
    score = _riff_score(4, _riff_strums(4, riff=True), Riffs(sections=[_riff_section()]))
    assert all(b.tab and [n.fret for n in b.tab] == [0, 2] for b in score.sections[0].bars)
    assert all([n.slot for n in b.tab] == [0, 2] for b in score.sections[0].bars)
    assert score.sections[0].state == "riff" and score.sections[0].octave_shift == 1


def test_a_two_bar_riff_alternates_its_halves_with_slots_inside_the_bar():
    # notes at slot 1 of the first bar and slot 3 of the second (8 + 3 in the two-bar unit)
    riffs = Riffs(sections=[_riff_section(unit=2, notes=((1, 0), (11, 3)))])
    score = _riff_score(4, _riff_strums(4, riff=True, unit=2), riffs)
    tabs = [[(n.slot, n.fret) for n in b.tab] for b in score.sections[0].bars]
    assert tabs == [[(1, 0)], [(3, 3)], [(1, 0)], [(3, 3)]]


def test_a_tab_bar_is_never_grey_even_when_its_member_is_uncertain():
    strums = _riff_strums(4, riff=True)
    strums = strums.model_copy(update={"bars": [b.model_copy(update={"uncertain": True}) for b in strums.bars]})
    score = _riff_score(4, strums, Riffs(sections=[_riff_section()]))
    assert all(b.tab is not None and not b.grey for b in score.sections[0].bars)


def test_a_two_bar_riff_with_an_empty_half_keeps_an_empty_tab_of_rests():
    # every note starts in the first bar of the unit: the second bar is tab with nothing starting
    riffs = Riffs(sections=[_riff_section(unit=2, notes=((1, 0),))])
    score = build_score(
        _source(), _grid(4), _C_CHORDS, _riff_strums(4, riff=True, unit=2), _C_ARRANGEMENT, riffs,
        UKULELE_TUNING, "Ukulele",
    )
    tabs = [b.tab for b in score.sections[0].bars]
    assert [len(t) for t in tabs] == [1, 0, 1, 0] and tabs[1] == []
    assert score.sections[0].state == "riff"
    beat_lines = [line for line in score_to_alphatex(score).splitlines() if line.startswith(":8")]
    # rests on every slot under the C chord, not the C brushes of a strummed bar
    assert beat_lines[1] == (
        ':8 r{ch "C" lyrics "D"} r{lyrics "-"} r{lyrics "D"} r{lyrics "-"} '
        'r{lyrics "D"} r{lyrics "-"} r{lyrics "D"} r{lyrics "-"} |'
    )


def _merged_riff_strums() -> Strums:
    bars = _bars((4, "D-D-D-D-", 0, True, False, True), (2, "D-D-D-D-", 1, True, False, True))
    return _merged_strums(bars, _pattern(riff=True))


def _merged_riff_score(riffs: Riffs):
    return build_score(
        _source(), _sectioned(6, _FOUR_TWO), _CHORDS, _merged_riff_strums(), _ARRANGEMENT, riffs,
        UKULELE_TUNING, "Ukulele",
    )


def test_octave_shift_comes_from_a_shorter_member_when_only_it_prints_tab():
    riffs = Riffs(sections=[
        _riff_section(start=0, end=4, printable=False),
        _riff_section(start=4, end=6, shift=-1),
    ])
    section = _merged_riff_score(riffs).sections[0]
    assert section.state == "riff" and section.octave_shift == -1
    assert [b.tab is not None for b in section.bars] == [False] * 4 + [True] * 2


def test_octave_shift_prefers_the_longest_member_when_it_prints_tab():
    riffs = Riffs(sections=[_riff_section(start=0, end=4, shift=1), _riff_section(start=4, end=6, shift=-1)])
    assert _merged_riff_score(riffs).sections[0].octave_shift == 1


def test_unprintable_riff_sets_the_not_transcribed_state_and_no_tab():
    riffs = Riffs(sections=[_riff_section(printable=False)])
    score = _riff_score(4, _riff_strums(4, riff=True), riffs)
    assert score.sections[0].state == "riff heard, not transcribed"
    assert all(b.tab is None for b in score.sections[0].bars)
    assert score.sections[0].octave_shift == 0
    # its strokes still print, as a strummed section's do
    assert all([k.slot for k in b.strokes] == [0, 2, 4, 6] for b in score.sections[0].bars)


def test_state_names_an_uncertain_pattern_and_a_missing_instrument():
    plan = [PlannedSection(start_bar=0, end_bar=2, label="Verse", members=[0])]
    uncertain = _strums_with_plan(plan, [_pattern().model_copy(update={"uncertain": True})])
    assert _riff_score(2, uncertain, Riffs()).sections[0].state == "pattern uncertain"
    silent = _pattern().model_copy(update={"uncertain": True, "no_instrument": True, "riff": True})
    state = _riff_score(2, _strums_with_plan(plan, [silent]), Riffs()).sections[0].state
    assert state == "no strummed instrument detected"


def test_riff_file_that_does_not_match_the_plan_is_refused():
    grid, strums = _grid(4), _riff_strums(4, riff=True)
    with pytest.raises(ArtifactError, match="riff.json describes sections the plan does not have"):
        check_strums_match_grid(grid, strums, _CHORDS, Riffs(sections=[_riff_section(section=7)]))
    # the right section, but a span no member of it has
    with pytest.raises(ArtifactError, match="riff.json describes sections the plan does not have; re-run from strums"):
        check_strums_match_grid(grid, strums, _CHORDS, Riffs(sections=[_riff_section(end=3)]))
    check_strums_match_grid(grid, strums, _CHORDS, Riffs(sections=[_riff_section()]))


def test_riff_sections_match_member_spans_of_a_merged_section():
    plan_strums = _three_section_plan_strums()
    grid = _sectioned(16, _THREE, _THREE_LABELS)
    member = Riffs(sections=[_riff_section(section=1, start=14, end=16)])
    check_strums_match_grid(grid, plan_strums, _CHORDS, member)
    whole = Riffs(sections=[_riff_section(section=1, start=8, end=16)])
    with pytest.raises(ArtifactError, match="riff.json describes sections the plan does not have"):
        check_strums_match_grid(grid, plan_strums, _CHORDS, whole)


def test_bar_records_that_do_not_cover_the_grid_are_refused():
    strums = _riff_strums(4, riff=False)
    strums = strums.model_copy(update={"bars": strums.bars[:3]})
    with pytest.raises(ValueError, match="re-run from strums"):
        check_strums_match_grid(_grid(4), strums, _CHORDS)


# version 1.7: a resting bar prints empty and black; a riff member inside a merged section is labelled

_RIFF_CELLS = "D-D-D-D-"


def _rest_score(runs, two_members=False, riffs=None, uncertain=False, riff=False):
    """One planned section: one member over the runs' bars, or (two_members) member 0 over bars 0 to 8
    and member 1 over bars 8 to 12, which the plan merges."""
    n = sum(r[0] for r in runs)
    pattern = _pattern(riff=riff).model_copy(update={"uncertain": uncertain})
    bounds = [(0, 8), (8, 12)] if two_members else [(0, n)]
    plan = [PlannedSection(start_bar=0, end_bar=n, label="verse", members=[0, 1] if two_members else [0])]
    strums = _strums_with_plan(plan, [pattern]).model_copy(update={"bars": _bars(*runs)})
    return build_score(
        _source(), _sectioned(n, bounds), _CHORDS, strums, _ARRANGEMENT, riffs or Riffs(), UKULELE_TUNING,
        "Ukulele",
    )


_ISLAND_CELLS = "".join(ISLAND)


def test_a_resting_bar_prints_empty_strokes_in_black():
    score = _rest_score([(2, _ISLAND_CELLS, 0, True, False, False, True), (6, _ISLAND_CELLS, 0, True, False, False)])
    bar = score.sections[0].bars[0]
    assert bar.rests and bar.strokes == [] and not bar.grey and bar.tab is None
    assert score.sections[0].bars[2].strokes and not score.sections[0].bars[2].rests


def test_a_resting_bar_of_an_uncertain_member_is_still_black():
    # a member silent only through rests keeps uncertain=True; its resting bars print black all the same
    score = _rest_score([(4, _ISLAND_CELLS, 0, True, True, False, True)])
    assert all(b.rests and not b.grey for b in score.sections[0].bars)


def test_an_embedded_riff_member_gets_one_label_on_its_first_bar():
    score = _rest_score(
        [(8, _ISLAND_CELLS, 0, True, False, False), (4, _RIFF_CELLS, 1, True, False, True)], two_members=True
    )
    labels = [b.label for b in score.sections[0].bars]
    assert labels == [""] * 8 + ["riff heard", "", "", ""] and score.sections[0].state == ""


def test_a_printed_riff_member_makes_the_header_say_riff_so_no_label_prints():
    score = _rest_score(
        [(8, _ISLAND_CELLS, 0, True, False, False), (4, _RIFF_CELLS, 1, True, False, True)], two_members=True,
        riffs=Riffs(sections=[_riff_section(section=0, start=8, end=12)]),
    )
    assert score.sections[0].state == "riff" and all(b.label == "" for b in score.sections[0].bars)


def test_labels_names_a_printed_member_riff_when_the_header_does_not():
    plan = [PlannedSection(start_bar=0, end_bar=12, label="verse", members=[0, 1])]
    grid = _sectioned(12, [(0, 8), (8, 12)])
    records = {b.index: b for b in _bars((8, _ISLAND_CELLS, 0, True, False, False), (4, _RIFF_CELLS, 1, True, False, True))}
    riffs = Riffs(sections=[_riff_section(section=0, start=8, end=12)])
    assert _labels(0, plan[0], grid, records, riffs, state="pattern uncertain") == {8: "riff"}
    assert _labels(0, plan[0], grid, records, Riffs(), state="pattern uncertain") == {8: "riff heard"}
    assert _labels(0, plan[0], grid, records, riffs, state="riff") == {}


def test_no_label_when_the_header_already_says_riff():
    score = _rest_score([(8, _RIFF_CELLS, 0, True, False, True)], riff=True)
    assert score.sections[0].state == "riff heard, not transcribed"
    assert all(b.label == "" for b in score.sections[0].bars)


def test_label_prints_under_an_uncertain_header():
    score = _rest_score(
        [(8, _ISLAND_CELLS, 0, True, True, False), (4, _RIFF_CELLS, 1, True, False, True)], two_members=True,
        uncertain=True,
    )
    assert score.sections[0].state == "pattern uncertain" and score.sections[0].bars[8].label == "riff heard"
