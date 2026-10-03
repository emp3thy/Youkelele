from __future__ import annotations

import numpy as np
import pytest

from youkelele.music.sections import (
    boundaries_from_clusters,
    label_sections,
    segment_bars,
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
    bounds = boundaries_from_clusters(ids)
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


def test_segment_bars_fewer_than_four_bars_is_one_cluster():
    X = _features([(_bases(1)[0], 3)])
    assert segment_bars(X) == ([0, 0, 0], 1, 1.0)


def test_boundaries_min_two_bars_merges_forward():
    # the one-bar segment at bar 3 loses its end boundary and absorbs bars 4 and 5
    assert boundaries_from_clusters([0, 0, 0, 1, 0, 0, 2, 2, 2, 2]) == [0, 3, 6]
    # a short first segment merges forward, then equal neighbours merge
    assert boundaries_from_clusters([0, 1, 0, 0, 0, 1, 1, 1]) == [0, 5]
    # a short last segment cannot merge forward and folds into the previous one
    assert boundaries_from_clusters([0, 0, 0, 1]) == [0]
    assert boundaries_from_clusters([0, 0, 1, 1], min_bars=3) == [0]


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
    sections, margin = label_sections(boundaries_from_clusters(ids), ids, loud)
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
