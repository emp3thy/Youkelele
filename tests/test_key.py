import mir_eval.key
import numpy as np
import pytest

from youkelele.music.key import (
    FINAL_CHORD_BONUS,
    KEY_HEDGE_MARGIN,
    KEY_TIE_MARGIN,
    KRUMHANSL_MAJOR,
    KRUMHANSL_MINOR,
    MODE_TIE_MARGIN,
    PAIR_TIE,
    POWER_MIN_SHARE,
    POWER_MODE_MARGIN,
    SECTION_END_WEIGHT,
    SET_VETO_MARGIN,
    best_major_set,
    decide_tonic,
    estimate_key,
    hedge_text,
    hedge_tonic,
    hedged,
    key_and_decision,
    key_from_chords,
    key_text,
    mode_at,
    pair_rule_note,
    pair_shares,
    power_chord_events,
    relation,
    relative_key,
    tonic_chord_mode,
    tonic_scores,
    tonic_votes_note,
)
from youkelele.music.triads import to_triad
from youkelele.schemas import Bar, ChordEvent, Key, Section, TonicVotes


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
    decision = decide_tonic(events, bars, sections, chroma)
    assert (decision.tonic, decision.runner_up) == ("D", "A")  # the D/A pair tie goes to the chroma
    assert decision.rule == "pair rule"
    assert decision.pair_tonic == "G"  # the record over every candidate still names G
    # the G major set then beats D's pair share by 0.167: the set veto names G (spec 1.8, 7.1)
    assert key_from_chords(events, bars, sections, chroma, MIX).tonic == "G"


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


def test_power_chord_events_take_only_the_plain_major_label():
    # a seventh, a slash chord and an added ninth have more than root and fifth in the label
    labels = ["C#:maj"] * 6 + ["C#:7", "C#:maj7", "C#/3", "C#:maj(9)"] + ["B:maj"] * 3 + ["E:maj"] * 2
    assert power_chord_events(_events(labels), C_SHARP_MINOR, MINOR_STEMS) == list(range(6))
    # a bare root is the plain major too
    assert power_chord_events(_events(["C#"] * 6 + ["B:maj"] * 3), C_SHARP_MINOR, MINOR_STEMS) == list(
        range(6)
    )


def test_tonic_chord_mode_counts_every_quality_by_its_triad():
    assert tonic_chord_mode("F", _events(["F:9", "F:maj6", "F:min9"])) == "major"
    assert tonic_chord_mode("F", _events(["F:min9", "F:minmaj7", "F:9"])) == "minor"
    assert tonic_chord_mode("F", _events(["F:sus4", "F:5"])) is None


# --- the hedge carries its own mode (final fix wave, A1 and B2) ---


def test_runner_up_hedge_carries_its_own_mode():
    # A and C tie on score and on pair share; the A minor chroma picks A, C is the runner-up
    labels = ["A:min", "C:maj"] * 4 + ["E:min", "D:min"]
    events, bars, sections = _events(labels), _bars(len(labels)), _sections([len(labels)])
    chroma = np.roll(KRUMHANSL_MINOR, 9)  # A minor's profile: major at C
    key = key_from_chords(events, bars, sections, chroma, MIX)
    assert (key.tonic, key.mode, key.runner_up) == ("A", "minor", "C")
    assert key.margin < KEY_HEDGE_MARGIN and hedge_tonic(key) == "C"
    assert key.hedge_mode == "major"
    assert key_text(key) == "A minor (or C major)"
    assert hedge_text(key) == "C major"


def test_mix_hedge_carries_the_mode_the_stems_hear_at_the_mix_tonic():
    labels = ["G:maj", "C:maj", "D:maj", "G:maj"] * 3
    events, bars, sections = _events(labels), _bars(len(labels)), _sections([4, 4, 4])
    chroma = np.roll(KRUMHANSL_MAJOR, 7)  # G major's profile: minor at E
    # the mix names E major; the stems hear E as minor, and the stored mode is the stems'
    mix = Key(tonic="E", mode="major", confidence=0.2)
    key = key_from_chords(events, bars, sections, chroma, mix)
    assert (key.tonic, key.mode) == ("G", "major") and key.margin >= KEY_HEDGE_MARGIN
    assert hedge_tonic(key) == "E" and key.hedge_mode == "minor"
    assert key_text(key) == "G major (or E minor)"


def test_hedge_mode_tie_is_decided_by_the_hedge_tonics_own_chords():
    # at F the chroma prefers minor by under MODE_TIE_MARGIN; the song's one F chord is major
    chroma = np.roll(KRUMHANSL_MAJOR, 5) + 1.2 * np.roll(KRUMHANSL_MINOR, 5)
    mode, margin = mode_at("F", chroma)
    assert mode == "minor" and margin < MODE_TIE_MARGIN
    labels = ["C:maj", "F:maj", "G:maj", "C:maj"] * 3
    events, bars, sections = _events(labels), _bars(len(labels)), _sections([4, 4, 4])
    key = key_from_chords(events, bars, sections, chroma, Key(tonic="F", mode="minor", confidence=0.1))
    assert key.tonic == "C" and hedge_tonic(key) == "F"
    assert key.hedge_mode == "major" and hedge_text(key) == "F major"


def test_hedge_text_for_files_written_before_the_hedge_mode():
    # no stored hedge mode: the runner-up takes the key's mode, the mix keeps its own
    close = Key(tonic="A", mode="minor", confidence=0.3, method="chords_stems", margin=0.01,
                mode_margin=0.3, runner_up="C", mix=Key(tonic="A", mode="minor", confidence=0.1))
    assert close.hedge_mode is None and hedge_text(close) == "C minor"
    mix_only = close.model_copy(
        update={"margin": 0.2, "mix": Key(tonic="C", mode="major", confidence=0.1)}
    )
    assert hedge_text(mix_only) == "C major" and key_text(mix_only) == "A minor (or C major)"
    # a stored mode wins over the mix's own
    stored = mix_only.model_copy(
        update={"mix": Key(tonic="C", mode="minor", confidence=0.1), "hedge_mode": "major"}
    )
    assert hedge_text(stored) == "C major"
    assert hedge_text(close.model_copy(update={"margin": 0.2})) is None


def test_key_json_from_version_1_3_loads_without_a_hedge_mode():
    key = Key.model_validate({"schema": 1, "tonic": "C", "mode": "major", "confidence": 0.5})
    assert key.hedge_mode is None and key_text(key) == "C major" and hedge_text(key) is None
    hedged_key = Key(tonic="D", mode="major", confidence=0.3, method="chords_stems", margin=0.01,
                     mode_margin=0.3, runner_up="A", hedge_mode="minor")
    assert Key.model_validate_json(hedged_key.model_dump_json(by_alias=True)) == hedged_key


def test_pair_rule_note_names_a_chroma_tie_as_a_tie():
    events = _events(["C:maj", "F:maj"] * 4 + ["A:min", "D:min"])
    decision = decide_tonic(events, _bars(10), _sections([10]), _triad_chroma((5, 9, 0)))
    assert decision.pair_margin < PAIR_TIE
    assert pair_rule_note(decision) == f"tie, {decision.pair_tonic} by chroma"
    labels = ["G:maj", "C:maj", "D:maj", "G:maj"] * 3
    clear = decide_tonic(_events(labels), _bars(12), _sections([12]), np.ones(12))
    assert clear.pair_margin >= PAIR_TIE
    assert pair_rule_note(clear) == f"{clear.pair_tonic} by {clear.pair_margin:.3f}"
    assert pair_rule_note(None) == "none"


# --- three tonic votes: the score, the pair rule and the mix (spec 1.5, section 6) ---

bars = _bars(12)
sections = _sections([12])
# shaped like Need You Tonight: C holds half the chord time and ends the song, so the score
# names C by a wide margin; A# major is diatonic to F major, not to C major, so the pair rule
# names F (1.0 against 11 / 12), within SET_VETO_MARGIN, so the set vetoes neither
events_score_c_pair_f = _events(
    ["C:maj", "F:maj", "C:maj", "A#:maj", "C:maj", "F:maj", "C:maj", "D:min", "F:maj", "C:maj",
     "F:maj", "C:maj"]
)
# every chord diatonic to G major, G holding half the time: the score and the pair rule agree
events_clear_g = _events(["G:maj", "C:maj", "D:maj", "G:maj"] * 3)
# D and A tie on score; the pair rule decides (D, A, Bm and G are all diatonic to D major)
events_close_d_a = _events(["D:maj", "A:maj"] * 5 + ["B:min", "G:maj"])
chroma_f = np.roll(KRUMHANSL_MAJOR, 5)  # F major's profile: major at F and at C
chroma_g = np.roll(KRUMHANSL_MAJOR, 7)  # G major's profile: major at G and at D
chroma_d = _triad_chroma((2, 6, 9))
mix_key_f = Key(tonic="F", mode="major", confidence=0.2)
mix_key_g = Key(tonic="G", mode="major", confidence=0.2)
mix_key_d = Key(tonic="D", mode="major", confidence=0.2)
# the key of tests/fixtures/v14/chords.json, written by 1.4: no pair_tonic, no tonic_votes
FIXTURE_14_KEY_JSON = (
    '{"schema": 1, "tonic": "D", "mode": "major", "confidence": 0.30000378914920933, '
    '"method": "chords_stems", "margin": 0.0515576789091271, '
    '"mode_margin": 0.30000378914920933, "runner_up": "A", "mix": {"schema": 1, "tonic": "D", '
    '"mode": "major", "confidence": 0.055961666104045654, "method": "mix_krumhansl", '
    '"margin": null, "mode_margin": null, "runner_up": null, "mix": null}}'
)
EXPECTED_14_HEDGE = None  # what hedge_text returned for it before 1.5: a clear D major


def test_two_of_three_mix_decides_when_the_chord_rules_disagree():
    decision = decide_tonic(events_score_c_pair_f, bars, sections, chroma_f, mix_tonic="F")
    assert (decision.tonic, decision.score_tonic, decision.pair_tonic) == ("F", "C", "F")
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma_f, mix_key_f)
    assert key.tonic_votes == TonicVotes(
        score="C", pair="F", mix="F", decided_by="mix", set_tonic="F", set_share_best=1.0,
        set_share_decided=1.0,
    )
    assert key_text(key) == "F major (or C major)"


def test_score_leads_when_the_mix_names_neither():
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma_f, mix_key_g)
    assert key.tonic == "C" and key.tonic_votes.decided_by == "score"
    assert key_text(key) == "C major (or F major)"


def test_agreement_records_itself_and_the_mix_only_hedges():
    key, _ = key_and_decision(events_clear_g, bars, sections, chroma_g, mix_key_d)
    assert key.tonic_votes.decided_by == "agreement" and key_text(key) == "G major (or D major)"


def test_close_score_margin_keeps_the_pair_rule_decision():
    key, decision = key_and_decision(events_close_d_a, bars, sections, chroma_d, mix_key_d)
    assert decision.rule == "pair rule" and key.tonic_votes.decided_by == "pair rule"


def test_no_mix_estimate_falls_to_the_score_without_raising():
    decision = decide_tonic(events_score_c_pair_f, bars, sections, chroma_f, mix_tonic=None)
    assert decision.tonic == "C"


def test_pre_1_5_key_without_votes_hedges_as_1_4_did():
    key = Key.model_validate_json(FIXTURE_14_KEY_JSON)
    assert hedge_text(key) == EXPECTED_14_HEDGE  # the fixture's 1.4 text
    assert key_text(key) == "D major" and not hedged(key)


def test_mix_siding_with_the_score_still_hedges_the_pair_rule():
    decision = decide_tonic(events_score_c_pair_f, bars, sections, chroma_f, mix_tonic="C")
    assert (decision.tonic, decision.decided_by, decision.rule) == ("C", "mix", "score")
    mix_key_c = Key(tonic="C", mode="major", confidence=0.2)
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma_f, mix_key_c)
    assert key.pair_tonic == "F"
    votes = key.tonic_votes
    assert (votes.score, votes.pair, votes.mix, votes.decided_by) == ("C", "F", "C", "mix")
    assert votes.set_tonic == "F" and votes.set_share_decided == pytest.approx(11 / 12)
    # the score margin is clear and the mix agrees: only the losing chord rule hedges
    assert hedged(key) and hedge_tonic(key) == "F" and key_text(key) == "C major (or F major)"


def test_decision_records_the_score_tonic_and_who_decided():
    agree = decide_tonic(events_clear_g, bars, sections, chroma_g, mix_tonic="D")
    assert (agree.tonic, agree.score_tonic, agree.pair_tonic) == ("G", "G", "G")
    assert (agree.rule, agree.decided_by) == ("score", "agreement")
    close = decide_tonic(events_close_d_a, bars, sections, chroma_d, mix_tonic="A")
    assert (close.tonic, close.rule, close.decided_by) == ("D", "pair rule", "pair rule")
    # the mix chose the pair rule's tonic: the score's tonic is the runner-up and the score
    # margin (clear of KEY_TIE_MARGIN, so of KEY_HEDGE_MARGIN) is kept
    mixed = decide_tonic(events_score_c_pair_f, bars, sections, chroma_f, mix_tonic="F")
    assert mixed.runner_up == "C" and mixed.margin >= KEY_HEDGE_MARGIN


def test_hedge_rungs_in_order():
    votes = TonicVotes(score="C", pair="F", mix="A#", decided_by="mix")
    key = Key(tonic="F", mode="major", confidence=0.3, method="chords_stems", margin=0.2,
              mode_margin=0.3, runner_up="C", mix=Key(tonic="A#", mode="major", confidence=0.1),
              pair_tonic="F", tonic_votes=votes, hedge_mode="major")
    # rung 2 before rung 3: the losing chord rule, not the mix
    assert hedged(key) and hedge_tonic(key) == "C" and key_text(key) == "F major (or C major)"
    # rung 1 before rung 2: a close margin names the runner-up
    close = key.model_copy(update={"margin": 0.01, "runner_up": "A#"})
    assert hedge_tonic(close) == "A#"
    # agreement and the pair rule's own decision never reach rung 2
    for decided_by in ("agreement", "pair rule"):
        settled = key.model_copy(
            update={"tonic_votes": votes.model_copy(update={"decided_by": decided_by})}
        )
        assert hedge_tonic(settled) == "A#"  # the mix differs: rung 3
        same_mix = settled.model_copy(update={"mix": Key(tonic="F", mode="major", confidence=0.1)})
        assert not hedged(same_mix) and hedge_tonic(same_mix) is None
    # the score led: the pair rule's tonic
    score_led = key.model_copy(
        update={"tonic": "C", "tonic_votes": votes.model_copy(update={"decided_by": "score"})}
    )
    assert hedged(score_led) and hedge_tonic(score_led) == "F"


def test_tonic_votes_note_prints_none_for_a_missing_vote():
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma_f, mix_key_f)
    assert tonic_votes_note(key) == "score C, pair F, mix F, decided by mix, set F (1.000 vs 1.000)"
    no_mix = key.model_copy(
        update={"tonic_votes": TonicVotes(score="C", pair="F", decided_by="mix")}
    )  # a file before 1.8 has no set vote either
    assert tonic_votes_note(no_mix) == "score C, pair F, mix none, decided by mix"
    assert tonic_votes_note(MIX) == "none"  # a mix key, or a file before 1.5, has no votes


# --- the diatonic-set veto, the relative-key hedge and the key relation (spec 1.8, section 7) ---

# shaped like Badge: D holds the most chord time, but every chord fits the G major set; A is
# minor (ii of G), which D major's own set credits at half
BADGE_SHARES = {"D:maj": 34, "A:min": 21, "E:min": 17, "C:maj": 13, "G:maj": 11, "B:min": 4}
events_badge = _events([label for label, n in BADGE_SHARES.items() for _ in range(n)])
bars_badge, sections_badge = _bars(100), _sections([100])


def test_best_major_set_names_the_set_that_holds_the_whole_stream():
    events = _events(["A:min", "D:maj", "E:min", "C:maj", "G:maj", "B:min"])
    tonic, share = best_major_set(events)
    assert tonic == "G" and share == pytest.approx(1.0)
    # the relative pair ties in pair_shares; the major set is named explicitly
    shares = pair_shares(events, ["E", "G"])
    assert shares["E"] == pytest.approx(shares["G"])


def test_set_veto_replaces_a_dominant_heavy_tonic_with_the_sets_major_tonic():
    assert SET_VETO_MARGIN == 0.10
    decision = decide_tonic(events_badge, bars_badge, sections_badge, chroma_g, mix_tonic="D")
    assert decision.tonic == "D"  # the three votes alone name D
    key, vetoed = key_and_decision(events_badge, bars_badge, sections_badge, chroma_g, mix_key_d)
    assert (key.tonic, key.mode) == ("G", "major")
    votes = key.tonic_votes
    assert votes.decided_by == "set" and vetoed.decided_by == "set"
    assert votes.set_tonic == "G"
    assert votes.set_share_best - votes.set_share_decided >= SET_VETO_MARGIN
    assert votes.set_share_best == pytest.approx(1.0)
    assert votes.set_share_decided == pytest.approx(pair_shares(events_badge, ["D"])["D"])
    assert key.margin == pytest.approx(votes.set_share_best - votes.set_share_decided)
    assert key.runner_up is None and vetoed.runner_up is None and vetoed.tonic == "G"
    # the hedge is the relative key by construction
    assert key.hedge_mode == "minor" and hedge_text(key) == "E minor"
    assert key_text(key) == "G major (or E minor)"


def test_set_veto_compares_pair_shares_not_the_tonics_own_major_set():
    # C# minor: its own major set holds only the half-credited C#m, but its pair (E major's
    # set) holds every chord, so the best set (E) does not beat it
    events = _events(["E:maj"] * 2 + ["A:maj"] * 2 + ["B:maj"] * 2 + ["C#:min"] * 4)
    decision = decide_tonic(events, _bars(10), _sections([10]), MINOR_STEMS, MIX.tonic)
    key, after = key_and_decision(events, _bars(10), _sections([10]), MINOR_STEMS, MIX)
    assert key.tonic == "C#" and after.decided_by == decision.decided_by != "set"
    assert key.tonic_votes.decided_by == decision.decided_by
    assert key.tonic_votes.set_tonic == "E"
    assert key.tonic_votes.set_share_best == pytest.approx(1.0)
    assert key.tonic_votes.set_share_decided == pytest.approx(1.0)


def test_set_veto_does_not_fire_within_the_margin():
    # A minor is ii of G, half-credited in D major's set: the best set (G) beats D's pair
    # share by 0.05
    labels = ["A:min"] * 2 + ["E:min"] * 4 + ["G:maj"] * 4 + ["B:min"] * 2 + ["D:maj"] * 8
    events = _events(labels)
    key, decision = key_and_decision(events, _bars(20), _sections([20]), chroma_d, MIX)
    assert key.tonic == "D" and decision.decided_by != "set"
    votes = key.tonic_votes
    assert votes.decided_by != "set" and votes.set_tonic == "G"
    assert votes.set_share_best == pytest.approx(1.0)
    assert votes.set_share_best - votes.set_share_decided == pytest.approx(0.05)


def test_set_veto_with_no_chord_time_or_too_few_events_leaves_the_mix_key():
    events = _events(["N"] * 4 + ["G:maj", "C:maj", "D:maj"])
    key, decision = key_and_decision(events, _bars(7), _sections([7]), chroma_g, MIX)
    assert key == MIX and decision is None
    assert best_major_set(_events(["N"] * 4)) == ("C", 0.0)
    assert best_major_set([]) == ("C", 0.0)


def test_relation_matches_mir_eval_categories():
    weights = {"same": 1.0, "fifth": 0.5, "relative": 0.3, "parallel": 0.2, "other": 0.0}
    for a, b, expect in [
        (("G", "major"), ("D", "major"), "fifth"),
        (("G", "major"), ("E", "minor"), "relative"),
        (("G", "major"), ("G", "minor"), "parallel"),
        (("G", "major"), ("A", "major"), "other"),
        (("G", "major"), ("G", "major"), "same"),
    ]:
        assert relation(*a, *b) == expect
        assert mir_eval.key.weighted_score(f"{a[0]} {a[1]}", f"{b[0]} {b[1]}") == weights[expect]
    # a fifth either way, and the relative pair either way round
    assert relation("D", "major", "G", "major") == "fifth"
    assert relation("E", "minor", "G", "major") == "relative"
    assert relation("G", "minor", "E", "major") == "other"


def test_relative_key_both_ways():
    assert relative_key("G", "major") == ("E", "minor") and relative_key("E", "minor") == ("G", "major")
    assert relative_key("C", "major") == ("A", "minor") and relative_key("C#", "minor") == ("E", "major")


def test_an_unrelated_hedge_is_dropped_but_a_fifth_hedge_stays():
    base = Key(tonic="G", mode="major", confidence=0.3, method="chords_stems", margin=0.2,
               mode_margin=0.3, runner_up="C", hedge_mode="major")
    second = base.model_copy(update={"mix": Key(tonic="A", mode="major", confidence=0.1)})
    assert hedge_tonic(second) is None and hedge_text(second) is None
    assert not hedged(second) and key_text(second) == "G major"
    fifth = base.model_copy(update={"mix": Key(tonic="D", mode="major", confidence=0.1)})
    assert hedge_tonic(fifth) == "D" and key_text(fifth) == "G major (or D major)"
    # on a close margin an unrelated hedge stays
    close = second.model_copy(update={"margin": 0.01, "runner_up": None})
    assert hedge_tonic(close) == "A"
    # end to end: the mix names A major against a clear G; nothing is hedged, and the stems'
    # mode at A stays stored so no fallback mode can revive the hedge
    key, _ = key_and_decision(events_clear_g, bars, sections, chroma_g,
                              Key(tonic="A", mode="major", confidence=0.2))
    assert key.tonic == "G" and key.margin >= KEY_HEDGE_MARGIN
    assert key.hedge_mode is not None
    assert not hedged(key) and hedge_text(key) is None and key_text(key) == "G major"


def test_a_dropped_mix_hedge_stays_dropped_when_the_mixs_own_mode_would_relate_it():
    # the mix names E minor (G's relative), but the stems hear E major: unrelated to G major
    chroma = _triad_chroma((4, 8, 11))
    assert mode_at("G", chroma)[0] == "major" and mode_at("E", chroma)[0] == "major"
    key, _ = key_and_decision(events_clear_g, bars, sections, chroma,
                              Key(tonic="E", mode="minor", confidence=0.2))
    assert (key.tonic, key.mode) == ("G", "major") and key.margin >= KEY_HEDGE_MARGIN
    assert key.hedge_mode == "major"
    assert not hedged(key) and hedge_text(key) is None and key_text(key) == "G major"


def test_a_dropped_chord_rule_hedge_stays_dropped_when_the_keys_mode_would_relate_it():
    # the score leads C over the pair rule's F (the mix names neither); the stems hear F minor,
    # unrelated to C major, where the key's own mode would read F major, a fifth
    chroma = _triad_chroma((0, 4, 5, 7, 8))
    assert mode_at("C", chroma)[0] == "major" and mode_at("F", chroma)[0] == "minor"
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma, mix_key_g)
    assert (key.tonic, key.mode, key.tonic_votes.decided_by) == ("C", "major", "score")
    assert key.margin >= KEY_HEDGE_MARGIN and key.hedge_mode == "minor"
    assert not hedged(key) and hedge_text(key) is None and key_text(key) == "C major"


def test_tonic_votes_note_prints_the_set():
    key, _ = key_and_decision(events_badge, bars_badge, sections_badge, chroma_g, mix_key_d)
    votes = key.tonic_votes
    assert tonic_votes_note(key) == (
        f"score D, pair A, mix D, decided by set, "
        f"set G ({votes.set_share_best:.3f} vs {votes.set_share_decided:.3f})"
    )
    assert tonic_votes_note(key).endswith("set G (1.000 vs 0.765)")
