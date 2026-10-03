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

- Drum bleed can read as muted strums. On a separated stem, drum bleed can satisfy the centroid and zero-crossing mute rule, so a busy snare shows up as chunked `x` slots in the strum pattern. The end-to-end test clip uses a quiet snare for this reason.
