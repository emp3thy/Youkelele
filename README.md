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
- To correct a stage, edit its JSON (for example `02_grid/grid.json`) and re-run from the next stage with `--from`.
- `youkelele stages` lists the stages; `youkelele status <slug>` shows which have run and which are stale.
- `youkelele evaluate <slug> --truth <dir>` prints beat, downbeat and chord accuracy against `beats.txt` and `chords.lab` in `<dir>`; the formats are in `tests/fixtures/ground_truth/README.md`.

Options for `run`:

- `--tier easy|full` chooses the arrangement tier (default `easy`).
- `--beat-octave auto|none|half|double` forces or auto-detects the beat tempo octave.
- `--sections-k N` sets the number of song sections instead of choosing it automatically (`auto` restores automatic choice).
- `--meter 4/4` sets the time signature (default `4/4`).

Options are saved in `runs/<slug>/manifest.json`. A `--from` run reuses them and changes only the flags you give again.

### Requirements

- `youkelele setup` needs git on PATH and network access: it clones the chord model and downloads ffmpeg.
- Rendering the PDF needs Playwright's Chromium. If preflight reports that Chromium is missing, run `uv run playwright install chromium`.
- Fast test suite (seconds, no network, no models): `uv run pytest -q -W error -m "not slow"`.
- Slow suite (real models on a bundled clip, after `youkelele setup`): `uv run pytest -q -m slow`.

### Known limitations

Version 1.1 (`docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-1-design.md`) prints each section as a strum box followed by a chord grid. Version 1.2 (`docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-2-design.md`) adds a four-bar minimum section, a header tempo from the mean beat interval, cleaned titles, chords inferred for no-chord bars where the harmonic stems play (printed in italics), passing chords named without a diagram, phrase-aligned section starts and repeating row blocks printed once with a repeat count. The five real songs it was validated on print in two or three pages (`docs/superpowers/specs/2026-10-03-v1-2-validation.md`). What remains:

- Strum patterns are often mostly rests. The slot-wise majority vote keeps only slots struck in most bars, so a section strummed throughout can print as one or two arrows, and the confidence score does not flag it. Lowering the strike threshold, reporting strike density or marking sparse patterns uncertain is a measured spike in section 7 of the version 1.1 spec, not yet built.
- Drum bleed can read as strums. On a separated stem, snare bleed can satisfy the onset and mute rules, so beats 2 and 4 show up as down strokes or chunked `x` slots. The end-to-end test clip uses a quiet snare for this reason.
- Section labels are low confidence. The chorus is usually found, but a bridge that clusters with another part is named "verse 2" and an instrumental intro or break can be named after a verse. Sections are at least four bars, so a genuine two-bar part is merged into its neighbour.
- Key mode can be wrong when the estimate is close: a power-chord riff is read as major, and a vamp whose chords are major can be read as minor. Under a capo the header then names a shape key that disagrees with the grid.
- Inferred chords cover only bars whose harmonic stems clearly match one of the song's own chords. A lead line over the band still prints as N.C., and a faint guitar in a sparse verse can be filled with a chord the record may not have; inferred chords are italic so a reader can tell.
- Phrase alignment only moves a section start one bar later. When the phrase starts a bar earlier, the rows still start mid-phrase.
- A sheet can spill a few rows, or a single N.C. bar at the end of the recording, onto a third page.
