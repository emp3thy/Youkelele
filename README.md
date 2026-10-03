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
