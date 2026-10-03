"""Stem separation through audio-separator running Demucs htdemucs_6s."""

from __future__ import annotations

import logging
import random
import re
from pathlib import Path

from youkelele.paths import cache_dir

STEMS = ("vocals", "drums", "bass", "guitar", "piano", "other")
MODEL = "htdemucs_6s.yaml"
# Demucs (shifts=2) offsets the input by random.randint before each pass. Unseeded,
# the stems differed run to run enough to flip the strum pattern on the
# end-to-end clip, so the separation runs under a fixed seed.
SHIFT_SEED = 0

_DEFAULT_NAME = re.compile(r"_\((?P<stem>[^)]+)\)_", re.IGNORECASE)


def map_stem_filename(name: str) -> str | None:
    """Map `{base}_({Stem})_{model}.wav` (any case) to a lower-case stem name."""
    match = _DEFAULT_NAME.search(name)
    if match and match.group("stem").lower() in STEMS:
        return match.group("stem").lower()
    return None


def separate_stems(
    wav: Path, out_dir: Path, model_dir: Path | None = None, log=print
) -> dict[str, Path]:
    import static_ffmpeg

    static_ffmpeg.add_paths()  # audio-separator shells out to ffmpeg at construction
    from audio_separator.separator import Separator

    out_dir = Path(out_dir).resolve()
    wav = Path(wav).resolve()
    model_dir = model_dir or cache_dir() / "models" / "audio-separator"
    model_dir.mkdir(parents=True, exist_ok=True)
    separator = Separator(
        output_dir=str(out_dir),
        model_file_dir=str(model_dir),
        output_format="WAV",
        log_level=logging.WARNING,
    )
    log(f"loading {MODEL}")
    separator.load_model(MODEL)
    log("separating stems")
    # Keys must be capitalised: the chunked code path matches them case-sensitively.
    state = random.getstate()
    random.seed(SHIFT_SEED)
    try:
        returned = separator.separate(
            str(wav), custom_output_names={s.capitalize(): s for s in STEMS}
        )
    finally:
        random.setstate(state)
    result: dict[str, Path] = {}
    for name in returned:
        base = Path(name).name  # separate() returns bare filenames
        stem = Path(base).stem if Path(base).stem in STEMS else map_stem_filename(base)
        if stem is not None:
            result[stem] = out_dir / base
    missing = [s for s in STEMS if s not in result]
    if missing:
        raise RuntimeError(f"separator did not produce stems: {', '.join(missing)}")
    return result
