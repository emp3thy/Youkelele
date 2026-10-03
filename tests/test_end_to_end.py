from pathlib import Path

import pytest

from tests.fixtures.make_clip import make_clip
from youkelele.cli import main
from youkelele.jsonio import load_model
from youkelele.schemas import Chords, Grid, Strums


@pytest.mark.slow
def test_end_to_end_on_synthetic_clip(tmp_path: Path):
    make_clip(tmp_path / "clip.wav")
    rc = main(["run", str(tmp_path / "clip.wav"), "--runs-dir", str(tmp_path / "runs")])
    assert rc == 0
    run = tmp_path / "runs" / "clip"
    assert (run / "07_render" / "sheet.pdf").stat().st_size > 10_000
    grid = load_model(run / "02_grid" / "grid.json", Grid)
    assert 118 <= grid.bpm <= 122 and grid.octave_decision == "none"
    chords = load_model(run / "03_harmony" / "chords.json", Chords)
    assert {"C:maj", "G:maj", "A:min", "F:maj"} <= {e.triad for e in chords.events}
    strums = load_model(run / "04_strums" / "strums.json", Strums)
    assert strums.source in ("other_stem", "mix")  # Demucs routes plucked ukulele to "other"
    main_section = max(strums.patterns, key=lambda p: p.confidence)
    assert "".join(main_section.slots) == "D-DU-UDU" and main_section.confidence >= 0.7
