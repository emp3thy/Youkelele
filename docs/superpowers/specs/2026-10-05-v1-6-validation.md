# Version 1.6 validation on eight real songs and one blind song

Date: 2026-10-06. Branch `worktree-v1-6` at `762851b` plus this commit (package version 0.7.0). Checks every expectation in section 8 of `2026-10-05-ukulele-tab-chain-v1-6-design.md` against the kept version 1.5 runs, and runs one song the chain had never seen. Bar and section numbers are 0-based, as in `grid.json`; a range written `55-61` ends before bar 61. "Planned section" means a section of the section plan, which is what the sheet prints; "member" means one of the grid sections a planned section merged. "Pattern changed" means that at least one bar of the section prints a stroke vector different from the one pattern 1.5 printed for the section, as `evaluate --compare` counts it ("patterns changed in N bars"). The ear verdicts quoted are the owner's from the 1.5 listening pass (`2026-10-04-v1-5-validation.md`), which is this version's ear truth; nothing in this record was listened to.

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
| 4 | Need You Tonight's and Fame's sections are short (no sustain lines); every section of the other six rings and shows sustain lines on held strokes; per-section medians recorded and none within 1 dB of the threshold; Pour Some Sugar On Me prints greyed strokes in every section | **No** | Need You Tonight: all seven sections short. Fame: 8 of 9 short; **Instrumental 3 (81-85) rings at 4.25 dB** and draws sustain lines. Of the other six songs' 53 sections, **four are short**: Summer of '69 Intro (6.01 dB), Chelsea Dagger Intro (12.16), The Cars Chorus 2 (12.47) and Verse 3 (9.35); so is All Fired Up's Verse 2 member 97-104 (7.33; the ring flag is decided per member). **Nine** of the 68 measured section medians on the eight songs lie within 1 dB of 5: Chelsea Dagger Instrumental 4.98; Fame Instrumental 3 4.25; Need You Tonight Intro 5.60, Chorus 2 5.87, Verse 3 5.95; The Cars Intro 4.27, Verse 1 4.92, Chorus 1 4.31, Verse 4 4.33 (Summer of '69's Intro at 6.008 is just outside). Stroke-less bars draw sustain lines even in a short section (Need You Tonight Intro bars 0 to 7, Fame bar 0): see "What to improve next", item 4. Pour Some Sugar On Me prints greyed strokes in all eight sections (103 of 103 bars) |
| 5 | Riff flags: All Fired Up 33-49 and The Cars 11-19 lose theirs; every 1.5 flag the ear confirmed stays; nothing new is flagged outside All Fired Up 97-104 | **No** | All Fired Up 33-49 loses its flag (pitch-change share 0.08) and The Cars 11-19 loses its (0.15). Fame's nine, Need You Tonight's six and The Cars Verse 3 (52-68) keep theirs; All Fired Up 97-104 gains one. **All Fired Up Verse 2 (61-90) loses its flag** (0.29), and the owner heard that figure as a riff ("d D D DUD", clip 7 of the 1.5 pass). **Wet Leg's member 58-65 is newly flagged** by the test on its own onsets, outside the expected list; it prints the section's pattern, so the flag does not reach the sheet. Nine other 1.5 flags that the ear never judged also go: Summer of '69 Intro and Verse 1, All Fired Up Chorus 2, The Cars Intro, Chorus 1, Verse 2, Chorus 2, Verse 4 and Chorus 4 (shares 0.07 to 0.33). See "Riff test" below |
| 6 | Tab prints on Need You Tonight's verses and choruses that pass the gate (the verse must), on the C string without an octave shift; Fame, Need You Tonight's intro, The Cars Verse 3 and All Fired Up 97-104 print "riff heard, not transcribed" | **No** | Need You Tonight Verse 1 (13-24) prints tab on all 11 bars: C string, frets 0, 2 and 3, no octave shift (agreement 0.739, support 0.777, named share 0.942). No other section passes. Fame's nine sections and The Cars Verse 3 print "riff heard, not transcribed". **Need You Tonight's Intro prints "pattern uncertain"**: it is not a riff by the test (it fails the 1.5 chroma features, as in 1.5, which never flagged it) and its pattern is uncertain (p 0.989). **All Fired Up 97-104 prints no phrase** (row 3) |
| 7 | Pages at most one more than 1.5 on every song | **Yes** | 3, 3, 3, 2, 3, 2, 2, 3 against 1.5's 2, 3, 2, 2, 2, 2, 2, 3: three songs gain one page, none gains two; 18 pages become 21. Against the A14 estimate (3, 3, 3, 2, 3, 3, 3, 3): equal on six, one fewer on All Fired Up and Need You Tonight |
| 8 | The blind song runs to a sheet with exit 0; its riff flags, gate figures and tab, if any, are recorded, not judged | **Yes** | Exit 0, 287 s, 3 pages; no section flagged riff, so `riff.json` is empty and no tab prints. Figures below |

Scorecard: three met (1, 7, 8), five missed (2 to 6). Nothing was tuned; every miss is recorded here with its figure.

## Pattern changes

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

Why: spec 4.2 says `PERIOD2_MARGIN = 0.10` with "median 0.034, 90th percentile 0.204; seven sections clear it". Recomputed on the planned sections with the stage's own `period_margin`, the median is 0.030 and the 90th percentile 0.202, as the spec says, but **20 sections clear 0.10**, not seven; the seven of the spike were the sections where a two-bar medoid wins by 0.10, a different statistic. The strike floor drops two (All Fired Up 110-124 and 124-128), and the stage prints 20 two-bar sections, because two more (Summer of '69's Outro and Need You Tonight's Outro) clear the margin over the bars the stage analyses (it leaves out trailing bars after the last chord). A3's "the floor removes exactly one near-empty case" therefore describes the spike's statistic, not the built rule.

Medoid switches: 8 sections keep the medoid (Summer of '69 Verse 2, Chelsea Dagger Chorus 2, Pour Some Sugar On Me Chorus 2 and Chorus 3, Fame Verse 3, All Fired Up Chorus 1 and Outro, Need You Tonight Verse 2); in three of them (Pour Some Sugar On Me Chorus 3, All Fired Up Chorus 1 and Outro) the medoid bar is identical to the majority, so nothing on the page changes. Only three of the eight are among the spike's ten. The stage votes on its own strike classes (struck, muted, rest), which is not exactly the vector the spike read.

**Certainty.** One section changed state: Summer of '69 Verse 5 (95-111) is certain in 1.6 and was uncertain in 1.5. The chance p is the same (0.027); what moved is the confidence, from 0.43 to 0.57, because a two-bar unit agrees better with the bars than a one-bar vote, which lifted it over the confidence floor. A6 ("no section's state changes") holds for the chance test and not for the state.

## Per song

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

Gate figures from `riff.json` (agreement, support, named share; the gate wants 0.70, 0.75, 0.6):

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
| All Fired Up member 97-104 | 1 | 0.065 | 0.204 | 0.932 | fails; prints the section's pattern, no phrase |
| Wet Leg Verse 1 0-5 | 2 | 0.000 | 0.500 | 0.786 | not transcribed |
| Wet Leg member 58-65 | 2 | 0.111 | 0.429 | 0.818 | fails; prints the section's pattern, no phrase |
| Wet Leg Chorus 3 100-108 | 1 | 0.222 | 0.354 | 0.808 | not transcribed |
| The Cars Verse 3 52-68 | 1 | 0.106 | 0.250 | 0.753 | not transcribed |

The printed tab on Need You Tonight's Verse 1, one bar on the sixteenth grid, slot and fret on the C string: 0 (0), 1 (0), 2 (2), 4 (2), 6 (2), 8 (0), 9 (0), 10 (2), 11 (3), 13 (2), 15 (0); the notes are C4, D4 and D#4, the three pitches the ear check passed ("the tones are right"). Against the spike's figure (C C D D C D D# D C) it has one more D (slot 4) and one more C (slot 9). Whether the rhythm is right is for the ear; the clips are prepared. Every tab note is drawn short, since the section is short. Only this one section passes: Need You Tonight's other two verses fail at agreement 0.41 and 0.17, both reduced as two-bar units; whether they play the same part as Verse 1 is for the ear.

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

Under `%TEMP%\youkulele-ear-v16\<song>\`, made by `make_clips.py` in the validation scratch folder. A strum clip (`held_`, `short_`, `changed_`, `member_`, `unflagged_`) is the strums stage's source stem (the guitar stem on every song) over the bars named (0-based, end exclusive) with a click on every printed stroke as the score prints it (down 1500 Hz, up 1000 Hz, a muted strike a short noise tick) and a soft low tick on every beat; the click times come from the grid's own beat times, slot by slot. A `tab_` clip is every printed tab bar synthesised as plucked strings (Karplus-Strong, as the riff-pitch spike's `synth_riffs.py`) at the song's own bar and beat times with beat ticks; its `tabover_` twin lays the plucks over the stem.

| Clip | Tests |
|---|---|
| `all-fired-up\held_outro_132.wav` | held strokes drawn with a sustain line (4 held slots): does the strum ring through them? |
| `summer-of-69\held_verse_95.wav` | the same, 6 held slots (Verse 5's `D--U----` bar) |
| `chelsea-dagger\held_chorus_62.wav` | the same, 5 held slots (Chorus 2's two-bar figure) |
| `mangetout\held_verse_18.wav` | the same, 3 held slots |
| `the-cars-you-might-think\held_chorus_68.wav` | the same, 1 held slot (Chorus 3's `-UDUDUD-`) |
| `pour-some-sugar-on-me\held_verse_77.wav` | the same, 14 held slots on a greyed bar (Verse 3) |
| `need-you-tonight\short_chorus_24.wav` | short strokes, no sustain line (9 empty slots after strokes): are the strokes damped? |
| `need-you-tonight\short_verse_48.wav` | the same, 8 empty slots (the phrase-shifted last bar of Verse 2) |
| `need-you-tonight\short_chorus_50.wav` | the same, 8 empty slots |
| `fame\short_instrumental_47.wav` | the same, 7 empty slots |
| `fame\short_instrumental_30.wav` | the same, 6 empty slots |
| `summer-of-69\changed_verse_4-12.wav` | Verse 1: two-bar `D-DU-xxx` / `xxxxxxxU`, was `xxxUxxxx` |
| `summer-of-69\changed_verse_31-39.wav` | Verse 2: two-bar medoid `D--U--D-` / `DUD-DUD-`, was `DUDUD-D-` |
| `summer-of-69\changed_chorus_41-49.wav` | Chorus 2: two-bar `D-DU-UD-` / `D-DUDUD-`, was `D-DUDUD-` |
| `summer-of-69\changed_verse_53-58.wav` | Verse 3: two-bar `DU-U-UDU` / `DUDUDUD-`, was `DU-UDUDU` (the ear called the 1.5 pattern wrong: "syncopated 8th notes") |
| `summer-of-69\changed_instrumental_68-75.wav` | Instrumental: two-bar `D--UDUDU` / `DUDUDUDU`, was `DUDUDUDU` |
| `summer-of-69\changed_verse_75-83.wav` | Verse 4: two-bar `D-DU-UD-` / `DU-UD-D-`, was `DUDUDUD-` |
| `summer-of-69\changed_verse_95-103.wav` | Verse 5: two-bar `D--U----` / `DUDUDUDU`, was `D--UD-D-`; now certain |
| `summer-of-69\changed_outro_111-119.wav` | Outro: two-bar `D--U----` / `-U--D-D-`, was `x---D---` |
| `chelsea-dagger\changed_chorus_61-69.wav` | Chorus 2: two-bar medoid `--D-D-D-` / `D-D---D-`, was `D-D-D-D-` |
| `pour-some-sugar-on-me\changed_chorus_55-63.wav` | Chorus 2: medoid `D---D-DUD---D--U`, was `----D---D-D-D---` |
| `fame\changed_verse_17-25.wav` | Verse 1: two-bar `----DUx-D-DUD-D-` / `DUD-DUD-D-DUDU--`, was `DUD-DUx-D-DUDUD-` |
| `fame\changed_instrumental_29-35.wav` | Instrumental 1: two-bar `-U--DUxxD-xUD-D-` / `DU--xUD-D-DUDU--`, was `DU--DUx-D-DUDUD-` (the ear: "dum dum dum de dum dum de dum") |
| `fame\changed_verse_35-43.wav` | Verse 2: two-bar `----DUx-D-DUD-D-` / `DUD-DUD-D-D-DU--`, was `DU--DUx-D-DUDUD-` |
| `fame\changed_chorus_61-69.wav` | Chorus: two-bar `D-DUD-D-D-D-DUDU` / `DUDUDUD--UD-D-x-`, was `DUDUDUD---D-DUD-` |
| `fame\changed_verse_71-79.wav` | Verse 3: medoid `D-DUDUD--UD-DUxx`, was `D-DUDUD-DUD-DUxx` |
| `fame\changed_instrumental_81-85.wav` | Instrumental 3: two-bar `D--Ux-D--UD-DUD-` / `D-DUDUD--U--xU-U`, was `D-DUDUD--U--xU--`; also the one Fame section drawn ringing |
| `need-you-tonight\changed_chorus_24-31.wav` | Chorus 1: two-bar `D---D---D--UxU-U` / `D-DUD-DU-UDU-U-U`, was `D-DUD-DUDUDUxU-U` |
| `need-you-tonight\changed_verse_31-39.wav` | Verse 2: two-bar medoid `D---D-D-D--UxU-U` / `DUD-D-D-D-xU-U-U`, was `DUD-D-D-DUxU-U-U` |
| `need-you-tonight\changed_chorus_48-56.wav` | Chorus 2: two-bar `D---D-D-D--UxU-U` / `DUD-DUDU-UDU-U-U`, was `DUD-D-DUDUDUxU-U` |
| `need-you-tonight\changed_outro_79-86.wav` | Outro: two-bar `DU-U-UDU--DU-UDx` / `DUx-D-DxDUxUxx-U`, was `DU-UDUDUD-xU-UDU` (bars 84 and 85 are not printed, so they carry beat ticks only) |
| `the-cars-you-might-think\changed_instrumental_72-76.wav` | Instrumental: two-bar `-UD-D-D-` / `DUD-DUDU`, was `DUD-DUDU` |
| `all-fired-up\member_verse2_55-61.wav` | Verse 2 member 55-61 prints the section's `D-D-D-DU` (the ear: "8th notes again with variations") |
| `all-fired-up\member_verse2_90-97.wav` | Verse 2 member 90-97 prints its own greyed `xUDxxxx-` (the ear: sparse sustained strums) |
| `all-fired-up\member_verse2_104-110.wav` | Verse 2 member 104-110 prints the section's `D-D-D-DU` (the ear: improvisation, then the figure) |
| `need-you-tonight\tab_verse_13-24.wav` | every printed tab bar of Verse 1 (13 to 23) as plucks at the song's tempo: are the notes and the rhythm the riff? |
| `need-you-tonight\tabover_verse_13-24.wav` | the same plucks over the guitar stem |
| `the-beatles-day-tripper\unflagged_intro_0-8.wav` | blind song Intro (not flagged), printed `-UDUDUDU` / `D-DUDUDU`: riff or strum, and do the clicks fit? |
| `the-beatles-day-tripper\unflagged_verse_52-58.wav` | blind song Verse 3, the one section that reached the pitch-change step (0.29, under 0.4), printed `DUDUDUDU`: riff or strum? |

No section of the blind song is flagged, so there are no riff-section clips for it; the two clips above cover its opening section and the one section the riff test came nearest to flagging. Five held bars were asked for and six are prepared, since The Cars' bar holds only one slot; the Pour Some Sugar On Me bar is greyed.

## What to improve next

Ranked by benefit to the person reading the sheet.

1. **Decide whether two-bar units should fire on 20 sections.** Stage: strums (`music/vote.py`, `PERIOD2_MARGIN`). Evidence: 20 of 69 sections print an alternating pair, against the six the spec expected, and they account for 19 of the 22 pattern changes (11 of them unexpected). The spec's count came from a different statistic (the two-bar medoid winning by 0.10), and the median and 90th percentile it quoted are right for the built statistic. The listening pass on the `changed_` clips decides whether the alternations are real figures (Summer of '69 53-58 now shows the spike's syncopated bar every other bar) or noise that a one-bar print hid. Nothing was tuned; any new margin needs those verdicts.
2. **A riff member that agrees with its section loses its riff on the page.** Stage: score (spec 4.3 against 3.2). Evidence: All Fired Up 97-104 (riff by the test, gate failed, member agreement 0.50) prints the section's `D-D-D-DU` in black with no phrase, and Wet Leg 58-65 the same. The member rule decides strokes, and the header phrase follows the longest member, so a riff inside a merged section can never say "riff heard, not transcribed". Spec 4.3 promised the phrase for 97-104 and the 0.50 agreement in the same paragraph.
3. **The riff test drops a riff the ear heard.** Stage: strums (`PITCH_CHANGE_MIN`). Evidence: All Fired Up Verse 2 (61-90), which the owner calls "the d D D DUD riff", reads 0.29 and loses its flag; the non-riff side now reaches 0.33 and the riff side starts at 0.43, so A8's gap is 0.10 wide, not 0.48. The sheet is not wrong for it (the strokes print, the section says nothing), but the owner's ear and the test disagree on a figure of repeated single notes on one pitch class, which is exactly what a pitch-change share cannot see.
4. **A bar with no detected strokes draws sustain lines in a short section.** Stage: score (`music/score_builder.py`, `_strokes_for`: `rings = record.strokes[0].rings if record.strokes else True`). Evidence: Need You Tonight's Intro bars 0 to 7 each print one grey down stroke held across the whole bar, Fame's pickup bar 0 and Summer of '69's pickup bar 0 draw sustain lines, all inside sections flagged short. The member's ring flag is the right default. This is a drawing error, not a pattern error (A5's cost).
5. **Section ring medians sit on the threshold.** Stage: strums (`RING_SECTION_DB`). Evidence: 9 of the 68 measured section medians on the eight songs lie within 1 dB of 5 (and 6 of 12 on the blind song), and five sections of ringing songs read short (Summer of '69 Intro 6.01, Chelsea Dagger Intro 12.16, The Cars Chorus 2 12.47 and Verse 3 9.35, All Fired Up member 97-104 7.33) while Fame's Instrumental 3 reads ringing (4.25). Song medians separate as A5 measured; section medians do not. The muted intros of Summer of '69 and Chelsea Dagger may genuinely be short (both print muted figures), which the held and short clips can test.
6. **Line packing breaks sections into mixed widths and stray one-bar lines.** Stage: render (`render/lines.py`). Evidence: twelve one-bar lines across the eight sheets; Chelsea Dagger's Verse 2, All Fired Up's Verse 2 and The Cars' Verse 1 change between eight narrow and four wide boxes inside one section, so the same figure prints in two sizes; a phrase-shifted bar often sits alone on a line (Summer of '69 bar 4, All Fired Up bar 28). The rule is applied as spec 3.1 states it (per line); the cost is visual consistency, which the owner flagged as a question at Task 10.
7. **Adjacent muted strokes merge on 10 px slots.** Stage: render. Evidence: `xx` pairs on eight-bar lines (Wet Leg Verse 4 `DUDUxxDU`, All Fired Up Intro `DxxUDUD-`) and on sixteenth bars (Fame Verse 3) print as one dark mark at 110 dpi; single crosses and arrows are legible. The eight-bar lines otherwise read well and are what holds the page counts (expectation 7).
8. **Read the title and artist when the uploader is not the artist.** Stage: ingest. Evidence: carried from 1.5 (item 1 there) and repeated on the blind song: "The Beatles - Day Tripper" by "Natan Santos". The first thing on the sheet is wrong on both songs the chain had not seen.
9. **Third pages that hold a fifth of a page.** Stage: render. Evidence: Summer of '69 (0.18, the nine-bar Outro), Fame (0.18, Verse 4), Chelsea Dagger (0.21). Page counts are within the expectation; the whole-line repeat mark of A14 already folds what it can (Fame's Verse 4 is "play three times" and still spills).
10. **Carried from 1.5**, unchanged: the sandwich rule unexercised, hedging a close tonic call, pairing sections in `compare_runs` (done in 1.5), correcting late refrain boundaries, sustained strums on sixteenth grids, the mode hedge.

Not ranked as faults: "play 4 times" and "play 5 times" print digits from four by the renderer's design (spec 3.1 forbids only a bare multiplier); phrase-shifted bars printing their own grid section's strokes (Task 8 ruling), visible as one black bar at the end of a grey Intro on Chelsea Dagger and All Fired Up.

## Assumptions after validation

Every row of spec section 9, with its status after these runs.

| # | Assumption | Status now | Evidence |
|---|---|---|---|
| A1 | `HYBRID_DELTA` 0.04 with a two-strike floor fixes the flattened patterns without regressing ear-right ones | **Held for regressions, mostly bypassed by A3** | No ear-right pattern changed. The medoid prints on 8 sections (5 change the page), only 3 of them among the spike's ten; Summer of '69 53-58, the section the lower edge rests on, prints its syncopated bar through a two-bar majority, not through the medoid. Listening pass to judge |
| A2 | A mute tie-break is needed | **Refuted and dropped** (unchanged) | The Cars 52-60 prints `DUDUDUDU` without it, as the assumption pass said |
| A3 | A two-bar unit needs at least two strikes in each bar of the pair | **Measured again: the rule fires far more than recorded** | 20 of 69 sections clear `PERIOD2_MARGIN` on the built statistic (spec: seven); the floor removes two (All Fired Up 110-124, 124-128); 20 sections print as two-bar units. The spec's count was the spike's two-bar-medoid statistic |
| A4 | `MEMBER_AGREE` 0.35 separates members that share the section's playing from those that do not | **Held on strokes; cost found on riffs** | All Fired Up 55-61, 61-90, 104-110 print the section's pattern; 90-97 its own, greyed; Wet Leg 58-65 and All Fired Up 28-33 the section's. A member that is a riff and agrees above 0.35 (97-104 at 0.50, Wet Leg 58-65) prints the section's strokes and no riff phrase |
| A5 | A section rings when its median stroke decay is under 5 dB per slot | **Measured: song medians hold, section medians do not** | Need You Tonight 7 of 7 short, Fame 8 of 9; four sections and one member of the six ringing songs short; 9 of 68 medians within 1 dB of 5. Ring is decided per member, so All Fired Up's 97-104 is short inside a ringing section. Stroke-less bars default to ringing (item 4) |
| A6 | The chance test behaves the same on a medoid candidate as on a majority | **Held for p; one state flip via confidence** | Every chance p identical to 1.5; Summer of '69 Verse 5 flips to certain because its two-bar confidence (0.57) clears the floor its one-bar vote (0.43) did not |
| A7 | Short sections print their own greyed candidate better than an inherited neighbour's | Unverified by ear | No section inherits: every uncertain section prints its own strokes greyed (Summer of '69 Verse 3, All Fired Up Verse 3 `-------U` and Chorus 3 `D---DUD-`, every Pour Some Sugar On Me section) |
| A8 | `PITCH_CHANGE_MIN` 0.4 separates riffs from strums | **Measured: the gap is 0.33 to 0.43** | Removes both ear-confirmed false positives (All Fired Up 33-49 0.08, The Cars 11-19 0.15); keeps Fame's flags, Need You Tonight's verse and The Cars Verse 3; drops All Fired Up 61-90 (0.29), which the ear calls a riff; Summer of '69 95-111 stays unflagged |
| A9 | `RIFF_AGREE_MIN` 0.70 passes real steady riffs and fails blends | **Held on the verified pair** | Need You Tonight Verse 1 0.739 passes; Fame Instrumental 1 0.391 fails (the stage's own figure; the spike measured 0.52 to 0.62); every other riff section 0.00 to 0.41 |
| A10 | `RIFF_SUPPORT_MIN` 0.75 | Measured | Verified riff 0.777 (spec 0.80); Fame Instrumental 1 0.733 now fails on support as well |
| A11 | `RIFF_NAMED_MIN` 0.6 | Measured, a floor | Verified riff 0.942; every riff section 0.62 to 0.95, so it decided nothing |
| A12 | Pitch at the trusted onsets reproduces the verified notes | **Measured consistent; unverified by ear** | The printed notes are C4, D4 and D#4, the verified pitch set; the figure has one more D and one more C than the spike's; clips prepared |
| A13 | The octave-and-fret mapping gives playable tab | Held on the one riff | C string frets 0 to 3, no shift, as predicted; no other tab printed |
| A14 | Pages stay within one of 1.5 | **Verified** | 21 pages against 18; three songs +1, none +2; equal to the estimate on six songs and one fewer on two. The line pitch on the page is about 17.3 mm for a stroke line and 25.4 mm for a tab line (measured on the 110 dpi rasters), against 17.6 mm assumed; the sixteenth-grid songs gained one page (Pour Some Sugar On Me, Fame) or none (Need You Tonight) |
| A15 | A blind song with a steady single-line riff exists among the owner's choices | **The song exists; the chain did not flag its riff** | "Day Tripper" ran from ingest; no section passed the riff test (one reached the pitch-change step at 0.29), so the blind song tested only the strum side, the cost the spec named |
| A16 | Chords, beats, bars and onsets are untouched by this version | **Verified** | Byte comparison on all eight songs |
| A17 | 1.5 files render under the new page via the rebuilt `bars` | **Verified for reading; not rendered here** | `evaluate` and `evaluate --compare` read all eight 1.5 folders through the rebuilt bars; rendering a 1.5 score is covered by the unit tests on the 1.5 fixture, and no 1.5 folder was rendered in this validation since every folder was re-run from strums |

## README sample

The README's sample image (`docs/images/sample-sheet.png`) was regenerated from the test suite's synthetic 120-bar song (`_realistic_120_bar_score` in `tests/test_stage_render.py`) through the render stage and real Chromium, page 1 rasterised at 110 dpi (`make_sample.py`; 109 kB, two pages). Page 1 shows the Intro (four wide bars from the pickup, then four narrow), Verse 1 and Verse 2 folded to "play twice", the greyed Pre-chorus with "pattern uncertain", and Chorus 1. The README's sample text, its version line, the limitation that spoke of the pattern "beside" a section and the "55-bar" illustration were updated to match.
