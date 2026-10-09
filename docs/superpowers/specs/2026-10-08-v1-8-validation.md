# Version 1.8 validation on eleven songs and one blind song

Date: 2026-10-09. Branch `worktree-v1-8` at `87db38d` (package version 0.9.0), then one fix round at `5734e6d` (the harness, not the chain). Checks every expectation in section 12 of `2026-10-08-ukulele-tab-chain-v1-8-design.md` against the kept version 1.7 runs of the eleven songs (the ten of the 1.7 validation and Cream "Badge", its blind song). Bar and section numbers are 0-based, as in `grid.json`; a range written `55-61` ends before bar 61. "Planned section" means a section of the section plan, which is what the sheet prints; "member" means one of the grid sections a planned section merged. A bar "rests" when its `strums.json` record has `rests` true; it "holds" otherwise. "Grey" means the bar's record is uncertain and prints grey. Every figure below is traceable to a file under `%TEMP%\youkulele-v18-validation\` (named in "Where the figures live"). The new blind song, The Housemartins "Happy Hour", ran from ingest at `c23cbe8` once the owner gave its URL (see "Blind song").

## Runs and baselines

Each of the eleven run folders under `runs\` was copied whole to `%TEMP%\youkulele-v18-validation\baseline\<folder>\` before any re-run (`setup.py`). The eight known songs were then re-run in place `--from harmony`, and The Cars, Day Tripper and Badge `--from ingest`, one at a time, each with its manifest's source URL and `--runs-dir C:\Users\gethi\sources\Youkulele\runs` (`rerun.py`; logs under `logs\<folder>.txt`). Every run exited 0.

The chain writes `source_meta.json` only when it names a new folder: `layout.resolve_run_dir` returns early for a folder it finds by manifest, so a re-run of an existing folder keeps the 1.7 file with its five fields. Before each ingest re-run, `refresh_meta.py` ran the two lines `resolve_run_dir` runs for a new folder (`fetch_metadata`, then `METADATA_FIELDS` to `source_meta.json`), so the three blind-song folders hold a fresh fetch. Ingest takes `uploader`, `uploader_id` and `channel` from the download's own info dict either way, so the credits would have resolved the same without it.

| Song | Folder | From | Wall time | Exit |
|---|---|---|---:|---|
| Summer of '69 | `summer-of-69` | harmony | 30.6 s | 0 |
| Chelsea Dagger | `chelsea-dagger` | harmony | 26.4 s | 0 |
| Pour Some Sugar On Me | `pour-some-sugar-on-me` | harmony | 38.8 s | 0 |
| Wet Leg "mangetout" | `mangetout` | harmony | 29.7 s | 0 |
| David Bowie "Fame" | `fame` | harmony | 35.7 s | 0 |
| Pat Benatar "All Fired Up" | `all-fired-up` | harmony | 36.1 s | 0 |
| INXS "Need You Tonight" | `need-you-tonight` | harmony | 28.6 s | 0 |
| AC/DC "You Shook Me All Night Long" | `you-shook-me-all-night-long` | harmony | 29.5 s | 0 |
| The Cars "You Might Think" | `the-cars-you-might-think` | ingest | 132.2 s | 0 |
| The Beatles "Day Tripper" | `the-beatles-day-tripper` | ingest | 120.8 s | 0 |
| Cream "Badge" | `cream-badge` | ingest | 116.8 s | 0 |

Every manifest records 0.9.0 for the stages that ran. The run folder names are unchanged (the re-runs found each folder by its manifest).

Measurement: `measure.py` compares each re-run with its baseline (`grid.json` and the audio and stems byte for byte; the chord events, the chords file less `key`, `bar_onsets`, the plan and `riff.json` value for value; every bar's rest flag and figures; every bar's printed row and certainty in `strums.json` and `score.json`, grouped by member; every planned section's vote and gate figures; the key; the credits and the "uploaded by" line; the pickup bars; the PDF page counts; the legend lines). `probe.py` re-runs the 1.8 strums stage in-process on each folder and records every member's figures (the stage writes them only for each planned section's longest member); its `strums.json` is byte-identical to the run's on all eleven, so the figures are the run's. `members.py` compares the members' certainty with the 1.7 validation's probe files. `summarise_truth.py` pools the `evaluate --truth` scores over the eleven songs. `evaluate_all.py` saves `evaluate --truth` on every re-run and `evaluate <baseline> --compare <re-run>`. `sweeps.py` runs `scripts/band_sweep.py` for the seven constants on the re-runs.

## Expectations from spec section 12

Written before the runs, as the spec states them; checked after (figures after the fix round).

| # | Expectation | Met? | Figure |
|---|---|---|---|
| 1 | `grid.json` and `bar_onsets` byte-identical to 1.7 on all eleven songs; chord events identical except the tonic votes | **Partly** | Eight known songs and Badge: `grid.json` byte-identical, `bar_onsets`, the plan and the chord events identical, the chords file identical apart from `key`. **The Cars and Day Tripper (from ingest): `bar_onsets`, the plan, beats, bars and sections identical, but `grid.json` and two chord events are not byte-identical.** Their `audio.wav` is byte-identical to 1.7's; the six stems are not (the separator's float output differs run to run); `grid.json` differs in `backbeat_ratio` (1e-7) and `bar_vocal_db` (at most 1e-3 dB), and two filled chord events' `confidence` (at most 1.4e-4); every label, time, beat and bar is the same. Badge, also from ingest, came out byte-identical |
| 2 | Rests: Chelsea Dagger 7 and 12, The Cars 63 and Pour Some Sugar On Me 80 rest; Pour Some Sugar On Me 7 holds; the 25 ear-confirmed resting bars still rest; none of the 98 ear-confirmed playing bars rests; the ten 1.7 songs' resting bars number 54; no other flag changes | **Yes** | Exactly five flags change, the five named: Chelsea Dagger 7 (ratio 0.0503 to 0.0064) and 12 (0.0619 to 0.0222), The Cars 63 (0.1330 to 0.0004) and Pour Some Sugar On Me 80 (0.0546 to 0.0335) rest; Pour Some Sugar On Me 7 holds (0.0499 to 0.0502). Resting bars on the ten 1.7 songs: 51 to 54 (Badge: none). **All 25 ear-confirmed resting bars still rest and all 98 ear-confirmed playing bars hold**: no flag but the five named changes (see "Rests"), and those five are the flags the assumption pass measured on the same end-trimmed window when it found 25 of 25 rests resting and 98 of 98 playing bars holding (spec 4.1, A1). Against the truth files' 132 scored bars: 0 of 90 playing bars rest, 41 of 42 resting bars rest, the one held being Pour Some Sugar On Me 7 (labelled `tail`, the cost spec 4.1 names). The clips for bars 7 and 80 are cut (Ear clips 1 and 2) |
| 3 | Certainty: Need You Tonight 0-13 (its bars 8-12), The Cars 72-76, Summer of '69 0-4 and Chelsea Dagger 7-19 print grey; no ear-passed range of spec 5.7 changes vector or certainty; no other member changes vector or certainty; `evaluate --truth` on the 24 judged ranges reports 8 wrong ranges still certain and 4 right ranges grey, each named | **Partly** | The four print grey: Need You Tonight 8-12 `D-D-D-DUD--UD--U` one-bar (confidence 0.503, all-bars 0.193, p over all bars 0.989); The Cars 72-76 `-UD-D-D-` one-bar (p 0.067); Summer of '69 0-4 (3 voted bars); Chelsea Dagger 13-19 `D-xxxUx-` (all-bars confidence 0.325) with 7 and 12 now resting. None of the thirteen ear-passed ranges moves. **Two other members move**: Pour Some Sugar On Me 67-77 greys (p 0.047 on its holding bars, 0.051 over all bars: spec 4.4, predicted by A6 as the third 1.7 flip but missing from 5.7's list), and Pour Some Sugar On Me 0-11's vector moves from `-UDUDUDUDUD-D-D-` to `DUDUDUDUDUD-D-DU`, grey both ways, because bar 7 now holds and joins the vote. On the 24 judged ranges: **7 of 16 wrong ranges certain** (from 9 on the 1.7 baseline) and **3 of 8 right ranges grey** (3 on the baseline as well), named under "Truth scores" |
| 4 | Badge's Verse 1, Chorus 1, Instrumental 2, Chorus 2 and Verse 2 print grey under "guitar not separated here" with no riff flag; its Intro and Instrumental 1 print as 1.7 printed them; no other song's gate fires; the four figures are written on every member | **Partly** | All five fire (bass ratio 0.0007 to 0.0020, own share 0.422 to 0.864) and print grey under the phrase with no riff flag (the 1.7 "riff heard" on Verse 1 and Verse 2 is gone, and their `riff.json` sections with it); Intro and Instrumental 1 print as 1.7 (bar 0, the pickup, now draws as a partial box). No member of the other ten songs fires. **The figures are written on 100 of 101 members**: Wet Leg's silent Outro 108-113 carries none (a silent member is not measured), and `strums.json` stores each planned section's figures, which are its longest member's; the shorter members' figures are the probe's |
| 5 | Badge's key is G major or E minor with the other as its hedge; the lead tonic of the other ten runs is unchanged; the three printed hedges are unchanged | **Yes** | Badge: "G major (or E minor)", decided by the set (best 0.995 against the decided tonic's 0.756, margin 0.238), mode margin 0.644. The other ten leads are unchanged. Hedges unchanged on Chelsea Dagger (D major), Need You Tonight (C major) and AC/DC (D major; a fourth 1.7 hedge the spec's count left out); Badge's 1.7 hedge A major is replaced by E minor, by design |
| 6 | The Cars by The Cars, Day Tripper by The Beatles, Badge by Cream, each with an "uploaded by" line; the eight known songs' credits unchanged and no "uploaded by" line on any of them; the run folder names unchanged | **Yes** | "You Might Think" by The Cars, uploaded by RHINO (`@rhino`); "Day Tripper" by The Beatles, uploaded by Natan Santos (`@goldsongs7948`); "Badge" by Cream, uploaded by Gñåf Ütøpìe (`@GnafUtopie`); title and artist decided by rung 2 (`title`) on all three. The eight known songs print as 1.7 with no "uploaded by" line. Folder names unchanged. The eight known songs re-ran from harmony, so their ingest records are 1.7's and the channel test was not exercised on them (All Fired Up's `@PatBenatarVEVO` case rests on Task 9's unit tests) |
| 7 | The six pickup bars print as partial bars: Summer of '69 and The Cars empty, All Fired Up and You Shook Me with one down stroke, Badge with the strokes it plays (spec 12 wrote "riff strokes"; its Intro carries no riff flag), Fame as the rest rule decides; page counts recorded against 1.7 | **Partly** as first measured; **met in print** after the fix wave | All six draw as partial boxes with the "pickup" label. Summer of '69: two columns, empty (rests, ratio 0.0025). As first measured: Badge, six columns, its Intro member's pattern squeezed, `D U x U D x`; Fame, four columns, holds (ratio 0.338), prints `D U D U`; **The Cars prints a down and an up stroke, not an empty box**: bar 0 holds at ratio 0.956 (stem RMS 0.021 against the mix's 0.022 in the bar: the stem carries nearly all the mix there); **All Fired Up and AC/DC print a down and an up stroke, not one down stroke**: a holding pickup printed its member's voted pattern squeezed onto its columns (`pickup_column`), whose second cell lands on the up column. **After the fix wave** (a holding pickup prints its own quantised onsets on its columns): All Fired Up `D` (grey) and AC/DC `D`, one down stroke each; The Cars empty (it holds, but its own row has no onset); Fame empty (it holds, its own row has no onset); Badge `D D x x` on columns 2, 4, 5 and 7 (its own row `D--UxU-x`). Pages 1.7 to 1.8: 3, 3, 3, 2, 3, 2 to **3**, 2, 2, 3, 3, 2 (All Fired Up gains a page: its 1.7 last page was filled to 0.94 and its third page now holds the Outro); the fix wave moves no page count. See "Fix wave after the final review" |
| 8 | Every sheet carries the two legend lines | **Yes** | Both lines, verbatim, once on each of the eleven sheets |
| 9 | `evaluate --truth` runs on all eleven truth folders and prints every line of 9.2; its totals on the 1.7 baseline runs are recorded before any change | **Yes** | Exit 0 on all eleven, before and after; every block prints (patterns with voted bars, margin and certainty; riffs; rests; key; credits; the four bass-gate figures on each section line). Baseline totals in "Truth scores", saved before any re-run (`evaluate-baseline\`) |
| 10 | The blind song runs to a sheet with exit 0; its figures recorded, not judged | **Yes** | The Housemartins "Happy Hour": exit 0 from ingest, 74 bars, A# major, 4 planned sections (Intro and Outro grey, Chorus and Instrumental certain), no riff flag, bass gate off, "uploaded by MiNaNi", 2 pages. Figures in "Blind song" |

Scorecard on rows 1 to 10: six met (2, 5, 6, 8, 9, 10), four partly met (1, 3, 4, 7), none missed. Nothing was tuned. Row 1 is partly met because a re-run from ingest re-runs the separator, whose output is not bit-stable; row 3 because the bar-7 hold and spec 4.4 move two members the expectation's list does not name, and the judged-range counts are 7 and 3 against the expectation's 8 and 4 (false certain: 5.7's "9 to 8" conflicts with its own list, which greys two judged ranges; false grey: the scorer's 1.7 baseline is 3, and the records do not identify the spec's fourth range; see "Truth scores"); row 4 because a silent member has no figures and shorter members' figures are not written; row 7 because The Cars' pickup holds and a holding pickup printed its member's squeezed pattern. After the fix wave row 7 is met in print (see "Fix wave after the final review"); the scorecard keeps the first measurement.

## Fix round

**Finding.** `evaluate --truth` read each judged range's printed row and certainty from the range's first bar. A resting bar prints an empty black row and is not uncertain (nothing was guessed), so a range whose first bar now rests counted as printed certain although every stroke it prints is grey. On the re-runs two judged ranges start on a bar that 1.8 rests: Pour Some Sugar On Me 80-84 (bar 80 rests, 81-83 print grey) and Chelsea Dagger 7-19 (bar 7 rests, 8-19 print grey). The first round therefore reported 9 of 16 wrong ranges certain, with both counted. A harness defect, not a threshold: Task 11's report had named the case as not occurring on 1.7 runs.

**Fix** (commit `5734e6d`): `truth.score_patterns` reads a range from its first bar that holds; a range whose bars all rest reads its first bar as before; a two-bar figure moved by an odd number of bars has its two bar strings swapped so it is compared in the printed rows' phase. Covering test `tests/test_truth.py::test_score_patterns_reads_a_range_from_its_first_bar_that_holds`. Full suite: 971 passed.

**Exposure and re-run.** The fix touches no stage, so no song was re-run; `evaluate_all.py` was run again on all eleven. Only the Chelsea Dagger and Pour Some Sugar On Me outputs differ from the first round (both ranges now grey, false certain 0 on each); the other nine are byte-identical. The 1.7 baseline totals are unchanged by the fix (no 1.7 range starts on a resting bar). `band_sweep.py` uses the same scorer, so the sweeps below are after the fix. The first round's outputs are kept as `evaluate-round1\` and `truth-totals-rerun.txt`.

## Rests

Rest flags that changed (all five predicted by spec 4.1; no other bar on the eleven songs changes):

| Song | Bar | 1.7 | 1.8 | Ratio 1.7 to 1.8 | Low share 1.7 to 1.8 | Member and print |
|---|---:|---|---|---|---|---|
| Chelsea Dagger | 7 | holds | rests | 0.0503 to 0.0064 | 0.348 to 0.0001 | Intro 0-20: empty row (was `D-xxxUx-`) |
| Chelsea Dagger | 12 | holds | rests | 0.0619 to 0.0222 | 0.369 to 0.162 | Intro 0-20: empty row |
| The Cars | 63 | holds | rests | 0.1330 to 0.0004 | 0.280 to 0.252 | Verse 3 52-68: empty row (was `DUDUDUDU`) |
| Pour Some Sugar On Me | 80 | holds | rests | 0.0546 to 0.0335 | 0.326 to 0.197 | Verse 3 77-84: empty row; the member now votes on 3 bars |
| Pour Some Sugar On Me | 7 | rests | holds | 0.0499 to 0.0502 | 0.954 | Intro 0-11: prints the intro's grey row; the vote now reads it |

Resting bars per song, 1.7 to 1.8: Summer of '69 2 to 2 (0, 120), Chelsea Dagger 9 to 11, Pour Some Sugar On Me 15 to 15, Wet Leg 12 to 12, Fame 0, All Fired Up 1 to 1 (114), Need You Tonight 10 to 10, AC/DC 0, The Cars 1 to 2 (62, 63), Day Tripper 1 to 1 (94), Badge 0. On the ten 1.7 songs, 51 to 54. Since only the five flags above change, and they are the five the assumption pass's measurement on the same window changed, every one of the 25 ear-confirmed resting bars still rests and every one of the 98 ear-confirmed playing bars holds (spec 4.1). Near the floor on the 1.8 window, only Pour Some Sugar On Me 7 (0.0502) lies within 0.01 of 0.05 (`measure\<song>.txt`).

**The rest-floor sweep on the 1.8 figures** (`sweeps\REST_RATIO_MIN.txt`; per-bar rest F pooled over the seven songs with rest truth): F 0.895 at 0.02, 0.976 at 0.03, 0.988 from 0.035 to 0.05 (one false hold, Pour Some Sugar On Me 7), 1.000 from 0.055 to 0.07, 0.988 at 0.075 and falling to 0.923 at 0.10 (false rests). Held out, six songs' bands are 0.055 to 0.07 (Chelsea Dagger's 0.055 to 0.075) and Pour Some Sugar On Me's is 0.03 to 0.07; 0.05 lies outside six of seven bands. On the 1.7 window the same sweep peaked at 0.065 to 0.07 with 0.05 at F 0.976 (Task 12): the new window moves the flat region down to start at 0.055 and lifts 0.05 by one bar. The whole difference between 0.05 and the peak is one bar, Pour Some Sugar On Me 7, two ten-thousandths over the floor; its stem-alone clip is cut. `REST_LOW_SHARE_MIN` reads F 0.988 from 0.002 to 0.02, flat, and 0.005 lies inside every held-out band. Neither constant was moved.

## Certainty and the vote

Members whose printed vector, unit or certainty changed (`measure\<song>.txt`, `members.txt`):

| Song, member | Bars whose row changed | 1.7 | 1.8 | Why |
|---|---|---|---|---|
| Need You Tonight 0-13 | 8-12 | two-bar `D---D---D---D---` / `D-D---DU---U---U`, black | one-bar `D-D-D-DUD--UD--U`, grey | 5.1: two pairs; confidence 0.503 under the sixteenth floor 0.53, all-bars 0.193, all-bars p 0.989 |
| The Cars 72-76 | 72, 74 | two-bar `DUD-DUDU` / `-UD-D-D-`, grey | one-bar `-UD-D-D-`, grey | 5.1: two pairs; p 0.067 |
| Summer of '69 0-4 | 1-3 | `D-xx-xxx`, black | the same, grey | 5.4: 3 voted bars |
| Chelsea Dagger 0-20 | 7-9, 12-19 | `D-xxxUx-`, black | 7, 12 empty (rest); the rest `D-xxxUx-`, grey | 4.4: confidence 0.569 on the holding bars, 0.325 over all bars |
| **Pour Some Sugar On Me 67-77** | 69-76 | `DUDUxUDU-UDUDUDU`, black | the same, grey | 4.4: p 0.047 on the holding bars, 0.051 over all bars (confidence 0.548 and 0.505 against 0.53). A6 named it as the third 1.7 flip; 5.7 and expectation 3 did not list it |
| **Pour Some Sugar On Me 0-11** | 1-7 | 1-6 `-UDUDUDUDUD-D-D-`, grey; 7 empty | 1-7 `DUDUDUDUDUD-D-DU`, grey | bar 7 now holds and joins the vote (seven bars); the 1.6 row returns |
| Pour Some Sugar On Me 77-84 | 80 | `D-----D----U----`, grey | empty (rests) | the member votes on 81-83 and stays grey (now also by 5.4) |
| The Cars 52-68 | 63 | `DUDUDUDU` | empty (rests) | rest |
| Badge 4-28, 34-50, 56-61 | all their bars | black | grey | spec 6 (gate); 50-56 and 61-70 were grey already |

The thirteen ear-passed ranges of spec 5.7 (Summer of '69 4-19, 75-83, 95-111; Chelsea Dagger 61-71; Need You Tonight 13-24, 79-86; Wet Leg 26-32; All Fired Up 33-49, 55-61, 61-90, 128-132; The Cars 11-19, 68-72) keep their vector and certainty. Certain voiced members, 1.7 to 1.8: **75 to 68 of 100** (spec 5.7 predicted 72 before Badge's gate). The seven: Need You Tonight 0-13 and Summer of '69 0-4 (spec 5), Chelsea Dagger 0-20 and Pour Some Sugar On Me 67-77 (4.4), Badge 4-28, 34-50 and 56-61 (spec 6).

`top2_margin` is written on all 100 voiced members (-0.125 to 0.159); it decides nothing (spec 5.5).

**`riff.json` gate figures that moved** (Task 3's ruling: `unit_and_phase`'s pair floor also reaches `riff_line.py`'s reduction): one section on the eleven songs, Fame section 7 (bars 81-85, two pairs): unit 2 to 1, candidate majority to medoid, agreement 0.412 to 0.148, support 0.706 to 0.393, reason "agreement 0.41 < 0.70" to "agreement 0.15 < 0.70"; it printed no tab before or after. Badge's Verse 1 and Verse 2 sections leave `riff.json` because the gate removes their riff flag. Every other `riff.json` is byte-identical to 1.7, including Need You Tonight's: the tab on Verse 1 13-24 is identical (agreement 0.739, support 0.777, named 0.942).

The pattern sweeps (`sweeps\`; false certain plus false grey over all 39 pattern lines): `PERIOD2_MIN_PAIRS` flat at 17 errors from 1 to 6 (no judged range sits on a member it alone decides); `MIN_SLOT_SUPPORT` 17 at 1 and 2, 18 at 3 and 4 (held out, The Cars' best is 4, so 2 lies outside one band); `MIN_VOTE_BARS` 17 from 2 to 4, 18 at 5 and 6, 4 inside every held-out band. None moved.

## The bass-on-stem gate

Figures over each member's analysed span, from the probe (`members.txt`); the gate wants bass ratio at or under 0.05 and own low share at or over 0.40.

| Member | Bass stem ratio | Own low share | Mix low share, bass / source | Gate | Print |
|---|---:|---:|---|---|---|
| Badge Intro 0-4 | 0.548 | 0.878 | 0.304 / 0.375 | off | as 1.7, `DUDxDUDx` black |
| Badge Verse 1 4-28 | 0.0020 | 0.864 | 0.000 / 0.756 | **on** | grey, "guitar not separated here" |
| Badge Instrumental 1 28-34 | 0.0113 | 0.223 | 0.001 / 0.867 | off | as 1.7, "riff heard, not transcribed" (the bridge arpeggio; the gate's known miss) |
| Badge Chorus 1 34-50 | 0.0007 | 0.544 | 0.000 / 0.424 | **on** | grey, "guitar not separated here" |
| Badge Instrumental 2 50-56 | 0.0010 | 0.422 | 0.000 / 0.215 | **on** | grey, "guitar not separated here" |
| Badge Chorus 2 56-61 | 0.0010 | 0.595 | 0.000 / 0.311 | **on** | grey, "guitar not separated here" |
| Badge Verse 2 61-70 | 0.0008 | 0.462 | 0.000 / 0.234 | **on** | grey, "guitar not separated here" |

**Bands on the 1.8 spans.** Among members whose bass ratio is at or under 0.05: own share 0.422 to 0.864 on the five gated Badge members, against at most 0.376 elsewhere (Summer of '69 0-4; then Badge's bridge 0.223, Pour Some Sugar On Me 0-11 0.070, AC/DC 0-16 0.036). **The own-share band is 0.376 to 0.422, 0.046 wide**, narrower than the assumption pass's 0.376 to 0.462 (0.086): Instrumental 2 reads 0.422 over its whole analysed span. Among members whose own share is at or over 0.40: bass ratio 0.0007 to 0.0020 on Badge against at least 0.317 elsewhere (All Fired Up 104-110), as spec 6 measured. The gate sweeps over the two `bleed` ranges of the truth files: `OWN_LOW_SHARE_MIN` reads F 1.000 from 0.38 to 0.46 (a false gate on Summer of '69 0-4 below 0.38, Verse 2 missed above 0.46), and every held-out band contains 0.40 but Badge's (with Badge held out nothing is positive, as spec 6 says); `BASS_STEM_MAX` reads F 1.000 from 0.01 to 0.40. The three unjudged gated members are not labelled in the truth files, so the sweep cannot see Instrumental 2's 0.422.

## Key

| Song | 1.7 | 1.8 | Set best / decided | Decided by |
|---|---|---|---|---|
| Badge | D major (or A major) | **G major (or E minor)** | G 0.995 / D 0.756 | set |
| Fame | F major | F major | A# 0.988 / F 0.981 (0.008) | agreement |
| the other nine | unchanged | unchanged | margin 0.000 | as 1.7 |

The other nine leads: Summer of '69 D major, Chelsea Dagger G major (or D major), Pour Some Sugar On Me C# minor, Wet Leg C major, All Fired Up G major, Need You Tonight F major (or C major), AC/DC G major (or D major), The Cars D major, Day Tripper E major. The re-runs from ingest moved The Cars' and Day Tripper's mode margins by under 1e-6.

## Credits

| Song | 1.7 header | 1.8 header | Rung | `uploader_id` | Provenance line |
|---|---|---|---|---|---|
| The Cars | "The Cars - You Might Think" by RHINO | "You Might Think" by The Cars | title | `@rhino` | uploaded by RHINO |
| Day Tripper | "The Beatles - Day Tripper" by Natan Santos | "Day Tripper" by The Beatles | title | `@goldsongs7948` | uploaded by Natan Santos |
| Badge | "Cream - Badge" by Gñåf Ütøpìe | "Badge" by Cream | title | `@GnafUtopie` | uploaded by Gñåf Ütøpìe |
| the eight known songs | unchanged | unchanged | (1.7 record) | not fetched | none |

The three fresh `source_meta.json` files hold all twelve `METADATA_FIELDS`; `artist`, `artists` and `track` are null on all three, so rung 1 is absent and rung 2 decides.

## Pickup bars and pages

| Song | Pickup | Columns | 1.7 printed | 1.8 first measured (member's pattern squeezed) | Own quantised row | 1.8 after the fix wave | Rest rule |
|---|---|---:|---|---|---|---|---|
| Summer of '69 | bar 0, one beat | 2 | empty | empty partial box | `--------` | empty partial box (not re-run) | rests (0.0025) |
| The Cars | bar 0, one beat | 2 | `DUDUDUDU` | `D U` on its two columns | `--------` | empty partial box | holds (0.956) |
| All Fired Up | bar 0, one beat | 2 | `DxxUDUD-`, grey | `D U`, grey | `D-------` | `D` on column 6, grey | holds (0.992) |
| AC/DC | bar 0, one beat | 2 | `--DUDUDU` | `D U` | `D-------` | `D` on column 6 | holds (1.006) |
| Fame | bar 0, one beat | 4 | 11 strokes over the full box | `D U D U` | `----------------` | empty partial box | holds (0.338) |
| Badge | bar 0, three beats | 6 | `DUDxDUDx` | `D U x U D x` | `D--UxU-x` | `D D x x` on columns 2, 4, 5, 7 | holds (0.345) |

Pages per sheet, 1.7 to 1.8: Summer of '69 3 to 3, Chelsea Dagger 3 to 3, Pour Some Sugar On Me 3 to 3, Wet Leg 2 to 2, Fame 3 to 3, **All Fired Up 2 to 3**, Need You Tonight 2 to 2, AC/DC 2 to 2, The Cars 3 to 3, Day Tripper 3 to 3, Badge 2 to 2.

**Fix wave after the final review.** The final whole-branch review found that the squeeze above is time-correct only for a pickup bar's own quantised row (the quantiser spreads a pickup's `n` slots over its short duration), not for its member's pattern, which is in full-bar time; it ruled that a holding pickup bar prints its own quantised onsets mapped onto its columns, the first stroke on a column kept and its down or up re-read from the column (spec 3.2 amendment; commit "fix(score): a holding pickup bar prints its own quantised onsets on its columns"). The score and render stages were re-run (`--from score`, `--runs-dir C:\Users\gethi\sources\Youkulele\runs`, `rerun.py` with `TAG=finalfix`, logs `logs\<folder>-finalfix.txt`) on the five songs whose pickup bar holds: All Fired Up, AC/DC, The Cars, Fame and Badge; each exited 0. Their pickups now print: All Fired Up `D` on column 6, grey; AC/DC `D` on column 6; The Cars nothing (an empty box: the bar holds by the rest rule, but its own row holds no onset); Fame nothing (likewise); Badge `D` on column 2, `D` on column 4, `x` on 5 and `x` on 7 (its own row's `U` at cell 3 lands on the down column 4, and its `U` at cell 5 shares column 5 with the earlier `x`). Pages: All Fired Up 3, AC/DC 2, The Cars 3, Fame 3, Badge 2, all as first measured. All Fired Up and AC/DC now print the one down stroke the assumption pass heard; The Cars and Fame print the empty box the expectation named for The Cars. Each pickup's chord still starts on the same column (6, 6, 6, 12 and 2), and the full bars print as before, since only a pickup bar's stroke source changed; no other stage re-ran, so no other figure in this record moves. Ear clips 4 to 6 were cut against the first print; their questions about the audio (does the guitar play, how many strokes) stand. The figures in the table's "first measured" column, in "Recorded, not tuned" items 4 and 5 and in A10 are kept as they were measured.

## Truth scores

`evaluate --truth` pooled over the eleven songs (`truth-totals-baseline.txt`, `truth-totals-rerun-fix1.txt`; per song in `evaluate-baseline\` and `evaluate\`). The truth files hold 39 pattern lines: the reviews' 24 judged ranges (1.6 clips 12-29 and 1.7 clips 9-14: 8 YES or MOSTLY, 16 NO), six ear-passed ranges with no clip (YES), and nine ear verdicts the reviews did not count (AC/DC's six, Badge's two verses, Day Tripper's intro). Three keys rest on "general knowledge, confirm" (Summer of '69, Day Tripper, AC/DC).

| Score | 1.7 baseline | 1.8 re-run | 1.8 re-run, truth after the listening pass (twelve songs) |
|---|---|---|---|
| Judged 24: wrong ranges printed certain | 9 of 16 | **7 of 16** | 7 of 14 (two NO verdicts superseded: Need You Tonight 8-13 now MOSTLY, Pour Some Sugar On Me 1-6 now YES) |
| Judged 24: right ranges printed grey | 3 of 8 | 3 of 8 | 5 of 10 (adds Need You Tonight 8-13 and Pour Some Sugar On Me 1-6, both grey) |
| All pattern lines: false certain | 16 of 24 | 13 of 24 | 14 of 24 (47 lines; adds Happy Hour 17-21) |
| All pattern lines: false grey | 4 of 15 | 4 of 15 | 8 of 23 (adds the two above and Happy Hour 2-5 and 44-52) |
| Riff flags | 28 ranges, 19 riff or mixed; 15 flagged, 12 hits: precision 0.800, recall 0.632 | 13 flagged, 12 hits: **precision 0.923**, recall 0.632 | 35 ranges, 21 riff or mixed; 13 flagged, 12 hits: precision 0.923, recall 0.571 |
| Rests | 132 bars: 40 hits, 0 false rests, 2 false holds (Chelsea Dagger 7, 12): F 0.976 | 41 hits, 0 false rests, 1 false hold (Pour Some Sugar On Me 7): **F 0.988** | 210 bars: 44 hits, 0 false rests, 3 false holds (Pour Some Sugar On Me 7, The Cars 0, Happy Hour 1): F 0.967 |
| Key | 8 songs: 7 same, Badge 0.5 (fifth): mean 0.938 | **8 same: mean 1.000** | 9 same: mean 1.000 |
| Credits | 8 of 11 | **11 of 11** | 12 of 12 |

The third column scores the same runs against the truth files as the listening pass left them (`truth-totals-listening.txt`); its changes come from the verdicts, not from the chain.

Wrong ranges still certain on the 1.8 re-run, by name: Summer of '69 31-39, Wet Leg 58-66, Fame 61-69 and 71-79, All Fired Up 97-104 and 104-110, Need You Tonight 24-31. Those leaving the 1.7 list: Chelsea Dagger 7-19 and Need You Tonight 8-13. Right ranges grey: Summer of '69 4-12 (YES), Pour Some Sugar On Me 19-27 (MOSTLY), Need You Tonight 79-86 (MOSTLY). Against spec 5.7's prediction of 8 of 16 and 4 of 8, the two counts differ for different reasons. **False certain: the baseline matches the spec** (5.7's "from 9", and the scorer counts 9 on the 1.7 runs), so the gap of 7 against 8 is in the delta: two ranges left the list where 5.7's arithmetic, "fall from 9 to 8", has one. That arithmetic conflicts with 5.7's own list of greyed members, which names both Need You Tonight 0-13 (holding the judged range 8-13) and Chelsea Dagger 7-19; both turned grey as listed, so 7 is what the list predicts. **False grey: the gap is in the baseline**: the scorer counts 3 right ranges grey on the 1.7 runs where 5.7 says 4. The records do not identify the spec's fourth range: of the other five right ranges (Summer of '69 75-83 and 95-103, Chelsea Dagger 61-69, Wet Leg 26-33, All Fired Up 55-61), every holding bar prints certain on the 1.7 runs, so no reading by first bar or by any bar makes one of them grey. The likeliest source is the pattern review's 25-range set (it counts 25 judged ranges where the clips give 24), but no record names the range. Neither count moved because of a right range lost: no right range changed certainty. The remaining seven false-certain rows are the onset failures spec 5.7 assigns to 1.9. Outside the judged 24, AC/DC's five NO ranges and Day Tripper 0-8 stay certain; Badge 4-12 leaves the list (grey under the gate); All Fired Up 128-132 (YES) stays grey.

## Ground truth from published sources

The rows this version changed against the 1.7 sources table (`2026-10-06-v1-7-validation.md`, "Ground truth from published sources"); no new source was fetched in this pass.

| Item | Chain, 1.8 | Published source (1.7 table) | Agree? |
|---|---|---|---|
| Chelsea Dagger 7 and 12 rest | empty | Songsterr: guitar from tab bar 9 (chain bar 8), staccato stabs | agrees on 7 (before the guitar enters); 12 is inside the stabs, as 10 and 11 were, which the owner's 1.7 clip heard silent on the stem |
| The Cars 63 rests | empty | Songsterr: tab bar 63 has no guitar note at all | agrees |
| Pour Some Sugar On Me 80 rests | empty | Songsterr: tab bars 79 on both guitars on chords, a lead line arriving | contradicts; ear clip 2 |
| Pour Some Sugar On Me 7 holds | grey intro row | Songsterr: tab bars 7-10 no guitar in either track | contradicts; ear clip 1 |
| The Cars pickup 0 | `D U` | Songsterr: rhythm guitar from tab bar 1 (palm-muted dyads) | says nothing on the pickup; the assumption pass said silent; ear clip 4 |
| Badge's five gated members | grey, "guitar not separated here" | Songsterr s4135: a chord guitar from bar 1, bass and piano from bar 5 | agrees that the stem's line is not the guitar part; ear clips 7 to 16 |
| Badge key G major (or E minor) | | the 1.7 researcher's reading of the tab: G major or E minor | agrees |
| The three credits | as above | the artists and titles named in the truth files | agree |

## Ear clips

Cut on 2026-10-09 from the 1.8 run folders (`clips\make_clips_v18.py`; files under `%TEMP%\youkulele-ear-v18\<song>\`, listing `listing-v18-validation.md`). Stem-alone clips are the source stem, not normalised, with half a second of the preceding bar first; click clips are the stem with a click on each printed stroke and a tick on each beat. Pour Some Sugar On Me 67-77 and Summer of '69 0-4 were not re-cut: their vectors are byte-identical to the rows the 1.7 clip 8 and the 1.7 assumption clip `a3_intro_0-4` judged, and only their colour changed. Clips 20 to 26 are the blind song's (`clips\make_clips_blind.py`). The 26 clips, the question each asked and the owner's verdicts are in "Listening pass" below.

## Listening pass (owner, 2026-10-09)

Verdicts are the owner's words, recorded as given. "Bars" lists the clip's bars inclusive; the bar times inside each clip are in the listing's notes. Clips 4 to 6 were cut and asked about the pickups as first measured (a holding pickup then printed its member's squeezed pattern); the fix wave above changed what the pickups print, and the verdicts are read against both.

| # | Clip | Bars | What it tests | Verdict |
|---|---|---|---|---|
| 1 | `pour-some-sugar-on-me\rest_pssom_intro_6-9_stem.wav` | 6-8 | bar 7 now holds at 0.0502 and prints the grey intro row; the tab calls it empty | "no guitar in bar 7." |
| 2 | `pour-some-sugar-on-me\rest_pssom_verse3_79-82_stem.wav` | 79-81 | bar 80 now rests; 1.7 printed three strokes in its last slots | "bar 80 is silent." |
| 3 | `the-cars-you-might-think\rest_cars_bridge_62-65_stem.wav` | 62-64 | bar 63 now rests | "yes. no guitar on bar 63." |
| 4 | `the-cars-you-might-think\pickup_cars_0-2_stem.wav` | 0-1 | the pickup holds (ratio 0.956); the assumption pass said silent | "no." (no guitar in the pickup) |
| 5 | `all-fired-up\pickup_afu_0-2_stem.wav` | 0-1 | how many strokes in the one-beat pickup | "there are 6 strokes in total. it's syncopated: duuu de duuu de duuu de." The clip holds the pickup and the whole of bar 1 (bar 1 from 0.4 s), and the verdict does not say how many sit before bar 1's downbeat: the pickup's own count is unsettled |
| 6 | `you-shook-me-all-night-long\pickup_acdc_0-2_stem.wav` | 0-1 | as 5 | "one" (one stroke in the pickup) |
| 7 | `cream-badge\gated_badge_chorus1_34-42_stem.wav` | 34-41 | gated, not judged before: bass line, guitar, or both on the stem | "both - guitar playing the main riff and bass in background (guitar high notes, bass quite low)." |
| 8 | `cream-badge\gated_badge_instrumental2_50-56_stem.wav` | 50-55 | as 7 | "both. Same thing - guitar high, bass low." |
| 9 | `cream-badge\gated_badge_chorus2_56-61_stem.wav` | 56-60 | as 7 | "both" |
| 10 | `cream-badge\gated_badge_verse1_4-12_stem.wav` | 4-11 | as 7 (1.7 heard the bass carrying the line) | "both, just as you describe. Bass carrying the melody and guitars cut-off single notes." |
| 11 | `cream-badge\gated_badge_verse2_61-70_stem.wav` | 61-69 | as 7 | "both - with the added complication that there is a lead guitar playing a solo and a rhythm guitar playing short, cut-off notes (solo is higher notes, cut off notes are lower)." |
| 12 | `cream-badge\gated_badge_chorus1_34-42_clicks.wav` | 34-41 | the grey strokes, said to be the bass line's rhythm: what do the clicks follow | "clicks follow the guitar riff. Missing the second note of the guitar riff but otherwise perfect." |
| 13 | `cream-badge\gated_badge_instrumental2_50-56_clicks.wav` | 50-55 | as 12 | "neither." |
| 14 | `cream-badge\gated_badge_chorus2_56-61_clicks.wav` | 56-60 | as 12 | "I think it's trying to follow the rhythm guitar - the clip has bass, lead guitar doing the solo in the first half with rhythm guitar playing in background and then lead guitar stops and rhythm guitar continues." |
| 15 | `cream-badge\gated_badge_verse1_4-12_clicks.wav` | 4-11 | as 12 | "It's not really following either - it does a strange click click click-click-click. I think it's mixing bass and guitar riffs. Again - guitar high, bass low." |
| 16 | `cream-badge\gated_badge_verse2_61-70_clicks.wav` | 61-69 | as 12 | "the clip is a mix of lead guitar doing a solo, rhythm guitar doing cut off notes and the bass. The clicks are going pause click-clock-click pause click-clock-click, which doesn't match any of the rhythms being played." |
| 17 | `pour-some-sugar-on-me\changed_pssom_intro_1-8.wav` | 1-7 | now `DUDUDUDUDUD-D-DU` grey, from bar 7 joining the vote | "The first 14 seconds are absolutely correct but at 16 seconds it keeps on clicking when it goes silent. The rhythm changes at 14 seconds and it keeps the same clicks even though the rhythm has changed." (bars 1-5 run 0.5 to 14.6 s; bar 6 from 14.6 s, bar 7 from 17.5 s) |
| 18 | `the-cars-you-might-think\changed_cars_instrumental_72-76.wav` | 72-75 | now one-bar `-UD-D-D-` grey | "clicks don't fit. You've got two guitars playing - a guitar solo (higher notes) and a rhythm guitar in the background." |
| 19 | `need-you-tonight\changed_nyt_intro_8-13.wav` | 8-12 | now one-bar `D-D-D-DUD--UD--U` grey | "it almost has it - it is D D D DUDUDUDUD." |
| 20 | `happy-hour\blind_rest_pickup_0-2_stem.wav` | 0-1 | blind song: the two-beat pickup bar 0 rests (ratio 0.0008) | "no - completely silent." |
| 21 | `happy-hour\blind_intro_0-5.wav` | 0-4 | blind song: Intro `D-DUDUD-D--UD-DU` grey, no riff flag; the tab has a single-note lead over the chords | "yes - that's right. the music doesn't start until 4 seconds in but the clicks are correct when the music starts." (bar 1 runs 1.8 to 4.3 s, bar 2 from 4.3 s) |
| 22 | `happy-hour\blind_chorus1_5-13.wav` | 5-12 | blind song: Chorus `D-DU--D-D-DUDUD-` certain | "yes. something weird happens to the clicks at around 13 seconds for a half-second but it recovers after that, but overall exactly right." (13 s is in bar 10) |
| 23 | `happy-hour\blind_verse_17-24.wav` | 17-23 | blind song: the verse member prints the section's row, certain | "up until 7 seconds in it's just randomly clicking very quickly. At around 8 seconds it starts to fit." (bars 17-20 run 0.5 to 5.8 s, bar 21 5.8 to 8.2 s, bar 22 from 8.2 s) |
| 24 | `happy-hour\blind_chorus2_24-32.wav` | 24-31 | blind song: second chorus, the same row | "yes. coping with changes in beat as well. excellent." |
| 25 | `happy-hour\blind_instrumental_40-44.wav` | 40-43 | blind song: Instrumental `DUDUD-D-DUDUD-D-` certain | "mostly right - it plays that 3 times and then there's a long chord and then it resumes the pattern - it keeps on clicking over the long chord with the (now incorrect) rhythm but then it returns to the pattern and it gets it right." |
| 26 | `happy-hour\blind_outro_44-52.wav` | 44-51 | blind song: Outro `D---D-D-D-D-D---` grey | "the clicks fit." |

**Tally.** Rests and pickups (clips 1 to 6 and 20): the chain is right on four (Pour Some Sugar On Me 80 and The Cars 63 rest; AC/DC's pickup prints one stroke after the fix wave; Happy Hour's pickup rests), wrong on two (Pour Some Sugar On Me 7 and The Cars' pickup hold with no guitar), and one is unsettled (All Fired Up's pickup). Badge's stems (7 to 11): "both" on all five, a guitar part high and the bass low. Badge's grey clicks (12 to 16): one follows the guitar riff (Chorus 1), one the rhythm guitar (Chorus 2), three follow neither or a mix. Changed rows (17 to 19): none right, two partly right (Pour Some Sugar On Me's intro right on bars 1-5, Need You Tonight 8-12 "almost"), one wrong (The Cars 72-76). The blind song's sections (21 to 26): four right (Intro from where the music starts, both choruses, Outro), one mostly right (Instrumental), one half right (Verse: wrong on 17-20, right from 22).

**What the pass settles.**

*Rests.* Every flag the 1.8 window changed toward rest is right by ear (Chelsea Dagger 7 and 12, heard silent by the 1.7 clip 6; Pour Some Sugar On Me 80; The Cars 63), and the one it changed toward hold is wrong: Pour Some Sugar On Me 7 has no guitar, so the hold at 0.0502 that spec 4.1 named as a cost is now a judged false hold, a bar the 1.7 window rested at 0.0499. Two more bars hold with no guitar: The Cars' pickup (ratio 0.956, the stem and the mix both near silence there) and Happy Hour's bar 1 (ratio 0.076; the music starts at bar 2). With the truth files as the pass leaves them, the rest-floor sweep reads F 0.967 at 0.05 (three false holds) and 0.978 from 0.055 to 0.07 (two: The Cars 0 and Happy Hour 1, which no floor in the band rests); eight of nine held-out bands exclude 0.05 (`sweeps\REST_RATIO_MIN.txt`). Not tuned.

*Pickups.* AC/DC's pickup is one stroke, which is what it prints since the fix wave (one `D`); The Cars' pickup is silent, and since the fix wave it prints no stroke, though its bar still holds; Happy Hour's is silent and rests; All Fired Up's count is unsettled (its clip ran into bar 1).

*The gate.* The gate fired on sections whose stem holds a guitar part and the bass together, not the bass alone: the header "guitar not separated here" is honest, but the claim that the grey strokes are the bass line's rhythm is wrong. On Chorus 1 they follow the guitar riff (one note missed), on Chorus 2 the rhythm guitar, and on Instrumental 2 and both verses neither part or a mix of them. Spec 3.3 and the README limitation line are corrected to say the strokes follow whatever the stem holds.

*Changed rows.* Need You Tonight 8-12's one-bar row, grey, is almost the owner's "D D D DUDUDUDUD" (now MOSTLY, and grey: a false grey). Pour Some Sugar On Me's intro row is right on bars 1-5 and wrong on 6-7, where the rhythm changes and then stops; the row prints unchanged over both. The Cars 72-76 is a solo over a rhythm guitar (`mixed`), and its row fits neither.

*The blind song.* The chain's strum rows are right on most of "Happy Hour": the Intro (from where the music starts), both choruses and the Outro fit, the Instrumental fits except over one long chord, and the Verse fits from bar 22 after random fast clicks on bars 17-20. Two of its right rows print grey (Intro bars 2-4 and the Outro: false greys); its Verse prints certain where the first four bars are wrong (a false certain); and bar 1, silent, holds and prints the intro row.

## Recorded, not tuned

1. **Pour Some Sugar On Me 7 holds at 0.0502** and prints the intro's grey row. Clip 1: "no guitar in bar 7.", so it is a judged false hold, the cost spec 4.1 named; the 1.7 window rested it at 0.0499.
2. **Pour Some Sugar On Me 0-11's vector moves** because bar 7 holds and joins the vote; still grey, so no certainty claim moves. Clip 17.
3. **Pour Some Sugar On Me 67-77 greys by spec 4.4** (p 0.051 over all bars), as A6 predicted and 5.7 did not list. Its 1.7 verdict (a two-part passage, the clicks fitting the riff only) makes grey the more honest print.
4. **The Cars' pickup holds** (ratio 0.956, the stem carrying nearly all the mix in the bar) where the assumption pass called it silent; clip 4 hears no guitar, so the bar is a false hold. Since the fix wave it prints no stroke (it has no onset). **Happy Hour's bar 1 holds at 0.076** and prints the grey intro row, and clip 21 places the music's start at bar 2: a third false hold. Both are near-silent bars where the ratio of two quiet signals is not small.
5. **A holding one-beat pickup prints a down and an up**: the member's pattern squeezed onto two columns puts the second half of the bar on the up column (All Fired Up, AC/DC, The Cars). The assumption pass heard one down stroke on All Fired Up and AC/DC. This followed the Task 7 ruling that a pickup prints its member's pattern; the fix wave replaced it with the bar's own onsets. Clip 6 hears one stroke on AC/DC (it now prints one `D`); clip 5 leaves All Fired Up's count unsettled (the clip ran into bar 1).
6. **The own-share band is 0.046 wide, not 0.086**: Badge's Instrumental 2 reads 0.422 over its analysed span. The gate still fires on exactly the five members; the next blind song widens or kills the band.
7. **Wet Leg's silent Outro carries no bleed figures**, and shorter members' figures are not written to `strums.json` (only each planned section's longest member's); spec 6 says every member. The requirement stays unmet in 1.8 (expectation 4 partly met); the probe's `members.txt` holds every member's figures for this validation. A per-member record in `strums.json` (the four figures and the gate for each member, silent ones included) is the fix a later version needs.
8. **A re-run from ingest is not bit-stable**: the separator's float output differs between runs of the same audio, which moves two grid diagnostics and two chord confidences by under 1e-3 on The Cars and Day Tripper; nothing the sheet prints moved because of it.
9. **All Fired Up's sheet gains a page** (2 to 3): its Outro moves to a third page.
10. **The gated strokes are not the bass line's rhythm.** Spec 3.3 said the grey strokes under "guitar not separated here" are the bass line's rhythm; the listening pass (clips 7 to 16) hears a guitar part high and the bass low on the stem in all five gated sections, and the clicks follow the guitar riff on Chorus 1, the rhythm guitar on Chorus 2, and neither part or a mix on Instrumental 2 and both verses. The header is honest; the stroke claim is wrong. Spec 3.3 (amendment) and the README limitation line now say the strokes follow whatever the stem holds. The gate, its constants and its figures are unchanged.
11. **A row prints unchanged over a bar whose own rhythm departs from it**: Pour Some Sugar On Me's intro row is right on bars 1-5 and is printed over bars 6-7, where the rhythm changes and then stops (clip 17); Happy Hour's Instrumental row is printed over a long chord (clip 25).
12. **Happy Hour's verse bars 17-20 click at random, fast** (clip 23) under a certain row; the section prints certain because its longest member, 24-40, passes.

## Assumptions after validation

| # | Assumption | Status now | Evidence |
|---|---|---|---|
| A1 | The end-trimmed window rests Chelsea Dagger 7 and 12, keeps the confirmed rests and rests no confirmed playing bar | **Held, with one judged false hold** | Exactly the five predicted flags move; 54 resting bars on the ten 1.7 songs. By ear the four new rests are right (clips 2, 3 and the 1.7 clip 6) and the one new hold is wrong: clip 1 hears no guitar in Pour Some Sugar On Me 7, which the 1.7 window and the floor had right (0.0499) and the trimmed window lifts to 0.0502. Spec 4.1's named cost is now a judged cost of one bar. On the truth files after the pass: 0 false rests over every playing bar, 3 false holds (Pour Some Sugar On Me 7, The Cars 0, Happy Hour 1); the sweep reads F 0.967 at 0.05 and 0.978 from 0.055 to 0.07, eight of nine held-out bands excluding 0.05. Spec 4.5 not changed: nothing is tuned, and the two other false holds are near-silent bars no floor in the band rests |
| A2 | An attack statistic tells a carried tail from a new stroke | **Refuted** (unchanged) | Not built; Pour Some Sugar On Me 7, a tail by the truth files, holds at 0.0502 by the floor alone |
| A3 | A top-two margin separates heard-right from heard-wrong ranges | **Refuted** (unchanged) | Written on all 100 voiced members (-0.125 to 0.159); not used |
| A4 | 5.1, 5.2 and 5.4 change only Need You Tonight 0-13, The Cars 72-76 and Summer of '69 0-4, and no ear-passed range | **Held** | Exactly those three move by section 5 (`members.txt`); no ear-passed range moves. 5.4 also binds on Pour Some Sugar On Me 77-84 (three voted bars once bar 80 rests), grey already. The pair floor moves one `riff.json` gate figure set (Fame 81-85) and no tab. `PERIOD2_MIN_PAIRS` sweeps flat over 1 to 6 on the truth files. By ear: Need You Tonight 8-12's one-bar grey row is "almost" right (clip 19, MOSTLY), and The Cars 72-76's one-bar grey row still does not fit (clip 18: a solo over a rhythm guitar) |
| A5 | The gate fires on the Badge members whose stem carries the bass and on no other member | **Held as a gate; its meaning revised by ear; band narrower** | By ear (clips 7 to 16) every gated section's stem holds a guitar part high and the bass low, not the bass alone: the gate finds "guitar not separated" correctly, but the grey strokes follow the guitar riff (Chorus 1), the rhythm guitar (Chorus 2) or a mix (the other three), not the bass line's rhythm (Recorded, not tuned, item 10). The truth files now label all five `bleed`, and the gate sweep scores F 1.000 over 0.38 to 0.42 on them (missed above 0.42 by Instrumental 2). Earlier figures: | Fires on Badge 4-28, 34-50, 50-56, 56-61, 61-70 and nothing else of 101 members; own-share band 0.376 to 0.422 (**0.046 wide**), bass-ratio band 0.002 to 0.317; the bridge 28-34 (own 0.223) is the known miss. Ear clips 7 to 16. The blind song "Happy Hour" lands far from both bands (own share at most 0.080, bass ratio at least 0.368) and does not fire, so the bands are unchanged |
| A6 | 4.4 greys the three flipped members and no member whose 1.6 and 1.7 certainty agreed | **Held** | The three 1.7 flips grey (Chelsea Dagger 0-20, Need You Tonight 0-13, Pour Some Sugar On Me 67-77) and nothing else by 4.4; spec 5.7's list omits the third |
| A7 | `SET_VETO_MARGIN` 0.10 fires on Badge and no other run | **Held** | Badge 0.238; Fame 0.008; every other run 0.000, the blind song "Happy Hour" included (set A# agrees with the decided A#) |
| A8 | Badge prints "G major (or E minor)" | **Held** | Mode margin 0.644 at G; hedge E minor |
| A9 | Rung 2 splits the three blind titles; the channel test fails the three non-artist handles | **Held on the fresh fetches** | All three split by rung 2; `@rhino`, `@goldsongs7948`, `@GnafUtopie` fail and print the line; the passing handles were not re-fetched (the eight re-ran from harmony). The blind song adds a fourth: "The Housemartins - Happy Hour" splits by rung 2 and `@oly69` (MiNaNi) fails, so the line prints |
| A10 | The six pickup bars are counting conventions | **Refuted further** | Four play, as the assumption pass found, and **The Cars' pickup also holds** (ratio 0.956) and prints strokes; only Summer of '69's is empty. Clip 4. The blind song's two-beat pickup rests (ratio 0.0008) and prints empty, a second counting convention (clip 20). By ear: The Cars' pickup is silent after all (clip 4: the assumption pass was right, the hold is false; the print is empty since the fix wave), AC/DC's is one stroke (clip 6, as printed since the fix wave), All Fired Up's count is unsettled (clip 5 ran into bar 1) |
| A11 | The listening passes transcribe into the truth files without ambiguity | **Held** | All 55 files parse on all eleven songs; the one scoring fault found was in the scorer, not the transcription (fix round) |
| A12 | The tests and fixtures that depend on the changed rules are known | **Held** | No test weakened; the fix round adds one harness test; full suite 971 passed |

## Blind song

The Housemartins, "Happy Hour" (https://www.youtube.com/watch?v=KfDoPEN7n5k), chosen by the owner on 2026-10-09 and run from ingest at commit `c23cbe8` (`logs\blind.txt`, exit 0, wall 97.5 s; run folder `runs\happy-hour`). Figures recorded, not judged (expectation 10); `blind-figures.txt`, `probe\happy-hour.json`, `evaluate\happy-hour.txt`.

| Figure | Value |
|---|---|
| Grid | 74 bars from 14.4 s to 152.5 s, 126.6 bpm, 4/4 (the beat stage logged 100.0 bpm detected, octave none); bar lengths 0.68 to 2.60 s, median 2.20 s; 6 grid sections: Intro 0-5, Chorus 5-17, Verse 17-24, Chorus 24-40, Instrumental 40-44, Outro 44-74; bar 0 a two-beat pickup |
| Plan | 4 planned sections: Intro 0-5, Chorus 5-40 (grid sections 1 to 3 merged), Instrumental 40-44, Outro 44-74 |
| Key | A# major, decided by agreement (score, pair and mix all A#; set A# 1.00 against decided 1.00, so no veto, margin 0.000); score margin 0.132, mode margin 0.501, runner-up F; no hedge. Chords: Bb 26 events, F 24, Eb 19, D minor 18, N 2, two inversions |
| Strums source | guitar stem, ratio 0.37, 16 slots per bar, grid fit 0.70 |
| Resting bars | bar 0 only (the pickup; ratio 0.0008, low share 0.046); no bar within 0.01 of the ratio floor |
| Rows | Intro `D-DUDUD-D--UD-DU` grey, "pattern uncertain" (4 voted bars; confidence 0.656, all-bars 0.525 under the sixteenth floor); Chorus 5-40 `D-DU--D-D-DUDUD-` certain (16 voted bars of its longest member 24-40; p 0.001), printed on all 35 bars; Instrumental `DUDUD-D-DUDUD-D-` certain (medoid, 4 voted bars, confidence 0.827); Outro `D---D-D-D-D-D---` grey, "pattern uncertain" (confidence 0.484) |
| Riff flags | none (entropy 0.90 to 0.91 on every section, single share 0.14 to 0.27); `riff.json` empty; no tab, no labels |
| Bass gate | off on all six members: bass stem ratio 0.368 to 0.554, own low share 0.026 to 0.080, mix low share under the bass stem 0.36 to 0.53, under the source stem 0.006 to 0.031 |
| Credits | "Happy Hour" by The Housemartins, both by rung 2 (`title`), from the raw title "The Housemartins - Happy Hour"; uploader MiNaNi (`@oly69`), whose handles fail the channel test, so the sheet prints "uploaded by MiNaNi"; `artist`, `artists` and `track` null in the fetch |
| Pickup | bar 0, two beats, an empty eight-column partial box (rests) |
| Legend lines, pages | both lines once; 2 pages |

**Against the published sources** (no lyrics read into any record):

| Item | Chain | Published source says | Agree? | Source |
|---|---|---|---|---|
| Title and artist | "Happy Hour" by The Housemartins | "Happy Hour", The Housemartins, 1986, from *London 0 Hull 4*, written by Paul Heaton and Stan Cullimore | agrees | en.wikipedia.org/wiki/Happy_Hour_(The_Housemartins_song); Songsterr s197972 |
| Key | A# major | the Songsterr tab's bass cycles Bb, D, Eb, F and opens and closes on Bb, and its guitar tracks' pitch classes are Bb major's; chordu.com's automatic chord recognition lists Bb, Eb, F, Dm, C and names Bb major | agrees (A# is B flat) | songsterr.com/a/wsa/housemartins-happy-hour-tab-s197972; chordu.com (Top of the Pops 1986 upload) |
| Tempo and bars | 74 bars at 126.6 bpm over 138 s | the tab: 112 bars at 192 bpm over 140 s; chordu reads 96.05 bpm (half of 192); a 1986 *Making Music* songwriting piece names verse, chorus and a link between them | the chain's bar does not match the tab's bar length (74 against 112 bars, or about 56 at 96 bpm), so alignment is by time, not bar number; recorded, not judged | Songsterr s197972; chordu; muzines.co.uk/articles/coverage-housemartins/13507 |
| Intro 0-5 | strum, grey, no riff flag | the tab's lead guitar plays a single-note figure over the rhythm guitar's chords in its first 8 bars (about 14 to 24 s), the bass under it on Bb, D, Eb, F | the source has a riff over a strum (`mixed`); the chain prints the strum | Songsterr s197972 |
| Chorus and verse 5-24 | strum, certain | the tab's rhythm guitar strums chords; the lead guitar is silent from tab bar 9 to 64 (to about 94 s) | agrees | Songsterr s197972 |
| 24-74 | strum (chorus certain, instrumental certain, outro grey) | the lead guitar re-enters in tab bars 65-72, 80-86 and 103-107 over the rhythm guitar | not settled at bar level by the time alignment | Songsterr s197972 |
| Activity | only the pickup bar 0 rests | the rhythm guitar has notes in every tab bar from 1 to 112 | agrees on 1-73; bar 0 not settled (the alignment's least certain point) | Songsterr s197972 |

The truth folder `truth/happy-hour/` holds the settled lines: `credits.txt` (Happy Hour, The Housemartins) and `key.txt` (Bb major) from the sources; after the listening pass, `rests.txt` (`0 2 rest` by clips 20 and 21, `2 74 play` from the tab), `riffs.txt` (`0 5 mixed`, `6 17 strum`, `17 24 strum`; clip 21 moved the tab's time alignment to start at bar 2, about 18.2 s, so the lead's intro figure ends at bar 6's start and bar 5 is omitted) and `patterns.txt` (Intro 2-5 YES, Chorus 5-13 YES, Verse 17-21 NO, bar 21 omitted as straddling the verdict, 22-24 YES, Chorus 24-32 YES, Instrumental 40-44 MOSTLY, Outro 44-52 YES). As first written, before the pass, `rests.txt` read `1 74 play` and `riffs.txt` `5 17 strum`. `evaluate --truth` on it after the pass: patterns false certain 1 (17-21), false grey 2 (2-5, 44-52); riffs recall 0.0% on the one riff-or-mixed range (the intro), no false flag; rests no false rest, one false hold (bar 1); key 100% (same); credits title yes and artist yes (both by `title`).

**Assumptions the blind song touches.** A5: its figures land far from both bands (own share at most 0.080 against the floor 0.40; bass ratio at least 0.368 against the cap 0.05), so the gate stays off and the bands neither widen nor narrow. A7: the set agrees with the decided tonic (margin 0.000); no veto. A9: rung 2 splits a fourth blind title correctly and the channel test fails a fourth non-artist handle (`@oly69`). A10: its pickup is a counting convention (rests, empty box), the second such after Summer of '69. Ear clips 20 to 26 (stem alone for the resting pickup; clicks on six sections) were heard in the listening pass above.

## What to improve next

Ranked by benefit to the reader, from the listening pass. None is built here.

1. **Part assignment by register.** On every section where the separator merged two parts the sheet prints a blend: Badge's gated sections hold a guitar riff high and the bass low (clips 7 to 16), The Cars 72-76 a solo over a rhythm guitar (clip 18), and the 1.7 pass heard the same on Pour Some Sugar On Me 67-77 and AC/DC. A per-song reference pitch split (the stem's notes above or below a register line found from the bass stem or the chord roots) would let the strums follow one part. A cheap first spike: a high-pass on the stem before onset detection, scored on clips 7 to 16 (does Chorus 1's click track still follow the riff, and do the other four start to?).
2. **A bar whose own onsets depart strongly from its member's pattern should not print the pattern unchanged.** A held chord or a rhythm change inside a section gets the section's clicks over it: Pour Some Sugar On Me's intro bars 6-7 (clip 17), Happy Hour's Instrumental long chord (clip 25). Print such a bar from its own onsets, or grey, by a measured departure figure.
3. **Fast runs.** Need You Tonight's three stabs then nine fast notes (clips 19 and 1.7 clip 10) are under-detected; this is 1.9's onset detector and strike density.
4. **Happy Hour's verse bars 17-20** click at random and fast under a certain row (clip 23): investigate what the stem holds there (the tab's rhythm guitar strums through) before any rule is written.
5. **All Fired Up's pickup count.** Re-cut a clip of the pickup bar alone, to settle whether the one `D` it prints is right.

## Where the figures live

All under `%TEMP%\youkulele-v18-validation\`: `setup.py`, `baseline\` (each 1.7 run folder whole), `evaluate-baseline\` (the 1.7 totals, before any re-run), `refresh_meta.py`, `rerun.py`, `rerun-times.json`, `logs\` (one per run, and `<folder>-meta.txt` for the three fetches); `measure.py`, `measure\<song>.json|.txt`, `measure\all.txt`; `probe.py`, `probe\<song>.json`; `members.py`, `members.txt`; `summarise_truth.py`, `truth-totals-baseline.txt`, `truth-totals-rerun.txt` (first round), `truth-totals-rerun-fix1.txt`; `evaluate_all.py`, `evaluate\` and `evaluate-round1\`; `sweeps.py`, `sweeps\<constant>.txt`; `clips\make_clips_v18.py`; the clips under `%TEMP%\youkulele-ear-v18\`. The blind song: `blind.py`, `logs\blind.txt`, `rerun-times-blind.json`, `blind_figures.py`, `blind-figures.txt`, `probe\happy-hour.json`, `evaluate\happy-hour.txt` and `evaluate\happy-hour-truth.txt`, `parse_songsterr.py` and `pitch_songsterr.py` (structure and pitch-class counts from the Songsterr guitar and bass tracks, downloaded to `sources-dl\`; the vocal track was not fetched), `clips\make_clips_blind.py`. After the listening pass: `truth-totals-listening.txt` (twelve songs), `sweeps\` re-run for `REST_RATIO_MIN`, `OWN_LOW_SHARE_MIN` and `BASS_STEM_MAX` on the truth as the pass left it (the earlier sweeps kept as `sweeps-before-listening\`).
