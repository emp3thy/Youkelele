# Version 1.4 validation on seven real songs and the non-coder path

Date: 2026-10-04. Branch `worktree-v1-4` at `b0d8ec4` plus this commit (version 0.5.0); three songs were re-run after the final fix wave, and the rows they change say so (see "Final fix wave" below). Checks every expectation in section 7 of `2026-10-04-ukulele-tab-chain-v1-4-design.md` against the kept version 1.3 runs and two songs the chain had never seen. Bar and section numbers are 0-based, as in `grid.json`; a range written `58-68` ends before bar 68 unless it says "printed bars", which are inclusive.

## Runs

The five version 1.3 run folders were the baseline. `02_grid` to `07_render` and `manifest.json` of each were copied aside with each folder's `evaluate` output. The run-folder scan of version 1.4 would have resolved the five known links to their id-named folders and re-run into them, so the five folders were then moved out of the runs folder to a sibling `runs_v13` (folder names `9f06qzcvuhg`, `sexhetcxqy4`, `0uib9y4ofps`, `lbc6ccztp5e`, `ypgq0qdgvza`), and the version was set to 0.5.0 before any run.

All seven then ran through the whole chain, one at a time: `uv run youkelele run "<url>" --runs-dir C:\Users\gethi\sources\Youkelele\runs`. Every run exited 0, and each landed in a folder named after the song with no flag or prompt. Every manifest records version 0.5.0 for all eight stages, `source`, `video_id` and `title_slug`, and harmony's `decoding: beats+downbeats`.

| Song | Folder | Audio download | Separate | Grid | Harmony | Strums | Arrange, score, render | Ingest done to render done |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Summer of '69 | `summer-of-69` | 3.17 MiB | 245.1 s | 16.8 s | 23.5 s | 5.5 s | 1.3 s | 292 s |
| Chelsea Dagger | `chelsea-dagger` | 3.47 MiB | 276.9 s | 18.6 s | 25.4 s | 6.1 s | 1.3 s | 328 s |
| Pour Some Sugar On Me | `pour-some-sugar-on-me` | 4.34 MiB | 348.0 s | 23.0 s | 32.7 s | 5.1 s | 1.4 s | 410 s |
| Wet Leg "mangetout" | `mangetout` | 3.29 MiB | 252.3 s | 18.4 s | 24.0 s | 5.8 s | 1.3 s | 302 s |
| David Bowie "Fame" | `fame` | 4.08 MiB | 306.1 s | 20.4 s | 27.1 s | 2.5 s | 1.3 s | 357 s |
| Pat Benatar "All Fired Up" | `all-fired-up` | 4.08 MiB | 321.8 s | 24.2 s | 30.8 s | 7.4 s | 1.3 s | 386 s |
| INXS "Need You Tonight" | `need-you-tonight` | 2.98 MiB | 222.3 s | 17.7 s | 23.4 s | 1.9 s | 0.9 s | 266 s |

Stage times are differences between the `finished_at` stamps in each `manifest.json`. The model weights were already in the shared caches, so these logs show only the song's audio being downloaded; the first-run model downloads were measured on the non-coder path below. Every ingest printed the usual harmless ffmpeg "Error parsing Opus packet header" line and nothing else went wrong. Separation took about twice as long as in the 1.3 validation (Chelsea Dagger 123.6 s then, 276.9 s now) with the same model and audio; the machine was in other use during the runs and nothing in the chain's separation changed, so this is recorded and not explained.

Each of the five was compared with its 1.3 folder through `compare_runs(runs_v13\<id>, runs\<name>)` from `youkelele.evaluate`, and a bar-by-bar comparison of `grid.json`, `chords.json` and `strums.json`. On all five the beats, bars and tempo are identical to 1.3, and so are the chord events' times and labels except for Pour Some Sugar On Me's six relabelled power chords. Every bar's detected onsets are identical on four songs; on Chelsea Dagger seven bars differ (14, 18, 19, 41, 105, 106, 107), all through the recall gate following the new section edges (bars 14, 18 and 19 are now in the unboosted intro and lost added strikes). `evaluate` was run on all seven, every page of every sheet was rasterised and looked at, and Pour Some Sugar On Me was also rendered in the full tier in a scratch copy to see the badge. I cannot listen to audio; what that leaves open is listed under "What cannot be verified".

## Summary

| Song | Folder | Key (method, margin) | Hedged | Sections and labels | Power chords | Pages 1.3 to 1.4 | Verdict |
|---|---|---|---|---|---|---|---|
| Summer of '69 | `summer-of-69` | D major (chords and stems, 0.052 by the pair rule over A; mode margin 0.300) | No | 12: Intro, Verse 1 to 5, Chorus 1 to 3, Bridge 58-68, Instrumental 68-75, Outro 111-121 | 0 | 3 to 3 | Better. Intro and bridge named as the spec asked; the solo is an instrumental; key unchanged and unhedged |
| Chelsea Dagger | `chelsea-dagger` | G major (0.096 by score over D; mode margin 0.299) | Yes, "(or D major)": the mix estimate says D, and the stems hear D as major | 7: Intro 0-20, Chorus 1 to 3, Verse 1 and 2, Instrumental 93-108 | 0 | 3 to 3 | Better. The tonic changes from D to G, hedged; no chorus over the 20-bar intro; the first chorus strip shows played bars |
| Pour Some Sugar On Me | `pour-some-sugar-on-me` | C# minor (0.146 by score over B; mode margin 0.430) | No | 8: Intro, Verse 1 to 3, Chorus 1 to 3, Instrumental 67-77 | 6 events relabelled, 39.5% of chord time | 2 to 2 | Better after the final fix wave. Key and riff cells right (Am at capo 4, sounding C# minor); the full tier now prints "Am is a power chord on the record"; the default easy sheet is unchanged and still shows no mark |
| Wet Leg "mangetout" | `mangetout` | C major (0.209 by score over F; mode margin 0.218) | No | 9: Verse 1 to 5, Chorus 1 to 3, Outro | 0 | 3 to 3 | As expected. The 35-bar "bridge" is Verse 5; the outro says no strummed instrument; still three pages |
| David Bowie "Fame" | `fame` | F major (1.067 by score, the only candidate; mode by the tonic's chords, margin 0.003) | No | 9: Intro 0-17, Verse 1 to 4, Instrumental 1 to 3, Chorus | 0 | 3 to 3 | Better. The header reads D major shapes at capo 3, sounding F major, matching a grid of D shapes; every label agrees with the vocal level |
| Pat Benatar "All Fired Up" (blind) | `all-fired-up` | G major (0.726 by score, the only candidate; mode margin 0.218) | No | 13: Intro 0-28, Verse 1 to 8, Chorus 1 to 3, Outro 132-156 | 0 (major key) | new, 4 | Mixed. Chain, folder, title, artist and key fine; verse and chorus names do not follow the chord content; four pages |
| INXS "Need You Tonight" (blind) | `need-you-tonight` | C major (0.327 by score over F; mode margin 0.097) | Yes, "(or F major)": the mix estimate says F, and the stems hear F as major | 7: Intro 0-13, Verse 1 to 3, Chorus 1 and 2, Outro | 0 (major key) | new, 2 | Mixed. Chain, folder and title fine; the artist prints "INXS" after the final fix wave (it printed "Inxs" before); the score rule says C, and the pair rule over every candidate is a tie broken by the chroma for F, which the hedge happens to name through the mix |

## Expectations from spec section 7

| Song | Expectation | Met? | Evidence |
|---|---|---|---|
| Summer of '69 | Key D major, not hedged | Yes | Header "Key D major"; `chords.json` key D major, method `chords_stems`, margin 0.052 by the pair rule (D/Bm 0.931 over A/F#m 0.879), because the scores were D 0.472, A 0.458; the mix estimate also says D, so no hedge |
| | `Intro` | Yes | Bars 0-4 (vocal share 0.25) print "Intro" where 1.3 printed "verse 2" |
| | `Bridge` for bars 58-68 | Yes | Grid section 58-68 is a verse with novelty 0.80 (the next highest on the song is 0.00) and vocal share 1.00; `refine_labels` makes it the bridge; printed bars 58-67 under "Bridge" (A, F, Bb, C) |
| | `Instrumental 68-75` for the solo | Yes | Vocal run (68, 75); section 68-75 vocal share 0.00; printed "Instrumental", bars 68-74 |
| | Outro boundary at 111 unchanged | Yes | Outro 111-121 in both runs; the trailing run (114, 118) is marked trailing and moves nothing |
| | Strum boxes unchanged from 1.3 | Yes for nine sections, no for three | Every bar's onsets are identical. The nine sections whose bar range is unchanged print the same pattern and state as 1.3. The three sections the vocal run re-cut differ: the bridge (58-68, one bar shorter than 1.3's 58-69) went from `D-DUD-DU` to `D-DU--D-` (still certain, confidence 0.479, covers 72%); the new Instrumental 68-75 prints `DUDUDUDU`; the verse 75-83 prints `DUDUDUD-` (1.3's 69-83 verse printed `DUDUDUDU`) |
| Chelsea Dagger | Key G major (or D major), hedged | Yes | Header "Key G major (or D major)". G 0.445 over D 0.349 by score (margin 0.096), mode major by 0.299; the hedge comes from the mix estimate (D major), not from the margin. The pair rule agrees (G by 0.059). Re-run from harmony after the final fix wave: the hedge now carries the mode the stems hear at D (`hedge_mode` major) rather than copying G's, and the text is the same "(or D major)"; chord events and the sheet are unchanged |
| | `Intro 0-20` | Yes | Grid intro 0-20, vocal share 0.00; it prints as "Intro" over printed bars 0-20, because phrase alignment starts the first chorus one bar later, at 21 |
| | No chorus before bar 20 | Yes | The first chorus starts at grid bar 20 (printed from 21); 1.3 printed a chorus from bar 9 |
| | `Instrumental 93-108` | Yes | Vocal run (93, 108); section 93-108 vocal share 0.00; printed "Instrumental", bars 93-107. 1.3 split this into a chorus and a bridge |
| | First-chorus strip starts on a struck bar | Yes | The strip shows bars 21 and 22 (G, G), both with detected strikes; 1.3 showed bars 9 and 10, before the guitar enters |
| Pour Some Sugar On Me | Key C# minor | Yes | Header "Key A minor (shapes)", "Sounding key: C# minor"; C# 0.439 over B 0.293 by score, mode minor by 0.430. 1.3 printed C# major |
| | Riff cells Am with the badge at capo 4 | Partly: Am yes, badge only in the full tier | The six `C#:maj` events (39.5% of chord time) are now `C#:5` with triad `C#:min` and print Am at capo 4 in every riff cell. The default easy tier prints plain Am, as spec section 4 says it should; in the full tier the 25 riff cells print Am with a raised 5 (seen in a scratch copy re-run from arrange with `--tier full`) |
| | The legend line | Yes in the full tier, after the final fix wave (it was **No** before) | Before: neither tier printed "Am is a power chord on the record", because one plain `C#:min` event (bar 65, 1.42 s, 0.6% of chord time) meant the Am diagram was not power-only and the score builder dropped the line when any use was plain. The rule is now that the line prints when any use is a power chord. Re-run from harmony into `pour-some-sugar-on-me`: the six relabelled events are the same, `score.json` marks the Am diagram as power, and the default easy sheet's HTML is identical to the one before the fix (no badge, no line, by design). A scratch copy under `%TEMP%\youkelele-fix\runs` re-run from arrange with `--tier full` (the tier is chosen at arrange, so a re-run from score would keep the easy arrangement) prints "Am is a power chord on the record" under the no-capo line, with the raised 5 in 25 riff cells, the same name as the badge; still two pages |
| | The no-capo line with five shapes (amended from six) | Yes | "Without a capo: C#m 1444, F# 3124, B 4322 (barre), E 1402, A 2100". The spec's first example had six shapes including C# major; the power relabel turns every C# major event into C# minor, so C# major no longer occurs and five is the right count |
| | `Instrumental 67-77` | Yes | Vocal run (67, 77); printed "Instrumental", bars 67-76 |
| | Capo stays 4 | Yes | "Capo fret 4"; `capo_margin` 0.80, capo scores 3.02, 2.66, 2.60, 4.18, 1.80, 4.58 for capo 0 to 5 |
| | Every section still uncertain | Yes | 8 of 8 sections uncertain, no strip printed; the patterns of the six sections whose ranges are unchanged are identical to 1.3 |
| Wet Leg "mangetout" | Key C major | Yes | C 0.588 over F 0.379 by score (margin 0.209); the pair rule ties C and F at 0.995 and the stem chroma breaks the tie for C |
| | The 35-bar bridge prints as a verse | Yes | Grid 65-100 is now `verse` (novelty 0.00) and prints as "Verse 5" |
| | Boundaries unchanged | Yes | All nine grid sections have the same bar ranges as 1.3; no vocal run inside the song (only the trailing (108, 113)) |
| | Outro "No strummed instrument detected" | Yes | The one printed outro bar (108) is N.C. with "No strummed instrument detected" in italics; 1.3 printed "Strum as in chorus (uncertain)" |
| David Bowie "Fame" | Header read against a grid that is D major in 83 of 101 bars | Yes | Header "Key D major (shapes)", "Capo fret 3", "Sounding key: F major". 84 of the 100 printed bars hold only a D shape (F sounding); 1.3 printed F minor |
| | Labels judged against the vocal levels | Yes | Vocal runs (0, 17), (29, 35), (47, 61), (81, 85) and the trailing (93, 101). Intro 0-17 and Instrumentals 29-35, 47-61 and 81-85 have vocal share 0.00; Verses 17-29, 35-47 and 71-81 1.00; Chorus 61-71 0.90; the last Verse 85-101 0.50 (it includes the trailing run). 1.3's "bridge" (71-82) is now a verse (novelty 0.00) |
| | Both tonic rules' results recorded | Yes | Score rule: F, the only candidate, 1.067 (F holds 0.884 of chord time plus the final-chord and section-end bonuses). Pair rule: F, the only candidate, 0.981. They agree. Mode margin 0.003, under 0.05, so the tonic's own chords decided: F major and F7 hold 216.2 s against F minor's 5.8 s |
| Pat Benatar "All Fired Up" (blind) | The chain completes | Yes | Exit 0, 386 s from ingest to render |
| | Folder `all-fired-up`, title "All Fired Up", artist "Pat Benatar" | Yes | Raw title "Pat Benatar - All Fired Up (Official Music Video)", uploader "Benatar Giraldo"; the wider prefix rule took "Pat Benatar" as the artist |
| | Tempo, key with margin | Recorded | Tempo 140 bpm (the log reads "150.0 bpm detected, octave none, 139.9 bpm"), 156 bars. Key G major by score, the only candidate at 0.726 (G holds 0.545 of chord time); mode major by 0.218; the mix estimate also says G major; not hedged. Every chord (G, Em, D, Am) is diatonic to G major |
| | Both tonic rules | Recorded | Score rule G (only candidate, 0.726); pair rule G (only candidate, 1.000). They agree |
| | Power-chord relabel | Did not fire | The key is major, so the first gate fails; G is major for 143.4 s and minor for none |
| | Sections and labels against the vocal levels | Recorded; verse and chorus names doubtful | Vocal runs (0, 28) and the trailing (132, 156). Intro 0-28 and Outro 132-156 have vocal share 0.00 and are named for it. In between, 11 sections of 4 to 29 bars: eight verses and three choruses, vocal shares 0.57 to 1.00. The same chord cycle (Em Em D D then G) appears under "Verse 2", "Chorus 1", "Verse 4", "Chorus 3" and the Outro, so the verse and chorus names do not follow the chord content |
| | Strum boxes | Recorded | Eighth-note grid, guitar stem (ratio 0.36), song grid fit 0.66. Nine sections certain with strips, four uncertain (Intro, Verse 5, Chorus 2, Verse 8). The recall gate fired on five sections (2, 3, 5, 11 and 12; section 3 went from 1.3 to 4.8 strikes per bar). Verses 6 and 7 print mostly muted strokes (`xxDxDxDx`, `Dxxxxxxx`). No box is mostly rests |
| | Filled and passing chords | Recorded | 0 filled, no passing chord; N.C. 1.2% of the time, 2 all-N bars |
| INXS "Need You Tonight" (blind) | The chain completes | Yes | Exit 0, 266 s from ingest to render |
| | Folder `need-you-tonight`, title "Need You Tonight", artist "INXS" | Yes, after the final fix wave (the artist was **no** before) | The first run printed "Inxs": the uploader is "INXS" and the title prefix "INXS - " matches it, but `clean_artist` title-cased any name given wholly in capitals (meant for "DEF LEPPARD"). Now only two or more words in capitals are title-cased. Re-run from ingest: the sheet prints "INXS" in its artist line and page title, and nothing else in the sheet changed |
| | Tempo, key with margin | Recorded | Tempo 109 bpm, 86 bars. Key C major by score, C 0.745 over F 0.418 (margin 0.327); mode major by only 0.097; hedged "(or F major)" because the mix estimate says F major. 0.908 of chord time is diatonic to C major at full credit; Eb (5.9%) is not |
| | Both tonic rules | Recorded; the pair rule is a tie | Score rule C (0.745 over 0.418). The pair shares tie (F/Dm 0.928 against C/Am 0.924, within `PAIR_TIE` 0.02), and the stem chroma breaks the tie for F; the manifest now records this as "tie, F by chroma" (it read "F by 0.003" before the final fix wave). Only the score rule decides, so this is not a disagreement between the rules; the printed hedge names F, but through the mix estimate, with the mode the stems hear at F (major) |
| | Power-chord relabel | Did not fire | Major key; C is major for 89.3 s and minor for 4.4 s |
| | Sections and labels | Recorded | Vocal run (0, 13) only. Intro 0-13 (vocal 0.00), Verse 13-24, Chorus 24-31, Verse 31-48, Chorus 48-56, Verse 56-79, Outro 79-86 (vocal share 1.00; named outro as the last segment, not for want of singing). The choruses alternate C and Eb/C; the verses alternate F and C |
| | No-chord filling, strum box, key margin (the points to watch) | Recorded | N.C. 11.1% of the time, 10 all-N bars (8 of them the first eight intro bars), 0 filled. Sixteenth grid, guitar stem (ratio 0.21), grid fit 0.64; five sections certain (confidence 0.615 to 0.815, covering 89 to 95%), Intro (covers 18%) and Outro (confidence 0.532) uncertain. Key margin as above: comfortable by score, a tie under the pair rule |
| All | Folders named after the songs | Yes | `summer-of-69`, `chelsea-dagger`, `pour-some-sugar-on-me`, `mangetout`, `fame`, `all-fired-up`, `need-you-tonight` |
| | No section shorter than four bars | Yes in the grid | Every grid section is four bars or longer on all seven (shortest: Fame 81-85, All Fired Up 124-128 and 128-132). Printed, Wet Leg's outro is one bar after the trailing drop, as in 1.3 |
| | Page counts no worse than 1.3 | Yes | 3, 3, 2, 3, 3 in both versions (Summer of '69, Chelsea Dagger, Pour Some Sugar On Me, Wet Leg, Fame). The no-capo line and hedges added no page |
| | `evaluate` prints the key method and margins and the vocal runs | Yes | For example "Key: G major (chords_stems, margin 0.096, mode margin 0.299, runner-up D, mix D major)" and "Vocal runs: (0, 20), (93, 108)". It printed each section's grid label, not the refined one (Summer of '69's bridge read "verse"); after the final fix wave it prints both where they differ (`verse -> bridge`) |
| | Nothing in a sheet contradicts the chord grid; the header key is diatonic to most of the grid | Yes | Share of chord time diatonic to the printed key, full credit only: 0.931, 0.941, 0.981 (the power chord counted at its written C# minor), 0.995, 0.961, 1.000, 0.908 |
| Non-coder path | `install.cmd` ends with "Ready" without git on PATH | Yes | See below |
| | `run-youkelele.cmd` with one validation link opens the sheet | Yes | See below |
| | The steps as the README lists them, nothing extra typed | Yes, with one difference in the security box | See below |

## Per song

### Summer of '69

**Pages.** Page 1: header (Key D major, Capo none, Tempo 139 bpm, the italics note), seven diagrams (D A Bm G F Bb C), Intro with its strip and the pickup cell, Verse 1, Chorus 1. Page 2: Verse 2, Chorus 2, Verse 3, Bridge (strip A then F; A F Bb C, Bb F Bb C, C D). Page 3: Instrumental (`DUDUDUDU`, D A A D), Verse 4, Chorus 3, Verse 5 and Outro (both uncertain); about four fifths of the page used.

**Quality.** The names now read like a chart: one intro, one bridge on the only section with new chords, and the solo as an instrumental. The key is the same D major as 1.3 but now decided by the pair rule at a margin of 0.052, just above the hedge threshold.

### Chelsea Dagger

**Pages.** Page 1: header with "Key G major (or D major)" and the song-level strum note, seven diagrams (C G D A Bm Em Am) and "Passing: B 4322", the Intro (uncertain, no strip; N.C., italic C, G and D cells), Chorus 1 with its strip, the start of Verse 1. Page 2: the rest of Verse 1, Chorus 2, Verse 2. Page 3: Instrumental (strip G, G), Chorus 3; about three fifths used.

**Quality.** The 20 bars before the singing are one intro, so no chorus is printed over bars where nobody sings, and the 15-bar instrumental is no longer split into a chorus and a bridge. The tonic changed from D to G: G holds 38% of chord time against D's 31%, and the stems prefer major at G by 0.299; the hedge keeps D in view because the mix estimate still says D.

### Pour Some Sugar On Me

**Pages.** Page 1: header ("Key A minor (shapes)", capo 4, "Sounding key: C# minor", four notes), diagrams Am G C F, "Passing: D 2220", the no-capo line, Intro, Verse 1, Chorus 1, all uncertain with no strip. Page 2: Verse 2, Chorus 2, Instrumental, Verse 3, Chorus 3; about three quarters used.

**Quality.** The riff cells that printed A (major) at capo 4 in 1.3 print Am, and the header says minor; the strip-less, uncertain sections are as before. The power chord is invisible on the default sheet: the easy tier prints no badge and no legend line by design. In the first run the legend line was also dropped in the full tier by one short real C# minor in bar 65; after the final fix wave the full tier prints "Am is a power chord on the record". The no-capo line is correct for the chords the sheet prints, with five shapes.

### Wet Leg "mangetout"

**Pages.** Page 1: header (Key C major), C F Dm diagrams, "Passing: C# 1114", Verse 1, Chorus 1, Verse 2. Page 2: Chorus 2, Verse 3, Verse 4, Verse 5. Page 3: Chorus 3 and the Outro, about a third used.

**Quality.** "verse 2" and "bridge" are gone; five verses and three choruses, numbered in order. The outro is honest again. Still three pages: the last chorus and a one-bar outro sit on page 3, as in 1.3.

### David Bowie "Fame"

**Pages.** Page 1: header (D major shapes, capo 3, sounding F major), Dm G D diagrams, "Passing: Am 2000", "Without a capo: Fm 1013, Cm 0333, Bb 3211 (barre), F 2010", Intro (now certain, 16-slot strip with the Dm to Am change), Verse 1, Instrumental 1. Page 2: Verse 2, Instrumental 2, Chorus, Verse 3. Page 3: Instrumental 3, Verse 4; about two fifths used.

**Quality.** The header finally agrees with the grid: D shapes at capo 3 sound F, and the key says F major. The long instrumental intro is one section and is certain now (1.3's five-bar intro was uncertain); the vocal breaks are named instrumentals. The no-capo line lists F last because it follows first occurrence, and the song starts on the Fm cell.

### Pat Benatar "All Fired Up"

**Pages.** Page 1: header (G major, 140 bpm), Am G Em D diagrams, Intro (uncertain; a pickup Am cell, twelve bars of Am, eight of G, then Em Em D D, G G G), Verse 1, Verse 2. Page 2: Chorus 1, Verse 3, Verse 4, Verse 5 (uncertain). Page 3: Verse 6, Verse 7, Chorus 2 (uncertain), Verse 8 (uncertain), Chorus 3. Page 4: the Outro (strip `D-D-D-D-`, three rows), about a quarter used.

**Quality.** The new title rule and folder naming work on an uploader who is not the artist. The key is unambiguous on every measure. The structure is the weak part: 13 sections, eight of them verses of 4 to 29 bars, with the chorus label on three short sections that carry the same chord cycle as the verses around them. The 28-bar intro (45 s) and 24-bar outro (39 s) have no singing; whether they are the record's own or the video's is a listening question. Four pages.

### INXS "Need You Tonight"

**Pages.** Page 1: header ("INXS" since the final fix wave, "Inxs" before; "Key C major (or F major)", 109 bpm), C Eb F Cm diagrams, "Passing: Gm 0231", Intro (uncertain; eight N.C. bars, then C and Eb/C), Verse 1, Chorus 1. Page 2: Verse 2 (ending Cm Cm), Chorus 2, Verse 3, Outro (uncertain); about four fifths used.

**Quality.** Two pages, readable, with a strip per sung section. The artist was mis-cased in the first run and is right since the final fix wave. The key is the open question: C by chord time, a tie under the diatonic-pair rule that the chroma breaks for F, F by the mix. A riff song with sparse chords gives the strum stage a pattern with high confidence on a sixteenth grid; whether a strummed part exists to match it cannot be measured here.

## The non-coder path

Done on this machine (Windows 11 Home 10.0.26200) on 2026-10-04. The branch is not pushed, so the ZIP was made the way GitHub serves a branch as closely as possible: `git archive --format=zip --prefix=Youkelele-worktree-v1-4/ HEAD` (1,277,827 bytes; `.gitattributes` makes the archive carry CRLF in `install.cmd` and `run-youkelele.cmd`, as GitHub's would). It was given the internet zone mark (`Zone.Identifier`, `ZoneId=3`, a GitHub `HostUrl`) and unpacked with Explorer's own copy engine (`Shell.Application` `CopyHere`) into `%TEMP%\youkelele-task9\nc`, outside the repository. The download caches were pointed at empty folders for both scripts (`UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, `PLAYWRIGHT_BROWSERS_PATH`, `YOUKELELE_CACHE`, `TORCH_HOME`) so the downloads could be measured, and every Git folder was removed from PATH (`git` not found in that shell). `uv` was left installed in `%USERPROFILE%\.local\bin`.

Steps as a non-coder takes them, and what appeared:

1. **Extract.** Extracting gave one folder `Youkelele-worktree-v1-4` holding the repository. All 183 extracted files carry the `Zone.Identifier` stream with `ZoneId=3`, `install.cmd` and `run-youkelele.cmd` included, so Windows treats them as downloaded.
2. **Double-click `install.cmd`.** Opened through the shell as a double-click does (`Start-Process`, which uses ShellExecute), Windows showed the "Open File - Security Warning" box: "The publisher could not be verified. Are you sure you want to run this software?", Name `install.cmd`, Publisher "Unknown Publisher", Type "Windows Command Script", with **Run** and **Cancel**. Not the blue "Windows protected your PC" box. I cannot press Run on someone's behalf, so I cancelled it and started the same file through `cmd /c start "" /wait install.cmd`, which opens the same new console window but does not apply the zone check (the mark was still present). The README already tells the reader to choose **Run** in this box, but as the second case; it now comes first.
3. **Install.** A new window ran the four steps: "[1/4] Installing uv: already present", then `uv sync` (the package downloads listed one by one), the chord model zip and ffmpeg, and Playwright's Chromium and headless shell. Playwright's progress bars print as runs of garbled characters (`ÔûáÔûá...`) in this window, though the percentages and "downloaded to" lines read normally. (Fixed in the final fix wave: `install.cmd` sets the UTF-8 code page and `install.ps1` reads the tools' output as UTF-8, so the bars print as rows of small squares; uv runs without its progress bars.) It ended with "Ready. Double-click run-youkelele.cmd to make a sheet." and "Press any key to continue . . .". 113 s from start to finish, with git not on PATH; `setup` fetched the chord model as a zip (the model folder has its `COMMIT` file).
4. **Double-click `run-youkelele.cmd`, paste the link, press Enter.** The link `https://www.youtube.com/watch?v=w-rv2BQa2OU` was given at the script's "Paste a YouTube link and press Enter:" prompt (piped into the prompt, which is what a paste and Enter give). It printed "Making the sheet. The first song takes longer while the models download.", downloaded the separation weights (55.0 MB) and the Beat This! checkpoint (77.3 MiB as its progress bar shows, 81.1 MB on disk), ran the eight stages, printed "The sheet is ready:" with the path `...\Youkelele-worktree-v1-4\runs\need-you-tonight\07_render\sheet.pdf`, and opened it: Edge, the default PDF viewer here, recorded opening that file in the same second the script finished. Exit 0 after 506 s. The sheet matches the main `need-you-tonight` run (same key, sections and log lines).

**Downloads measured (A10).** The network adapter received 818 MB (779.8 MiB) during the 113 s install, machine-wide, so slightly over-counted by anything else using the connection. That covers the Python packages, the chord model zip, ffmpeg and Chromium; it does not include uv or Python 3.12, because uv was already installed and, despite the empty install folder, reused the Python 3.12 it had installed before. The first song then fetched 136.1 MB of models (55.0 MB plus 81.1 MB, by file size) plus its audio (2.98 MiB); the adapter counted 197 MB over the 506 s run, with other traffic. On disk after install and one song: `.venv` 1.5 GB, Chromium about 707 MB, models about 161 MB, the song's run folder about 224 MB (the seven validation folders hold 224 to 349 MB each, mostly separated stems).

**One more finding.** Before the run above, the link was first given as a command-line argument (`start ... run-youkelele.cmd "https://www.youtube.com/watch?v=w-rv2BQa2OU"`, the way a dropped file arrives). `cmd` split the argument at the `=`, so the script received `https://www.youtube.com/watch?v`; `youkelele run` accepted it, the metadata fetch resolved it to YouTube's "recommended" feed, a run folder `runs\recommended` was created and ingest was still going when the run was interrupted after 88 s (a Ctrl+C reached the window; I did not send it). The documented path, pasting at the prompt, is not affected; dropping an audio file whose name holds `=` would be. Fixed in the final fix wave, see below.

## What cannot be verified without listening

- Whether the keys of the blind songs are right: All Fired Up's G major, and Need You Tonight's C major against the F major that the mix prefers and that the chroma picks when the pair rule ties.
- Whether Need You Tonight's intro has a chord in its first eight bars, which print N.C. and were not filled, and whether either blind song's chord names (All Fired Up's Am, G, Em, D; Need You Tonight's C, F, Eb, Cm, Gm) are what is played.
- Section names on the blind songs: which of All Fired Up's eleven inner sections are verses and which choruses; whether its 28-bar intro and 24-bar outro belong to the record or to the video; whether Need You Tonight's last seven bars are an outro.
- Every strum pattern on the blind songs, in particular All Fired Up's muted-stroke Verses 6 and 7 and Need You Tonight's certain sixteenth-grid patterns on a riff song; and the tempos (140 and 109 bpm).
- Whether Pour Some Sugar On Me's riff is a power chord rather than a minor triad (the relabel rests on the research's chord-quality evidence, not on these files), and whether bar 65's C# minor is real.
- The patterns of the re-cut sections on the known songs: Summer of '69's bridge (`D-DU--D-`), instrumental and following verse; Chelsea Dagger's first chorus (from bar 20) and instrumental; Fame's intro, instrumentals and verses.
- As in 1.3: true key mode where the stems tie (Fame by 0.003), and section names generally.

## What to improve next

Ranked by benefit to the person reading the sheet.

1. **Name verse and chorus by chord content as well as by sound.** Stage: grid labels or score. Evidence: All Fired Up prints eight verses and three choruses, and the same Em Em D D G cycle sits under both names in five sections; 13 sections make it four pages. Sections whose chord sequences match could share a label (and merge when adjacent), with the chorus chosen by repetition and vocal level. Wet Leg and Fame show that the vocal-based intro, instrumental and outro names work; the verse and chorus split is what is left.
2. **Show the power chord on the default sheet.** Stage: score and render. Evidence: Pour Some Sugar On Me's riff (39.5% of chord time) prints plain Am in the easy tier. The full tier's legend line was dropped by one 1.42 s C# minor in bar 65; since the final fix wave it prints when any use is a power chord. What is left: consider printing the line in the easy tier too, so the reader knows the record plays root and fifth.
3. Done in the final fix wave: **keep acronym artists in capitals.** One word in capitals stays as written (INXS, ABBA, AC/DC); two or more are title-cased (PAT BENATAR to Pat Benatar).
4. Done in the final fix wave: **refuse a link without a video, and pass dropped arguments whole.** Preflight refuses a YouTube watch link without an 11-character id before any folder is named, and `run-youkelele.cmd` reads the whole argument line when the first argument is not an existing file.
5. **Decide close tonic calls with both rules in view.** Stage: harmony. Evidence: Need You Tonight's score rule says C by 0.327 while the pair rule over every candidate is a tie (F/Dm 0.928, C/Am 0.924) that the chroma breaks for F; the hedge names F only because the mix estimate does. When the score is clear but the pair rule ties, the hedge could name the pair rule's chroma winner by rule rather than by coincidence.
6. Done in the final fix wave: **clean the install window's progress bars.** The window now reads the tools' output as UTF-8, so Playwright's bars print as rows of small squares, and uv draws none.
7. **Carried from 1.3**, unchanged: a chance-corrected strum confidence (Pour Some Sugar On Me's sections stay uncertain only by threshold), winning back the page (Wet Leg and Fame keep a third page with little on it), and recovering sustained strums on sixteenth grids.

Not ranked as faults: the no-capo line's five shapes on Pour Some Sugar On Me (the spec's sixth, C# major, no longer occurs once the riff is relabelled); Fame's no-capo line ordering by first occurrence.

## Final fix wave

After the whole-branch review, one wave of fixes landed and three songs were re-run with it. The other four run folders were not touched, and `runs_v13` was only read.

| Fix | What changed | Seen on the re-runs |
|---|---|---|
| The hedge carries its own mode | The other tonic the hedge names (the runner-up when the margin is close, else the mix estimate's tonic) gets its own mode from the stems at that tonic, stored as `Key.hedge_mode`; before, it copied the key's mode, so an A minor song with C as runner-up would have read "A minor (or C minor)" | Chelsea Dagger re-run from harmony: `hedge_mode` major, "(or D major)" as before. Need You Tonight re-run from ingest: `hedge_mode` major, "(or F major)" as before. Neither printed text changed, because both songs and both other tonics are major |
| Only the plain major relabels as a power chord | `X:7`, `X:maj7`, slash chords and added degrees are left alone | Pour Some Sugar On Me re-run from harmony: the same six `C#:maj` events become `C#:5`; every chord event is identical to the first run |
| The legend line prints when any use is a power chord | One plain minor no longer drops it; one line per name | Pour Some Sugar On Me: `score.json` marks Am as power; the default easy sheet is byte-identical to the first run's HTML; the full tier (scratch copy, re-run from arrange with `--tier full`) prints "Am is a power chord on the record", two pages |
| One word in capitals stays as written | INXS, ABBA, AC/DC; two or more words are still title-cased | Need You Tonight prints "INXS"; nothing else in its sheet changed |
| A pair-rule tie is recorded as a tie | The manifest note reads "tie, F by chroma" when the pair shares are within `PAIR_TIE` | Need You Tonight: "tie, F by chroma" (was "F by 0.003"); Chelsea Dagger "G by 0.059" and Pour Some Sugar On Me "C# by 0.140" are clear wins and read as before |
| The link reaches the CLI whole | `run-youkelele.cmd` reads the whole argument line when the first argument is not an existing file | `run-youkelele.cmd https://www.youtube.com/watch?v=zzzzzzzzzzz`, unquoted, reached the CLI whole and failed as a download error for that id ("This video is unavailable"), not as `watch?v`; the quoted form and a quoted Mix link holding `&` did the same; a dropped file whose name holds `=` and one whose path holds spaces both reached ingest whole |
| A cut link is a preflight problem | A YouTube watch link without an 11-character `v=` id, or `watch?v...` alone, is refused before any folder is named | `run-youkelele.cmd "https://www.youtube.com/watch?v"` printed "YouTube link has no 11-character video id" with the fix "paste the whole link, for example https://www.youtube.com/watch?v=dQw4w9WgXcQ", and no runs folder was created |
| One video, not its playlist | yt-dlp runs with `noplaylist` | The details of `https://www.youtube.com/watch?v=w-rv2BQa2OU&list=RDw-rv2BQa2OU&start_radio=1` read as the one video ("INXS - Need You Tonight (Official Video)"), not the Mix |
| Install window | UTF-8 code page and output, no uv progress bars | Watched during a Chromium download into an empty folder: the progress bars print as rows of small squares, not `Ôûá`; Playwright's download hit CDN timeouts and resets on this connection and retried them itself. A headless run of `install.ps1` afterwards printed the four steps and "Ready" |
| `run-youkelele.cmd` without uv | Says "uv was not found. Run install.cmd first." and pauses | Seen with uv off PATH and no `%USERPROFILE%\.local\bin\uv.exe` |
