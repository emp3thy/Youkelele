"""Stroke decay and the per-section ring flag.

A strummed stroke that rings keeps sounding into the empty slots after it; a
muted one dies within a slot. The decay is measured on the signal and the
section is called ringing when its median stroke decays slowly. Pure numpy.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

# Song medians on eight real songs: 1.8 to 2.7 dB per slot ringing, 8.3 to 8.7 muted.
RING_SECTION_DB = 5  # a section whose median decay is under this rings
RING_MIN_GAP_SLOTS = 1.5  # a next stroke nearer than this cuts the decay short, so it is not measured
_FRAME_S = 0.010  # RMS frame, long enough to span a few cycles of a low string
_HOP_S = 0.005  # frames overlap by half, so the peak is found to within 5 ms
_EPS = 1e-9


def _frame_rms(y: np.ndarray, start: int, length: int) -> float:
    return float(np.sqrt(np.mean(np.square(y[start : start + length], dtype=np.float64))))


def stroke_decay_db(
    y: np.ndarray, sr: int, onset: float, next_onset: float | None, slot_seconds: float
) -> float | None:
    """dB lost in the first slot after the stroke's peak, or None when it cannot be measured.

    The peak is the loudest 10 ms frame (hopped 5 ms) within half a slot of the
    onset; the decay compares it with the frame one slot later, clipped at 0.
    None when the next onset is nearer than 1.5 slots or the signal ends first.
    """
    if next_onset is not None and next_onset - onset < RING_MIN_GAP_SLOTS * slot_seconds:
        return None
    frame = max(int(round(_FRAME_S * sr)), 1)
    hop = max(int(round(_HOP_S * sr)), 1)
    first = int(round(onset * sr))
    last = int(round((onset + slot_seconds / 2) * sr))
    starts = np.arange(max(first, 0), last + 1, hop)
    starts = starts[starts + frame <= len(y)]
    if len(starts) == 0:
        return None
    rms = np.array([_frame_rms(y, int(s), frame) for s in starts])
    peak = int(np.argmax(rms))
    if rms[peak] <= _EPS:
        return None
    later = int(starts[peak]) + int(round(slot_seconds * sr))
    if later + frame > len(y):
        return None
    after = max(_frame_rms(y, later, frame), _EPS)
    return max(0.0, float(20 * np.log10(rms[peak] / after)))


def section_rings(decays: Sequence[float | None]) -> tuple[bool, float | None]:
    """(median < RING_SECTION_DB, median) over the measured decays; (True, None) with none."""
    values = [d for d in decays if d is not None]
    if not values:
        return True, None
    median = float(np.median(values))
    return median < RING_SECTION_DB, median
