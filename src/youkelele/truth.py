"""Truth files (spec 1.8, section 9.1) and the scores `evaluate` prints against them (9.2).

Each reader takes one file of `truth/<run>/` and returns its records; a `#` starts a comment
at the start of a line or after whitespace (so `C# minor` is a key), and blank and
comment-only lines carry no record. A malformed record raises `TruthFormatError`. A file
with no record line reads as nothing (`[]` or None), which the caller treats as a missing
file.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import mir_eval

from youkelele.music.as_played import jaccard
from youkelele.music.compat import with_bars
from youkelele.music.key import hedge_text, relation
from youkelele.music.rhythm_distance import swap_distance
from youkelele.schemas import BarStrums, Grid, Key, SectionPattern, SourceInfo, Strums
from youkelele.titles import _comparable, _tidy

Verdict = Literal["YES", "MOSTLY", "NO"]
VERDICTS = ("YES", "MOSTLY", "NO")
RIFF_LABELS = ("riff", "strum", "mixed", "dyad", "bleed")
REST_LABELS = ("rest", "play", "tail", "contested")
RIFF_HITS = frozenset({"riff", "mixed"})  # a mixed range counts as a riff; dyad and bleed do not
RESTING = frozenset({"rest", "tail"})  # a tail carries only the previous stroke's decay
SKIPPED = frozenset({"contested"})  # the records dispute the bar; no score counts it
EDGE_COLLAR_BARS = 1  # a rest region's edge matches within one bar
_COMMENT = re.compile(r"(?:^|(?<=\s))#.*")
_FIGURE = re.compile(r"[DUx-]+")
_STRIKE = {"D": "S", "U": "S", "x": "x", "-": "-"}  # the printed alphabet as strike classes


class TruthFormatError(Exception):
    def __init__(self, path: Path, line_number: int, detail: str) -> None:
        super().__init__(f"{path}:{line_number}: {detail}")
        self.path = path
        self.line_number = line_number
        self.detail = detail


@dataclass
class PatternTruth:
    start: int
    end: int  # exclusive
    verdict: Verdict
    figure: list[str] | None  # one or two bar strings in the printed alphabet, when given


@dataclass
class RangeLabel:
    start: int
    end: int  # exclusive
    label: str


@dataclass
class KeyTruth:
    tonic: str
    mode: str
    source: str
    alternative: tuple[str, str] | None  # (tonic, mode) the sources also allow


@dataclass
class CreditsTruth:
    title: str
    artist: str


@dataclass
class PatternScore:
    start: int
    end: int
    verdict: Verdict
    printed: list[str]  # the printed row of the range's first bar (and the next, for a two-bar figure)
    figure: list[str] | None
    jaccard: float | None  # None without a figure or when the slot counts differ
    swap: int | None
    certain: bool  # the range's first bar prints black
    voted_bars: int  # the range's bars among its planned section's voted bars
    top2_margin: float | None


def _records(path: Path) -> Iterator[tuple[int, str]]:
    """(line number, text) of each record line, comments and surrounding space removed."""
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        text = _COMMENT.sub("", line).strip()
        if text:
            yield number, text


def _range(path: Path, number: int, fields: Sequence[str]) -> tuple[int, int]:
    try:
        start, end = int(fields[0]), int(fields[1])
    except ValueError:
        raise TruthFormatError(
            path, number, f"expected start and end bar numbers, got {list(fields[:2])!r}"
        ) from None
    if start < 0 or end <= start:
        raise TruthFormatError(path, number, f"expected 0 <= start < end, got {start} {end}")
    return start, end


def read_patterns(path: Path) -> list[PatternTruth]:
    """`start end verdict [figure]` per line; the figure is one or two bar strings."""
    found = []
    for number, text in _records(path):
        fields = text.split()
        if not 3 <= len(fields) <= 5:
            raise TruthFormatError(path, number, "expected 'start end verdict [figure]'")
        start, end = _range(path, number, fields)
        verdict = fields[2]
        if verdict not in VERDICTS:
            raise TruthFormatError(path, number, f"expected a verdict YES, MOSTLY or NO, got {verdict!r}")
        figure = fields[3:] or None
        if figure is not None and not all(_FIGURE.fullmatch(bar) for bar in figure):
            raise TruthFormatError(path, number, f"expected a figure of D, U, x and -, got {figure!r}")
        found.append(PatternTruth(start, end, verdict, figure))
    return found


def read_labels(path: Path) -> list[RangeLabel]:
    """`start end label` per line, for `riffs.txt` and `rests.txt`."""
    found = []
    for number, text in _records(path):
        fields = text.split()
        if len(fields) != 3:
            raise TruthFormatError(path, number, "expected 'start end label'")
        start, end = _range(path, number, fields)
        if fields[2] not in RIFF_LABELS + REST_LABELS:
            raise TruthFormatError(
                path, number,
                f"expected a label ({', '.join(RIFF_LABELS + REST_LABELS)}), got {fields[2]!r}",
            )
        found.append(RangeLabel(start, end, fields[2]))
    return found


def read_key(path: Path) -> KeyTruth | None:
    """`tonic mode source`, and an optional second line for an alternative; None when the
    file holds no record line (the sources settle no key)."""
    keys = []
    for number, text in _records(path):
        fields = text.split()
        if len(fields) != 3:
            raise TruthFormatError(path, number, "expected 'tonic mode source'")
        tonic, mode, source = fields
        if len(keys) == 2:
            raise TruthFormatError(path, number, "expected at most two key lines")
        try:
            mir_eval.key.validate_key(f"{tonic} {mode}")
        except ValueError as exc:
            raise TruthFormatError(path, number, f"not a key: {exc}") from None
        if mode not in ("major", "minor"):
            raise TruthFormatError(path, number, f"not a key: mode {mode!r} is not major or minor")
        keys.append((tonic, mode, source))
    if not keys:
        return None
    tonic, mode, source = keys[0]
    return KeyTruth(tonic, mode, source, keys[1][:2] if len(keys) > 1 else None)


def read_credits(path: Path) -> CreditsTruth | None:
    """The title on the first record line, the artist on the second; None when empty."""
    lines = list(_records(path))
    if not lines:
        return None
    if len(lines) < 2:
        raise TruthFormatError(path, lines[0][0], "expected the artist on a second line")
    if len(lines) > 2:
        raise TruthFormatError(path, lines[2][0], "expected only a title line and an artist line")
    return CreditsTruth(lines[0][1], lines[1][1])


def _bars(strums: Strums, grid: Grid | None = None) -> dict[int, BarStrums]:
    """Each bar's record by index, backfilled for a file before 1.6 when it can be."""
    if grid is not None:
        try:
            strums = with_bars(strums, grid)
        except ValueError:  # patterns that do not match the plan cannot be backfilled
            pass
    return {b.index: b for b in strums.bars}


def _pattern_at(strums: Strums, grid: Grid, bar: int) -> SectionPattern | None:
    """The pattern of the planned section holding `bar` (one per grid section before 1.5)."""
    spans = [(p.start_bar, p.end_bar) for p in strums.plan] or [
        (s.start_bar, s.end_bar) for s in grid.sections
    ]
    for k, (start, end) in enumerate(spans):
        if start <= bar < end:
            return strums.patterns[k] if k < len(strums.patterns) else None
    return None


def _strikes(bars: Sequence[str]) -> list[str]:
    return [_STRIKE[c] for bar in bars for c in bar]


def _first_holding(t: PatternTruth, records: dict[int, BarStrums]) -> int:
    """The range's first bar that holds: a resting bar prints an empty black row and judges
    nothing. A range whose recorded bars all rest reads its first bar."""
    for i in range(t.start, t.end):
        if i in records and not records[i].rests:
            return i
    return t.start


def score_patterns(truth: list[PatternTruth], strums: Strums, grid: Grid) -> list[PatternScore]:
    """Each judged range against the printed row of its first bar that holds (two bars for a
    two-bar figure, whose bar strings are swapped when that bar sits an odd number of bars
    after the range's start, so the figure is read in the printed rows' phase)."""
    records = _bars(strums, grid)
    scores = []
    for t in truth:
        first = _first_holding(t, records)
        if t.figure and len(t.figure) == 2 and (first - t.start) % 2:
            t = PatternTruth(t.start, t.end, t.verdict, [t.figure[1], t.figure[0]])
        length = len(t.figure) if t.figure else 1
        rows = [records[i] for i in range(first, first + length) if i in records]
        printed = ["".join(r.pattern) for r in rows]
        comparable = t.figure is not None and len(printed) == len(t.figure) and all(
            len(p) == len(f) for p, f in zip(printed, t.figure)
        )
        heard, shown = (_strikes(t.figure), _strikes(printed)) if comparable else ([], [])
        pattern = _pattern_at(strums, grid, t.start)
        voted = set(pattern.voted_bars) if pattern is not None else set()
        scores.append(
            PatternScore(
                start=t.start, end=t.end, verdict=t.verdict, printed=printed, figure=t.figure,
                jaccard=jaccard(shown, heard) if comparable else None,
                swap=swap_distance(shown, heard) if comparable else None,
                certain=bool(rows) and not rows[0].uncertain,
                voted_bars=sum(1 for i in range(t.start, t.end) if i in voted),
                top2_margin=pattern.top2_margin if pattern is not None else None,
            )
        )
    return scores


def false_certain(scores: list[PatternScore]) -> int:
    """NO ranges printed certain."""
    return sum(1 for s in scores if s.verdict == "NO" and s.certain)


def false_grey(scores: list[PatternScore]) -> int:
    """YES or MOSTLY ranges printed grey."""
    return sum(1 for s in scores if s.verdict in ("YES", "MOSTLY") and not s.certain)


def discontinuity(strums: Strums) -> float:
    """Printed pattern changes per bar over the song's bar records."""
    bars = sorted(strums.bars, key=lambda b: b.index)
    if not bars:
        return 0.0
    changes = sum(1 for a, b in zip(bars, bars[1:]) if a.pattern != b.pattern)
    return changes / len(bars)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def score_flags(
    truth: list[RangeLabel], strums: Strums, grid: Grid
) -> tuple[float | None, float | None, float, float]:
    """(precision, recall, baseline_not_riff, baseline_riff) of the riff flag over the labelled
    ranges. A range is flagged when any of its own bar records is a riff (each bar carries
    its member's flag; a pre-1.6 file's backfilled records carry the section's); a range the
    run records no bar of falls back to its planned section's pattern, which is the longest
    member's flag. Riff and mixed are riffs, strum, dyad and bleed are not. The baselines
    are the accuracy of calling every range not a riff, and every range a riff."""
    records = _bars(strums, grid)
    flagged_hits = flagged = hits = 0
    labelled = [t for t in truth if t.label in RIFF_LABELS]
    for t in labelled:
        rows = [records[i] for i in range(t.start, t.end) if i in records]
        if rows:
            is_flagged = any(r.riff for r in rows)
        else:
            pattern = _pattern_at(strums, grid, t.start)
            is_flagged = pattern is not None and pattern.riff
        is_hit = t.label in RIFF_HITS
        flagged += is_flagged
        hits += is_hit
        flagged_hits += is_flagged and is_hit
    n = len(labelled)
    return (
        _ratio(flagged_hits, flagged),
        _ratio(flagged_hits, hits),
        (n - hits) / n if n else 0.0,
        hits / n if n else 0.0,
    )


def _regions(bars: Sequence[int]) -> list[tuple[int, int]]:
    """Runs of consecutive bar indices as (first, last)."""
    runs: list[list[int]] = []
    for i in sorted(bars):
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    return [(a, b) for a, b in runs]


def _event_f(reference: list[tuple[int, int]], estimate: list[tuple[int, int]]) -> float | None:
    """F of regions matched one to one, each edge within `EDGE_COLLAR_BARS`."""
    if not reference and not estimate:
        return None
    unmatched = list(estimate)
    matched = 0
    for first, last in reference:
        for region in unmatched:
            if abs(region[0] - first) <= EDGE_COLLAR_BARS and abs(region[1] - last) <= EDGE_COLLAR_BARS:
                unmatched.remove(region)
                matched += 1
                break
    return 2 * matched / (len(reference) + len(estimate))


def score_rests(
    truth: list[RangeLabel], strums: Strums
) -> tuple[float | None, float | None, int, int, float | None]:
    """(precision, recall, deletions, insertions, event_f) of the bars' `rests` flag over the
    labelled bars the run records. Rest and tail are rests, play is not, contested is not
    counted. A deletion is a playing bar rested (a false rest), an insertion a resting bar
    held (a false hold). The event F matches rest regions over the scored bars."""
    records = _bars(strums)
    labels = {i: t.label for t in truth if t.label in REST_LABELS for i in range(t.start, t.end)}
    scored = {i: label in RESTING for i, label in labels.items() if label not in SKIPPED and i in records}
    predicted = {i: records[i].rests for i in scored}
    hits = sum(1 for i in scored if scored[i] and predicted[i])
    deletions = sum(1 for i in scored if predicted[i] and not scored[i])
    insertions = sum(1 for i in scored if scored[i] and not predicted[i])
    event_f = _event_f(
        _regions([i for i in scored if scored[i]]), _regions([i for i in scored if predicted[i]])
    )
    return _ratio(hits, hits + deletions), _ratio(hits, hits + insertions), deletions, insertions, event_f


def score_key(truth: KeyTruth, key: Key) -> tuple[float, str, bool | None]:
    """(weighted score, category, hedge related) of the printed lead against the better of the
    truth and its alternative. The category is `relation` from that truth to the lead; the
    hedge is related when it names a key related to the truth or its alternative (None when
    the key is not hedged)."""
    truths = [(truth.tonic, truth.mode)] + ([truth.alternative] if truth.alternative else [])
    lead = f"{key.tonic} {key.mode}"
    scored = [(float(mir_eval.key.weighted_score(f"{t} {m}", lead)), (t, m)) for t, m in truths]
    best, (tonic, mode) = max(scored, key=lambda s: s[0])  # the first wins a tie
    hedge = hedge_text(key)
    related = None
    if hedge is not None:
        other, other_mode = hedge.split()
        related = any(relation(t, m, other, other_mode) != "other" for t, m in truths)
    return best, relation(tonic, mode, key.tonic, key.mode), related


def _credit(text: str | None) -> str:
    """A credit casefolded with upload-tag brackets, tag words and surrounding quotes removed."""
    return _comparable(_tidy(text or "")).strip(" -–:")


def _same_credit(expected: str, printed: str | None) -> bool:
    return printed is not None and _credit(expected) == _credit(printed)


def score_credits(truth: CreditsTruth, source: SourceInfo) -> tuple[bool, bool]:
    """Whether the printed title and artist match the truth after casefold and tag stripping."""
    return _same_credit(truth.title, source.title), _same_credit(truth.artist, source.artist)
