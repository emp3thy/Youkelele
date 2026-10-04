"""The song's key.

1.4: the tonic comes from the chord stream and the mode from the harmonic-stem chroma
(`key_from_chords`). The 24-way Krumhansl-Kessler search on the mix (`estimate_key`)
is kept as the fallback for songs with too few chords and for comparison.

1.5: when the score and the pair rule disagree on a clear score margin, the mix estimate's
tonic decides between them (`decide_tonic`), and the losing chord rule is hedged (`_hedge`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import mir_eval.chord
import numpy as np
import soundfile as sf

from youkelele.music.triads import to_triad
from youkelele.schemas import Bar, ChordEvent, Key, Section, TonicVotes

KRUMHANSL_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KRUMHANSL_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)
_TONICS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def estimate_key(chroma_mean: np.ndarray) -> Key:
    chroma = np.asarray(chroma_mean, dtype=float)
    scored: list[tuple[float, int, str]] = []
    for mode, profile in (("major", KRUMHANSL_MAJOR), ("minor", KRUMHANSL_MINOR)):
        for tonic in range(12):
            corr = np.corrcoef(chroma, np.roll(profile, tonic))[0, 1]
            scored.append((float(np.nan_to_num(corr)), tonic, mode))
    scored.sort(key=lambda s: s[0], reverse=True)
    best, second = scored[0][0], scored[1][0]
    confidence = float(np.clip((best - second) / best, 0.0, 1.0)) if best > 0 else 0.0
    return Key(tonic=_TONICS[scored[0][1]], mode=scored[0][2], confidence=confidence)


def chroma_mean_for(wav: Path) -> np.ndarray:
    import librosa

    signal, sr = sf.read(str(wav), dtype="float32", always_2d=True)
    chroma = librosa.feature.chroma_cqt(y=signal.mean(axis=1), sr=sr)
    return chroma.mean(axis=1)


# --- The key from the chord stream: tonic from the chords, mode from the stems ---
#
# Measured on the five 1.3 runs (spec 2026-10-04 v1.4, section 9, A1 to A3).

# A root needs this share of chord time to be a tonic candidate.
TONIC_MIN_SHARE = 0.2
# Added when the song's final chord has the root and lasts at least a bar. Kept small: where
# the recording fades decides it (Summer of '69 ended on D in 1.1 and on B minor in 1.3).
FINAL_CHORD_BONUS = 0.10
# Times the share of sections whose last chord has the root.
SECTION_END_WEIGHT = 0.15
# Under this score margin the relative-major pair rule decides (Summer of '69: 0.028).
KEY_TIE_MARGIN = 0.05
# Pair shares this close are a tie, decided by the stem chroma's Krumhansl fit at each tonic.
PAIR_TIE = 0.02
# Under this deciding margin the sheet names the runner-up as well.
KEY_HEDGE_MARGIN = 0.05
# Under this mode margin the tonic's own chords decide (Fame: 0.003 at F).
MODE_TIE_MARGIN = 0.05
# With fewer chord events than this the mix estimate stands.
MIN_CHORD_EVENTS = 4

_NO_CHORD = ("N", "X")
# The diatonic triads of a major key by semitones above its tonic.
_DIATONIC = {0: "maj", 2: "min", 4: "min", 5: "maj", 7: "maj", 9: "min", 11: "dim"}


@dataclass(frozen=True)
class _Chord:
    root: int  # pitch class
    quality: str  # the label's own quality, e.g. "7"
    triad: str  # the reduced triad quality, e.g. "maj"
    duration: float
    bar: int
    plain: bool = False  # the plain major label: no seventh, extra degree or bass


def plain_major_root(label: str) -> str | None:
    """The root as written when `label` is the plain major chord (`C#:maj` or `C#`), else None.

    A seventh, an added degree (`C#:maj(9)`) or a bass (`C#/3`) has more than a root and
    fifth in it, so none of them is a plain major."""
    try:
        root, quality, degrees, bass = mir_eval.chord.split(label)
    except (mir_eval.chord.InvalidChordException, ValueError, IndexError):
        return None
    return root if quality == "maj" and not degrees and bass == "1" else None


@dataclass(frozen=True)
class TonicDecision:
    tonic: str
    margin: float  # the pair rule's margin under rule 1, else the score's (rules 2 and 3, even when the mix picks the pair rule's tonic)
    runner_up: str | None
    rule: Literal["score", "pair rule"]
    pair_tonic: str  # the pair rule's winner, computed whether or not it decided
    pair_margin: float
    score_tonic: str  # the score's winner, before any override
    decided_by: Literal["agreement", "pair rule", "mix", "score"]


def _pitch_class(name: str) -> int:
    return mir_eval.chord.pitch_class_to_semitone(name) % 12


def _chords(events: Sequence[ChordEvent]) -> list[_Chord]:
    """The events holding a parseable chord, in order."""
    out: list[_Chord] = []
    for event in events:
        if event.label in _NO_CHORD or event.end <= event.start:
            continue
        try:
            root, quality, _degrees, _bass = mir_eval.chord.split(event.label)
            _root, triad, _degrees, _bass = mir_eval.chord.split(to_triad(event.label))
            pc = _pitch_class(root)
        except (mir_eval.chord.InvalidChordException, ValueError, IndexError):
            continue
        plain = plain_major_root(event.label) is not None
        out.append(_Chord(pc, quality, triad, event.end - event.start, event.bar, plain))
    return out


def _bar_length(bars: Sequence[Bar]) -> float:
    lengths = [bar.end - bar.start for bar in bars if not bar.pickup] or [
        bar.end - bar.start for bar in bars
    ]
    return float(np.median(lengths)) if lengths else 0.0


def _section_endings(events: Sequence[ChordEvent], sections: Sequence[Section]) -> dict[int, int]:
    """Sections per root whose last event (by start bar) has that root; a section whose last
    event is no-chord ends on nothing."""
    endings: dict[int, int] = {}
    for section in sections:
        inside = [e for e in events if section.start_bar <= e.bar < section.end_bar]
        last = _chords(inside[-1:])
        if last:
            endings[last[0].root] = endings.get(last[0].root, 0) + 1
    return endings


def _scores(
    chords: Sequence[_Chord],
    endings: dict[int, int],
    bars: Sequence[Bar],
    n_sections: int,
    min_share: float,
) -> dict[str, float]:
    times: dict[int, float] = {}
    for chord in chords:
        times[chord.root] = times.get(chord.root, 0.0) + chord.duration
    total = sum(times.values())
    if total <= 0:
        return {}

    # the final chord (trailing no-chord events skipped): the last run of events on one
    # root, held for at least a bar
    final_root, held = chords[-1].root, 0.0
    for chord in reversed(chords):
        if chord.root != final_root:
            break
        held += chord.duration
    final_held = held >= _bar_length(bars) - 1e-9

    scores: dict[str, float] = {}
    for pc, held_time in times.items():
        share = held_time / total
        if share < min_share:
            continue
        score = share
        if final_held and pc == final_root:
            score += FINAL_CHORD_BONUS
        if n_sections:
            score += SECTION_END_WEIGHT * endings.get(pc, 0) / n_sections
        scores[_TONICS[pc]] = score
    return scores


def tonic_scores(
    events: Sequence[ChordEvent], bars: Sequence[Bar], sections: Sequence[Section]
) -> dict[str, float]:
    """Score each root holding at least `TONIC_MIN_SHARE` of chord time (filled events count).

    Score = the root's share of chord time, plus `FINAL_CHORD_BONUS` when the song's final
    chord has the root and lasts at least the median full-bar length, plus
    `SECTION_END_WEIGHT` times the share of sections whose last event has the root.
    """
    chords = _chords(events)
    if not chords:
        return {}
    return _scores(chords, _section_endings(events, sections), bars, len(sections), TONIC_MIN_SHARE)


def _set_share(chords: Sequence[_Chord], major_tonic: int, total: float) -> float:
    """Time share of chords diatonic to the major key on `major_tonic`: full credit with the
    diatonic quality, half for a diatonic root of the wrong quality, none otherwise."""
    credit = 0.0
    for chord in chords:
        quality = _DIATONIC.get((chord.root - major_tonic) % 12)
        if quality is not None:
            credit += chord.duration * (1.0 if chord.triad == quality else 0.5)
    return credit / total if total > 0 else 0.0


def pair_shares(events: Sequence[ChordEvent], candidates: Sequence[str]) -> dict[str, float]:
    """Time-weighted diatonic share of each candidate's better relative pair.

    A candidate X has two pairs: X major with its relative minor (the X-major diatonic set)
    and X minor with its relative major (the diatonic set of the major key a minor third
    up). Its share is the larger of the two.
    """
    chords = _chords(events)
    total = sum(c.duration for c in chords)
    shares: dict[str, float] = {}
    for name in candidates:
        tonic = _pitch_class(name)
        shares[name] = max(
            _set_share(chords, tonic, total), _set_share(chords, (tonic + 3) % 12, total)
        )
    return shares


def _profile_fit(tonic: str, chroma_mean: np.ndarray) -> float:
    """The better of the Krumhansl major and minor correlations at the tonic."""
    chroma = np.asarray(chroma_mean, dtype=float)
    pc = _pitch_class(tonic)
    return max(
        _corr(chroma, np.roll(KRUMHANSL_MAJOR, pc)), _corr(chroma, np.roll(KRUMHANSL_MINOR, pc))
    )


def _winner(values: dict[str, float]) -> tuple[str, float, str | None]:
    """(best, margin over the runner-up, runner-up); a sole entry's margin is its value."""
    ranked = sorted(values.items(), key=lambda kv: (-kv[1], _pitch_class(kv[0])))
    best, value = ranked[0]
    if len(ranked) == 1:
        return best, value, None
    return best, value - ranked[1][1], ranked[1][0]


def pair_rule(
    events: Sequence[ChordEvent], candidates: Sequence[str], chroma_mean: np.ndarray
) -> tuple[str, float, str | None]:
    """(winner, margin, runner-up) by pair share; shares within `PAIR_TIE` of the best are
    decided by the stem chroma's better Krumhansl correlation at each tonic.

    The margin is the share difference between the winner and the best other candidate;
    a sole candidate's margin is its share.
    """
    shares = pair_shares(events, candidates)
    best = max(shares.values())
    tied = [name for name, share in shares.items() if best - share < PAIR_TIE]
    winner = max(tied, key=lambda name: (_profile_fit(name, chroma_mean), shares[name]))
    others = {name: share for name, share in shares.items() if name != winner}
    if not others:
        return winner, shares[winner], None
    runner_up = _winner(others)[0]
    return winner, abs(shares[winner] - others[runner_up]), runner_up


def decide_tonic(
    events: Sequence[ChordEvent],
    bars: Sequence[Bar],
    sections: Sequence[Section],
    chroma_mean: np.ndarray,
    mix_tonic: str | None = None,
) -> TonicDecision | None:
    """The tonic by two of three votes: the score, the pair rule and the mix estimate.

    1. A score margin under `KEY_TIE_MARGIN`: the pair rule decides, weighing only the
       candidates whose score is within `KEY_TIE_MARGIN` of the top (`decided_by` "pair rule").
    2. Otherwise, when the score and the pair rule over every candidate name one tonic, that
       tonic ("agreement").
    3. Otherwise the mix's tonic decides between the two when it names one of them ("mix");
       when it names neither, or there is none, the score's tonic leads ("score").

    Under 2 and 3 the margin is the score's (clear of `KEY_TIE_MARGIN`); when the mix picks
    the pair rule's tonic, the score's tonic is the runner-up. When no root reaches
    `TONIC_MIN_SHARE`, every root is a candidate. None without chords.
    """
    chords = _chords(events)
    if not chords:
        return None
    endings = _section_endings(events, sections)
    scores = _scores(chords, endings, bars, len(sections), TONIC_MIN_SHARE) or _scores(
        chords, endings, bars, len(sections), 0.0
    )
    if not scores:
        return None
    score_tonic, margin, runner_up = _winner(scores)
    pair_tonic, pair_margin, _ = pair_rule(events, list(scores), chroma_mean)
    if runner_up is not None and margin < KEY_TIE_MARGIN:
        top = scores[score_tonic]
        close = [name for name, score in scores.items() if top - score < KEY_TIE_MARGIN]
        tonic, margin, runner_up = pair_rule(events, close, chroma_mean)
        return TonicDecision(
            tonic, margin, runner_up, "pair rule", pair_tonic, pair_margin, score_tonic,
            "pair rule",
        )
    tonic = score_tonic
    decided_by: Literal["agreement", "mix", "score"] = "score"
    if pair_tonic == score_tonic:
        decided_by = "agreement"
    elif mix_tonic in (score_tonic, pair_tonic):
        decided_by = "mix"
        if mix_tonic == pair_tonic:
            tonic, runner_up = pair_tonic, score_tonic
    return TonicDecision(
        tonic, margin, runner_up, "score", pair_tonic, pair_margin, score_tonic, decided_by
    )


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation; 0 for a flat vector, which has none."""
    if np.ptp(a) <= 0 or np.ptp(b) <= 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def mode_at(tonic: str, chroma_mean: np.ndarray) -> tuple[Literal["major", "minor"], float]:
    """The sign of the Krumhansl major-minus-minor correlation at the tonic, and its size."""
    chroma = np.asarray(chroma_mean, dtype=float)
    pc = _pitch_class(tonic)
    diff = _corr(chroma, np.roll(KRUMHANSL_MAJOR, pc)) - _corr(
        chroma, np.roll(KRUMHANSL_MINOR, pc)
    )
    return ("major" if diff >= 0 else "minor"), float(abs(diff))


def tonic_chord_mode(
    tonic: str, events: Sequence[ChordEvent]
) -> Literal["major", "minor"] | None:
    """The quality holding more of the tonic root's chord time, each chord by its triad (X:7,
    X:9 and X:maj6 major; X:min7, X:min9 and X:minmaj7 minor); None when neither holds more.
    Suspended, diminished and power chords count for neither."""
    pc = _pitch_class(tonic)
    major = minor = 0.0
    for chord in _chords(events):
        if chord.root != pc:
            continue
        if chord.triad == "maj":
            major += chord.duration
        elif chord.triad == "min":
            minor += chord.duration
    if major > minor:
        return "major"
    if minor > major:
        return "minor"
    return None


def key_and_decision(
    events: Sequence[ChordEvent],
    bars: Sequence[Bar],
    sections: Sequence[Section],
    chroma_mean: np.ndarray,
    mix_key: Key,
) -> tuple[Key, TonicDecision | None]:
    """`key_from_chords` with the tonic decision behind it (None when the mix key stands)."""
    if len(_chords(events)) < MIN_CHORD_EVENTS:
        return mix_key, None
    # the mix may hear another mode; only its tonic votes
    decision = decide_tonic(events, bars, sections, chroma_mean, mix_key.tonic)
    if decision is None:
        return mix_key, None
    mode, mode_margin = _mode_of(decision.tonic, chroma_mean, events)
    votes = TonicVotes(
        score=decision.score_tonic, pair=decision.pair_tonic, mix=mix_key.tonic,
        decided_by=decision.decided_by,
    )
    key = Key(
        tonic=decision.tonic, mode=mode, confidence=mode_margin, method="chords_stems",
        margin=decision.margin, mode_margin=mode_margin, runner_up=decision.runner_up,
        mix=mix_key, pair_tonic=decision.pair_tonic, tonic_votes=votes,
    )
    other = hedge_tonic(key)
    if other is not None:  # the other tonic the sheet names carries its own mode
        key = key.model_copy(update={"hedge_mode": _mode_of(other, chroma_mean, events)[0]})
    return key, decision


def _mode_of(
    tonic: str, chroma_mean: np.ndarray, events: Sequence[ChordEvent]
) -> tuple[Literal["major", "minor"], float]:
    """The mode at a tonic by the chroma, and its margin; under `MODE_TIE_MARGIN` the tonic's
    own chords decide."""
    mode, margin = mode_at(tonic, chroma_mean)
    if margin < MODE_TIE_MARGIN:
        mode = tonic_chord_mode(tonic, events) or mode
    return mode, margin


def key_from_chords(
    events: Sequence[ChordEvent],
    bars: Sequence[Bar],
    sections: Sequence[Section],
    chroma_mean: np.ndarray,
    mix_key: Key,
) -> Key:
    """The key with its tonic from the chord stream and its mode from the harmonic chroma.

    With fewer than `MIN_CHORD_EVENTS` chord events the mix estimate is returned as it is.
    When the mode margin is under `MODE_TIE_MARGIN`, the tonic's own chords decide.
    """
    return key_and_decision(events, bars, sections, chroma_mean, mix_key)[0]


# --- Tonic power chords: a minor tonic played as root and fifth reads as major ---
#
# The chord model has no power-chord class, so it prints a minor-key riff on root and fifth as
# the tonic's major (Pour Some Sugar On Me: C#:maj for 41 percent of chord time).

# The harmonic chroma must prefer minor at the tonic by at least this much (the Krumhansl
# major-minus-minor difference; Pour Some Sugar On Me 0.423, the three major songs 0.2 to 0.3
# in the other direction).
POWER_MODE_MARGIN = 0.2
# The tonic root must hold at least this share of non-N chord time, so a one-bar Picardy or
# borrowed major tonic is left alone.
POWER_MIN_SHARE = 0.2


def power_chord_events(
    events: Sequence[ChordEvent], key: Key, chroma_mean: np.ndarray
) -> list[int]:
    """Indices of the tonic root's plain major events when the tonic is a power chord, else `[]`.

    Only the plain major label counts as major here (`X:maj`, see `plain_major_root`): a
    seventh, an added degree or a slash chord has more than root and fifth in its label.
    All four hold: the key is minor; the tonic root's chord time as plain major exceeds its
    time as minor; the harmonic chroma prefers minor at the tonic by at least
    `POWER_MODE_MARGIN`; and the tonic root holds at least `POWER_MIN_SHARE` of non-N chord
    time.
    """
    if key.mode != "minor":
        return []
    tonic = _pitch_class(key.tonic)
    total = root_time = major = minor = 0.0
    majors: list[int] = []
    for index, event in enumerate(events):
        chords = _chords([event])
        if not chords:
            continue
        chord = chords[0]
        total += chord.duration
        if chord.root != tonic:
            continue
        root_time += chord.duration
        if chord.plain:
            major += chord.duration
            majors.append(index)
        elif chord.triad == "min":
            minor += chord.duration
    if not majors or major <= minor or root_time < POWER_MIN_SHARE * total:
        return []
    mode, margin = mode_at(key.tonic, chroma_mean)
    if mode != "minor" or margin < POWER_MODE_MARGIN:
        return []
    return majors


def _close(key: Key) -> bool:
    return key.margin is not None and key.margin < KEY_HEDGE_MARGIN


def _mix_disagrees(key: Key) -> bool:
    return key.mix is not None and key.mix.tonic != key.tonic


def _losing_chord_rule(key: Key) -> str | None:
    """The tonic of the chord rule (score or pair rule) that lost when the two disagreed and
    the mix or the score settled it (spec 1.5, section 6.1, rule 3); None otherwise, and for
    a file written before 1.5, which has no votes."""
    votes = key.tonic_votes
    if votes is None or votes.decided_by not in ("mix", "score"):
        return None
    loser = votes.pair if key.tonic == votes.score else votes.score
    return loser if loser is not None and loser != key.tonic else None


def hedged(key: Key) -> bool:
    """A close call on the tonic, a chord rule that lost, or a mix estimate that names
    another tonic."""
    return _close(key) or _hedge(key) is not None


def _hedge(key: Key) -> tuple[str, Literal["runner_up", "chord rule", "mix"]] | None:
    """The other tonic and where it comes from, by three rungs in order: a close margin names
    the runner-up; a chord rule that lost names its tonic; a mix estimate that differs names
    its tonic."""
    if _close(key) and key.runner_up is not None:
        return key.runner_up, "runner_up"
    loser = _losing_chord_rule(key)
    if loser is not None:
        return loser, "chord rule"
    if _mix_disagrees(key):
        return key.mix.tonic, "mix"
    return None


def hedge_tonic(key: Key) -> str | None:
    """The other tonic a hedged key names: the runner-up when the margin is close, else the
    losing chord rule's tonic when the mix or the score settled a disagreement, else the
    mix's tonic when the mix disagrees."""
    hedge = _hedge(key)
    return hedge[0] if hedge is not None else None


def hedge_text(key: Key) -> str | None:
    """The other key a hedged key names, `C major`, with its own mode; None when not hedged.

    The mode is the one stored at harmony time (`Key.hedge_mode`). A file written before it
    was stored falls back to the mix estimate's mode for a mix hedge and to the key's own
    mode for a runner-up; such a file has no votes, so it never reaches the chord-rule rung."""
    hedge = _hedge(key)
    if hedge is None:
        return None
    other, source = hedge
    mode = key.hedge_mode
    if mode is None:
        mode = key.mix.mode if source == "mix" and key.mix is not None else key.mode
    return f"{other} {mode}"


def key_text(key: Key) -> str:
    """`D major`, or `A minor (or C major)` when hedged."""
    text = f"{key.tonic} {key.mode}"
    other = hedge_text(key)
    return f"{text} (or {other})" if other is not None else text


def pair_rule_note(decision: TonicDecision | None) -> str:
    """The pair rule over every candidate, for the manifest: `F by 0.083`, or `tie, F by
    chroma` when the pair shares were within `PAIR_TIE` and the stem chroma chose."""
    if decision is None:
        return "none"
    if decision.pair_margin < PAIR_TIE:
        return f"tie, {decision.pair_tonic} by chroma"
    return f"{decision.pair_tonic} by {decision.pair_margin:.3f}"


def tonic_votes_note(key: Key) -> str:
    """The three tonic votes, for the manifest: `score C, pair F, mix F, decided by mix`; a
    missing vote prints `none`, and a key without votes (the mix's own, or a file before
    1.5) is `none`."""
    votes = key.tonic_votes
    if votes is None:
        return "none"
    return (
        f"score {votes.score or 'none'}, pair {votes.pair or 'none'}, "
        f"mix {votes.mix or 'none'}, decided by {votes.decided_by or 'none'}"
    )
