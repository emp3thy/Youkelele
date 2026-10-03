import numpy as np
import pytest

from youkelele.music.fill import bar_chroma, bar_energy, chord_template, fill_silent_bars
from youkelele.music.triads import to_triad
from youkelele.schemas import Bar, ChordEvent


def _bars(n: int, seconds: float = 2.0) -> list[Bar]:
    return [
        Bar(index=i, start=i * seconds, end=(i + 1) * seconds, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(n)
    ]


def _event(bar: int, label: str, start: float, end: float, beat: int = 0) -> ChordEvent:
    return ChordEvent(
        bar=bar, beat=beat, start=start, end=end, label=label, triad=to_triad(label), confidence=0.9
    )


def _tpl(label: str) -> np.ndarray:
    template = chord_template(label)
    assert template is not None
    return template.astype(float)


def _song_c_g_n_g() -> list[ChordEvent]:
    return [
        _event(0, "C:maj", 0.0, 2.0),
        _event(1, "G:maj", 2.0, 4.0),
        _event(2, "N", 4.0, 6.0),
        _event(3, "G:maj", 6.0, 8.0),
    ]


def _chroma(bar2: np.ndarray) -> np.ndarray:
    return np.stack([_tpl("C:maj"), _tpl("G:maj"), bar2, _tpl("G:maj")])


def test_chord_template_c_major_marks_c_e_g():
    template = chord_template("C:maj")
    assert template is not None and template.shape == (12,)
    assert set(np.flatnonzero(template)) == {0, 4, 7}
    assert set(np.flatnonzero(chord_template("A:min7"))) == {9, 0, 4}
    assert set(np.flatnonzero(chord_template("G:maj/5"))) == {7, 11, 2}


def test_chord_template_none_for_n_x_and_bad_labels():
    assert chord_template("N") is None
    assert chord_template("X") is None
    assert chord_template("C:wibble") is None
    assert chord_template("nonsense") is None
    assert chord_template("") is None


def test_fill_fills_loud_bar_matching_a_song_chord():
    out = fill_silent_bars(_song_c_g_n_g(), _bars(4), _chroma(_tpl("C:maj")), np.ones(4))
    bar2 = [e for e in out if e.bar == 2]
    assert len(bar2) == 1
    filled = bar2[0]
    assert filled.label == "C:maj" and filled.triad == "C:maj" and filled.filled
    assert (filled.beat, filled.start, filled.end) == (0, 4.0, 6.0)
    assert filled.confidence == pytest.approx(1.0)
    assert [e.filled for e in out if e.bar != 2] == [False, False, False]
    assert [e.label for e in out] == ["C:maj", "G:maj", "C:maj", "G:maj"]


def test_fill_leaves_quiet_bar_as_n():
    energy = np.array([1.0, 1.0, 0.01, 1.0])
    out = fill_silent_bars(_song_c_g_n_g(), _bars(4), _chroma(_tpl("C:maj")), energy)
    assert [e.label for e in out] == ["C:maj", "G:maj", "N", "G:maj"]
    assert not any(e.filled for e in out)


def test_fill_leaves_ambiguous_bar_as_n():
    both = _tpl("C:maj") + _tpl("G:maj")
    out = fill_silent_bars(_song_c_g_n_g(), _bars(4), _chroma(both), np.ones(4))
    assert [e.label for e in out] == ["C:maj", "G:maj", "N", "G:maj"]
    assert not any(e.filled for e in out)


def test_fill_never_introduces_a_chord_not_in_the_song():
    out = fill_silent_bars(_song_c_g_n_g(), _bars(4), _chroma(_tpl("F:maj")), np.ones(4))
    bar2 = [e for e in out if e.bar == 2]
    assert len(bar2) == 1
    assert bar2[0].label != "F:maj"
    assert bar2[0].label in ("N", "C:maj", "G:maj")
    assert {e.label for e in out} <= {"N", "C:maj", "G:maj"}


def test_fill_with_only_n_returns_events_unchanged():
    events = [_event(0, "N", 0.0, 4.0)]
    chroma = np.stack([_tpl("C:maj"), _tpl("C:maj")])
    out = fill_silent_bars(events, _bars(2), chroma, np.ones(2))
    assert [(e.bar, e.beat, e.start, e.end, e.label) for e in out] == [
        (0, 0, 0.0, 2.0, "N"),
        (1, 0, 2.0, 4.0, "N"),
    ]
    assert not any(e.filled for e in out)


def test_fill_splits_multi_bar_n_event_at_bar_boundaries():
    events = [
        _event(0, "C:maj", 0.0, 1.0),
        _event(0, "N", 1.0, 7.0, beat=2),
        _event(3, "G:maj", 7.0, 8.0, beat=2),
    ]
    quiet = np.array([1.0, 0.0, 0.0, 1.0])
    out = fill_silent_bars(events, _bars(4), np.zeros((4, 12)), quiet)
    assert [(e.bar, e.beat, e.start, e.end, e.label) for e in out] == [
        (0, 0, 0.0, 1.0, "C:maj"),
        (0, 2, 1.0, 2.0, "N"),
        (1, 0, 2.0, 4.0, "N"),
        (2, 0, 4.0, 6.0, "N"),
        (3, 0, 6.0, 7.0, "N"),
        (3, 2, 7.0, 8.0, "G:maj"),
    ]
    assert not any(e.filled for e in out)


def test_fill_labels_sharing_a_triad_compete_as_one_candidate():
    events = [
        _event(0, "C:maj", 0.0, 2.0),
        _event(1, "G:maj", 2.0, 3.0),
        _event(1, "G:7", 3.0, 4.0, beat=2),
        _event(2, "N", 4.0, 6.0),
        _event(3, "G:7", 6.0, 8.0),
    ]
    chroma = np.stack([_tpl("C:maj"), _tpl("G:maj"), _tpl("G:maj"), _tpl("G:maj")])
    out = fill_silent_bars(events, _bars(4), chroma, np.ones(4))
    bar2 = [e for e in out if e.bar == 2]
    assert len(bar2) == 1 and bar2[0].filled
    assert bar2[0].label == "G:7" and bar2[0].triad == "G:maj"


def test_fill_partly_chorded_bar_is_not_a_candidate():
    events = [
        _event(0, "C:maj", 0.0, 2.0),
        _event(1, "G:maj", 2.0, 3.0),
        _event(1, "N", 3.0, 4.0, beat=2),
    ]
    chroma = np.stack([_tpl("C:maj"), _tpl("C:maj")])
    out = fill_silent_bars(events, _bars(2), chroma, np.ones(2))
    assert [e.label for e in out] == ["C:maj", "G:maj", "N"]
    assert not any(e.filled for e in out)


def test_bar_energy_is_rms_per_bar():
    y = np.concatenate([np.full(200, 0.5), np.zeros(200)])
    assert bar_energy(y, 100, _bars(2)) == pytest.approx([0.5, 0.0])


def test_bar_chroma_peaks_on_the_triad_played_in_each_bar():
    sr = 22050
    t = np.arange(2 * sr) / sr
    c_major = sum(np.sin(2 * np.pi * f * t) for f in (261.63, 329.63, 392.0))
    y = np.concatenate([c_major, np.zeros(2 * sr)]) * 0.2
    chroma = bar_chroma(y, sr, _bars(2))
    assert chroma.shape == (2, 12)
    assert set(np.argsort(chroma[0])[-3:]) == {0, 4, 7}


def test_bar_chroma_of_silence_is_zero():
    assert not bar_chroma(np.zeros(44100), 22050, _bars(1)).any()


def test_chord_event_filled_defaults_false_for_v1_1_files():
    event = ChordEvent.model_validate(
        {"schema": 1, "bar": 0, "beat": 0, "start": 0.0, "end": 1.0, "label": "C:maj",
         "triad": "C:maj", "confidence": 1.0}
    )
    assert event.filled is False
