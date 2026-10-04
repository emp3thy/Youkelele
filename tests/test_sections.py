from __future__ import annotations

import numpy as np
import pytest

from youkelele.music.sections import (
    EDGE_INSTRUMENTAL_BELOW,
    HOP,
    INSTRUMENTAL_BELOW,
    VOCAL_BELOW_MEDIAN_DB,
    VOCAL_RUN_MIN_BARS,
    bar_features,
    bar_stem_db,
    boundaries_from_clusters,
    insert_vocal_boundaries,
    label_sections,
    segment_bars,
    vocal_flags,
    vocal_runs,
)
from youkelele.schemas import Bar, Grid, Meter


def _features(layout: list[tuple[np.ndarray, int]], seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cols = []
    for base, n in layout:
        for _ in range(n):
            cols.append(base + 0.03 * rng.standard_normal(base.shape))
    return np.stack(cols, axis=1)  # (dims, bars)


def _bases(n: int, seed: int = 0) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.random(32) for _ in range(n)]


def _segments(bounds: list[int], n_bars: int, clusters: list[int]) -> list[int]:
    ids = []
    for b, e, c in zip(bounds, bounds[1:] + [n_bars], clusters):
        ids += [c] * (e - b)
    return ids


def test_segment_bars_recovers_abab_structure():
    a, b = _bases(2)
    X = _features([(a, 8), (b, 8), (a, 8), (b, 8)])
    ids, k, share = segment_bars(X)
    assert len(ids) == 32
    bounds, _ = boundaries_from_clusters(ids)
    assert bounds[0] == 0
    found = bounds[1:]
    # the measured method stacks four bars of chroma history, so a boundary can
    # lag by up to two bars; with k = 3 on two real clusters, extra splits appear
    for expected in (8, 16, 24):
        assert min(abs(f - expected) for f in found) <= 2
    assert k == 3
    assert share <= 0.6


def test_segment_bars_splits_80_percent_cluster():
    a1, b, c = _bases(3, seed=3)
    a2 = a1 + 0.2 * (_bases(1, seed=9)[0] - 0.5)  # close to a1, far from b and c
    X = _features([(a1, 10), (a2, 10), (b, 5), (a1, 10), (a2, 10), (c, 5)])
    _, k3, share3 = segment_bars(X, k=3)
    assert k3 == 3
    assert share3 == pytest.approx(0.8)
    ids, k, share = segment_bars(X)
    assert k == 4
    assert share < 0.6


def test_bar_features_use_exactly_each_bars_beats_when_first_beat_is_at_zero():
    import librosa

    sr = 22050
    beats = [i * 0.5 for i in range(16)]
    t = np.arange(int(0.5 * sr)) / sr
    y = np.concatenate(
        [0.3 * np.sin(2 * np.pi * 220.0 * 2 ** (i / 12) * t) for i in range(16)]
    ).astype(np.float32)
    bars = [
        Bar(index=b, start=beats[4 * b], end=beats[4 * b] + 2.0, beats=list(range(4 * b, 4 * b + 4)))
        for b in range(4)
    ]
    X, loud = bar_features(y, sr, bars, beats)

    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP, bins_per_octave=36)
    M = librosa.feature.mfcc(y=y, sr=sr, hop_length=HOP, n_mfcc=20)
    n = min(C.shape[1], M.shape[1])
    frames = librosa.time_to_frames(np.array(beats), sr=sr, hop_length=HOP)
    assert frames[0] == 0
    per_beat = np.vstack(
        [librosa.util.sync(C[:, :n], frames, aggregate=np.mean),
         librosa.util.sync(M[:, :n], frames, aggregate=np.mean)]
    )
    assert per_beat.shape[1] == 16  # one column per beat, no pre-beat column
    for b, bar in enumerate(bars):
        assert X[:, b] == pytest.approx(per_beat[:, bar.beats].mean(axis=1))
    assert len(loud) == 4


def test_segment_bars_fewer_than_four_bars_is_one_cluster():
    X = _features([(_bases(1)[0], 3)])
    assert segment_bars(X) == ([0, 0, 0], 1, 1.0)


@pytest.mark.parametrize("n", [5, 7, 8])
def test_segment_bars_short_inputs_are_one_cluster(n):
    # recurrence_matrix(width=3) needs at least 9 bars; shorter clips must not crash
    a, b = _bases(2)
    X = _features([(a, n // 2), (b, n - n // 2)])
    assert segment_bars(X) == ([0] * n, 1, 1.0)


def test_segment_bars_nine_bars_runs_the_laplacian():
    a, b = _bases(2)
    ids, k, share = segment_bars(_features([(a, 4), (b, 5)]))
    assert len(ids) == 9
    assert k == 3


def test_boundaries_min_two_bars_merges_forward():
    # the one-bar segment at bar 3 merges into the following 0-cluster segment,
    # which then merges with the equal segment before it
    assert boundaries_from_clusters([0, 0, 0, 1, 0, 0, 2, 2, 2, 2]) == (
        [0, 6],
        [0, 0, 0, 0, 0, 0, 2, 2, 2, 2],
    )
    # a short run of one-bar segments merges until it reaches two bars
    assert boundaries_from_clusters([0, 1, 0, 0, 0, 1, 1, 1]) == (
        [0, 2, 5],
        [1, 1, 0, 0, 0, 1, 1, 1],
    )
    # a short last segment cannot merge forward and folds into the previous one
    assert boundaries_from_clusters([0, 0, 0, 1]) == ([0], [0, 0, 0, 0])
    assert boundaries_from_clusters([0, 0, 1, 1], min_bars=3) == ([0], [1, 1, 1, 1])


def _segment_lengths(bounds: list[int], n: int) -> list[int]:
    return [e - s for s, e in zip(bounds, bounds[1:] + [n])]


def test_boundaries_min_four_bars_merges_two_and_three_bar_segments():
    ids = [0] * 8 + [1] * 2 + [0] * 8 + [2] * 3 + [0] * 8
    bounds, per_bar = boundaries_from_clusters(ids, min_bars=4)
    assert len(per_bar) == len(ids)
    assert min(_segment_lengths(bounds, len(ids))) >= 4
    # at min_bars=2 the same input keeps the short segments
    short, _ = boundaries_from_clusters(ids, min_bars=2)
    assert min(_segment_lengths(short, len(ids))) < 4


def test_boundaries_min_four_on_twelve_bar_song_keeps_every_section_at_four_bars():
    # three-bar segments merge forward in pairs: two six-bar sections, none under four bars
    ids = [0] * 3 + [1] * 3 + [2] * 3 + [3] * 3
    bounds, per_bar = boundaries_from_clusters(ids, min_bars=4)
    assert bounds == [0, 6]
    assert per_bar == [1] * 6 + [3] * 6
    assert min(_segment_lengths(bounds, len(ids))) >= 4


def test_boundaries_blip_takes_the_following_segment_cluster():
    # a one-bar chorus-like blip (cluster 1) before a long verse (cluster 2)
    bounds, ids = boundaries_from_clusters([0, 0, 0, 1, 2, 2, 2, 2, 2, 2])
    assert bounds == [0, 3]
    assert ids == [0, 0, 0] + [2] * 7
    assert 1 not in ids
    sections, _ = label_sections(bounds, ids, [-20.0] * 10)
    assert [(s.start_bar, s.end_bar) for s in sections] == [(0, 3), (3, 10)]


def test_label_sections_chorus_is_loudest_recurring_bar_weighted():
    # V C V C V C(3-bar quiet fade): the segment-mean rule would pick V, bar-weighted picks C
    bounds = [0, 8, 16, 24, 32, 40]
    clusters = [0, 1, 0, 1, 0, 1]
    n_bars = 43
    ids = _segments(bounds, n_bars, clusters)
    loud = [-20.0 if c == 0 else -16.0 for c in ids]
    loud[40:43] = [-40.0] * 3
    sections, margin = label_sections(bounds, ids, loud)
    assert [s.label for s in sections] == ["verse", "chorus"] * 3
    chorus_db = (16 * -16.0 + 3 * -40.0) / 19
    assert margin == pytest.approx(chorus_db - -20.0)
    assert all(s.confidence == 0.3 for s in sections)  # margin under 1.5 dB


def test_label_sections_order_intro_bridge_outro():
    bounds = [0, 4, 12, 20, 24, 32, 40, 44, 48, 52, 60]
    clusters = [0, 1, 2, 6, 1, 2, 3, 4, 6, 2, 5]
    n_bars = 64
    ids = _segments(bounds, n_bars, clusters)
    db = {0: -25.0, 1: -20.0, 2: -10.0, 3: -25.0, 4: -25.0, 5: -25.0, 6: -22.0}
    loud = [db[c] for c in ids]
    sections, margin = label_sections(bounds, ids, loud)
    assert [s.label for s in sections] == [
        "intro", "verse", "chorus", "verse 2", "verse", "chorus",
        "bridge", "bridge 2", "verse 2", "chorus", "outro",
    ]
    assert [(s.start_bar, s.end_bar) for s in sections] == list(
        zip(bounds, bounds[1:] + [n_bars])
    )
    assert margin == pytest.approx(10.0)
    assert all(s.confidence == 0.5 for s in sections)


def test_label_sections_dominant_cluster_is_verse():
    # cluster 0 holds 36 of 50 bars; no other cluster recurs, so chorus falls back to most bars
    bounds = [0, 20, 28, 44]
    ids = _segments(bounds, 50, [0, 1, 0, 2])
    sections, _ = label_sections(bounds, ids, [-20.0] * 50)
    assert [s.label for s in sections] == ["verse", "chorus", "verse", "outro"]


def test_sections_cover_all_bars_contiguously():
    a, b = _bases(2)
    X = _features([(a, 8), (b, 8), (a, 8), (b, 8)])
    ids, k, share = segment_bars(X)
    loud = [-20.0] * 32
    sections, margin = label_sections(*boundaries_from_clusters(ids), loud)
    beats = [i * 0.5 for i in range(128)]
    bars = [Bar(index=i, start=2.0 * i, end=2.0 * i + 2.0, beats=list(range(4 * i, 4 * i + 4))) for i in range(32)]
    grid = Grid(
        bpm=120.0,
        meter=Meter(numerator=4, denominator=4),
        beats=beats,
        downbeats=list(range(0, 128, 4)),
        bars=bars,
        sections=sections,
        octave_decision="none",
        bar_loudness_db=loud,
        sections_k=k,
        largest_cluster_share=share,
        chorus_margin_db=margin,
        labels_low_confidence=False,
    )
    assert grid.sections[0].start_bar == 0
    assert grid.sections[-1].end_bar == 32


def test_vocal_flags_threshold_from_median_and_median_filter():
    assert VOCAL_BELOW_MEDIAN_DB == 12.0 and VOCAL_RUN_MIN_BARS == 4
    # median over bars above -60 dB is -20, so the threshold is -32
    db = [-20.0, -20.0, -35.0, -20.0, -20.0, -35.0, -35.0, -35.0, -20.0, -120.0]
    # raw:      T T F T T F F F T F; the 3-bar median fills the lone gap at bar 2 and drops the
    # lone vocal bar 8; the edge bars keep their own flag
    assert vocal_flags(db) == [True] * 5 + [False] * 5
    # within 12 dB counts as vocal; the last bar keeps its own flag
    assert vocal_flags([-20.0, -20.0, -20.0, -32.0]) == [True] * 4
    assert vocal_flags([-20.0, -20.0, -20.0, -32.5]) == [True] * 3 + [False]
    # silent bars do not pull the median down: with them the median would be -77.5 and bar 4 vocal
    db = [-20.0] * 4 + [-35.0] + [-120.0] * 5
    assert vocal_flags(db) == [True] * 4 + [False] * 6


def test_vocal_flags_all_true_when_stem_silent():
    # an instrumental track: a silent vocals stem must not make every section instrumental
    sr = 8000
    bars = [Bar(index=i, start=2.0 * i, end=2.0 * i + 2.0, beats=[]) for i in range(8)]
    db = bar_stem_db(np.zeros(16 * sr, dtype=np.float32), sr, bars)
    assert db == [-120.0] * 8
    flags = vocal_flags(db)
    assert flags == [True] * 8
    assert vocal_runs(flags) == []
    bounds = [0, 4]
    ids = [0] * 4 + [1] * 4
    loud = [-20.0] * 8
    assert label_sections(bounds, ids, loud, vocal=flags) == label_sections(bounds, ids, loud)


def test_bar_stem_db_is_rms_level_per_bar():
    sr = 8000
    t = np.arange(4 * sr) / sr
    y = np.concatenate([0.5 * np.sin(2 * np.pi * 440.0 * t[: 2 * sr]), np.zeros(2 * sr)])
    bars = [Bar(index=0, start=0.0, end=2.0, beats=[]), Bar(index=1, start=2.0, end=4.0, beats=[])]
    db = bar_stem_db(y.astype(np.float32), sr, bars)
    assert db[0] == pytest.approx(20 * np.log10(0.5 / np.sqrt(2)), abs=0.01)
    assert db[1] == -120.0


def test_vocal_runs_skip_short_runs_and_trailing_run():
    T, F = True, False
    flags = [F] * 4 + [T] * 3 + [F] * 3 + [T] * 2 + [F] * 5 + [T] * 2 + [F] * 4
    # (0, 4) counts at exactly four bars; (7, 10) is too short; (19, 23) is the trailing run
    assert vocal_runs(flags) == [(0, 4), (12, 17)]
    assert vocal_runs(flags, keep_trailing=True) == [(0, 4), (12, 17), (19, 23)]
    assert vocal_runs([T] * 10) == []
    assert vocal_runs([F] * 10) == []  # one run that is the trailing run


def test_insert_vocal_boundaries_adds_edges_when_pieces_keep_four_bars():
    # Chelsea-shaped: the end of the opening run splits the first chorus
    assert insert_vocal_boundaries([0, 9, 38, 61], [(0, 20), (45, 50)], 80) == [
        0, 9, 20, 38, 45, 50, 61,
    ]
    # a piece of three bars is not enough: edge 23 moves boundary 20 instead; edge 30 is added
    assert insert_vocal_boundaries([0, 20, 40], [(23, 30)], 60) == [0, 23, 30, 40]
    assert insert_vocal_boundaries([0, 20], [(10, 30)], 40, min_bars=12) == [0, 20]


def test_insert_vocal_boundaries_moves_nearest_within_three_bars():
    # edge 24 would leave 2 bars before 26: boundary 26 moves onto it; edge 40 is inserted
    assert insert_vocal_boundaries([0, 10, 26, 50], [(24, 40)], 60) == [0, 10, 24, 40, 50]
    # edge 10 sits 2 bars from both 8 and 12, and either move leaves a 2-bar neighbour
    assert insert_vocal_boundaries([0, 8, 12, 30], [(10, 20)], 40) == [0, 8, 12, 20, 30]
    # a boundary on one run's edge is not moved off it by the next run: 20 stays, 30 moves to 27
    assert insert_vocal_boundaries([0, 30, 50], [(10, 20), (22, 27)], 60) == [0, 10, 20, 27, 50]


def test_insert_vocal_boundaries_never_moves_first_boundary():
    # edge 2 is 2 bars from bar 0 (which never moves) and 5 from 7 (too far)
    assert insert_vocal_boundaries([0, 7, 30], [(2, 6)], 40) == [0, 6, 30]
    assert insert_vocal_boundaries([0, 12, 30], [(2, 8)], 40) == [0, 8, 12, 30]
    # nor any boundary at or after the trailing run's start: 34 would otherwise move to 32
    assert insert_vocal_boundaries([0, 20, 34], [(26, 32), (34, 44)], 44) == [0, 20, 26, 34]


def _chelsea_shaped() -> tuple[list[int], list[int], list[float], list[bool]]:
    bounds = [0, 9, 20, 38, 61, 71, 93, 108]
    n_bars = 120
    ids = _segments(bounds, n_bars, [0, 1, 1, 0, 1, 0, 1, 1])
    loud = [-20.0 if c == 0 else -15.0 for c in ids]
    vocal = [False] * 20 + [True] * 73 + [False] * 15 + [True] * 12
    return bounds, ids, loud, vocal


def test_label_sections_instrumental_intro_and_merge():
    assert INSTRUMENTAL_BELOW == 0.25 and EDGE_INSTRUMENTAL_BELOW == 0.5
    bounds, ids, loud, vocal = _chelsea_shaped()
    sections, margin = label_sections(bounds, ids, loud, vocal=vocal)
    assert [(s.label, s.start_bar, s.end_bar) for s in sections] == [
        ("intro", 0, 20),  # two non-vocal segments of different clusters merge
        ("chorus", 20, 38),
        ("verse", 38, 61),
        ("chorus", 61, 71),
        ("verse", 71, 93),
        ("instrumental", 93, 108),
        ("chorus", 108, 120),
    ]
    assert margin == pytest.approx(5.0)
    assert all(s.confidence == 0.5 for s in sections)

    # the first and last segments need half vocal, a middle one only a quarter
    bounds = [0, 8, 16, 24, 32, 40, 48]
    ids = _segments(bounds, 56, [0, 1, 3, 2, 1, 2, 4])
    loud = [-15.0 if c == 2 else -20.0 for c in ids]
    part = [True] * 3 + [False] * 5  # a vocal share of 0.375
    vocal = part + [True] * 8 + [False] * 8 + [True] * 8 + part + [True] * 8 + part
    sections, _ = label_sections(bounds, ids, loud, vocal=vocal)
    assert [s.label for s in sections] == [
        "intro", "verse", "instrumental", "chorus", "verse", "chorus", "outro",
    ]
    # a non-vocal segment next to the low-vocal last one merges into the outro
    vocal = vocal[:32] + [True] * 8 + [False] * 8 + part
    sections, _ = label_sections(bounds, ids, loud, vocal=vocal)
    assert [(s.label, s.start_bar, s.end_bar) for s in sections][-1] == ("outro", 40, 56)


def test_label_sections_chorus_needs_half_vocal_share():
    # cluster 1 is loudest and recurs but carries vocals in only 3 of 8 bars per segment
    bounds = [0, 8, 16, 24, 32]
    ids = _segments(bounds, 40, [0, 1, 2, 1, 2])
    loud = [{0: -20.0, 1: -10.0, 2: -15.0}[c] for c in ids]
    third = [True, True, True] + [False] * 5
    vocal = [True] * 8 + third + [True] * 8 + third + [True] * 8
    sections, _ = label_sections(bounds, ids, loud, vocal=vocal)
    assert [s.label for s in sections] == ["intro", "verse", "chorus", "verse", "chorus"]
    sections, _ = label_sections(bounds, ids, loud)
    assert [s.label for s in sections] == ["intro", "chorus", "verse", "chorus", "verse"]


def test_label_sections_unchanged_without_vocal():
    bounds = [0, 4, 12, 20, 24, 32, 40, 44, 48, 52, 60]
    ids = _segments(bounds, 64, [0, 1, 2, 6, 1, 2, 3, 4, 6, 2, 5])
    db = {0: -25.0, 1: -20.0, 2: -10.0, 3: -25.0, 4: -25.0, 5: -25.0, 6: -22.0}
    loud = [db[c] for c in ids]
    expected = label_sections(bounds, ids, loud)
    assert [s.label for s in expected[0]][:3] == ["intro", "verse", "chorus"]
    assert label_sections(bounds, ids, loud, vocal=None) == expected
    assert label_sections(bounds, ids, loud, vocal=[True] * 64) == expected
