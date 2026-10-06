"""Mapping riff notes onto ukulele strings and frets.

Three rules of the instrument, none of them about a song: a whole-octave shift into the
comfortable range, any outlier moved by octaves, then the lowest fret among the strings.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from youkelele.music.riff_line import NoteBar
from youkelele.schemas import TabNote

RANGE_LO, RANGE_HI = 60, 81  # open C to the twelfth fret of A on re-entrant G C E A

_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NOTE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")


def _midi(name: str) -> int:
    m = _NOTE.match(name.strip())
    if not m:
        raise ValueError(f"not a pitch name: {name!r}")
    letter, accidental, octave = m.groups()
    shift = {"#": 1, "b": -1, "": 0}[accidental]
    return 12 * (int(octave) + 1) + _SEMITONE[letter.upper()] + shift


def tuning_midis(pitches: Sequence[str]) -> list[int]:
    return [_midi(p) for p in pitches]


def octave_shift(midis: Sequence[int]) -> int:
    """The whole-octave shift in [-2, 2] that puts most notes in range; ties to the smaller, then positive."""

    def inside(s: int) -> int:
        return sum(1 for m in midis if RANGE_LO <= m + 12 * s <= RANGE_HI)

    return min(range(-2, 3), key=lambda s: (-inside(s), abs(s), -s))


def into_range(midi: int) -> int:
    """Moved by whole octaves until inside the range."""
    m = midi
    while m < RANGE_LO:
        m += 12
    while m > RANGE_HI:
        m -= 12
    if not RANGE_LO <= m <= RANGE_HI:
        raise ValueError(f"midi {midi} cannot be moved into {RANGE_LO}..{RANGE_HI}")
    return m


def string_fret(midi: int, tuning: Sequence[int]) -> tuple[int, int]:
    """The string with the lowest non-negative fret; ties to the lower-numbered string."""
    options = [(midi - open_, i) for i, open_ in enumerate(tuning) if midi >= open_]
    if not options:
        raise ValueError(f"midi {midi} is below every open string")
    fret, string = min(options)
    return string, fret


def to_tab(notes: NoteBar, rings: bool, tuning: Sequence[int]) -> tuple[list[TabNote], int]:
    """(tab, shift): the notes shifted, moved into range, and placed on strings and frets."""
    shift = octave_shift([n for n in notes if n is not None])
    tab: list[TabNote] = []
    for slot, n in enumerate(notes):
        if n is None:
            continue
        midi = into_range(n + 12 * shift)
        string, fret = string_fret(midi, tuning)
        tab.append(TabNote(slot=slot, midi=midi, string=string, fret=fret, rings=rings))
    return tab, shift
