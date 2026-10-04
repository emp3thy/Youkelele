from __future__ import annotations

import pytest

from youkelele.music.relabel import BRIDGE_NOVEL_CHORDS, refine_labels, section_novelty
from youkelele.schemas import Bar, ChordEvent, Chords, Grid, Key, Meter, Section

BAR = 2.0


def _grid(specs: list[tuple[str, int]], vocal_db: list[float] | None = None) -> Grid:
    """specs: (label, bars) per section; vocal_db one level per bar, or None for none stored."""
    n = sum(b for _, b in specs)
    sections, start = [], 0
    for label, bars in specs:
        sections.append(Section(label=label, start_bar=start, end_bar=start + bars, confidence=0.5))
        start += bars
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4),
        beats=[i * 0.5 for i in range(n * 4)], downbeats=[4 * i for i in range(n)],
        bars=[
            Bar(index=i, start=i * BAR, end=(i + 1) * BAR, beats=list(range(4 * i, 4 * i + 4)))
            for i in range(n)
        ],
        sections=sections, octave_decision="none", bar_loudness_db=[-20.0] * n, sections_k=3,
        largest_cluster_share=0.4, chorus_margin_db=None, labels_low_confidence=False,
        bar_vocal_db=vocal_db if vocal_db is not None else [],
    )


def _chords(per_bar: list[str]) -> Chords:
    """One event per bar; a triad of "N" is a no-chord bar."""
    events = [
        ChordEvent(
            bar=i, beat=0, start=i * BAR, end=(i + 1) * BAR, label=t, triad=t, confidence=0.9
        )
        for i, t in enumerate(per_bar)
    ]
    return Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=events)


def _two_chord_sections(*chord_pairs: tuple[str, str], bars: int = 8) -> list[str]:
    """Per-bar triads: each section alternates its pair of chords."""
    out: list[str] = []
    for a, b in chord_pairs:
        out += [a, b] * (bars // 2)
    return out


C, G, F, BB = "C:maj", "G:maj", "F:maj", "Bb:maj"


def test_section_novelty_counts_triads_unique_to_a_section():
    # section 1 plays C and F; F occurs nowhere else, so half its bars are novel
    triads = [C, G] * 4 + [C, F] * 4 + [G, C] * 4
    grid = _grid([("verse", 8), ("chorus", 8), ("verse", 8)])
    assert section_novelty(grid, _chords(triads)) == [0.0, 0.5, 0.0]


def test_section_novelty_ignores_no_chord_bars_and_counts_overlapping_events():
    # bars 4-5 are N; a chord starting mid-bar still counts for the bar it overlaps
    triads = [C, G, C, G, "N", "N", C, G]
    grid = _grid([("verse", 4), ("chorus", 4)])
    chords = _chords(triads)
    chords.events.append(
        ChordEvent(bar=6, beat=2, start=6 * BAR + 1.0, end=7 * BAR, label=F, triad=F, confidence=0.9)
    )
    # chorus chord-bars are 6 and 7 (4 and 5 are N); F overlaps bar 6 and occurs only here
    assert section_novelty(grid, _chords(triads)) == [0.0, 0.0]
    assert section_novelty(grid, chords) == [0.0, 0.5]


def test_section_novelty_of_a_section_with_no_chords_is_zero():
    grid = _grid([("verse", 4), ("chorus", 4), ("verse", 4)])
    assert section_novelty(grid, _chords([C, G] * 2 + ["N"] * 4 + [C, G] * 2)) == [0.0, 0.0, 0.0]


def test_refine_labels_names_the_one_novel_middle_vocal_section_bridge():
    # Summer of '69-shaped: the middle once-only section holds F and Bb, heard nowhere else
    triads = _two_chord_sections((C, G), (C, G), (C, G), (F, BB), (C, G))
    grid = _grid(
        [("intro", 8), ("verse", 8), ("chorus", 8), ("verse", 8), ("verse", 8), ("outro", 8)],
        vocal_db=[-40.0] * 8 + [-20.0] * 40,
    )
    triads = [C, G] * 4 + triads
    chords = _chords(triads)
    novelty = section_novelty(grid, chords)
    assert novelty[4] == 1.0 and novelty[:4] + novelty[5:] == [0.0] * 5
    assert refine_labels(grid, chords) == [
        "intro", "verse", "chorus", "verse", "bridge", "outro",
    ]
    assert BRIDGE_NOVEL_CHORDS == 0.5


def test_refine_labels_turns_non_novel_bridge_into_verse():
    # Wet Leg-shaped: a once-only middle section that plays the verse's chords
    triads = _two_chord_sections((C, G), (C, G), (C, G), (C, G))
    grid = _grid([("verse", 8), ("chorus", 8), ("bridge", 8), ("chorus", 8)], vocal_db=[-20.0] * 32)
    chords = _chords(triads)
    assert section_novelty(grid, chords) == [0.0] * 4
    assert refine_labels(grid, chords) == ["verse", "chorus", "verse", "chorus"]


def test_refine_labels_passes_through_intro_instrumental_outro_and_hand_labels():
    triads = _two_chord_sections((C, G), (F, BB), (C, G), (C, G), (C, G))
    grid = _grid(
        [("Intro", 8), ("instrumental", 8), ("pre-chorus", 8), ("verse", 8), ("outro", 8)],
        vocal_db=[-20.0] * 40,
    )
    # the instrumental holds the novel chords but is not a bridge candidate
    assert refine_labels(grid, _chords(triads)) == [
        "Intro", "instrumental", "pre-chorus", "verse", "outro",
    ]


def test_refine_labels_first_and_last_sections_are_never_the_bridge():
    triads = _two_chord_sections((F, BB), (C, G), (C, G), (C, G))
    grid = _grid([("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8)], vocal_db=[-20.0] * 32)
    assert refine_labels(grid, _chords(triads)) == ["verse", "chorus", "verse", "chorus"]
    triads = _two_chord_sections((C, G), (C, G), (C, G), (F, BB))
    assert refine_labels(grid, _chords(triads)) == ["verse", "chorus", "verse", "chorus"]


def test_refine_labels_novel_section_needs_half_its_bars_vocal():
    triads = _two_chord_sections((C, G), (F, BB), (C, G), (C, G))
    db = [-20.0] * 8 + [-20.0] * 3 + [-60.0] * 5 + [-20.0] * 16  # 3 of 8 bars vocal
    grid = _grid([("verse", 8), ("verse", 8), ("chorus", 8), ("chorus", 8)], vocal_db=db)
    assert refine_labels(grid, _chords(triads)) == ["verse", "verse", "chorus", "chorus"]
    # without stored vocal levels the vocal test is skipped
    bare = _grid([("verse", 8), ("verse", 8), ("chorus", 8), ("chorus", 8)])
    assert refine_labels(bare, _chords(triads)) == ["verse", "bridge", "chorus", "chorus"]


def test_refine_labels_at_most_one_bridge():
    # two middle sections are each fully novel: neither is named, the grid's bridge is a verse
    triads = _two_chord_sections((C, G), (F, BB), ("D:min", "A:min"), (C, G))
    grid = _grid([("verse", 8), ("verse", 8), ("bridge", 8), ("chorus", 8)], vocal_db=[-20.0] * 32)
    assert refine_labels(grid, _chords(triads)) == ["verse", "verse", "verse", "chorus"]


def test_refine_labels_ignores_a_novel_section_with_an_ineligible_label():
    # the only novel middle section is an instrumental: a stray bridge elsewhere is a verse
    triads = _two_chord_sections((C, G), (F, BB), (C, G), (C, G))
    grid = _grid(
        [("verse", 8), ("instrumental", 8), ("bridge", 8), ("chorus", 8)], vocal_db=[-20.0] * 32
    )
    assert refine_labels(grid, _chords(triads)) == ["verse", "instrumental", "verse", "chorus"]


def test_refine_labels_leaves_the_grid_unchanged():
    triads = _two_chord_sections((C, G), (F, BB), (C, G))
    grid = _grid([("verse", 8), ("verse", 8), ("chorus", 8)], vocal_db=[-20.0] * 24)
    before = [s.label for s in grid.sections]
    assert refine_labels(grid, _chords(triads))[1] == "bridge"
    assert [s.label for s in grid.sections] == before


@pytest.mark.parametrize("n", [0, 1])
def test_refine_labels_handles_songs_with_fewer_than_three_sections(n):
    grid = _grid([("verse", 8), ("chorus", 8)][: n + 1], vocal_db=[-20.0] * (8 * (n + 1)))
    labels = refine_labels(grid, _chords([C, G] * (4 * (n + 1))))
    assert labels == [s.label for s in grid.sections]
