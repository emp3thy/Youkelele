# Youkelele tab chain, version 1.1: design

Date: 2026-10-03. Status: approved in conversation, awaiting written review. Amends `2026-10-03-ukulele-tab-chain-design.md` (version 1). Evidence: `2026-10-03-real-run-lessons.md`, the analysis of the first three real-song runs.

## 1. Purpose

Version 1 produced correct chord content on real songs but sheets of ten to fifteen pages that a player cannot use: a slash staff drew every bar, bars within a section differ only by chord name, and most strum patterns were mainly rests. Version 1.1 makes the sheet short and readable, and applies four stage-rule changes each backed by a measurement across the songs run so far. The chain, its stages, its editable intermediate files and its resume workflow are unchanged.

## 2. Scope

In: a chord-grid sheet replacing the slash staff; removal of alphaTab from the package; a tempo cap on strum slots; a drum-backbeat test in the automatic tempo-octave rule; corrected last-bar and pickup-bar handling; a re-weighted capo score; a working module entry point for the CLI.

Out, deferred to a spike before any adoption: lowering the strike threshold of the strum majority vote (lesson 5). Out, awaiting more evidence: key mode detection from power chords, intro gap filling, bridge labelling by chord novelty, the chorus-margin flag, tempo from the mean beat interval, title hygiene (lessons 6 to 10).

## 3. The sheet (score and render stages)

### 3.1 Section block

Each section prints as:

1. **Heading line**: the section label; "Strum as played, N% repeatable" where N is `bar_repeat` as a percentage; "(uncertain)" when `uncertain`; "inherited from <label>" when `inherited_from` is set; "No strummed instrument detected" when `no_instrument`.
2. **Strum box**: the existing arrow box, printed once, only when the section is neither uncertain nor without instrument. An uncertain section prints the heading note and no box, because the chords are the dependable part.
3. **Chord grid**: rows of four bars. A cell shows the bar's chord name; a bar with more than one chord shows the names in time order separated by ` / ` (`G / D`); a bar with no chord shows `N.C.` in grey. Consecutive identical rows collapse into one row with `×N` at the right edge. Each row is one unbreakable block (`break-inside: avoid`); a heading keeps with its first row (`break-after: avoid`); sections no longer force a page break.
4. **Pickup bar**: when the grid marks bar 0 as a pickup, the sheet draws it as a narrow leading cell labelled "pickup" before the first full row, not as a full bar.

### 3.2 Header

Title, artist, key, capo, tempo, tuning, tier and meter as before; plus the stage-level strum note ("Strum detection uncertain for this song" when `strums_uncertain`, "Strum detected from full mix" when the source is the mix). When `capo > 0`, two more lines: "Shapes are relative to the capo" and "Sounding key: <key>".

### 3.3 alphaTab removed

The vendored `@coderline/alphatab` bundle, its fonts and licences, the per-section `AlphaTabApi` instances, the `assets/` copy and the file-URL worker constraints are removed from the package and the page. The page is plain HTML, CSS and inline SVG, printed to A4 by Playwright exactly as before (fixed 182 mm sheet width, A4 at 14 mm margins). The score stage keeps writing `score.alphatex` from `score.json`, since the emitter is tested and a future tab line would use it; nothing reads it in version 1.1.

### 3.4 Expected result

One to three pages for a three to five minute song. The 120-bar synthetic score used in the render tests prints in at most three pages.

## 4. Stage rules

Each rule below changes one measured constant or adds one measured test. Thresholds not mentioned are unchanged from version 1.

### 4.1 Strums: slot cap by tempo

Sixteen slots per bar are allowed only when a sixteenth lasts at least 105 ms, that is at 140 bpm and below; above 140 bpm the stage uses eight slots regardless of the odd-sixteenth share. The 25% share rule is unchanged. Evidence: Chelsea Dagger at 158 bpm got sixteenths of 95 ms and a grid fit of 0.40; the same onsets at eight slots fit 0.55 with section confidence 0.45 to 0.71; the cap changes neither Summer of '69 (already eight) nor Pour Some Sugar On Me (86 bpm, sixteen is plausible).

### 4.2 Grid: drum backbeat test in the automatic octave rule

The grid stage now also requires `separate/stems/drums.wav`, which exists by the time it runs. It computes the backbeat ratio: the spectral-flux strength of the drums stem in the 1.5 to 6 kHz band summed on beats 2 and 4 of the detected grid, divided by the same on beats 1 and 3. The drums stem counts as silent when its RMS is below 0.003 (Over the Rainbow measured 0.001; songs with drums measured far above). The automatic rule becomes: halve if and only if the detected tempo is above 140, the half lies in 60 to 95, and either the backbeat ratio is below 1.0 or the drums stem is silent. Evidence: the ratio is 2.1 to 2.4 on the three songs whose detected tempo was right, 0.86 on Riptide (right), 0.57 on I'm Yours (needed halving), and no drums on Over the Rainbow (needed halving); a narrower band cannot separate Chelsea Dagger at 158 (right) from I'm Yours at 150 and Over the Rainbow at 167 (both doubled). `grid.json` gains `backbeat_ratio: float | None` and `drums_silent: bool`. The `--beat-octave` overrides are unchanged.

### 4.3 Grid: bar ends and pickup

The final bar ends one median beat interval after the last detected beat, not at the end of the audio; audio after that belongs to no bar. Evidence: the last bar was stretched to 10.0 s on Chelsea Dagger and 7.1 s on Pour Some Sugar On Me and drawn as a full bar. A leading partial bar before the first full downbeat keeps bar index 0 and gains `pickup: true` in the `Bar` schema (default false); it holds the beats it has and the sheet draws it as a pickup.

### 4.4 Arrange: capo score

`score_capo` becomes the mean, over the distinct chord names in the song, of the best shape cost for that name transposed by the capo, plus 0.2 per capo fret; the extra surcharge above fret 3 is removed. Evidence: of seven variants tested on six chord lists (the three runs, the spike's two lists and C G Am F), only this one and a fragile count-weighted variant chose the published capo on all six, and only this one did so with clear margins (0.33 on Summer of '69, 0.47 on Pour Some Sugar On Me). Pour Some Sugar On Me moves from capo 2 with a barre on its most-used chord to capo 4 with all-open shapes. The one-shape-per-chord voicing rule and `no_capo_alternative` are unchanged.

### 4.5 Command line entry point

`python -m youkelele` and `python -m youkelele.cli` run `main()` and exit with its return code. Evidence: the module form exited silently and a batch of two songs "succeeded" in one second.

## 5. Data format changes

- `Bar.pickup: bool = False`.
- `Grid.backbeat_ratio: float | None` and `Grid.drums_silent: bool`.
- `ScoreBar` and `ScoreSection` are unchanged; the collapse of identical rows happens in the renderer, not in `score.json`, so the score remains a faithful bar-by-bar record for hand editing.
- `score.alphatex` is still written.
- The schema version stays 1: every added field has a default, so version 1 files load.

## 6. Validation

Re-run the three songs on their existing run folders from the grid stage (`--from grid`), since separation does not change, and check:

| Song | Expectation |
|---|---|
| Chelsea Dagger (`--beat-octave auto`) | Automatic rule keeps 158 bpm (backbeat ratio about 2.1); eight slots; grid fit about 0.55; at most three pages |
| Summer of '69 | Chord sequence and capo 0 unchanged; at most three pages; pickup bar drawn as a pickup; final bar not stretched |
| Pour Some Sugar On Me | Capo 4 with A, C, G, F shapes; header shows shapes relative to capo and sounding key; at most three pages |

The synthetic end-to-end test keeps every current assertion and adds a page-count ceiling of two.

## 7. Follow-on spike (not built here)

Strike threshold of the majority vote: 16 of 26 section patterns were 75% or more rests while their bars averaged 1.8 to 7.7 strikes, and the confidence score did not flag them. Before adopting a lower threshold (about 35 to 40%), a strike-density measure or a sparse-pattern uncertainty rule, measure all three on the five spike songs plus these three runs. The spike's output is a recommendation, not code.

## 8. Decisions

- A chord grid rather than a staff, because within a section bars differ only by chord name (31 of 142, 34 of 121 and 27 of 103 bars were distinct) and a strum pattern is read once per section.
- alphaTab removed rather than kept unused, to drop 1.4 MB and the file-URL constraints; the alphaTex emitter stays as the cheap bridge to a future tab line.
- Collapse identical rows in the renderer only, keeping `score.json` bar-by-bar for editing.
- A drum backbeat test rather than a narrower tempo band, because the band provably cannot separate the measured songs.
- The strike threshold is a spike first, because it would change every section pattern and has only been examined, not measured, so far.
