# Youkelele

Youkelele turns a song into a printable ukulele sheet. Give it a YouTube link or an audio file and it writes a PDF with the song's chords, a diagram for each chord shape, the strumming pattern of each section and a bar-by-bar chord grid, laid out to print on A4. It is for people who want to play along with a song and have no chart for it. It runs on an ordinary computer with no graphics card: it is developed and tested on Windows, and the macOS and Linux scripts are written but untested.

## A sample sheet

![Page 1 of a sample sheet: the title, a header line with key, capo, tempo and tuning, four chord diagrams, and the Intro, Verse 1, Pre-chorus and Chorus 1 sections, each with its chord grid and most with a two-bar strum strip above it.](docs/images/sample-sheet.png)

*Page 1 of the sheet for "Synthetic Song", the project's own made-up test song (no real song's chart is published here).*

*At the top, the header gives the key in ukulele shapes (C major), the capo (fret 2), the tempo (120 bpm), the tuning and the tier, with notes that italic chords were inferred, that shapes are relative to the capo and that the song sounds in D major. Below it are the diagrams for C, G, Am and F, and a passing B, named with its fret numbers but no diagram.*

*Each section then opens with its two-bar worked example (down and up arrows over the counts 1 & 2 & 3 & 4 &, with the chord under the stroke it starts on), followed by its chord grid: one box per bar, a pickup bar marked as such, and a repeat count such as ×4 where rows repeat. The Pre-chorus has no strip because its pattern was too uncertain to print.*

## Using it without coding (Windows)

You need Windows 10 or 11 with an internet connection, and nothing else installed. You do not need to know anything about programming for this. Each step is one thing to do.

1. On this repository's GitHub page, press the green **Code** button, then **Download ZIP**.
2. Find the downloaded file (it is called `Youkelele-main.zip`, usually in your Downloads folder). Right-click it, choose **Extract All**, and pick a place you will find again, such as your Documents folder. This makes a folder called `Youkelele-main`. If you open it and see only another folder with the same name, open that one too.
3. Open the `Youkelele-main` folder and double-click `install.cmd`. A black window opens and works through four steps.
   - Windows will probably first show a box saying **The publisher could not be verified. Are you sure you want to run this software?** This happens because the files came from the internet. Choose **Run**. If instead a blue box says **Windows protected your PC**, choose **More info**, then **Run anyway**.
   - The first time, it downloads a little over 800 MB and uses about 3 GB of disk space, so leave it until it finishes. Some download progress bars may show as rows of odd characters; that is harmless.
4. Wait until the window says **Ready**, then press any key to close it. You only need to do steps 1 to 4 once.
5. Double-click `run-youkelele.cmd`. It may show the same security box the first time; choose **Run** again. When it asks, paste the YouTube link (press Ctrl+V, or right-click in the window) and press Enter.
   - Then wait: a song takes several minutes while the window shows the eight steps going by, and the first song takes longer, because it downloads another 140 MB or so of song-analysis models. Later songs skip this.
6. When it is done, the sheet opens as a PDF and the black window closes by itself; that is normal. The sheet is also saved inside the `Youkelele-main` folder, under `runs`, then the song's name, then `07_render`, as `sheet.pdf`.

You can also drag an audio file (an MP3 or WAV, say) onto `run-youkelele.cmd` instead of pasting a link. Giving it the same link again makes that song's sheet again from the start. Each song's folder in `runs` keeps the separated audio, about 200 to 350 MB, so delete old song folders when space runs short.

**If something goes wrong.** If a window closes before you can read it, or says that something is not installed or is missing, double-click `install.cmd` again (it only fetches what is missing), then try the song again. If it still goes wrong, the window says **Something went wrong**: take a screenshot of the window, or copy its text, and send it to the person who gave you the tool, and, if it names a folder, that folder.

On a Mac or Linux computer the same steps use `install.sh` and `run-youkelele.sh`, run from a terminal; these two scripts are written but have not been tried.

Youkelele makes ukulele sheets today. Other instruments, such as guitar and bass, are planned.

## Quick start for developers

Install [uv](https://docs.astral.sh/uv/getting-started/installation/); it brings its own Python 3.12. Then, from a clone or an unpacked ZIP of this repository:

```
uv sync
uv run youkelele setup
uv run playwright install chromium
uv run youkelele run "https://www.youtube.com/watch?v=VIDEO_ID"
```

`setup` downloads the chord model and ffmpeg (no git needed). Playwright's Chromium prints the PDF. The sheet lands in `runs/<song-name>/07_render/sheet.pdf`, where the folder is named after the song's title (or after the file, for a local audio file).

## How it works

The tool runs a chain of eight stages. Each stage reads earlier stages' files from the run folder and writes its own into a numbered folder, so a run can be resumed from any stage and any stage's output can be corrected by hand. `uv run youkelele stages` prints this list.

| Stage | Reads | Writes | Model or method |
|---|---|---|---|
| `00_ingest` | the link or file | `audio.wav`, `source.json` | [yt-dlp](https://github.com/yt-dlp/yt-dlp) download and ffmpeg conversion to 44.1 kHz stereo WAV; title and artist cleaned from the video's details |
| `01_separate` | `audio.wav` | six stems: vocals, drums, bass, guitar, piano, other | Demucs `htdemucs_6s` through [audio-separator](https://github.com/nomadkaraoke/python-audio-separator), on the CPU |
| `02_grid` | `audio.wav`, drums and vocals stems | `grid.json` (beats, bars, tempo, sections), `beats_raw.json` | [Beat This!](https://github.com/CPJKU/beat_this) beats and downbeats; a drum backbeat test for the tempo octave; sections by Laplacian segmentation of bar features, named with the help of the vocal stem |
| `03_harmony` | `audio.wav`, `grid.json`, guitar, bass, piano and other stems | `chords.json`, `spans.lab` | [Chord-CNN-LSTM](https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition) (ISMIR 2019) decoded on the beats and downbeats; no-chord bars filled from the harmonic stems' chroma; the key from the chord stream, its mode from the stems; tonic power chords marked |
| `04_strums` | guitar and other stems, `audio.wav`, `grid.json`, `chords.json` | `strums.json` | onset detection on the best strum source, quantised to an eighth or sixteenth slot grid; a strike vote per section; a recall gate for sustained strums the detector misses |
| `05_arrange` | `chords.json`, `grid.json` | `arrangement.json` | capo and transposition scored over the [chords-db](https://github.com/tombatossals/chords-db) ukulele shapes; one shape per chord chosen to keep hand movement low; the easy tier reduces chords to triads |
| `06_score` | `grid.json`, `chords.json`, `strums.json`, `arrangement.json`, `source.json` | `score.json`, `score.alphatex` | merges everything into one score: section starts aligned to the chord phrase, the bridge chosen by chord novelty, repeating rows collapsed |
| `07_render` | `score.json` | `sheet.html`, `sheet.pdf` | an HTML page with SVG chord diagrams, printed to A4 by headless Chromium through Playwright |

Every run also writes two diagnostic files: `02_grid/beats_raw.json` (the beats and downbeats before gap filling and octave correction) and `03_harmony/spans.lab` (the chord model's raw output). The options of each run are saved in `runs/<song-name>/manifest.json`.

## Correcting a result

To fix something the tool got wrong, edit that stage's JSON file and run again from the next stage with `--from`, giving the same link or file. For example, after moving a section boundary or renaming a section in `02_grid/grid.json`:

```
uv run youkelele run "https://www.youtube.com/watch?v=VIDEO_ID" --from harmony
```

- The score stage may move a section start one bar later so that it lines up with the chord phrase; `shifted` in `06_score/score.json` records each move.
- In `03_harmony/chords.json`, an event with `filled: true` was inferred and prints in italics; clear the flag when you correct its label.
- The score stage chooses at most one bridge from the chords, so it may rename sections labelled `verse`, `chorus` or `bridge`. Any other label (`intro`, `instrumental`, `outro`, or one of your own such as `solo` or `pre-chorus`) prints as written.

`uv run youkelele status <song-name>` shows which stages have run and which are stale after an edit.

## Measuring

`evaluate` reads a run's own files and needs no reference: it prints the key with its method and margins, the no-chord share, the share of chord changes on a bar start, and per section the strikes per bar, the share of detected strokes the printed pattern covers, and whether it is uncertain.

```
uv run youkelele evaluate <song-name>
```

`--truth` adds beat, downbeat and chord accuracy against hand-made `beats.txt` and `chords.lab` files in a folder; the formats are in [tests/fixtures/ground_truth/README.md](tests/fixtures/ground_truth/README.md).

```
uv run youkelele evaluate <song-name> --truth tests/fixtures/ground_truth/<song-name>
```

`--compare` scores a second run against the first, which is the reference: chord agreement, then each section's strum figures side by side with the second minus the first. To see what a change did, copy the run folder first (to `runs/<song-name>-before`, say), re-run, then compare. A run compared with itself scores 1.000.

```
uv run youkelele evaluate <song-name>-before --compare <song-name>
```

`--debug` also writes `04_strums/onsets.txt`, every detected onset as an Audacity label track (`S` for a strike, `x` for a mute, `+` where the recall gate added it), to check the strums by ear beside the audio. It is saved with the run; `--no-debug` turns it off.

```
uv run youkelele run "https://www.youtube.com/watch?v=VIDEO_ID" --debug
```

## Options

Options for `run`. A run resumed with `--from` keeps the options saved in its `manifest.json` and changes only the flags given again.

| Flag | Values | Default | What it does |
|---|---|---|---|
| `--instrument` | `ukulele` | `ukulele` | the instrument profile; ukulele is the only one so far |
| `--tier` | `easy`, `full` | `easy` | `easy` reduces chords to triads and simpler shapes; `full` keeps the recognised chord quality |
| `--beat-octave` | `auto`, `none`, `half`, `double` | `auto` | keep, halve or double the detected tempo, or decide automatically |
| `--sections-k` | a whole number, or `auto` | `auto` | the number of distinct section types, instead of choosing it automatically |
| `--meter` | `N/D`, such as `4/4` | `4/4` | the time signature; every song tested so far is in 4/4 |
| `--separator` | `demucs`, `roformer-sw` | `demucs` | the stem separator; `roformer-sw` is not implemented yet and stops the run before it starts |
| `--chord-model` | `cnn-lstm`, `chordmini` | `cnn-lstm` | the chord recogniser; `chordmini` is not implemented yet and stops the run before it starts |
| `--from` | a stage name or number | `ingest` (the whole chain) | start at this stage, reusing earlier stages' files |
| `--to` | a stage name or number | `render` | stop after this stage |
| `--debug`, `--no-debug` | on or off | off | also write the strum onsets as an Audacity label track |
| `--runs-dir` | a folder | `runs` | where run folders are kept |

## Requirements and tests

- Python 3.12, which uv installs for the project. No graphics card is needed; everything runs on the CPU.
- `uv run youkelele setup` needs network access, not git: it downloads the chord model as a zip of its pinned commit (27.2 MB) and ffmpeg. A model folder cloned by an earlier version is still accepted.
- The PDF needs Playwright's Chromium: `uv run playwright install chromium`. The run checks for it before starting and says so if it is missing.
- The separation and beat models download on first use (about 136 MB together).
- Fast tests (no network, no models): `uv run pytest -q -W error -m "not slow"`.
- Slow tests (real models on a bundled clip, after `setup`): `uv run pytest -q -m slow`.

## Known limitations

- The recall gate works only on the eighth-note grid. A song whose strums fall on a sixteenth grid keeps the detector's onsets, so a sustained, distorted strum there can still print as a sparse pattern.
- Two guitars in one stem are not told apart. When the guitar stem holds a strummed part and a single-note riff at once, the strum pattern describes neither. Whether such a section prints as uncertain depends on its confidence, not on any test for a second guitar.
- The certainty test is not a test for noise. A dense two-part or noisy section can pass it: the strike vote keeps most of a dense spray's slots, so the pattern seems to cover most strokes and its confidence is inflated. A confidence corrected for chance is planned.
- Drum bleed can read as strums. On a separated stem, snare bleed can pass the onset and mute rules, so beats 2 and 4 show up as down strokes or muted `x` slots.
- Section names are a best guess from repeating chord and sound patterns and from where the singing is. Sections are at least four bars long, so a genuine two-bar part is merged into its neighbour.
- The key's hedge names a second possible tonic but not the other mode. A song whose stems carry little harmony and whose tonic chord is ambiguous can get the wrong mode.
- Inferred chords cover only bars whose harmonic stems clearly match one of the song's own chords. A lead line over the band still prints as N.C., and a faint guitar in a sparse verse can be filled with a chord the record may not have; inferred chords are italic so a reader can tell.
- Phrase alignment only moves a section start one bar later. When the phrase starts a bar earlier, the rows still start mid-phrase.
- Real songs print on two to four pages (of the seven measured, two print on two, four on three and one on four); each section's two-bar worked example adds height to the page, and a song cut into many short sections runs longer.
- Verse and chorus are told apart by sound and repetition, not by chord content, so on a song cut into many short sections the same chord cycle can print under both names.
- The power-chord mark (a raised 5 after the chord name) prints only in the full tier, and the line explaining it is left out if the record also plays that chord as a full minor chord anywhere.
- An artist name given wholly in capitals is printed in title case, so "INXS" prints as "Inxs".

## Project history

Each version has a design spec and a record of how it did on real songs, all under [docs/superpowers/specs](docs/superpowers/specs).

- 1.0: the eight-stage chain and a slash-staff sheet. [Spec](docs/superpowers/specs/2026-10-03-ukulele-tab-chain-design.md); [lessons from the first real runs](docs/superpowers/specs/2026-10-03-real-run-lessons.md).
- 1.1: the sheet becomes a strum box and a chord grid per section, short enough to use. [Spec](docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-1-design.md); [validation](docs/superpowers/specs/2026-10-03-v1-1-validation.md).
- 1.2: four-bar sections, inferred and passing chords, phrase-aligned starts, repeated rows printed once. [Spec](docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-2-design.md); [validation](docs/superpowers/specs/2026-10-03-v1-2-validation.md).
- 1.3: the measurement harness, a more reliable strum pattern, chord changes on the bar lines, the two-bar worked example. [Spec](docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-3-design.md); [validation](docs/superpowers/specs/2026-10-04-v1-3-validation.md).
- 1.4: the key from the chords with a hedge, power chords, section names from the vocals, the no-capo line, run folders named after the song, install and run scripts for non-coders, and this README. [Spec](docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-4-design.md); [validation](docs/superpowers/specs/2026-10-04-v1-4-validation.md).

The quality research behind versions 1.3 and 1.4 is in [docs/superpowers/research/2026-10-03-quality](docs/superpowers/research/2026-10-03-quality/README.md).

## Background research

The project started as research into turning a YouTube music video into ukulele tablature.

- [YouTube to ukulele tab pipeline](reports/YouTube%20to%20ukulele%20tab%20pipeline.md): round one, covering chord recognition, note transcription, source separation, tablature theory, existing tools, visualisers and a recommended architecture.
- [Ukulele tab pipeline gap analysis](reports/Ukulele%20tab%20pipeline%20gap%20analysis.md): round two, on what else is needed (timing, lyrics, vocal melody, bass-anchored harmony, input conditioning, techniques and arrangement, evaluation, engineering and licensing), with ranked open questions.
- [research_notes](research_notes): the round one source notes, one file per topic with every claim cited.
- [research_notes/gap_analysis](research_notes/gap_analysis): the round two source notes, including two verification notes that re-checked every item the reports had marked unverified: [papers and libraries](research_notes/gap_analysis/verification_papers_and_libraries.md) and [web pages](research_notes/gap_analysis/verification_web_pages.md).

## Licence

Youkelele is released under the MIT licence; see [LICENSE](LICENSE).

The tool ships or downloads these components, each under its own licence, checked at its source on 2026-10-04:

| Component | How it arrives | Licence |
|---|---|---|
| Chord-CNN-LSTM chord model and its checkpoints | downloaded by `setup` as a zip of a pinned commit | MIT License, "Copyright (c) 2023 Music X Lab", in the repository's [LICENSE](https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition/blob/master/LICENSE); the checkpoints are committed in the same repository |
| chords-db ukulele shapes | included in this repository, with its licence, under `src/youkelele/data/chords-db` | MIT License, "Copyright (c) 2016 David Rubert" ([LICENSE](https://github.com/tombatossals/chords-db/blob/master/LICENSE)) |
| Demucs `htdemucs_6s` weights, run by audio-separator | downloaded on first use from Meta's server | The [Demucs README](https://github.com/facebookresearch/demucs) says "Demucs is released under the MIT license"; it makes no separate statement about the weights, so their terms are taken to be the repository's but are not stated outright. The repository is archived. audio-separator itself is MIT. |
| Beat This! `final0` checkpoint | downloaded on first use | MIT License for the code; the maintainer [states](https://github.com/CPJKU/beat_this/issues/16) "The MIT license also applies to the model weights." |
| yt-dlp, which fetches the audio | installed with the Python packages | The Unlicense, a public-domain dedication ("This is free and unencumbered software released into the public domain", [LICENSE](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE)) |
| Playwright and its Chromium, which print the PDF | Playwright installed with the Python packages; Chromium downloaded by `playwright install chromium` | Playwright: Apache License 2.0 ([LICENSE](https://github.com/microsoft/playwright-python/blob/main/LICENSE)). Chromium: BSD 3-Clause, "Copyright 2015 The Chromium Authors" ([LICENSE](https://chromium.googlesource.com/chromium/src/+/main/LICENSE)), with its bundled third-party components under their own licences |
| static-ffmpeg | installed with the Python packages | MIT License ([PyPI](https://pypi.org/project/static-ffmpeg/)) |
| ffmpeg, fetched by static-ffmpeg | downloaded by `setup` | On Windows this is the gyan.dev 8.0.1 "essentials" build, configured with `--enable-gpl --enable-version3`, so it is under the [GNU GPL version 3 or later](https://www.ffmpeg.org/legal.html) (as `ffmpeg -L` reports). It is not included in this repository and the tool runs it as a separate program. The builds for other systems were not checked. |

None of these carries a non-commercial clause. The one unclear term is the Demucs weights, as above. The other Python packages that uv installs come under their own licences.

The sheets the tool makes are transcriptions of the recordings you give it, and those recordings' copyright still applies, so keep the sheets for your own playing. Fetching audio from YouTube is subject to YouTube's terms.
