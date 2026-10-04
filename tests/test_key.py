import numpy as np
import pytest

from youkelele.music.key import (
    FINAL_CHORD_BONUS,
    KEY_HEDGE_MARGIN,
    KEY_TIE_MARGIN,
    KRUMHANSL_MAJOR,
    KRUMHANSL_MINOR,
    MODE_TIE_MARGIN,
    SECTION_END_WEIGHT,
    estimate_key,
    hedge_tonic,
    hedged,
    key_from_chords,
    key_text,
    mode_at,
    pair_shares,
    tonic_chord_mode,
    tonic_scores,
)
from youkelele.music.triads import to_triad
from youkelele.schemas import Bar, ChordEvent, Key, Section


def _chroma(pitch_classes):
    chroma = np.full(12, 0.05)
    for pc in pitch_classes:
        chroma[pc] = 1.0
    return chroma


def test_estimate_key_c_major_from_scale_chroma():
    chroma = _chroma([0, 2, 4, 5, 7, 9, 11])
    chroma[0] += 0.5
    chroma[7] += 0.3
    key = estimate_key(chroma)
    assert (key.tonic, key.mode) == ("C", "major")
    assert 0 <= key.confidence <= 1


def test_estimate_key_a_minor_prefers_minor_profile():
    chroma = _chroma([9, 11, 0, 2, 4, 5, 8])
    chroma[9] += 0.6
    chroma[4] += 0.4
    chroma[0] += 0.3
    key = estimate_key(chroma)
    assert (key.tonic, key.mode) == ("A", "minor")


# --- the key from the chord stream ---


def _bars(n: int, seconds: float = 1.0) -> list[Bar]:
    return [
        Bar(index=i, start=i * seconds, end=(i + 1) * seconds, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(n)
    ]


def _events(labels: list[str], seconds: float = 1.0) -> list[ChordEvent]:
    """One event per bar."""
    return [
        ChordEvent(
            bar=i, beat=0, start=i * seconds, end=(i + 1) * seconds, label=label,
            triad=to_triad(label), confidence=0.9,
        )
        for i, label in enumerate(labels)
    ]


def _sections(lengths: list[int]) -> list[Section]:
    out, start = [], 0
    for length in lengths:
        out.append(Section(label="s", start_bar=start, end_bar=start + length, confidence=0.5))
        start += length
    return out


def _triad_chroma(pitch_classes) -> np.ndarray:
    chroma = np.full(12, 0.1)
    chroma[list(pitch_classes)] = 1.0
    return chroma


MIX = Key(tonic="A", mode="minor", confidence=0.3)


def test_tonic_scores_root_share_final_bonus_and_section_ends():
    a_end = ["D:maj", "A:maj", "G:maj", "A:maj", "D:maj", "B:min", "A:maj", "D:maj", "A:maj"]
    d_end = ["D:maj", "A:maj", "G:maj", "A:maj", "D:maj", "B:min", "A:maj", "D:maj", "D:maj"]
    labels = a_end * 5 + d_end * 6  # 11 sections; the last 6 (and the song) end on D
    events = _events(labels)
    sections = _sections([9] * 11)
    scores = tonic_scores(events, _bars(len(labels)), sections)
    assert set(scores) == {"D", "A"}  # G and B hold 11 of 99 bars each, under TONIC_MIN_SHARE
    share_d, share_a = 39 / 99, 38 / 99
    assert scores["D"] == pytest.approx(share_d + FINAL_CHORD_BONUS + SECTION_END_WEIGHT * 6 / 11)
    assert scores["A"] == pytest.approx(share_a + SECTION_END_WEIGHT * 5 / 11)
    assert max(scores, key=scores.get) == "D"


def test_tonic_scores_skip_trailing_n_for_the_final_chord_not_for_section_ends():
    events = _events(["D:maj", "A:maj", "D:maj", "A:maj", "N"])
    scores = tonic_scores(events, _bars(5), _sections([2, 3]))
    # the song's final chord is A (the trailing N is skipped); the first section ends on A,
    # the second on N, which is no root
    assert scores["A"] == pytest.approx(0.5 + FINAL_CHORD_BONUS + SECTION_END_WEIGHT / 2)
    assert scores["D"] == pytest.approx(0.5)


def test_tonic_scores_final_chord_shorter_than_a_bar_earns_no_bonus():
    events = _events(["D:maj", "A:maj", "D:maj", "A:maj"])
    events[-1] = events[-1].model_copy(update={"end": events[-1].start + 0.5})
    scores = tonic_scores(events, _bars(4), _sections([4]))
    # A's final event lasts half a bar: only the section end counts
    assert scores["A"] == pytest.approx(1.5 / 3.5 + SECTION_END_WEIGHT)


def test_tonic_tie_breaks_by_pair_share():
    labels = ["D:maj", "A:maj"] * 4 + ["B:min", "G:maj"]  # D and A tie at 0.4 each
    events = _events(labels)
    bars, sections = _bars(len(labels)), _sections([len(labels)])
    scores = tonic_scores(events, bars, sections)
    assert set(scores) == {"D", "A"}
    assert abs(scores["D"] - scores["A"]) < KEY_TIE_MARGIN
    shares = pair_shares(events, ["D", "A"])
    assert shares["D"] == pytest.approx(1.0)  # D, A, Bm and G are all diatonic to D/Bm
    assert shares["A"] == pytest.approx(0.9)  # G is outside A/F#m
    # half credit for a diatonic root of the wrong quality: E is ii (minor) in D major
    assert pair_shares(_events(["E:maj", "D:maj"]), ["D"])["D"] == pytest.approx(0.75)
    key = key_from_chords(events, bars, sections, _triad_chroma((2, 6, 9)), MIX)
    assert (key.tonic, key.method, key.runner_up) == ("D", "chords_stems", "A")
    assert key.margin == pytest.approx(0.1)
    assert key.mix == MIX


def test_mode_at_tonic_major_and_minor():
    mode, margin = mode_at("D", _triad_chroma((2, 6, 9)))
    assert mode == "major" and margin > MODE_TIE_MARGIN
    mode, margin = mode_at("D", _triad_chroma((2, 5, 9)))
    assert mode == "minor" and margin > MODE_TIE_MARGIN
    assert mode_at("D", np.zeros(12)) == ("major", 0.0)  # a silent chroma is a tie, not an error


def test_mode_tie_falls_back_to_tonic_chord_quality():
    # both profiles at F, weighted so minor wins by about 0.026: a tie under MODE_TIE_MARGIN
    chroma = np.roll(KRUMHANSL_MAJOR, 5) + 1.2 * np.roll(KRUMHANSL_MINOR, 5)
    mode, margin = mode_at("F", chroma)
    assert mode == "minor" and 0 < margin < MODE_TIE_MARGIN
    labels = ["F:maj", "F:7", "A#:maj", "F:7", "C:7", "F:maj"]
    key = key_from_chords(_events(labels), _bars(6), _sections([6]), chroma, MIX)
    assert (key.tonic, key.mode) == ("F", "major")
    assert key.mode_margin == pytest.approx(margin)
    assert key.confidence == pytest.approx(margin)
    flat = key_from_chords(_events(labels), _bars(6), _sections([6]), np.ones(12), MIX)
    assert (flat.mode, flat.mode_margin) == ("major", 0.0)
    minor = ["F:min", "F:min7", "A#:min", "F:min7", "C:7", "F:min"]
    flat = key_from_chords(_events(minor), _bars(6), _sections([6]), np.ones(12), MIX)
    assert (flat.tonic, flat.mode) == ("F", "minor")
    assert tonic_chord_mode("F", _events(labels)) == "major"
    assert tonic_chord_mode("F", _events(["F:min7", "F:min7", "F:7"])) == "minor"
    assert tonic_chord_mode("F", _events(["F:sus4", "C:maj"])) is None
    assert tonic_chord_mode("G", _events(labels)) is None


def test_key_from_chords_falls_back_with_fewer_than_four_events():
    events = _events(["D:maj", "N", "A:maj", "N", "D:maj"])
    key = key_from_chords(events, _bars(5), _sections([5]), _triad_chroma((2, 6, 9)), MIX)
    assert key == MIX
    assert key.method == "mix_krumhansl" and key.margin is None and key.mix is None


def test_hedged_when_margin_small_or_mix_disagrees():
    near = Key(tonic="G", mode="major", confidence=0.3, method="chords_stems",
               margin=KEY_HEDGE_MARGIN - 0.01, mode_margin=0.3, runner_up="D",
               mix=Key(tonic="G", mode="major", confidence=0.1))
    assert hedged(near) and hedge_tonic(near) == "D"
    assert key_text(near) == "G major (or D major)"
    clear = near.model_copy(update={"margin": 0.15})
    assert not hedged(clear) and hedge_tonic(clear) is None
    assert key_text(clear) == "G major"
    disagrees = clear.model_copy(update={"mix": Key(tonic="D", mode="major", confidence=0.1)})
    assert hedged(disagrees) and key_text(disagrees) == "G major (or D major)"
    alone = disagrees.model_copy(update={"runner_up": None})  # a sole candidate: the mix's tonic
    assert hedge_tonic(alone) == "D"
    assert not hedged(MIX) and key_text(MIX) == "A minor"


def test_key_json_without_new_fields_loads():
    key = Key.model_validate({"schema": 1, "tonic": "C", "mode": "major", "confidence": 0.5})
    assert key.method == "mix_krumhansl"
    assert key.margin is None and key.mode_margin is None
    assert key.runner_up is None and key.mix is None
    nested = Key(tonic="D", mode="major", confidence=0.3, method="chords_stems", margin=0.05,
                 mode_margin=0.3, runner_up="A", mix=key)
    assert Key.model_validate_json(nested.model_dump_json(by_alias=True)) == nested
