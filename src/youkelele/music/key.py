"""The song's key.

1.4: the tonic comes from the chord stream and the mode from the harmonic-stem chroma
(`key_from_chords`). The 24-way Krumhansl-Kessler search on the mix (`estimate_key`)
is kept as the fallback for songs with too few chords and for comparison.
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
from youkelele.schemas import Bar, ChordEvent, Key, Section

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
# Under this deciding margin the sheet names the runner-up as well.
KEY_HEDGE_MARGIN = 0.05
# Under this mode margin the tonic's own chords decide (Fame: 0.003 at F).
MODE_TIE_MARGIN = 0.05
# With fewer chord events than this the mix estimate stands.
MIN_CHORD_EVENTS = 4

_NO_CHORD = ("N", "X")
# The diatonic triads of a major key by semitones above its tonic.
_DIATONIC = {0: "maj", 2: "min", 4: "min", 5: "maj", 7: "maj", 9: "min", 11: "dim"}
# Sevenths count by their third; every other quality is ignored for the tonic's mode.
_MAJOR_QUALITIES = frozenset({"maj", "7", "maj7"})
_MINOR_QUALITIES = frozenset({"min", "min7"})


@dataclass(frozen=True)
class _Chord:
    root: int  # pitch class
    quality: str  # the label's own quality, e.g. "7"
    triad: str  # the reduced triad quality, e.g. "maj"
    duration: float
    bar: int


@dataclass(frozen=True)
class TonicDecision:
    tonic: str
    margin: float  # the deciding margin
    runner_up: str | None
    rule: Literal["score", "pair rule"]
    pair_tonic: str  # the pair rule's winner, computed whether or not it decided
    pair_margin: float


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
        out.append(_Chord(pc, quality, triad, event.end - event.start, event.bar))
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


def pair_shares(events: Sequence[ChordEvent], candidates: Sequence[str]) -> dict[str, float]:
    """Time-weighted diatonic share of each candidate's relative-major pair.

    For a candidate X the pair is X major and its relative minor: a chord whose root is
    diatonic to X major counts in full when its triad has the diatonic quality and half
    otherwise; any other chord counts nothing.
    """
    chords = _chords(events)
    total = sum(c.duration for c in chords)
    shares: dict[str, float] = {}
    for name in candidates:
        tonic = _pitch_class(name)
        credit = 0.0
        for chord in chords:
            quality = _DIATONIC.get((chord.root - tonic) % 12)
            if quality is not None:
                credit += chord.duration * (1.0 if chord.triad == quality else 0.5)
        shares[name] = credit / total if total > 0 else 0.0
    return shares


def _winner(values: dict[str, float]) -> tuple[str, float, str | None]:
    """(best, margin over the runner-up, runner-up); a sole entry's margin is its value."""
    ranked = sorted(values.items(), key=lambda kv: (-kv[1], _pitch_class(kv[0])))
    best, value = ranked[0]
    if len(ranked) == 1:
        return best, value, None
    return best, value - ranked[1][1], ranked[1][0]


def decide_tonic(
    events: Sequence[ChordEvent], bars: Sequence[Bar], sections: Sequence[Section]
) -> TonicDecision | None:
    """The tonic by score, or by the pair rule when the score margin is under `KEY_TIE_MARGIN`.

    When no root reaches `TONIC_MIN_SHARE`, every root is a candidate. None without chords.
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
    tonic, margin, runner_up = _winner(scores)
    pair_tonic, pair_margin, pair_runner_up = _winner(pair_shares(events, list(scores)))
    if runner_up is not None and margin < KEY_TIE_MARGIN:
        return TonicDecision(
            pair_tonic, pair_margin, pair_runner_up, "pair rule", pair_tonic, pair_margin
        )
    return TonicDecision(tonic, margin, runner_up, "score", pair_tonic, pair_margin)


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
    """The quality holding more of the tonic root's chord time, sevenths by their third
    (X:7 and X:maj7 major, X:min7 minor); None when neither holds more."""
    pc = _pitch_class(tonic)
    major = minor = 0.0
    for chord in _chords(events):
        if chord.root != pc:
            continue
        if chord.quality in _MAJOR_QUALITIES:
            major += chord.duration
        elif chord.quality in _MINOR_QUALITIES:
            minor += chord.duration
    if major > minor:
        return "major"
    if minor > major:
        return "minor"
    return None


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
    if len(_chords(events)) < MIN_CHORD_EVENTS:
        return mix_key
    decision = decide_tonic(events, bars, sections)
    if decision is None:
        return mix_key
    mode, mode_margin = mode_at(decision.tonic, chroma_mean)
    if mode_margin < MODE_TIE_MARGIN:
        mode = tonic_chord_mode(decision.tonic, events) or mode
    return Key(
        tonic=decision.tonic, mode=mode, confidence=mode_margin, method="chords_stems",
        margin=decision.margin, mode_margin=mode_margin, runner_up=decision.runner_up,
        mix=mix_key,
    )


def hedged(key: Key) -> bool:
    """A close call on the tonic, or a mix estimate that names another tonic."""
    close = key.margin is not None and key.margin < KEY_HEDGE_MARGIN
    return close or (key.mix is not None and key.mix.tonic != key.tonic)


def hedge_tonic(key: Key) -> str | None:
    """The other tonic a hedged key names: the runner-up, else the mix's tonic."""
    if not hedged(key):
        return None
    if key.runner_up is not None:
        return key.runner_up
    return key.mix.tonic if key.mix is not None else None


def key_text(key: Key) -> str:
    """`D major`, or `G major (or D major)` when hedged."""
    text = f"{key.tonic} {key.mode}"
    other = hedge_tonic(key)
    return f"{text} (or {other} {key.mode})" if other is not None else text
