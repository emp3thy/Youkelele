"""Name the bridge from the chord stream (version 1.4 spec, section 3.4 and assumption A5).

The grid stage cannot tell a bridge from a once-only verse: both are a segment whose
audio matches nothing else. The chords can. A bridge introduces chords the rest of the
song never plays; a once-only verse reuses the song's own. Measured on five songs, one
section had novelty 0.73 (Summer of '69's bridge) and the other 56 had 0.00 to 0.12.

The section plan (version 1.5 spec, section 3) merges section fragments into their
neighbours by chord content: a short verse between two choruses on their chords becomes
one chorus, and a short verse or chorus joins a same-label neighbour that plays all its
chords. The plan is the single list of sections the strums stage and the score use.
"""

from __future__ import annotations

from collections.abc import Sequence

from youkelele.music.sections import vocal_flags
from youkelele.schemas import Chords, Grid, PlannedSection

BRIDGE_NOVEL_CHORDS = 0.5  # share of a section's chord-bars on chords no other section plays
BRIDGE_MIN_VOCAL = 0.5  # the bridge is sung, not an instrumental break
BRIDGE_CANDIDATE_LABELS = frozenset({"verse", "chorus", "bridge"})
_EPS = 1e-6

FRAGMENT_BARS = 8  # a verse or chorus shorter than this is a fragment (band: above 7, at most 16)
ONE_LOOP_SHARE = 0.85  # largest chord group's share of the sung bars (band 0.77 to 0.93)
CHORD_MATCH_DISTANCE = 0.35  # containment distance for a chord match (band 0.29 to 0.40)
SUNG_LABELS = frozenset({"verse", "chorus"})  # the only labels that merge or absorb


def _bar_triads(grid: Grid, chords: Chords) -> list[set[str]]:
    """Per bar, the triads of the non-N events overlapping it."""
    per_bar: list[set[str]] = [set() for _ in grid.bars]
    events = [e for e in chords.events if e.triad not in ("N", "X")]
    for bar in grid.bars:
        per_bar[bar.index] = {
            e.triad for e in events if e.start < bar.end - _EPS and e.end > bar.start + _EPS
        }
    return per_bar


def section_novelty(grid: Grid, chords: Chords) -> list[float]:
    """Per section, the share of its chord-bars that hold a triad no other section plays.

    A chord-bar is a bar with at least one non-N event over it; it is novel when any of
    its triads occurs in no other section. A section with no chord-bars scores 0.
    """
    per_bar = _bar_triads(grid, chords)
    in_section = [
        set().union(*per_bar[s.start_bar : s.end_bar]) for s in grid.sections
    ]
    result: list[float] = []
    for i, section in enumerate(grid.sections):
        elsewhere: set[str] = set().union(*(t for j, t in enumerate(in_section) if j != i))
        bars = [t for t in per_bar[section.start_bar : section.end_bar] if t]
        novel = sum(1 for t in bars if t - elsewhere)
        result.append(novel / len(bars) if bars else 0.0)
    return result


def refine_labels(grid: Grid, chords: Chords) -> list[str]:
    """The section labels for the score: the grid's, with the bridge decided by the chords.

    Among sections labelled verse, chorus or bridge, the single section whose novelty is
    at least BRIDGE_NOVEL_CHORDS, that is neither first nor last, and whose vocal share
    is at least BRIDGE_MIN_VOCAL becomes `bridge` (the vocal test is skipped when the
    grid stored no vocal levels). Every other `bridge` becomes `verse`. `intro`,
    `instrumental`, `outro` and any hand-edited label pass through.
    """
    labels = [s.label for s in grid.sections]
    novelty = section_novelty(grid, chords)
    flags = vocal_flags(grid.bar_vocal_db) if grid.bar_vocal_db else None
    last = len(labels) - 1

    def is_candidate(i: int) -> bool:
        if i in (0, last) or labels[i] not in BRIDGE_CANDIDATE_LABELS:
            return False
        if novelty[i] < BRIDGE_NOVEL_CHORDS:
            return False
        if flags is None:
            return True
        section = grid.sections[i]
        sung = flags[section.start_bar : section.end_bar]
        return sum(sung) / len(sung) >= BRIDGE_MIN_VOCAL

    candidates = [i for i in range(len(labels)) if is_candidate(i)]
    bridge = candidates[0] if len(candidates) == 1 else None
    return [
        "bridge" if i == bridge else "verse" if label == "bridge" else label
        for i, label in enumerate(labels)
    ]


def bar_triad_strings(grid: Grid, chords: Chords) -> list[str]:
    """One token per bar: the bar's triads sorted and joined with `+`, `N` when none."""
    return _triad_strings(_bar_triads(grid, chords))


def _triad_strings(per_bar: list[set[str]]) -> list[str]:
    return ["+".join(sorted(t)) if t else "N" for t in per_bar]


def _levenshtein(a: Sequence[str], b: Sequence[str]) -> int:
    """Edit distance (insert, delete, substitute, each costing 1) between two sequences."""
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, start=1):
        current = [i]
        for j, y in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def containment_distance(a: Sequence[str], b: Sequence[str]) -> float:
    """How far the shorter sequence is from lying inside the longer (research M2).

    The edit distance of the shorter sequence against every window of its length in the
    longer, the windows also shifted one bar before the start and one bar past the end
    (the part of such a window outside the longer sequence is dropped, not padded), the
    least of them divided by the shorter length. 0.0 when the shorter sequence is empty.
    """
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    n, total = len(short), len(long)
    if n == 0:
        return 0.0
    best = min(
        _levenshtein(short, long[max(start, 0) : min(start + n, total)])
        for start in range(-1, total - n + 2)
    )
    return best / n


def pair_novelty(
    grid: Grid, chords: Chords, fragment: tuple[int, int], neighbour: tuple[int, int]
) -> float:
    """Share of the fragment's chord-bars holding a triad the neighbour never plays.

    `fragment` and `neighbour` are bar ranges (start, end exclusive). 0.0 when the
    fragment has no chord-bars.
    """
    return _pair_novelty(_bar_triads(grid, chords), fragment, neighbour)


def _pair_novelty(
    per_bar: list[set[str]], fragment: tuple[int, int], neighbour: tuple[int, int]
) -> float:
    played: set[str] = set().union(*per_bar[neighbour[0] : neighbour[1]])
    bars = [t for t in per_bar[fragment[0] : fragment[1]] if t]
    novel = sum(1 for t in bars if t - played)
    return novel / len(bars) if bars else 0.0


def default_plan(grid: Grid, chords: Chords) -> list[PlannedSection]:
    """One planned section per grid section, labelled by `refine_labels`."""
    labels = refine_labels(grid, chords)
    return [
        PlannedSection(start_bar=s.start_bar, end_bar=s.end_bar, label=labels[i], members=[i])
        for i, s in enumerate(grid.sections)
    ]


def _bars(section: PlannedSection) -> int:
    return section.end_bar - section.start_bar


def _span(section: PlannedSection) -> tuple[int, int]:
    return (section.start_bar, section.end_bar)


def _join(sections: Sequence[PlannedSection], label: str) -> PlannedSection:
    """One planned section over consecutive sections, their members concatenated."""
    return PlannedSection(
        start_bar=sections[0].start_bar,
        end_bar=sections[-1].end_bar,
        label=label,
        members=[m for s in sections for m in s.members],
    )


def _sandwich_merge(
    plan: list[PlannedSection], per_bar: list[set[str]]
) -> list[PlannedSection] | None:
    """The plan with the first sandwiched verse joined to its choruses, or None if none."""
    for i in range(1, len(plan) - 1):
        before, middle, after = plan[i - 1], plan[i], plan[i + 1]
        if (
            middle.label == "verse"
            and _bars(middle) < FRAGMENT_BARS
            and before.label == "chorus"
            and after.label == "chorus"
            and _pair_novelty(per_bar, _span(middle), _span(before)) == 0.0
            and _pair_novelty(per_bar, _span(middle), _span(after)) == 0.0
        ):
            return plan[: i - 1] + [_join(plan[i - 1 : i + 2], "chorus")] + plan[i + 2 :]
    return None


def _fragment_merge(
    plan: list[PlannedSection], per_bar: list[set[str]], strings: list[str]
) -> list[PlannedSection] | None:
    """The plan with the first fragment joined to its neighbour, or None if none joins."""
    for i, fragment in enumerate(plan):
        if fragment.label not in SUNG_LABELS or _bars(fragment) >= FRAGMENT_BARS:
            continue
        eligible = [
            j
            for j in (i - 1, i + 1)
            if 0 <= j < len(plan)
            and plan[j].label == fragment.label
            and _bars(plan[j]) >= _bars(fragment)
            and _pair_novelty(per_bar, _span(fragment), _span(plan[j])) == 0.0
        ]
        if not eligible:
            continue
        own = strings[fragment.start_bar : fragment.end_bar]
        # min keeps the first of equal distances, so the earlier neighbour wins a tie
        j = min(
            eligible,
            key=lambda k: containment_distance(own, strings[plan[k].start_bar : plan[k].end_bar]),
        )
        lo = min(i, j)
        return plan[:lo] + [_join(plan[lo : lo + 2], fragment.label)] + plan[lo + 2 :]
    return None


def section_plan(grid: Grid, chords: Chords) -> list[PlannedSection]:
    """The sections the strums stage and the score use (version 1.5 spec, section 3.1).

    Starts from `default_plan` and merges one pair or triple at a time until nothing
    changes, the sandwich rule always tried before the fragment rule:

    - Sandwich: a `verse` shorter than FRAGMENT_BARS between two `chorus` sections, with
      pair novelty 0 against each, becomes one `chorus` spanning the three.
    - Fragment: a `verse` or `chorus` shorter than FRAGMENT_BARS joins a neighbour with
      the same label that is at least as long and against which its pair novelty is 0.
      With two such neighbours, the lower containment distance of bar-triad strings wins,
      the earlier on a tie.

    Only `verse` and `chorus` merge or absorb, so `intro`, `instrumental`, `outro` and
    `bridge` stay as they are. Every merge removes a section, so the loop ends.
    """
    per_bar = _bar_triads(grid, chords)
    strings = _triad_strings(per_bar)
    plan = default_plan(grid, chords)
    while True:
        merged = _sandwich_merge(plan, per_bar)
        if merged is None:
            merged = _fragment_merge(plan, per_bar, strings)
        if merged is None:
            return plan
        plan = merged


def longest_member(section: PlannedSection, grid: Grid) -> tuple[int, int]:
    """The bar range of the member grid section with most bars, the earlier on a tie.

    A merged section's strum is read over this range: the fragment is absorbed for
    naming, not for strumming (spec section 3.3). With no members, the section's own span.
    """
    spans = [(grid.sections[m].start_bar, grid.sections[m].end_bar) for m in section.members]
    if not spans:
        return _span(section)
    # max keeps the first of equal lengths, so the earlier member wins a tie
    return max(spans, key=lambda s: s[1] - s[0])


def one_loop_share(grid: Grid, chords: Chords) -> float:
    """The largest chord group's share of the sung bars (research 3.2 and 4.5).

    Sung sections are those `refine_labels` calls verse or chorus. Two sung sections match
    when the containment distance of their bar-triad strings is at most
    CHORD_MATCH_DISTANCE; a group is a connected set of matches. 0.0 with no sung bars.
    """
    labels = refine_labels(grid, chords)
    strings = bar_triad_strings(grid, chords)
    sung = [i for i, label in enumerate(labels) if label in SUNG_LABELS]
    seqs = {i: strings[grid.sections[i].start_bar : grid.sections[i].end_bar] for i in sung}
    total = sum(len(s) for s in seqs.values())
    if total == 0:
        return 0.0
    unvisited, largest = set(sung), 0
    while unvisited:
        first = min(unvisited)
        unvisited.discard(first)
        stack, bars = [first], 0
        while stack:
            i = stack.pop()
            bars += len(seqs[i])
            for j in sorted(unvisited):
                if containment_distance(seqs[i], seqs[j]) <= CHORD_MATCH_DISTANCE:
                    unvisited.discard(j)
                    stack.append(j)
        largest = max(largest, bars)
    return largest / total
