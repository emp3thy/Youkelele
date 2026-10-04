# Youkelele

Research and design notes for a pipeline that takes a YouTube music video (or audio/MIDI file) and produces ukulele tablature: chords, single-note riffs and melody, and strumming patterns.

## Reports

- `reports/YouTube to ukulele tab pipeline.md` - round one: chord recognition, note transcription, source separation, tablature theory, existing implementations, visualisers, recommended architecture.
- `reports/Ukulele tab pipeline gap analysis.md` - round two: what else is needed (timing spine, lyrics, vocal melody, bass-anchored harmony, input conditioning, techniques and arrangement, evaluation, engineering and licensing), ranked open questions, and extra pipeline stages.

## Research notes

- `research_notes/*.md` - round one source notes (one file per topic, every claim cited).
- `research_notes/gap_analysis/*.md` - round two source notes, including the scout list of missing topics and two verification notes from the 2026-10-03 pass that re-checked every item the reports had marked unverified: `verification_papers_and_libraries.md` (papers, repositories, package metadata) and `verification_web_pages.md` (product, tab and terms pages read in a browser).

## Tool

The `youkelele` command-line tool lives in `src/youkelele`. It turns a YouTube URL into a ukulele chord-and-strum sheet through a chain of file-based stages. See `docs/superpowers/specs/2026-10-03-ukulele-tab-chain-design.md` for the design spec and stage layout. Run `uv sync`, then `uv run youkelele --version`.

### Usage

- `youkelele setup` fetches the chord model and ffmpeg once.
- `youkelele run <url-or-path>` runs the whole chain; each stage writes a numbered folder under `runs/<slug>/`.
- Resume with `--from <stage>` (and stop early with `--to <stage>`), for example `youkelele run <url-or-path> --from harmony`.
- To correct a stage, edit its JSON (for example `02_grid/grid.json`) and re-run from the next stage with `--from`. The score stage may move a hand-edited section start one bar later to align with the chord phrase; `shifted` in `score.json` records it.
- In `03_harmony/chords.json`, an event with `filled: true` prints in italics as inferred; clear the flag when you correct its label.
- `youkelele stages` lists the stages; `youkelele status <slug>` shows which have run and which are stale.
- `youkelele evaluate <slug>` needs no truth: it prints diagnostics read from the run's own files (no-chord share, all-N and filled bars, the share of chord changes on a bar start, events shorter than a beat, key confidence, the number of certain strum patterns that are mostly rests) and, per section, strikes per bar, the share of detected strokes the printed pattern covers, its rests, and whether it is uncertain or recall-boosted.
- `youkelele evaluate <slug> --truth <dir>` adds beat, downbeat and chord accuracy against `beats.txt` and `chords.lab` in `<dir>`; the formats are in `tests/fixtures/ground_truth/README.md`.
- `youkelele evaluate <a> --compare <b>` scores two runs under the same `--runs-dir` against each other: chord segmentation and majmin agreement, then each section's strum figures for `a` and `b` side by side with `b` minus `a`. To compare a folder kept elsewhere (a copied baseline, say), call the Python API: `uv run python -c "from pathlib import Path; from youkelele.evaluate import compare_runs, format_comparison; print(format_comparison(compare_runs(Path(r'<a>'), Path(r'<b>'))))"`. A run compared with itself scores 1.000 with no differences.

Options for `run`:

- `--tier easy|full` chooses the arrangement tier (default `easy`).
- `--beat-octave auto|none|half|double` forces or auto-detects the beat tempo octave.
- `--sections-k N` sets the number of song sections instead of choosing it automatically (`auto` restores automatic choice).
- `--meter 4/4` sets the time signature (default `4/4`).
- `--debug` also writes `04_strums/onsets.txt`: every detected onset as an Audacity label track (`S` for a strike, `x` for a mute, `+` appended where the recall gate added it). Import the label track beside the audio in Audacity to check the strums by ear. `--no-debug` switches a saved `--debug` off.

Every run, with or without `--debug`, also writes two diagnostic files: `02_grid/beats_raw.json` (the beats and downbeats before gap filling and octave normalisation, with the inserted and dropped beats) and `03_harmony/spans.lab` (the chord model's raw output).

Options are saved in `runs/<slug>/manifest.json`. A `--from` run reuses them and changes only the flags you give again; `--debug` is saved like the others, so later runs keep writing `onsets.txt` until you give `--no-debug`.

### Requirements

- `youkelele setup` needs git on PATH and network access: it clones the chord model and downloads ffmpeg.
- Rendering the PDF needs Playwright's Chromium. If preflight reports that Chromium is missing, run `uv run playwright install chromium`.
- Fast test suite (seconds, no network, no models): `uv run pytest -q -W error -m "not slow"`.
- Slow suite (real models on a bundled clip, after `youkelele setup`): `uv run pytest -q -m slow`.

### Known limitations

Version 1.1 (`docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-1-design.md`) prints each section as a strum box followed by a chord grid. Version 1.2 (`docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-2-design.md`) adds a four-bar minimum section, a header tempo from the mean beat interval, cleaned titles, chords inferred for no-chord bars where the harmonic stems play (printed in italics), passing chords named without a diagram, phrase-aligned section starts and repeating row blocks printed once with a repeat count. Version 1.3 (`docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-3-design.md`) adds the truth-free `evaluate` and `--compare`, a strike vote that keeps slots struck in more than a third of a section's bars with a density floor, a per-section recall gate that recovers sustained strums the onset detector misses, trailing no-chord bars dropped from the sheet, chord decoding that uses the beats and downbeats, and a two-bar worked example in place of the strum box that places each chord under the stroke it starts on. On the five validation songs no certain pattern is mostly rests any more, and the share of chord changes on a bar start rises on every song (to 100 percent on Summer of '69) (`docs/superpowers/specs/2026-10-04-v1-3-validation.md`). What remains:

- The recall gate works only on the eighth-note grid. A song whose strums are counted in sixteenths (Pour Some Sugar On Me, Fame) keeps the detector's onsets, so a sustained, distorted strum on a sixteenth grid can still print as a sparse pattern.
- Two guitars in one stem are not separated. When the `guitar` stem holds a strummed part and a single-note riff at once, the strum pattern describes neither. On Pour Some Sugar On Me every section prints as uncertain with no strip, but only because the sixteenth-grid certainty threshold (0.55) sits above its two-guitar sections' confidence (0.453 to 0.472); nothing tells one guitar from two.
- The certainty test is not a test for noise. A dense two-part or noisy section can pass it on either grid: the strike vote keeps most of a dense spray's slots, so the share of strokes the pattern covers is high and the confidence is inflated. Random sections striking half the slots print as certain most of the time at 8 slots, and still about 30 percent of the time at 16 slots. A confidence corrected for chance (against a slot-shuffled baseline at the same density) is planned for the next version.
- Drum bleed can read as strums. On a separated stem, snare bleed can satisfy the onset and mute rules, so beats 2 and 4 show up as down strokes or chunked `x` slots. The end-to-end test clip uses a quiet snare for this reason.
- Section labels are low confidence. The chorus is usually found, but a bridge that clusters with another part is named "verse 2" and an instrumental intro or break can be named after a verse. Sections are at least four bars, so a genuine two-bar part is merged into its neighbour.
- Key mode can be wrong when the estimate is close: a power-chord riff is read as major, and a vamp whose chords are major can be read as minor. Under a capo the header then names a shape key that disagrees with the grid.
- Inferred chords cover only bars whose harmonic stems clearly match one of the song's own chords. A lead line over the band still prints as N.C., and a faint guitar in a sparse verse can be filled with a chord the record may not have; inferred chords are italic so a reader can tell.
- Phrase alignment only moves a section start one bar later. When the phrase starts a bar earlier, the rows still start mid-phrase.
- Four of the five validation sheets need three pages; Fame grew from two to three. The worked example is 90 px tall where the one-bar box was 60 px, which pushes the last section or two of Fame onto a third page and keeps Wet Leg at three pages. The trailing-bar rule never empties the last section, so a recording that ends in a short no-chord outro still prints one N.C. cell for it: Wet Leg's outro is one N.C. cell under "Strum as in chorus (uncertain)", because one bar is too short for a pattern of its own and it inherits the chorus's.
