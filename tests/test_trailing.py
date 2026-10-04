from __future__ import annotations

from youkelele.music.trailing import trailing_silent_bars
from youkelele.schemas import Bar, ChordEvent, Chords, Key

BAR = 2.0


def _bars(n: int) -> list[Bar]:
    return [Bar(index=i, start=i * BAR, end=(i + 1) * BAR, beats=list(range(4 * i, 4 * i + 4))) for i in range(n)]


def _chords(*specs: tuple[float, float, str, bool]) -> Chords:
    """specs are (start, end in bars, label, filled)."""
    events = [
        ChordEvent(
            bar=int(s), beat=0, start=s * BAR, end=e * BAR, label=lab, triad=lab, confidence=0.9, filled=f
        )
        for s, e, lab, f in specs
    ]
    return Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=events)


def test_trailing_silent_bars_counts_bars_after_last_chord():
    # the last chord ends where bar 110 starts, in a 113-bar song
    chords = _chords((0, 100, "C", False), (100, 110, "G", False), (110, 113, "N", False))
    assert trailing_silent_bars(chords, _bars(113), cap=113) == 3


def test_trailing_silent_bars_counts_filled_as_chords():
    # a filled event is a chord (it carries a real label), so the bars it covers are music
    chords = _chords((0, 100, "C", False), (100, 110, "C", True), (110, 113, "N", False))
    assert trailing_silent_bars(chords, _bars(113), cap=113) == 3
    chords = _chords((0, 100, "C", False), (100, 113, "C", True))
    assert trailing_silent_bars(chords, _bars(113), cap=113) == 0


def test_trailing_silent_bars_zero_when_song_is_all_n():
    chords = _chords((0, 10, "N", False))
    assert trailing_silent_bars(chords, _bars(10), cap=10) == 0
    assert trailing_silent_bars(_chords(), _bars(10), cap=10) == 0


def test_trailing_silent_bars_capped_to_keep_one_bar_in_the_section():
    chords = _chords((0, 6, "C", False), (6, 10, "N", False))
    assert trailing_silent_bars(chords, _bars(10), cap=10) == 4
    assert trailing_silent_bars(chords, _bars(10), cap=3) == 2
    assert trailing_silent_bars(chords, _bars(10), cap=1) == 0


def test_trailing_silent_bars_ignores_a_chord_ending_inside_a_bar():
    # a chord that ends part-way through bar 6 keeps bar 6; only bars 7 onwards are silent
    chords = _chords((0, 6.5, "C", False))
    assert trailing_silent_bars(chords, _bars(10), cap=10) == 3
