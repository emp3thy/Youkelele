"""Run directory layout: run folder names, numbered stage folders and artifact keys."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

from youkelele.jsonio import ArtifactError
from youkelele.manifest import Manifest, load_manifest
from youkelele.models.ytdl import fetch_metadata
from youkelele.titles import clean_title

DEFAULT_RUNS_DIR = "runs"
# The video details fetched to name a new run folder; ingest reuses them. Not a stage artefact.
SOURCE_META_NAME = "source_meta.json"

_YOUTUBE_ID = re.compile(r"(?:[?&]v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})")


def video_id_for(source: str) -> str | None:
    """The YouTube video id in a URL, as written, or None."""
    match = _YOUTUBE_ID.search(source)
    return match.group(1) if match else None


def is_url(source: str) -> bool:
    return source.startswith(("http://", "https://"))


def _stem(source: str) -> str:
    name = re.split(r"[\\/]", source.rstrip("\\/"))[-1]
    return name.rsplit(".", 1)[0] if "." in name else name


def slug_for(source: str) -> str:
    match = _YOUTUBE_ID.search(source)
    if match:
        return match.group(1).lower()
    stem = _stem(source)
    slug = re.sub(r"[\W_]+", "-", stem.lower(), flags=re.UNICODE).strip("-")
    if not slug:
        slug = "song-" + hashlib.sha1(stem.encode("utf-8")).hexdigest()[:8]
    assert slug, "slug must not be empty"
    return slug


def title_slug(title: str) -> str:
    """A folder name from a song title: lowercase ASCII words joined by single hyphens.

    Accents fold to their base letter, apostrophes vanish ("Summer Of '69" gives
    summer-of-69), and anything else not a letter or digit separates words. A title with
    nothing left gives the empty string."""
    folded = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    folded = folded.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def _saved_runs(runs_dir: Path) -> Iterator[tuple[Path, Manifest]]:
    """Each folder directly under the runs dir with a readable manifest, by name."""
    if not runs_dir.is_dir():
        return
    for folder in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        try:
            manifest = load_manifest(folder)
        except ArtifactError:
            continue
        if manifest is not None:
            yield folder, manifest


def _manifest_video_id(manifest: Manifest) -> str | None:
    return manifest.video_id or video_id_for(manifest.source)


def _local_key(source: str) -> str:
    """One spelling for every way of writing a local file's path."""
    try:
        return os.path.normcase(str(Path(source).resolve()))
    except (OSError, RuntimeError, ValueError):
        return os.path.normcase(os.path.abspath(source))


def same_source(a: str, b: str) -> bool:
    """Whether two sources name the same thing: the same text, or the same local file."""
    if a == b:
        return True
    if is_url(a) or is_url(b):
        return False
    return _local_key(a) == _local_key(b)


def find_run_dir(runs_dir: Path, source: str) -> Path | None:
    """The saved run for a source: the same source first, then the same video id."""
    saved = list(_saved_runs(Path(runs_dir)))
    for folder, manifest in saved:
        if same_source(manifest.source, source):
            return folder
    video_id = video_id_for(source)
    if video_id is not None:
        for folder, manifest in saved:
            if _manifest_video_id(manifest) == video_id:
                return folder
    return None


def find_run_by_name(runs_dir: Path, name: str) -> Path | None:
    """A run folder by its name, or else by the video id its manifest records."""
    runs_dir = Path(runs_dir)
    if name and (runs_dir / name).is_dir():
        return runs_dir / name
    wanted = name.casefold()
    for folder, manifest in _saved_runs(runs_dir):
        video_id = _manifest_video_id(manifest)
        if video_id is not None and video_id.casefold() == wanted:
            return folder
    return None


def _taken(folder: Path, source: str, video_id: str | None) -> bool:
    """Whether a folder already belongs to some other source."""
    if not folder.exists():
        return False
    if not folder.is_dir():
        return True
    try:
        manifest = load_manifest(folder)
    except ArtifactError:
        return True
    if manifest is not None:
        return not same_source(manifest.source, source)
    meta = folder / SOURCE_META_NAME
    if meta.exists():
        # a fetch whose run never started: free again for the same video only
        try:
            saved_id = json.loads(meta.read_text(encoding="utf-8")).get("id")
        except (OSError, ValueError, AttributeError):
            return True
        return video_id is None or saved_id != video_id
    return any(folder.iterdir())


def _free_folder(runs_dir: Path, base: str, source: str, video_id: str | None) -> Path:
    candidate, number = runs_dir / base, 2
    while _taken(candidate, source, video_id):
        candidate, number = runs_dir / f"{base}-{number}", number + 1
    return candidate


_METADATA_FIELDS = ("id", "title", "uploader", "artist", "duration")


def resolve_run_dir(
    runs_dir: Path, source: str, fetch: Callable[[str], dict] = fetch_metadata
) -> tuple[Path, dict | None]:
    """The run folder for a source, and the video details when they had to be fetched.

    A saved run for the source is found by scanning manifests, with no network. A local
    file is named after its stem; a URL after its cleaned title, read by `fetch` without
    downloading, or its video id when the title leaves nothing. A name already used by
    another source gets -2, -3. Fetched details are saved beside the manifest as
    source_meta.json for ingest to reuse."""
    runs_dir = Path(runs_dir)
    found = find_run_dir(runs_dir, source)
    if found is not None:
        return found, None
    if not is_url(source):
        base = title_slug(_stem(source)) or slug_for(source)
        return _free_folder(runs_dir, base, source, None), None
    fetched = fetch(source)
    meta = {field: fetched.get(field) for field in _METADATA_FIELDS}
    raw_artist = meta["artist"] or meta["uploader"]
    base = title_slug(clean_title(meta["title"] or "", raw_artist))
    if not base:
        video_id = video_id_for(source)
        base = video_id.lower() if video_id else title_slug(str(meta["id"] or "")) or slug_for(source)
    run_dir = _free_folder(runs_dir, base, source, meta["id"])
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / SOURCE_META_NAME).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return run_dir, meta


class RunLayout:
    def __init__(self, run_dir: Path, stage_names: Sequence[str]) -> None:
        self.run_dir = Path(run_dir)
        self.stage_names = list(stage_names)

    def number(self, stage: str) -> int:
        return self.stage_names.index(stage)

    def folder(self, stage: str) -> Path:
        return self.run_dir / f"{self.number(stage):02d}_{stage}"

    def producer(self, key: str) -> str:
        return key.split("/", 1)[0]

    def path(self, key: str) -> Path:
        stage, _, rest = key.partition("/")
        return self.folder(stage) / rest
