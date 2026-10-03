# Ukulele Tab Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `youkelele` command-line tool that turns a YouTube URL or local audio file into a readable, printable ukulele chord-and-strum sheet (HTML and PDF) through a chain of restartable, file-based stages.

**Architecture:** Eight numbered stages communicate only through validated JSON and WAV files in a per-song run folder. The first four stages are instrument-agnostic; an instrument profile supplies the rest. One `score.json` is rendered to HTML and PDF from a single template. Heavy models sit behind small adapter functions that stages receive by injection, so every stage is testable with fakes in seconds.

**Tech Stack:** Python 3.12 (uv), pydantic 2, argparse, yt-dlp[default,deno], static-ffmpeg, audio-separator[cpu] with Demucs htdemucs_6s, beat-this, vendored Chord-CNN-LSTM (music-x-lab ISMIR 2019), librosa 1.0, mir_eval 0.8, Jinja2, alphaTab 1.8.4 (vendored), Playwright 1.63.0, pytest.

**Spec:** `docs/superpowers/specs/2026-10-03-ukulele-tab-chain-design.md` (read it first; the two `2026-10-03-assumption-checks-*.md` files beside it hold the verified install recipes, the alphaTex example and the strum pattern table that this plan cites).

## Global Constraints

- `requires-python = "==3.12.*"`; interpreter managed by uv. uv lives at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`; use `uv run` for every command in this plan.
- All inference on CPU. No CUDA, XPU or DirectML code paths.
- Stages never import one another; they communicate only through files under `runs/<slug>/NN_<stage>/`. A stage writes into a temporary folder that the runner moves into place on success.
- Every JSON artifact carries `"schema": 1` and is a pydantic model validated on load and save.
- Artifact keys are `<stage name>/<file>` (for example `grid/grid.json`); folders on disk are `NN_<stage name>`.
- Times are float seconds from the start of `00_ingest/audio.wav` (44.1 kHz, stereo, 16-bit).
- Strum slot tokens are exactly `D`, `U`, `x`, `-`.
- Dependencies declared in `pyproject.toml`: `yt-dlp[default,deno]`, `static-ffmpeg`, `audio-separator[cpu]`, `audioread`, `beat-this`, `torch` (PyPI CPU wheel, no custom index), `librosa>=1.0`, `soundfile`, `mir_eval`, `numpy`, `scipy`, `scikit-learn`, `pydantic>=2`, `jinja2`, `playwright==1.63.0`, `h5py`, `joblib`, `pydub`, `pretty_midi` (the last two are imported by the vendored chord model at inference; found missing by the models spike). Dev: `pytest`, `pytest-cov`.
- Licences: ship `LICENSE` files beside everything vendored (alphaTab MPL-2.0, Bravura OFL, chords-db MIT, Chord-CNN-LSTM MIT). Nothing non-commercial or unlicensed is installed by default.
- The `--separator roformer-sw` and `--chord-model chordmini` option values are parsed and rejected with "not implemented in this version" in version one. The default paths are the deliverable.
- UK spelling in user-facing text. No em-dashes in generated output.
- Commit after every task with the message style shown and the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Confidence Summary

Every task carries a `**Confidence:**` percentage: how sure we are that we have enough information to complete it reliably to a high standard. Tasks at or above 85% rest on verified facts from the assumption-check reports. The weak points, and what would raise them before or during implementation:

| Task | Confidence | What would raise it |
|---|---|---|
| 10 Strums | 65% | Run onset detection on the real guitar stems of the two target songs once Tasks 6 to 8 exist, inspect the bar slot vectors by eye against the UkuTabs and Ultimate Guitar patterns, and tune the three thresholds before writing the Viterbi tests. A half-day spike. |
| 14 End to end | 70% | Generate the synthetic clip early (it has no dependencies) and run Beat This! and the chord model on it during Tasks 8 and 9; adjust the clip, not the assertion, if they disagree. |
| 8 Grid | 75% | Try the Laplacian segmentation on the two target songs' audio once Task 6 exists and compare boundaries with the Hooktheory section list in the research notes. |
| 9 Harmony | 80% | Do the pinned clone and hash computation as the very first step of the task; everything after is verified. |
| 11 Arrange | 80% | Print the chosen shapes for the two target songs and have a ukulele player read them; adjust `shape_cost` weights from that. |
| 13 Render | 80% | Render one real sheet to PDF and check page breaks and diagram legibility by eye before writing the SVG tests in stone. |

Tasks 10 and 14 are the only ones where the plan's tests could all pass while the product is still poor. Treat their confidence as a signal to look at real output, not just green tests.

## Review Focus

1. **Unreachable or private YouTube video.** A person pastes a URL that yt-dlp cannot fetch. Expected: three retries with backoff, then a one-line failure naming the URL and the yt-dlp error, no run folder left half-made. Test added to Task 6.
2. **Hand-edited `grid.json` whose sections no longer cover every bar.** A person deletes a section while fixing labels. Expected: the next stage refuses with the file name and the field path, not an index error deep in strums. Test added to Task 2.
3. **Guitar stem is near-silent** (keyboard-driven song, or separation failed on the guitar). Expected: strum onsets come from the full mix, `strums.json` says `"source": "mix"`, and the sheet header says so. Test added to Task 10.
4. **Chord label with no shape in chords-db** (for example `E:aug7`, or an inversion such as `A:min/b3`). Expected: inversion dropped, unknown quality reduced to its triad, substitution recorded, never a crash. Test added to Task 11.
5. **Song in 3/4 given with `--meter 3/4`.** Expected: six or twelve slots per bar, only 3/4 patterns in the vocabulary, `\ts 3 4` in the alphaTex, and the strum box drawn with three beats. Tests added to Tasks 10 and 12.

---

### Task 1: Project scaffold and CLI entry point

**Confidence:** 95%

**Files:**
- Create: `pyproject.toml`, `.python-version`, `src/youkelele/__init__.py`, `src/youkelele/cli.py`, `tests/__init__.py`, `tests/test_cli.py`
- Modify: `.gitignore` (add `runs/`, `.venv/`, `*.egg-info/`, `.pytest_cache/`, `tests/fixtures/generated/`)
- Modify: `README.md` (add a "Tool" section pointing at `src/youkelele` and the spec)

**Interfaces:**
- Produces: console script `youkelele` calling `youkelele.cli.main(argv: list[str] | None = None) -> int`; `youkelele.__version__: str = "0.1.0"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
from youkelele.cli import main

def test_version_flag_prints_version(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'youkelele'` (after `uv sync`, `ImportError` on `main`).

- [ ] **Step 3: Create `pyproject.toml` with `[project]` name `youkelele`, version `0.1.0`, `requires-python = "==3.12.*"`, the dependency list from Global Constraints, `[project.scripts] youkelele = "youkelele.cli:main"`, hatchling build backend with `src` layout, `[tool.pytest.ini_options] testpaths = ["tests"]` and a `slow` marker. Write `.python-version` containing `3.12`. Implement `main` with argparse and a `--version` action in `src/youkelele/cli.py`.**

Subcommands `run`, `stages`, `status`, `setup`, `evaluate` are registered here as parser names only; later tasks fill their handlers.

- [ ] **Step 4: Sync and run tests**

Run: `uv sync && uv run pytest tests/test_cli.py -v`
Expected: PASS. Also run `uv run python -c "import torch, librosa, audio_separator, beat_this, yt_dlp, static_ffmpeg, deno, playwright, mir_eval; print('ok')"` and expect `ok`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .python-version uv.lock .gitignore README.md src tests
git commit -m "feat: scaffold youkelele package and CLI entry point"
```

---

### Task 2: Artifact schemas

**Confidence:** 95%

**Files:**
- Create: `src/youkelele/schemas.py`, `src/youkelele/jsonio.py`, `tests/test_schemas.py`

**Interfaces:**
- Produces, in `schemas.py` (all pydantic `BaseModel`, all with `schema_version: int = Field(1, alias="schema")`, `model_config = ConfigDict(populate_by_name=True)`):
  - `Slot = Literal["D", "U", "x", "-"]`
  - `Meter(numerator: int, denominator: int)` with `classmethod parse(text: str) -> Meter` for `"4/4"`.
  - `SourceInfo(url: str | None, path: str | None, video_id: str | None, title: str, artist: str | None, duration: float, sample_rate: int, channels: int, fetched_at: datetime)`
  - `Bar(index: int, start: float, end: float, beats: list[int])`
  - `Section(label: str, start_bar: int, end_bar: int, confidence: float)` where `end_bar` is exclusive.
  - `Grid(bpm: float, meter: Meter, beats: list[float], downbeats: list[int], bars: list[Bar], sections: list[Section])` with validators: beats strictly increasing; every downbeat index in range; bars indexed 0..n-1 in order; sections in order, contiguous, first `start_bar == 0`, last `end_bar == len(bars)`.
  - `Key(tonic: str, mode: Literal["major", "minor"], confidence: float)`
  - `ChordEvent(bar: int, beat: int, start: float, end: float, label: str, triad: str, confidence: float)`
  - `Chords(key: Key, events: list[ChordEvent])`
  - `SectionPattern(section: int, slots: list[Slot], confidence: float, uncertain: bool)`
  - `Strums(slots_per_bar: int, source: Literal["guitar_stem", "mix"], patterns: list[SectionPattern], bar_onsets: list[list[Slot]])` with validator: every slot list has length `slots_per_bar`.
  - `Shape(frets: list[int], fingers: list[int], base_fret: int, barres: list[int])` (frets in diagram order left to right, G C E A for ukulele, -1 muted).
  - `ArrangedChord(event: int, name: str, shape: Shape)`
  - `Substitution(event: int, original: str, chosen: str, reason: str)`
  - `Arrangement(capo: int, transpose: int, tier: Literal["easy", "full"], chords: list[ArrangedChord], substitutions: list[Substitution])`
  - `Instrument(name: str, strings: int, tuning: list[str], capo: int)`
  - `ChordDiagram(name: str, shape: Shape)`
  - `ScoreChord(name: str, diagram: int, start_slot: int, slots: list[Slot])`
  - `ScoreBar(index: int, chords: list[ScoreChord])`
  - `ScoreSection(label: str, pattern: list[Slot], uncertain: bool, bars: list[ScoreBar])`
  - `Score(instrument: Instrument, title: str, artist: str | None, key: str, bpm: float, meter: Meter, tier: str, slots_per_bar: int, strum_source: Literal["guitar_stem", "mix"], chord_diagrams: list[ChordDiagram], sections: list[ScoreSection])`
- Produces, in `jsonio.py`: `load_model(path: Path, model: type[T]) -> T` and `save_model(path: Path, obj: BaseModel) -> None`; both raise `ArtifactError(path: Path, detail: str)` whose `str()` is `"<path>: <field.path>: <message>"` for validation failures.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_schemas.py
def test_grid_rejects_sections_that_do_not_cover_all_bars(tmp_path):
    grid = make_grid(n_bars=8)                      # helper in this test file: 4/4, 120 bpm, one section
    grid["sections"] = [{"label": "verse", "start_bar": 0, "end_bar": 6, "confidence": 1.0}]
    (tmp_path / "grid.json").write_text(json.dumps(grid))
    with pytest.raises(ArtifactError) as e:
        load_model(tmp_path / "grid.json", Grid)
    assert "grid.json" in str(e.value) and "sections" in str(e.value)

def test_grid_rejects_unsorted_beats(tmp_path): ...   # beats [0.0, 1.0, 0.5] -> ArtifactError mentioning "beats"

def test_strums_rejects_wrong_slot_length(): ...     # slots_per_bar 8, a pattern of 7 slots -> ValidationError

def test_meter_parse(): assert Meter.parse("3/4") == Meter(numerator=3, denominator=4)

def test_round_trip_preserves_schema_alias(tmp_path):
    save_model(tmp_path / "k.json", Chords(key=Key(tonic="C", mode="major", confidence=1.0), events=[]))
    assert json.loads((tmp_path / "k.json").read_text())["schema"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the models and `jsonio` as specified in Interfaces.**

Use `model_validator(mode="after")` for the Grid and Strums rules. `save_model` writes `model_dump_json(by_alias=True, indent=2)` to a temp file in the same directory and `os.replace`s it into place.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/schemas.py src/youkelele/jsonio.py tests/test_schemas.py
git commit -m "feat: add validated artifact schemas and JSON IO"
```

---

### Task 3: Stage contract, run layout, manifest and options

**Confidence:** 92%

**Files:**
- Create: `src/youkelele/options.py`, `src/youkelele/stage.py`, `src/youkelele/layout.py`, `src/youkelele/manifest.py`, `src/youkelele/paths.py`, `tests/test_layout.py`, `tests/test_manifest.py`

**Interfaces:**
- `options.py`: `RunOptions(BaseModel)` with `source: str`, `instrument: str = "ukulele"`, `tier: Literal["easy","full"] = "easy"`, `beat_octave: Literal["none","half","double"] = "none"`, `meter: str = "4/4"`, `separator: Literal["demucs","roformer-sw"] = "demucs"`, `chord_model: Literal["cnn-lstm","chordmini"] = "cnn-lstm"`.
- `paths.py`: `cache_dir() -> Path` returning `$YOUKELELE_CACHE` or `~/.youkelele`; `package_data(*parts) -> Path` resolving inside `src/youkelele/data`; `vendor_dir(*parts) -> Path` resolving inside `src/youkelele/vendor`.
- `stage.py`:
  - `class Stage(ABC)`: class attributes `name: ClassVar[str]`, `requires: ClassVar[tuple[str, ...]]`, `produces: ClassVar[tuple[str, ...]]`; abstract `run(self, ctx: StageContext) -> None`.
  - `class StageContext`: constructed by the runner with `(layout: RunLayout, options: RunOptions, out_dir: Path, log: Callable[[str], None])`; methods `input(key: str) -> Path` (raises `MissingArtifact(key, producer: str)` if absent), `output(key: str) -> Path` (path inside `out_dir`, asserting the key is in `produces`), `note(key: str, value: str)` recorded into the manifest stage record.
  - `class MissingArtifact(Exception)` with `.key` and `.producer`.
- `layout.py`: `class RunLayout(run_dir: Path, stage_names: Sequence[str])` with `folder(stage: str) -> Path` (`run_dir / f"{number:02d}_{stage}"`), `path(key: str) -> Path`, `producer(key: str) -> str` (stage name before the slash), `number(stage: str) -> int`; `slug_for(source: str) -> str` returning the YouTube video id for a URL (regex over `v=`, `youtu.be/`, `shorts/`) or the file stem for a path, lower-cased, non-alphanumerics replaced by `-`.
- `manifest.py`: `StageRecord(name: str, number: int, finished_at: datetime, version: str, input_hashes: dict[str, str], notes: dict[str, str])`; `Manifest(slug: str, source: str, instrument: str, options: RunOptions, stages: dict[str, StageRecord])`; `load_manifest(run_dir) -> Manifest | None`; `save_manifest(run_dir, m)`; `hash_file(path) -> str` (sha256 hex, streamed).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_layout.py
def test_slug_for_youtube_variants():
    for url in ["https://www.youtube.com/watch?v=eFjjO_lhf9c", "https://youtu.be/eFjjO_lhf9c", "https://youtube.com/shorts/eFjjO_lhf9c"]:
        assert slug_for(url) == "efjjo_lhf9c"

def test_slug_for_local_path(): assert slug_for(r"C:\music\Summer Of 69.mp3") == "summer-of-69"

def test_layout_maps_key_to_numbered_folder(tmp_path):
    lay = RunLayout(tmp_path, ["ingest", "separate", "grid"])
    assert lay.path("grid/grid.json") == tmp_path / "02_grid" / "grid.json"
    assert lay.producer("grid/grid.json") == "grid"

# tests/test_manifest.py
def test_manifest_round_trip_and_hash(tmp_path): ...  # save, load, equal; hash_file of b"abc" == known sha256
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_layout.py tests/test_manifest.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the five modules as specified in Interfaces.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_layout.py tests/test_manifest.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/options.py src/youkelele/stage.py src/youkelele/layout.py src/youkelele/manifest.py src/youkelele/paths.py tests/test_layout.py tests/test_manifest.py
git commit -m "feat: add stage contract, run layout, manifest and options"
```

---

### Task 4: Runner and instrument profile registry

**Confidence:** 90%

**Files:**
- Create: `src/youkelele/runner.py`, `src/youkelele/profiles/__init__.py`, `src/youkelele/profiles/base.py`, `src/youkelele/profiles/ukulele.py`, `tests/test_runner.py`, `tests/fakes.py`

**Interfaces:**
- `profiles/base.py`: `@dataclass(frozen=True) Tuning(name: str, pitches: tuple[str, ...], reentrant: bool)` where `pitches` are in diagram order left to right; `@dataclass(frozen=True) InstrumentProfile(name: str, tuning: Tuning, stages: tuple[Stage, ...])`.
- `profiles/ukulele.py`: `UKULELE_TUNING = Tuning("gCEA", ("G4", "C4", "E4", "A4"), reentrant=True)`; `def ukulele_profile() -> InstrumentProfile` returning stages `()` for now (Task 14 fills it).
- `profiles/__init__.py`: `PROFILES: dict[str, Callable[[], InstrumentProfile]] = {"ukulele": ukulele_profile}`; `get_profile(name: str) -> InstrumentProfile` raising `KeyError` with the list of known names.
- `runner.py`:
  - `GENERIC_STAGES: tuple[Stage, ...]` (empty for now; Tasks 6 to 9 append).
  - `build_chain(profile: InstrumentProfile, generic: Sequence[Stage] = GENERIC_STAGES) -> list[Stage]` (concatenation, shared `RenderStage` appended by Task 13).
  - `resolve_stage(chain: Sequence[Stage], ref: str) -> int` accepting a number or a name; `ValueError` otherwise.
  - `check_requirements(chain, layout: RunLayout, start: int, end: int) -> list[MissingArtifact]`: for stages `start..end`, every `requires` key must exist on disk or be produced by a stage in `start..end` with a lower index.
  - `run_chain(run_dir: Path, chain: Sequence[Stage], options: RunOptions, start: int = 0, end: int | None = None, log=print) -> Manifest`: refuses on missing requirements (raises `MissingArtifact` of the first); for each stage creates `out_dir = run_dir / f".tmp_{NN}_{name}"`, runs it, deletes any existing stage folder, renames `out_dir` into place, records `StageRecord` with hashes of all `requires` files, saves manifest after each stage; on exception re-raises `StageFailed(stage: str, number: int, cause: Exception, resume_command: str)` and leaves the tmp folder deleted and earlier outputs intact.
  - `status(run_dir: Path, chain) -> list[tuple[str, Literal["done","stale","missing"]]]` where stale means any recorded input hash differs from the file on disk now.
- `tests/fakes.py`: `make_fake_stage(name, requires, produces, body=None, fail=False) -> Stage` that writes `produces` files containing their own key, or raises `RuntimeError("boom")` if `fail`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_runner.py
def test_run_from_zero_creates_numbered_folders_and_manifest(tmp_path): ...  # two fake stages -> 00_a/a.txt, 01_b/b.txt, manifest.stages has both
def test_from_refuses_when_input_missing(tmp_path):
    chain = [fake("a", (), ("a/a.txt",)), fake("b", ("a/a.txt",), ("b/b.txt",))]
    with pytest.raises(MissingArtifact) as e:
        run_chain(tmp_path, chain, opts, start=1)
    assert e.value.key == "a/a.txt" and e.value.producer == "a"
def test_failure_leaves_earlier_outputs_and_no_tmp(tmp_path): ...  # second stage fails -> 00_a exists, no .tmp_* dirs, StageFailed.resume_command contains "--from 1"
def test_rerun_from_later_stage_reuses_saved_options(tmp_path): ...  # first run tier=full; run_chain(start=1, options=None) -> stage sees tier full
def test_status_reports_stale_after_input_edit(tmp_path): ...  # edit 00_a/a.txt after run -> status says ("b", "stale")
def test_resolve_stage_by_name_and_number(): ...
def test_get_profile_unknown_lists_names(): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_runner.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `runner.py` and the profile modules as specified.**

`run_chain` with `options=None` loads them from the existing manifest; with options given, saves the merged result. Version string comes from `youkelele.__version__`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_runner.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/runner.py src/youkelele/profiles tests/test_runner.py tests/fakes.py
git commit -m "feat: add chain runner with resume, atomic outputs and profile registry"
```

---

### Task 5: Preflight and CLI commands `run`, `stages`, `status`

**Confidence:** 95%. Spike (models report, Spike A): static-ffmpeg 3.0 installs into `static_ffmpeg.run.get_platform_dir()` and writes `installed.crumb` there; presence without download is `crumb and ffmpeg.exe and ffprobe.exe exist`; `run.get_or_fetch_platform_executables_else_raise()` returns `(ffmpeg, ffprobe)` and downloads only when the crumb is missing.

**Files:**
- Create: `src/youkelele/preflight.py`, `tests/test_preflight.py`
- Modify: `src/youkelele/cli.py`, `tests/test_cli.py`

**Interfaces:**
- `preflight.py`: `@dataclass Problem(what: str, fix: str)`; `check_environment(options: RunOptions, stages_to_run: Sequence[str], probes: Probes = default_probes()) -> list[Problem]`. `Probes` is a dataclass of callables so tests can fake them: `ffmpeg_dir() -> Path | None` (returns `Path(static_ffmpeg.run.get_platform_dir())` when `installed.crumb`, `ffmpeg.exe` and `ffprobe.exe` all exist there, else `None`; never downloads; the fix text is `youkelele setup`), `deno_bin() -> Path | None` (`deno.find_deno_bin()`), `chromium_present() -> bool` (Playwright's executable path exists), `chord_model_present() -> bool` (Task 9's `vendoring.chord_model_ready()`). Rules: ffmpeg needed if `ingest` or `separate` runs; deno if `ingest` runs with a URL source; chromium if `render` runs; chord model if `harmony` runs. Unsupported option values (`roformer-sw`, `chordmini`) produce a Problem with fix text "not implemented in this version; use the default".
- `cli.py`: `run` builds `RunOptions`, computes slug, chain and `start`/`end`, calls `check_environment`, prints each Problem as `what` then `  fix: ...` and returns 2 if any; otherwise `run_chain`. `stages` prints `NN name  reads: ...  writes: ...`. `status <slug>` prints one line per stage. `--runs-dir` defaults to `runs`. On `StageFailed` prints the stage, the cause and the resume command, returns 1.

- [ ] **Step 1: Write the failing tests**

```python
def test_preflight_requires_ffmpeg_for_ingest(): ...     # probes.ffmpeg_dir -> None, stages ["ingest"] -> one Problem mentioning ffmpeg
def test_preflight_skips_ffmpeg_when_starting_at_grid(): ...
def test_preflight_rejects_roformer(): ...               # options.separator "roformer-sw" -> Problem containing "not implemented"
def test_stages_command_lists_numbered_stages(capsys): ...  # output has "00 " first line (empty chain -> header only is acceptable until Task 14, assert exit 0)
def test_run_returns_2_and_prints_fix_when_preflight_fails(tmp_path, capsys, monkeypatch): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_preflight.py tests/test_cli.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `preflight.py` and the three CLI handlers.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_preflight.py tests/test_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/preflight.py src/youkelele/cli.py tests/test_preflight.py tests/test_cli.py
git commit -m "feat: add preflight checks and run/stages/status commands"
```

---

### Task 6: Ingest stage

**Confidence:** 95%. Spike (audio report, Task 6): the library options below downloaded both target songs through the pip-installed Deno and ffmpeg; the debug line read `JS runtimes: deno-2.9.7`. Residual risk is YouTube itself changing, which the retry and error reporting cover.

**Files:**
- Create: `src/youkelele/models/__init__.py`, `src/youkelele/models/ytdl.py`, `src/youkelele/models/ffmpeg.py`, `src/youkelele/stages/__init__.py`, `src/youkelele/stages/ingest.py`, `tests/test_stage_ingest.py`, `tests/audio_fixtures.py`
- Modify: `src/youkelele/runner.py` (`GENERIC_STAGES = (IngestStage(),)`)

**Interfaces:**
- `models/ffmpeg.py`: `ffmpeg_paths() -> tuple[Path, Path]` (ffmpeg, ffprobe from static-ffmpeg, fetching on first call); `to_wav(src: Path, dst: Path) -> None` running `ffmpeg -y -i src -ac 2 -ar 44100 -sample_fmt s16 dst`; `probe_duration(path: Path) -> float` via ffprobe JSON.
- `models/ytdl.py`: `@dataclass DownloadResult(audio_path: Path, info: dict)`; `download_audio(url: str, out_dir: Path, retries: int = 3) -> DownloadResult` using `yt_dlp.YoutubeDL` with `format: "bestaudio/best"`, `outtmpl: str(out_dir / "source.%(ext)s")`, `writeinfojson: True`, `ffmpeg_location: str(ffmpeg_paths()[0].parent)` (a directory is accepted), `js_runtimes: {"deno": {"path": str(deno.find_deno_bin())}}` (the only config key is `path`); the downloaded file is `info["requested_downloads"][0]["filepath"]`; build a fresh options dict per call because `YoutubeDL` mutates it; backoff 2, 4, 8 seconds; raises `DownloadError(url, last_error)`. Log lines must tolerate non-ASCII titles on a cp1252 console (encode with `errors="replace"`).
- `stages/ingest.py`: `class IngestStage(Stage)` with `name = "ingest"`, `requires = ()`, `produces = ("ingest/audio.wav", "ingest/source.json")`; constructor `IngestStage(downloader=download_audio, converter=to_wav, prober=probe_duration)`. Treats `options.source` as a URL if it starts with `http`, else as a path. Writes `SourceInfo` (title from info `title`, artist from info `artist` or `uploader`, else file stem; `video_id` from info `id`).
- `tests/audio_fixtures.py`: `write_sine_wav(path, seconds, sr=44100, freq=220.0, channels=2)`; `write_click_track(path, seconds, bpm, sr=44100)`; `write_chord_loop(path, labels: list[str], bar_seconds, sr=44100)` synthesising triads as summed sines.

- [ ] **Step 1: Write the failing tests**

```python
def test_ingest_local_file_writes_wav_and_source(tmp_path): ...  # fake converter copies file; source.json title == stem, path set, url None
def test_ingest_url_uses_downloader_and_info(tmp_path): ...     # fake downloader returns DownloadResult with info {"id":"abc","title":"T","artist":"A"}
def test_download_retries_three_times_then_raises(monkeypatch): ...  # fake YoutubeDL raising -> 3 attempts, DownloadError str contains url
def test_to_wav_real_ffmpeg_produces_44100_stereo(tmp_path):      # marked slow: uses static-ffmpeg; checks soundfile.info
    pytest.importorskip("static_ffmpeg"); ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_stage_ingest.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the three modules; register `IngestStage()` in `GENERIC_STAGES`.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_stage_ingest.py -v -m "not slow"` then `uv run pytest tests/test_stage_ingest.py -v -m slow`
Expected: PASS both.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/models src/youkelele/stages src/youkelele/runner.py tests/test_stage_ingest.py tests/audio_fixtures.py
git commit -m "feat: add ingest stage with yt-dlp and ffmpeg adapters"
```

---

### Task 7: Separate stage

**Confidence:** 95%. Spike (audio report, Task 7): `custom_output_names` with capitalised stem keys produced exactly `vocals.wav` to `other.wav` on a real song; `separate()` returns bare filenames to join with `output_dir`; measured 0.5x real time with cached weights.

**Files:**
- Create: `src/youkelele/models/separator.py`, `src/youkelele/stages/separate.py`, `tests/test_stage_separate.py`
- Modify: `src/youkelele/runner.py` (append `SeparateStage()`)

**Interfaces:**
- `models/separator.py`: `STEMS = ("vocals", "drums", "bass", "guitar", "piano", "other")`; `separate_stems(wav: Path, out_dir: Path, model_dir: Path | None = None, log=print) -> dict[str, Path]`: imports `static_ffmpeg` and calls `add_paths()` before constructing `audio_separator.separator.Separator(output_dir=str(out_dir), model_file_dir=str(model_dir or cache_dir()/"models"/"audio-separator"), output_format="WAV")`, `load_model("htdemucs_6s.yaml")`, `separate(str(wav), custom_output_names={"Vocals": "vocals", "Drums": "drums", "Bass": "bass", "Guitar": "guitar", "Piano": "piano", "Other": "other"})` (keys must be capitalised: the chunked code path matches them case-sensitively); `separate()` returns bare filenames, so join each with `out_dir`; keep a regex fallback that maps the default `{base}_({Stem})_{model}.wav` form, case-insensitive, in case a future version ignores the custom names.
- `stages/separate.py`: `class SeparateStage(Stage)` with `name="separate"`, `requires=("ingest/audio.wav",)`, `produces=tuple(f"separate/stems/{s}.wav" for s in STEMS)`; constructor `SeparateStage(separator=separate_stems)`; notes `model=htdemucs_6s.yaml` and `licence=MIT (Demucs repository; no separate weight statement)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_separate_stage_writes_six_named_stems(tmp_path): ...  # fake separator writes six files -> all produces present
def test_stem_name_mapping_from_audio_separator_filenames(): ...  # fallback: "source_(Guitar)_htdemucs_6s.wav" -> "guitar"
def test_separate_passes_capitalised_custom_output_names(): ...     # fake Separator records kwargs; keys == {"Vocals","Drums","Bass","Guitar","Piano","Other"}
def test_separate_real_model_on_two_seconds(tmp_path):            # marked slow; downloads weights; asserts six WAVs with same length as input
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_stage_separate.py -v -m "not slow"`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement both modules; append `SeparateStage()` to `GENERIC_STAGES`.**

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_stage_separate.py -v -m "not slow"` then once `uv run pytest tests/test_stage_separate.py -v -m slow`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/models/separator.py src/youkelele/stages/separate.py src/youkelele/runner.py tests/test_stage_separate.py
git commit -m "feat: add separate stage using audio-separator with Demucs htdemucs_6s"
```

---

### Task 8: Grid stage (beats, tempo, bars, sections)

**Confidence:** 75%. Beat This! is verified, but the Laplacian segmentation on bar-synchronous features and the heuristic section labeller are our own design with no ground truth yet; the synthetic ABAB test and the `k` heuristic may need tuning on real songs.

**Files:**
- Create: `src/youkelele/models/beats.py`, `src/youkelele/music/__init__.py`, `src/youkelele/music/tempo.py`, `src/youkelele/music/sections.py`, `src/youkelele/stages/grid.py`, `tests/test_tempo.py`, `tests/test_sections.py`, `tests/test_stage_grid.py`
- Modify: `src/youkelele/runner.py` (append `GridStage()`)

**Interfaces:**
- `models/beats.py`: `@dataclass BeatResult(beats: list[float], downbeats: list[float])`; `detect_beats(wav: Path) -> BeatResult` using `beat_this.inference.Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)` on audio read with `soundfile` (mono mix, native rate passed as `sr`); `CHECKPOINT = "final0"`.
- `music/tempo.py`: `bpm_from_beats(beats: Sequence[float]) -> float` (60 / median interval); `apply_beat_octave(beats, downbeats, mode: Literal["none","half","double"]) -> tuple[list[float], list[float]]` (half keeps every other beat starting from the first downbeat; double inserts midpoints); `downbeat_indices(beats, downbeats, tol=0.07) -> list[int]`; `build_bars(beats: Sequence[float], downbeat_idx: Sequence[int], meter: Meter, duration: float) -> list[Bar]` (a bar spans one downbeat to the next; a leading partial bar before the first downbeat becomes bar 0 if it holds at least one beat; the final bar ends at `duration`).
- `music/sections.py`: `beat_sync_features(y: np.ndarray, sr: int, beats: Sequence[float]) -> np.ndarray` (CQT chroma + MFCC stacked, synced to beats with `librosa.util.sync`); `segment_boundaries(features: np.ndarray, bars: Sequence[Bar], k: int | None = None) -> list[int]` (Laplacian method from the librosa tutorial on bar-synchronous features: recurrence_matrix(width=3, mode="affinity", sym=True) -> timelag_filter(median) -> laplacian -> eigh -> KMeans with k chosen as `max(3, min(8, round(n_bars / 8)))` when None; boundaries at cluster changes, snapped to bar starts, minimum section length 2 bars); `label_sections(boundaries: Sequence[int], cluster_ids: Sequence[int], n_bars: int) -> list[Section]` using: first segment "intro" if it is not the most repeated cluster; the most frequent cluster "chorus"; the second "verse"; a cluster that occurs once in the middle "bridge"; a last segment that is a new cluster "outro"; others "verse 2", "verse 3" and so on; confidence 0.5 for every heuristic label.
- `stages/grid.py`: `class GridStage(Stage)` with `name="grid"`, `requires=("ingest/audio.wav",)`, `produces=("grid/grid.json",)`; constructor `GridStage(detector=detect_beats)`; applies `options.beat_octave`, `Meter.parse(options.meter)`, writes `Grid`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tempo.py
def test_bpm_from_regular_beats(): assert bpm_from_beats([0, 0.5, 1.0, 1.5]) == pytest.approx(120)
def test_half_octave_keeps_downbeat_aligned_beats(): ...   # beats at 0.25 s spacing, downbeats every 8 -> every other beat from first downbeat, downbeats preserved
def test_double_octave_inserts_midpoints(): ...
def test_build_bars_handles_pickup_and_tail(): ...         # beats 0.5..., first downbeat at 1.5 -> bar 0 is [0.5,1.5) pickup; last bar ends at duration
# tests/test_sections.py
def test_segment_boundaries_recovers_abab_structure(): ... # synthetic features: 32 bars, pattern A(8) B(8) A(8) B(8) with noise -> boundaries [8,16,24] within +-1
def test_label_sections_names_most_repeated_cluster_chorus(): ...
def test_sections_cover_all_bars_contiguously(): ...       # output validates as Grid sections
# tests/test_stage_grid.py
def test_grid_stage_writes_valid_grid_with_fake_detector(tmp_path): ...  # click track 120 bpm fixture; fake detector; bpm approx 120; meter from options "3/4" -> numerator 3
def test_grid_stage_real_beat_this_on_click_track(tmp_path): ...        # slow; 20 s click at 120 bpm -> bpm within 118..122
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tempo.py tests/test_sections.py tests/test_stage_grid.py -v -m "not slow"`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the four modules; append `GridStage()` to `GENERIC_STAGES`.**

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_tempo.py tests/test_sections.py tests/test_stage_grid.py -v -m "not slow"` then `-m slow`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/models/beats.py src/youkelele/music src/youkelele/stages/grid.py src/youkelele/runner.py tests/test_tempo.py tests/test_sections.py tests/test_stage_grid.py
git commit -m "feat: add grid stage with Beat This!, tempo octave, bars and Laplacian sections"
```

---

### Task 9: Chord model vendoring, harmony stage, triads and key

**Confidence:** 92%. Spike (models report, Spike B): the exact subprocess form ran on Windows with spaces and a drive letter in both paths, on the synthetic clip and both full songs (about 14 seconds per song); commit and hashes below are measured; the two missing dependencies are now declared.

**Files:**
- Create: `src/youkelele/vendoring.py`, `src/youkelele/models/chords.py`, `src/youkelele/music/triads.py`, `src/youkelele/music/key.py`, `src/youkelele/music/snap.py`, `src/youkelele/stages/harmony.py`, `tests/test_triads.py`, `tests/test_key.py`, `tests/test_snap.py`, `tests/test_stage_harmony.py`, `tests/test_vendoring.py`
- Modify: `src/youkelele/cli.py` (`setup` command), `src/youkelele/preflight.py` (use `chord_model_ready`), `src/youkelele/runner.py` (append `HarmonyStage()`)

**Interfaces:**
- `vendoring.py`: `CHORD_MODEL_REPO = "https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition"`, `CHORD_MODEL_COMMIT = "481f4ce703f8822b99f4037e9104ba1760e21ea3"`, `CHORD_MODEL_CHECKPOINT_SHA256` for the five `cache_data/joint_chord_net_ismir_naive_v1.0_reweight(0.0,10.0)_s{N}.best.sdict` files: s0 `921b42d5d1cf9ce1c0c0e45a74d409b8066e0acec46058ef74e24ee0fb540761`, s1 `bcb75859e0efa256696cf5da396b320093317b9b1d9560c304f46c25fe1f8b17`, s2 `acddf85c3fff29954c4877021177d72e2cba9f729ce80c1010f054c477bf3f61`, s3 `65d81a3ab73435aaaade586981b4cabdf57b8953d76052703e6968c32ef8421c`, s4 `5ff6b0ec85640e17a09a9b3de68c93fdd45adc24488e8fa9be5715c28d561122`; `chord_model_dir() -> Path` = `cache_dir()/"models"/"chord_cnn_lstm"`; `ensure_chord_model(log=print) -> Path` (git clone, `git checkout` the pinned commit if absent, apply `patch_numpy_aliases(dir)` which replaces the regex `\bnp\.int\b` with `int` in `extractors/xhmm_ismir.py` (7 sites), `extractors/xhmm_decoder.py` (7), `results_ismir2017.py` (1) and `extractors/beat_preprocess.py` (2), then verify checkpoint hashes, raising `VendoringError` on mismatch); `chord_model_ready() -> bool`.
- `models/chords.py`: `@dataclass LabelSpan(start: float, end: float, label: str)`; `recognise_chords(wav: Path, work_dir: Path, log=print) -> list[LabelSpan]` calls `static_ffmpeg.add_paths()` first (so the child's pydub finds ffmpeg and stays silent), then runs `[sys.executable, "chord_recognition.py", str(wav), str(work_dir/"out.lab"), "submission"]` with `cwd=chord_model_dir()`, streams stderr to `log`, parses the tab-separated `.lab`. Label boundaries lag true changes by 0.1 to 0.4 s, which the beat snapping absorbs.
- `music/triads.py`: `TRIAD_TEMPLATES: dict[str, frozenset[int]]` for `maj {0,4,7}`, `min {0,3,7}`, `dim {0,3,6}`, `aug {0,4,8}`, `sus4 {0,5,7}`, `sus2 {0,2,7}`; `to_triad(label: str) -> str`: `N` and `X` unchanged; `mir_eval.chord.split(label, reduce_extended_chords=True)`, `quality_to_bitmap`, take semitones `< 8` where bit set, pick the template equal to that set, else the template with the largest overlap preferring `maj`; return `join(root, quality)` with no bass; on `InvalidChordException` return `f"{root}:maj"` if a root parses else the label unchanged.
- `music/key.py`: `KRUMHANSL_MAJOR`, `KRUMHANSL_MINOR` (the 12-value Krumhansl-Kessler profiles); `estimate_key(chroma_mean: np.ndarray) -> Key` correlating against the 24 rotated profiles, confidence = (best - second best) / best clipped to [0, 1]; `chroma_mean_for(wav: Path) -> np.ndarray` using `librosa.feature.chroma_cqt` on the mono signal.
- `music/snap.py`: `snap_to_beats(spans: Sequence[LabelSpan], grid: Grid) -> list[ChordEvent]`: for each beat, the label covering the largest share of it; adjacent beats with equal labels merge into one event; `confidence` = covered share averaged over the merged beats; `triad = to_triad(label)`; `bar`/`beat` from `grid.bars`.
- `stages/harmony.py`: `class HarmonyStage(Stage)` with `name="harmony"`, `requires=("ingest/audio.wav", "grid/grid.json")`, `produces=("harmony/chords.json",)`; constructor `HarmonyStage(recogniser=recognise_chords, chroma=chroma_mean_for)`; notes `model=chord_cnn_lstm@<commit>` and `checkpoints=<comma-joined sha256 prefixes>`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_triads.py (parametrised with the verified table from the tools check report)
@pytest.mark.parametrize("label,triad", [("C#:min7","C#:min"),("G:7","G:maj"),("F:maj7","F:maj"),("A:hdim7","A:dim"),("D:sus4(b7)","D:sus4"),("E:dim7","E:dim"),("C:maj/5","C:maj"),("C:min9","C:min"),("C:maj6","C:maj"),("C:minmaj7","C:min"),("C:13","C:maj"),("N","N"),("X","X"),("E:aug7","E:maj")])
def test_to_triad(label, triad): assert to_triad(label) == triad
# tests/test_key.py
def test_estimate_key_c_major_from_scale_chroma(): ...   # chroma mean of C major scale weights -> tonic "C", mode "major"
def test_estimate_key_a_minor_prefers_minor_profile(): ...
# tests/test_snap.py
def test_snap_merges_adjacent_equal_labels_and_sets_bar_beat(): ...
def test_snap_majority_label_within_beat(): ...
# tests/test_stage_harmony.py
def test_harmony_stage_writes_chords_with_triads(tmp_path): ...   # fake recogniser returns C-G-Am-F spans; fake chroma -> events triads ["C:maj","G:maj","A:min","F:maj"]
def test_harmony_real_model_on_synthetic_loop(tmp_path): ...      # slow; requires chord_model_ready(); chord loop fixture 16 s -> set of triads superset of {"C:maj","G:maj","A:min","F:maj"}
# tests/test_vendoring.py
def test_patch_numpy_aliases_rewrites_only_np_int(tmp_path): ...  # "np.int(3) np.int64 np.integer" -> "int(3) np.int64 np.integer"; returns {"extractors/xhmm_ismir.py": 7, ...} counts on the real clone (slow)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_triads.py tests/test_key.py tests/test_snap.py tests/test_stage_harmony.py tests/test_vendoring.py -v -m "not slow"`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the modules as specified. Add `youkelele setup` calling `ensure_chord_model` and fetching ffmpeg via `ffmpeg_paths()`. Append `HarmonyStage()` to `GENERIC_STAGES`.**

The commit and hashes are already pinned above from the spike; verify them once after cloning rather than recomputing.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_triads.py tests/test_key.py tests/test_snap.py tests/test_stage_harmony.py tests/test_vendoring.py -v -m "not slow"`, then `uv run youkelele setup` and `uv run pytest tests/test_stage_harmony.py -v -m slow`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/vendoring.py src/youkelele/models/chords.py src/youkelele/music src/youkelele/stages/harmony.py src/youkelele/cli.py src/youkelele/preflight.py src/youkelele/runner.py tests
git commit -m "feat: add harmony stage with vendored Chord-CNN-LSTM, triad reduction and key"
```

---

### Task 10: Strums stage (onsets, slots, vocabulary, Viterbi)

**Confidence:** 65%. The slot quantisation, direction rule, emission function and thresholds (mute flatness 0.3, usable-stem RMS ratio 0.05, uncertainty floor 0.45) are our own design with no measurement on real audio; the fake-driven tests will pass, but real-world pattern accuracy is unknown until the two target songs are run and the thresholds tuned.

**Files:**
- Create: `src/youkelele/data/strum_patterns.json`, `src/youkelele/music/onsets.py`, `src/youkelele/music/strum_vocab.py`, `src/youkelele/stages/strums.py`, `tests/test_onsets.py`, `tests/test_strum_vocab.py`, `tests/test_stage_strums.py`

**Interfaces:**
- `data/strum_patterns.json`: `{"sources": [three URLs from the rendering check report, B4], "patterns": [{"meter": "4/4", "slots": "D-DU-UDU", "name": "island strum"}, ...]}` containing the 37 4/4 eight-slot rows of the B4 table, the 16-slot `D-DU-UDU-UDU-UD-` (marked `"span_bars": 2`, excluded in version one by the loader), the 3/4 patterns `D-DUD-` and `D-DUDU`, and the 6/8 patterns `D--D-U` and `D-UD-U`. Names only where the table gives one. No prose copied.
- `music/onsets.py`: `@dataclass Onsets(times: np.ndarray, flatness: np.ndarray)`; `detect_onsets(y: np.ndarray, sr: int) -> Onsets` (`librosa.onset.onset_detect(units="time", backtrack=False)` on spectral flux, with `librosa.feature.spectral_flatness` sampled at each onset frame); `stem_is_usable(stem: np.ndarray, mix: np.ndarray) -> bool` (RMS ratio stem/mix >= 0.05); `choose_slots_per_bar(onsets: Onsets, bars: Sequence[Bar], meter: Meter) -> int` (returns `meter.numerator * 2`, or `* 4` if more than 25% of onsets are nearer a sixteenth position than an eighth position); `quantise_bar(onsets: Onsets, bar: Bar, slots_per_bar: int, mute_threshold: float = 0.3) -> list[Slot]` (nearest slot per onset within half a slot; `x` if flatness > threshold else direction by `direction_for_slot`); `direction_for_slot(i: int, slots_per_bar: int, meter: Meter) -> Literal["D","U"]` (`D` when `i % (slots_per_bar // meter.numerator) == 0` or, for sixteenths, on the eighth positions; `U` otherwise).
- `music/strum_vocab.py`: `@dataclass Pattern(slots: tuple[Slot, ...], name: str | None, meter: str)`; `load_vocabulary(meter: Meter, slots_per_bar: int) -> list[Pattern]` (filters by meter; expands an 8-slot pattern to 16 slots by inserting `-` when `slots_per_bar == 16`; raises `ValueError` if empty); `emission(observed: Sequence[Slot], pattern: Pattern) -> float` (share of slots where both are strikes with equal direction, both rests, or both mutes; strike-vs-rest mismatch 0; `x` vs `D`/`U` counts 0.5); `decode_section(bars: Sequence[Sequence[Slot]], vocab: Sequence[Pattern], switch_penalty: float = 0.35) -> tuple[Pattern, float]` (Viterbi over bars maximising sum of log emissions minus penalty per switch; the section pattern is the mode of the decoded path; confidence = mean emission of that pattern over the bars that chose it times the share of bars that chose it); `UNCERTAIN_BELOW = 0.45`; `all_down(slots_per_bar, meter) -> Pattern`.
- `stages/strums.py`: `class StrumsStage(Stage)` with `name="strums"`, `requires=("separate/stems/guitar.wav", "ingest/audio.wav", "grid/grid.json")`, `produces=("strums/strums.json",)`; constructor `StrumsStage(onset_detector=detect_onsets)`. Uses the guitar stem if `stem_is_usable`, else the mix; writes `Strums` with `source` set accordingly and `uncertain=True` plus `all_down` where confidence `< UNCERTAIN_BELOW`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_onsets.py
def test_direction_for_slot_eighths_4_4(): assert [direction_for_slot(i, 8, m44) for i in range(8)] == list("DUDUDUDU")
def test_direction_for_slot_sixteenths_marks_eighths_down(): ...  # 16 slots: D at even indices
def test_quantise_bar_island_strum(): ...     # onsets at slots 0,2,3,5,6,7 of a 2 s bar -> "D-DU-UDU"
def test_quantise_bar_marks_flat_onset_muted(): ...
def test_choose_slots_per_bar_prefers_8_for_eighth_grid_and_6_for_3_4(): ...
def test_stem_is_usable_false_for_silence(): ...
# tests/test_strum_vocab.py
def test_load_vocabulary_4_4_has_at_least_30_patterns(): ...
def test_load_vocabulary_3_4_returns_only_six_slot_patterns(): ...
def test_decode_section_recovers_pattern_with_one_noisy_bar(): ...  # 8 bars of island strum, one bar random -> island strum, confidence > 0.7
def test_decode_section_low_confidence_on_random_bars(): ...        # confidence < UNCERTAIN_BELOW
# tests/test_stage_strums.py
def test_strums_stage_uses_mix_when_stem_silent(tmp_path): ...   # silent guitar stem, mix with onsets -> source == "mix"
def test_strums_stage_one_pattern_per_section_and_valid_schema(tmp_path): ...  # fake onset detector returning island-strum onsets; grid with 2 sections -> 2 patterns, slots_per_bar 8
def test_strums_stage_3_4_meter_gives_six_slots(tmp_path): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_onsets.py tests/test_strum_vocab.py tests/test_stage_strums.py -v`
Expected: FAIL with `ImportError` / `FileNotFoundError` for the data file.

- [ ] **Step 3: Implement the data file, the two music modules and the stage.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_onsets.py tests/test_strum_vocab.py tests/test_stage_strums.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/data/strum_patterns.json src/youkelele/music/onsets.py src/youkelele/music/strum_vocab.py src/youkelele/stages/strums.py tests/test_onsets.py tests/test_strum_vocab.py tests/test_stage_strums.py
git commit -m "feat: add strums stage with onset quantisation and pattern Viterbi"
```

---

### Task 11: Arrange stage (chords-db shapes, capo chooser, voicing Viterbi, tiers)

**Confidence:** 80%. chords-db and the Harte mapping are verified; the `shape_cost` weights and the capo and movement penalties are untested heuristics that may need adjusting once real sheets are read by a player.

**Files:**
- Create: `src/youkelele/data/chords-db/ukulele.json`, `src/youkelele/data/chords-db/LICENSE`, `src/youkelele/music/shapes.py`, `src/youkelele/music/arrange.py`, `src/youkelele/stages/arrange.py`, `tests/test_shapes.py`, `tests/test_arrange.py`, `tests/test_stage_arrange.py`

**Interfaces:**
- `data/chords-db/ukulele.json`: downloaded verbatim from `https://raw.githubusercontent.com/tombatossals/chords-db/master/lib/ukulele.json` with the repository `LICENSE` (MIT) beside it.
- `music/shapes.py`: `HARTE_TO_SUFFIX: dict[str, str]` = `{"maj": "major", "min": "minor", "dim": "dim", "aug": "aug", "7": "7", "min7": "m7", "maj7": "maj7", "hdim7": "m7b5", "dim7": "dim7", "sus2": "sus2", "sus4": "sus4", "sus4(b7)": "7sus4", "maj9": "maj9", "9": "9", "min9": "m9", "11": "11", "13": "13", "maj6": "6", "min6": "m6", "minmaj7": "mmaj7"}`; `ROOT_TO_DB_KEY: dict[str, str]` mapping all enharmonic spellings to chords-db keys (`C# -> Db`, `D# -> Eb`, `F# -> Gb`, `G# -> Ab`, `A# -> Bb`, and the flats to themselves); `class ShapeDB`: `classmethod load(path: Path = package_data("chords-db", "ukulele.json")) -> ShapeDB`; `shapes(root: str, suffix: str) -> list[Shape]` (empty if unknown; `Shape.frets` already in G C E A order with `-1` muted, `base_fret` from `baseFret`, `barres` from `barres`); `display_name(root: str, suffix: str) -> str` (`"C"`, `"Cm"`, `"C7"`, `"Cm7"`, `"Cmaj7"`, `"Cdim"`, `"Caug"`, `"Csus4"`, `"C7sus4"`, `"Cm7b5"`, `"Cdim7"`, `"C9"`, `"Cm9"`, `"C6"`, `"Cm6"`, `"CmMaj7"`, `"Csus2"`, `"Cmaj9"`, `"C11"`, `"C13"`); `harte_to_db(label: str) -> tuple[str, str] | None` (drops the bass, maps root and quality, `None` for `N`/`X` or unknown quality); `shape_cost(shape: Shape) -> float` = `0.0` base + `1.5` if any barre + `0.4` per fretted string + `0.6 * max(0, base_fret - 1)` + `0.5 * (max fret - min fret among fretted strings)`.
- `music/arrange.py`: `transpose_label(label: str, semitones: int) -> str` (mir_eval split/join, root moved through the 12 pitch classes using sharps); `score_capo(labels: Sequence[str], capo: int, db: ShapeDB) -> float` (sum over labels of the min `shape_cost` of shapes for the label transposed down by `capo`, plus `2.0 * capo`, plus `5.0` per label with no shape); `choose_capo(labels, db, max_capo: int = 5) -> tuple[int, int]` returning `(capo, transpose = -capo)` minimising `score_capo`; `select_voicings(labels: Sequence[str], db: ShapeDB) -> list[Shape | None]` Viterbi minimising `shape_cost(shape) + 0.3 * movement` where movement is the sum of absolute fret differences per string between consecutive shapes, muted strings ignored; `simplify_for_tier(label: str, tier: str, db: ShapeDB) -> tuple[str, str | None]` returning `(label_to_use, reason)`: for `easy`, `to_triad(label)` with reason `"easy tier: reduced to triad"` when it differs; for both tiers, if `harte_to_db` finds no shape, fall back to `to_triad` with reason `"no shape in chords-db for <quality>"`, and if still none, `"N"` with reason `"no shape; left blank"`.
- `stages/arrange.py`: `class ArrangeStage(Stage)` with `name="arrange"`, `requires=("harmony/chords.json", "grid/grid.json")`, `produces=("arrange/arrangement.json",)`; builds the label list from `chords.events`, applies tier simplification (recording `Substitution`s), chooses capo, transposes, selects voicings, writes `Arrangement` with `display_name`s. `N` events get no `ArrangedChord`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_shapes.py
def test_db_loads_552_chords_and_c_major_open_shape(): ...   # shapes("C","major")[0].frets == [0,0,0,3]
def test_harte_to_db_maps_inversion_and_7sus4(): assert harte_to_db("A:min/b3") == ("A","minor"); assert harte_to_db("D:sus4(b7)") == ("D","7sus4"); assert harte_to_db("C#:maj") == ("Db","major")
def test_harte_to_db_returns_none_for_unknown_quality(): assert harte_to_db("E:aug7") is None
def test_shape_cost_prefers_open_c_over_barre(): ...
# tests/test_arrange.py
def test_choose_capo_zero_for_c_g_am_f(): ...
def test_choose_capo_moves_eb_bb_cm_ab_to_capo_3(): ...    # Eb Bb Cm Ab -> capo 3 gives C G Am F
def test_select_voicings_minimises_movement(): ...
def test_simplify_easy_reduces_seventh_and_records_reason(): assert simplify_for_tier("G:7", "easy", db) == ("G:maj", "easy tier: reduced to triad")
def test_simplify_full_keeps_seventh(): assert simplify_for_tier("G:7", "full", db) == ("G:7", None)
def test_simplify_unknown_quality_falls_back_to_triad(): ...  # "E:aug7" -> ("E:maj", "no shape in chords-db for aug7")
# tests/test_stage_arrange.py
def test_arrange_stage_writes_shapes_and_substitutions(tmp_path): ...  # chords with G:7 in easy tier -> name "G", one substitution
def test_arrange_stage_never_crashes_on_inversion_or_unknown(tmp_path): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_shapes.py tests/test_arrange.py tests/test_stage_arrange.py -v`
Expected: FAIL.

- [ ] **Step 3: Download the JSON and LICENSE; implement the two music modules and the stage.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_shapes.py tests/test_arrange.py tests/test_stage_arrange.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/data/chords-db src/youkelele/music/shapes.py src/youkelele/music/arrange.py src/youkelele/stages/arrange.py tests/test_shapes.py tests/test_arrange.py tests/test_stage_arrange.py
git commit -m "feat: add arrange stage with chords-db shapes, capo chooser and voicing Viterbi"
```

---

### Task 12: Score stage (score.json and alphaTex)

**Confidence:** 92%. Spike (render report, Spike 2): fourteen alphaTex cases rendered, including mid-bar changes, one-slot chords, 16 slots, 3/4, capo and high-position diagrams. Two earlier assumptions were wrong and are corrected below: direction tokens must be per-beat `lyrics` properties, not a `\lyrics` line, and `{firstfret}` diagrams take absolute frets.

**Files:**
- Create: `src/youkelele/music/score_builder.py`, `src/youkelele/music/alphatex.py`, `src/youkelele/stages/score.py`, `tests/test_score_builder.py`, `tests/test_alphatex.py`, `tests/test_stage_score.py`

**Interfaces:**
- `music/score_builder.py`: `build_score(source: SourceInfo, grid: Grid, chords: Chords, strums: Strums, arrangement: Arrangement, tuning: Tuning, instrument_name: str) -> Score`. Rules: `chord_diagrams` are unique `(name, shape)` pairs in order of first appearance; each bar's chords are the arranged events starting in that bar (an event continuing from an earlier bar is repeated at `start_slot 0` without a diagram change); slot rule (verified in the render spike, case k): `start_slot = round((event.start - bar.start) / bar_len * slots_per_bar)` clamped to `[0, slots_per_bar - 1]`; an event whose rounded start equals the previous chord's `start_slot` in the same bar replaces it, so every chord lasts at least one slot; an event rounding to `slots_per_bar` belongs to the next bar at slot 0; each chord's `slots` is the section pattern sliced from its `start_slot` to the next chord's `start_slot` (or bar end); bars with no chord get one `ScoreChord(name="N.C.", diagram=-1, ...)`; `key` string is `f"{tonic} {mode}"`.
- `music/alphatex.py`: `score_to_alphatex(score: Score) -> str` producing, in order: `\title`, `\artist` (if any), `\tempo <round bpm>`, `\hideDynamics`, `.`, `\track "<instrument name>"`, `\staff {slash}`, `\tuning (<pitches reversed, e.g. A4 E4 C4 G4>) { hide }`, `\capo <n>` if capo > 0, one `\chord ("<name>" f1 f2 f3 f4) {showdiagram false ...}` per diagram with frets listed in the reversed string order as ABSOLUTE fret numbers (`x` for a muted string), plus `firstfret <base_fret>` when `base_fret > 1` and `barre <absolute fret>` for each barre (both verified: relative frets draw garbage), `\ts <num> <den>`, then per section `\section "<label>"` and per bar the beats with the direction token as a per-beat property: duration prefix `:8` for `slots_per_bar == 2 * numerator`, `:16` for `4 *`; `D` -> `(<f>.1 <f>.2 <f>.3 <f>.4){bd lyrics "D"}` (string 1 is the first tuning entry, A4; a muted string is omitted from the chord; `ch "<name>"` added inside the braces on the first beat of each chord), `U` -> same with `{bu lyrics "U"}`, `x` -> `(){ds lyrics "x"}`, `-` -> `r{lyrics "-"}`; bars separated by ` |` and newline. A staff-level `\lyrics` line must NOT be used: alphaTab skips rests when spreading it and stacks one line per directive. Must reproduce the corrected two-bar example in the render spike report (Spike 2, "verified fix") when fed the equivalent `Score`.
- `stages/score.py`: `class ScoreStage(Stage)` with `name="score"`, `requires=("grid/grid.json", "harmony/chords.json", "strums/strums.json", "arrange/arrangement.json", "ingest/source.json")`, `produces=("score/score.json", "score/score.alphatex")`; constructor `ScoreStage(tuning: Tuning, instrument_name: str)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_score_builder.py
def test_diagrams_unique_in_first_appearance_order(): ...
def test_chord_change_mid_bar_splits_slots(): ...   # C for 4 slots then G for 4 -> two ScoreChords with start_slot 0 and 4, slots lengths 4 and 4
def test_change_at_three_eighths_rounds_to_slot_3(): ...
def test_two_events_rounding_to_same_slot_later_wins(): ...
def test_event_rounding_to_bar_end_moves_to_next_bar_slot_0(): ...
def test_bar_without_chord_gets_nc(): ...
# tests/test_alphatex.py
def test_alphatex_matches_verified_two_bar_example(): ...   # Score for C island strum + G chunked -> exact string from the render spike report Spike 2 "verified fix", whitespace-normalised
def test_alphatex_uses_per_beat_lyrics_never_staff_lyrics(): ...  # output contains '{lyrics "' on every beat and never a line starting with '\lyrics'
def test_alphatex_3_4_uses_ts_3_4_and_six_slots(): ...
def test_alphatex_omits_muted_strings_and_uses_absolute_firstfret(): ...  # shape frets [-1,2,1,0] base 1 -> beat "(0.1 1.2 2.3)" and chord "x 0 1 2"; shape frets [3,3,4,5] base 3 barre 3 -> '\chord ("C" 5 4 3 3) {showdiagram false firstfret 3 barre 3}'
# tests/test_stage_score.py
def test_score_stage_writes_both_files_and_score_validates(tmp_path): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_score_builder.py tests/test_alphatex.py tests/test_stage_score.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the two modules and the stage.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_score_builder.py tests/test_alphatex.py tests/test_stage_score.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/score_builder.py src/youkelele/music/alphatex.py src/youkelele/stages/score.py tests/test_score_builder.py tests/test_alphatex.py tests/test_stage_score.py
git commit -m "feat: add score stage building score.json and alphaTex"
```

---

### Task 13: Render stage (diagrams, strum boxes, HTML template, PDF)

**Confidence:** 90%. Spike (render report, Spike 3): a 64-bar prototype with eight hand-rolled diagrams and three strum boxes printed to six A4 pages with every section intact and everything legible; the settings below are the ones that worked. The one open point is cosmetic: 16-slot bars take a full line each.

**Files:**
- Create: `src/youkelele/vendor/alphatab/alphaTab.min.js`, `src/youkelele/vendor/alphatab/font/Bravura.woff2`, `src/youkelele/vendor/alphatab/font/Bravura.woff`, `src/youkelele/vendor/alphatab/Bravura-OFL.txt`, `src/youkelele/vendor/alphatab/LICENSE`, `src/youkelele/render/__init__.py`, `src/youkelele/render/diagrams.py`, `src/youkelele/render/strum_box.py`, `src/youkelele/render/html.py`, `src/youkelele/render/templates/sheet.html.j2`, `src/youkelele/render/pdf.py`, `src/youkelele/stages/render.py`, `tests/test_diagrams.py`, `tests/test_strum_box.py`, `tests/test_html.py`, `tests/test_stage_render.py`
- Modify: `src/youkelele/runner.py` (`build_chain` appends `RenderStage()` after the profile stages)

**Interfaces:**
- Vendored alphaTab: files from the `@coderline/alphatab@1.8.4` npm tarball `dist/` as listed; `LICENSE` is the package's MPL-2.0 text.
- `render/diagrams.py`: `chord_diagram_svg(name: str, shape: Shape, string_labels: Sequence[str] = ("G","C","E","A"), frets_shown: int = 4) -> str` producing a standalone `<svg>` 80x100 px: title, four vertical strings, nut as a thick line when `base_fret == 1` else a `<text>` fret number at the left of row one, dots with finger numbers from `fingers` (0 means no number), a barre rectangle across the strings covered for each entry in `barres`, `x` above muted strings and `o` above open ones.
- `render/strum_box.py`: `strum_pattern_svg(slots: Sequence[Slot], meter: Meter) -> str`: one column per slot, beat numbers `1 & 2 &` above (`1 e & a` for sixteenths), a down arrow for `D`, an up arrow for `U`, a crossed arrow for `x`, nothing for `-`; width 28 px per slot.
- `render/html.py`: `render_html(score: Score, alphatex: str, assets_rel: str = "assets") -> str` rendering `templates/sheet.html.j2` with: header fields; a "Strum pattern uncertain" badge per uncertain section and a "Strum detected from full mix" note when `strum_source == "mix"`; the diagram legend; per section a heading, the strum box and a `<div class="at-section" data-start-bar="..." data-bar-count="...">`; the whole-song alphaTex inlined RAW (not HTML-escaped) in a `<script type="text/plain" id="tex">`; ONE `AlphaTabApi` per section, each with `{core: {useWorkers: false, tex: true, fontDirectory: assets_rel + "/font/"}, player: {playerMode: 0}, display: {scale: 0.85 (0.75 when slots_per_bar == 16), startBar: <section first bar, 1-based>, barCount: <bars in section>, layoutMode: "page"}, notation: {elements: {effectTempo: false, trackNames: false, scoreTitle: false, chordDiagrams: false, effectMarker: false, effectCapo: false}}}`; `window.__rendered = true` only when every section has fired `postRenderFinished` and `document.fonts.ready` resolved. Layout CSS: `.sheet { width: 182mm; margin: 0 auto }` on screen and `html, body { width: 182mm }` under `@media print`, because alphaTab does not reflow during `page.pdf()` and a fluid page prints shrunk. Print CSS: `@page { size: A4; margin: 14mm }`, `.section-head { break-after: avoid }`, `.section { break-inside: avoid-page }`, `.no-print { display: none }`; crop alphaTab's hard-coded "rendered by alphaTab" footer with an `overflow: hidden` wrapper. Fonts for text: system sans-serif stack, no external stylesheets.
- `render/pdf.py`: `html_to_pdf(html_path: Path, pdf_path: Path, timeout_ms: int = 60000) -> None` using `playwright.sync_api`, `chromium.launch(args=["--allow-file-access-from-files"])`, `page.goto(html_path.as_uri())`, `page.wait_for_function("window.__rendered === true")`, `page.evaluate("document.fonts.ready")`, `page.pdf(path=..., format="A4", print_background=True, prefer_css_page_size=True)`.
- `stages/render.py`: `class RenderStage(Stage)` with `name="render"`, `requires=("score/score.json", "score/score.alphatex")`, `produces=("render/sheet.html", "render/sheet.pdf")`; constructor `RenderStage(pdf_writer=html_to_pdf)`; copies the vendored alphaTab folder to `07_render/assets/` so the HTML is self-contained.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_diagrams.py
def test_open_c_has_nut_one_dot_and_three_open_markers(): ...   # count "<circle", "o" markers, nut rect present, no fret number text
def test_barre_shape_draws_rect_and_first_fret_label(): ...     # Bb: frets [3,2,1,1] barre [1] base 1 -> rect present
def test_muted_string_draws_x(): ...
# tests/test_strum_box.py
def test_island_strum_box_has_three_down_three_up_arrows(): ...
def test_3_4_box_has_six_columns_and_beat_labels_1_2_3(): ...
# tests/test_html.py
def test_html_inlines_tex_and_disables_workers(): ...   # contains 'useWorkers: false', the alphaTex text unescaped (a '\chord ("C"' literal survives), 'playerMode: 0'
def test_html_one_api_per_section_with_bar_ranges(): ...  # two sections of 8 and 4 bars -> data-start-bar 1 and 9, data-bar-count 8 and 4
def test_html_fixed_sheet_width_for_print(): ...         # CSS contains 'width: 182mm' inside @media print
def test_html_shows_uncertain_badge_and_mix_note(): ...
# tests/test_stage_render.py
def test_render_stage_writes_html_and_calls_pdf_writer(tmp_path): ...   # fake pdf_writer records paths; assets/font/Bravura.woff2 copied
def test_real_chromium_renders_pdf_from_two_bar_example(tmp_path): ...   # slow; real html_to_pdf; PDF exists and > 10 KB; rendered flag reached
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_diagrams.py tests/test_strum_box.py tests/test_html.py tests/test_stage_render.py -v -m "not slow"`
Expected: FAIL.

- [ ] **Step 3: Fetch the alphaTab tarball (`npm pack @coderline/alphatab@1.8.4` or the registry tarball URL) and copy the listed files; implement the render modules, the template and the stage; append `RenderStage()` in `build_chain`.**

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_diagrams.py tests/test_strum_box.py tests/test_html.py tests/test_stage_render.py -v -m "not slow"` then `-m slow`
Expected: PASS. Open the slow test's PDF once and confirm by eye: diagrams read G C E A left to right, slash staff present, direction tokens under each bar.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/vendor/alphatab src/youkelele/render src/youkelele/stages/render.py src/youkelele/runner.py tests/test_diagrams.py tests/test_strum_box.py tests/test_html.py tests/test_stage_render.py
git commit -m "feat: add render stage with chord diagrams, strum boxes, alphaTab page and PDF"
```

---

### Task 14: Ukulele profile wiring and end-to-end run

**Confidence:** 70%. The wiring is trivial, but the end-to-end assertion depends on the synthetic clip being musical enough for Beat This! and the chord model to recover 120 bpm and C-G-Am-F; the chord model did recognise a sine-tone loop in verification, beat tracking on a plucked envelope has not been tried.

**Files:**
- Modify: `src/youkelele/profiles/ukulele.py`, `tests/test_cli.py`
- Create: `tests/test_end_to_end.py`, `tests/fixtures/make_clip.py`

**Interfaces:**
- `ukulele_profile()` returns `InstrumentProfile("ukulele", UKULELE_TUNING, (StrumsStage(), ArrangeStage(), ScoreStage(UKULELE_TUNING, "Ukulele")))`.
- `tests/fixtures/make_clip.py`: `make_clip(path: Path, seconds: int = 30) -> None` synthesising a 120 bpm C-G-Am-F loop with an island-strum onset envelope (plucked-string style decaying sines summed per chord, a strike per `D`/`U` slot) so the real chain has something musically sensible to find. Not committed as audio; generated into `tests/fixtures/generated/`.

- [ ] **Step 1: Write the failing tests**

```python
def test_stages_command_lists_eight_ukulele_stages(capsys):
    assert main(["stages"]) == 0
    out = capsys.readouterr().out
    assert [l[:2] for l in out.splitlines() if l[:2].isdigit()] == ["00","01","02","03","04","05","06","07"]
    assert "07 render" in out

@pytest.mark.slow
def test_end_to_end_on_synthetic_clip(tmp_path):
    make_clip(tmp_path / "clip.wav")
    rc = main(["run", str(tmp_path / "clip.wav"), "--runs-dir", str(tmp_path / "runs")])
    assert rc == 0
    run = tmp_path / "runs" / "clip"
    assert (run / "07_render" / "sheet.pdf").stat().st_size > 10_000
    chords = load_model(run / "03_harmony" / "chords.json", Chords)
    assert {"C:maj", "G:maj", "A:min", "F:maj"} <= {e.triad for e in chords.events}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py::test_stages_command_lists_eight_ukulele_stages -v`
Expected: FAIL (fewer than eight stages).

- [ ] **Step 3: Wire the profile; write `make_clip`.**

- [ ] **Step 4: Run the fast test, then the slow end-to-end test (expect roughly two to four minutes, dominated by separation)**

Run: `uv run pytest tests/test_cli.py -v` then `uv run pytest tests/test_end_to_end.py -v -m slow -s`
Expected: PASS. Then run `uv run pytest -m "not slow"` and confirm the whole fast suite finishes in under 60 seconds.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/profiles/ukulele.py tests/test_cli.py tests/test_end_to_end.py tests/fixtures/make_clip.py
git commit -m "feat: wire the ukulele profile and add the end-to-end run"
```

---

### Task 15: Accuracy report (`evaluate` command) and ground-truth fixture format

**Confidence:** 90%

**Files:**
- Create: `src/youkelele/evaluate.py`, `tests/test_evaluate.py`, `tests/fixtures/ground_truth/README.md`, `tests/fixtures/ground_truth/example/beats.txt`, `tests/fixtures/ground_truth/example/chords.lab`
- Modify: `src/youkelele/cli.py` (`evaluate <slug> --truth <dir>`), `README.md` (how to run, resume, edit between stages, evaluate)

**Interfaces:**
- `evaluate.py`: `@dataclass Report(beat_f: float | None, downbeat_f: float | None, chord_root: float | None, chord_majmin: float | None, chord_triads: float | None)`; `evaluate_run(run_dir: Path, truth_dir: Path) -> Report` reading `02_grid/grid.json` and `03_harmony/chords.json`, and from `truth_dir` the optional `beats.txt` (one time per line; downbeats marked by a second column `1`) and `chords.lab` (Harte, tab-separated `start end label`); beats via `mir_eval.beat.f_measure`, chords via `mir_eval.chord.evaluate` on the full labels (`root`, `majmin`, `triads` weighted scores); `format_report(r: Report) -> str` printing one metric per line as percentages, `n/a` when the truth file is absent.
- `tests/fixtures/ground_truth/README.md`: the two file formats, and the note that the real annotations for Summer of '69 and Pour Some Sugar On Me are made by hand by the project owner and saved under `<slug>/` here; they are not part of this plan.

- [ ] **Step 1: Write the failing tests**

```python
def test_evaluate_perfect_match_scores_100(tmp_path): ...   # write grid/chords from a tiny Grid/Chords and matching truth files -> all metrics == 1.0
def test_evaluate_missing_truth_file_gives_none(tmp_path): ...
def test_cli_evaluate_prints_report(tmp_path, capsys): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_evaluate.py -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `evaluate.py`, the CLI command, the fixture README and example files; update the README with usage.**

- [ ] **Step 4: Run the whole fast suite**

Run: `uv run pytest -m "not slow" -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/evaluate.py src/youkelele/cli.py tests/test_evaluate.py tests/fixtures/ground_truth README.md
git commit -m "feat: add evaluate command with mir_eval beat and chord metrics"
```

---

## Self-review notes

- **Spec coverage.** Stages 0 to 7: Tasks 6 to 13. Profiles and renumber-safe keys: Tasks 3 and 4. Manifest, stale detection, option reuse: Tasks 3 and 4. Preflight and error reporting: Task 5 and `StageFailed` in Task 4. Schemas with field-path errors: Task 2. Vendoring and licences: Tasks 9, 11, 13. Testing layers: unit tests throughout, stage tests with fakes, runner tests in Task 4, opt-in end-to-end in Task 14, accuracy report in Task 15. Spec section 2 deferrals (`roformer-sw`, `chordmini`) are rejected by preflight rather than built, as Global Constraints state.
- **Not built by this plan.** Hand annotations for the two target songs (owner's job, format fixed in Task 15). The spec's `--separator roformer-sw` and `--chord-model chordmini` behaviours.
- **Deviation from the spec worth the owner's eye.** The spec says the chord model is vendored "into the package". Its five checkpoints total 29 MB, so this plan vendors by pinned-commit clone into the cache during `youkelele setup`, with the commit SHA and checkpoint hashes recorded in `vendoring.py` and checked on every run. The effect is the same (no run-time download, hashes verified) without 29 MB in git.
- **Type consistency checked:** `Slot`, `Meter`, `Bar`, `Section`, `Grid`, `Chords`, `Strums`, `Arrangement`, `Score` names are used identically across Tasks 2, 8 to 13. `Tuning.pitches` is diagram order (G C E A); `alphatex.py` reverses it for `\tuning`. `StageContext.input/output/note`, `RunLayout.path/producer`, `MissingArtifact(key, producer)`, `StageFailed(..., resume_command)` are used as defined in Tasks 3 and 4.
