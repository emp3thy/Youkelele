"""Ukulele chord shapes from chords-db, Harte label mapping and playing-cost scoring."""

from __future__ import annotations

import json
from pathlib import Path

from youkelele.paths import package_data
from youkelele.schemas import Shape

HARTE_TO_SUFFIX: dict[str, str] = {
    "maj": "major",
    "min": "minor",
    "dim": "dim",
    "aug": "aug",
    "7": "7",
    "min7": "m7",
    "maj7": "maj7",
    "hdim7": "m7b5",
    "dim7": "dim7",
    "sus2": "sus2",
    "sus4": "sus4",
    "sus4(b7)": "7sus4",
    "maj9": "maj9",
    "9": "9",
    "min9": "m9",
    "11": "11",
    "13": "13",
    "maj6": "6",
    "min6": "m6",
    "minmaj7": "mmaj7",
    "aug7": "aug7",
}

_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLATS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

ROOT_TO_DB_KEY: dict[str, str] = {sharp: flat for sharp, flat in zip(_SHARPS, _FLATS)}
ROOT_TO_DB_KEY.update({flat: flat for flat in _FLATS})
ROOT_TO_DB_KEY.update({"Cb": "B", "Fb": "E", "E#": "F", "B#": "C"})

_DISPLAY_SUFFIX: dict[str, str] = {
    "major": "",
    "minor": "m",
    "mmaj7": "mMaj7",
}


class ShapeDB:
    def __init__(self, data: dict) -> None:
        self._chords: dict[tuple[str, str], list[Shape]] = {}
        for key, entries in data["chords"].items():
            for entry in entries:
                self._chords[(key, entry["suffix"])] = [
                    Shape(
                        frets=list(p["frets"]),
                        fingers=list(p.get("fingers", [0, 0, 0, 0])),
                        base_fret=p.get("baseFret", 1),
                        barres=list(p.get("barres", [])),
                    )
                    for p in entry["positions"]
                ]

    @classmethod
    def load(cls, path: Path | None = None) -> ShapeDB:
        path = path if path is not None else package_data("chords-db", "ukulele.json")
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def shapes(self, root: str, suffix: str) -> list[Shape]:
        key = ROOT_TO_DB_KEY.get(root)
        if key is None:
            return []
        return list(self._chords.get((key, suffix), []))

    def display_name(self, root: str, suffix: str) -> str:
        return root + _DISPLAY_SUFFIX.get(suffix, suffix)


def _split_label(label: str) -> tuple[str, str] | None:
    """Root and quality of a Harte label with the bass dropped; None for N/X."""
    if label in ("N", "X"):
        return None
    body = label.split("/", 1)[0]
    root, _, quality = body.partition(":")
    return root, quality or "maj"


def harte_to_db(label: str) -> tuple[str, str] | None:
    parts = _split_label(label)
    if parts is None:
        return None
    root, quality = parts
    suffix = HARTE_TO_SUFFIX.get(quality)
    key = ROOT_TO_DB_KEY.get(root)
    if suffix is None or key is None:
        return None
    return key, suffix


def display_name_for(label: str, db: ShapeDB) -> str:
    """Display name keeping the label's own root spelling (C#:min is C#m, looked up as Db)."""
    parts = _split_label(label)
    mapped = harte_to_db(label)
    if parts is None or mapped is None:
        return label
    return db.display_name(parts[0], mapped[1])


def shape_cost(shape: Shape) -> float:
    fretted = [f for f in shape.frets if f > 0]
    cost = 1.5 if shape.barres else 0.0
    cost += 0.4 * len(fretted)
    cost += 0.6 * max(0, shape.base_fret - 1)
    if len(fretted) >= 2:
        cost += 0.5 * (max(fretted) - min(fretted))
    cost += 0.4 * max(0, len({f for f in shape.fingers if f > 0}) - 3)
    return cost
