# Youkelele tab chain: design

Date: 2026-10-03. Status: approved in conversation, awaiting written review.

## 1. Purpose

A command-line tool that takes a YouTube URL or a local audio file and produces readable, printable ukulele tablature: chords with diagrams, one strumming pattern per section, and section labels, aligned to a beat grid. It runs as a chain of numbered stages that each read the previous stages' files from a run folder and write their own. A run can start at any stage, and a person can hand-edit a stage's output and re-run from the next stage.

Version one ships the ukulele chain. The structure must let a guitar or bass chain be added later as a new instrument profile without changing the runner or the generic stages.

The tool is for the author first, with a path to a public release. Permissive licences are preferred at every stage; where the best model is non-commercial or unlicensed it is excluded by default and available behind an explicit flag.

## 2. Out of scope for version one

Riff and melody transcription to fretted tab lines, per-bar strum/riff/melody classification, lyrics, MIDI and Guitar Pro input, a review UI, audio playback in the page, a YouTube-synced cursor, the harmonic re-mix for chord recognition, and any instrument profile other than ukulele. The data formats below leave room for all of these.

## 3. Environment and constraints

- Windows 11, Intel Core Ultra 9 285H, 31 GB RAM, Intel Arc integrated graphics. No CUDA. All inference runs on CPU. Separation takes minutes per song, and the tool prints progress rather than pretending otherwise.
- Python 3.12 exactly, pinned with uv (`requires-python = "==3.12.*"`). librosa 1.0 requires 3.12 or newer, and the ChordMini pins exclude 3.13, so 3.12 is the only version the whole stack shares. uv 0.12 is installed through WinGet at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_...\uv.exe` and may not be on PATH in every shell.
- ffmpeg, yt-dlp and the Deno JavaScript runtime yt-dlp needs for YouTube are all installed from PyPI into the project environment (`yt-dlp[default,deno]`, `static-ffmpeg`), not assumed on the machine. A preflight step downloads the ffmpeg binary on first run.
- The whole dependency set resolves and imports on Python 3.12.15 on this machine (checked 2026-10-03, see the assumption-check reports beside this spec). PyTorch comes from PyPI, whose Windows wheel is the CPU build. The Intel XPU backend is ignored in version one because only Beat This! accepts a device string.
- Code lives in this repository under `src/youkelele`, with `tests/`, `docs/`, and a git-ignored `runs/`.

## 4. Architecture

### 4.1 Stages

A stage is a class with four members:

- `name`: a short identifier, for example `harmony`.
- `requires`: artifact keys it reads, for example `ingest/audio.wav`, `grid/grid.json`.
- `produces`: artifact keys it writes.
- `run(run_dir, options)`: does the work. It writes into a temporary folder and moves it into place only on success, so a crash never leaves a half-written output that a later run would trust.

Artifact keys are `<stage name>/<file>`, for example `grid/grid.json`; the runner maps a key to its numbered folder on disk, `02_grid/grid.json`, so renumbering stages when a profile adds one never changes the keys stages are written against.

Stages never import each other. They communicate only through files in the run folder. That is what makes hand-editing between stages and adding a new profile cheap.

### 4.2 Instrument profiles

A profile is a small object with a `name`, a `tuning` (string count, open-string pitches, re-entrant flag) and `stages`, the list of stages it contributes after the generic ones. Profiles are registered in a dictionary keyed by name. `--instrument` selects one; the default is `ukulele`.

### 4.3 The chain

The runner concatenates the generic stages and the profile's stages, numbers them from 0, and runs from `--from` to `--to` (defaults: 0 and the last stage). Before running it checks that every artifact required by the stages it is about to run either already exists and validates, or will be produced by an earlier stage in this same run. If something is missing it refuses, naming the missing file and the stage that would have produced it.

| # | Stage | Owner | Reads | Writes |
|---|---|---|---|---|
| 0 | ingest | generic | URL or local path | `00_ingest/audio.wav`, `00_ingest/source.json` |
| 1 | separate | generic | audio.wav | `01_separate/stems/{vocals,drums,bass,guitar,piano,other}.wav` |
| 2 | grid | generic | audio.wav | `02_grid/grid.json` |
| 3 | harmony | generic | audio.wav, grid.json | `03_harmony/chords.json` |
| 4 | strums | ukulele | stems/guitar.wav, audio.wav, grid.json | `04_strums/strums.json` |
| 5 | arrange | ukulele | chords.json, grid.json | `05_arrange/arrangement.json` |
| 6 | score | ukulele | grid.json, chords.json, strums.json, arrangement.json, source.json | `06_score/score.json`, `06_score/score.alphatex` |
| 7 | render | shared | score.json, score.alphatex | `07_render/sheet.html`, `07_render/sheet.pdf` |

The render stage is shared by all profiles. It is parameterised entirely by `score.json` and never knows which instrument it is drawing. A profile may replace it, but none needs to in version one.

### 4.4 The run folder and manifest

`runs/<slug>/` where the slug is the YouTube video id or the local file's stem. Each stage owns one numbered subfolder and writes only there. `manifest.json` at the root records the source, the instrument, the options used, and for each completed stage its finish time, the code version, and a hash of the artifacts it read. A stage whose recorded input hash no longer matches the files on disk is reported as stale by `youkelele status`, but the runner does not rebuild automatically; the person decides with `--from`.

Options are saved in the manifest. Re-running from a later stage reuses the saved options unless the command line overrides them, so a `--from 4` run uses the same tier and beat-octave as the original.

## 5. Data formats

Every JSON file carries `"schema": 1` and is validated with pydantic models on load and on save. A hand edit that breaks the schema fails fast with the field path, not deep inside a later stage. Times are floating-point seconds from the start of `audio.wav`. From `grid.json` onward, events also carry bar and beat indices so later stages reason in musical positions.

- **source.json**: url or path, video id, title, artist (both best-effort from yt-dlp metadata, editable), duration, sample rate, channels, download time.
- **grid.json**: `bpm`, `meter` (numerator, denominator), `beats` (list of seconds), `downbeats` (indices into beats), `bars` (bar index, start, end, beat indices), `sections` (label, start bar, end bar, confidence). Labels are free text; the heuristic labeller uses intro, verse, pre-chorus, chorus, bridge, solo, outro.
- **chords.json**: `key` (tonic, mode, confidence), `events` (bar, beat, start, end, label in Harte syntax such as `C#:min7`, triad reduction such as `C#:min`, confidence).
- **strums.json**: `slots_per_bar` (8 or 16), `patterns` (per section: section index, a slot vector where each slot is one of `D`, `U`, `x` for muted, `-` for rest, plus confidence), and `bar_onsets` (per bar: slot vector actually detected) kept for inspection and for a later per-bar mode.
- **arrangement.json**: `capo`, `transpose` (semitones applied to labels), `tier`, `chords` (per chord event: display name, shape as frets per string with -1 for muted, fingering hint, barre flag), `substitutions` (original label, chosen label, reason) so a person can see what `easy` changed.
- **score.json**: `instrument` (name, string count, tuning as pitches, capo), `title`, `artist`, `key`, `bpm`, `meter`, `tier`, `chord_diagrams` (unique shapes in order of first appearance), `sections` (label, strum pattern, bars), bars (chord events with display name, shape reference, slot vector). Nothing in this file is ukulele-specific; a six-string profile fills the same fields.

## 6. Stage behaviour

### 6.1 Ingest
yt-dlp with `--write-info-json` and best audio, then ffmpeg to 44.1 kHz stereo 16-bit WAV. A local path skips yt-dlp and is converted the same way. Title and artist come from the info JSON when present and are otherwise taken from the file name; both are editable in `source.json`.

YouTube extraction in 2026 requires an external JavaScript runtime, and Deno is the only one yt-dlp enables by default. The PyPI `deno` package supplies the binary, so the stage passes `--js-runtimes deno:<path from deno.find_deno_bin()>` and `--ffmpeg-location <path from static_ffmpeg>` explicitly rather than relying on PATH. Verified end to end on this machine with yt-dlp 2026.08.19, yt-dlp-ejs 0.8.0, deno 2.9.7 and static-ffmpeg 3.0.

### 6.2 Separate
audio-separator 0.47 (`audio-separator[cpu]`, MIT) running Demucs `htdemucs_6s.yaml` (Demucs code MIT), six stems including guitar. CPU only. Measured on this machine: a 240-second stereo WAV separates in about 248 seconds, roughly real time. Two install facts the stage must handle: audio-separator imports `audioread`, which librosa 1.0 no longer pulls in, so it is declared as a direct dependency; and `Separator()` shells out to `ffmpeg -version` at construction, so the stage puts the static-ffmpeg binary on PATH first. Demucs weights download from Meta's public file server on first use into a `model_file_dir` inside the project cache. The stage renames audio-separator's `<name>_(Guitar)_htdemucs_6s.wav` style outputs to the plain `stems/guitar.wav` names the rest of the chain expects.

The unlicensed BS-RoFormer-SW guitar model is not installed by default; `--separator roformer-sw` enables it for personal runs and the manifest records that a non-redistributable model was used.

### 6.3 Grid
Beat This! for beats and downbeats on CPU (`pip install beat-this` 1.1.0, MIT including the weights per the maintainer; `Audio2Beats(device="cpu", dbn=False)`; the 77 MB `final0` checkpoint downloads from the JKU server into the torch hub cache on first use and its name is recorded in the manifest; madmom is only needed for the optional `--dbn` postprocessing, which is not used). Measured here: a 30-second clip in 1.7 seconds. The stage passes a WAV path, which Beat This! reads through soundfile, because `torchaudio.load` on torchaudio 2.11 raises without TorchCodec. Tempo from the median beat interval. `--beat-octave half|double` halves or doubles the beat list after detection, which handles the doubled-count problem found on Pour Some Sugar On Me. Meter defaults to 4/4 with a `--meter` override, because automatic time-signature detection is unreliable. Sections come from librosa's Laplacian segmentation over beat-synchronous features, with heuristic labels from position and repetition. Section boundaries snap to downbeats. Sections are expected to be hand-corrected sometimes, which is why they live in an editable file.

### 6.4 Harmony
Chord-CNN-LSTM (the music-x-lab ISMIR 2019 repository, MIT, PyTorch) on the original mix. Its five checkpoints ship inside the repository (`cache_data/*.sdict`, about 5.7 MB each), so the code and checkpoints are vendored into the package under their MIT licence with checkpoint hashes recorded in the manifest; nothing is downloaded at run time. The vendored copy carries one small patch, replacing the removed `np.int` alias at ten sites, without which it does not run on NumPy 2. Verified here: a 16-second clip in 9 seconds on CPU with correct labels. Its output is tab-separated Harte labels with inversions, for example `A:min/b3` and `C:sus4(b7)`, which the stage normalises through mir_eval's `split` and `join`.

ChordMini (MIT, checkpoints in its repository) is available behind `--chord-model chordmini`. Its requirements are pinned to NumPy 1.26 and librosa 0.10, which conflict with the rest of the stack, but it runs correctly on the unpinned stack, so the vendored copy relaxes those pins.

Frame labels are snapped to the beat grid by majority vote within each beat, then merged into events. Each event keeps the full label and a triad reduction. mir_eval 0.8 has no label-to-triad function (its `reduce_extended_quality` only folds ninths and above into sevenths), so the package implements `to_triad`: split the label, take `quality_to_bitmap`, match the lower octave against maj, min, dim, aug, sus4 and sus2 templates, and join, guarding `InvalidChordException` for qualities such as `aug7`. Key is estimated with Krumhansl-Schmuckler profiles over librosa chroma, since the madmom key model is non-commercial.

### 6.5 Strums
Onsets from spectral flux on the guitar stem; if the stem's RMS is below a threshold relative to the mix, fall back to the full mix and say so in the file. Onsets are quantised to 8 slots per bar, or 16 if more than a configurable share of onsets fall off the eighth grid. Direction is assigned by metric position: down on beats and on-beat eighths, up on off-beat eighths and sixteenths. A muted flag is set when spectral flatness at the onset exceeds a threshold. Per section, a Viterbi decode over a bundled vocabulary of around thirty common ukulele patterns, with a penalty for switching, picks one pattern and a confidence. Below a confidence threshold the pattern is all downstrokes and the file and the sheet both say "pattern uncertain". The vocabulary lives in a data file so it can be extended without code changes. It is seeded from public pattern lists at UkuTabs, Ukulele Tricks and Ukulele Go, which together yield 37 distinct 8-slot 4/4 patterns plus 3/4 and 6/8 variants; the patterns are uncopyrightable facts, the data file credits its sources in a header, and no prose or images are copied.

### 6.6 Arrange
Candidate capo positions 0 to 5 and transpositions are scored by how many chord events get open, barre-free shapes from the chords-db ukulele set, with a penalty for capo use. chords-db (tombatossals, MIT) is vendored as its 215 KB `ukulele.json` plus licence: tuning G4 C4 E4 A4, 12 keys, 46 suffixes, 552 chords and 2,114 positions, each with `frets` in G C E A order (-1 muted), `fingers`, `baseFret`, `barres` and `midi`. It is not on PyPI. Within the winning candidate, a chord-level Viterbi picks voicings to minimise hand movement and prefer open strings. `--tier easy` reduces to triads, drops extensions, and substitutes simpler shapes where a listed alternative exists; `--tier full` keeps the recognised quality. Every substitution is recorded.

### 6.7 Score
Builds `score.json` from the four inputs, then emits alphaTex for alphaTab 1.8.4. Verified by rendering on this machine: `\staff {slash}` gives a slash-only staff with no standard notation or tab; `\chord ("C" 3 0 0 0)` definitions draw diagrams at the top; `{ch "C"}` puts chord names above beats; `\section "Verse"` draws rehearsal markers; `\tuning (A4 E4 C4 G4)` is accepted with re-entrant pitches (the last string listed draws leftmost on diagrams, so strings are listed A E C G and the A string is string 1); `\hideDynamics` suppresses dynamics marks.

Two findings change how strums are written. alphaTab parses brush strokes `{bd}` and `{bu}` on a slash staff but does not draw them there, so the slash staff cannot show direction by itself. Instead, each bar carries a `\lyrics` line with one `D`, `U`, `x` or `-` token per slot, rendered beneath the staff, while `{bd}` and `{bu}` are still emitted for correct MIDI if playback is ever added. Dead notes on a slash staff render as ordinary slashes, so muted slots are emitted as the dead-slap beat `(){ds}`, which draws a large X. Empty slots are rests. `:8` or `:16` sets the slot duration. A two-bar working example is in the rendering assumption-check report beside this spec.

The alphaTex is regenerated from `score.json` whenever the score stage runs, so `score.json` is the thing to edit, not the alphaTex.

### 6.8 Render
One HTML template (Jinja2). Header: title, artist, key, capo, tempo, tuning, tier, and an "uncertain" note where strums fell back. Chord diagram legend: every chord used, in order of first appearance, drawn as inline SVG from the shapes in `score.json`. Each section opens with its label and a strum pattern box drawing the slot grid as arrows with muted slots crossed, so the pattern is read once per section. Below it, alphaTab renders the slash staff with chord names above. The chord diagram legend is drawn by the package itself as SVG from the chords-db shapes, since no maintained Python library does this (the JS options, svguitar and chordbook, would need Node). alphaTab is vendored so the page works offline: `@coderline/alphatab` 1.8.4, MPL-2.0, shipping `alphaTab.min.js` (1.1 MB), `font/Bravura.woff2` (313 KB), the Bravura OFL text and the alphaTab licence. No soundfont is shipped because playback is off (`player.playerMode: 0`).

Rendering from a `file://` page has two constraints, both verified in headless Chromium here. alphaTab's default web worker fails under `file://` because the worker cannot import a file URL, so the template sets `core.useWorkers: false` and loads alphaTab as a classic script, which also lets it find its fonts automatically. `fetch()` also fails from `file://`, so the alphaTex and all data are inlined into the page rather than loaded. A print stylesheet sets A4 margins, hides anything interactive, keeps a section header with its first system, and prefers page breaks at section boundaries.

The PDF is the same page printed by headless Chromium via Playwright for Python, pinned to 1.63.0 because that version's Chromium (revision 1243) is already installed on this machine and launches without `playwright install`. The renderer launches Chromium with `--allow-file-access-from-files`, waits for alphaTab's render-finished event and `document.fonts.ready`, then calls `page.pdf(format="A4", print_background=True, prefer_css_page_size=True)`. If workers are ever needed, the fallback is serving the folder over localhost. alphaTab also has an official Node-side SVG renderer, noted as a second fallback but not used.

## 7. Command line

```
youkelele run <url-or-path> [--instrument ukulele] [--from N|name] [--to N|name]
                            [--tier easy|full] [--beat-octave half|double]
                            [--meter 4/4] [--separator demucs|roformer-sw]
                            [--runs-dir runs]
youkelele stages [--instrument ukulele]       # numbered stages with reads and writes
youkelele status <slug>                        # completed, stale and missing stages
```

`run` on an existing slug without `--from` starts at 0 and overwrites, after printing that it will.

## 8. Errors

A stage failure stops the chain, leaves earlier outputs intact, prints the failing stage, the exception, and the exact `--from` command to resume. Validation failures on a hand-edited file name the file and the field path. A missing external tool (ffmpeg, yt-dlp, a model checkpoint) is reported with the install command before any work starts. Network failures in ingest are retried three times with backoff and then fail.

## 9. Testing

- **Unit tests** for the pure logic: slot quantisation, direction assignment, the strum Viterbi, capo scoring, voicing Viterbi, triad reduction, alphaTex generation, chord-diagram SVG, schema validation including rejection of plausible hand-edit mistakes.
- **Stage tests** run every stage on small fixtures with the heavy models replaced by fakes that return recorded outputs, so the whole suite runs in seconds with no network and no model downloads. Each stage test also checks that the stage writes exactly its declared `produces` and reads nothing outside its declared `requires`.
- **Runner tests** for `--from`/`--to`, the missing-input refusal, atomic writes, manifest recording, option reuse and override.
- **One opt-in end-to-end test** runs the real chain on a bundled thirty-second local clip.
- **Accuracy report**, not pass/fail: hand-annotated beats and chords for the two target songs under `tests/fixtures/ground_truth`, and a script that scores a run folder against them with mir_eval and prints beat F-measure and chord WCSR. This is how model and threshold changes are judged.

## 10. Adding an instrument later

Write a profile with its tuning and its own strums, arrange and score stages (or reuse the ukulele ones where the logic is instrument-neutral, which strums and score largely are), register it, and bundle a shape set. The runner, the generic stages, the data formats and the renderer do not change. A six-string guitar profile would differ mainly in the shape set and the voicing cost model.

## 11. Decisions already taken

- Linear chain with profiles over a build-style dependency graph, because the chain is genuinely linear and "start at stage N" must stay a direct concept.
- One `score.json` rendered to HTML and PDF from one template, so screen and paper never disagree.
- Slash notation for strums rather than fretted tab per strum, because repeated fret numbers do not read well for a chord sheet.
- Demucs htdemucs_6s rather than the stronger but unlicensed RoFormer checkpoint as the default separator.
- Krumhansl key estimation rather than madmom's model, for licence reasons.
- Chord recognition on the original mix only; the re-mix gain of +0.20 WCSR does not justify a stage.
- Strum direction shown as a token line under the slash staff, not as brush arrows, because alphaTab does not draw brushes on a slash staff (verified 2026-10-03).
- Chord model code and checkpoints vendored rather than fetched, because they live in the MIT repository and the code needs a one-line NumPy 2 patch.
- Playwright pinned to the version whose Chromium is already on this machine; alphaTab run without web workers so the page renders from a local file.

## 12. Assumption checks

Every tool and library claim above was checked on 2026-10-03, most by installing the stack into a throwaway Python 3.12 environment on this machine and running it. The evidence, with URLs, is in `2026-10-03-assumption-checks-tools.md` and `2026-10-03-assumption-checks-rendering.md` beside this file. Status: 13 confirmed, 9 changed and folded into this spec, none unknown.
