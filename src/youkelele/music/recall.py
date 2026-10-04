"""Recall gate: recover the strums of loud sustained sections from a high-band onset list.

Today's detector uses one global threshold on a full-band envelope, set by the
sharpest attacks in the song, so the re-attacks of a ringing distorted chord
fall under it. Per section, where today's strikes are sparse, onsets from an
envelope restricted to the high band are added, and the union is kept only
when it is measurably better. Every constant is measured on the five
validation songs (docs/superpowers/specs/2026-10-04-v1-3-recall-measurements.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from youkelele.music.as_played import section_summary
from youkelele.music.onsets import Onsets, grid_fit, quantise_bar
from youkelele.schemas import Bar, Meter

HIGH_BAND_FMIN = 3000.0  # the choruses are recovered from 2500 to 4000 Hz, not at 2000 (measurements doc, sections 1 and 3)
SPARSE_SHARE = 0.4  # 0.4 and 0.5 both pass; 0.4 is the conservative one judged by ear (measurements doc, sections 1 and 3)
MERGE_MS = 60.0  # a high-band onset within 60 ms of one of today's is the same strike (measurements doc, section 1)
MIN_GAIN = 1.0  # 0.5 gives the same decisions; the outro and intro gain 0.1 to 0.3 (measurements doc, sections 1 and 3)
FIT_TOLERANCE = 0.05  # the lowest accepted section fit is 0.02 under its song's (measurements doc, section 5.1)
SILENT_BAR_SHARE = 0.25  # silent entry bars sit at 0.135 or less, struck bars at 0.446 or more (measurements doc, section 5.2)


@dataclass
class SectionDecision:
    accepted: bool
    before: float  # strikes per bar today
    after: float  # strikes per bar with the union (equal to before when the union was not tried)
    reason: str  # "accepted" or the first check that failed or skipped the section


def eighth_grid(slots_per_bar: int, meter: Meter) -> bool:
    return slots_per_bar == meter.numerator * 2


def _take(onsets: Onsets, mask: np.ndarray) -> Onsets:
    return Onsets(times=onsets.times[mask], centroid=onsets.centroid[mask], zcr=onsets.zcr[mask])


def merge_onsets(base: Onsets, extra: Onsets, merge_ms: float, keep: np.ndarray) -> tuple[Onsets, np.ndarray]:
    """`base` plus the `keep` entries of `extra` that lie more than `merge_ms` from every base onset.

    Returns the union sorted by time and a boolean array marking the added entries.
    """
    allowed = np.asarray(keep, dtype=bool).copy()
    if len(base.times) and len(extra.times):
        nearest = np.min(np.abs(extra.times[:, None] - base.times[None, :]), axis=1)
        allowed &= nearest > merge_ms / 1000.0
    added_part = _take(extra, allowed)
    times = np.concatenate([base.times, added_part.times])
    order = np.argsort(times, kind="stable")
    union = Onsets(
        times=times[order],
        centroid=np.concatenate([base.centroid, added_part.centroid])[order],
        zcr=np.concatenate([base.zcr, added_part.zcr])[order],
    )
    added = np.concatenate([np.zeros(len(base.times), dtype=bool), np.ones(len(added_part.times), dtype=bool)])
    return union, added[order]


def silent_bar_mask(y: np.ndarray, sr: int, bars: Sequence[Bar], share: float) -> np.ndarray:
    """True where a bar's RMS is below `share` x the median bar RMS over `bars`.

    A silent stretch (median 0) marks nothing, so nothing divides by zero.
    """
    rms = np.zeros(len(bars))
    for k, bar in enumerate(bars):
        part = y[int(round(bar.start * sr)):int(round(bar.end * sr))]
        rms[k] = float(np.sqrt(np.mean(np.square(part, dtype=np.float64)))) if len(part) else 0.0
    if not len(bars):
        return np.zeros(0, dtype=bool)
    return rms < share * float(np.median(rms))


def bar_index(times: np.ndarray, bars: Sequence[Bar], slots_per_bar: int) -> np.ndarray:
    """Index into `bars` of the bar whose slots each onset quantises into, or -1.

    A bar's window is shifted back by half a slot, as in `quantise_bar`, so an
    onset just before a downbeat belongs to the bar that starts there.
    """
    out = np.full(len(times), -1, dtype=int)
    for k, bar in enumerate(bars):
        half = (bar.end - bar.start) / slots_per_bar / 2
        out[(times >= bar.start - half) & (times < bar.end - half)] = k
    return out


def _strikes_and_agreement(onsets: Onsets, bars: Sequence[Bar], slots_per_bar: int, meter: Meter) -> tuple[float, float]:
    """Strikes per bar and mean Jaccard of the bars to their own vote (the section pattern's vote).

    The mute rule is left out: the gate judges where strikes land, not their timbre.
    """
    muted = np.zeros(len(onsets.times), dtype=bool)
    classes = [quantise_bar(onsets, muted, bar, slots_per_bar) for bar in bars]
    strikes = float(np.mean([sum(1 for c in bar if c != "-") for bar in classes]))
    _, agreement, _, _ = section_summary(classes, slots_per_bar, meter)
    return strikes, agreement


def gate_section(
    base: Onsets,
    extra: Onsets,
    y: np.ndarray,
    sr: int,
    bars: Sequence[Bar],
    slots_per_bar: int,
    song_fit: float,
    meter: Meter,
) -> tuple[Onsets, np.ndarray, SectionDecision]:
    """The section's onsets (today's, or the union with the high band) and which of them were added.

    `base` and `extra` may cover the whole song; only onsets inside `bars` are used
    and returned. The union is kept only when strikes per bar rise by `MIN_GAIN`,
    the agreement with the section's own vote does not fall, raw onsets per bar
    stay at or under the slot count and the section's grid fit stays within
    `FIT_TOLERANCE` of the song's.
    """
    own = _take(base, bar_index(base.times, bars, slots_per_bar) >= 0)
    unchanged = np.zeros(len(own.times), dtype=bool)
    if not bars:
        return own, unchanged, SectionDecision(False, 0.0, 0.0, "no onsets")
    before, agreement_before = _strikes_and_agreement(own, bars, slots_per_bar, meter)
    if not eighth_grid(slots_per_bar, meter):
        return own, unchanged, SectionDecision(False, before, before, "sixteenth grid")
    if len(own.times) == 0:
        return own, unchanged, SectionDecision(False, 0.0, 0.0, "no onsets")
    if before >= SPARSE_SHARE * slots_per_bar:
        return own, unchanged, SectionDecision(False, before, before, "dense")

    idx = bar_index(extra.times, bars, slots_per_bar)
    silent = silent_bar_mask(y, sr, bars, SILENT_BAR_SHARE)
    keep = (idx >= 0) & ~silent[np.clip(idx, 0, None)]
    union, added = merge_onsets(own, extra, MERGE_MS, keep)
    after, agreement_after = _strikes_and_agreement(union, bars, slots_per_bar, meter)

    if after < before + MIN_GAIN:
        reason = "gain"
    elif agreement_after < agreement_before:
        reason = "jaccard"
    elif len(union.times) / len(bars) > slots_per_bar:
        reason = "raw"
    elif grid_fit(union, bars, slots_per_bar) < song_fit - FIT_TOLERANCE:
        reason = "fit"
    else:
        return union, added, SectionDecision(True, before, after, "accepted")
    return own, unchanged, SectionDecision(False, before, after, reason)
