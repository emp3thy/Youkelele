# Youkelele tab chain, version 1.2: design

Date: 2026-10-03. Status: approved in conversation, awaiting written review. Amends `2026-10-03-ukulele-tab-chain-v1-1-design.md`. Evidence: `2026-10-03-v1-1-validation.md` ("What to improve next", items 1, 3, 4, 5, 7, 9 and 10).

## 1. Purpose

Version 1.1 made the sheet a chord grid and brought three of four real songs to two or three pages. Version 1.2 tightens the sheet further and fixes the gaps a reader notices first: a blind-test song fragmented into many short sections and printed four pages; repeating two-row patterns printed in full; titles carried upload text; whole intros and solos printed as no chord while the band was playing; rare passing chords got full barre diagrams; the header tempo used the median beat interval, which reads low; the pickup bar printed as a full cell on its own row.

## 2. Scope

In: the seven items above. Out: the strike-threshold spike (still pending, spec 1.1 section 7), key mode from power chords, bridge naming by chord novelty, the chorus-margin flag.

## 3. Stage changes

### 3.1 Grid: minimum section of four bars

`boundaries_from_clusters` takes `min_bars = 4` (was 2). A shorter segment merges into the following segment, or into the preceding one when it is last, with the same cluster reassignment rule as version 1.1. Evidence: Wet Leg "mangetout" had 17 of 25 sections under four bars and printed four pages; the three other validation songs have no section under four bars, so they are unaffected. Accepted cost: a genuine two-bar section, such as a short pre-chorus, no longer gets its own label; no validation song currently shows one.

### 3.2 Grid: header tempo from the mean beat interval

`Grid.bpm` is 60 divided by the mean interval of the gap-filled beats at the final octave. The automatic octave decision keeps using the median-based tempo it was measured on. Evidence: mean gives 138.6 against a published 139 (Summer of '69) and 84.9 against 85 (Pour Some Sugar On Me), where the median gave 136.4 and 85.7.

### 3.3 Ingest: title cleaning

`SourceInfo` gains `raw_title: str | None = None`; `title` holds the cleaned title. Cleaning, applied in order:
1. Remove a leading `"<artist> - "` (also with an en dash or colon) when it matches the artist field case-insensitively.
2. Remove bracketed or parenthesised upload tags whose text contains any of: official, video, audio, lyric, lyrics, visualiser, visualizer, hd, hq, 4k, remaster, remastered, live (whole words, case-insensitive).
3. Strip surrounding quotes and whitespace.
4. If the remaining title has no lower-case letters, convert it to title case.
The artist field gets step 4 only. Both fields remain hand-editable. Evidence: 4 of 4 validation titles repeated the artist, 3 of 4 carried "(Official ... Video)", one artist was in capitals.

### 3.4 Harmony: filling no-chord bars where the band plays

After beat snapping, each bar whose events are all `N` is a candidate. A candidate is filled when both hold:
- the summed RMS of the harmonic stems (guitar, bass, piano, other) in the bar is at least `FILL_MIN_ENERGY` times the median harmonic RMS over bars that hold a chord (this is the measured definition; see `music/fill.py`);
- the bar's mean chroma (CQT chroma of the summed harmonic stems) correlates with the template of one of the song's existing chord labels (triad templates from `quality_to_bitmap`) at least `FILL_MIN_MATCH`, and beats the second-best template by at least `FILL_MIN_MARGIN`.
A filled bar becomes one event spanning the bar, with the matched label, its triad, `confidence` equal to the correlation, and `filled: true` (new `ChordEvent.filled: bool = False`). The three constants are set by measurement during implementation: Chelsea Dagger's intro and Pour Some Sugar On Me's solo are the positive cases; Summer of '69 and Wet Leg are the controls, where filling must not add chords to bars that are genuinely silent or unpitched. The measured values and the evidence are recorded beside the constants. The harmony stage now also requires the four harmonic stems.

### 3.5 Arrange: passing chords

A chord name is passing when its events cover less than 2% of the song's chord time and none of its events is longer than one bar. `ArrangedChord` gains `passing: bool = False`. Passing chords keep their shape; only presentation changes. Evidence: Wet Leg's C# (1.1%, a barre shape) and Chelsea Dagger's B (0.7%, one event, a barre shape).

### 3.6 Score: phrase alignment

When a section's chord changes fall predominantly on bars of one parity relative to the section start, and the section start is on the other parity, the section's start (and the previous section's end) moves one bar later. At most one bar of movement per boundary; never past the next boundary; never creating a section under four bars. `ScoreSection` gains `shifted: int = 0` recording the move. Evidence: Summer of '69's first verse prints "D A A D" because its boundary is one bar into the two-bar rhythm.

## 4. The sheet

- **Repeated blocks.** After identical consecutive rows collapse, the renderer looks for the longest unit of 2 to 4 rows that repeats immediately at least twice, prints the unit once with `×N`, and prints any remainder after it. Exact repetition of cell text only. `score.json` stays bar by bar.
- **Passing chords.** Named in their grid cells; omitted from the diagram legend; listed on one line below the legend as `Passing: <name> <frets>` in fret notation (G C E A order), for example `Passing: B 4322, C# 1114`.
- **Filled chords.** Cells holding a filled chord show its name in italics; a one-line note under the header explains italics as "chords inferred where the recording had no clear chord".
- **Pickup.** A narrow leading cell, about a quarter of a normal cell's width, at the start of the section's first row, labelled "pickup", not a row of its own.

## 5. Data format changes

`SourceInfo.raw_title: str | None = None`; `ChordEvent.filled: bool = False`; `ArrangedChord.passing: bool = False`; `ScoreChord.filled: bool = False` and `ScoreChord.passing: bool = False` (copied by `build_score`); `ScoreSection.shifted: int = 0`. Schema version stays 1; version 1.1 files load.

## 6. Validation

Re-run the four validation songs through the whole chain from their URLs, since title cleaning happens at ingest; separation is seeded, so the stems match the previous runs.

| Song | Expectation |
|---|---|
| Wet Leg "mangetout" | no section under four bars; at most three pages |
| Chelsea Dagger | intro bars filled with chords from the song's set; alternating G and D rows collapsed as a block; at most three pages, ideally two |
| Summer of '69 | first verse rows start on D A; tempo header 138 or 139; at most three pages |
| Pour Some Sugar On Me | solo bars filled where the band plays; still capo 4; at most three pages |
| David Bowie, "Fame" (`Ypgq0qdgVZA`, 261 s), a second blind test run from scratch | the chain completes; title cleaned to "Fame" (the "(2016 Remaster)" tag removed); no section under four bars; at most three pages; tempo, key, capo, filled bars and passing chords recorded and judged from measurable audio features, with what cannot be verified stated plainly |
| All | titles without artist prefix or upload tags; passing chords without diagrams; no filled chords in bars without harmonic energy |

## 7. Decisions

- Four-bar minimum in the grid rather than grouping short sections in the renderer, so labels and strum patterns are computed on musically sized sections.
- Template matching restricted to the song's own chord set, so filling cannot introduce a chord the song does not contain; filled chords are marked in the sheet.
- Passing chords keep their name; only the diagram goes.
- Constants for filling are measured, not guessed, and recorded with their evidence.
