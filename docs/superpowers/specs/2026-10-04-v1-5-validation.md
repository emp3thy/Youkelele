# Version 1.5 validation on seven real songs and one blind song

Date: 2026-10-04. Branch `worktree-v1-5` at `5cad67c` plus this commit (package version 0.6.0). Checks every expectation in section 8 of `2026-10-04-ukulele-tab-chain-v1-5-design.md` against the kept version 1.4 runs, and runs one song the chain had never seen. Bar and section numbers are 0-based, as in `grid.json`; a range written `55-61` ends before bar 61 unless it says "printed bars", which are inclusive. "Grid section" means a section of `grid.json`; "planned section" means a section of the 1.5 section plan, which is what the sheet prints.

## Runs and baselines

The seven version 1.4 run folders under `runs\` were the baseline. Before any re-run, `02_grid` to `07_render`, `manifest.json` and `source_meta.json` of each were copied to `%TEMP%\youkelele-v15-validation\baseline\<folder>\`, with the output of `uv run youkelele evaluate <folder>` beside them. Then, one at a time, each folder was re-run in place with `uv run youkelele run "<source from its manifest>" --from <stage> --runs-dir C:\Users\gethi\sources\Youkelele\runs`; every source resolved to its own folder with no prompt. The blind song ran from ingest with the same `--runs-dir`. Every run exited 0. Each run's log is under `%TEMP%\youkelele-v15-validation\logs\`.

| Song | Folder | From | Wall time of the command | Stage times from the manifest |
|---|---|---|---:|---|
| Summer of '69 | `summer-of-69` | strums | 12 s | arrange 0.2 s, score 0.1 s, render 1.0 s |
| Chelsea Dagger | `chelsea-dagger` | strums | 13 s | arrange 0.2 s, score 0.1 s, render 1.0 s |
| Pour Some Sugar On Me | `pour-some-sugar-on-me` | strums | 13 s | arrange 0.3 s, score 0.1 s, render 0.9 s |
| Wet Leg "mangetout" | `mangetout` | strums | 11 s | arrange 0.2 s, score 0.1 s, render 1.0 s |
| David Bowie "Fame" | `fame` | strums | 11 s | arrange 0.2 s, score 0.1 s, render 1.0 s |
| Pat Benatar "All Fired Up" | `all-fired-up` | strums | 13 s | arrange 0.3 s, score 0.1 s, render 1.0 s |
| INXS "Need You Tonight" | `need-you-tonight` | harmony | 85 s | strums 5.1 s, arrange 0.2 s, score 0.1 s, render 1.0 s |
| The Cars "You Might Think" (blind) | `the-cars-you-might-think` | ingest | 304 s | separate 239.4 s, grid 18.2 s, harmony 23.8 s, strums 5.4 s, arrange 0.4 s, score 0.1 s, render 0.9 s; ingest done to render done 288.2 s (audio 2.85 MiB) |

The wall time includes `uv run` starting Python; the first stage of a partial re-run has no start stamp, so its own time is inside the wall time only. Every manifest records version 0.6.0 for each stage that ran: strums to render on six folders, harmony to render on Need You Tonight, all eight stages on the blind song. The stages that were not re-run keep their 0.5.0 stamps, as they should.

Measurement: `evaluate` on all eight folders and `evaluate <baseline> --compare <folder>` on the seven; a script (`measure.py`) that compares `grid.json`, the chord events, the key and `strums.json` baseline against new, bar by bar, prints each planned section with its members and the 1.4 pattern of its longest member, and applies the 1.5 certainty rule (the stage's own `section_summary` and `structure_test`, seeded as the stage seeds them) to every 1.4 grid section on both the 1.4 and the 1.5 onsets; page counts from the PDFs; every page of all eight sheets rasterised with PyMuPDF and looked at. `compare_runs` pairs sections by position, so on the two songs whose plan merges sections (Wet Leg, All Fired Up) its rows after the first merge compare different sections; the script pairs each planned section with its longest member instead. All Fired Up was also re-run from strums a second time: `strums.json` and `score.json` were byte-identical to the first re-run (A9).

## Expectations from spec section 8

Written before the runs, as the spec states them; checked after.

| Expectation | Met? | Figure |
|---|---|---|
| Section counts 12, 7, 8, 8, 9, 6, 7 | **No** | 12, 7, 8, 8, 9, **8**, 7. All Fired Up merged 13 grid sections into 8, not 6: the sandwich merge of 110-132 did not fire (see All Fired Up below). Wet Leg merged 9 into 8 as expected. After this validation the controller ruled that the sandwich rule stands as written and that All Fired Up's expected count is 8; spec 3.4 is being amended to say so |
| All Fired Up's merged Verse 1 prints 29 to 49 with `DUDUDUDU`, certain | Yes | Planned 28-49 (grid 1 and 2), shifted one bar by phrase alignment, printed bars 29 to 48; pattern `DUDUDUDU` from its longest member 33-49, confidence 0.555, full vote at strike density 0.672 (at least 0.6), certain |
| Pages 2, 3, 2, 2, 2, at most 3, 2 | Yes | 2, 3, 2, 2, 2, 2, 2 (1.4: 3, 3, 2, 3, 3, 4, 2). Twenty pages become fifteen |
| Certainty flips exactly Summer of '69 53-58, All Fired Up 55-61 and 128-132, and no other | Yes | On the 1.4 grid sections the 1.5 rule flips exactly these three, on the 1.4 onsets and on the 1.5 onsets alike: p 0.328, 0.065 and 0.207 (the spec measured 0.332, 0.064 and 0.208). Every other grid section on the seven songs keeps its 1.4 state. How they print: Summer of '69's Verse 3 (53-58) prints uncertain; All Fired Up's 128-132 prints uncertain as its own Chorus 3 (the sandwich did not absorb it); All Fired Up's 55-61 is absorbed into the merged Verse 2 (55-110), whose strip comes from its longest member 61-90 (`D-D-D-DU`, p 0.001, certain), so that flip does not reach the sheet |
| Riff marker on every Fame section and every Need You Tonight section with its own pattern; on the recorded list; nowhere else; merged sections take their longest member's flag | **No** | Fame 9 of 9. Need You Tonight: the five sung sections and the Outro 79-86 are marked; the Intro 0-13 is not (entropy 0.862, single share 0.444). Spec 8's wording is being corrected to "every Need You Tonight section with its own certain pattern": the Intro is uncertain (confidence 0.084, p 0.989), so it is outside the expectation as corrected, and Need You Tonight agrees. Recorded list: Summer of '69 0-4 and 4-19, Wet Leg 0-5 and 100-108, All Fired Up Verse 1 (longest 33-49), Verse 2 (longest 61-90) and Chorus 2 (110-124) are marked; **All Fired Up Chorus 1 (49-55) is not** (0.806 and 0.433 against 0.788 and 0.625 in `riff-thresholds.md`), the one remaining departure. Nothing outside the list, Fame and Need You Tonight is marked. Chosen fix: the riff features move to the detector's own onsets before the recall gate, the definition the thresholds were measured on, in the final fix wave; All Fired Up Chorus 1 (49-55) is expected to regain its flag after it. See "Riff marker" below |
| Headers unchanged except Need You Tonight "F major (or C major)" | Yes | Summer of '69 "D major", Chelsea Dagger "G major (or D major)", Pour Some Sugar On Me "A minor (shapes)" sounding "C# minor", Wet Leg "C major", Fame "D major (shapes)" sounding "F major", All Fired Up "G major", Need You Tonight "F major (or C major)" (1.4: "C major (or F major)"). Votes on Need You Tonight: score C, pair F, mix F, decided by the mix |
| Power line on Pour Some Sugar On Me's easy sheet; no other sheet has one | Yes | "Am is a power chord (root and fifth) on the record; this sheet prints the triad." under the no-capo line, on Pour Some Sugar On Me only (also not on the blind song) |
| Chords, beats, bars and onsets identical to 1.4 on the six re-run from strums | Yes | `grid.json` byte-identical on all seven; chord events identical (bar, beat, start, end, label, triad, filled, power) on all seven, Need You Tonight included; slots per bar, source and grid fit identical; `bar_onsets` identical in every bar of every song (the recall gate fired on the same sections, now counted as planned sections) |
| Blind song `3dOx510kyOs` runs to a sheet with exit 0 | Yes | Exit 0, 304 s; key, sections, riff flags, certainty, pages and the power gates are recorded below |

## Per song

| Song | Planned sections (grid) | Pages 1.4 to 1.5 | Last page filled to | Strips beside, above | Flips | Riff marked | Header |
|---|---|---|---:|---|---|---|---|
| Summer of '69 | 12 (12) | 3 to 2 | 0.90 | 9, 0 | Verse 3 53-58 to uncertain | Intro 0-4, Verse 1 4-19 | D major |
| Chelsea Dagger | 7 (7) | 3 to 3 | 0.34 | 3, 3 | none | none | G major (or D major) |
| Pour Some Sugar On Me | 8 (8) | 2 to 2 | 0.76 | 0, 0 (all uncertain) | none | none | A minor (shapes), sounding C# minor |
| Wet Leg "mangetout" | 8 (9) | 3 to 2 | 0.58 | 6, 1 | none | Verse 1 0-5, Chorus 3 100-108 | C major |
| Fame | 9 (9) | 3 to 2 | 0.91 | 6, 3 | none | all nine | D major (shapes), sounding F major |
| All Fired Up | 8 (13) | 4 to 2 | 0.89 | 3, 1 | 55-61 (absorbed), 128-132 (Chorus 3) to uncertain | Verse 1, Verse 2, Chorus 2 | G major |
| Need You Tonight | 7 (7) | 2 to 2 | 0.59 | 2, 3 | none | the five sung sections and the Outro | F major (or C major) |

"Last page filled to" is the lowest text on the last page as a share of the page height. No chord cell wraps on any page of the eight sheets (A16).

### Summer of '69

**Pages.** Page 1: header, seven diagrams, Intro and Verse 1 (both with the riff wording and mostly muted strips, `D-xx-xxx` and `xxxUxxxx`), Chorus 1, Verse 2, Chorus 2, every strip one bar beside the rows. Page 2: Verse 3 (uncertain, no strip), Bridge, Instrumental, Verse 4, Chorus 3, Verse 5 and Outro (uncertain).

**Quality.** A page shorter, as the spec measured; every certain section's strip sits beside its rows. The opening guitar line marked as a riff is on the recorded list; whether it is one is a listening question. Verse 3 (53-58, `DU-UDUDU`, confidence 0.693) now prints uncertain because a five-bar section whose bars all look alike gives the shuffle test nothing to beat (p 0.328).

### Chelsea Dagger

**Pages.** Page 1: header with the hedge, seven diagrams, "Passing: B 4322", Intro (uncertain), Chorus 1 (strip beside), Verse 1 (two-bar strip above, its second bar changes from Em to Bm). Page 2: Verse 1 continued, Chorus 2 (beside), Verse 2 (two bars above), Instrumental (beside). Page 3: Chorus 3 (two bars above) and its rows, a third of the page.

**Quality.** Unchanged in content. Three pages as the spec predicted: three of its six strips change chord inside a bar and stay above the rows.

### Pour Some Sugar On Me

**Pages.** Page 1: header, Am G C F, "Passing: D 2220", the no-capo line, then the power line, Intro, Verse 1, Chorus 1. Page 2: Verse 2, Chorus 2, Instrumental, Verse 3, Chorus 3.

**Quality.** The default sheet now says the riff is a power chord, under the chord diagrams after the no-capo line, and still two pages. Every section stays uncertain; no section is marked riff (the two-guitar sections sit at single share 0.153 to 0.426, under 0.45).

### Wet Leg "mangetout"

**Pages.** Page 1: header, C F Dm, "Passing: C# 1114", Verse 1 (riff wording), Chorus 1, Verse 2, Chorus 2, all strips beside. Page 2: Verse 3, Verse 4 (58-100, the merged old Verse 4 and Verse 5, strip `DUDUxxDU` from 65-100), Chorus 3 (two-bar strip above, riff wording), Outro ("No strummed instrument detected").

**Quality.** The merge the spec predicted: 58-65 joined 65-100 and prints as one Verse 4 with a ×9 repeat. A page shorter. Verse 1 and Chorus 3 carry the riff wording as recorded.

### David Bowie "Fame"

**Pages.** Page 1: header, Dm G D, passing and no-capo lines, Intro (two bars above), Verse 1, Instrumental 1, Verse 2 (beside). Page 2: Instrumental 2 (above), Chorus (beside), Verse 3 (above), Instrumental 3, Verse 4 (beside); nine tenths of the page.

**Quality.** Every section reads "Riff heard in this section: strum the chord to this rhythm", which is what the ear said of this record. A page shorter. Patterns, confidence and certainty are as in 1.4.

### Pat Benatar "All Fired Up"

**Pages.** Page 1: header, Am G Em D, Intro (uncertain, 28 bars), Verse 1 (from printed bar 29, `DUDUDUDU` beside, riff wording), Chorus 1 (beside), Verse 2 (two-bar strip above: G, then D to G inside the bar). Page 2: Verse 2's rows continued (two rows repeat ×3), Chorus 2 (uncertain, riff wording), Verse 3 (124-128, uncertain), Chorus 3 (128-132, uncertain), Outro (beside).

**Quality.** From four pages to two, and from eight verses and three choruses to Intro, Verse 1, Chorus 1, Verse 2, Chorus 2, Verse 3, Chorus 3, Outro. The plan is 0-28, 28-49 (grid 1, 2), 49-55, 55-110 (grid 4 to 8), 110-124, 124-128, 128-132, 132-156.

**The miss.** The spec expected the sandwich rule to join 110-124, 124-128 and 128-132 into one Chorus 2. It did not fire: the fragment 124-128 is four bars of G, and the chorus after it, 128-132, plays only Em (128, 129) and D (130, 131), so the fragment's G is a triad that neighbour never plays (pair novelty 1.0 against 128-132, 0.0 against 110-124). The research table (`sections-by-chords.md` 3.8) says "Its G is in both"; the research's own per-section table in the same document lists 128-132 as "Emx2 Dx2" (its All Fired Up table, row 11), so the claim contradicts the research's own figures; it is true only if bar 132, the Outro's first bar (G), is counted. The code follows the rule as written; nothing was tuned, and the controller has ruled that the rule stands as written and that All Fired Up's expected section count is 8. Two consequences: the sheet prints a four-bar Verse 3 and a four-bar Chorus 3 (both uncertain) where the spec expected one 22-bar Chorus 2, and 128-132's flip to uncertain shows on the sheet. The page count is still two.

**The merged sections' patterns.** Verse 1 takes `DUDUDUDU` from 33-49 (ear-confirmed in 1.4); the absorbed 28-33 had printed `DUxxxUxU` in 1.4. Verse 2 takes `D-D-D-DU` from 61-90; its absorbed members printed `D-Dx-U-U` (55-61), `xUDxxxx-` (90-97, uncertain), `xxDxDxDx` (97-104) and `Dxxxxxxx` (104-110) in 1.4. Whether one pattern serves the whole of Verse 2 is the listening pass's question (clips below).

### INXS "Need You Tonight"

**Pages.** Page 1: header "Key F major (or C major)", C Eb F Cm, "Passing: Gm 0231", Intro (uncertain), Verse 1 (beside), Chorus 1 (two bars above), Verse 2 (two bars above). Page 2: Verse 2 continued, Chorus 2 (above), Verse 3 (beside), Outro (uncertain).

**Quality.** The header now leads with the tonic the ear heard (F) and hedges the score rule's C. The chord rules disagreed (score C by 0.327; pair rule a tie that the chroma breaks for F) and the mix estimate (F) decided. Every sung section and the Outro carry the riff wording; the Intro does not (see below).

## Riff marker

Measured flags against the recorded list, by planned section:

| Song | Marked | Expected | Agrees? |
|---|---|---|---|
| Summer of '69 | Intro 0-4 (0.611, 0.667), Verse 1 4-19 (0.693, 0.547) | the same | yes |
| Chelsea Dagger | none | none | yes |
| Pour Some Sugar On Me | none | none | yes |
| Wet Leg | Verse 1 0-5 (0.795, 0.600), Chorus 3 100-108 (0.798, 0.561) | the same; Verse 4 takes 65-100's "no" | yes |
| Fame | all nine (entropy 0.695 to 0.760, single share 0.466 to 0.629) | all nine | yes |
| All Fired Up | Verse 1 (33-49: 0.670, 0.589), Verse 2 (61-90: 0.773, 0.500), Chorus 2 (110-124: 0.701, 0.500) | also Chorus 1 49-55 | **no**: Chorus 1 reads 0.806, 0.433 |
| Need You Tonight | Verses 1 to 3, Choruses 1 and 2, Outro 79-86 (0.646, 0.630) | every section with its own certain pattern (spec 8 as corrected) | yes: the unmarked Intro (0.862, 0.444) is uncertain |

Two departures from what spec 8 was written to expect, neither tuned:

- **All Fired Up 49-55.** `riff-thresholds.md` measured 0.788 and 0.625 on eight onsets. The stage now reads the section's onsets after the recall gate, which added strikes there (the gate's log: 1.3 to 4.8 strikes per bar on the slot grid), and the added onsets are mostly not single notes. The figures that moved are exactly the recall-boosted sections (33-49 went from 0.660 and 0.614 to 0.670 and 0.589; 61-90 from 0.729 and 0.721 to 0.773 and 0.500); 110-124, not boosted, is identical (0.701, 0.500). So the research measured the riff features on the onsets before the gate, and the stage measures them after it. Chosen fix: the features move to the detector's own onsets before the gate in the final fix wave, and this section is expected to regain its flag.
- **Need You Tonight's Intro.** The research's truth rows for this song were the five sung sections (`riff-thresholds.md`, truth mapping), and its list of unlabelled riff rows named the Outro 79-86, not the Intro; the spec's wording "every Need You Tonight section with its own pattern" reached the Intro, and is being corrected to "every Need You Tonight section with its own certain pattern". The Intro is uncertain (confidence 0.084, p 0.989), which is the reason it falls outside; its first eight bars are drums and voice (an ear fact) and its pattern explains 18% of its strokes. The marker on the Outro is the research's twelfth unlabelled row: the spec's sentence "eight on All Fired Up" counts it with All Fired Up's seven.

The one known miss stands: All Fired Up's ear-confirmed strum (33-49, now Verse 1) prints the riff wording, as A13 recorded; its instruction ("strum the chord to this rhythm") is still right there.

## The blind song: The Cars "You Might Think"

Source `https://www.youtube.com/watch?v=3dOx510kyOs`, raw title "The Cars - You Might Think (Official Music Video)", uploader "RHINO". Not listened to; the figures are recorded, not judged.

| What | Recorded |
|---|---|
| Run | Exit 0, 304 s from the command to the sheet; folder `the-cars-you-might-think` |
| Title and artist | Title "The Cars - You Might Think", artist "RHINO": the uploader is the record label and does not match the title's prefix, so the title rule left the prefix in the title and took the uploader as the artist. Both print on the sheet |
| Tempo, bars | 134 bpm (136.4 detected, octave none), 101 bars, 4/4 |
| Key | D major; header "Key C major (shapes)", "Capo fret 2", "Sounding key: D major"; not hedged |
| Three votes | score D, pair D (by 0.124, not a tie), mix D: decided by agreement. Score margin 0.0505 over G, 0.0005 above `KEY_TIE_MARGIN` (0.05), so no close-call hedge; mode margin 0.382 |
| Chords | D 59.1 s, G 50.2 s, A 43.8 s, Bm 23.3 s, N 3.1 s; printed C, F, G, Am at capo 2; no-capo line "D 2220, G 0232, A 2100, Bm 4222 (barre)"; 2 bars filled (italic) |
| Power-chord gates | Did not fire. Of the four gates two fail: the key is major (the first gate), and the stems prefer major at D by 0.382 (the gate wants minor by 0.2). D is plain major for 59.1 s and minor for none, and holds 0.34 of chord time, so the other two would pass. No power line |
| Sections | 10 grid sections, 10 planned (no merge; the song's one chord group holds every sung bar, one-loop share 1.00): Intro 0-11, Verse 1 11-24, Chorus 1 24-33, Verse 2 33-45, Chorus 2 45-52, Verse 3 52-68, Chorus 3 68-72, Instrumental 72-76, Verse 4 76-90, Chorus 4 90-101. Vocal runs (0, 11) and (71, 76) |
| Strums | Eighth-note grid, guitar stem (ratio 0.36), grid fit 0.94, no recall boost |
| Certainty | 9 of 10 certain. Eight are full `DUDUDUDU` votes passed on density (0.63 to 0.99); Chorus 3 `-UDUDUD-` passed the shuffle test (p 0.025); the Instrumental 72-76 (`DUD-DUDU`, confidence 0.750) failed it (p 0.067) and prints uncertain |
| Riff flags | 8 of 10 marked, exactly the eight full-vote sections: every section except Chorus 3 and the Instrumental (entropy 0.691 to 0.793, single share 0.544 to 0.694) |
| Strips | Seven two-bar strips above the rows (a chord changes inside a bar, F/G or Am/G, in each of those sections) and two one-bar strips beside |
| Pages | 3, the last filled to 0.69 |

**What cannot be verified without listening.** Whether the key is D major and not G (the score margin is the smallest of the eight songs and only just clears the hedge line); whether the guitar is a riff, as the marker says on eight sections, or a dense eighth-note strum read as single notes, as on All Fired Up's known miss (full votes at density up to 0.99 look like strumming); whether `DUDUDUDU` is what is played; whether Chorus 3 (four bars, half sung) and the Instrumental are real parts; the section names in general (the names rest on loudness, since verse and chorus share their chords).

## Ear clips for the listening pass

Under `%TEMP%\youkelele-ear-v15\<song>\`, made the way the 1.5 research's `make_clips.py` made them (`make_clips_v15.py` and `make_clips_extra.py` in the validation scratch folder). A `strum_` clip is the guitar stem over the bars named, with a click on every struck slot of the pattern named; each has an `onsets_` twin with clicks on the detected strokes instead. A `key_` clip is ten seconds of the mix from the loudest sung section, then a synthesised triad.

| Clip | Tests |
|---|---|
| `all-fired-up\strum_verse1_longest_33-41.wav` | Verse 1's printed `DUDUDUDU` on its longest member (ear-accepted in 1.4; should still fit) |
| `all-fired-up\strum_verse1_fragment_28-33.wav` | whether the absorbed five-bar fragment plays Verse 1's pattern too (A2, A4) |
| `all-fired-up\strum_verse2_longest_61-69.wav` | Verse 2's printed `D-D-D-DU` on its longest member 61-90 |
| `all-fired-up\strum_verse2_fragment_55-61.wav` | whether the absorbed 55-61 plays Verse 2's pattern (A2, A4) |
| `all-fired-up\strum_verse2_fragment_90-97.wav` | whether the quietly sung 90-97 plays Verse 2's pattern (A4's named cost) |
| `all-fired-up\strum_verse2_fragment_97-104.wav` | the same for 97-104 |
| `all-fired-up\strum_verse2_fragment_104-110.wav` | the same for 104-110 |
| `all-fired-up\strum_flipped_1-4pattern_55-61.wav` | the flip of 55-61: does its own 1.4 pattern `D-Dx-U-U` fit (the spec says no bar matches it) |
| `all-fired-up\strum_flipped_chorus3_128-132.wav` | the flip of 128-132, now printed as Chorus 3: does `D---DUD-` fit (the spec thought the flip probably wrong) |
| `summer-of-69\strum_flipped_verse3_53-58.wav` | the flip of Verse 3: does `DU-UDUDU` fit its five bars (the spec called the flip defensible) |
| `the-cars-you-might-think\key_D_major.wav` | the header's D major against the mix |
| `the-cars-you-might-think\key_G_major.wav` | the score rule's runner-up G, 0.0505 behind |
| `the-cars-you-might-think\strum_certain_riff_planned5_52-60.wav` | Verse 3, the longest certain section, marked riff: does `DUDUDUDU` fit, and is it a riff or a strum |
| `the-cars-you-might-think\strum_certain_riff_verse1_11-19.wav` | Verse 1, the most confident verse (0.957), marked riff with a full vote: riff or strum |
| `the-cars-you-might-think\strum_certain_strum_chorus3_68-72.wav` | Chorus 3, the only certain section not marked riff: does `-UDUDUD-` fit |

## What to improve next

Ranked by benefit to the person reading the sheet.

1. **Read the title and artist when the uploader is a label.** Stage: ingest. Evidence: the blind song prints "The Cars - You Might Think" by "RHINO". A title of the form "<artist> - <title>" whose prefix does not match the uploader could still be split when the uploader is not a person (a label channel), with the prefix taken as the artist. The first thing on the sheet is wrong, on the one song the chain had not seen.
2. **Weigh the two-bar strip's page cost on songs with many split bars.** Stage: render. Evidence: `strip_bars` as built is the variant the page study measured: two bars when a shown bar changes chord, the shown bars being `example_bars`' choice (which swaps the second bar for a later bar that changes chord inside it); spec 5.1's prose is being corrected to "a shown bar" to match. Its measured cost on the blind song is seven two-bar strips above the rows and a third page; Chelsea Dagger keeps its third page for the same reason, as the page study predicted. A strip that keeps one bar unless one of the first two bars changes is an unmeasured idea, not a measured alternative.
3. **The sandwich rule stands as written.** Stage: strums (section plan). Evidence: its one design case (All Fired Up 124-128) does not meet its precondition (chorus 128-132 holds no G), so it fired on no song, and All Fired Up prints a four-bar Verse 3 and a four-bar Chorus 3. All Fired Up's expected section count is now 8 (spec 3.4 is being amended). Any restatement of the rule would need evidence from more than this one song, under the generality rule; none is proposed here.
4. **Read the riff features on the detector's own onsets.** Stage: strums. Evidence: the recall gate's added onsets move the features on boosted sections (All Fired Up 49-55 lost its flag, 0.788 and 0.625 to 0.806 and 0.433), so the thresholds in spec 4.3 were set on onsets the stage no longer reads there. Chosen fix: the features move to the detector's own onsets before the recall gate, the definition the thresholds were measured on, in the final fix wave; All Fired Up Chorus 1 (49-55) is expected to regain its flag.
5. **Listen to the blind song's riff marks.** Evidence: eight of ten sections marked riff with full eighth-note votes at density up to 0.99, the pattern of All Fired Up's known miss. If the ear says strum, the marker's false-positive rate on tight strumming is the next thing to fix, and the A13 bands rest on one counter-example fewer than they need.
6. **Hedge a tonic call this close.** Stage: harmony. Evidence: the blind song's score margin is 0.0505 against a 0.05 line; all three votes agree on D, so nothing hedges. A margin this close to the line is a coin toss by measure even when the rules agree.
7. **Pair sections by member in `compare_runs`.** Stage: tooling. Evidence: on Wet Leg and All Fired Up the compare rows after the first merge compare different sections; the plan's members say which 1.4 section each planned section came from.
8. **Carried from 1.4**, unchanged: correcting late refrain boundaries, recovering sustained strums on sixteenth grids, and the mode hedge.

Not ranked as faults: All Fired Up's 55-61 flip not reaching the sheet (the section is absorbed for naming, and its strip comes from 61-90 by design); the one-loop log line firing on Wet Leg, Fame, All Fired Up and the blind song at share 1.00 (spec 3.3 gives 0.96 as its example; the research's table gives 0.93 to 1.00 for the one-loop songs).

## Assumptions after validation

Status of spec section 9's assumptions after these runs; the ones this validation was asked to settle first, then the rest that it touched.

| # | Assumption | Status now | Evidence |
|---|---|---|---|
| A2 | A same-label section under 8 bars that adds no chord is a fragment of its neighbour | **Measured on the runs**, unverified by ear | 6 merges by the fragment rule (Wet Leg 58-65; All Fired Up 28-33, 55-61, 90-97, 97-104, 104-110), none on the five other songs or the blind song; clips prepared |
| A3 | A verse fragment between two choruses on their chords is chorus | **Unexercised** | Its one design case (All Fired Up 124-128) does not meet the rule's precondition (chorus 128-132 holds no G: pair novelty 1.0), so the rule fired on no song; the rule stands as written |
| A4 | A merged section's strip comes from its longest member | **Held as built**, unverified by ear | Verse 1 `DUDUDUDU` certain from 33-49; Verse 2 `D-D-D-DU` certain from 61-90; Wet Leg Verse 4 `DUDUxxDU` from 65-100. The fragments' own 1.4 patterns differ (see All Fired Up); clips prepared |
| A5 | Phrase alignment behaves on the plan's spans as on grid spans | **Verified** | The only start that moved against 1.4 is All Fired Up's Verse 1, to 29 as predicted; the other shifted starts (Summer of '69 5, Chelsea Dagger 21, Wet Leg 6, Need You Tonight 49) are as in 1.4 |
| A9 | Seeded shuffles make runs reproducible | **Verified** | All Fired Up re-run from strums twice: `strums.json` and `score.json` byte-identical |
| A13 | The two riff features classify the ear-labelled sections as the ear did | **Measured again: 21 of 22**, with one departure from the recorded unlabelled list | The same known miss (All Fired Up 33-49). All Fired Up 49-55 is no longer marked because the stage reads the recall gate's onsets (0.806, 0.433), expected to regain its flag when the final fix wave moves the features to the detector's own onsets; Need You Tonight's Intro is unmarked as the research found, and is uncertain, so it is outside spec 8 as corrected ("its own certain pattern"). The blind song is marked on eight of ten sections, unverified |
| A14 | One bar is enough in the strip when no bar changes inside it | Unverified with a player | 31 one-bar strips beside the rows across the eight sheets; 18 sections keep two bars above |
| A15 | Players accept differing cell widths between sections | Unverified | Seen on every sheet with both kinds of strip (for example All Fired Up page 1: Verse 1 and Chorus 1 narrow, Verse 2 wide) |
| A16 | Cells as narrow as 18.8 mm hold every chord cell without wrapping | **Verified on eight sheets** | Every page of the eight sheets looked at: no cell wraps. Every two-chord cell sits in a section whose strip is above the rows or that has no strip; this holds nearly by construction, since under the built rule (two bars when a shown bar changes chord, `example_bars` choosing a later split bar as the second shown bar) a section with any struck bar that changes chord inside it keeps the two-bar strip above (see "What to improve next", item 2), so the narrow beside layout only ever holds one-chord cells |
| A18 | Two of three rules name the right tonic when the chord rules disagree | **Verified on Need You Tonight**, and held on the blind song | Need You Tonight: score C, pair F, mix F, header "F major (or C major)", the tonic the ear heard. Blind: all three D. The other six were re-run from strums, so their `chords.json` is 1.4's and their headers rest on the stored-decision probe |
| A21 | One extra legend line adds no page | **Verified** | Pour Some Sugar On Me prints the power line and stays at two pages |
| A23 | The blind song exercises the power-chord gates and the riff marker | **Half refuted** | The riff marker fired (eight of ten sections). The power gates did not: the key is major, so the first gate fails before any other |
| A8 | `FULL_VOTE_DENSITY` 0.6 separates real full votes from dense sprays | Measured, narrow, unchanged | The blind song's Verse 3 passes on density at 0.633; All Fired Up Verse 1 at 0.672 |
| A10 | The sixteenth floor at 0.53 flips nothing | **Verified** | No section on the three sixteenth-grid songs (Pour Some Sugar On Me, Fame, Need You Tonight) changed state |
| A22 | New defaulted fields keep 1.4 files loading | **Verified in use** | The six songs re-run from strums read 1.4 `chords.json` files without `pair_tonic` or votes and printed the 1.4 headers |

The rest (A1, A6, A7, A11, A12, A17, A19, A20) were not touched by these runs beyond what the table above says, and keep their spec 9 status.
