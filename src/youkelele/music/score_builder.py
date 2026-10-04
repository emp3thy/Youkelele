"""Build the instrument-neutral Score from the stage artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from youkelele.music.key import hedge_text
from youkelele.music.phrase import NO_CHORD, aligned_starts, bar_change_bars
from youkelele.music.relabel import default_plan, section_plan
from youkelele.music.trailing import trailing_silent_bars
from youkelele.schemas import (
    ArrangedChord,
    Arrangement,
    ChordDiagram,
    Chords,
    Grid,
    Instrument,
    PlannedSection,
    Score,
    ScoreBar,
    ScoreChord,
    ScoreSection,
    SourceInfo,
    Strums,
)

if TYPE_CHECKING:  # profiles imports the score stage, which imports this module
    from youkelele.profiles.base import Tuning

_EPS = 1e-6


def _plan(grid: Grid, strums: Strums, chords: Chords) -> list[PlannedSection]:
    """The section plan strums.json carries; a 1.4 file has none, so one per grid section."""
    return strums.plan or default_plan(grid, chords)


def _planned_text(p: PlannedSection) -> str:
    return f"bars {p.start_bar} to {p.end_bar}, {p.label}, grid sections {p.members}"


def _plan_difference(stored: list[PlannedSection], current: list[PlannedSection]) -> str | None:
    """What differs between the stored plan and the one the inputs give now (the section count,
    then the first planned section that differs), or None."""
    parts: list[str] = []
    if len(stored) != len(current):
        parts.append(f"strums.json plans {len(stored)} sections but grid.json and chords.json give {len(current)}")
    for k, (old, new) in enumerate(zip(stored, current)):
        if old != new:
            parts.append(f"planned section {k} is {_planned_text(old)} in strums.json but {_planned_text(new)} now")
            break
    return "; ".join(parts) or None


def check_strums_match_grid(grid: Grid, strums: Strums, chords: Chords) -> None:
    """Fail clearly when grid.json was edited after strums.json was made from it."""
    plan = _plan(grid, strums, chords)
    n, m = len(strums.patterns), len(plan)
    if n != m:
        where = "planned sections in strums.json" if strums.plan else "sections in grid.json"
        raise ValueError(f"strums.json has {n} patterns for {m} {where}; re-run from strums")
    indices = [p.section for p in strums.patterns]
    if indices != list(range(m)):
        where = "the section plan in strums.json" if strums.plan else "grid.json"
        raise ValueError(
            f"strums.json patterns are for sections {indices} but {where} has sections "
            f"{list(range(m))}; re-run from strums"
        )
    if strums.plan:  # the plan must still be the one grid.json and chords.json give: any edit since shows
        difference = _plan_difference(strums.plan, section_plan(grid, chords))
        if difference:
            raise ValueError(
                f"strums.json's section plan no longer matches grid.json and chords.json: {difference}; "
                "re-run from strums"
            )
    num = grid.meter.numerator
    if strums.slots_per_bar not in (2 * num, 4 * num):
        raise ValueError(
            f"strums.json has slots_per_bar {strums.slots_per_bar} but grid.json meter "
            f"{num}/{grid.meter.denominator} needs {2 * num} or {4 * num}; re-run from strums"
        )


def _place_events(grid: Grid, chords: Chords, spb: int) -> list[tuple[int, int, int]]:
    """Return (bar, slot, event index) for every event that lands inside the grid."""
    bars = grid.bars
    placed: list[tuple[int, int, int]] = []
    for i, event in enumerate(chords.events):
        bar_idx = next((b.index for b in bars if b.start - _EPS <= event.start < b.end - _EPS), None)
        if bar_idx is None:
            continue
        bar = bars[bar_idx]
        slot = round((event.start - bar.start) / (bar.end - bar.start) * spb)
        slot = max(0, slot)
        if slot >= spb:
            bar_idx += 1
            slot = 0
            if bar_idx >= len(bars):
                continue
        placed.append((bar_idx, slot, i))
    return placed


def _bar_starts(
    grid: Grid, chords: Chords, arranged: dict[int, ArrangedChord], spb: int
) -> list[dict[int, ArrangedChord]]:
    """Per bar, slot -> arranged chord starting there (continuations included at slot 0)."""
    placed = _place_events(grid, chords, spb)
    per_bar: list[dict[int, ArrangedChord | None]] = [{} for _ in grid.bars]
    for bar_idx, slot, event_idx in placed:
        per_bar[bar_idx][slot] = arranged.get(event_idx)  # later event replaces earlier

    result: list[dict[int, ArrangedChord]] = []
    for bar in grid.bars:
        slots = per_bar[bar.index]
        if 0 not in slots:
            before = [p for p in placed if (p[0], p[1]) < (bar.index, 0)]
            if before:
                event_idx = max(before, key=lambda p: (p[0], p[1], p[2]))[2]
                if event_idx in arranged and chords.events[event_idx].end > bar.start + _EPS:
                    slots[0] = arranged[event_idx]
        result.append({s: a for s, a in slots.items() if a is not None})
    return result


def _bar_ends(starts: list[dict[int, ArrangedChord]]) -> list[tuple[str, str]]:
    """(first chord, last chord) per bar as placed in the score, for phrase alignment.

    Passing chords are ignored unless they are all the bar holds; a bar with no chord
    is ("N", "N"), so a change into or out of silence counts as a change.
    """
    ends: list[tuple[str, str]] = []
    for slot_map in starts:
        placed = [slot_map[slot] for slot in sorted(slot_map)]
        names = [a.name for a in placed if not a.passing] or [a.name for a in placed]
        ends.append((names[0], names[-1]) if names else (NO_CHORD, NO_CHORD))
    return ends


def build_score(
    source: SourceInfo,
    grid: Grid,
    chords: Chords,
    strums: Strums,
    arrangement: Arrangement,
    tuning: Tuning,
    instrument_name: str,
) -> Score:
    check_strums_match_grid(grid, strums, chords)
    plan = _plan(grid, strums, chords)
    spb = strums.slots_per_bar
    arranged = {a.event: a for a in arrangement.chords}
    starts = _bar_starts(grid, chords, arranged, spb)

    def diagram_index(diagrams: list[ChordDiagram], a: ArrangedChord) -> int:
        for i, d in enumerate(diagrams):
            if d.name == a.name and d.shape == a.shape:
                d.passing = d.passing and a.passing  # one full use makes a full diagram
                d.power = d.power or a.power  # one power use gives the legend line
                return i
        diagrams.append(
            ChordDiagram(name=a.name, shape=a.shape, passing=a.passing, power=a.power)
        )
        return len(diagrams) - 1

    diagrams: list[ChordDiagram] = []
    alternative: list[ChordDiagram] = []
    if arrangement.capo > 0:  # the open-position shapes, deduped as the played ones are
        for a in arrangement.no_capo_alternative:
            diagram_index(alternative, a)

    # rows follow the chord-change phrase over the planned sections; grid.json is unchanged
    aligned = aligned_starts(
        [(p.start_bar, p.end_bar) for p in plan], bar_change_bars(_bar_ends(starts))
    )

    # the strums stage calls trailing_silent_bars the same way, capped by the grid's last section,
    # to leave these bars out of the pattern; the two calls must stay in step. The bars come off
    # the planned section that ends the song.
    last = grid.sections[-1]
    drop = trailing_silent_bars(chords, grid.bars, cap=last.end_bar - last.start_bar)
    ends_song = [k for k, p in enumerate(plan) if p.end_bar == last.end_bar]

    # the labels (the bridge decided from the chords, merges named) come with the plan;
    # grid.json keeps the labeller's own names
    sections: list[ScoreSection] = []
    dropped = 0
    for k, (planned, (start_bar, end_bar, shifted)) in enumerate(zip(plan, aligned)):
        pattern = strums.patterns[k]
        if ends_song and k == ends_song[-1]:
            dropped = min(drop, max(end_bar - start_bar - 1, 0))  # phrase alignment may have shortened it
            end_bar -= dropped
        bars: list[ScoreBar] = []
        for bar_idx in range(start_bar, end_bar):
            slot_map = starts[bar_idx]
            ordered = sorted(slot_map)
            chord_list: list[ScoreChord] = []
            for j, slot in enumerate(ordered):
                end = ordered[j + 1] if j + 1 < len(ordered) else spb
                a = slot_map[slot]
                chord_list.append(
                    ScoreChord(
                        name=a.name, diagram=diagram_index(diagrams, a), start_slot=slot,
                        slots=list(pattern.slots[slot:end]),
                        filled=chords.events[a.event].filled, passing=a.passing, power=a.power,
                    )
                )
            if chord_list and chord_list[0].start_slot > 0:
                lead = chord_list[0].start_slot
                chord_list.insert(
                    0,
                    ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=list(pattern.slots[:lead])),
                )
            if not chord_list:
                chord_list.append(
                    ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=list(pattern.slots))
                )
            bars.append(
                ScoreBar(
                    index=bar_idx, chords=chord_list, pickup=grid.bars[bar_idx].pickup,
                    struck=bar_idx < len(strums.bar_onsets)
                    and any(slot != "-" for slot in strums.bar_onsets[bar_idx]),
                )
            )
        sections.append(
            ScoreSection(
                label=planned.label, pattern=list(pattern.slots), uncertain=pattern.uncertain,
                bars=bars, bar_repeat=pattern.bar_repeat, no_instrument=pattern.no_instrument,
                inherited_from=pattern.inherited_from, shifted=shifted,
                explained=pattern.explained, riff=pattern.riff, members=list(planned.members),
            )
        )

    return Score(
        instrument=Instrument(
            name=instrument_name, strings=len(tuning.pitches), tuning=list(tuning.pitches),
            capo=arrangement.capo,
        ),
        title=source.title,
        artist=source.artist,
        key=f"{chords.key.tonic} {chords.key.mode}",
        key_hedge=hedge_text(chords.key),
        bpm=grid.bpm,
        meter=grid.meter,
        tier=arrangement.tier,
        slots_per_bar=spb,
        strum_source=strums.source,
        strums_uncertain=strums.uncertain,
        chord_diagrams=diagrams,
        alternative_diagrams=alternative,
        sections=sections,
        trailing_bars_dropped=dropped,
    )
