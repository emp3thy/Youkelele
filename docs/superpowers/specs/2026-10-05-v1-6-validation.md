# Version 1.6 validation on eight real songs and one blind song

Date: 2026-10-06. Branch `worktree-v1-6` at `762851b` (first validation, commit `ccb295c`), then the fix round at `7ed8072` (package version 0.7.0) and the final fix wave at `705b451`. Checks every expectation in section 8 of `2026-10-05-ukulele-tab-chain-v1-6-design.md` against the kept version 1.5 runs, and runs one song the chain had never seen. Bar and section numbers are 0-based, as in `grid.json`; a range written `55-61` ends before bar 61. "Planned section" means a section of the section plan, which is what the sheet prints; "member" means one of the grid sections a planned section merged. "Pattern changed" means that at least one bar of the section prints a stroke vector different from the one pattern 1.5 printed for the section, as `evaluate --compare` counts it ("patterns changed in N bars"). The ear verdicts quoted are the owner's from the 1.5 listening pass (`2026-10-04-v1-5-validation.md`), which is this version's ear truth; nothing in this record was listened to.

## Runs and baselines

The eight version 1.5 run folders under `runs\` were the baseline. Before any re-run, `02_grid` to `07_render`, `manifest.json` and `source_meta.json` of each were copied to `%TEMP%\youkulele-v16-validation\baseline\<folder>\`, with the output of `uv run youkelele evaluate <folder>` beside them (`evaluate.txt`, made by this branch's harness, which reads a 1.5 `strums.json` through the rebuilt bars of spec 7). Then, for each folder in turn, the stale 1.5 stage folders `05_arrange`, `06_score` and `07_render` were removed (1.6 numbers the stages after strums `05_riff`, `06_arrange`, `07_score`, `08_render`, so the old folders would otherwise have stayed beside the new ones) and the folder was re-run in place with `uv run youkelele run "<source from its manifest>" --from strums --runs-dir C:\Users\gethi\sources\Youkulele\runs`. Every source resolved to its own folder with no prompt. The blind song ran from ingest with the same `--runs-dir`. Every run exited 0. Each run's log is under `%TEMP%\youkulele-v16-validation\logs\`; the scripts (`baseline.py`, `rerun.py`, `measure.py`, `analyse.py`, `evaluate_all.py`, `make_clips.py`, `make_sample.py`) and their outputs are in the same scratch folder.

| Song | Folder | From | Wall time of the command | Stage times from the manifest |
|---|---|---|---:|---|
| Summer of '69 | `summer-of-69` | strums | 34.1 s | riff 0.3 s, arrange 0.3 s, score 0.1 s, render 1.4 s |
| Chelsea Dagger | `chelsea-dagger` | strums | 16.9 s | riff 0.4 s, arrange 0.4 s, score 0.2 s, render 1.3 s |
| Pour Some Sugar On Me | `pour-some-sugar-on-me` | strums | 17.3 s | riff 0.4 s, arrange 0.5 s, score 0.2 s, render 1.8 s |
| Wet Leg "mangetout" | `mangetout` | strums | 67.0 s | riff 26.7 s, arrange 0.4 s, score 0.1 s, render 1.4 s |
| David Bowie "Fame" | `fame` | strums | 85.2 s | riff 34.5 s, arrange 0.4 s, score 0.2 s, render 1.8 s |
| Pat Benatar "All Fired Up" | `all-fired-up` | strums | 61.7 s | riff 21.5 s, arrange 0.3 s, score 0.1 s, render 0.9 s |
| INXS "Need You Tonight" | `need-you-tonight` | strums | 41.5 s | riff 16.3 s, arrange 0.2 s, score 0.1 s, render 0.9 s |
| The Cars "You Might Think" | `the-cars-you-might-think` | strums | 38.5 s | riff 14.7 s, arrange 0.2 s, score 0.1 s, render 0.9 s |
| The Beatles "Day Tripper" (blind) | `the-beatles-day-tripper` | ingest | 287.2 s | separate 217.8 s, grid 15.6 s, harmony 22.3 s, strums 20.4 s, riff 0.1 s, arrange 0.1 s, score 0.1 s, render 0.8 s |

The wall time includes `uv run` starting Python, and the eight re-runs shared the machine with the blind song's separation, which ran at the same time. The riff stage's time is the pitch tracking of the songs that have a riff section; on the three without one it is under half a second. Every manifest records version 0.7.0 for strums, riff, arrange, score and render; the stages that were not re-run keep their earlier stamps (0.5.0 on six songs, harmony 0.6.0 on Need You Tonight, ingest to harmony 0.6.0 on The Cars), as they should. The blind song's log shows one `HTTP Error 403: Forbidden` from the downloader before the download succeeded on its own retry (2.75 MiB, 169 s of audio).

Measurement: `evaluate` on all nine folders and `evaluate <baseline> --compare <folder>` on the eight (outputs in `evaluate\`); `measure.py`, which compares `grid.json` and `chords.json` byte for byte, the chord events and `bar_onsets` value for value, the plan and the recall-boost flags, then lists per planned section the 1.5 pattern, the 1.6 vote (candidate, unit, both scores, certainty, chance p), the riff test figures, the ring median, the members' printed patterns, the score's printed stroke vectors, grey and tab bars, the riff stage's gate figures, page counts and the lines of the HTML; `analyse.py`, which collects the ring medians, finds every sustain line on the two muted songs and chooses the ear-clip bars. Every page of all nine sheets was rasterised at 110 dpi with PyMuPDF (`pages\<song>\p<n>.png`) and looked at.

## Expectations from spec section 8

Written before the runs, as the spec states them; checked after.

| # | Expectation | Met? | Figure |
|---|---|---|---|
| 1 | `grid.json`, the chord events and `bar_onsets` byte-identical to 1.5 on all eight songs | **Yes** | `grid.json` and `chords.json` byte-identical on all eight; chord events, `bar_onsets`, the plan and every recall-boost flag identical on all eight |
| 2 | The 10 sections the spike says change pattern under the hybrid vote are exactly the sections that change; the five ear-right patterns print as before; Summer of '69 53-58 prints `DU-U-UDU`; The Cars 52-60 prints `DUDUDUDU` | **No** | All ten predicted sections changed, but **22** sections changed in all (the harness and the script agree): the period rule of spec 4.2 made **20** of 69 sections two-bar units where the spec expected six, and 11 of the 22 changes are two-bar alternations nobody predicted. Only 3 of the ten print through the medoid switch the spike measured; 7 change by the two-bar rule. The ear-right patterns all print as before (the spec lists six ranges under "five": All Fired Up 33-49 `DUDUDUDU`, 61-90 `D-D-D-DU`, 128-132 `D---DUD-`; The Cars 11-19 `DUDUDUDU`, 68-72 `-UDUDUD-`; Need You Tonight 13-24 `DUD-D-D-DUxUxU-U`). Summer of '69 53-58 prints `DU-U-UDU` alternating with `DUDUDUD-` (a two-bar majority, not the one-bar medoid). The Cars 52-60 prints `DUDUDUDU`. See "Pattern changes" below |
| 3 | All Fired Up's Verse 2 prints the section pattern on 55-61, 61-90 and 104-110, its own greyed pattern on 90-97, and "riff heard, not transcribed" strokes on 97-104; one "Verse 2" header. Wet Leg's Verse 4 and All Fired Up's Verse 1 print one pattern throughout | **No** | 55-61, 61-90 and 104-110 print `D-D-D-DU`; 90-97 prints its own `xUDxxxx-`, greyed (bars 90 to 96; bar 97 starts the next member); one "Verse 2" header. **97-104 prints the section's `D-D-D-DU` in black with no riff phrase**: the member is a riff by the 5.1 test (pitch-change share on its own onsets above 0.4) and fails the gate (agreement 0.07), but its own pattern agrees 0.50 with the section's, above `MEMBER_AGREE` 0.35, so by 4.3 it prints the section's pattern, and the header phrase is the longest member's (none). Spec 4.3 states both 0.50 for this member and that it prints "riff heard, not transcribed" strokes; the two cannot both hold under the rule as written. Wet Leg Verse 4 (58-100) prints `DUDUxxDU` throughout; All Fired Up Verse 1 prints `DUDUDUDU` on printed bars 29 to 48 |
| 4 | Need You Tonight's and Fame's sections are short (no sustain lines); every section of the other six rings and shows sustain lines on held strokes; per-section medians recorded and none within 1 dB of the threshold; Pour Some Sugar On Me prints greyed strokes in every section | **No** | Need You Tonight: all seven sections short. Fame: 8 of 9 short; **Instrumental 3 (81-85) rings at 4.25 dB** and draws sustain lines. Of the other six songs' 53 sections, **four are short**: Summer of '69 Intro (6.01 dB), Chelsea Dagger Intro (12.16), The Cars Chorus 2 (12.47) and Verse 3 (9.35); so is All Fired Up's Verse 2 member 97-104 (7.33; the ring flag is decided per member). **Nine** of the 68 measured section medians on the eight songs lie within 1 dB of 5: Chelsea Dagger Instrumental 4.98; Fame Instrumental 3 4.25; Need You Tonight Intro 5.60, Chorus 2 5.87, Verse 3 5.95; The Cars Intro 4.27, Verse 1 4.92, Chorus 1 4.31, Verse 4 4.33 (Summer of '69's Intro at 6.008 is just outside). Stroke-less bars draw sustain lines even in a short member (Need You Tonight Intro bars 0 to 7, Fame bar 0, Summer of '69 bar 0, Chelsea Dagger Intro bars 5, 6 and 9 to 11, The Cars Verse 3 bars 62 and 63): see "What to improve next", item 4, fixed in the fix round. Pour Some Sugar On Me prints greyed strokes in all eight sections (103 of 103 bars) |
| 5 | Riff flags: All Fired Up 33-49 and The Cars 11-19 lose theirs; every 1.5 flag the ear confirmed stays; nothing new is flagged outside All Fired Up 97-104 | **No** | All Fired Up 33-49 loses its flag (pitch-change share 0.08) and The Cars 11-19 loses its (0.15). Fame's nine, Need You Tonight's six and The Cars Verse 3 (52-68) keep theirs; All Fired Up 97-104 gains one. **All Fired Up Verse 2 (61-90) loses its flag** (0.29), and the owner heard that figure as a riff ("d D D DUD", clip 7 of the 1.5 pass). **Wet Leg's member 58-65 is newly flagged** by the test on its own onsets, outside the expected list; it prints the section's pattern, so the flag does not reach the sheet. Nine other 1.5 flags that the ear never judged also go: Summer of '69 Intro and Verse 1, All Fired Up Chorus 2, The Cars Intro, Chorus 1, Verse 2, Chorus 2, Verse 4 and Chorus 4 (shares 0.07 to 0.33). See "Riff test" below |
| 6 | Tab prints on Need You Tonight's verses and choruses that pass the gate (the verse must), on the C string without an octave shift; Fame, Need You Tonight's intro, The Cars Verse 3 and All Fired Up 97-104 print "riff heard, not transcribed" | **No** | Need You Tonight Verse 1 (13-24) prints tab on all 11 bars: C string, frets 0, 2 and 3, no octave shift (agreement 0.739, support 0.777, named share 0.942). No other section passes. Fame's nine sections and The Cars Verse 3 print "riff heard, not transcribed". **Need You Tonight's Intro prints "pattern uncertain"**: it is not a riff by the test (it fails the 1.5 chroma features, as in 1.5, which never flagged it) and its pattern is uncertain (p 0.989). **All Fired Up 97-104 prints no phrase** (row 3) |
| 7 | Pages at most one more than 1.5 on every song | **Yes** | 3, 3, 3, 2, 3, 2, 2, 3 against 1.5's 2, 3, 2, 2, 2, 2, 2, 3: three songs gain one page, none gains two; 18 pages become 21. Against the A14 estimate (3, 3, 3, 2, 3, 3, 3, 3): equal on six, one fewer on All Fired Up and Need You Tonight |
| 8 | The blind song runs to a sheet with exit 0; its riff flags, gate figures and tab, if any, are recorded, not judged | **Yes** | Exit 0, 287 s, 3 pages; no section flagged riff, so `riff.json` is empty and no tab prints. Figures below |

Scorecard: three met (1, 7, 8), five missed (2 to 6). Nothing was tuned; every miss is recorded here with its figure. The table above is the first validation (at `762851b`); the fix round below changed the code and spec where the misses traced to a defect, re-ran every song and re-measured rows 2 to 7.

## Fix round after the first validation

**What changed and why** (commit `7ed8072`, with the spec amendments; rulings by the controller after review):

1. **Two-bar unit on the statistic the spike measured.** Spec 4.2 named lag-2 minus lag-1 agreement, but its count and A3's figures came from the two-bar medoid margin (see "Why" under "The twelve unpredicted changes"). `music/vote.py` now measures the margin as the best consecutive pair's score (every other bar against the pair's bar in its phase) minus the one-bar medoid's score; `PERIOD2_MARGIN` (0.10) and the two-strike floor are unchanged and apply to that pair; the voted pairs are phased from that pair's start, and the printed vector is aligned to the section's first bar. The riff reduction (`music/riff_line.py`) uses the same unit and phase. Spec 4.2 and A3 amended.
2. **Ring flag on every bar.** `BarStrums` carries `rings`, its member's flag, and the score builder reads it, so a bar with no detected stroke in a short member prints no sustain line (it defaulted to ringing). 1.5 files take the flag from the pattern. The flag stays per member; spec 4.4 now says so, with the section figure the longest member's.
3. **Riff members print their own strokes.** A member that is a riff by the 5.1 test prints its own pattern, greyed when uncertain, whatever its agreement with the section's; the header still follows the longest member, so nothing on the page names it a riff. Spec 4.3 amended.

Covering tests: `tests/test_vote.py` (the margin's value, a section where lag agreement would fire and the medoid margin does not, odd-phase pairing aligned to the first bar), `tests/test_riff_line.py` (an odd-phase two-bar riff aligned to the first bar), `tests/test_score_builder.py` (a strokeless bar takes its member's flag, short and ringing), `tests/test_compat.py` (backfilled bars carry the pattern's flag), `tests/test_stage_strums.py` (a riff member that agrees with its section prints its own pattern; strokeless bar records carry the member's flag).

**Re-runs.** The eight songs re-ran `--from strums` (11 to 53 s each, exit 0). The blind song re-ran from ingest by a slip in the run script (262 s, exit 0; tempo, bars, sections, key and the 44 chord events came out as in the first run), then `--from strums` as intended (22 s). Logs are under `logs\`; the first round's outputs are kept as `measure-round1\`, `evaluate-round1\`, `pages-round1\` and `logs-round1\`.

**Before and after.**

| Figure (eight songs, 69 planned sections) | First validation | After the fix round |
|---|---:|---:|
| Two-bar sections | 20 | **6** (Summer of '69 4-19, 31-41, 75-83, 95-111; Need You Tonight 24-31; The Cars 72-76), exactly the spec's six |
| Sections keeping the medoid | 8 (5 change the page) | 11 (8 change the page) |
| Sections whose printed pattern changed against 1.5 | 22 | 15 |
| Of the ten predicted, printed by the medoid alone | 3 | 7 |
| Certainty flips against 1.5 | 1 | 2 |
| Strokeless bars of short members drawing sustain lines | 17 | 0 |
| Sustain lines on Need You Tonight's sheet | 4 | 0 |
| Pages | 3, 3, 3, 2, 3, 2, 2, 3 | 3, 3, 3, 2, 3, 2, 2, 3 |

On the medoid margin, 7 planned sections clear 0.10 and the floor removes one (All Fired Up 124-128, whose best pair has a bar with no strike); at 0.08 and 0.15 the counts are 8 and 7, and 4 and 3. The spike reported 9 and 8 at 0.08 and 5 and 4 at 0.15; the stage reads its own strike classes, not the spike's rendered bars.

**Spec 8 re-measured (rows 2 to 7).**

| # | Met? | Figure after the fix round |
|---|---|---|
| 1 | **Yes** | Byte-identical again on all eight songs |
| 2 | **No**, by sections the amended spec itself predicts | All ten predicted sections change. Seven print the spike's medoid bar alone: Summer of '69 53-58 `DU-U-UDU` (medoid 0.632 vs majority 0.582) and Outro `xU--DU--` (0.180 vs 0.089), Chelsea Dagger Chorus 2 `D-D---D-` (0.574 vs 0.518), Pour Some Sugar On Me Chorus 2 `D---D-DUD---D--U` (0.279 vs 0.238), Fame Chorus `DUDUDUD---D-D-D-` (0.704 vs 0.658) and Verse 3 `D-DUDUD--UD-DUxx` (0.650 vs 0.609), Need You Tonight Outro `DU-U-UDU--DU-U-x` (0.382 vs 0.324). Three are among spec 4.2's six two-bar sections and print an alternating pair: Summer of '69 75-83 `D-DU-UD-` / `DU-UD-D-`, Need You Tonight 24-31 `D---D---D--UxU-U` / `D-DUD-DU-UDU-U-U`, The Cars 72-76 `-UD-D-D-` / `DUD-DUDU`. Five sections change beyond the ten: Summer of '69 4-19 (`D-DU-xxx` / `xxxxxxD-`), 31-41 (`D--U--D-` / `DUD-DUD-`, medoid) and 95-111 (`D--U----` / `DUDUDUDU`), the other three two-bar sections spec 4.2 names; Wet Leg Verse 4, whose riff member 58-65 now prints its own `D-DU-UDU` (ruling 3); and All Fired Up Verse 2 (row 3). The ear-right patterns all print as before; Summer of '69 53-58 prints `DU-U-UDU`; The Cars 52-60 prints `DUDUDUDU` |
| 3 | **No** (Wet Leg) | All Fired Up Verse 2: 55-61, 61-90 and 104-110 print `D-D-D-DU`; 90-97 its own `xUDxxxx-`, greyed; 97-104 its own `xxDxDxDx` in black, short, with no phrase, as spec 4.3 now says; one "Verse 2" header. All Fired Up Verse 1 prints `DUDUDUDU` throughout. **Wet Leg Verse 4 no longer prints one pattern**: its member 58-65 is a riff by the test (row 5), so by ruling 3 it prints its own `D-DU-UDU` on bars 58 to 64, then `DUDUxxDU` |
| 4 | **No** | Ring medians and flags are as in the first validation (Fame Instrumental 3 rings at 4.25; four sections and one member of the ringing songs are short; nine medians within 1 dB of 5). Every printed stroke now carries its member's flag: no bar of a short member draws a sustain line (Need You Tonight's sheet has none; Fame's 16 are all Instrumental 3). Pour Some Sugar On Me prints greyed strokes on 103 of 103 bars |
| 5 | **No** | Unchanged: All Fired Up 33-49 and The Cars 11-19 lose their flags; All Fired Up 61-90 loses its flag (0.29), which the ear calls a riff; Wet Leg 58-65 is newly flagged |
| 6 | **No** | Need You Tonight Verse 1 still prints tab (0.739, 0.777, 0.942; C string, frets 0, 2, 3, no shift), and nothing else passes. The reduction of Need You Tonight's other verses is now one-bar: 31-48 reads 0.430, 0.523, 0.945 (was 0.411 as two-bar) and 56-79 reads 0.241, 0.288, 0.850 (was 0.171); both still fail on agreement, so no new tab prints. Fame's nine and The Cars Verse 3 print "riff heard, not transcribed"; Need You Tonight's Intro prints "pattern uncertain" (not a riff by the test); All Fired Up 97-104 prints its own strokes with no phrase, as the amended spec 4.3 says |
| 7 | **Yes** | Pages 3, 3, 3, 2, 3, 2, 2, 3, as in the first validation |
| 8 | **Yes** | The blind song again runs to three pages with no riff flag; it now has two two-bar sections (Instrumental 2 46-52, Outro 78-95; it had five) and one medoid (Verse 2 `--DUDUDU`) |

Scorecard after the fix round: three met (1, 7, 8), five missed (2 to 6). Row 2 now misses only by the three two-bar sections and the riff member that the amended spec itself predicts; row 3 misses on Wet Leg because ruling 3 meets the new riff flag of row 5.

**Certainty after the fix round.** Two sections differ from 1.5. Summer of '69 Verse 5 (95-111) stays certain as in the first validation (two-bar confidence 0.57 clears the floor its one-bar vote of 0.43 did not). Summer of '69 Verse 1 (4-19), certain in 1.5 and in the first validation, prints uncertain and greyed after the fix round. *Corrected in the final fix wave:* the chance p never reads the vote; what the vote's first half decided was which test applies. In 1.5 the one-bar vote `xxxxxxxU` was full (no rest), and in the first validation the two-bar vote's first half was `xxxxxxxU` too, so the section took the density test (density 0.77, certain). Paired from bar 5 in the fix round, the first half became `xxxxxxD-`, which has a rest, so the section took the shuffle test, which its bars cannot pass (p 1.0). The final fix wave makes the whole two-bar vector the representative (full only when both bars are); Verse 1's two bars `xxxxxxD-` / `D-DU-xxx` both rest somewhere, so it takes the shuffle test whichever bar it starts on and stays uncertain (p 1.0).

**Pages after the fix round.** Every page of the nine sheets was rasterised again and the pages that changed were looked at. Summer of '69 page 1: the pickup bar no longer draws a sustain line, and Verse 1 prints its alternating pair in grey. Need You Tonight page 1: the Intro's single down strokes draw no sustain lines. All Fired Up page 2: 97-104 prints its own muted figure in black, short, on four-bar lines. Wet Leg page 2: Verse 4 opens with seven bars of `D-DU-UDU` before `DUDUxxDU`. Fame page 2: Chorus and Verse 3 print their one-bar medoids. No element is clipped.

### Final fix wave

**What changed** (commit `705b451`, rulings after the whole-branch review; spec 4.1 amended):

1. **The whole two-bar vector decides the chance test.** The stage passed the first half of a two-bar vote to the structure test, so whether a section took the density test of a full vote or the shuffle test depended on the bar it started on. It now passes the whole unit vector, which is full only when both bars are. One-bar votes are tested exactly as before.
2. **A merged member aligns to the section's two-bar pattern.** A member that is not the longest compared only its first bar with the section's first bar and printed the section's vector from its own first bar, so a member playing the figure from its second bar could print it swapped. The stage now scores both alignments (offset 0 and 1) of the section's vector against the member's own bars, uses the better one for the `MEMBER_AGREE` test and for printing, records the offset on the member and logs it when it is 1.

**Re-run.** The eight songs and the blind song re-ran `--from strums` (11 to 54 s each, exit 0; logs under `logs\`, the fix round's outputs kept as `snapshot-round2\`, `evaluate-round2\`, `logs-round2\`). `diff_final.py` and `exposure_final.py` in the scratch folder compare them.

**Before and after: nothing moved.** `strums.json` is byte-identical to the fix round's on all nine songs, and so are `riff.json`, `score.json` and `sheet.html`; every `evaluate` and `evaluate --compare` output against the 1.5 baselines is identical to the fix round's. No state or alignment changed, because no section on these songs is exposed to either ruling:

| Ruling | Could move | On these songs |
|---|---|---|
| 1, whole vector | a two-bar vote with exactly one full bar, where the full bar came first | Of the eight two-bar sections (six on the eight songs, two on the blind song), only Summer of '69 Verse 5 (95-111, `D--U----` / `DUDUDUDU`) has a full bar, and it is the second: the section took the shuffle test before and takes it now (p 0.027, certain). Summer of '69 Verse 1 (4-19, `xxxxxxD-` / `D-DU-xxx`) has a rest in both bars and stays uncertain (p 1.0), now whichever bar it starts on |
| 2, member alignment | a member of a merged section whose longest member votes two bars | The three merged sections (Wet Leg Verse 4, All Fired Up Verse 1 and Verse 2) all have one-bar longest members, so every offset is 0 and no alignment log line was written |

**Pages.** Unchanged: 3, 3, 3, 2, 3, 2, 2, 3 on the eight songs and 3 on the blind song; the HTML is byte-identical, so the pages were not looked at again.

## Pattern changes (first validation, superseded by the fix round)

Everything in this section, its tables and its certainty paragraph, was measured in the first validation, on the lag-based two-bar rule that the fix round replaced. The patterns the sheets print now are in "Fix round after the first validation" (row 2 of its table) and "Final fix wave"; this section is kept as the record of what the first rule did.

### The ten predicted sections

The pattern-vote spike's follow-up (`followup_out.txt` in its scratch folder) lists the 14 sections where the medoid wins by at least 0.04; four have an all-rest medoid and are held by the two-stroke floor, which leaves the ten. All ten print a new pattern, but only three by the route the spike measured.

| Song, section | 1.5 printed | Spike's medoid | 1.6 prints | How | Scores (kept first) |
|---|---|---|---|---|---|
| Summer of '69 Verse 3 53-58 | `DU-UDUDU` | `DU-U-UDU` | `DU-U-UDU` / `DUDUDUD-`, greyed | two-bar majority | majority 0.692, medoid 0.692 |
| Summer of '69 Verse 4 75-83 | `DUDUDUD-` | `DU-UD-D-` | `D-DU-UD-` / `DU-UD-D-` | two-bar majority | 0.766 vs 0.739 |
| Summer of '69 Outro 111-121 | `x---D---` | `xU--DU--` | `D--U----` / `-U--D-D-`, greyed | two-bar majority | 0.300 vs 0.208 |
| Chelsea Dagger Chorus 2 61-71 | `D-D-D-D-` | `D-D---D-` | `--D-D-D-` / `D-D---D-` | two-bar medoid | medoid 0.566 vs 0.502 |
| Pour Some Sugar On Me Chorus 2 55-67 | `----D---D-D-D---` | `D---D-DUD---D--U` | `D---D-DUD---D--U`, greyed | medoid | 0.279 vs 0.238 |
| Fame Chorus 61-71 | `DUDUDUD---D-DUD-` | `DUDUDUD---D-D-D-` | `D-DUD-D-D-D-DUDU` / `DUDUDUD--UD-D-x-` | two-bar majority | 0.727 vs 0.727 |
| Fame Verse 3 71-81 | `D-DUDUD-DUD-DUxx` | `D-DUDUD--UD-DUxx` | `D-DUDUD--UD-DUxx` | medoid | 0.650 vs 0.609 |
| Need You Tonight Chorus 1 24-31 | `D-DUD-DUDUDUxU-U` | `DUDUD-DUDUDU-U-U` | `D---D---D--UxU-U` / `D-DUD-DU-UDU-U-U` | two-bar majority | 0.773 vs 0.804 |
| Need You Tonight Outro 79-86 | `DU-UDUDUD-xU-UDU` | `DU-U-UDU--DU-U-x` | `DU-U-UDU--DU-UDx` / `DUx-D-DxDUxUxx-U`, greyed | two-bar majority | 0.458 vs 0.458 |
| The Cars Instrumental 72-76 | `DUD-DUDU` | `-UD-D-D-` | `-UD-D-D-` / `DUD-DUDU`, greyed | two-bar majority | 0.909 vs 0.909 |

Where a two-bar majority prints, the spike's medoid bar is usually one of the pair (Summer of '69 53-58 and 75-83, The Cars 72-76, nearly Need You Tonight's Outro), so the syncopation the medoid was meant to keep is on the page every other bar.

### The twelve unpredicted changes

Eleven sections changed only because the period rule made them two-bar units, plus All Fired Up's Verse 2 member 90-97, which spec 4.3 did predict.

| Song, section | 1.5 printed | 1.6 prints | Vote |
|---|---|---|---|
| Summer of '69 Verse 1 4-19 | `xxxUxxxx` | `D-DU-xxx` / `xxxxxxxU` | two-bar majority 0.765 vs 0.787 |
| Summer of '69 Verse 2 31-41 | `DUDUD-D-` | `D--U--D-` / `DUD-DUD-` | two-bar medoid 0.688 vs 0.636 |
| Summer of '69 Chorus 2 41-53 | `D-DUDUD-` | `D-DU-UD-` / `D-DUDUD-` | two-bar majority 0.709 vs 0.728 |
| Summer of '69 Instrumental 68-75 | `DUDUDUDU` | `D--UDUDU` / `DUDUDUDU` | two-bar majority 0.867 vs 0.833 |
| Summer of '69 Verse 5 95-111 | `D--UD-D-` (uncertain) | `D--U----` / `DUDUDUDU` (certain) | two-bar majority 0.531 vs 0.490 |
| Fame Verse 1 17-29 | `DUD-DUx-D-DUDUD-` | `----DUx-D-DUD-D-` / `DUD-DUD-D-DUDU--` | two-bar majority 0.656 vs 0.660 |
| Fame Instrumental 1 29-35 | `DU--DUx-D-DUDUD-` | `-U--DUxxD-xUD-D-` / `DU--xUD-D-DUDU--` | two-bar majority 0.647 vs 0.632 |
| Fame Verse 2 35-47 | `DU--DUx-D-DUDUD-` | `----DUx-D-DUD-D-` / `DUD-DUD-D-D-DU--` | two-bar majority 0.629 vs 0.611 |
| Fame Instrumental 3 81-85 | `D-DUDUD--U--xU--` | `D--Ux-D--UD-DUD-` / `D-DUDUD--U--xU-U` | two-bar majority 0.632 vs 0.632 |
| Need You Tonight Verse 2 31-48 | `DUD-D-D-DUxU-U-U` | `D---D-D-D--UxU-U` / `DUD-D-D-D-xU-U-U` | two-bar medoid 0.662 vs 0.621 |
| Need You Tonight Chorus 2 48-56 | `DUD-D-DUDUDUxU-U` | `D---D-D-D--UxU-U` / `DUD-DUDU-UDU-U-U` | two-bar majority 0.598 vs 0.620 |
| All Fired Up Verse 2, member 90-97 | `D-D-D-DU` | `xUDxxxx-`, greyed | member's own (agreement 0.31) |

Why: spec 4.2 named the statistic as lag-2 minus lag-1 agreement and quoted figures from two different measurements of the spike. The median (0.034) and 90th percentile (0.204) are the lag statistic's; the count ("seven sections clear it") and A3's figures are the two-bar medoid margin's (the best pair's score minus the one-bar medoid's). The stage was built on the lag statistic. On the planned sections it has a median of 0.030 and a 90th percentile of 0.202, as quoted, and **20 sections clear 0.10**, not seven. The strike floor removed two of those (All Fired Up 110-124 and 124-128), and two others cleared it only over the bars the stage analyses, which leave out trailing bars after the last chord (the Outros of Summer of '69 and Need You Tonight); the stage printed 20 two-bar sections. The fix round below rebuilt the rule on the medoid margin.

Medoid switches: 8 sections keep the medoid (Summer of '69 Verse 2, Chelsea Dagger Chorus 2, Pour Some Sugar On Me Chorus 2 and Chorus 3, Fame Verse 3, All Fired Up Chorus 1 and Outro, Need You Tonight Verse 2); in three of them (Pour Some Sugar On Me Chorus 3, All Fired Up Chorus 1 and Outro) the medoid bar is identical to the majority, so nothing on the page changes. Only three of the eight are among the spike's ten. The stage votes on its own strike classes (struck, muted, rest), which is not exactly the vector the spike read.

**Certainty (first validation).** One section changed state: Summer of '69 Verse 5 (95-111) is certain in 1.6 and was uncertain in 1.5. The chance p is the same (0.027); what moved is the confidence, from 0.43 to 0.57, because a two-bar unit agrees better with the bars than a one-bar vote, which lifted it over the confidence floor. A6 ("no section's state changes") holds for the chance test and not for the state.

## Per song

As measured in the first validation. The fix round left the pages, lines, riff flags and ring flags as they are here and changed the pattern columns as "Fix round after the first validation" lists (Summer of '69: 6 changes, 3 of them two-bar; Chelsea Dagger: 1, now a one-bar medoid; Wet Leg: 1, the riff member; Fame: 2, both one-bar medoids; Need You Tonight: 2; The Cars: 1; Summer of '69's grey bars 14 to 29, since Verse 1 is now uncertain, with the phrase-shifted bar 4 printed in the Intro).

| Song | Planned sections | Pages 1.5 to 1.6 (A14 estimate) | Last page filled to | Lines (one-bar lines) | Grey bars | Pattern changes (two-bar, medoid) | Riff flags | Short sections |
|---|---|---|---:|---|---:|---|---|---|
| Summer of '69 | 12 | 2 to 3 (3) | 0.18 | 20 (2) | 14 | 8 (8 two-bar, 1 of them medoid) | none (Intro, Verse 1 lost) | Intro |
| Chelsea Dagger | 7 | 3 to 3 (3) | 0.21 | 24 (1) | 20 | 1 (two-bar medoid) | none | Intro |
| Pour Some Sugar On Me | 8 | 2 to 3 (3) | 0.39 | 24 (1) | 103 | 1 (medoid) | none | none |
| Wet Leg "mangetout" | 8 | 2 to 2 (2) | 0.56 | 15 (2) | 1 | 0 (Chorus 1 is two-bar with both bars `DUDUDUDU`) | Verse 1, Chorus 3; member 58-65 new | none |
| Fame | 9 | 2 to 3 (3) | 0.18 | 22 (1) | 0 | 6 (5 two-bar, 1 medoid) | all nine | 8 of 9 (Instrumental 3 rings) |
| All Fired Up | 8 | 2 to 2 (3) | 0.94 | 22 (1) | 57 | 1 (member 90-97) | Chorus 1; member 97-104 (Verse 1, Verse 2, Chorus 2 lost) | member 97-104 |
| Need You Tonight | 7 | 2 to 2 (3) | 0.76 | 17 (2) | 18 | 4 (all two-bar, 1 medoid) | the six flagged in 1.5 (all but the Intro) | all seven |
| The Cars | 10 | 3 to 3 (3) | 0.31 | 23 (2) | 4 | 1 (two-bar) | Verse 3 only (7 lost) | Chorus 2, Verse 3 |

"Last page filled to" is the lowest text on the last page as a share of the page height. Three of the four songs that print three pages put a fifth or less on the third: Summer of '69's third page holds only the nine-bar Outro, Fame's only Verse 4, Chelsea Dagger's the end of Chorus 3.

### Summer of '69

**Pages.** Page 1: header, seven diagrams, Intro (four wide bars with the pickup, then bar 4 alone on a line, which phrase alignment moved into the Intro and which prints Verse 1's `xxxxxxxU`), Verse 1, Chorus 1, Verse 2. Page 2: Chorus 2 to Verse 5 ("play twice" on Verse 5's eight-bar line). Page 3: the Outro's nine grey bars.

**Quality.** The bar boxes are clear and the alternating two-bar patterns are easy to see. On eight-bar lines Verse 1's `xxxxxxxU` reads as a row of crossed arrows packed edge to edge; at 110 dpi the crosses are visible but a muted bar and a down bar are hard to tell apart at a glance. The pickup bar (bar 0) draws a sustain line although the Intro is short (item 4 below). The ring flags are right by the strokes on the page: the Intro's muted figure draws no sustain lines; every other section rings.

### Chelsea Dagger

**Pages.** Page 1: header with the key hedge and the strum-uncertain note, seven diagrams, Intro (20 grey bars of `D-x-x-x-` and the black phrase-shifted bar 20), Chorus 1 ("play twice"), Verse 1. Page 2: the last three bars of Verse 1, Chorus 2's two-bar figure, Verse 2, Instrumental, Chorus 3 begins. Page 3: Chorus 3 ends, a fifth of the page.

**Quality.** Verse 2 and Chorus 3 alternate between eight-bar lines of narrow boxes and four-bar lines of wide boxes whenever a two-chord bar falls in the next eight, so the same `D-D-D-D-` looks different from line to line. Chelsea Dagger's Instrumental rings at 4.98 dB, 0.02 under the threshold.

### Pour Some Sugar On Me

**Pages.** Page 1: header, four diagrams, passing, the no-capo and power lines, Intro, Verse 1. Page 2: Chorus 1, Verse 2, Chorus 2, Instrumental. Page 3: Verse 3 and Chorus 3 ("play three times"), two fifths of the page.

**Quality.** Every bar prints its strokes in grey with "pattern uncertain"; the chord names stay black and read well. Sixteenth-grid bars are four to a line and legible. Long sustain lines run through the sparse greyed bars of Verse 3 and Chorus 3; whether these strokes ring is one of the held-bar clips.

### Wet Leg "mangetout"

**Pages.** Page 1: header, three diagrams, Verse 1 ("riff heard, not transcribed"), Chorus 1, Verse 2, Chorus 2, Verse 3 begins. Page 2: Verse 3 ends, Verse 4 ("play 4 times"), Chorus 3 ("riff heard, not transcribed", four wide bars to a line because one bar holds F and a passing C#), Outro ("no strummed instrument detected").

**Quality.** The same page count as 1.5. Verse 4's `DUDUxxDU` on eight-bar lines puts two muted crosses side by side on 10 px slots, where they merge into one dark mark. The repeat says "play 4 times" with a digit; spec 3.1 names only "play twice" and "three times" in words, and the renderer prints digits from four by design.

### David Bowie "Fame"

**Pages.** Page 1: header, three diagrams, passing and no-capo lines, Intro ("play twice"), Verse 1, Instrumental 1. Page 2: Verse 2 to Instrumental 3. Page 3: Verse 4 ("play three times"), a fifth of the page.

**Quality.** Every section says "riff heard, not transcribed". Short strokes print with faint rest dots in the empty slots and no sustain lines, except the pickup bar 0 (item 4) and Instrumental 3, which rings at 4.25 dB. Sixteenth bars at four to a line are readable; adjacent muted strokes (`xx` at the end of Verse 3's bars) merge.

### Pat Benatar "All Fired Up"

**Pages.** Page 1: header, four diagrams, Intro (28 grey bars of `DxxUDUD-` and the black phrase-shifted bar 28 alone on a line), Verse 1 ("play twice"), Chorus 1 ("riff heard, not transcribed"), Verse 2 begins. Page 2: Verse 2 continues (61-90 "play three times"; 90-96 grey `xUDxxxx-` on wide lines; 97-104 black `D-D-D-DU` without sustain lines because that member is short; 104-110), Chorus 2, Verse 3, Chorus 3 (all grey), Outro ("play twice"), filling the page to 0.94.

**Quality.** Two pages as Task 10's smoke run printed, one fewer than the estimate. The Verse 2 member rule shows on the page as intended for 90-97. Within Verse 2 the line width changes four times (eight, four, eight), and the same `D-D-D-DU` appears with sustain lines on 61-90 and without on 97-104; a reader sees three styles of the same figure in one section. The Intro's eight-bar lines of grey `DxxUDUD-` are the densest on any sheet: the two crosses touch.

### INXS "Need You Tonight"

**Pages.** Page 1: header "Key F major (or C major)", four diagrams, passing, the tab legend ("Tab: A E C G top to bottom; numbers are frets. Re-entrant tuning: G is the high string."), Intro (grey), Verse 1 with tab ("riff"), Chorus 1. Page 2: Verse 2, Chorus 2, Verse 3 ("play 5 times"), Outro (grey).

**Quality.** The tab block reads well: the four string lines, the A E C G labels at the left of each line's first bar, the fret numbers on the C line, the stroke row under it in black. The Intro's first eight bars are each a single grey down stroke with a sustain line across the whole bar, on a song whose sections are all short (item 4).

### The Cars "You Might Think"

**Pages.** Page 1: header (title "The Cars - You Might Think", artist "RHINO", as in 1.5), four diagrams, the no-capo line, Intro, Verse 1, Chorus 1. Page 2: Verse 2 to Verse 4 begins (Verse 3 "riff heard, not transcribed"; Instrumental grey). Page 3: Verse 4 ends, Chorus 4.

**Quality.** Several sections break into lines of eight, four and one (Verse 1 is eight, four, one); a one-bar line after an eight-bar line looks like a stray. The Chorus 3 figure `-UDUDUD-` is on the page as the ear accepted it.

## Riff test, gate and tab

The pitch-change share is computed only for sections and members that pass the two 1.5 chroma features. Measured shares: flagged riffs 0.43 to 0.81 (lowest All Fired Up Chorus 1 at 0.43, on 8 onsets); not flagged 0.07 to 0.33 (highest Summer of '69 Intro 0.33, then All Fired Up Verse 2 0.29, the blind song's Verse 3 0.29, The Cars Intro 0.28). The gap that A8 recorded as 0.17 to 0.65 is 0.33 to 0.43 on these runs, and the 0.4 line sits 0.03 above the lowest flagged section.

Gate figures from `riff.json` in the first validation (agreement, support, named share; the gate wants 0.70, 0.75, 0.6); the paragraph under the table gives the figures that moved in the fix round, and the Result column is the current one:

| Song, section or member | Unit | Agreement | Support | Named | Result |
|---|---:|---:|---:|---:|---|
| Need You Tonight Verse 1 13-24 | 1 | 0.739 | 0.777 | 0.942 | **tab**, C string frets 0, 2, 3, no shift |
| Need You Tonight Chorus 1 24-31 | 1 | 0.380 | 0.633 | 0.838 | not transcribed |
| Need You Tonight Verse 2 31-48 | 2 | 0.411 | 0.538 | 0.945 | not transcribed |
| Need You Tonight Chorus 2 48-56 | 1 | 0.339 | 0.688 | 0.838 | not transcribed |
| Need You Tonight Verse 3 56-79 | 2 | 0.171 | 0.364 | 0.850 | not transcribed |
| Need You Tonight Outro 79-86 | 1 | 0.067 | 0.286 | 0.884 | not transcribed |
| Fame, nine sections | 1 or 2 | 0.09 to 0.41 | 0.22 to 0.73 | 0.62 to 0.87 | not transcribed; Instrumental 1 (29-35, the verified wrong figure) 0.391, 0.733, 0.810 |
| All Fired Up Chorus 1 49-55 | 1 | 0.133 | 0.300 | 0.897 | not transcribed |
| All Fired Up member 97-104 | 1 | 0.065 | 0.204 | 0.932 | fails; no phrase; prints its own strokes since the fix round (the section's pattern in the first validation) |
| Wet Leg Verse 1 0-5 | 2 | 0.000 | 0.500 | 0.786 | not transcribed |
| Wet Leg member 58-65 | 2 | 0.111 | 0.429 | 0.818 | fails; no phrase; prints its own strokes since the fix round (the section's pattern in the first validation) |
| Wet Leg Chorus 3 100-108 | 1 | 0.222 | 0.354 | 0.808 | not transcribed |
| The Cars Verse 3 52-68 | 1 | 0.106 | 0.250 | 0.753 | not transcribed |

After the fix round the riff reductions that were two-bar units became one-bar where the two-bar medoid margin does not clear 0.10: Wet Leg Verse 1 now reads 0.062, 0.300, 0.786 and member 58-65 0.097, 0.238, 0.818; Fame Instrumental 1 0.248, 0.450, 0.810 (Fame Verse 2 and Instrumental 3 stay two-bar); Need You Tonight Verse 2 0.430, 0.523, 0.945 and Verse 3 0.241, 0.288, 0.850. Every result is unchanged: only Need You Tonight Verse 1 prints tab, with the same notes.

The printed tab on Need You Tonight's Verse 1, one bar on the sixteenth grid, slot and fret on the C string: 0 (0), 1 (0), 2 (2), 4 (2), 6 (2), 8 (0), 9 (0), 10 (2), 11 (3), 13 (2), 15 (0); the notes are C4, D4 and D#4, the three pitches the ear check passed ("the tones are right"). Against the spike's figure (C C D D C D D# D C) it has one more D (slot 4) and one more C (slot 9). Whether the rhythm is right is for the ear; the clips are prepared. Every tab note is drawn short, since the section is short. Only this one section passes: Need You Tonight's other two verses fail at agreement 0.430 and 0.241, both reduced as one-bar units since the fix round (0.41 and 0.17 as two-bar units in the first validation); whether they play the same part as Verse 1 is for the ear.

## The blind song: The Beatles "Day Tripper"

Chosen by the controller on the owner's behalf for a prominent, steady, single-note riff (A15). Resolved with `uv run yt-dlp "ytsearch1:The Beatles Day Tripper" --get-id --get-title`: id `AYZlME0mQB8`, title "The Beatles - Day Tripper (Official Video)", the first hit and not a cover; its uploader is "Natan Santos", a re-upload of the official film, not the band's channel. Not listened to; the figures are recorded, not judged.

| What | Recorded |
|---|---|
| Run | Exit 0, 287.2 s from the command to the sheet; folder `the-beatles-day-tripper` |
| Title and artist | Title "The Beatles - Day Tripper", artist "Natan Santos": as with The Cars in 1.5, the uploader is not the artist, so the title keeps its prefix and the uploader prints as the artist |
| Tempo, bars | 137.4 bpm (136.4 detected, octave none), 95 bars, 4/4 |
| Key | E major, all three votes E (score margin 0.546, mode margin 0.312); header "Key D major (shapes)", "Capo fret 2", "Sounding key: E major" |
| Chords | 44 events, 8 chord shapes, 1 bar filled; no power-chord events, no power line |
| Sections | 12 grid sections, 12 planned (no merge): Intro 0-11, Chorus 1 11-15, Verse 1 15-26, Instrumental 1 26-30, Chorus 2 30-35, Verse 2 35-46, Instrumental 2 46-52, Verse 3 52-58, Instrumental 3 58-63, Chorus 3 63-68, Verse 4 68-78, Outro 78-95 |
| Strums | Eighth grid, guitar stem (ratio 0.40), grid fit 0.79, no recall boost; 9 of 12 certain (Chorus 1, Chorus 2 and Instrumental 2 uncertain, p 0.244, 0.063, 0.092); 5 two-bar sections; one medoid (Verse 2, `--DUDUDU`, 0.721 vs 0.675) |
| Riff test | No section flagged. Only Verse 3 (52-58) passes the two 1.5 chroma features (entropy 0.71, single share 0.53), and its pitch-change share is 0.29, under 0.4. Every other section's entropy is above the 0.82 ceiling (0.82 to 0.89), and six of them also fall under the 0.45 single share (0.19 to 0.43). `riff.json` is empty; no gate figures, no tab |
| Ring | 7 sections ring, 5 short (Instrumental 1 5.74, Chorus 2 6.28, Instrumental 2 5.10, Instrumental 3 5.86, Verse 4 5.44 dB); 6 of 12 medians within 1 dB of the threshold |
| Pages | 3, the last filled to 0.24 (the Outro) |

**What cannot be verified without listening.** Whether the opening figure is the riff the song is chosen for and the chain heard it as a strum; whether `DUDUDUDU`-like votes with full density on a clean guitar are strums; whether the twelve section names fit the song.

## Ear clips for the listening pass

Under `%TEMP%\youkulele-ear-v16\<song>\`, made by `make_clips.py` in the validation scratch folder. A strum clip (`held_`, `short_`, `shortsection_`, `changed_`, `member_`, `unflagged_`) is the strums stage's source stem (the guitar stem on every song) over the bars named (0-based, end exclusive) with a click on every printed stroke as the score prints it (down 1500 Hz, up 1000 Hz, a muted strike a short noise tick) and a soft low tick on every beat; the click times come from the grid's own beat times, slot by slot. A `tab_` clip is every printed tab bar synthesised as plucked strings (Karplus-Strong, as the riff-pitch spike's `synth_riffs.py`) at the song's own bar and beat times with beat ticks; its `tabover_` twin lays the plucks over the stem.

| Clip | Tests |
|---|---|
| `all-fired-up\held_outro_132.wav` | held strokes drawn with a sustain line (4 held slots): does the strum ring through them? |
| `summer-of-69\held_verse_95.wav` | held strokes drawn with a sustain line (6 held slots): does the strum ring through them? |
| `chelsea-dagger\held_chorus_61.wav` | held strokes drawn with a sustain line (5 held slots): does the strum ring through them? |
| `mangetout\held_verse_18.wav` | held strokes drawn with a sustain line (3 held slots): does the strum ring through them? |
| `the-cars-you-might-think\held_chorus_68.wav` | held strokes drawn with a sustain line (1 held slot): does the strum ring through them? |
| `pour-some-sugar-on-me\held_verse_77.wav` | held strokes drawn with a sustain line (14 held slots, greyed): does the strum ring through them? |
| `need-you-tonight\short_chorus_24.wav` | short strokes, no sustain line (9 empty slots after strokes): are the strokes damped? |
| `need-you-tonight\short_verse_31.wav` | short strokes, no sustain line (5 empty slots after strokes): are the strokes damped? |
| `need-you-tonight\short_verse_56.wav` | short strokes, no sustain line (5 empty slots after strokes): are the strokes damped? |
| `fame\short_instrumental_47.wav` | short strokes, no sustain line (7 empty slots after strokes): are the strokes damped? |
| `fame\short_chorus_61.wav` | short strokes, no sustain line (6 empty slots after strokes): are the strokes damped? |
| `summer-of-69\changed_verse_4-12.wav` | verse 4-19: new printed pattern (two-bar) D-DU-xxx / xxxxxxD-, was xxxUxxxx |
| `summer-of-69\changed_verse_31-39.wav` | verse 31-41: new printed pattern (medoid, two-bar) D--U--D- / DUD-DUD-, was DUDUD-D- |
| `summer-of-69\changed_verse_53-58.wav` | verse 53-58: new printed pattern (medoid) DU-U-UDU, was DU-UDUDU (the ear called 1.5's `DU-UDUDU` wrong: "syncopated 8th notes") |
| `summer-of-69\changed_verse_75-83.wav` | verse 75-83: new printed pattern (two-bar) D-DU-UD- / DU-UD-D-, was DUDUDUD- |
| `summer-of-69\changed_verse_95-103.wav` | verse 95-111: new printed pattern (two-bar) D--U---- / DUDUDUDU, was D--UD-D- |
| `summer-of-69\changed_outro_111-119.wav` | outro 111-121: new printed pattern (medoid) xU--DU--, was x---D--- |
| `chelsea-dagger\changed_chorus_61-69.wav` | chorus 61-71: new printed pattern (medoid) D-D---D-, was D-D-D-D- |
| `pour-some-sugar-on-me\changed_chorus_55-63.wav` | chorus 55-67: new printed pattern (medoid) D---D-DUD---D--U, was ----D---D-D-D--- |
| `mangetout\changed_verse_58-66.wav` | verse 58-100: new printed pattern (member) D-DU-UDU / DUDUxxDU, was DUDUxxDU |
| `fame\changed_chorus_61-69.wav` | chorus 61-71: new printed pattern (medoid) DUDUDUD---D-D-D-, was DUDUDUD---D-DUD- |
| `fame\changed_verse_71-79.wav` | verse 71-81: new printed pattern (medoid) D-DUDUD--UD-DUxx, was D-DUDUD-DUD-DUxx |
| `need-you-tonight\changed_chorus_24-31.wav` | chorus 24-31: new printed pattern (two-bar) D---D---D--UxU-U / D-DUD-DU-UDU-U-U, was D-DUD-DUDUDUxU-U |
| `need-you-tonight\changed_outro_79-86.wav` | outro 79-86: new printed pattern (medoid) DU-U-UDU--DU-U-x, was DU-UDUDUD-xU-UDU |
| `the-cars-you-might-think\changed_instrumental_72-76.wav` | instrumental 72-76: new printed pattern (two-bar) -UD-D-D- / DUD-DUDU, was DUD-DUDU |
| `all-fired-up\member_verse2_55-61.wav` | Verse 2 member 55-61 prints the section's D-D-D-DU (agreement above 0.35) (the ear: "8th notes again with variations") |
| `all-fired-up\member_verse2_90-97.wav` | Verse 2 member 90-97 prints its own greyed xUDxxxx- (agreement below 0.35) (the ear: sparse sustained strums) |
| `all-fired-up\member_verse2_97-104.wav` | Verse 2 member 97-104 is a riff by the test and prints its own xxDxDxDx (fix round ruling), short (the ear: a riff with improvisation) |
| `all-fired-up\member_verse2_104-110.wav` | Verse 2 member 104-110 prints the section's D-D-D-DU (agreement above 0.35) (the ear: improvisation, then the figure) |
| `summer-of-69\shortsection_intro_0-4.wav` | a section of a ringing song flagged short (intro 0-4), drawn without sustain lines: are the strokes damped? |
| `chelsea-dagger\shortsection_intro_0-8.wav` | a section of a ringing song flagged short (intro 0-8), drawn without sustain lines: are the strokes damped? |
| `the-cars-you-might-think\shortsection_chorus2_45-52.wav` | a section of a ringing song flagged short (chorus2 45-52), drawn without sustain lines: are the strokes damped? |
| `the-cars-you-might-think\shortsection_verse3_52-60.wav` | a section of a ringing song flagged short (verse3 52-60), drawn without sustain lines: are the strokes damped? |
| `need-you-tonight\tab_verse_13-24.wav` | Verse 1: every printed tab bar 13-23 as plucks at the song's own tempo; are the notes and rhythm the riff? |
| `need-you-tonight\tabover_verse_13-24.wav` | Verse 1: every printed tab bar 13-23 as plucks at the song's own tempo; are the notes and rhythm the riff? (plucks over the stem) |
| `the-beatles-day-tripper\unflagged_intro_0-8.wav` | blind song intro 0-11 (the opening section, not flagged), printed D-DUDUDU: riff or strum, and do the clicks fit? |
| `the-beatles-day-tripper\unflagged_verse_52-58.wav` | blind song verse 52-58 (passed the two 1.5 chroma features, pitch-change share 0.29 under 0.4), printed DUDUDUDU: riff or strum, and do the clicks fit? |

No section of the blind song is flagged, so there are no riff-section clips for it; the two clips above cover its opening section and the one section the riff test came nearest to flagging. Five held bars were asked for and six are prepared, since The Cars' bar holds only one slot; the Pour Some Sugar On Me bar is greyed. The `shortsection_` clips cover the four sections of ringing songs that the ring flag calls short. The whole set was remade after the fix round, so every `changed_` clip carries the pattern the sheet prints now; the first round's clips for sections that no longer change (Summer of '69 41-53 and 68-75, Fame 17-29, 29-35, 35-47 and 81-85, Need You Tonight 31-48 and 48-56) are gone.

## What to improve next

Ranked by benefit to the person reading the sheet. **After the fix round:** item 1 is done (the rule now fires on six sections, as the spec intended); item 2 is settled by ruling 3 (a riff member prints its own strokes; the header still follows the longest member, so the page names no riff there); item 4 is fixed. The fix round adds items 11 and 12; the final fix wave fixes item 11.

1. **Decide whether two-bar units should fire on 20 sections.** Stage: strums (`music/vote.py`, `PERIOD2_MARGIN`). Evidence: 20 of 69 sections print an alternating pair, against the six the spec expected, and they account for 19 of the 22 pattern changes (11 of them unexpected). The spec's count came from a different statistic (the two-bar medoid winning by 0.10), and the median and 90th percentile it quoted are right for the built statistic. The listening pass on the `changed_` clips decides whether the alternations are real figures (Summer of '69 53-58 now shows the spike's syncopated bar every other bar) or noise that a one-bar print hid. Nothing was tuned; any new margin needs those verdicts.
2. **A riff member that agrees with its section loses its riff on the page.** Stage: score (spec 4.3 against 3.2). Evidence: All Fired Up 97-104 (riff by the test, gate failed, member agreement 0.50) prints the section's `D-D-D-DU` in black with no phrase, and Wet Leg 58-65 the same. The member rule decides strokes, and the header phrase follows the longest member, so a riff inside a merged section can never say "riff heard, not transcribed". Spec 4.3 promised the phrase for 97-104 and the 0.50 agreement in the same paragraph.
3. **The riff test drops a riff the ear heard.** Stage: strums (`PITCH_CHANGE_MIN`). Evidence: All Fired Up Verse 2 (61-90), which the owner calls "the d D D DUD riff", reads 0.29 and loses its flag; the non-riff side now reaches 0.33 and the riff side starts at 0.43, so A8's gap is 0.10 wide, not 0.48. The sheet is not wrong for it (the strokes print, the section says nothing), but the owner's ear and the test disagree on a figure of repeated single notes on one pitch class, which is exactly what a pitch-change share cannot see.
4. **A bar with no detected strokes draws sustain lines in a short section.** Stage: score (`music/score_builder.py`, `_bar_strokes`: `rings = record.strokes[0].rings if record.strokes else True`). Evidence: Need You Tonight's Intro bars 0 to 7 each print one grey down stroke held across the whole bar; Fame's and Summer of '69's pickup bar 0, Chelsea Dagger's Intro bars 5, 6 and 9 to 11 and The Cars' Verse 3 bars 62 and 63 draw sustain lines too, all inside members flagged short. **Fixed in the fix round** (each bar now carries its member's flag). The member's ring flag is the right default. This is a drawing error, not a pattern error (A5's cost).
5. **Section ring medians sit on the threshold.** Stage: strums (`RING_SECTION_DB`). Evidence: 9 of the 68 measured section medians on the eight songs lie within 1 dB of 5 (and 6 of 12 on the blind song), and five sections of ringing songs read short (Summer of '69 Intro 6.01, Chelsea Dagger Intro 12.16, The Cars Chorus 2 12.47 and Verse 3 9.35, All Fired Up member 97-104 7.33) while Fame's Instrumental 3 reads ringing (4.25). Song medians separate as A5 measured; section medians do not. The muted intros of Summer of '69 and Chelsea Dagger may genuinely be short (both print muted figures), which the held and short clips can test.
6. **Line packing breaks sections into mixed widths and stray one-bar lines.** Stage: render (`render/lines.py`). Evidence: twelve one-bar lines across the eight sheets; Chelsea Dagger's Verse 2, All Fired Up's Verse 2 and The Cars' Verse 1 change between eight narrow and four wide boxes inside one section, so the same figure prints in two sizes; a phrase-shifted bar often sits alone on a line (Summer of '69 bar 4, All Fired Up bar 28). The rule is applied as spec 3.1 states it (per line); the cost is visual consistency, which the owner flagged as a question at Task 10.
7. **Adjacent muted strokes merge on 10 px slots.** Stage: render. Evidence: `xx` pairs on eight-bar lines (Wet Leg Verse 4 `DUDUxxDU`, All Fired Up Intro `DxxUDUD-`) and on sixteenth bars (Fame Verse 3) print as one dark mark at 110 dpi; single crosses and arrows are legible. The eight-bar lines otherwise read well and are what holds the page counts (expectation 7).
8. **Read the title and artist when the uploader is not the artist.** Stage: ingest. Evidence: carried from 1.5 (item 1 there) and repeated on the blind song: "The Beatles - Day Tripper" by "Natan Santos". The first thing on the sheet is wrong on both songs the chain had not seen.
9. **Third pages that hold a fifth of a page.** Stage: render. Evidence: Summer of '69 (0.18, the nine-bar Outro), Fame (0.18, Verse 4), Chelsea Dagger (0.21). Page counts are within the expectation; the whole-line repeat mark of A14 already folds what it can (Fame's Verse 4 is "play three times" and still spills).
10. **Carried from 1.5**, unchanged: the sandwich rule unexercised, hedging a close tonic call, pairing sections in `compare_runs` (done in 1.5), correcting late refrain boundaries, sustained strums on sixteenth grids, the mode hedge.
11. **The chance test reads one bar of a two-bar vote.** Stage: strums (`structure_test` on `vote.vector[:slots]`). Evidence: after the fix round Summer of '69 Verse 1 (4-19) is a two-bar unit whose first-bar half is `xxxxxxD-`; that half has a rest, so the section took the shuffle test instead of the density test of a full vote, and the section that was certain in 1.5 prints greyed (p 1.0). Which half is "first" depends on the section's start, not on the music. **Fixed in the final fix wave** (the whole unit vector decides; Verse 1 stays uncertain, now for a reason that does not depend on its start).
12. **A new riff flag now changes strokes on the page.** Stage: strums (ruling 3 meeting row 5). Evidence: Wet Leg's member 58-65, flagged a riff for the first time in 1.6 and never judged by ear, now prints its own `D-DU-UDU` inside a Verse 4 that otherwise prints `DUDUxxDU`. The `changed_verse_58-66` clip covers it.

Not ranked as faults: "play 4 times" and "play 5 times" print digits from four by the renderer's design (spec 3.1 forbids only a bare multiplier); phrase-shifted bars printing their own grid section's strokes (Task 8 ruling), visible as one black bar at the end of a grey Intro on Chelsea Dagger and All Fired Up.

## Assumptions after validation

Every row of spec section 9, with its status after these runs.

| # | Assumption | Status now | Evidence |
|---|---|---|---|
| A1 | `HYBRID_DELTA` 0.04 with a two-strike floor fixes the flattened patterns without regressing ear-right ones | **Held after the fix round; unverified by ear** | No ear-right pattern changed in either round. After the fix round the medoid prints on 11 sections (8 change the page), and 7 of the spike's ten print its medoid bar alone, including Summer of '69 53-58 `DU-U-UDU`, the section the lower edge rests on; the other three are two-bar sections. (In the first validation the lag-based unit bypassed the medoid on 7 of the ten.) Listening pass to judge |
| A2 | A mute tie-break is needed | **Refuted and dropped** (unchanged) | The Cars 52-60 prints `DUDUDUDU` without it, as the assumption pass said |
| A3 | A two-bar unit needs at least two strikes in each bar of the pair | **Measured on the correct statistic after the fix round** | On the two-bar medoid margin (spec 4.2 as amended): 7 of 69 sections clear 0.10 and the floor removes one (All Fired Up 124-128), leaving the spec's six two-bar sections; at 0.08 and 0.15, 8 and 4 clear and 7 and 3 remain. The first validation, on the lag statistic the spec had named, found 20 two-bar sections |
| A4 | `MEMBER_AGREE` 0.35 separates members that share the section's playing from those that do not | **Held on strokes; riff members exempt after the fix round** | All Fired Up 55-61, 61-90, 104-110 and 28-33 print the section's pattern; 90-97 its own, greyed. In the first validation a riff member agreeing above 0.35 (All Fired Up 97-104 at 0.50, Wet Leg 58-65) printed the section's strokes; by the fix-round ruling a riff member prints its own (97-104 `xxDxDxDx`, Wet Leg 58-65 `D-DU-UDU`), and the header still follows the longest member |
| A5 | A section rings when its median stroke decay is under 5 dB per slot | **Measured: song medians hold, section medians do not** | Need You Tonight 7 of 7 short, Fame 8 of 9; four sections and one member of the six ringing songs short; 9 of 68 medians within 1 dB of 5. Ring is decided per member (spec 4.4 as amended), so All Fired Up's 97-104 is short inside a ringing section. Stroke-less bars defaulted to ringing in the first validation; after the fix round every bar carries its member's flag and no bar of a short member draws a sustain line |
| A6 | The chance test behaves the same on a medoid candidate as on a majority | **Held for p on one-bar votes; two state flips via two-bar votes** | Every one-bar section's chance p is identical to 1.5. After the fix round two two-bar sections differ: Summer of '69 Verse 5 flips to certain (two-bar confidence 0.57 clears the floor its one-bar vote of 0.43 did not) and Verse 1 flips to uncertain. The chance p never reads the vote; Verse 1 flipped because the vote's first half decided between the density test and the shuffle test, and pairing from bar 5 moved a half with a rest (`xxxxxxD-`) to the front, so the full-vote density test (certain in 1.5 and the first validation) gave way to the shuffle test (p 1.0; item 11). Since the final fix wave the whole two-bar vector decides (full only when both bars are); Verse 1's vector has rests in both bars, so it stays uncertain whichever bar it starts on |
| A7 | Short sections print their own greyed candidate better than an inherited neighbour's | Unverified by ear | No section inherits: every uncertain section prints its own strokes greyed (Summer of '69 Verse 3, All Fired Up Verse 3 `-------U` and Chorus 3 `D---DUD-`, every Pour Some Sugar On Me section) |
| A8 | `PITCH_CHANGE_MIN` 0.4 separates riffs from strums | **Measured: the gap is 0.33 to 0.43** | Removes both ear-confirmed false positives (All Fired Up 33-49 0.08, The Cars 11-19 0.15); keeps Fame's flags, Need You Tonight's verse and The Cars Verse 3; drops All Fired Up 61-90 (0.29), which the ear calls a riff; Summer of '69 95-111 stays unflagged |
| A9 | `RIFF_AGREE_MIN` 0.70 passes real steady riffs and fails blends | **Held on the verified pair** | Need You Tonight Verse 1 0.739 passes; Fame Instrumental 1 0.391 fails (0.248 after the fix round, voted one-bar; the spike measured 0.52 to 0.62); every other riff section 0.00 to 0.41 in the first validation, 0.06 to 0.43 after the fix round |
| A10 | `RIFF_SUPPORT_MIN` 0.75 | Measured | Verified riff 0.777 (spec 0.80); Fame Instrumental 1 0.733 (0.450 after the fix round) now fails on support as well |
| A11 | `RIFF_NAMED_MIN` 0.6 | Measured, a floor | Verified riff 0.942; every riff section 0.62 to 0.95, so it decided nothing |
| A12 | Pitch at the trusted onsets reproduces the verified notes | **Measured consistent; unverified by ear** | The printed notes are C4, D4 and D#4, the verified pitch set; the figure has one more D and one more C than the spike's; clips prepared |
| A13 | The octave-and-fret mapping gives playable tab | Held on the one riff | C string frets 0 to 3, no shift, as predicted; no other tab printed |
| A14 | Pages stay within one of 1.5 | **Verified** | 21 pages against 18; three songs +1, none +2; equal to the estimate on six songs and one fewer on two. The line pitch on the page is about 17.3 mm for a stroke line and 25.4 mm for a tab line (measured on the 110 dpi rasters), against 17.6 mm assumed; the sixteenth-grid songs gained one page (Pour Some Sugar On Me, Fame) or none (Need You Tonight) |
| A15 | A blind song with a steady single-line riff exists among the owner's choices | **The song exists; the chain did not flag its riff** | "Day Tripper" ran from ingest; no section passed the riff test (one reached the pitch-change step at 0.29), so the blind song tested only the strum side, the cost the spec named |
| A16 | Chords, beats, bars and onsets are untouched by this version | **Verified** | Byte comparison on all eight songs |
| A17 | 1.5 files render under the new page via the rebuilt `bars` | **Verified for reading; not rendered here** | `evaluate` and `evaluate --compare` read all eight 1.5 folders through the rebuilt bars; rendering a 1.5 score is covered by the unit tests on the 1.5 fixture, and no 1.5 folder was rendered in this validation since every folder was re-run from strums |

## README sample

The README's sample image (`docs/images/sample-sheet.png`) was regenerated from the test suite's synthetic 120-bar song (`_realistic_120_bar_score` in `tests/test_stage_render.py`) through the render stage and real Chromium, page 1 rasterised at 110 dpi (`make_sample.py`; 109 kB, two pages). Page 1 shows the Intro (four wide bars from the pickup, then four narrow), Verse 1 and Verse 2 folded to "play twice", the greyed Pre-chorus with "pattern uncertain", and Chorus 1. The README's sample text, its version line, the limitation that spoke of the pattern "beside" a section and the "55-bar" illustration were updated to match.

## Listening pass (owner, 2026-10-06)

The owner listened to all 37 clips the day after the merge. Verdicts are the owner's words.

| # | Clip | Tests | Owner's verdict |
|---|---|---|---|
| 1 | all-fired-up\held_outro_132 | held strokes drawn with a sustain line (4 held slots) | PARTLY: "two notes - syncopated, short note first, long note cut" (the long stroke rings but is cut before the next stroke; the sustain line over four slots overstates it) |
| 2 | summer-of-69\held_verse_95 | held strokes with a sustain line (6 held slots) | YES: "rings through" |
| 3 | chelsea-dagger\held_chorus_61 | held strokes with a sustain line (5 held slots) | PARTLY: "syncopated duu du da and cut on the third note" (the third stroke is cut; the sustain line overstates it) |
| 4 | mangetout\held_verse_18 | held strokes with a sustain line (3 held slots) | NO: "cut" |
| 5 | the-cars-you-might-think\held_chorus_68 | held stroke with a one-slot sustain line | NO: "cut" |
| 6 | pour-some-sugar-on-me\held_verse_77 | greyed pattern, 14 held slots with a sustain line | YES: "a single note - plays through" |
| 7 | need-you-tonight\short_chorus_24 | short strokes, no sustain line (9 empty slots) | NO: "rings" (the song-level short flag is wrong for this chorus) |
| 8 | need-you-tonight\short_verse_31 | short strokes, no sustain line (5 empty slots) | YES: "damped" |
| 9 | need-you-tonight\short_verse_56 | short strokes, no sustain line (5 empty slots) | YES: "damped" |
| 10 | fame\short_instrumental_47 | short strokes, no sustain line (7 empty slots) | YES: "damped" |
| 11 | fame\short_chorus_61 | short strokes, no sustain line (6 empty slots) | damped YES; pattern NO: "too many clicks - i think it's clicking to the higher pitched strumming" (the second, higher guitar) |
| 12 | summer-of-69\changed_verse_4-12 | Verse 1 4-19 new two-bar pattern D-DU-xxx / xxxxxxD- (printed uncertain) | YES: "clicks fit" |
| 13 | summer-of-69\changed_verse_31-39 | verse 31-41 new two-bar medoid D--U--D- / DUD-DUD- (was DUDUD-D-) | NO: "way too many clicks it's a quarter note and then the rest of the measure is a single tone and the clicker is missing this" (one strum then a held tone per bar; both candidates over-strike) |
| 14 | summer-of-69\changed_verse_53-58 | Verse 3 53-58 new medoid DU-U-UDU (1.5 DU-UDUDU was "too fast") | NO: "too many clicks. I think you're clicking 16th notes when it's playing 8th notes" (still too dense; the ear hears eighths, the grid or the clip may be at twice the rate) |
| 15 | summer-of-69\changed_verse_75-83 | verse 75-83 new two-bar D-DU-UD- / DU-UD-D- (was DUDUDUD-) | YES: "clicks fit" |
| 16 | summer-of-69\changed_verse_95-103 | verse 95-111 new two-bar D--U---- / DUDUDUDU (was D--UD-D-) | MOSTLY: "much better except for the very end where there was a single note and then 8th notes rather than the 16th notes you were clicking" (the full bar is at half the clicked density) |
| 17 | summer-of-69\changed_outro_111-119 | outro 111-121 new medoid xU--DU-- (was x---D---) | NO: "too few notes - it was playing the signature riff and you were doing 2 8th notes and then a pause then another 2 8th notes" (the outro is the riff; a strum pattern is the wrong object) |
| 18 | chelsea-dagger\changed_chorus_61-69 | chorus 61-71 new medoid D-D---D- (was D-D-D-D-) | YES: "clicks fit" |
| 19 | pour-some-sugar-on-me\changed_chorus_55-63 | chorus 55-67 new medoid D---D-DUD---D--U (was ----D---D-D-D---), greyed | NO: "wrong" |
| 20 | mangetout\changed_verse_58-66 | Verse 4 member 58-65, newly flagged riff, prints its own D-DU-UDU (never ear-judged before) | NO: "clicks do not fit the riff at all. it's playing a syncopated rhythm and it is 8th notes evenly spaced" (the owner calls it a riff; the printed strokes do not match) |
| 21 | fame\changed_chorus_61-69 | chorus 61-71 new medoid DUDUDUD---D-D-D- (was DUDUDUD---D-DUD-) | NO: "too many clicks" (two guitars in one stem; as clip 11) |
| 22 | fame\changed_verse_71-79 | verse 71-81 new medoid D-DUDUD--UD-DUxx (was D-DUDUD-DUD-DUxx) | NO: "too many clicks" (two guitars in one stem) |
| 23 | need-you-tonight\changed_chorus_24-31 | chorus 24-31 new two-bar D---D---D--UxU-U / D-DUD-DU-UDU-U-U (was D-DUD-DUDUDUxU-U) | NO: "you're using syncopation when it does not exist. it goes 3 1 beat notes, all cut off, and then 9 fast notes" (three quarter-note stabs then a run of nine fast notes; neither bar of the pair is right) |
| 24 | need-you-tonight\changed_outro_79-86 | outro 79-86 new medoid DU-U-UDU--DU-U-x (was DU-UDUDUD-xU-UDU) | MOSTLY: "clicks mostly fit" |
| 25 | the-cars-you-might-think\changed_instrumental_72-76 | instrumental 72-76 new two-bar -UD-D-D- / DUD-DUDU (was DUD-DUDU) | NO: "not enough clicks - they don't fit" (the sparse half under-strikes) |
| 26 | all-fired-up\member_verse2_55-61 | member 55-61 prints the section D-D-D-DU (agreement above 0.35) | MOSTLY: "mostly fits" |
| 27 | all-fired-up\member_verse2_90-97 | member 90-97 prints its own greyed xUDxxxx- (agreement below 0.35) | NO: "completely, hilariously, wrong" (the own vote of a sparse sustained stretch is mutes; grey does not rescue it) |
| 28 | all-fired-up\member_verse2_97-104 | riff member 97-104 prints its own xxDxDxDx, short, unlabelled | NO: "clicks are completely wrong" |
| 29 | all-fired-up\member_verse2_104-110 | member 104-110 prints the section D-D-D-DU | NO: "this is a damped note, a pause, and then 8th notes" (1.5 pass said the end fit; now rejected) |
| 30 | summer-of-69\shortsection_intro_0-4 | intro flagged short inside a ringing song (median 6.01 dB) | NO: "the strokes are not damped" (the short flag is wrong here) |
| 31 | chelsea-dagger\shortsection_intro_0-8 | intro flagged short inside a ringing song (median 12.16 dB) | NO MUSIC: "there is no music in that piece - that's a doorbell" (the stem holds no guitar here; the section should be no-instrument, and 1.4 printed this intro as uncertain/no strum) |
| 32 | the-cars-you-might-think\shortsection_chorus2_45-52 | Chorus 2 flagged short inside a ringing song (median 12.47 dB) | YES: "damped" |
| 33 | the-cars-you-might-think\shortsection_verse3_52-60 | Verse 3 (a riff by ear) flagged short inside a ringing song (median 9.35 dB) | YES: "damped" |
| 34 | need-you-tonight\tab_verse_13-24 | Verse 1 printed tab (C string frets 0 2 3) as plucks at tempo | YES: "that is the pattern. That's the riff." (notes and rhythm both right; the only printed tab of 1.6 is verified) |
| 35 | need-you-tonight\tabover_verse_13-24 | the same tab plucks over the stem | YES: "sits right on it" |
| 36 | the-beatles-day-tripper\unflagged_intro_0-8 | blind intro, not flagged, printed D-DUDUDU | NO: "it's playing a riff and you did not match it" (riff test false negative on a single-note riff; the pattern does not fit either) |
| 37 | the-beatles-day-tripper\unflagged_verse_52-58 | blind verse 52-58, nearest to a riff flag (pcs 0.29), printed DUDUDUDU | RIFF OVER STRUM: "it's a riff with a strum in the background (strum is the low notes, riff is the high notes). the clicks match the strum, not the riff" |

**Tally.** Held strokes: 2 ring through, 4 cut or partly cut (the per-member ring flag is not per-stroke length). Short strokes: 4 damped, 1 rings (Need You Tonight's chorus). Changed patterns: 3 fit, 2 mostly fit, 9 wrong. All Fired Up Verse 2 members: 1 mostly fit, 3 wrong. Short sections inside ringing songs: 2 damped, 1 not damped, 1 holds no guitar at all. Tab: 2 of 2 right. Blind song: both sections are riffs the test did not flag.

**What the pass settles.**

- **The riff path works when the gate passes (A9, A12 verified).** Need You Tonight's Verse 1 tab is the riff, notes and rhythm, and sits on the stem. It is the first transcription the chain has had verified end to end.
- **The strum pattern machinery is the weak link, not the vote alone.** Nine of fourteen changed patterns are wrong, and the complaints repeat across songs: too many clicks (Summer of '69 three times, "clicking 16th notes when it's playing 8th notes"; Fame twice, the clicks follow the higher second guitar), long notes voted into rows of hits (Summer of '69 31-41 "a quarter note and then the rest of the measure is a single tone"), syncopation printed where there is none (Need You Tonight's chorus: "3 1 beat notes, all cut off, and then 9 fast notes"). The onset grid and what counts as a strike need the ear before the vote can help.
- **Sustain lines need per-stroke length (A5 refuted in use).** A section-level ring flag draws lines through slots the player cuts: 4 of 6 held clips. Stroke duration must be measured per onset.
- **The ring threshold is on the wrong side for one section and meaningless for another.** Summer of '69's intro (6.01 dB) is not damped; Chelsea Dagger's intro holds no guitar ("that's a doorbell") and should be a no-instrument section.
- **The riff test misses riffs on one or two pitches and riffs over a strum.** Day Tripper's intro and verse are riffs (the verse a riff over a low strum, and the clicks match the strum); All Fired Up's Verse 2 figure (61-90) was heard as a riff in 1.5 and lost its flag. Wet Leg 58-65 was flagged correctly but its printed strokes do not fit.
- **The member rule's print is only as good as the member's pattern.** 90-97 printing its own vote is "completely, hilariously, wrong"; the sparse sustained stretch comes out as mutes.

**Priorities for 1.7, from the ear.** Per-onset stroke duration instead of a section flag; the onset grid and the recall gate re-examined against these clips (sixteenth versus eighth density); riff detection for repeated-pitch riffs and riff-over-strum; no-instrument detection on sections of drums and bells; then more riff-led songs so the gate's bands rest on more than one verified riff.
