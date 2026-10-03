"""Bar features, Laplacian segmentation and section labels.

Rules measured on five real songs in the grid round-three spike
(docs/superpowers/specs/2026-10-03-spike-grid-round3.md).
"""

from __future__ import annotations

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


def label_sections(
    boundaries: Sequence[int],
    cluster_ids: Sequence[int],
    bar_loudness_db: Sequence[float],
) -> tuple[list[Section], float | None]:
    """Name segments and return the chorus margin in dB (None when there is no rival).

    Cluster loudness is the bar-weighted mean dB over all bars of the cluster's
    segments. Order: a cluster over 60% of bars is `verse`; `chorus` is the
    loudest recurring cluster not already verse (fallback: most bars); `verse`
    if unset is the remaining recurring cluster with most bars; once-only
    clusters are `intro` (first), `outro` (last) or `bridge`, `bridge 2`;
    other recurring clusters `verse 2`, `verse 3`. Confidence is 0.5, or 0.3
    when the chorus margin is under 1.5 dB.
    """
    n_bars = len(cluster_ids)
    starts = list(boundaries)
    ends = starts[1:] + [n_bars]
    segc = [int(cluster_ids[b]) for b in starts]
    loud = np.asarray(bar_loudness_db, dtype=float)
    occ = Counter(segc)
    bars_of = {c: sum(e - s for s, e, cc in zip(starts, ends, segc) if cc == c) for c in occ}
    db_of = {
        c: float(np.mean(np.concatenate([loud[s:e] for s, e, cc in zip(starts, ends, segc) if cc == c])))
        for c in occ
    }

    big = [c for c in occ if bars_of[c] > SPLIT_SHARE * n_bars]
    verse = big[0] if big else None
    recurring = [c for c in occ if occ[c] >= 2 and c != verse]
    if recurring:
        chorus = max(recurring, key=lambda c: db_of[c])
    else:
        candidates = [c for c in occ if c != verse]
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

    sections = []
    n_bridge = 0
    for i, (s, e, c) in enumerate(zip(starts, ends, segc)):
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
