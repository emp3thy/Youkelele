# Version 1.3 validation on five real songs

Date: 2026-10-04. Branch `worktree-v1-3` at `9b8aa67` plus this commit (version 0.4.0), updated after the whole-branch review's fix wave (the sixteenth-grid uncertainty threshold, the inherited-section label and the harness trimming the last section as the strums stage does). Checks every expectation in section 7 of `2026-10-04-ukulele-tab-chain-v1-3-design.md` against the kept version 1.2 runs, using the new truth-free `evaluate` and its compare. Bar and section numbers are 0-based, as in `grid.json`.

## Runs

The five version 1.2 run folders were the baseline. Summer of '69's harmony stage had been re-run with version 1.3 code during implementation, so it was first restored with the main checkout's version 1.2 code (`youkelele run <url> --from harmony`, version 0.3.0): its `strums.json` then had no `explained` field and its sheet was three pages, as in the version 1.2 validation. Then `02_grid`, `03_harmony`, `04_strums`, `05_arrange`, `06_score`, `07_render` and `manifest.json` of each folder were copied aside, with each folder's `evaluate` output.

All five then ran through the whole chain from their URLs: `uv run youkelele run "<url>" --debug --runs-dir C:\Users\gethi\sources\Youkelele\runs`. Re-downloading re-ran every stage; every manifest records version 0.4.0 for all eight stages, `debug: true`, and harmony's `decoding: beats+downbeats`.

| Song | Slug | Exit | Separate | Grid | Harmony | Strums | Arrange, score, render | Ingest done to render done |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Chelsea Dagger | `sexhetcxqy4` | 0 | 123.6 s | 8.2 s | 13.4 s | 2.9 s | 0.9 s | 149 s |
| Summer of '69 | `9f06qzcvuhg` | 0 | 105.1 s | 7.1 s | 12.4 s | 2.6 s | 0.9 s | 128 s |
| Pour Some Sugar On Me | `0uib9y4ofps` | 0 | 170.4 s | 10.8 s | 17.1 s | 3.6 s | 0.9 s | 203 s |
| Wet Leg "mangetout" | `lbc6ccztp5e` | 0 | 127.5 s | 8.6 s | 13.3 s | 2.7 s | 0.9 s | 153 s |
| David Bowie "Fame" | `ypgq0qdgvza` | 0 | 154.8 s | 9.9 s | 15.0 s | 2.9 s | 0.9 s | 184 s |

Stage times are differences between the `finished_at` stamps in each `manifest.json`. Every ingest printed the usual harmless ffmpeg "Error parsing Opus packet header" line. Wet Leg's download also printed "unable to download video data: HTTP Error 403: Forbidden" before downloading in full; its audio hash matches version 1.2, as do the other four.

The audio of all five is byte-identical to version 1.2. For four songs every stem the manifests record is identical too; Wet Leg's five stems hash differently, the same 16-bit rounding difference the version 1.2 validation saw on Chelsea Dagger, and it changed nothing measurable: Wet Leg's beats, bars, sections and every bar's detected onsets match version 1.2 exactly. On all five, beats, downbeats, bars, tempo and sections are identical to version 1.2, so every difference below comes from the harmony, strums, score and render changes.

After the review's fix wave, all five ran again from the strums stage (`uv run youkelele run "<url>" --from strums --runs-dir C:\Users\gethi\sources\Youkelele\runs`; strums, arrange, score and render, a few seconds each). Against the first validation run, every bar's onsets and every pattern's slots, confidence and `explained` are unchanged on all five songs, and so are the page counts. What changed: Pour Some Sugar On Me's intro, first chorus and second verse became uncertain and lost their strips, and Wet Leg's outro label became "Strum as in chorus (uncertain)". No covers percentage changed. The figures below are from these runs.

Each song was compared with `compare_runs(baseline copy, new run)` from `youkelele.evaluate` (the CLI's `evaluate --compare` takes two slugs in one runs folder; deltas are new minus old), and its new `evaluate` output saved. Every page of every sheet was rasterised and looked at. I cannot listen to audio; what that leaves open is listed under "What cannot be verified".

## Summary

| Song | Pages 1.2 / 1.3 | Boxes mostly rests 1.2 / 1.3 | Changes on a bar start 1.2 / 1.3 | Recall-boosted sections | Trailing bars dropped | Verdict |
|---|---|---|---|---|---|---|
| Summer of '69 | 3 / 3 | 1 / 0 | 75 of 78 (96.2%) / 78 of 78 (100%) | 4 and 8, the second and third choruses (2.9 to 5.2 and 1.8 to 4.6 strikes per bar) | 1 (bar 120) | Better. Both sparse choruses print `D-DUDUD-` with certainty; every chord change is on a bar line; nine sections get a worked example. Still three pages |
| Chelsea Dagger | 3 / 3 | 3 / 0 | 59 of 69 (85.5%) / 60 of 69 (87.0%) | 1 and 7, the first and last choruses (2.8 to 4.3 and 2.6 to 5.0) | 0 | Better. No chorus box is mostly rests; nothing added before the guitar enters. Still three pages |
| Pour Some Sugar On Me | 2 / 2 | 0 / 0 | 55 of 89 (61.8%) / 56 of 81 (69.1%) | none | 0 | As expected for the strums: every section uncertain, no strip, as version 1.2 printed no box. The sixteenth-grid threshold of 0.55 holds the three sections the new vote lifted to 0.453 to 0.472. Chords cleaner; sub-beat events 5 to 1, and the one left is a measurement artefact |
| Wet Leg "mangetout" | 3 / 3 | 0 / 0 | 61 of 66 (92.4%) / 62 of 63 (98.4%) | none | 4 (bars 109 to 112) | Mixed. Onsets identical, trailing noise gone, but still three pages and three patterns changed (two denser, the outro now inherited); the one-bar outro reads "Strum as in chorus (uncertain)" over an N.C. cell |
| David Bowie "Fame" | 2 / 3 | 0 / 0 | 6 of 14 (42.9%) / 8 of 14 (57.1%) | none | 1 (bar 100) | Mixed. Half-bar changes show at their strokes; onsets identical; six patterns gained strokes, five of them printed (the intro gained strokes too but stays uncertain); grew to three pages |

Order of the spec's `boxes_mostly_rests` line (Summer of '69, Chelsea Dagger, Pour Some Sugar On Me, Wet Leg, Fame): 1, 3, 0, 0, 0 on the version 1.2 runs as the harness measures them, and 0, 0, 0, 0, 0 now. The spec's 4, 4, 4, 1, 0 were counted on version 1.1 runs.

## Expectations from spec section 7

| Song | Expectation | Met? | Evidence |
|---|---|---|---|
| Summer of '69 | Both chorus boxes dense (`S-SSSSS-` or denser) and certain | Yes | Sections 4 (bars 41 to 52) and 8 (bars 83 to 94) print `D-DUDUD-`, which strikes exactly the `S-SSSSS-` slots; certain, confidence 0.78 and 0.70, `explained` 95.2% and 96.4%, `recall_boost` true. Version 1.2 printed `D-------` for both (section 4 uncertain, section 8 certain) |
| | Verse 1 unchanged | Yes for onsets, no for the printed pattern | Section 1 (bars 4 to 18): every bar's struck slots are identical to version 1.2 and strikes per bar stay 6.1. One slot in bar 8 is now a strike rather than a mute, because the mute medians are computed on the final onset list, which includes the choruses' added onsets. The new vote adds a muted stroke on beat 3: `xxxU-xxx` became `xxxUxxxx`, `explained` 92.4% to 100% |
| | Chord changes on bar starts 75 of 75 | Yes | The harness counts every label change, including those into and out of N: 75 of 78 to 78 of 78 (100%). Label set unchanged; 82 events to 81 (one N event fewer) |
| | Tempo header still 139 | Yes | "Tempo 139 bpm"; `bpm` 138.555 in both runs |
| Chelsea Dagger | Chorus boxes no longer mostly rests | Yes | Choruses 1, 3, 5, 7 rest shares 75.0, 62.5, 37.5, 75.0% became 37.5, 50.0, 25.0, 12.5%; the bridge 75.0% to 37.5%. `boxes_mostly_rests` 3 to 0 |
| | No added onsets in the silent bars before the guitar enters | Yes | Bars 9 to 11 (the chorus's first three bars) have no onsets in either run; bars 9 to 12 are identical and bar 13 changed one strike to a mute (`D-xxD-x-` to `D-xxx-x-`, the same onsets); the first onset the gate added (`+` in `onsets.txt`) is in bar 14 |
| | On-bar changes rise from 54 of 68 | Yes, by one change | The harness counts 59 of 69 on the version 1.2 run (the spec's 54 of 68 was measured another way) and 60 of 69 now (85.5% to 87.0%) |
| Pour Some Sugar On Me | Sub-beat events gone | No, by the count; yes in substance | 5 to 1. The one left is an E (prints as C under the capo) at 243.18 s in bar 86, 0.70 s long against a median beat of 0.70 s. It is a measurement artefact, not a sliver: the event is one beat long, and floating-point rounding puts its length (0.69999999999999 s) a hair under the median beat (0.70000000000000 s), which `sub_beat_events` counts as shorter |
| | The recall gate does not fire on its choruses | Yes | No section has `recall_boost`; every bar's onsets are identical to version 1.2 and `onsets.txt` holds no `+` (the song runs 16 slots per bar, so the gate is off) |
| | Every section stays uncertain as today | Yes | All seven sections are uncertain and the sheet prints no strip. The onsets are unchanged, but the third-share vote and density floor lifted sections 0 (intro), 2 (first chorus) and 3 (second verse) to `DUDUDUDUDUD-D-DU`, `D--UD-D-D-D-DU-U` and `DU--DxDU-UDUDU-U`, confidence 0.467, 0.453 and 0.472, `explained` 94.1%, 81.2% and 87.4%. In the first validation run these cleared the single threshold of 0.45 and printed three strips. The owner then set a sixteenth-grid threshold of 0.55 (spec 4.2; Fame's certain sections start at 0.625), which holds all three uncertain. It is a threshold, not a test that tells one guitar from two (see "What to improve next", item 1) |
| | Capo 4 kept | Yes | "Capo fret 4", "Key A major (shapes)", "Sounding key: C# major" |
| Wet Leg "mangetout" | Onsets and patterns identical to version 1.2 | Yes for onsets, no for patterns | Every bar's onsets identical; no section boosted. Six of nine patterns identical. The verse (section 2) `D-D---DU` uncertain became `D-D-D-DU` certain and now prints a strip; "verse 2" (section 5) `D-D--UDU` became `D-DU-UDU`; the outro, cut to one bar, is no longer "No strummed instrument detected" but inherits the last chorus's pattern as uncertain and prints "Strum as in chorus (uncertain)" |
| | Trailing bars dropped | Yes | `trailing_bars_dropped` 4: bars 109 to 112. Bar 108 is all N too but stays, because the rule never empties the last section (the outro is bars 108 to 112) |
| | Two pages | **No** | Three. Page 3 holds the last chorus (strip and two rows) and the outro's single N.C. cell |
| David Bowie "Fame" | Onsets and patterns identical to version 1.2 | Yes for onsets, no for patterns | Every bar's onsets identical; no section boosted. Sections 2 and 7 identical; six patterns gained strokes, five of them printed: sections 1, 3, 4, 5 and 6 gained one to three strokes (rests 37.5, 43.8, 50.0, 50.0, 37.5% became 31.2, 31.2, 43.8, 31.2, 18.8%), and the intro, which stays uncertain and prints no strip, went from all rests to `D-D-D---D-----D-` (rests 100.0% to 68.8%) |
| | Bar 100 dropped | Yes | `trailing_bars_dropped` 1; the last verse has 18 bars instead of 19 and its closing N.C. cell is gone |
| | The chain completes | Yes | Exit 0, 184 s |
| All | `boxes_mostly_rests` falls to at most 0, 1, 2, 0, 0 | Yes | 1, 3, 0, 0, 0 to 0, 0, 0, 0, 0 |
| | `evaluate <run>` works with no truth | Yes | On all five 1.3 runs and all five 1.2 folders |
| | `evaluate --compare` of a run with itself gives identity | Yes | overseg, underseg, seg and majmin 1.000 and every section difference zero, for each 1.2 copy and each 1.3 run through the API, and for Fame through the CLI |
| | Chord label sets unchanged except removed slivers | Yes | Every song's label set is identical to version 1.2. Events: 82 to 81, 76 to 76, 106 to 94, 71 to 68, 16 to 15 (Summer of '69, Chelsea Dagger, Pour Some Sugar On Me, Wet Leg, Fame). Chelsea's counts moved within the set: one B minor event became B major |
| | No section gets sparser | Yes | Across all 43 sections strikes per bar never fall and the printed rest share never rises; every 1.3 pattern strikes at least as many slots as its 1.2 pattern |
| | Every section with a certain pattern shows the strip and no uncertain section does | Yes | Strips per sheet equal certain sections: 9, 7, 0, 8, 7 (Summer of '69, Chelsea Dagger, Pour Some Sugar On Me, Wet Leg, Fame); every uncertain section shows only its label line. No sheet says "repeatable" |
| | On Fame's verses the strip shows the second chord at its stroke | Yes | "verse 2" (bars 53 to 60): bar 1 of the strip is Dm with Am under beat 4, bar 2 is Am with G under beat 3, each on a down stroke. The bridge's strip shows D with G under beat 3 the same way |

## Per-section strums

From the compare (A version 1.2, B version 1.3). Strikes are per bar; "explained" is the share of the section's detected strikes on a slot the pattern strikes; "unc" uncertain, "boost" recall gate kept.

### Summer of '69

| Section | Bars | 1.2 pattern | 1.3 pattern | Strikes per bar | Explained | Rests | State 1.2 / 1.3 |
|---|---|---|---|---|---|---|---|
| 0 verse 2 | 0-3 | `D-xx-xxx` | `D-xx-xxx` | 5.0 / 5.0 | 90.0% / 90.0% | 25.0% / 25.0% | certain / certain |
| 1 verse | 4-18 | `xxxU-xxx` | `xxxUxxxx` | 6.1 / 6.1 | 92.4% / 100.0% | 12.5% / 0.0% | certain / certain |
| 2 chorus | 19-30 | `D-DU--D-` | `D-DU-UD-` | 3.9 / 3.9 | 76.6% / 87.2% | 50.0% / 37.5% | certain / certain |
| 3 verse | 31-40 | `D-DU--D-` | `DUDUD-D-` | 4.4 / 4.4 | 70.5% / 93.2% | 50.0% / 25.0% | certain / certain |
| 4 chorus | 41-52 | `D-------` | `D-DUDUD-` | 2.9 / 5.2 | 31.4% / 95.2% | 87.5% / 25.0% | unc / certain, boost |
| 5 verse | 53-57 | `DU-U-UD-` | `DU-UDUDU` | 5.2 / 5.2 | 80.8% / 96.2% | 37.5% / 12.5% | certain / certain |
| 6 verse 2 | 58-68 | `D--U----` | `D-DUD-DU` | 3.5 / 3.5 | 41.0% / 87.2% | 75.0% / 25.0% | unc / certain |
| 7 verse | 69-82 | `D--UDUD-` | `DUDUDUDU` | 5.2 / 5.2 | 74.0% / 100.0% | 37.5% / 0.0% | certain / certain |
| 8 chorus | 83-94 | `D-------` | `D-DUDUD-` | 1.8 / 4.6 | 45.5% / 96.4% | 87.5% / 25.0% | certain / certain, boost |
| 9 verse | 95-110 | `D--UD---` | `D--UD-D-` | 3.3 / 3.3 | 56.6% / 67.9% | 62.5% / 50.0% | unc / unc |
| 10 outro | 111-120 | `D-------` | `x---D---` | 2.4 / 2.4 | 22.7% / 40.9% | 87.5% / 75.0% | unc / unc |

Chord comparison: overseg 0.996, underseg 0.994, majmin 0.994. Song grid fit 0.908 in both runs. The outro's figures leave out bar 120, the trailing bar the strums stage ignores; the harness now trims the last section in both runs as the stage does (before the review's fix wave it counted bar 120 and printed 2.6, 23.1% and 42.3%, which disagreed with the stage's own `explained` of 40.9%).

### Chelsea Dagger

| Section | Bars | 1.2 pattern | 1.3 pattern | Strikes per bar | Explained | Rests | State 1.2 / 1.3 |
|---|---|---|---|---|---|---|---|
| 0 verse | 0-8 | `--------` | `D-------` | 2.0 / 2.0 | 0.0% / 16.7% | 100.0% / 87.5% | unc / unc |
| 1 chorus | 9-37 | `--D---D-` | `D-D-D-DU` | 2.8 / 4.3 | 53.8% / 88.0% | 75.0% / 37.5% | certain / certain, boost |
| 2 verse | 38-60 | `D-D-D-D-` | `D-DUDUDU` | 3.9 / 3.9 | 68.9% / 97.8% | 50.0% / 12.5% | certain / certain |
| 3 chorus | 61-70 | `D-D---D-` | `D-D-D-D-` | 3.2 / 3.2 | 71.9% / 84.4% | 62.5% / 50.0% | certain / certain |
| 4 verse | 71-92 | `D-D-D-D-` | `D-D-D-D-` | 3.7 / 3.7 | 75.3% / 75.3% | 50.0% / 50.0% | certain / certain |
| 5 chorus | 93-98 | `D-DU--DU` | `D-DUD-DU` | 5.0 / 5.0 | 83.3% / 93.3% | 37.5% / 25.0% | certain / certain |
| 6 bridge | 99-104 | `--D---D-` | `--DUD-DU` | 3.8 / 3.8 | 47.8% / 87.0% | 75.0% / 37.5% | certain / certain |
| 7 chorus | 105-141 | `--D-D---` | `D-DUDUDU` | 2.6 / 5.0 | 52.1% / 97.8% | 75.0% / 12.5% | certain / certain, boost |

Chord comparison: overseg 0.996, underseg 0.996, majmin 0.989. Song grid fit 0.546 in both runs (the song-level "strum detection uncertain" note still prints, as in version 1.2). Outside the two boosted choruses no strike moved; six bars changed only between a strike and a mute.

## Per song

### Summer of '69

**Pages.** Page 1: header (Key D major, Capo none, Tempo 139 bpm, the italics note), seven diagrams (D A Bm G F Bb C), the intro "verse 2" with its strip (D, D) and the pickup cell, the first verse with its strip and `A A D D ×3`, and the first chorus with its strip (Bm, A) and `Bm A D G ×2`. Page 2: the short verse, the second chorus with its new strip, a 5-bar verse and the bridge ("verse 2", now certain, strip A then F). Page 3: the third verse, the third chorus, the last verse (uncertain, label line only) and the outro (uncertain); about two thirds of the page is used.

**Quality.** The two choruses that printed a single down stroke (`D-------`) now print `D-DUDUD-`, and the bridge, uncertain before, prints `D-DUD-DU`. Every chord change sits on a bar line; the intro's second bar reads D where it read N.C./D. In the outro, bar 113 reads D (was A/D) and bar 115 reads N.C. (was D): the decoder moved the end of the last D to the bar line before it, so the outro now has three N.C. bars before the two italic fills. Bar 120 no longer prints. Still three pages: the strips are taller than the boxes were, so page 3 now holds four sections rather than the outro alone.

**Completeness.** 120 of 121 bars printed (bar 120, the ring-out, dropped). Sections 9 and 10 are uncertain and show no strip.

### Chelsea Dagger

**Pages.** Page 1: header (Key D major, Tempo 155 bpm, the italics and strum-uncertain notes), seven diagrams, "Passing: B 4322", the intro "verse" (uncertain, no strip), the first chorus with its strip (G, G) and its two `×2` blocks, and the first verse with its strip (G; Em changing to Bm on beat 3). Page 2: the rest of the first verse, the 10-bar chorus with its strip, and the second verse with its strip (A; D changing to Em on beat 3). Page 3: the 6-bar chorus, the bridge and the final chorus (strip D; C changing to D on beat 3), about four fifths full.

**Quality.** The boxes that were three quarters rests are gone: the first chorus prints `D-D-D-DU`, the final chorus `D-DUDUDU`, the bridge `--DUD-DU`. Two chord cells changed: bar 50 in the first verse prints B where version 1.2 printed Bm (one B minor event decoded as B major), and bar 53 reads Em where it read D/Em. B is still a passing chord without a diagram, now named in two cells. The first chorus's strip draws its pattern over bars 9 and 10, where the guitar has not yet entered; the strip shows the section's first two full bars whether they are played or not.

**Completeness.** All 142 bars present; no trailing bars to drop. Three pages, as in version 1.2.

### Pour Some Sugar On Me

**Pages.** Page 1: header (Key A major (shapes), Capo fret 4, Tempo 85 bpm, the four notes), four diagrams (A G C F), "Passing: D 2220, Am 2000", the intro, the first verse, the first chorus and the first row of the second verse, each under its label line with "(uncertain)" and no strip. Page 2: the rest of the second verse, the second chorus, the solo section and the final chorus, all uncertain; about two thirds of the page is used. The first validation run printed strips for the intro, the first chorus and the second verse; without them the sheet is still two pages.

**Quality.** The decoder removed four of the five sub-beat events and 12 of 106 chord events, and N.C. time fell from 20.3% to 18.6%. D (F# sounding) lost its diagram: two short F# events went, so its share of the chord time fell under the passing threshold, and it now prints as passing in the D/G cells. Bars 1 and 38 read A where they read N.C./A, and the intro's bar 7 reads N.C. where it read A; bar 8 is still the italic A fill. Every section prints as uncertain with its covers figure (48 to 94%), as the expectation required: the ear check of the last chorus found two guitars in the stem and no single strumming pattern to extract, and the intro, first chorus and second verse come from the same stem.

**Completeness.** All 103 bars present; nothing dropped (the last bar holds a chord).

### Wet Leg "mangetout"

**Pages.** Page 1: header (Key C major, Tempo 128 bpm), three diagrams (C F Dm), "Passing: C# 1114", the opening "verse 2" with its strip, the chorus (`C C F F ×3`) with straight eighths, and the verse, now certain, with its strip. Page 2: the second chorus, the verse, "verse 2" and the bridge (`F C C Dm ×8`), each with a strip. Page 3: the last chorus (strip Dm; F changing to C# on beat 3) and the outro, one N.C. cell under the line "Strum as in chorus (uncertain)".

**Quality.** The four bars of non-song audio no longer print, and three chord cells lost a stray C# or F (bars 18, 57 and 63 now read C). In bar 107 the passing C# moved from slot 6 to slot 4 (beat 3), and bar 108 reads N.C. where it held a passing C#. The verse prints `D-D-D-DU` with certainty where version 1.2 showed no box. But the sheet stays at three pages: the strips are 90 px tall where the boxes were 60 px, and one more section has one, so the last chorus moved to page 3. The outro is one N.C. bar where version 1.2 said no strummed instrument was detected: the trailing drop leaves it one bar long, so it is short and inherits the chorus's pattern. The first validation run printed the chorus's "covers 100% of detected strokes" there; it now reads "Strum as in chorus (uncertain)", which names where the pattern came from without claiming a figure for this bar.

**Completeness.** 109 of 113 bars printed (bars 109 to 112 dropped); bar 108 kept as the outro's only bar.

### David Bowie "Fame"

**Pages.** Page 1: header (Key D minor (shapes), Capo fret 3, Tempo 95 bpm, the capo notes), three diagrams (Dm G D), "Passing: Am 2000", the intro (uncertain, the pickup cell), "verse 2" with a 16-slot strip, and the chorus with its strip. Page 2: the 34-bar verse with its strip, the second "verse 2" (strip with the Dm to Am and Am to G changes), the chorus and the start of the bridge (strip D; D changing to G on beat 3). Page 3: the rest of the bridge and the last verse with its strip; about a third of the page is used.

**Quality.** The worked example does what it was built for here: the half-bar changes of the second "verse 2" are drawn under the strokes they fall on. Changes on a bar start rose from 6 of 14 to 8 of 14; the six left all fall inside a bar (four on beat 3, one on beat 2 in the intro, one on beat 4), which is where the strip draws them. Bar 52 reads D where it read D/Dm. Bar 100 is gone. The cost is a third page: version 1.2 fitted in two, with the last verse ending near the foot of page 2. The header still names F minor above a grid of D major, as in version 1.2.

**Completeness.** 100 of 101 bars printed (bar 100 dropped).

## What cannot be verified without listening

- Whether the recovered chorus patterns are what is played: Summer of '69 sections 4 and 8 (`D-DUDUD-`) and Chelsea Dagger sections 1 and 7 (`D-D-D-DU`, `D-DUDUDU`). The ear check judged click tracks from the recall spike's configuration on Summer of '69's first chorus and Chelsea Dagger's chorus, not these runs' final patterns.
- Every pattern the new vote changed without new onsets: for example Summer of '69's first verse (`xxxUxxxx`) and bridge (`D-DUD-DU`), Wet Leg's verse (`D-D-D-DU`), and Fame's five denser printed sections. The onsets are the same as version 1.2; whether the added slots are played is a listening question.
- Whether one strummed part dominates Pour Some Sugar On Me's intro, first chorus and second verse. The ear check covered the last chorus only (two guitars, no single pattern). These three sections score 0.453 to 0.472 and print as uncertain because the sixteenth-grid threshold is 0.55, not because anything measured here tells one guitar from two.
- The chord cells the beat-aware decoder changed: Summer of '69 bars 1, 113 and 115; Chelsea Dagger bars 50 (Bm to B) and 53; Pour Some Sugar On Me bars 1 and 38 (N.C./A to A), the intro's bar 7 and the chorus cells that lost a D or C; Wet Leg bars 18, 57 and 63, bar 107 (`F/C#@6` to `F/C#@4`, the passing C# a beat earlier) and bar 108 (a passing `C#` to `N.C.`); Fame bar 52. The decoder made each change land on a bar or beat line; whether the new reading is the played chord is not measurable from these files.
- Whether Wet Leg's bar 108 is music; the ear check judged bars 108 to 112 as noise, and the cap keeps 108.
- As in version 1.2: true key mode, section names, and the chord names of Wet Leg and Fame.

## What to improve next

Ranked by benefit to the person reading the sheet.

1. **A chance-corrected confidence.** Stage: strums. Evidence: Pour Some Sugar On Me's two-guitar sections are held uncertain only by the sixteenth-grid threshold (0.55 against confidences of 0.453 to 0.472), and `explained` (81 to 94%) does not separate them from the good sections, exactly as the recall spike found for the union. Neither threshold is a test for noise: the third-share vote keeps most of a dense spray's slots, so random sections striking half the slots print as certain 85 percent of the time at 8 slots with 0.45 and 69 percent at 16 slots with 0.50 (the whole-branch review's measurement), and still about 30 percent at 16 slots with 0.55 (2000 random eight-bar sections). Replace the bare mean Jaccard with one corrected for chance: the mean Jaccard to the section's vote less the same figure for a slot-shuffled baseline at the same density, measured on all five songs. Song grid fit is not the answer on its own: Chelsea Dagger's is poor (0.55) and the ear check accepted its patterns.
2. **Win back the page.** Stage: render. Evidence: Fame went from two pages to three and Wet Leg stayed at three, because the strip is 90 px tall against the box's 60 px and more sections now have one (Summer of '69 7 to 9, Wet Leg 7 to 8). Page 3 of Wet Leg holds one chorus and one N.C. cell; page 3 of Fame holds the last 25 bars. Options: a one-bar strip when neither of the first two bars has a change inside it (most sections, which show the same chord twice), or the strip beside the first rows rather than above them.
3. **Fix the one-bar outro.** Stage: score or strums. Evidence: dropping Wet Leg's trailing bars left a one-bar, all-N outro that inherits the last chorus's pattern and prints "Strum as in chorus (uncertain)" over an N.C. cell; version 1.2 printed "No strummed instrument detected". Either let the trailing rule drop a whole trailing section that is all N, or decide `no_instrument` after the drop.
4. **Choose strip bars that are played.** Stage: render. Evidence: Chelsea Dagger's first-chorus strip shows bars 9 and 10, where the guitar has not entered (Pour Some Sugar On Me prints no strips, so its N.C. intro bar no longer applies). Skipping bars with no detected strikes, or all-N bars, before choosing the first two would show what is played.
5. **Recover sustained strums on sixteenth grids.** Stage: strums. Evidence: the recall gate is off on 16-slot songs by design (stated limitation), so a sixteenth-grid song with distorted sustained strums keeps sparse patterns. It needs a guard that tells one guitar from two, which the recall measurements did not find.
6. **Carried from version 1.2** (items 3 to 6 there, unchanged): the key mode on a near tie (Fame F minor over D major shapes; Pour Some Sugar On Me C# major), phrase shifts that move a section earlier, fill refinement where the guitar is faint, and section naming.

Not ranked as faults: Chelsea Dagger's on-bar share rose only from 59 to 60 of 69, but all nine changes still off a bar start fall in the middle of a bar (Em to Bm twice and D to Em once in the verses, C to D six times in the final chorus's C/D cells), which is where the grid and the strip put them.
