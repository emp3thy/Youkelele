from __future__ import annotations

import re

from youkelele.music.alphatex import score_to_alphatex
from youkelele.schemas import (
    ChordDiagram,
    Instrument,
    Meter,
    Score,
    ScoreBar,
    ScoreChord,
    ScoreSection,
    Shape,
)

ISLAND = list("D-DU-UDU")
C = Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[])
G = Shape(frets=[0, 2, 3, 2], fingers=[0, 1, 3, 2], base_fret=1, barres=[])


def _score(sections, diagrams, slots_per_bar=8, meter=(4, 4), capo=0, artist="Band", title="Song"):
    return Score(
        instrument=Instrument(name="Ukulele", strings=4, tuning=["G4", "C4", "E4", "A4"], capo=capo),
        title=title,
        artist=artist,
        key="C major",
        bpm=100.4,
        meter=Meter(numerator=meter[0], denominator=meter[1]),
        tier="easy",
        slots_per_bar=slots_per_bar,
        strum_source="other_stem",
        strums_uncertain=False,
        chord_diagrams=diagrams,
        sections=sections,
    )


def _section(bars, pattern=ISLAND, label="Verse 1"):
    return ScoreSection(
        label=label, pattern=pattern, uncertain=False, bars=bars, bar_repeat=1.0, no_instrument=False
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _one_bar(name, diagram, slots):
    return ScoreBar(
        index=0, chords=[ScoreChord(name=name, diagram=diagram, start_slot=0, slots=list(slots))]
    )


def test_alphatex_matches_verified_two_bar_example():
    bar1 = ScoreBar(
        index=0,
        chords=[
            ScoreChord(name="C", diagram=0, start_slot=0, slots=list("D-D")),
            ScoreChord(name="G", diagram=1, start_slot=3, slots=list("U-UDU")),
        ],
    )
    bar2 = ScoreBar(
        index=1, chords=[ScoreChord(name="G", diagram=1, start_slot=0, slots=list("xxDU-UDU"))]
    )
    score = _score(
        [_section([bar1, bar2])],
        [ChordDiagram(name="C", shape=C), ChordDiagram(name="G", shape=G)],
    )
    expected = r"""
\title "Song"
\artist "Band"
\tempo 100
\hideDynamics
.
\track "Ukulele"
\staff {slash}
\tuning (A4 E4 C4 G4) { hide }
\chord ("C" 3 0 0 0) {showdiagram false}
\chord ("G" 2 3 2 0) {showdiagram false}
\ts 4 4
\section "Verse 1"
:8 (3.1 0.2 0.3 0.4){bd ch "C" lyrics "D"} r{lyrics "-"} (3.1 0.2 0.3 0.4){bd lyrics "D"} (2.1 3.2 2.3 0.4){bu ch "G" lyrics "U"} r{lyrics "-"} (2.1 3.2 2.3 0.4){bu lyrics "U"} (2.1 3.2 2.3 0.4){bd lyrics "D"} (2.1 3.2 2.3 0.4){bu lyrics "U"} |
:8 (){ds ch "G" lyrics "x"} (){ds lyrics "x"} (2.1 3.2 2.3 0.4){bd lyrics "D"} (2.1 3.2 2.3 0.4){bu lyrics "U"} r{lyrics "-"} (2.1 3.2 2.3 0.4){bu lyrics "U"} (2.1 3.2 2.3 0.4){bd lyrics "D"} (2.1 3.2 2.3 0.4){bu lyrics "U"} |
"""
    assert _norm(score_to_alphatex(score)) == _norm(expected)


def test_alphatex_uses_per_beat_lyrics_never_staff_lyrics():
    text = score_to_alphatex(
        _score([_section([_one_bar("C", 0, ISLAND)])], [ChordDiagram(name="C", shape=C)])
    )
    assert not any(line.lstrip().startswith("\\lyrics") for line in text.splitlines())
    (beat_line,) = [line for line in text.splitlines() if line.startswith(":8")]
    assert beat_line.count('lyrics "') == 8


def test_alphatex_3_4_uses_ts_3_4_and_six_slots():
    score = _score(
        [_section([_one_bar("C", 0, "D-DUDU")], pattern=list("D-DUDU"))],
        [ChordDiagram(name="C", shape=C)],
        slots_per_bar=6,
        meter=(3, 4),
    )
    text = score_to_alphatex(score)
    assert "\\ts 3 4" in text
    (beat_line,) = [line for line in text.splitlines() if line.startswith(":8")]
    assert beat_line.count('lyrics "') == 6


def test_alphatex_sixteen_slots_use_sixteenth_duration():
    slots = list("D-DU-UDU" * 2)
    score = _score(
        [_section([_one_bar("C", 0, slots)], pattern=slots)],
        [ChordDiagram(name="C", shape=C)],
        slots_per_bar=16,
    )
    assert any(line.startswith(":16 ") for line in score_to_alphatex(score).splitlines())


def test_alphatex_omits_muted_strings_and_uses_absolute_firstfret():
    muted = Shape(frets=[-1, 2, 1, 0], fingers=[0, 2, 1, 0], base_fret=1, barres=[])
    high = Shape(frets=[3, 2, 1, 1], fingers=[3, 2, 1, 1], base_fret=3, barres=[1])
    bar = ScoreBar(
        index=0,
        chords=[
            ScoreChord(name="Fm", diagram=0, start_slot=0, slots=list("D-DU")),
            ScoreChord(name="C", diagram=1, start_slot=4, slots=list("D-DU")),
        ],
    )
    diagrams = [ChordDiagram(name="Fm", shape=muted), ChordDiagram(name="C", shape=high)]
    text = score_to_alphatex(_score([_section([bar])], diagrams))
    assert '(0.1 1.2 2.3){bd ch "Fm" lyrics "D"}' in text
    assert '\\chord ("Fm" 0 1 2 x) {showdiagram false}' in text
    assert '\\chord ("C" 3 3 4 5) {showdiagram false firstfret 3 barre 3}' in text
    assert '(3.1 3.2 4.3 5.4){bd ch "C" lyrics "D"}' in text


def test_alphatex_capo_artist_and_quote_escaping():
    score = _score(
        [_section([_one_bar("C", 0, ISLAND)])],
        [ChordDiagram(name="C", shape=C)],
        capo=2,
        artist=None,
        title='Say "Hi"',
    )
    text = score_to_alphatex(score)
    assert '\\title "Say \\"Hi\\""' in text
    assert "\\artist" not in text
    assert "\\capo 2" in text
