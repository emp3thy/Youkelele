"""Fill no-chord bars with one of the song's own chords where the band is playing.

The chord recogniser labels whole intros and solos `N` while the guitar and bass
are clearly playing. A bar whose events are all `N` is filled when the summed
harmonic stems are loud enough relative to the song's chorded bars and the bar's
chroma clearly matches the triad of one chord the song already uses. Matching is
restricted to the song's own chord set, so a fill never adds a new chord.
"""

from __future__ import annotations

from collections.abc import Sequence

import mir_eval.chord
import numpy as np

from youkelele.music.chroma import chroma_of
from youkelele.music.triads import to_triad
from youkelele.schemas import Bar, ChordEvent

# Measured on four real runs: docs/superpowers/specs/2026-10-03-v1-2-fill-measurements.md.
# Energy is the bar's RMS over the median RMS of the bars holding a chord. Silent-stem
# all-N bars reach 0.111 (Summer of '69 bar 120). Pour Some Sugar On Me bar 15 (0.163, a
# noise-floor bar with a flat chroma) cannot be told from bar 67 (0.162) on energy, so
# both stay N; the quietest filled bar is 0.235 (Pour Some Sugar On Me bar 68).
FILL_MIN_ENERGY = 0.2
# The best match of any unpitched or off-set control bar is 0.297 (Wet Leg bar 112, a drone
# outside the song's chords); the weakest filled match is 0.334 (Pour Some Sugar On Me
# bar 74). On bars the recogniser labelled with one chord, agreement with its triad is
# 96.4% at 0.32 against 96.9% at 0.4 (margin 0.05 both).
FILL_MIN_MATCH = 0.32
# The one bar that passes energy and match but is ambiguous has margin 0.027 (Pour Some
# Sugar On Me bar 46, B against F#); the smallest filled margin is 0.057 (bar 70).
FILL_MIN_MARGIN = 0.05

_NO_CHORD = ("N", "X")
_EPS = 1e-6


def chord_template(label: str) -> np.ndarray | None:
    """12-bin 0/1 triad template rotated to the chord's root; None for N, X or bad labels."""
    if label in _NO_CHORD:
        return None
    try:
        _root, quality, _degrees, _bass = mir_eval.chord.split(label, reduce_extended_chords=True)
        mir_eval.chord.quality_to_bitmap(quality)  # rejects an unknown quality
        root, quality, _degrees, _bass = mir_eval.chord.split(to_triad(label))
        bitmap = mir_eval.chord.quality_to_bitmap(quality)
        semitone = mir_eval.chord.pitch_class_to_semitone(root)
    except (mir_eval.chord.InvalidChordException, ValueError, IndexError):
        return None
    return np.roll(np.asarray(bitmap, dtype=float), semitone)


def bar_chroma(y: np.ndarray, sr: int, bars: Sequence[Bar]) -> np.ndarray:
    """Mean CQT chroma per bar (bars x 12); zeros for a bar with no frames.

    A thin wrapper: the harmony stage computes the chroma once with
    `music.chroma.harmonic_chroma` and reads its `bar_means` directly.
    """
    if not bars:
        return np.zeros((0, 12))
    return chroma_of(y, sr).bar_means(bars)


def bar_energy(y: np.ndarray, sr: int, bars: Sequence[Bar]) -> np.ndarray:
    """RMS of the signal within each bar; zero for a bar with no samples."""
    out = np.zeros(len(bars))
    for i, bar in enumerate(bars):
        seg = y[max(0, int(bar.start * sr)) : max(0, int(bar.end * sr))]
        if len(seg):
            out[i] = float(np.sqrt(np.mean(np.square(seg, dtype=np.float64))))
    return out


def _overlap(event: ChordEvent, bar: Bar) -> float:
    return min(event.end, bar.end) - max(event.start, bar.start)


def chorded_energy_reference(
    events: Sequence[ChordEvent], bars: Sequence[Bar], energy: np.ndarray
) -> float | None:
    """Median energy of the bars holding a chord; None when no bar does or it is silent.

    The fill and the key's chroma mask both measure a bar's energy against this.
    """
    chorded = [
        i for i, bar in enumerate(bars)
        if any(e.label not in _NO_CHORD and _overlap(e, bar) > _EPS for e in events)
    ]
    if not chorded:
        return None
    reference = float(np.median([energy[i] for i in chorded]))
    return reference if reference > 0 else None


def _split_n_at_bars(events: Sequence[ChordEvent], bars: Sequence[Bar]) -> list[ChordEvent]:
    out: list[ChordEvent] = []
    for event in events:
        covered = [bar for bar in bars if _overlap(event, bar) > _EPS]
        if event.label != "N" or len(covered) < 2:
            out.append(event)
            continue
        for bar in covered:
            first = bar is covered[0]
            out.append(
                event.model_copy(
                    update={
                        "bar": event.bar if first else bar.index,
                        "beat": event.beat if first else 0,
                        "start": max(event.start, bar.start),
                        "end": min(event.end, bar.end),
                    }
                )
            )
    return out


def _song_chords(events: Sequence[ChordEvent]) -> list[tuple[str, np.ndarray]]:
    """One (label, template) per distinct triad; the label is the longest-held one."""
    held: dict[str, float] = {}
    for event in events:
        if event.label not in _NO_CHORD and chord_template(event.label) is not None:
            held[event.label] = held.get(event.label, 0.0) + (event.end - event.start)
    by_triad: dict[str, str] = {}
    for label in held:
        triad = to_triad(label)
        if triad not in by_triad or held[label] > held[by_triad[triad]]:
            by_triad[triad] = label
    return [(label, chord_template(label)) for label in by_triad.values()]


def _best_match(
    chroma: np.ndarray, chords: Sequence[tuple[str, np.ndarray]]
) -> tuple[str, float, float] | None:
    """(label, best correlation, runner-up correlation), or None for a flat chroma."""
    if np.ptp(chroma) <= 0:
        return None
    scores = sorted(
        ((float(np.corrcoef(chroma, tpl)[0, 1]), label) for label, tpl in chords), reverse=True
    )
    runner_up = scores[1][0] if len(scores) > 1 else -1.0
    return scores[0][1], scores[0][0], runner_up


def fill_silent_bars(
    events: list[ChordEvent], bars: Sequence[Bar], chroma: np.ndarray, energy: np.ndarray
) -> list[ChordEvent]:
    """Split `N` events at bar boundaries, then fill all-`N` bars that pass the three tests.

    A bar is a candidate when every event overlapping it is `N`. It is filled when its
    energy is at least `FILL_MIN_ENERGY` times the median energy of the bars that hold
    a chord, and its chroma correlates with one of the song's own triads at least
    `FILL_MIN_MATCH`, beating the runner-up triad by at least `FILL_MIN_MARGIN`.
    Labels that reduce to the same triad compete as one candidate (the longest-held
    label is used). A song with only one triad has no runner-up, so the margin test
    passes on the match alone.
    """
    split = _split_n_at_bars(events, bars)
    chords = _song_chords(split)
    if not chords:
        return split

    overlapping = [[e for e in split if _overlap(e, bar) > _EPS] for bar in bars]
    reference = chorded_energy_reference(split, bars, energy)
    if reference is None:
        return split

    fills: dict[int, ChordEvent] = {}
    for i, (bar, evs) in enumerate(zip(bars, overlapping)):
        if not evs or any(e.label != "N" for e in evs):
            continue
        if energy[i] < FILL_MIN_ENERGY * reference:
            continue
        match = _best_match(np.asarray(chroma[i], dtype=float), chords)
        if match is None:
            continue
        label, best, runner_up = match
        if best < FILL_MIN_MATCH or best - runner_up < FILL_MIN_MARGIN:
            continue
        fills[i] = ChordEvent(
            bar=bar.index, beat=0, start=bar.start, end=bar.end, label=label,
            triad=to_triad(label), confidence=best, filled=True,
        )

    if not fills:
        return split
    out: list[ChordEvent] = []
    placed: set[int] = set()
    for event in split:
        i = next((b for b in fills if _overlap(event, bars[b]) > _EPS), None)
        if i is None:
            out.append(event)
        elif i not in placed:
            out.append(fills[i])
            placed.add(i)
    return out
