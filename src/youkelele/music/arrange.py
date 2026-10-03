"""Capo choice, one-shape-per-chord voicing selection and tier simplification (pure)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

import mir_eval.chord

from youkelele.music.shapes import ShapeDB, harte_to_db, shape_cost
from youkelele.music.triads import to_triad
from youkelele.schemas import Shape

_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_NO_SHAPE_COST = 5.0
_MAX_PASSES = 20


def transpose_label(label: str, semitones: int) -> str:
    if label in ("N", "X"):
        return label
    root, quality, degrees, bass = mir_eval.chord.split(label)
    pitch = mir_eval.chord.pitch_class_to_semitone(root)
    moved = _SHARPS[(pitch + semitones) % 12]
    return mir_eval.chord.join(moved, quality, degrees, bass)


def _best_cost(label: str, db: ShapeDB) -> float | None:
    mapped = harte_to_db(label)
    shapes = db.shapes(*mapped) if mapped else []
    return min(shape_cost(s) for s in shapes) if shapes else None


def score_capo(labels: Sequence[str], capo: int, db: ShapeDB) -> float:
    costs = []
    for label in labels:
        cost = _best_cost(transpose_label(label, -capo), db)
        costs.append(_NO_SHAPE_COST if cost is None else cost)
    mean = sum(costs) / len(costs) if costs else 0.0
    return mean + 0.3 * capo + 0.3 * max(0, capo - 3)


def choose_capo(labels: Sequence[str], db: ShapeDB, max_capo: int = 5) -> tuple[int, int]:
    best = min(range(max_capo + 1), key=lambda c: (score_capo(labels, c, db), c))
    return best, -best


def _absolute_frets(shape: Shape) -> list[int]:
    return [f if f <= 0 else f + shape.base_fret - 1 for f in shape.frets]


def _movement(a: Shape, b: Shape) -> int:
    return sum(
        abs(fa - fb)
        for fa, fb in zip(_absolute_frets(a), _absolute_frets(b))
        if fa >= 0 and fb >= 0
    )


def select_voicings(labels: Sequence[str], db: ShapeDB) -> dict[str, Shape]:
    """One shape per distinct label for the whole song, by coordinate descent."""
    candidates: dict[str, list[Shape]] = {}
    for label in dict.fromkeys(labels):
        mapped = harte_to_db(label)
        shapes = db.shapes(*mapped) if mapped else []
        if shapes:
            candidates[label] = shapes
    choice = {label: min(shapes, key=shape_cost) for label, shapes in candidates.items()}
    real = [label for label in labels if label in choice]
    counts = Counter(real)
    for _ in range(_MAX_PASSES):
        changed = False
        for label, shapes in candidates.items():
            best_total, best_shape = None, None
            for shape in shapes:
                total = shape_cost(shape) * counts[label]
                for prev, cur in zip(real, real[1:]):
                    if prev == label or cur == label:
                        a = shape if prev == label else choice[prev]
                        b = shape if cur == label else choice[cur]
                        total += 0.1 * _movement(a, b)
                if best_total is None or total < best_total:
                    best_total, best_shape = total, shape
            if best_shape != choice[label]:
                choice[label] = best_shape
                changed = True
        if not changed:
            break
    return choice


def simplify_for_tier(label: str, tier: str, db: ShapeDB) -> tuple[str, str | None]:
    if label in ("N", "X"):
        return label, None
    reason = None
    if tier == "easy":
        triad = to_triad(label)
        if triad != label:
            label, reason = triad, "easy tier: reduced to triad"
    mapped = harte_to_db(label)
    if mapped and db.shapes(*mapped):
        return label, reason
    quality = label.split("/", 1)[0].partition(":")[2] or "maj"
    triad = to_triad(label)
    mapped = harte_to_db(triad)
    if triad not in ("N", "X") and mapped and db.shapes(*mapped):
        return triad, f"no shape in chords-db for {quality}"
    return "N", "no shape; left blank"
