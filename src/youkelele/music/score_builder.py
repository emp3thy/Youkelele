"""Build the instrument-neutral Score from the stage artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from youkelele.jsonio import ArtifactError
from youkelele.music.compat import with_bars
from youkelele.music.key import hedge_text
from youkelele.music.members import member_spans
from youkelele.music.phrase import NO_CHORD, aligned_starts, bar_change_bars
from youkelele.music.relabel import default_plan, longest_member, section_plan
from youkelele.music.trailing import trailing_silent_bars
from youkelele.schemas import (
    ArrangedChord,
    Arrangement,
    BarStrums,
    ChordDiagram,
    Chords,
    Grid,
    Instrument,
    PlannedSection,
    Riffs,
    Score,
    ScoreBar,
    ScoreChord,
    ScoreSection,
    SectionPattern,
    SourceInfo,
    Stroke,
    Strums,
    TabNote,
)

if TYPE_CHECKING:  # profiles imports the score stage, which imports this module
    from youkelele.profiles.base import Tuning

_EPS = 1e-6
SCORE_SCHEMA = 2  # 1.6: per-bar strokes, tab and grey; a state phrase per section
_RIFF_FILE = Path("riff/riff.json")  # the artifact key an ArtifactError names

# the section header's state phrases (spec 3.2), verbatim
STATE_NO_INSTRUMENT = "no strummed instrument detected"
STATE_RIFF = "riff"
STATE_RIFF_NOT_TRANSCRIBED = "riff heard, not transcribed"
STATE_UNCERTAIN = "pattern uncertain"


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


def _check_riffs_match_plan(grid: Grid, plan: list[PlannedSection], riffs: Riffs) -> None:
    """Each riff.json section must name a planned section and one of its members' spans."""
    for r in riffs.sections:
        if not 0 <= r.section < len(plan) or (r.start_bar, r.end_bar) not in member_spans(plan[r.section], grid):
            raise ArtifactError(
                _RIFF_FILE, "riff.json describes sections the plan does not have; re-run from strums"
            )


def check_strums_match_grid(grid: Grid, strums: Strums, chords: Chords, riffs: Riffs | None = None) -> None:
    """Fail clearly when grid.json was edited after strums.json was made from it, or when
    riff.json (if given) does not follow the plan strums.json carries."""
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
    # bar records (1.6) must cover grid.json's bars one to one; a file without them is backfilled
    if strums.bars and [b.index for b in strums.bars] != list(range(len(grid.bars))):
        raise ValueError(
            f"strums.json has {len(strums.bars)} bar records but grid.json has {len(grid.bars)} bars; "
            "re-run from strums"
        )
    if riffs is not None:
        _check_riffs_match_plan(grid, plan, riffs)


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


def _tab_by_bar(riffs: Riffs, spb: int) -> dict[int, list[TabNote]]:
    """Bar index -> the tab it prints, for every bar of a printable riff.

    A riff is one unit of tab (one or two bars of slots); a bar prints the unit's bar at
    its own offset from the riff's first bar, with slots counted inside the bar.
    """
    tabs: dict[int, list[TabNote]] = {}
    for r in riffs.sections:
        if not r.printable:
            continue
        unit = max(r.unit, 1)
        for b in range(r.start_bar, r.end_bar):
            lo = ((b - r.start_bar) % unit) * spb
            tabs[b] = [
                n.model_copy(update={"slot": n.slot - lo}) for n in r.riff if lo <= n.slot < lo + spb
            ]
    return tabs


def _bar_strokes(record: BarStrums) -> list[Stroke]:
    """The strokes a bar prints: its pattern's non-rest cells, ringing when its member rings
    (the flag is per member and recorded on every bar, detected strokes or not)."""
    rings = record.rings
    return [Stroke(slot=j, kind=cell, rings=rings) for j, cell in enumerate(record.pattern) if cell != "-"]


def _state(pattern: SectionPattern, bars: list[ScoreBar]) -> str:
    """The section header's state phrase (spec 3.2)."""
    if pattern.no_instrument:
        return STATE_NO_INSTRUMENT
    if any(b.tab is not None for b in bars):  # an empty list is a tab bar with no note starting in it
        return STATE_RIFF
    if pattern.riff:
        return STATE_RIFF_NOT_TRANSCRIBED
    if pattern.uncertain:
        return STATE_UNCERTAIN
    return ""


def _labels(
    k: int, planned: PlannedSection, grid: Grid, records: dict[int, BarStrums], riffs: Riffs, state: str
) -> dict[int, str]:
    """Bar index -> the small label on the first bar of a riff member buried in a merged section
    (spec 3.2). None when the header already says riff; "riff" when that member's tab printed,
    else "riff heard"."""
    if state.startswith("riff"):
        return {}
    printed = {(r.start_bar, r.end_bar) for r in riffs.sections if r.section == k and r.printable}
    labels: dict[int, str] = {}
    for s, e in member_spans(planned, grid):
        first = next((records[b] for b in range(s, e) if b in records), None)
        if first is not None and first.riff:
            labels[s] = "riff" if (s, e) in printed else "riff heard"
    return labels


def _octave_shift(k: int, planned: PlannedSection, grid: Grid, riffs: Riffs) -> int:
    """The octave shift the header names (spec 3.2): the longest member's when it prints tab, else
    the first member's (by start bar) that does, so a "riff" header never lacks its shift; 0 with no tab."""
    printed = sorted((r for r in riffs.sections if r.section == k and r.printable), key=lambda r: r.start_bar)
    span = longest_member(planned, grid)
    chosen = next((r for r in printed if (r.start_bar, r.end_bar) == span), printed[0] if printed else None)
    return chosen.octave_shift if chosen else 0


def build_score(
    source: SourceInfo,
    grid: Grid,
    chords: Chords,
    strums: Strums,
    arrangement: Arrangement,
    riffs: Riffs,
    tuning: Tuning,
    instrument_name: str,
) -> Score:
    check_strums_match_grid(grid, strums, chords, riffs)
    strums = with_bars(strums, grid)  # a file before 1.6 gets its bar records rebuilt
    records = {b.index: b for b in strums.bars}
    plan = _plan(grid, strums, chords)
    spb = strums.slots_per_bar
    tabs = _tab_by_bar(riffs, spb)
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
            record = records[bar_idx]
            bar_pattern = record.pattern  # the bar's own record, wherever phrase alignment put it
            slot_map = starts[bar_idx]
            ordered = sorted(slot_map)
            chord_list: list[ScoreChord] = []
            for j, slot in enumerate(ordered):
                end = ordered[j + 1] if j + 1 < len(ordered) else spb
                a = slot_map[slot]
                chord_list.append(
                    ScoreChord(
                        name=a.name, diagram=diagram_index(diagrams, a), start_slot=slot,
                        slots=list(bar_pattern[slot:end]),
                        filled=chords.events[a.event].filled, passing=a.passing, power=a.power,
                    )
                )
            if chord_list and chord_list[0].start_slot > 0:
                lead = chord_list[0].start_slot
                chord_list.insert(
                    0,
                    ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=list(bar_pattern[:lead])),
                )
            if not chord_list:
                chord_list.append(
                    ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=list(bar_pattern))
                )
            tab = tabs.get(bar_idx)
            bars.append(
                ScoreBar(
                    index=bar_idx, chords=chord_list, pickup=grid.bars[bar_idx].pickup,
                    struck=bar_idx < len(strums.bar_onsets)
                    and any(slot != "-" for slot in strums.bar_onsets[bar_idx]),
                    # a tab bar's stroke row prints in full black (spec 3.4)
                    strokes=_bar_strokes(record), tab=tab,
                    # a resting bar prints black, even in a member silent only through rests (spec 7)
                    grey=record.uncertain and not record.rests and tab is None, rests=record.rests,
                )
            )
        state = _state(pattern, bars)
        labelled = _labels(k, planned, grid, records, riffs, state)
        for bar in bars:
            bar.label = labelled.get(bar.index, "")
        sections.append(
            ScoreSection(
                label=planned.label, pattern=list(pattern.slots), uncertain=pattern.uncertain,
                bars=bars, bar_repeat=pattern.bar_repeat, no_instrument=pattern.no_instrument,
                inherited_from=None, shifted=shifted,  # no section inherits from 1.6 (spec 4.5)
                explained=pattern.explained, riff=pattern.riff, members=list(planned.members),
                state=state, octave_shift=_octave_shift(k, planned, grid, riffs),
            )
        )

    return Score(
        schema_version=SCORE_SCHEMA,
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
