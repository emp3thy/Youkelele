from __future__ import annotations

import pytest

from youkelele.music.relabel import (
    BRIDGE_NOVEL_CHORDS,
    CHORD_MATCH_DISTANCE,
    FRAGMENT_BARS,
    ONE_LOOP_SHARE,
    bar_triad_strings,
    containment_distance,
    default_plan,
    longest_member,
    one_loop_share,
    pair_novelty,
    refine_labels,
    section_novelty,
    section_plan,
)
from youkelele.schemas import Bar, ChordEvent, Chords, Grid, Key, Meter, PlannedSection, Section

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


def _cycle_sections(*specs: tuple[tuple[str, ...], int]) -> list[str]:
    """Per-bar triads: each section cycles its chords one per bar, from its first bar."""
    out: list[str] = []
    for cycle, bars in specs:
        out += [cycle[i % len(cycle)] for i in range(bars)]
    return out


C, G, F, BB = "C:maj", "G:maj", "F:maj", "Bb:maj"
EM, D, A = "E:min", "D:maj", "A:maj"


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


# --- the section plan (version 1.5 spec, section 3) ---


def _grid_and_chords(specs: list[tuple[str, tuple[str, ...], int]]) -> tuple[Grid, Chords]:
    """specs: (label, chord cycle, bars) per grid section."""
    grid = _grid([(label, bars) for label, _, bars in specs])
    chords = _chords(_cycle_sections(*((cycle, bars) for _, cycle, bars in specs)))
    return grid, chords


def _plan_of(specs: list[tuple[str, tuple[str, ...], int]]) -> list[PlannedSection]:
    return section_plan(*_grid_and_chords(specs))


def test_section_plan_constants():
    assert FRAGMENT_BARS == 8
    assert ONE_LOOP_SHARE == 0.85
    assert CHORD_MATCH_DISTANCE == 0.35


def test_bar_triad_strings_sorts_and_joins_each_bars_triads():
    grid = _grid([("verse", 3)])
    chords = _chords([G, "N", C])
    chords.events.append(
        ChordEvent(bar=0, beat=2, start=1.0, end=BAR, label=F, triad=F, confidence=0.9)
    )
    assert bar_triad_strings(grid, chords) == [f"{F}+{G}", "N", C]


def test_containment_distance_finds_the_shorter_inside_the_longer_with_a_one_bar_shift():
    assert containment_distance(["Em", "D", "G"], ["C", "Em", "D", "G", "C"]) == 0.0
    assert containment_distance(["Em", "D", "G"], ["Em", "D", "G"]) == 0.0
    assert containment_distance(["Em", "D"], ["G", "C"]) == 1.0
    assert containment_distance([], []) == 0.0


def test_containment_distance_takes_the_shorter_either_way_and_uses_the_shifted_windows():
    # X a b against a b c d: the window shifted one bar before the start is a b, one edit away
    assert containment_distance(["X", "a", "b"], ["a", "b", "c", "d"]) == pytest.approx(1 / 3)
    assert containment_distance(["a", "b", "c", "d"], ["X", "a", "b"]) == pytest.approx(1 / 3)
    # and one past the end: c d X against a b c d leaves c d
    assert containment_distance(["c", "d", "X"], ["a", "b", "c", "d"]) == pytest.approx(1 / 3)
    # with equal lengths each is tried as the shorter (a a b in a c a's windows needs two
    # edits, a c a in a a b's needs one) and the lower is kept whichever order is given
    a, b = ["a", "a", "b"], ["a", "c", "a"]
    assert containment_distance(a, b) == containment_distance(b, a) == pytest.approx(1 / 3)


def test_containment_distance_substitutes_bars_at_one_less_their_triad_jaccard():
    assert containment_distance(["D"], ["D+G"]) == 0.5
    assert containment_distance(["N"], ["D"]) == 1.0
    assert containment_distance(["N"], ["N"]) == 0.0
    assert containment_distance(["D+G", "Em"], ["G", "Em"]) == pytest.approx(0.25)


def test_containment_distance_tries_windows_one_bar_longer_than_the_shorter():
    # the n+1 window a b X c d holds a b c d with one insertion
    assert containment_distance(["a", "b", "c", "d"], ["a", "b", "X", "c", "d"]) == 0.25


def test_pair_novelty_is_the_share_of_fragment_chord_bars_on_a_triad_the_neighbour_lacks():
    grid = _grid([("verse", 4), ("verse", 4)])
    chords = _chords([C, G, "N", F] + [C, G, C, G])
    assert pair_novelty(grid, chords, (0, 4), (4, 8)) == pytest.approx(1 / 3)
    assert pair_novelty(grid, chords, (4, 8), (0, 4)) == 0.0
    assert pair_novelty(grid, _chords(["N"] * 8), (0, 4), (4, 8)) == 0.0


def test_sandwich_verse_between_choruses_on_their_chords_becomes_one_chorus():
    # sections: chorus 0-8 (Em D G), verse 8-12 (Em D), chorus 12-20 (Em D G)
    plan = _plan_of([("chorus", (EM, D, G), 8), ("verse", (EM, D), 4), ("chorus", (EM, D, G), 8)])
    assert [(p.start_bar, p.end_bar, p.label, p.members) for p in plan] == [
        (0, 20, "chorus", [0, 1, 2])
    ]


def test_sandwich_verse_with_a_chord_one_chorus_lacks_stays():
    specs = [("chorus", (EM, D, G), 8), ("verse", (EM, C), 4), ("chorus", (EM, D, G, C), 8)]
    assert [p.label for p in _plan_of(specs)] == ["chorus", "verse", "chorus"]


def test_fragment_joins_a_same_label_neighbour_at_least_as_long_that_plays_its_chords():
    # verse 0-16 (Em D G), verse 16-23 (Em D): 7 bars, pair novelty 0 -> one verse 0-23
    plan = _plan_of([("verse", (EM, D, G), 16), ("verse", (EM, D), 7)])
    assert [(p.start_bar, p.end_bar, p.members) for p in plan] == [(0, 23, [0, 1])]


def test_fragment_with_a_new_chord_does_not_merge():
    # verse 0-16 (Em D G), verse 16-23 (Em D A): novelty > 0 -> two sections
    assert len(_plan_of([("verse", (EM, D, G), 16), ("verse", (EM, D, A), 7)])) == 2


def test_fragment_joins_only_a_neighbour_at_least_as_long_with_its_own_label():
    # the 4-bar verse joins the 6-bar one whichever side it is on
    assert [p.members for p in _plan_of([("verse", (EM, D), 4), ("verse", (EM, D), 6)])] == [[0, 1]]
    assert [p.members for p in _plan_of([("verse", (EM, D), 6), ("verse", (EM, D), 4)])] == [[0, 1]]
    # the 6-bar verse plays only chords of the 4-bar one, but the 4-bar one is shorter; the
    # 4-bar verse brings A, so it cannot join the 6-bar one either
    assert len(_plan_of([("verse", (EM, D), 6), ("verse", (EM, D, A), 4)])) == 2
    # a chorus never takes a verse
    assert len(_plan_of([("chorus", (EM, D, G), 16), ("verse", (EM, D), 6)])) == 2


def test_whole_sections_of_eight_bars_never_merge_on_chord_match():
    # verse 0-16 and verse 16-32 on the same chords -> two sections
    assert len(_plan_of([("verse", (EM, D, G), 16), ("verse", (EM, D, G), 16)])) == 2
    assert len(_plan_of([("verse", (EM, D, G), 16), ("verse", (EM, D, G), 8)])) == 2


def test_intro_instrumental_outro_and_bridge_never_merge():
    # intro 0-4 (Em), verse 4-20 (Em D G), instrumental 20-24 (Em D), verse 24-40, outro 40-44
    plan = _plan_of([
        ("intro", (EM,), 4), ("verse", (EM, D, G), 16), ("instrumental", (EM, D), 4),
        ("verse", (EM, D, G), 16), ("outro", (EM, D, G), 4),
    ])
    labels = [p.label for p in plan]
    assert labels == ["intro", "verse", "instrumental", "verse", "outro"]
    assert [p.members for p in plan] == [[0], [1], [2], [3], [4]]


def test_a_bridge_named_by_the_chords_never_merges():
    # the 4-bar middle section holds F and Bb, heard nowhere else: refine_labels names it bridge
    plan = _plan_of([("verse", (C, G), 8), ("verse", (F, BB), 4), ("verse", (C, G), 8)])
    assert [p.label for p in plan] == ["verse", "bridge", "verse"]


def test_two_eligible_neighbours_the_closer_chord_sequence_wins():
    # verse 0-16 (Em D G C), verse 16-22 (Em D), verse 22-38 (Em D Em D): the fragment joins 22-38
    grid, chords = _grid_and_chords(
        [("verse", (EM, D, G, C), 16), ("verse", (EM, D), 6), ("verse", (EM, D), 16)]
    )
    strings = bar_triad_strings(grid, chords)
    assert containment_distance(strings[16:22], strings[22:38]) == 0.0
    assert containment_distance(strings[16:22], strings[0:16]) > 0.0
    plan = section_plan(grid, chords)
    assert [(p.start_bar, p.end_bar) for p in plan] == [(0, 16), (16, 38)]
    assert plan[1].members == [1, 2]


def test_two_eligible_neighbours_the_earlier_wins_on_a_tie():
    plan = _plan_of([("verse", (EM, D), 8), ("verse", (EM, D), 4), ("verse", (EM, D), 8)])
    assert [(p.start_bar, p.end_bar, p.members) for p in plan] == [(0, 12, [0, 1]), (12, 20, [2])]


def test_all_fragment_song_cascades_to_a_fixed_point_and_never_absorbs_the_intro():
    # five verses of 4 bars each on the same chords: 4-bar fragments join a neighbour at least
    # as long; the rule reaches a fixed point and never produces a section over an intro
    plan = _plan_of([("verse", (EM, D, G), 4)] * 5)
    assert sum(p.end_bar - p.start_bar for p in plan) == 20 and plan[0].start_bar == 0
    assert [m for p in plan for m in p.members] == [0, 1, 2, 3, 4]
    plan = _plan_of([("intro", (EM, D, G), 4)] + [("verse", (EM, D, G), 4)] * 4)
    assert plan[0].label == "intro" and plan[0].members == [0]
    assert (plan[0].start_bar, plan[0].end_bar) == (0, 4)


def test_section_plan_leaves_the_grid_unchanged():
    grid, chords = _grid_and_chords(
        [("chorus", (EM, D, G), 8), ("verse", (EM, D), 4), ("chorus", (EM, D, G), 8)]
    )
    before = grid.model_dump()
    assert len(section_plan(grid, chords)) == 1
    assert grid.model_dump() == before


def test_default_plan_is_one_section_per_grid_section_with_refined_labels():
    grid, chords = _grid_and_chords(
        [("verse", (C, G), 8), ("bridge", (C, G), 8), ("chorus", (C, G), 8)]
    )
    plan = default_plan(grid, chords)
    assert [p.members for p in plan] == [[i] for i in range(len(grid.sections))]
    assert [p.label for p in plan] == refine_labels(grid, chords) == ["verse", "verse", "chorus"]
    assert [(p.start_bar, p.end_bar) for p in plan] == [(0, 8), (8, 16), (16, 24)]


def test_longest_member_is_the_earlier_on_a_tie():
    grid = _grid([("verse", 8), ("verse", 8)])
    sec = PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])  # grid sections 0-8 and 8-16
    assert longest_member(sec, grid) == (0, 8)


def test_longest_member_is_the_member_with_most_bars():
    grid = _grid([("verse", 5), ("verse", 16), ("verse", 7)])
    sec = PlannedSection(start_bar=0, end_bar=28, label="verse", members=[0, 1, 2])
    assert longest_member(sec, grid) == (5, 21)


def test_one_loop_share_is_high_when_every_sung_section_shares_its_chords():
    grid_one_loop, chords_one_loop = _grid_and_chords([
        ("intro", (C,), 4), ("verse", (EM, D, G), 16), ("chorus", (G, EM, D), 8),
        ("verse", (EM, D, G), 16), ("chorus", (G, EM, D), 8),
    ])
    grid_two_groups, chords_two_groups = _grid_and_chords([
        ("verse", (C, G), 8), ("chorus", (F, BB), 8), ("verse", (C, G), 8), ("chorus", (F, BB), 8),
    ])
    assert one_loop_share(grid_one_loop, chords_one_loop) >= 0.85
    assert one_loop_share(grid_two_groups, chords_two_groups) < 0.85
    assert one_loop_share(grid_two_groups, chords_two_groups) == 0.5


def test_one_loop_share_of_a_song_with_no_sung_sections_is_zero():
    grid = _grid([("intro", 8), ("instrumental", 8), ("outro", 8)])
    assert one_loop_share(grid, _chords([C, G] * 12)) == 0.0
