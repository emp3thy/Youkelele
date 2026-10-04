"""Bar features, Laplacian segmentation and section labels.

Rules measured on five real songs in the grid round-three spike
(docs/superpowers/specs/2026-10-03-spike-grid-round3.md); the vocal rules on the
same songs and one blind song (version 1.4 spec, section 3.3 and assumption A4).
"""

from __future__ import annotations

import bisect
import warnings
from collections import Counter
from collections.abc import Sequence

import numpy as np

from youkelele.schemas import Bar, Section

HOP = 512
N_CHROMA = 12
MIN_K, MAX_K = 3, 6
RECURRENCE_WIDTH = 3
# recurrence_matrix needs width < (n - 1) // 2, so n >= 2 * width + 3 bars
MIN_SEGMENT_BARS = 2 * RECURRENCE_WIDTH + 3
SPLIT_SHARE = 0.6  # a cluster above this share of bars is split (k rule) or is the verse (labeller)
LOW_MARGIN_DB = 1.5
SILENCE_RMS = 1e-6  # -120 dB floor
VOCAL_BELOW_MEDIAN_DB = 12.0  # a bar this far below the median vocal level is non-vocal
VOCAL_AUDIBLE_DB = -60.0  # only bars above this level set the median
VOCAL_RUN_MIN_BARS = 4  # a non-vocal run this long or longer marks a section edge
VOCAL_EDGE_MOVE_BARS = 3  # the furthest an existing boundary moves onto a run edge
INSTRUMENTAL_BELOW = 0.25  # a segment with less vocal share is intro, instrumental or outro
EDGE_INSTRUMENTAL_BELOW = 0.5  # the same for the first and last segments
CHORUS_MIN_VOCAL = 0.5  # a chorus candidate's bar-weighted vocal share
LOW_VOCAL_CONFIDENCE = 0.5


def beat_chroma(y: np.ndarray, sr: int, beats: Sequence[float]) -> np.ndarray:
    """CQT chroma (36 bins per octave) averaged from each beat to the next: 12 x beats."""
    import librosa

    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP, bins_per_octave=36)
    frames = np.clip(librosa.time_to_frames(np.asarray(beats), sr=sr, hop_length=HOP), 0, C.shape[1] - 1)
    bounds = list(frames) + [C.shape[1]]
    cols = []
    for a, b in zip(bounds, bounds[1:]):
        cols.append(C[:, a:b].mean(axis=1) if b > a else C[:, min(a, C.shape[1] - 1)])
    return np.stack(cols, axis=1) if cols else np.zeros((N_CHROMA, 0))


def bar_features(
    y: np.ndarray, sr: int, bars: Sequence[Bar], beats: Sequence[float]
) -> tuple[np.ndarray, list[float]]:
    """Per-bar features (12 chroma + 20 MFCC rows x bars) and per-bar loudness in dB.

    Chroma and MFCC are synced to the beats with `librosa.util.sync` (mean), then
    averaged over the beats of each bar.
    """
    import librosa

    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP, bins_per_octave=36)
    M = librosa.feature.mfcc(y=y, sr=sr, hop_length=HOP, n_mfcc=20)
    n_frames = min(C.shape[1], M.shape[1])
    C, M = C[:, :n_frames], M[:, :n_frames]
    frames = np.unique(
        np.clip(librosa.time_to_frames(np.asarray(beats), sr=sr, hop_length=HOP), 0, n_frames - 1)
    )
    Cb = librosa.util.sync(C, frames, aggregate=np.mean)
    Mb = librosa.util.sync(M, frames, aggregate=np.mean)
    # sync pads the frames with 0 and n_frames and de-duplicates, so column j covers
    # [segment_starts[j], next start); a beat in frame 0 adds no pre-beat column
    segment_starts = librosa.util.fix_frames(frames, x_min=0, x_max=n_frames)[:-1]
    bar_frames = librosa.time_to_frames(np.array([bar.start for bar in bars]), sr=sr, hop_length=HOP)
    owner = np.searchsorted(bar_frames, segment_starts, side="right") - 1
    columns = []
    loudness = []
    for b, bar in enumerate(bars):
        sel = np.where(owner == b)[0]
        if len(sel) == 0:
            nearest = min(len(segment_starts) - 1, int(np.searchsorted(segment_starts, bar_frames[b])))
            sel = np.array([nearest])
        sel = np.clip(sel, 0, Cb.shape[1] - 1)
        columns.append(np.concatenate([Cb[:, sel].mean(axis=1), Mb[:, sel].mean(axis=1)]))
        samples = y[int(bar.start * sr) : max(int(bar.end * sr), int(bar.start * sr) + 1)]
        rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64)))) if len(samples) else 0.0
        loudness.append(20.0 * np.log10(max(rms, SILENCE_RMS)))
    X = np.stack(columns, axis=1) if columns else np.zeros((N_CHROMA + 20, 0))
    return X, loudness


def _zscore_rows(X: np.ndarray) -> np.ndarray:
    std = X.std(axis=1, keepdims=True)
    return np.where(std > 0, (X - X.mean(axis=1, keepdims=True)) / np.where(std > 0, std, 1.0), 0.0)


def _embedding(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Laplacian eigenvectors of the bar recurrence graph (librosa tutorial method)."""
    import librosa
    import scipy.ndimage
    from scipy.linalg import eigh
    from scipy.sparse import csgraph

    chroma = librosa.util.normalize(X[:N_CHROMA], axis=0)
    timbre = _zscore_rows(X[N_CHROMA:])
    stacked = librosa.feature.stack_memory(chroma, n_steps=4, mode="edge")
    R = librosa.segment.recurrence_matrix(
        stacked, width=RECURRENCE_WIDTH, mode="affinity", sym=True
    )
    Rf = librosa.segment.timelag_filter(scipy.ndimage.median_filter)(R, size=(1, 7))
    path_distance = np.sum(np.diff(timbre, axis=1) ** 2, axis=0)
    sigma = float(np.median(path_distance))
    path_sim = np.exp(-path_distance / (sigma if sigma > 0 else 1.0))
    R_path = np.diag(path_sim, k=1) + np.diag(path_sim, k=-1)
    deg_path, deg_rec = R_path.sum(axis=1), Rf.sum(axis=1)
    mu = deg_path.dot(deg_path + deg_rec) / np.sum((deg_path + deg_rec) ** 2)
    A = mu * Rf + (1 - mu) * R_path
    L = csgraph.laplacian(A, normed=True)
    _, evecs = eigh(L)
    evecs = scipy.ndimage.median_filter(evecs, size=(9, 1))
    cnorm = np.cumsum(evecs**2, axis=1) ** 0.5
    return evecs, cnorm


def _cluster(evecs: np.ndarray, cnorm: np.ndarray, k: int) -> np.ndarray:
    from sklearn.cluster import KMeans
    from sklearn.exceptions import ConvergenceWarning

    Xk = evecs[:, :k] / (cnorm[:, k - 1 : k] + 1e-9)
    with warnings.catch_warnings():
        # near-identical bars (a click track, a one-chord loop) give fewer distinct points than k
        warnings.simplefilter("ignore", ConvergenceWarning)
        return KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(Xk)


def segment_bars(features: np.ndarray, k: int | None = None) -> tuple[list[int], int, float]:
    """Cluster id per bar (features: dims x bars), the k used and the largest cluster share.

    With `k` None: start at 3 and add one while the largest cluster covers more
    than 60% of bars, up to 6. Inputs too short for the recurrence matrix
    (fewer than MIN_SEGMENT_BARS bars) form a single cluster.
    """
    n = features.shape[1]
    if n < MIN_SEGMENT_BARS:
        return [0] * n, 1, 1.0
    evecs, cnorm = _embedding(features)
    k_now = min(k if k is not None else MIN_K, n)
    while True:
        labels = _cluster(evecs, cnorm, k_now)
        share = float(np.bincount(labels).max() / n)
        if k is not None or share <= SPLIT_SHARE or k_now >= min(MAX_K, n):
            return [int(c) for c in labels], k_now, share
        k_now += 1


def boundaries_from_clusters(
    cluster_ids: Sequence[int], min_bars: int = 2
) -> tuple[list[int], list[int]]:
    """Segment start bars (first is 0) and the cluster id per bar after merging.

    A segment shorter than `min_bars` loses its end boundary and merges into the
    following segment, taking that segment's cluster; a short last segment folds
    into the preceding one and takes its cluster. Then adjacent segments with
    equal clusters merge.
    """
    n = len(cluster_ids)
    if n == 0:
        return [], []
    ids = [int(c) for c in cluster_ids]
    run_starts = [0] + [i for i in range(1, n) if ids[i] != ids[i - 1]]
    run_ends = run_starts[1:] + [n]
    segments: list[list[int]] = []  # [start, end, cluster]
    start = 0
    for end in run_ends:
        if end - start >= min_bars:
            segments.append([start, end, ids[end - 1]])
            start = end
    if start < n:  # a short tail
        if segments:
            segments[-1][1] = n
        else:
            segments.append([0, n, ids[-1]])
    merged = [segments[0]]
    for seg in segments[1:]:
        if seg[2] == merged[-1][2]:
            merged[-1][1] = seg[1]
        else:
            merged.append(seg)
    per_bar = [c for s, e, c in merged for _ in range(s, e)]
    return [s for s, _, _ in merged], per_bar


def bar_stem_db(y: np.ndarray, sr: int, bars: Sequence[Bar]) -> list[float]:
    """Per-bar level of a stem in dB: 20 log10 of the RMS over the bar, floored at -120 dB."""
    levels = []
    for bar in bars:
        start = int(bar.start * sr)
        samples = y[start : max(int(bar.end * sr), start + 1)]
        rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64)))) if len(samples) else 0.0
        levels.append(float(20.0 * np.log10(max(rms, SILENCE_RMS))))
    return levels


def vocal_flags(db: Sequence[float]) -> list[bool]:
    """True for each bar with vocals: within VOCAL_BELOW_MEDIAN_DB of the median level.

    The median is taken over bars above -60 dB, so silent bars do not pull it down.
    The raw flags are then median-filtered over 3 bars; the first and last bars keep
    their own flag (as a reflected edge would give). With no bar above -60 dB (a
    silent stem, as on an instrumental track) every bar is vocal, so nothing changes.
    """
    levels = np.asarray(db, dtype=float)
    audible = levels[levels > VOCAL_AUDIBLE_DB]
    if len(audible) == 0:
        return [True] * len(levels)
    threshold = float(np.median(audible)) - VOCAL_BELOW_MEDIAN_DB
    raw = [bool(level >= threshold) for level in levels]
    last = len(raw) - 1
    return [
        raw[i] if i in (0, last) else raw[i - 1] + raw[i] + raw[i + 1] >= 2 for i in range(len(raw))
    ]


def vocal_runs(flags: Sequence[bool], keep_trailing: bool = False) -> list[tuple[int, int]]:
    """Non-vocal runs (start, end exclusive) of at least VOCAL_RUN_MIN_BARS bars.

    A run may start at bar 0. The trailing run (one ending at the last bar, usually a
    fade) is left out unless `keep_trailing`, in which case it comes last.
    """
    runs: list[tuple[int, int]] = []
    n = len(flags)
    i = 0
    while i < n:
        if flags[i]:
            i += 1
            continue
        j = i
        while j < n and not flags[j]:
            j += 1
        if j - i >= VOCAL_RUN_MIN_BARS and (keep_trailing or j < n):
            runs.append((i, j))
        i = j
    return runs


def runs_text(runs: Sequence[tuple[int, int]]) -> str:
    """`(0, 20), (93, 108)`, or `none`."""
    return ", ".join(f"({s}, {e})" for s, e in runs) or "none"


def insert_vocal_boundaries(
    boundaries: list[int], runs: Sequence[tuple[int, int]], n_bars: int, min_bars: int = 4
) -> list[int]:
    """Section start bars with the edges of non-vocal runs added.

    Each run edge becomes a boundary when both pieces it cuts keep `min_bars` bars;
    otherwise the nearest boundary moves onto the edge when the move is at most 3 bars
    and both of its neighbours keep `min_bars`. The first boundary never moves, nor a
    boundary already on a run edge. A trailing run (ending at `n_bars`, as listed by
    `vocal_runs(..., keep_trailing=True)`) adds no edges, and no boundary at or after
    its start moves.
    """
    bounds = sorted(set(boundaries))
    if not bounds:
        return bounds
    frozen_from = min((s for s, e in runs if e >= n_bars), default=n_bars)
    pinned = {bounds[0]}
    for edge in sorted({edge for s, e in runs if e < n_bars for edge in (s, e)}):
        if edge in bounds:
            pinned.add(edge)
            continue
        if not bounds[0] < edge < n_bars:
            continue
        i = bisect.bisect_left(bounds, edge)
        left, right = bounds[i - 1], bounds[i] if i < len(bounds) else n_bars
        if edge - left >= min_bars and right - edge >= min_bars:
            bounds.insert(i, edge)
            pinned.add(edge)
            continue
        nearby = sorted(
            (abs(b - edge), j)
            for j, b in enumerate(bounds)
            if b not in pinned and b < frozen_from and abs(b - edge) <= VOCAL_EDGE_MOVE_BARS
        )
        for _, j in nearby:
            before = bounds[j - 1]
            after = bounds[j + 1] if j + 1 < len(bounds) else n_bars
            if edge - before >= min_bars and after - edge >= min_bars:
                bounds[j] = edge
                pinned.add(edge)
                break
    return bounds


def _low_vocal(
    starts: list[int], ends: list[int], vocal: Sequence[bool] | None
) -> list[bool]:
    """Per segment: is it intro, instrumental or outro by its vocal share."""
    if vocal is None:
        return [False] * len(starts)
    flags = np.asarray(vocal, dtype=float)
    last = len(starts) - 1
    low = [
        float(flags[s:e].mean()) < (EDGE_INSTRUMENTAL_BELOW if i in (0, last) else INSTRUMENTAL_BELOW)
        for i, (s, e) in enumerate(zip(starts, ends))
    ]
    return [False] * len(starts) if all(low) else low


def label_sections(
    boundaries: Sequence[int],
    cluster_ids: Sequence[int],
    bar_loudness_db: Sequence[float],
    vocal: Sequence[bool] | None = None,
) -> tuple[list[Section], float | None]:
    """Name segments and return the chorus margin in dB (None when there is no rival).

    A segment's cluster is the most common id over its bars (the id at its start when
    the boundaries come straight from `boundaries_from_clusters`). Cluster loudness is
    the bar-weighted mean dB over all bars of the cluster's segments. Order: a cluster
    over 60% of bars is `verse`; `chorus` is the loudest recurring cluster not already
    verse (fallback: most bars); `verse` if unset is the remaining recurring cluster
    with most bars; once-only clusters are `intro` (first), `outro` (last) or `bridge`,
    `bridge 2`; other recurring clusters `verse 2`, `verse 3`. Confidence is 0.5, or
    0.3 when the chorus margin is under 1.5 dB.

    With `vocal` (one flag per bar), a segment whose vocal share is under
    INSTRUMENTAL_BELOW, or the first or last segment under EDGE_INSTRUMENTAL_BELOW, is
    `intro` (first), `outro` (last) or `instrumental` whatever its cluster, with
    confidence 0.5, and adjacent such segments merge into one. Those segments take no
    part in the cluster rules above (the 60% test counts the remaining bars), and
    chorus candidates need a bar-weighted vocal share of at least 0.5. When every
    segment would be low-vocal the flags are ignored.
    """
    n_bars = len(cluster_ids)
    starts = list(boundaries)
    ends = starts[1:] + [n_bars]
    segc = [Counter(int(c) for c in cluster_ids[s:e]).most_common(1)[0][0] for s, e in zip(starts, ends)]
    low = _low_vocal(starts, ends, vocal)
    sung = [(s, e, c) for s, e, c, lo in zip(starts, ends, segc, low) if not lo]
    sung_bars = sum(e - s for s, e, _ in sung)
    loud = np.asarray(bar_loudness_db, dtype=float)
    flags = np.ones(n_bars) if vocal is None else np.asarray(vocal, dtype=float)
    occ = Counter(c for _, _, c in sung)
    bars_of = {c: sum(e - s for s, e, cc in sung if cc == c) for c in occ}
    db_of = {c: float(np.mean(np.concatenate([loud[s:e] for s, e, cc in sung if cc == c]))) for c in occ}
    sung_of = {c: float(np.mean(np.concatenate([flags[s:e] for s, e, cc in sung if cc == c]))) for c in occ}

    big = [c for c in occ if bars_of[c] > SPLIT_SHARE * sung_bars]
    verse = big[0] if big else None
    recurring = [c for c in occ if occ[c] >= 2 and c != verse]
    if recurring:
        voiced = [c for c in recurring if sung_of[c] >= CHORUS_MIN_VOCAL]
        chorus = max(voiced, key=lambda c: db_of[c]) if voiced else None
    else:
        candidates = [c for c in occ if c != verse and sung_of[c] >= CHORUS_MIN_VOCAL]
        chorus = max(candidates, key=lambda c: bars_of[c]) if candidates else None
    rest = [c for c in recurring if c != chorus]
    if verse is None and rest:
        verse = max(rest, key=lambda c: bars_of[c])
    others = sorted((c for c in rest if c != verse), key=lambda c: -bars_of[c])

    rivals = [c for c in occ if occ[c] >= 2 and c != chorus]
    margin = (
        db_of[chorus] - max(db_of[c] for c in rivals) if chorus is not None and rivals else None
    )
    confidence = 0.3 if margin is not None and margin < LOW_MARGIN_DB else 0.5

    sections: list[Section] = []
    n_bridge = 0
    for i, (s, e, c) in enumerate(zip(starts, ends, segc)):
        if low[i]:
            if i > 0 and low[i - 1]:  # merge with the low-vocal segment before, keeping its start
                s = sections.pop().start_bar
            label = "intro" if s == 0 else "outro" if e == n_bars else "instrumental"
            sections.append(Section(label=label, start_bar=s, end_bar=e, confidence=LOW_VOCAL_CONFIDENCE))
            continue
        if c == verse:
            label = "verse"
        elif c == chorus:
            label = "chorus"
        elif occ[c] == 1:
            if i == 0:
                label = "intro"
            elif i == len(segc) - 1:
                label = "outro"
            else:
                n_bridge += 1
                label = "bridge" if n_bridge == 1 else f"bridge {n_bridge}"
        else:
            label = f"verse {others.index(c) + 2}"
        sections.append(Section(label=label, start_bar=s, end_bar=e, confidence=confidence))
    return sections, margin
