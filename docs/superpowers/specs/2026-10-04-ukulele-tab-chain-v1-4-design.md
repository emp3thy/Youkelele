# Youkelele tab chain, version 1.4: design

Date: 2026-10-04. Status: approved in conversation, awaiting written review. Amends `2026-10-04-ukulele-tab-chain-v1-3-design.md`. Evidence: `2026-10-04-v1-3-validation.md` ("What to improve next"), `../research/2026-10-03-quality/README.md` (ranks 3, 5, 6, 7 and 10, with the measurements in `strands/chords-applied.md`, `strands/structure-applied.md` and `strands/arrange-applied.md`).

## 1. Purpose

Version 1.3 made the strum box trustworthy and put chord changes on the bar lines. The next things a reader notices are a key in the header that is sometimes wrong and never hedged (Fame prints F minor on a margin of 0.005 over a grid that is D major in 83 of 101 bars; Pour Some Sugar On Me prints C# major where the chart says C# minor), and section names that do not match the song (Chelsea Dagger prints "chorus" over bars where nobody is singing; both solos print as verses; Summer of '69's bridge and intro both print "verse 2"). Version 1.4 takes the key from the chord stream with the mode from the harmonic stems, labels sections with the vocal stem's help and chart conventions, prints the chord a power chord stands for, shows the no-capo alternative, names run folders after the song, and closes two small 1.3 follow-ups on the sheet.

## 2. Scope

In: the key and its hedge; tonic power chords; vocal-aware section boundaries and labels; the bridge by chord novelty and display numbering by occurrence; the no-capo line; run folders named after the song, with a wider artist-prefix rule for titles; a trimmed all-N outro as "no instrument"; the strip skipping unplayed bars; install and run scripts for people who do not code, with `setup` no longer needing git; a README rewritten for a visitor, with a sample sheet and an MIT licence. Out: the chance-corrected strum confidence, the page budget and pattern pooling (version 1.5), fill refinement, earlier phrase shifts, the octave test, separating two guitars in one stem.

## 3. Stage changes

### 3.1 Harmony: the key from the chord stream

**Shared chroma.** `music/chroma.py: harmonic_chroma(stems, sr) -> HarmonicChroma` is computed once per run on the summed guitar, bass, piano and other stems (`chroma_cqt`, hop 512) with `bar_means(bars)`, `bar_energy(bars)` and `mean(mask)`. The fill (1.2) reads its bar means and energy instead of computing its own; the key reads the energy-masked mean over bars at or above `FILL_MIN_ENERGY` times the chorded median, so silence and pre-roll do not vote. The mix chroma stays only for the grid's beat-synchronous segmentation.

**Tonic.** Candidates are roots with at least `TONIC_MIN_SHARE = 0.2` of chord time (filled events count). Score = root time share + `FINAL_CHORD_BONUS = 0.10` when the song's final chord has that root and lasts at least a bar + `SECTION_END_WEIGHT = 0.15` times the share of sections ending on that root. Measured on the four known songs: Pour Some Sugar On Me C# 0.458 over B 0.421; Summer of '69 D 0.584 over A 0.451; Chelsea Dagger G 0.557 over D 0.336; Wet Leg C 0.593 over F 0.393. The alternative rule from the arrangement strand (relative-major pair by time-weighted diatonic share with half credit for a diatonic root of the wrong quality, ties broken by stem chroma) is computed as well and written to the harmony note `tonic_pair_rule`; only the first rule decides. Fame tells us whether the two ever disagree.

**Mode.** The sign of the Krumhansl major-minus-minor correlation at the chosen tonic on the harmonic chroma mean. Measured right on 4 of 4 with every profile: Pour Some Sugar On Me minor at C# by 0.379, Summer of '69 major at D by 0.299, Chelsea Dagger major at G by 0.313, Wet Leg major at C by 0.220. With fewer than four chord events the stage falls back to today's `estimate_key` on the mix.

**Hedge.** `Key` gains `method` (`chords_stems` or `mix_krumhansl`), `margin` (tonic score over the runner-up), `mode_margin`, `runner_up`, and `mix: Key | None` (today's estimate, kept for the validation table). The sheet prints `Key: G major (or D major)` when `margin < KEY_HEDGE_MARGIN = 0.05` or when the mix estimate's tonic disagrees with the chord tonic; under a capo the shape key and the sounding key are hedged the same way. Measured: Chelsea Dagger's 0.045 hedges; Summer of '69's 0.052 does not.

**Order.** The key is computed after the fill, so filled chords count.

### 3.2 Harmony: tonic power chords

After the key, when all four hold, the tonic's events are relabelled: `key.mode == "minor"`; the tonic root's chord time as `maj` exceeds its time as `min`; the harmonic chroma prefers minor at the tonic by at least `POWER_MODE_MARGIN = 0.2`; and that root holds at least `POWER_MIN_SHARE = 0.2` of chord time (so a one-bar Picardy or borrowed major tonic is left alone). Those events get `triad` = the key's quality, `label = "<root>:5"` and `power = True` (new `ChordEvent.power: bool = False`). No other label is touched: a wider rule relabels Summer of '69's and Chelsea Dagger's genuine majors and Pour Some Sugar On Me's real B and E. `to_triad` no longer collapses `X:5` to major; the stage writes `triad` explicitly. Evidence: the model has no `5` class and prints Pour Some Sugar On Me's riff (41 percent of chord time) as `C#:maj`; a chroma third test cannot separate it from real majors (median third-over-fifth 0.63 for the riff against 0.46 to 1.01 for genuine major triads). Measured effect: the riff prints C#m, Am at capo 4; the other three songs are unchanged.

### 3.3 Grid: vocal-aware sections

**Input.** `GridStage.requires` adds `separate/stems/vocals.wav`. The per-bar vocal level in dB is stored as `Grid.bar_vocal_db: list[float] = []`.

**Flags and runs.** A bar is vocal when its level is within `VOCAL_BELOW_MEDIAN_DB = 12` of the median over bars above -60 dB; flags are median-filtered over 3 bars. A non-vocal run is `VOCAL_RUN_MIN_BARS = 4` or more consecutive non-vocal bars strictly inside the song; the trailing run and the first boundary are never touched (the prototype wrongly moved Summer of '69's boundary into the fade). Measured runs match the known arrangements: Chelsea Dagger (0, 20) and (93, 108); Summer of '69 (0, 3), (67, 75), (114, 118); Pour Some Sugar On Me (12, 15), (67, 77); Wet Leg none.

**Boundaries.** After `boundaries_from_clusters(min_bars=4)` and before labelling, each run's edges become boundaries when both resulting pieces keep at least four bars; otherwise the nearest existing boundary moves onto the edge when the move is at most 3 bars and both neighbours keep four. Measured on the current segmentation: Summer of '69's one-bar boundary F-score 0.609 to 0.735 (8 to 10 of 13 hits), Pour Some Sugar On Me 0.484 to 0.555, Wet Leg unchanged.

**Labels.** `label_sections` gains the vocal share per segment. A segment with vocal share under `INSTRUMENTAL_BELOW = 0.25`, or the first or last segment under 0.5, is `intro`, `outro` or `instrumental` regardless of its cluster; chorus candidates are recurring clusters with bar-weighted vocal share of at least 0.5 (every recurring cluster passes on the four songs, 0.70 to 0.98); adjacent `intro`, `instrumental` and `outro` segments merge. Measured: Chelsea Dagger prints `intro 0-20`, `chorus 20-38`, `instrumental 93-108`; both solos print `instrumental`; Summer of '69's intro prints `intro 0-4`. No `solo` label: the guitar's share of the mix in the two solos is too close to the song medians to tell a solo from a riff. The four-bar minimum holds everywhere; phrase alignment and strum inheritance are unaffected; hand-edited `grid.json` labels still win downstream.

### 3.4 Score: the bridge by chord novelty

`music/relabel.py: refine_labels(grid, chords) -> list[str]`. For each section, novelty is the share of its chord-bars whose triad occurs in no other section. A section is the `bridge` when novelty is at least `BRIDGE_NOVEL_CHORDS = 0.5`, it is neither first nor last, its vocal share is at least 0.5, and it is the only such section (at most one bridge per song). Measured: Summer of '69 bars 58-69 (F, Bb, C) at 0.73 against 0.00 to 0.05 for all 49 other sections on the four songs. A once-only middle segment that fails the test is `verse`, not `bridge` (Wet Leg's 35-bar "bridge" with the verse chord set becomes a verse); the cluster-counting `verse 2` and `bridge 2` go. Refinement touches only labels in `{verse, chorus, bridge}`; `intro`, `instrumental`, `outro` and hand-edited labels pass through. The bare label lands in `ScoreSection.label`; `grid.json` is unchanged.

### 3.5 Strums: a trimmed outro with nothing to strum

When the trailing-bar drop (1.3) leaves the last section with every remaining bar `N` and no detected strikes on the analysed stem, the section is `no_instrument` (no strip, "No strummed instrument detected"), not inherited from its neighbour. Wet Leg's one-bar outro prints what 1.2 printed instead of "Strum as in chorus (uncertain)".

### 3.6 Run folders named after the song

A run folder is the cleaned title as a slug: `clean_title` lowercased, ASCII-folded, non-alphanumerics collapsed to single hyphens and trimmed (`summer-of-69`, `chelsea-dagger`, `pour-some-sugar-on-me`, `mangetout`, `fame`, `all-fired-up`). A local audio file uses its stem the same way.

`run` first scans the runs dir for a manifest whose `source` matches the URL, so a re-run or `--from` needs no network and finds the existing folder (today's id-named folders keep working as they are). If none matches, it asks yt-dlp for metadata only (no download), cleans the title, and creates the folder; a folder of that name for a different source gets `-2`, `-3`. The manifest records `source`, `video_id` and `title_slug`. `status`, `evaluate` and `--compare` take the folder name, with the video id accepted as a fallback for old folders. A metadata failure is a preflight Problem carrying yt-dlp's message. The five existing run folders are not renamed; the 1.4 validation runs land in the new names.

**Wider artist-prefix rule.** 1.2 strips a leading `<artist> - ` only when it equals the uploader case-insensitively. The third blind song's uploader is "Benatar Giraldo" for a title beginning "Pat Benatar - ", so the prefix would survive into the folder name. The rule becomes: a leading `X - ` (also en dash or colon) is stripped, and `X` becomes the artist, when `X` is at most four words and shares at least one word of three or more letters with the uploader, case-insensitively; the uploader-equality rule remains as the first test. Measured on the five known titles: no change (all five match by equality); "Pat Benatar - All Fired Up (Official Music Video)" with uploader "Benatar Giraldo" gives title "All Fired Up", artist "Pat Benatar".

### 3.7 Install and run without coding

The owner's daughter plays bass, does not code, and wants to try the tool. Today that needs `uv`, `git` on PATH, three commands and a terminal. Version 1.4 makes it: download, double-click install, double-click run, paste a link, the sheet opens.

**No git.** `youkelele setup` fetches the chord model as the zip archive of the pinned commit (`https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition/archive/<commit>.zip`), unpacks it into a sibling folder and renames it into place, as the clone does today, then runs the existing checkpoint verification and numpy patch. A folder already cloned by an earlier version is accepted as it is. `git` is no longer needed anywhere.

**Windows scripts at the repository root.**
- `install.cmd`: a one-line wrapper that runs `install.ps1` with the execution policy bypassed for that process.
- `install.ps1`: installs `uv` if missing (the official installer, `irm https://astral.sh/uv/install.ps1 | iex`, then refreshes PATH for the session); runs `uv sync`, `uv run youkelele setup` and `uv run playwright install chromium`; prints each step's outcome in plain words and a final "Ready" or the first error with what to do about it. It is safe to run twice.
- `run-youkelele.cmd`: asks for a YouTube link (or accepts a dropped audio file), runs `uv run youkelele run "<link>" --runs-dir runs` from the repository folder, and when the chain finishes opens `runs\<song-name>\07_render\sheet.pdf` with the default PDF viewer. On failure it leaves the window open with the last lines of output and the folder path to send to the owner.
- macOS and Linux get the equivalent `install.sh` and `run-youkelele.sh`, written but not exercised on this machine; the README says so.

**First-run downloads.** The separation model and the beat tracker fetch their weights on first use; the README states the approximate total download size (measured during implementation) and that the first song takes longer than later ones.

**Validation.** On this machine, in a fresh folder outside the repository: unpack the repository's ZIP as GitHub serves it, double-click `install.cmd`, then `run-youkelele.cmd` with one of the validation URLs; the sheet must open without a terminal command being typed. Recorded in the validation document with the exact steps a non-coder would take.

## 4. The sheet

- **Display names by occurrence.** `Verse 1`, `Verse 2`, `Chorus`, `Instrumental 1`, `Bridge`, `Outro`; a label that occurs once carries no number; "Strum as in" references use the same display names.
- **No-capo line.** When `capo > 0`, one line under the legend after the `Passing:` line: `Without a capo: C# 1114 (barre), F# 3124, B 4322 (barre), E 1402, A 2100, C#m 1444`, built from `arrangement.no_capo_alternative` with the fret formatter and the same dedupe as the diagrams, barre shapes marked. The arrange stage notes `capo_margin` and the per-capo scores in the manifest.
- **Power-chord badge.** A cell whose chord has `power = True` prints the key's chord with a small raised 5 (`C#m` with the badge, `Am` with the badge under capo 4), and the legend gains one line per such chord: `C#m is a power chord on the record`. The easy tier prints the plain key's chord with no badge.
- **Hedged key.** `Key: G major (or D major)`; under a capo, `Key: A major (or E major) (shapes)` and the sounding key hedged the same way.
- **The strip skips unplayed bars.** `example_bars` takes the first two full bars with at least one detected strike in `bar_onsets`; the mid-bar-change substitution rule is unchanged; a section with no struck bars keeps the fallback (pattern over an N.C. row). Chelsea Dagger's first-chorus strip no longer shows bars 9 and 10, before the guitar enters.

## 5. The README

The README today opens with the research reports and buries the tool under them; the tool section is a wall of bullets with no picture and no quick start, and "Known limitations" has become a version history. It is rewritten for a visitor to the repository, in this order:

1. **Title and one paragraph**: what the tool does (a YouTube link or audio file in, a printable ukulele chord-and-strum sheet out), for whom, and that it runs on an ordinary Windows, macOS or Linux computer with no graphics card.
2. **A sample sheet**: one PNG of page 1 rendered from the end-to-end test clip's score (the repository's own synthetic song, so no copyrighted chart is committed), stored under `docs/images/`, with a caption naming what the reader sees (header with key and tempo, chord diagrams, a section with its two-bar strip, the chord grid).
3. **Using it without coding** (section 3.7), written for someone who has never opened a terminal, as numbered steps with no jargon: on GitHub press the green "Code" button and "Download ZIP"; unzip it somewhere you can find; double-click `install.cmd` and wait until it says Ready (it downloads about N MB the first time); double-click `run-youkelele.cmd`, paste the YouTube link and press Enter; the sheet opens as a PDF when it is done, and it is also saved in the `runs` folder under the song's name. What to do if a window closes or says something is missing. A line that the tool makes ukulele sheets today and that other instruments are planned.
4. **Quick start for developers**: install `uv`, `uv sync`, `uv run youkelele setup`, `uv run youkelele run "<url>"`, where the PDF lands (`runs/<song-name>/07_render/sheet.pdf`), and that Chromium is needed for the PDF.
4. **How it works**: a table of the eight stages, one row each, with what the stage reads, what it writes and the model or method it uses.
5. **Correcting a result**: hand-editing a stage's JSON and `--from`, with the three notes that exist today (shifted section starts, `filled: true`, labels winning over refinement).
6. **Measuring**: `evaluate`, `--truth`, `--compare` and `--debug`, each in two lines with an example command.
7. **Options**: a table of every `run` flag (`--instrument`, `--tier`, `--beat-octave`, `--sections-k`, `--meter`, `--separator`, `--chord-model`, `--from`, `--to`, `--debug/--no-debug`, `--runs-dir`) with its values and default.
8. **Requirements and tests**: as today, shortened.
9. **Known limitations**: only what is still true after 1.4, one bullet each, no version narrative.
10. **Project history**: one line per version with links to its spec and validation document, and a link to the research folder.
11. **Background research**: the two reports and the research notes, moved here from the top.
12. **Licence**: the project is MIT (owner's decision, 2026-10-04): a `LICENSE` file is added and `pyproject.toml` gains `license = "MIT"`. The section also states the licences of what the tool vendors or downloads (the Chord-CNN-LSTM model, chords-db, Demucs weights, Beat This! checkpoints, static-ffmpeg), each checked from its source during implementation and quoted with a link; anything non-commercial or unclear is said to be so.

Measured by: the README renders on GitHub with the image showing; every command in it runs as written on a fresh clone after `uv sync` and `setup`; no sentence describes a version-numbered change rather than the tool as it is.

## 6. Data format changes

All defaulted; schema version stays 1; version 1.3 files load. `Key.method`, `Key.margin`, `Key.mode_margin`, `Key.runner_up`, `Key.mix: Key | None`; `ChordEvent.power: bool = False`; `Grid.bar_vocal_db: list[float] = []`; `Score.alternative_diagrams: list[ChordDiagram] = []`; `ScoreSection.label` carries the refined bare label; `manifest.json` gains `video_id` and `title_slug` and the notes `capo_margin`, `capo_scores`, `tonic_pair_rule`. The harness (`evaluate`) prints the key with its method and margins, the vocal runs, and each section's label.

## 7. Validation

Seven songs: the five from 1.3 and two new blind songs run from scratch, Pat Benatar, "All Fired Up (Official Music Video)" (`PsnYrH3BUP8`, 271 s, uploader "Benatar Giraldo") and INXS, "Need You Tonight (Official Video)" (`w-rv2BQa2OU`, 190 s, uploader "INXS"). Each of the five is re-run through the whole chain into its title-named folder and compared with its 1.3 run through the harness.

| Song | Expectation |
|---|---|
| Summer of '69 | key D major, not hedged; `Intro`, `Bridge` for bars 58-69, `Instrumental` for the solo; strum boxes unchanged from 1.3 |
| Chelsea Dagger | key G major (or D major), hedged; `Intro 0-20`, no chorus before bar 20, `Instrumental 93-108`; the first-chorus strip starts on a struck bar |
| Pour Some Sugar On Me | key C# minor; riff cells Am with the badge at capo 4 and the legend line; the no-capo line with six shapes; `Instrumental 67-77`; capo stays 4; every section still uncertain |
| Wet Leg "mangetout" | key C major; the 35-bar bridge prints as a verse; boundaries unchanged; outro "No strummed instrument detected" |
| David Bowie "Fame" | header read against a grid that is D major in 83 of 101 bars; labels judged against the vocal levels; both tonic rules' results recorded |
| Pat Benatar "All Fired Up" (blind) | the chain completes; folder `all-fired-up`, title "All Fired Up", artist "Pat Benatar"; tempo, key with margin, sections and labels, strum boxes, filled and passing chords recorded and judged from measurable features, with what cannot be verified stated plainly |
| INXS "Need You Tonight" (blind) | the chain completes; folder `need-you-tonight`, title "Need You Tonight", artist "INXS"; the same measurable record as above; a riff-based song with sparse chords, so the no-chord filling, the strum box and the key margin are the points to watch |
| All | folders named after the songs; no section shorter than four bars; page counts no worse than 1.3; `evaluate` prints the key method and margins and the vocal runs; nothing in a sheet contradicts the chord grid (a header key must be diatonic to most of the grid) |
| Non-coder path | from a fresh unpacked ZIP in a folder outside the repository: `install.cmd` ends with "Ready" without git installed on PATH for that shell; `run-youkelele.cmd` with one validation URL opens the sheet; the steps as the README lists them, nothing extra typed |

## 8. Decisions

- Evidence computed once where it is cheapest (harmonic chroma in harmony, vocal levels in grid); decisions made where the chord stream exists (key in harmony, names in score).
- The tonic comes from the chords and the mode from the stems; no 24-way profile search decides anything, because it is a coin toss on every source measured.
- Power chords are relabelled only at the tonic and only under the key's evidence; the sheet prints a playable shape and says what the record did.
- Section names follow chart convention: at most one bridge, chosen by chord novelty; intros, instrumentals and outros by the vocal stem; numbering by occurrence in the renderer, bare labels in the files.
- Run folders are for people; the manifest keeps the id for machines.
- The repository is MIT licensed; the README is written for a visitor, with the tool first and the research last, and ships a sample sheet rendered from the project's own test clip rather than a copyrighted song.
