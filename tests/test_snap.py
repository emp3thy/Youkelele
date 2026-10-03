import pytest

from youkelele.models.chords import LabelSpan
from youkelele.music.snap import snap_to_beats
from youkelele.schemas import Bar, Grid, Meter, Section


def _grid() -> Grid:
    beats = [i * 0.5 for i in range(8)]
    bars = [
        Bar(index=0, start=0.0, end=2.0, beats=[0, 1, 2, 3]),
        Bar(index=1, start=2.0, end=4.0, beats=[4, 5, 6, 7]),
    ]
    return Grid(
        bpm=120, meter=Meter(numerator=4, denominator=4), beats=beats, downbeats=[0, 4], bars=bars,
        sections=[Section(label="verse", start_bar=0, end_bar=2, confidence=1.0)],
        octave_decision="none", bar_loudness_db=[-20.0, -20.0], sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def test_snap_merges_adjacent_equal_labels_and_sets_bar_beat():
    spans = [LabelSpan(0.1, 1.9, "C:maj"), LabelSpan(1.9, 3.0, "G:maj/5"), LabelSpan(3.0, 4.0, "G:maj")]
    events = snap_to_beats(spans, _grid())
    assert [e.label for e in events] == ["C:maj", "G:maj/5", "G:maj"]
    assert [(e.bar, e.beat) for e in events] == [(0, 0), (1, 0), (1, 2)]
    assert events[0].start == pytest.approx(0.0) and events[0].end == pytest.approx(2.0)
    assert [e.triad for e in events] == ["C:maj", "G:maj", "G:maj"]


def test_snap_majority_label_within_beat():
    spans = [LabelSpan(0.0, 0.2, "C:maj"), LabelSpan(0.2, 0.5, "G:maj"), LabelSpan(0.5, 4.0, "G:maj")]
    events = snap_to_beats(spans, _grid())
    assert len(events) == 1 and events[0].label == "G:maj"
    assert events[0].confidence == pytest.approx((0.6 + 7) / 8)
