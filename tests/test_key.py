import numpy as np
import pytest

from youkelele.music.key import (
    FINAL_CHORD_BONUS,
    KEY_HEDGE_MARGIN,
    KEY_TIE_MARGIN,
    KRUMHANSL_MAJOR,
    KRUMHANSL_MINOR,
    MODE_TIE_MARGIN,
    POWER_MIN_SHARE,
    POWER_MODE_MARGIN,
    SECTION_END_WEIGHT,
    decide_tonic,
    estimate_key,
    hedge_tonic,
    hedged,
    key_from_chords,
    key_text,
    mode_at,
    pair_shares,
    power_chord_events,
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


def test_hedge_names_the_runner_up_for_a_close_margin_and_the_mix_otherwise():
    base = Key(tonic="G", mode="major", confidence=0.3, method="chords_stems", margin=0.15,
               mode_margin=0.3, runner_up="C", mix=Key(tonic="D", mode="major", confidence=0.1))
    # only the mix disagrees: the mix's tonic, not the score runner-up
    assert hedge_tonic(base) == "D" and key_text(base) == "G major (or D major)"
    # the margin is close and the mix disagrees too: the runner-up
    both = base.model_copy(update={"margin": 0.02})
    assert hedge_tonic(both) == "C"
    # only the margin is close
    close = both.model_copy(update={"mix": Key(tonic="G", mode="major", confidence=0.1)})
    assert hedge_tonic(close) == "C"


def test_pair_tie_is_broken_by_the_stem_chroma():
    # C and F tie on score (0.4 each, the song and its one section end on D minor) and on
    # pair share (every chord is diatonic to both C major and F major)
    labels = ["C:maj", "F:maj"] * 4 + ["A:min", "D:min"]
    events = _events(labels)
    bars, sections = _bars(len(labels)), _sections([len(labels)])
    scores = tonic_scores(events, bars, sections)
    assert scores["C"] == pytest.approx(scores["F"])
    shares = pair_shares(events, ["C", "F"])
    assert shares["C"] == pytest.approx(1.0) and shares["F"] == pytest.approx(1.0)
    for triad, tonic, other in (((0, 4, 7), "C", "F"), ((5, 9, 0), "F", "C")):
        key = key_from_chords(events, bars, sections, _triad_chroma(triad), MIX)
        assert (key.tonic, key.runner_up) == (tonic, other)
        assert key.margin == pytest.approx(0.0)
        assert hedged(key)


def test_pair_tie_break_weighs_only_candidates_close_on_score():
    # D and A tie on score (a third each); G is a candidate 0.11 behind whose pair share
    # (every chord diatonic to G major) beats both
    labels = ["D:maj", "A:min"] * 3 + ["G:maj"] * 2 + ["E:min"]
    events = _events(labels)
    bars, sections = _bars(len(labels)), _sections([len(labels)])
    scores = tonic_scores(events, bars, sections)
    assert set(scores) == {"D", "A", "G"}
    assert scores["D"] == pytest.approx(scores["A"]) and scores["G"] < scores["D"] - KEY_TIE_MARGIN
    shares = pair_shares(events, ["D", "A", "G"])
    assert shares["G"] == pytest.approx(1.0)
    assert shares["D"] == pytest.approx(7.5 / 9) and shares["A"] == pytest.approx(7.5 / 9)
    chroma = _triad_chroma((2, 6, 9))
    key = key_from_chords(events, bars, sections, chroma, MIX)
    assert (key.tonic, key.runner_up) == ("D", "A")  # the D/A pair tie goes to the chroma
    decision = decide_tonic(events, bars, sections, chroma)
    assert decision.rule == "pair rule"
    assert decision.pair_tonic == "G"  # the record over every candidate still names G


def test_minor_key_candidate_is_scored_by_its_minor_pair():
    # shaped like Pour Some Sugar On Me: C# major riff 40%, B 24%, E 20%, A 16%
    seconds = {"C#:maj": 10, "B:maj": 6, "E:maj": 5, "A:maj": 4}
    events = _events([label for label, n in seconds.items() for _ in range(n)])
    shares = pair_shares(events, ["C#", "B"])
    # C# minor with E major: C# (wrong quality) half, B, E and A full
    assert shares["C#"] == pytest.approx((5 + 6 + 5 + 4) / 25)
    # B major with G# minor beats B minor with D major: C# half, B and E full, A outside
    assert shares["B"] == pytest.approx((5 + 6 + 5) / 25)
    assert shares["C#"] > shares["B"]


# --- tonic power chords (spec 1.4, section 3.2) ---

C_SHARP_MINOR = Key(tonic="C#", mode="minor", confidence=0.4, method="chords_stems",
                    margin=0.14, mode_margin=0.42, runner_up="B")
# C# minor's own triad (C#, E, G#): the harmonic stems hear a minor tonic
MINOR_STEMS = _triad_chroma((1, 4, 8))


def _riff_stream() -> list[ChordEvent]:
    """Shaped like Pour Some Sugar On Me: the riff reads C#:maj for ten of 25 bars."""
    seconds = {"C#:maj": 10, "B:maj": 6, "E:maj": 5, "A:maj": 4}
    return _events([label for label, n in seconds.items() for _ in range(n)])


def test_power_chord_constants():
    assert POWER_MODE_MARGIN == 0.2 and POWER_MIN_SHARE == 0.2


def test_power_chord_events_fire_only_at_the_minor_tonic_with_all_gates():
    events = _riff_stream()
    mode, margin = mode_at("C#", MINOR_STEMS)
    assert mode == "minor" and margin >= POWER_MODE_MARGIN
    indices = power_chord_events(events, C_SHARP_MINOR, MINOR_STEMS)
    assert indices == [i for i, e in enumerate(events) if e.label == "C#:maj"] == list(range(10))


def test_power_chord_events_count_every_maj_event_of_the_tonic_root():
    labels = ["C#:maj", "B:maj", "C#:maj", "E:maj", "C#:min7", "C#:maj", "A:maj"]
    # C#:maj 3 bars against C#:min7 1 bar; the root holds 4 of 7 bars of chord time
    assert power_chord_events(_events(labels), C_SHARP_MINOR, MINOR_STEMS) == [0, 2, 5]


def test_power_chord_events_off_when_the_tonic_is_not_mostly_major():
    labels = ["C#:min"] * 3 + ["C#:maj"] * 2 + ["B:maj", "E:maj"]
    assert power_chord_events(_events(labels), C_SHARP_MINOR, MINOR_STEMS) == []


def test_power_chord_events_off_when_the_stems_do_not_clearly_prefer_minor():
    events = _riff_stream()
    major_stems = _triad_chroma((1, 5, 8))  # C# major's own triad
    assert power_chord_events(events, C_SHARP_MINOR, major_stems) == []
    assert power_chord_events(events, C_SHARP_MINOR, np.ones(12)) == []  # no preference at all
    # prefers minor, but not by POWER_MODE_MARGIN
    unsure = _triad_chroma((1, 4, 5, 8))
    assert mode_at("C#", unsure)[0] == "minor" and mode_at("C#", unsure)[1] < POWER_MODE_MARGIN
    assert power_chord_events(events, C_SHARP_MINOR, unsure) == []


def test_power_chord_events_off_for_picardy_under_share():
    # the tonic is major for two of twenty bars and never minor: 10 percent of chord time
    labels = ["C#:maj"] * 2 + ["B:maj"] * 8 + ["E:maj"] * 6 + ["A:maj"] * 4
    assert power_chord_events(_events(labels), C_SHARP_MINOR, MINOR_STEMS) == []


def test_power_chord_events_off_in_major_key():
    major = C_SHARP_MINOR.model_copy(update={"mode": "major"})
    assert power_chord_events(_riff_stream(), major, MINOR_STEMS) == []


def test_power_chord_events_share_ignores_no_chord_time():
    labels = ["C#:maj"] * 3 + ["N"] * 10 + ["B:maj"] * 6 + ["E:maj"] * 5 + ["A:maj"] * 1
    assert power_chord_events(_events(labels), C_SHARP_MINOR, MINOR_STEMS) == [0, 1, 2]


def test_key_json_without_new_fields_loads():
    key = Key.model_validate({"schema": 1, "tonic": "C", "mode": "major", "confidence": 0.5})
    assert key.method == "mix_krumhansl"
    assert key.margin is None and key.mode_margin is None
    assert key.runner_up is None and key.mix is None
    nested = Key(tonic="D", mode="major", confidence=0.3, method="chords_stems", margin=0.05,
                 mode_margin=0.3, runner_up="A", mix=key)
    assert Key.model_validate_json(nested.model_dump_json(by_alias=True)) == nested
