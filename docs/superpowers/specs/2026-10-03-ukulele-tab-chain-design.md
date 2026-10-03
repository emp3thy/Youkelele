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
- Python 3.12 pinned with uv (3.13 is the system default; the MIR libraries want 3.10 to 3.12).
- ffmpeg and yt-dlp are installed into the project environment, not assumed on the machine.
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

### 6.2 Separate
audio-separator running Demucs `htdemucs_6s` (MIT), six stems including guitar. CPU only. The unlicensed BS-RoFormer-SW guitar model is not installed by default; `--separator roformer-sw` enables it for personal runs and the manifest records that a non-redistributable model was used.

### 6.3 Grid
Beat This! for beats and downbeats on CPU. Tempo from the median beat interval. `--beat-octave half|double` halves or doubles the beat list after detection, which handles the doubled-count problem found on Pour Some Sugar On Me. Meter defaults to 4/4 with a `--meter` override, because automatic time-signature detection is unreliable. Sections come from librosa's Laplacian segmentation over beat-synchronous features, with heuristic labels from position and repetition. Section boundaries snap to downbeats. Sections are expected to be hand-corrected sometimes, which is why they live in an editable file.

### 6.4 Harmony
Chord-CNN-LSTM (MIT, PyTorch) on the original mix. Frame labels are snapped to the beat grid by majority vote within each beat, then merged into events. Each event keeps the full label and a triad reduction computed with mir_eval. Key is estimated with Krumhansl-Schmuckler profiles over librosa chroma, since the madmom key model is non-commercial. The chord model's checkpoints are downloaded on first use into a cache folder and their origin and licence are recorded in the manifest.

### 6.5 Strums
Onsets from spectral flux on the guitar stem; if the stem's RMS is below a threshold relative to the mix, fall back to the full mix and say so in the file. Onsets are quantised to 8 slots per bar, or 16 if more than a configurable share of onsets fall off the eighth grid. Direction is assigned by metric position: down on beats and on-beat eighths, up on off-beat eighths and sixteenths. A muted flag is set when spectral flatness at the onset exceeds a threshold. Per section, a Viterbi decode over a bundled vocabulary of around thirty common ukulele patterns, with a penalty for switching, picks one pattern and a confidence. Below a confidence threshold the pattern is all downstrokes and the file and the sheet both say "pattern uncertain". The vocabulary lives in a data file so it can be extended without code changes.

### 6.6 Arrange
Candidate capo positions 0 to 5 and transpositions are scored by how many chord events get open, barre-free shapes from the chords-db ukulele set (MIT), with a penalty for capo use. Within the winning candidate, a chord-level Viterbi picks voicings to minimise hand movement and prefer open strings. `--tier easy` reduces to triads, drops extensions, and substitutes simpler shapes where a listed alternative exists; `--tier full` keeps the recognised quality. Every substitution is recorded.

### 6.7 Score
Builds `score.json` from the four inputs, then emits alphaTex: metadata, tuning, tempo, chord definitions for diagrams, section markers, and a slash staff in which each bar's strum slots become brush strokes (`{bd}` and `{bu}`) with dead notes for muted slots and rests for empty ones. The alphaTex is regenerated from `score.json` whenever the score stage runs, so `score.json` is the thing to edit, not the alphaTex.

### 6.8 Render
One HTML template (Jinja2). Header: title, artist, key, capo, tempo, tuning, tier, and an "uncertain" note where strums fell back. Chord diagram legend: every chord used, in order of first appearance, drawn as inline SVG from the shapes in `score.json`. Each section opens with its label and a strum pattern box drawing the slot grid as arrows with muted slots crossed, so the pattern is read once per section. Below it, alphaTab renders the slash staff with chord names above. alphaTab is vendored so the page works offline. A print stylesheet sets A4 margins, hides anything interactive, keeps a section header with its first system, and prefers page breaks at section boundaries. The PDF is the same page printed by headless Chromium via Playwright for Python.

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
