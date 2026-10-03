"""Strum onsets, source selection, slot quantisation and the mute rule.

Every threshold here was measured on five real songs in the audio spikes
(docs/superpowers/specs/2026-10-03-spike-audio.md and ...-round2.md).
Only `detect_onsets` calls librosa; everything else is pure numpy.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from youkelele.schemas import Bar, Meter, Slot

StrikeClass = Literal["S", "-", "x"]
Source = Literal["guitar_stem", "other_stem", "mix"]

SOURCE_MIN_RATIO = 0.05  # below this the louder stem is too quiet; use the mix
SECTION_MIN_RATIO = 0.10  # a section's stem below this share of the mix has no instrument
ODD_SIXTEENTH_SHARE = 0.25  # more than this share of odd sixteenths selects the sixteenth grid
SIXTEENTH_MIN_MS = 105.0  # a sixteenth shorter than this is not a plausible strum slot
GRID_FIT_TOLERANCE = 0.15  # an onset within this share of a slot width fits the grid
MUTE_CENTROID = 0.85  # muted when centroid < 0.85 x song median ...
MUTE_ZCR = 0.65  # ... and zero-crossing rate < 0.65 x song median
_EPS = 1e-9


@dataclass
class Onsets:
    times: np.ndarray
    centroid: np.ndarray
    zcr: np.ndarray


def detect_onsets(y: np.ndarray, sr: int) -> Onsets:
    """librosa's default onset detector, with centroid and zcr at each onset frame."""
    import librosa

    times = np.asarray(librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=False), dtype=float)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    if len(times) == 0:
        return Onsets(times=times, centroid=np.zeros(0), zcr=np.zeros(0))
    frames = np.asarray(librosa.time_to_frames(times, sr=sr), dtype=int)
    return Onsets(
        times=times,
        centroid=np.asarray(centroid[np.clip(frames, 0, len(centroid) - 1)], dtype=float),
        zcr=np.asarray(zcr[np.clip(frames, 0, len(zcr) - 1)], dtype=float),
    )


def _rms(y: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(y, dtype=np.float64)))) if len(y) else 0.0


def rms_ratio(part: np.ndarray, mix: np.ndarray) -> float:
    return _rms(part) / max(_rms(mix), _EPS)


def choose_source(guitar: np.ndarray, other: np.ndarray, mix: np.ndarray) -> tuple[Source, np.ndarray, float]:
    """The louder of the guitar and other stems relative to the mix, or the mix below 0.05.

    The returned ratio is always the louder stem's ratio, so a mix fallback shows why.
    """
    g, o = rms_ratio(guitar, mix), rms_ratio(other, mix)
    source, y, ratio = ("guitar_stem", guitar, g) if g > o else ("other_stem", other, o)
    if ratio < SOURCE_MIN_RATIO:
        return "mix", mix, ratio
    return source, y, ratio


def section_has_instrument(stem_section: np.ndarray, mix_section: np.ndarray) -> bool:
    return rms_ratio(stem_section, mix_section) >= SECTION_MIN_RATIO


def _bar_positions(onsets: Onsets, bars: Sequence[Bar], units: int) -> np.ndarray:
    """Position of each onset inside its bar, in `units` per bar; onsets outside all bars are dropped."""
    if not bars or len(onsets.times) == 0:
        return np.zeros(0)
    starts = np.array([b.start for b in bars])
    ends = np.array([b.end for b in bars])
    idx = np.searchsorted(starts, onsets.times, side="right") - 1
    inside = (idx >= 0) & (onsets.times < ends[np.clip(idx, 0, None)])
    idx, times = idx[inside], onsets.times[inside]
    return (times - starts[idx]) / (ends[idx] - starts[idx]) * units


def choose_slots_per_bar(onsets: Onsets, bars: Sequence[Bar], meter: Meter, bpm: float) -> int:
    eighths = meter.numerator * 2
    if 60000.0 / bpm / 4 < SIXTEENTH_MIN_MS:  # sixteenths faster than a hand can strum
        return eighths
    pos = _bar_positions(onsets, bars, meter.numerator * 4)
    if len(pos) == 0:
        return eighths
    odd = np.floor(pos + 0.5).astype(int) % 2 == 1
    return eighths * 2 if float(np.mean(odd)) > ODD_SIXTEENTH_SHARE else eighths


def grid_fit(onsets: Onsets, bars: Sequence[Bar], slots_per_bar: int) -> float:
    pos = _bar_positions(onsets, bars, slots_per_bar)
    if len(pos) == 0:
        return 0.0
    return float(np.mean(np.abs(pos - np.floor(pos + 0.5)) <= GRID_FIT_TOLERANCE))


def mute_mask(onsets: Onsets, enabled: bool) -> np.ndarray:
    n = len(onsets.times)
    if not enabled or n == 0:
        return np.zeros(n, dtype=bool)
    med_c = float(np.median(onsets.centroid))
    med_z = float(np.median(onsets.zcr))
    return (onsets.centroid < MUTE_CENTROID * med_c) & (onsets.zcr < MUTE_ZCR * med_z)


def quantise_bar(onsets: Onsets, muted: np.ndarray, bar: Bar, slots_per_bar: int) -> list[StrikeClass]:
    """Each onset to its nearest slot (within half a slot); a strike beats a mute, else the first wins.

    The bar's window is shifted back by half a slot, so an onset just before the
    next downbeat counts as that bar's slot 0, not this bar's last slot.

    A struck onset overrides a muted one in the same slot: on the synthetic
    end-to-end clip the separated stem carries a quiet, dull pre-echo 25 to 50 ms
    before real strums (Demucs, unseeded random shifts, so it varies run to run);
    the mute rule marks it x and, taken first, it hid the strike and flipped the
    section pattern from D-DU-UDU to D-xU-xDU. A slot holds one stroke, and a
    real chuck has no strike after it within the slot.
    """
    width = (bar.end - bar.start) / slots_per_bar
    classes: list[StrikeClass] = ["-"] * slots_per_bar
    for t, m in zip(onsets.times, muted):
        if not bar.start - width / 2 <= t < bar.end - width / 2:
            continue
        j = int(np.floor((t - bar.start) / width + 0.5))
        j = min(max(j, 0), slots_per_bar - 1)  # floating point can land one past either edge
        if classes[j] == "-" or (classes[j] == "x" and not m):
            classes[j] = "x" if m else "S"
    return classes


def direction_for_slot(i: int, slots_per_bar: int, meter: Meter) -> Literal["D", "U"]:
    """Down on even slots (the beats on an eighth grid, the eighths on a sixteenth grid), up otherwise."""
    return "D" if i % 2 == 0 else "U"


def render_directions(classes: Sequence[StrikeClass], slots_per_bar: int, meter: Meter) -> list[Slot]:
    return [direction_for_slot(i, slots_per_bar, meter) if c == "S" else c for i, c in enumerate(classes)]
