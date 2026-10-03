from __future__ import annotations

from datetime import datetime

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


def _strums(slots=ISLAND) -> Strums:
    pattern = SectionPattern(
        section=0, slots=list(slots), confidence=0.8, bar_repeat=0.9, uncertain=False,
        no_instrument=False, inherited_from=None,
    )
    return Strums(
        slots_per_bar=len(slots), source="other_stem", source_ratio=0.6, grid_fit=0.9,
        uncertain=True, patterns=[pattern], bar_onsets=[],
    )


def _score(n_bars, events, shapes, capo=0):
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
        _strums(),
        Arrangement(capo=capo, transpose=0, tier="easy", chords=arranged, substitutions=[]),
        UKULELE_TUNING,
        "Ukulele",
    )


def _chords(score, bar):
    return score.sections[0].bars[bar].chords


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
    score = _score(2, [(0, 1, "C"), (1, 2, "N")], {"C": C, "N": None})
    (nc,) = _chords(score, 1)
    assert (nc.name, nc.diagram, nc.start_slot, nc.slots) == ("N.C.", -1, 0, ISLAND)
