import hashlib
import json
from datetime import datetime, timezone

from youkelele.manifest import Manifest, StageRecord, hash_file, load_manifest, save_manifest
from youkelele.options import RunOptions


def test_manifest_round_trip_and_hash(tmp_path):
    assert load_manifest(tmp_path) is None
    m = Manifest(
        slug="abc",
        source="https://youtu.be/abc",
        instrument="ukulele",
        options=RunOptions(source="https://youtu.be/abc", sections_k=3),
        stages={
            "grid": StageRecord(
                name="grid",
                number=2,
                finished_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
                version="1",
                input_hashes={"separate/stems/guitar.wav": "ff"},
                notes={"bpm": "120"},
            )
        },
    )
    save_manifest(tmp_path, m)
    assert load_manifest(tmp_path) == m
    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["schema"] == 1

    f = tmp_path / "a.bin"
    f.write_bytes(b"abc")
    assert hash_file(f) == hashlib.sha256(b"abc").hexdigest()
    assert hash_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
