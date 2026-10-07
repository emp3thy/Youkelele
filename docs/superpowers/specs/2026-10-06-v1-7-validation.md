# Version 1.7 validation on ten songs and one blind song

Date: 2026-10-06. Branch `worktree-v1-7` at `9608dd7` (package version 0.8.0), then one fix round at `999995e`. Checks every expectation in section 8 of `2026-10-06-ukulele-tab-chain-v1-7-design.md` against the kept version 1.6 runs of ten songs (the 1.6 eight, The Beatles "Day Tripper" and AC/DC "You Shook Me All Night Long"), and runs one song the chain has never seen. Bar and section numbers are 0-based, as in `grid.json`; a range written `55-61` ends before bar 61. "Planned section" means a section of the section plan, which is what the sheet prints; "member" means one of the grid sections a planned section merged. A bar "rests" when its `strums.json` record has `rests` true (spec 5); a bar "holds" otherwise. "Printed row changed" means the bar's stroke vector or grey flag in `score.json` differs from 1.6. Every figure below is traceable to a file under `%TEMP%\youkulele-v17-validation\` (named in "Where the figures live").

## Runs and baselines

The ten version 1.6 run folders under `runs\` are the baseline. Before any re-run, `02_grid` to `08_render`, `manifest.json` and `source_meta.json` of each were copied to `%TEMP%\youkulele-v17-validation\baseline\<folder>\`. Each folder was then re-run in place, one at a time, with `uv run youkelele run "<source from its manifest>" --from strums --runs-dir C:\Users\gethi\sources\Youkulele\runs` from the worktree root (`rerun.py`), with its log under `logs\<folder>.txt`. A first attempt passed the folder name as the source, as the task brief's command shape had it; the chain read the name as a new local source, made an empty folder `runs\summer-of-69-2` and stopped with "missing artifact separate/stems/guitar.wav" (exit 1, `logs\summer-of-69-attempt1-foldername.txt`). The empty folder was removed and every run then used its manifest's source URL, which resolves to its own folder with no network. Every run exited 0.

| Song | Folder | Wall time | Exit | strums s, 1.6 to 1.7 | riff s, 1.6 to 1.7 | arrange, score, render s (1.7) |
|---|---|---:|---|---|---|---|
| Summer of '69 | `summer-of-69` | 44.3 s | 0 | 25.4 to 25.7 | 0.2 to 17.0 | 0.2, 0.1, 0.8 |
| Chelsea Dagger | `chelsea-dagger` | 29.7 s | 0 | 9.2 to 27.8 | 0.2 to 0.2 | 0.2, 0.1, 0.9 |
| Pour Some Sugar On Me | `pour-some-sugar-on-me` | 61.0 s | 0 | 8.6 to 33.0 | 0.3 to 26.1 | 0.3, 0.1, 0.9 |
| Wet Leg "mangetout" | `mangetout` | 47.2 s | 0 | 24.6 to 27.9 | 17.0 to 17.6 | 0.2, 0.1, 0.9 |
| David Bowie "Fame" | `fame` | 54.8 s | 0 | 30.0 to 31.3 | 21.4 to 21.7 | 0.2, 0.1, 0.9 |
| Pat Benatar "All Fired Up" | `all-fired-up` | 57.5 s | 0 | 31.1 to 34.7 | 20.8 to 21.0 | 0.2, 0.1, 0.8 |
| INXS "Need You Tonight" | `need-you-tonight` | 42.4 s | 0 | 22.5 to 23.5 | 16.1 to 17.2 | 0.2, 0.1, 0.9 |
| The Cars "You Might Think" | `the-cars-you-might-think` | 37.8 s | 0 | 21.1 to 22.2 | 14.5 to 13.9 | 0.2, 0.1, 0.8 |
| The Beatles "Day Tripper" | `the-beatles-day-tripper` | 35.6 s | 0 | 20.6 to 20.4 | 0.2 to 13.6 | 0.2, 0.1, 0.8 |
| AC/DC "You Shook Me All Night Long" | `you-shook-me-all-night-long` | 29.8 s | 0 | 8.0 to 27.4 | 0.4 to 0.2 | 0.3, 0.1, 1.0 |

Stage times are differences between consecutive `finished_at` stamps in each manifest. The strums time counts from the command's start (the log's write time less the wall time), so it includes `uv run` starting Python, about 3 s; the 1.6 figures are measured the same way from the 1.6 validation's final-wave logs, except AC/DC, whose 1.6 run went from ingest in the 1.7 research and is timed from its harmony stage's finish (no start-up included). The 1.7 strums stage runs the pitch tracker on every song; 1.6 ran it only where a section passed the chroma features. It costs 18.6 to 24.4 s on the three songs where 1.6 did not run it (Chelsea Dagger, Pour Some Sugar On Me, AC/DC) and between -0.2 and +3.6 s on the other seven. The riff stage still tracks pitch on its own, so a song with a riff section pays the tracker twice: the three songs that gain their first riff section (Summer of '69, Pour Some Sugar On Me, Day Tripper) gain 13.4 to 25.8 s in the riff stage. Every manifest records 0.8.0 for strums, riff, arrange, score and render; the earlier stages keep their stamps.

Measurement: `probe.py` re-runs the 1.7 strums stage on each folder in-process into a scratch folder, recording the figures the stage computes per member but writes only for the longest member (riff features, holding bars, silent flag, vote unit), and checks that its `strums.json` is byte-identical to the run's (true on all ten, so the figures are the run's own). `measure.py` compares `grid.json` and `chords.json` byte for byte, the chord events, `bar_onsets`, the plan and the recall-boost flags value for value, lists every section's and member's riff flag and figures, every resting bar with its two figures and its place in its member, every printed row that changed with its reason, every label, the tab and gate figures, the sheet's `class="sustain"` and `class="chord label"` counts and the PDF page counts, and rasterises every page at 110 dpi. `evaluate_all.py` saves `evaluate` on all ten and `evaluate <baseline> --compare <run>` on all ten. `a11_render.py` renders every baseline 1.6 `score.json` through the 1.7 render stage.

## Expectations from spec section 8

Written before the runs, as the spec states them; checked after (figures after the fix round).

| # | Expectation | Met? | Figure |
|---|---|---|---|
| 1 | `grid.json`, the chord events and `bar_onsets` byte-identical to 1.6 on all ten songs (AC/DC and Day Tripper to their 1.6 runs) | **Yes** | `grid.json` and `chords.json` byte-identical on all ten; chord events, `bar_onsets`, the plan, the recall-boost flags, slots per bar and source identical on all ten |
| 2 | No sustain line on any sheet; the stroke rows of the eight 1.6 songs otherwise unchanged except where bars rest | **No, as worded** (sustain: yes) | `class="sustain"` 0 on all ten sheets (1.6: 0 to 302). On the eight 1.6 songs 97 printed rows changed: 43 resting bars, and **54 bars that hold**, all inside the seven members that have a resting bar, because the member's vote, chance test and riff features now read fewer bars (spec 5). No row changed in a member without a resting bar. Day Tripper adds one resting bar, AC/DC nothing. See "Printed rows that changed" |
| 3 | Riff flags change exactly as spec 4.3 lists (All Fired Up 61-90, Day Tripper 52-58, Summer of '69 0-4, The Cars 0-11 added; none removed); AC/DC gains none, and its sections are recorded against its ear truth | **No** | The four listed flags are added (pitch-change shares 0.289, 0.292, 0.333, 0.282) and none is removed; AC/DC gains none (entropy 0.835 to 0.946, single share 0.08 to 0.39). **A fifth flag is added: Pour Some Sugar On Me Instrumental 67-77**, not by the floor (its pitch-change share is 0.510) but because bars 67 and 68 rest and its single share over the holding bars rises from 0.426 to 0.468, over 0.45. See "Riff flags that changed" |
| 4 | The 51 bars of spec 5 rest and no bar of an ear-verified section rests; Chelsea Dagger's intro prints chords with empty strokes on bars 0-6, 10 and 11 and power-chord strokes from bar 13 | **Partly** | Exactly 51 bars rest, the same 51 the rests spike's rule names (none missing, none extra). No bar of the rests spike's ear-verified sections rests. **Three resting bars lie inside 1.6 listening clips in which the owner heard the guitar**: Wet Leg bar 18 (clip `held_verse_18`, "cut"; 6 onsets detected), Pour Some Sugar On Me bar 77 (`held_verse_77`, "a single note - plays through"; 3 onsets) and Summer of '69's pickup bar 0 (clips `shortsection_intro_0-4` and the 1.7 `a3_intro_0-4`; no onset). Need You Tonight 84-85 rest inside the outro clip 79-86 but are trailing bars that neither version prints. Chelsea Dagger: bars 0-6, 10 and 11 print their chords (N.C., C, G) with empty stroke rows, bars 13 to 19 print `D-xxxUx-`; bars 7, 8, 9 and 12 also hold (ratios 0.050, 0.308, 0.072, 0.062) and print the same strokes |
| 5 | The label appears on the first bar of every riff member whose section header does not say riff (All Fired Up 97-104, Wet Leg 58-65, and any member newly flagged), and nowhere else | **No** | One label on the ten sheets: Wet Leg bar 58, "riff heard". **All Fired Up 97-104 carries none**: the newly flagged 61-90 is Verse 2's longest member, so the header now says "riff heard, not transcribed", and spec 3.2 withholds the label under a riff header. The five new flags are all longest members, whose headers say riff. The label follows spec 3.2 on every member (derived independently from the riff members and headers: equal on all ten). In the first round the label pushed bar 58's chord name out of the box (fix round below) |
| 6 | Tab prints on Need You Tonight's verse as before; any newly flagged section that passes the gate is recorded, with its tab clip | **Yes** | Need You Tonight Verse 1 (13-24) prints tab on all 11 bars, identical to 1.6 (agreement 0.739, support 0.777, named 0.942; C string, frets 0, 2, 3). None of the five new flags passes the gate (agreement 0.14 to 0.43), so no new tab and no tab clip |
| 7 | Pages recorded against 1.6 (no sustain lines and empty rows do not change height) | **Yes** | Pages 3, 3, 3, 2, 3, 2, 2, 3, 3, 2 against 1.6's same counts on all ten; the last page's fill is unchanged on nine and moves from 0.56 to 0.61 on Wet Leg after the fix round (the labelled line prints four wide bars) |
| 8 | The blind song runs to a sheet with exit 0; its figures recorded, not judged | | |

Scorecard on rows 1 to 7: three met (1, 6, 7), one partly met (4), three missed (2, 3, 5). Nothing was tuned. Row 2 misses by the design of spec 5 (a resting bar leaves the vote), which the expectation's wording did not foresee; row 3 misses by an interaction of spec 5 with Rule A; row 5 misses because spec 4.3's new flag on All Fired Up 61-90 puts a riff header over 97-104, which the expectation did not foresee.

## Fix round

**Finding.** In the first round Wet Leg's sheet printed the label on bar 58 but not the bar's chord name. Verse 4 prints eight bars to a line on the eighth grid, so each box is 80 px wide; "riff heard" at the chord font advances 84 px, and the renderer placed the chord name `C` after it at x 87, outside the box, where the SVG clips it. Spec 3.2 puts the label left of the first chord name, which must still print. A code defect, not a threshold.

**Fix** (commit `999995e`): `render/lines.py` drops a line to four wide boxes when any bar in its eight-bar window carries a label, as it already does for a bar with two chords or a pickup, and the fold key includes the label, so a labelled line never folds into an identical unlabelled one (which would lose the label). Covering tests in `tests/test_render_lines.py`: `test_a_labelled_bar_in_the_window_drops_the_line_to_four` and `test_a_labelled_line_never_folds_into_an_unlabelled_one`. Full suite: 876 passed (fast and slow).

**Exposure and re-run.** `render_check.py` rendered every run's `score.json` through the fixed renderer: the HTML is byte-identical to the first round's on nine songs and differs only on Wet Leg, the one sheet with a label. Wet Leg was re-run `--from strums` (44.9 s, exit 0, `logs\mangetout-fix1.txt`); its `strums.json` and `score.json` are byte-identical to the first round's, its sheet now prints `riff heard` and `C` on bar 58 on a four-bar line, then Verse 4 continues in eight-bar lines ("play three times" where it was "play 4 times"); still 2 pages, the last filled to 0.61. Every `evaluate` and `evaluate --compare` output is identical to the first round's. The first round's outputs are kept as `snapshot-round1\`, `measure-round1\`, `pages-round1\` and `evaluate-round1\`.

**Second round (the whole-branch review's fix wave, commit `cbc40ad`).** The final code review found that a resting bar inside a printable riff member would still print tab (no song in the ten does this; the score builder now prints no tab on a resting bar, with a test), that a member silenced by the section-level cut carried per-bar rest flags from its own figures (now `rests` False on every such bar, as spec 5 says the per-bar rule runs only inside sections that pass the cut; a member silent because no bar holds keeps `rests` True), and that Review Focus 3's all-rest-longest-member case had no test (added; it passed as written). Wet Leg, the one song with resting bars in a silent member, re-ran `--from strums` (exit 0, `logs\mangetout-fix2.txt`): its Outro member is silent through the trimmed-tail path, not the section cut, so its `strums.json` rest flags and its `score.json` are byte-identical to the first fix round; no other song's strums or score could change (the fix wave touched no measurement). The README gained the 1.7 history links and a limitation line about quiet real bars resting. Full suite after the fix wave: 870 fast, 9 slow.

## Riff flags that changed

Figures are the member's own, on its holding bars (entropy and single share from the chroma features, pitch-change share, the share of named pitches on the chord root and the share of onsets the pitch tracker named), from `probe\<song>.json`; the gate is the riff stage's (agreement, support, named; the gate wants 0.70, 0.75, 0.6). Every changed flag is the planned section's longest member, so it changes the header.

| Song, section | Member | Change | Rule | Entropy | Single | Pitch change | Root | Named | Onsets | Header now | Gate |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| Summer of '69 Intro | 0-4 | added | A | 0.608 | 0.700 | 0.333 | 0.778 | 0.900 | 20 | riff heard, not transcribed | 0.43, 0.63, 1.00: fails |
| All Fired Up Verse 2 (55-110) | 61-90 | added | A | 0.729 | 0.721 | 0.289 | 0.951 | 0.953 | 43 | riff heard, not transcribed | 0.14, 0.19, 0.91: fails |
| The Cars Intro | 0-11 | added | A | 0.735 | 0.638 | 0.282 | 0.774 | 0.663 | 80 | riff heard, not transcribed | 0.20, 0.27, 0.74: fails |
| Day Tripper Verse 3 | 52-58 | added | A | 0.709 | 0.528 | 0.292 | 0.759 | 0.806 | 36 | riff heard, not transcribed | 0.37, 0.50, 0.86: fails |
| **Pour Some Sugar On Me Instrumental** | 67-77 | **added, not in spec 4.3** | A | 0.750 | 0.468 | 0.510 | 0.393 | 0.785 | 79 | riff heard, not transcribed (was "pattern uncertain") | 0.18, 0.28, 0.83: fails |

The first four are spec 4.3's, with the shares the riff-test spike measured (0.289, 0.292; Summer of '69 read 0.33 in 1.6 and passed the chroma features then too). Pour Some Sugar On Me 67-77 read entropy 0.786 and single share 0.426 over all ten bars in 1.6 (failing the 0.45 single share); in 1.7 bars 67 and 68 rest on the low-share test (0.0002 and 0.0026) and the features read 79 of the 94 onsets, giving 0.750 and 0.468. Its pitch-change share was not measured in 1.6 (the chroma features failed); at 0.510 it would pass the 1.6 floor of 0.40 as well. No flag was removed. All riff members on the ten songs, 1.7: Summer of '69 0-4; Pour Some Sugar On Me 67-77; Wet Leg 0-5, 58-65, 100-108; Fame's nine sections; All Fired Up 49-55, 61-90, 97-104; Need You Tonight's six flagged sections (all but the Intro); The Cars 0-11, 52-68; Day Tripper 52-58.

**The pitch-change band on these runs** (`chroma-passers.txt`, every voiced member that passes the two chroma features): the highest unflagged is All Fired Up 55-61 at 0.238, the lowest flagged The Cars 0-11 at 0.282, so the 0.26 floor sits in a band of 0.238 to 0.282.

**AC/DC against its ear truth** (no section flagged, as spec 4.3 predicts):

| Section | Ear truth (owner) | Printed | Entropy | Single | Pitch change | Root | Named |
|---|---|---|---:|---:|---:|---:|---:|
| Intro 0-16 | riff over an opening chord; clicks fit the riff | `--DUDUDU` two-bar, no phrase | 0.916 | 0.175 | 0.292 | 0.455 | 0.524 |
| Chorus 16-34 | strum; clicks do not fit | `--D-DUDU` two-bar | 0.942 | 0.082 | 0.364 | 0.343 | 0.479 |
| Verse 34-43 | riff with backing chords; clicks wrong | `--D---DU` | 0.926 | 0.143 | 0.412 | 0.476 | 0.750 |
| Verse 43-57 | strum; clicks wrong | `D-D----U` two-bar | 0.946 | 0.078 | 0.652 | 0.313 | 0.627 |
| Verse 57-74 | not judged | `--D---DU`, pattern uncertain | 0.916 | 0.095 | 0.391 | 0.548 | 0.738 |
| Instrumental 74-90 | solo over strum; clicks miss | `D-DUDUDU` | 0.835 | 0.383 | 0.725 | 0.310 | 0.716 |
| Verse 90-113 | riff over chords; clicks do not fit | `D-D-DUDU` | 0.894 | 0.391 | 0.438 | 0.487 | 0.848 |

Every section fails the chroma gate on both features. The lowest entropy is 0.835 (Instrumental), against the spec's quoted 0.84. AC/DC's sheet is unchanged from 1.6 apart from the sustain lines (114 in 1.6, 0 now): no bar rests and no printed row changed.

## Resting bars

Fifty-one bars rest, exactly the rests spike's 51 under the same rule (its per-bar figures, `youkulele-v17-research\rests\f_<song>.csv`, recomputed: the four "single bars" are All Fired Up 114, Summer of '69 0 and 120, Day Tripper 94, The Cars 62). Every bar's `rests` flag agrees with its two recorded figures (0 inconsistent of 1131 bars). Ratio is the bar's stem RMS over the mix's (floor 0.05); low is its STFT power share below 330 Hz (floor 0.005); onsets are the bar's detected strikes in `bar_onsets` (`resting-onsets.json`); place is where the bar sits in its member (leading: before the first holding bar; interior: between holding bars; tail: after the last holding bar; trailing: after the last chord, outside the analysed bars; silent member: a member with no holding bar).

| Song | Bars | Failed test (ratio, low) | Onsets detected | Place |
|---|---|---|---|---|
| Need You Tonight | 0-7 | ratio (0.0001 to 0.020) | 0 each | leading, Intro 0-13 |
| Need You Tonight | 84, 85 | ratio (0.014, 0.0004) | 1, 0 | trailing (not printed in either version) |
| Wet Leg | 18-25 | ratio (0.0001 to 0.029; bar 25 low 0.011) | 6, 5, 0, 0, 0, 0, 0, 0 | leading, Verse 2 18-33 |
| Wet Leg | 109-112 | ratio (0.0004 to 0.0015) | 1, 5, 8, 5 | silent member (Outro, already "no strummed instrument detected"; not printed) |
| Pour Some Sugar On Me | 0 | ratio (0.010) | 0 | leading, Intro 0-11 |
| Pour Some Sugar On Me | 7-10 | ratio (0.0499, 0.029, 0.002, 0.023) | 8, 6, 4, 7 | tail, Intro 0-11 |
| Pour Some Sugar On Me | 15-18 | ratio (0.0004 to 0.033); bar 16 also low (0.0042) | 1, 2, 0, 2 | interior, Verse 1 11-28 |
| Pour Some Sugar On Me | 66 | ratio (0.001) | 0 | tail, Chorus 2 55-67 |
| Pour Some Sugar On Me | 67, 68 | low (0.0002, 0.0026; ratios 0.080, 0.100) | 3, 7 | leading, Instrumental 67-77 |
| Pour Some Sugar On Me | 77-79 | ratio (0.029, 0.0002, 0.0001) | 3, 0, 0 | leading, Verse 3 77-84 |
| Chelsea Dagger | 0-2 | ratio (0.014 to 0.024) | 2, 2, 2 | leading, Intro 0-20 |
| Chelsea Dagger | 3-5 | low (0.0002, 0.0003, 0.0006; ratios 0.86, 0.88, 0.057): the bell | 4, 1, 0 | leading |
| Chelsea Dagger | 6 | both (0.011, 0.0001) | 0 | leading |
| Chelsea Dagger | 10, 11 | ratio (0.0001 each) | 0, 0 | interior |
| All Fired Up | 114 | ratio (0.005) | 0 | interior, Chorus 2 110-124 |
| Summer of '69 | 0 (pickup) | ratio (0.024) | 0 | leading, Intro 0-4 |
| Summer of '69 | 120 | ratio (0.004) | 4 | trailing (not printed) |
| The Cars | 62 | ratio (0.016) | 0 | interior, Verse 3 52-68 |
| Day Tripper | 94 | ratio (0.008) | 0 | tail, Outro 78-95 |

By test: 44 bars fail the ratio alone, 5 the low share alone (Chelsea Dagger 3, 4, 5; Pour Some Sugar On Me 67, 68), 2 both. Near the floors (`near-floor.txt`): within 0.01 of the ratio floor, Pour Some Sugar On Me 7 rests at 0.0499 and Chelsea Dagger 7 holds at 0.0503 (also Chelsea Dagger 5 at 0.057, resting on low share, and Pour Some Sugar On Me 80 holding at 0.055); under 0.01 of low share, Need You Tonight 9 (0.0073), Day Tripper 1 (0.0077) and Summer of '69 29 (0.0081) hold and Pour Some Sugar On Me 16 and 68 rest. Need You Tonight's tab bars 13-23 read ratio 0.080 to 0.307 and low share from 0.040.

**Ear-heard bars that rest.** Against the rests spike's ear-verified sections (Need You Tonight 13-24, All Fired Up 33-49 and 61-90, The Cars 11-19 and 68-72, Summer of '69 75-83, Chelsea Dagger 13-20) no bar rests. Against every 1.6 listening clip in which the owner heard music, AC/DC's six ear-truth clips and the three 1.7 assumption clips, these rest: Wet Leg 18 (`held_verse_18`, verdict "cut": a stroke was heard), Pour Some Sugar On Me 77 (`held_verse_77`, "a single note - plays through"), Summer of '69 0 (the pickup, inside `shortsection_intro_0-4` and `a3_intro_0-4`), and Need You Tonight 84-85 (trailing, inside `changed_outro_79-86`). All three printed bars are on spec 5's list of 51, so spec 5 and the listening pass disagree on them.

**The two counts.**

- **Unit-2 members with an interior resting bar: 0.** Of 93 voiced members on the ten songs, 12 vote a two-bar unit; none of them has a resting bar between holding bars, so the compressed bar list the vote pairs never differs from the absolute bars. Four members have an interior resting bar, all one-bar units: Chelsea Dagger 0-20 (10, 11), Pour Some Sugar On Me 11-28 (15-18), All Fired Up 110-124 (114), The Cars 52-68 (62).
- **Resting bars by place: 7 in trailing bars or silent members** (3 trailing: Need You Tonight 84, 85, Summer of '69 120; 4 in Wet Leg's silent Outro member, 109-112) **against 44 in members that hold** (30 leading, 8 interior, 6 tail). Of the 51, 44 print (as empty black rows); the 7 trailing and silent-member bars are not on the page.

## Printed rows that changed

Per bar in `score.json`, 1.6 against 1.7 (`measure\<song>.json`, `stroke_changes`); `evaluate --compare` counts the same changes per section on `strums.json` ("patterns changed in N bars", which also counts the three trailing bars).

| Song, member | Bars | 1.6 printed | 1.7 prints | Why |
|---|---|---|---|---|
| Summer of '69 Intro | 0 | `D-xx-xxx` | empty | rests |
| Chelsea Dagger Intro 0-20 | 0-6, 10, 11 | `D-x-x-x-`, grey | empty, black | rest |
| Chelsea Dagger Intro 0-20 | 7-9, 12-19 | `D-x-x-x-`, grey (pattern uncertain) | `D-xxxUx-`, black (certain) | the vote reads 11 holding bars; confidence 0.32 to 0.49, chance p 0.001 |
| Pour Some Sugar On Me Intro 0-11 | 0, 7-10 | grey strokes | empty | rest |
| Pour Some Sugar On Me Intro 0-11 | 1-6 | `DUDUDUDUDUD-D-DU`, grey | `-UDUDUDUDUD-D-D-`, grey | vote on 6 bars |
| Pour Some Sugar On Me Verse 1 11-28 | 15-18 | grey strokes | empty | rest |
| Pour Some Sugar On Me Verse 1 11-28 | 11-14, 19-27 | `D-D--UDU----DU--`, grey | `DUD-D-DU----D---`, grey | vote on 13 bars: majority to medoid |
| Pour Some Sugar On Me Chorus 2 55-67 | 66 | grey strokes | empty | rests |
| Pour Some Sugar On Me Instrumental 67-77 | 67, 68 | grey strokes | empty | rest |
| Pour Some Sugar On Me Instrumental 67-77 | 69-76 | `DU-UxUDU-UDUDUDU`, grey | `DUDUxUDU-UDUDUDU`, black | vote on 8 bars (chance p 0.051 to 0.047, now certain), and the new riff flag (header "riff heard, not transcribed") |
| Pour Some Sugar On Me Verse 3 77-84 | 77-79 | grey strokes | empty | rest |
| Pour Some Sugar On Me Verse 3 77-84 | 80-83 | `D----------U----`, grey | `D-----D----U----`, grey | vote on 4 bars: majority to medoid |
| Wet Leg Verse 2 18-33 | 18-25 | `D-D-D-DU` | empty | rest |
| Wet Leg Verse 2 18-33 | 26-32 | `D-D-D-DU` | `D-D-DUDU` | vote on 7 bars |
| All Fired Up Chorus 2 110-124 | 114 | grey strokes | empty | rests |
| Need You Tonight Intro 0-13 | 0-7 | `D---------------`, grey | empty | rest |
| Need You Tonight Intro 0-13 | 8-12 | `D---------------`, grey (p 0.989) | `D---D---D---D---` / `D-D---DU---U---U` two-bar, black (p 0.007) | vote on 5 bars |
| The Cars Verse 3 52-68 | 62 | `DUDUDUDU` | empty | rests |
| Day Tripper Outro 78-95 | 94 | `D--UDUDU` | empty | rests |

No printed row changed in a member without a resting bar, and none of the patterns the 1.6 listening pass accepted (Summer of '69 4-19, 75-83 and 95-111, Chelsea Dagger 61-71, Need You Tonight 13-24 and 79-86, All Fired Up 55-61) changed. Section states that changed: Chelsea Dagger Intro and Need You Tonight Intro from "pattern uncertain" to certain (no phrase); Pour Some Sugar On Me Instrumental from "pattern uncertain" to "riff heard, not transcribed"; the five flagged sections' headers as above.

## Labels

| Song | Bar | Label | Planned section (header) | Member | Expected by spec 8 row 5 |
|---|---|---|---|---|---|
| Wet Leg | 58 | riff heard | Verse 4 58-100 (no phrase) | 58-65 | yes |
| All Fired Up | (97) | none | Verse 2 55-110 ("riff heard, not transcribed") | 97-104 | yes, but spec 3.2 withholds it under a riff header |

`class="chord label"` appears once on the ten sheets (Wet Leg). Every riff member that is not its section's longest (Wet Leg 58-65, All Fired Up 97-104) was checked against its header; the label appears exactly where spec 3.2 puts it.

## Tab

Need You Tonight Verse 1 13-24: tab on all 11 bars, identical to 1.6 (`tab_identical` true; agreement 0.739, support 0.777, named 0.942; C string, frets 0, 2, 3, no shift). No other section prints tab. Gate figures of the five new flags are in the flag table (agreement 0.14 to 0.43); every other riff section's gate figures are as in 1.6.

## Per song

| Song | Planned sections | Riff sections 1.6 to 1.7 | Resting bars | Printed rows changed (resting / holding) | Labels | Tab bars | Pages 1.6 to 1.7 (last page filled) | Sustain lines 1.6 to 1.7 |
|---|---:|---|---:|---|---|---:|---|---|
| Summer of '69 | 12 | 0 to 1 | 2 | 1 (1 / 0) | none | 0 | 3 to 3 (0.18) | 221 to 0 |
| Chelsea Dagger | 7 | 0 to 0 | 9 | 20 (9 / 11) | none | 0 | 3 to 3 (0.21) | 227 to 0 |
| Pour Some Sugar On Me | 8 | 0 to 1 | 15 | 46 (15 / 31) | none | 0 | 3 to 3 (0.39) | 302 to 0 |
| Wet Leg "mangetout" | 8 | 2 to 2 | 12 | 15 (8 / 7) | bar 58 | 0 | 2 to 2 (0.56 to 0.61) | 69 to 0 |
| David Bowie "Fame" | 9 | 9 to 9 | 0 | 0 | none | 0 | 3 to 3 (0.18) | 16 to 0 |
| Pat Benatar "All Fired Up" | 8 | 1 to 2 | 1 | 1 (1 / 0) | none | 0 | 2 to 2 (0.94) | 207 to 0 |
| INXS "Need You Tonight" | 7 | 6 to 6 | 10 | 13 (8 / 5) | none | 11 | 2 to 2 (0.76) | 0 to 0 |
| The Cars "You Might Think" | 10 | 1 to 2 | 1 | 1 (1 / 0) | none | 0 | 3 to 3 (0.31) | 12 to 0 |
| The Beatles "Day Tripper" | 12 | 0 to 1 | 1 | 1 (1 / 0) | none | 0 | 3 to 3 (0.24) | 42 to 0 |
| AC/DC "You Shook Me All Night Long" | 7 | 0 to 0 | 0 | 0 | none | 0 | 2 to 2 (0.74) | 114 to 0 |

"Riff sections" counts planned sections whose header follows a riff-flagged longest member; riff members inside merged sections (Wet Leg 58-65, All Fired Up 97-104) are in the flag paragraph above. The pages of all ten sheets were rasterised (`pages\<song>\p<n>.png`); Chelsea Dagger page 1, Need You Tonight page 1 and Wet Leg page 2 were looked at. Resting bars print their chord name and a box of faint rest dots, with no arrows (Chelsea Dagger's intro reads N.C., N.C., N.C., C, C, N.C., N.C. over empty rows, then strokes); Need You Tonight's eight resting intro bars fold into one four-bar line marked "play twice"; the tab block reads as in 1.6.

## Recorded, not tuned

Every section whose output does not match spec 4.3 or spec 5, with its figures. No threshold was changed.

1. **Pour Some Sugar On Me Instrumental 67-77 is a fifth new riff flag.** Rule A fires (entropy 0.750, single share 0.468, pitch change 0.510) because bars 67 and 68 rest on the low-share test and leave the riff features; over all ten bars the single share is 0.426. Spec 4.3 did not predict it because the riff-test spike read every bar. The section now prints certain black strokes `DUDUxUDU-UDUDUDU` under "riff heard, not transcribed" (it was grey, "pattern uncertain"); the gate fails (0.18). Its root share, 0.393, is the lowest of the five new flags. For the sources step and, failing them, the ear.
2. **All Fired Up 97-104 carries no label.** Spec 8 row 5 expects one; spec 3.2 withholds it because Verse 2's header now says riff, which follows from spec 4.3's new flag on 61-90. The spec's two expectations cannot both hold.
3. **Three resting bars were heard by the owner** in the 1.6 listening clips: Wet Leg 18 (ratio 0.029, 6 onsets, "cut"), Pour Some Sugar On Me 77 (ratio 0.029, 3 onsets, "a single note - plays through") and Summer of '69's pickup bar 0 (ratio 0.024, no onset). Pour Some Sugar On Me 7-10 (ratio 0.002 to 0.0499, 4 to 8 onsets each) and 67-68 (low share 0.0002 and 0.0026 at ratios 0.08 and 0.10, 3 and 7 onsets) also rest with detected strikes. All are on spec 5's list; the stem-alone clips of the controller's ear step can settle them.
4. **Resting bars change the printed rows of the bars that hold in seven members** (54 bars): the vote, chance test and riff features read fewer bars, as spec 5 says, but spec 8 row 2 and A7 expected the holding bars to print as before. Two intros flip from uncertain to certain: Chelsea Dagger's `D-xxxUx-` now prints black on bars 7-9 and 12-19, and Need You Tonight's bars 8-12 print a certain two-bar `D---D---D---D---` / `D-D---DU---U---U` where 1.6 printed a grey single down stroke. Two Pour Some Sugar On Me sections switch from majority to medoid.
5. **Chelsea Dagger bars 7, 9 and 12 hold at ratios 0.050, 0.072 and 0.062**, within 0.03 of the floor, and print the intro's strokes; bar 9 has no detected onset. The riff-test spike calls bars 0-12 near silence apart from bar 8 (ratio 0.31). Spec 5 lists only 0-6, 10 and 11 to rest, so this matches the spec; it is recorded because the expectation "power-chord strokes from bar 13" reads as if 7-12 were empty.
6. **AC/DC's four riff-or-solo-over-chords sections print as strums**, as spec 4.3 and section 6 say; the lowest entropy is 0.835 against the spec's quoted 0.84.
7. **The pitch tracker runs twice on a song with a riff section** (once in strums, once in the riff stage): 13.4 to 25.8 s more in the riff stage on the three songs that gained their first riff section, and 18.6 to 24.4 s more in strums on the three songs where 1.6 did not track pitch.

## Assumptions after validation

Every row of spec section 9, with its status after these runs.

| # | Assumption | Status now | Evidence |
|---|---|---|---|
| A1 | `PITCH_CHANGE_MIN` 0.26 separates riffs from strums | **Held on these runs; band 0.238 to 0.282** | The four predicted flags fire at 0.282 to 0.333; the highest unflagged chroma-passing member is All Fired Up 55-61 at 0.238. The fifth flag (Pour Some Sugar On Me 67-77, 0.510) comes from the rest rule, not the floor. The band still rests on one strum below (All Fired Up 55-61); the sources and the ear judge the new flags |
| A2 | A chroma-free riff rule can be made general | **Refuted, dropped** (unchanged) | Not built; `root_share` and `named_share` are written on every one of the 93 voiced members (root 0.04 to 1.00, named 0.32 to 1.00 across the ten songs). Day Tripper's intro (pitch change 0.781, entropy above the gate) and Summer of '69's outro (0.600) stay unflagged and print as strums |
| A3 | The two new flags Rule A adds are riffs | **The two verified flags fire**; a third unverified flag appeared | Summer of '69 0-4 and The Cars 0-11 are flagged and print "riff heard, not transcribed" (gate 0.43 and 0.20). Pour Some Sugar On Me 67-77 is flagged without any ear verdict |
| A4 | `REST_RATIO_MIN` 0.05 | **Held on the spike's ear-verified bars; three listening-clip bars rest** | 46 of the 51 resting bars fail the ratio. Need You Tonight's tab bars read 0.080 to 0.307 and hold. Wet Leg 18 (0.029), Pour Some Sugar On Me 77 (0.029) and Summer of '69 0 (0.024) rest although the owner heard those clips play; Pour Some Sugar On Me 7 rests at 0.0499 and Chelsea Dagger 7 holds at 0.0503 |
| A5 | `REST_LOW_SHARE_MIN` 0.005 marks a bar as outside a guitar's register | **Held** | Rests the bell bars (Chelsea Dagger 3-5 at 0.0002 to 0.0006) and Pour Some Sugar On Me 67-68 (0.0002, 0.0026); 7 bars fail it, 5 of them on it alone. Day Tripper bar 1 holds at 0.0077, as the spike warned it would at 0.005 and not at 0.01. Pour Some Sugar On Me 67-68 carry 3 and 7 onsets and are unheard |
| A6 | Chelsea Dagger bars 13-19 hold a real guitar | **Held** | Ratios 0.229 to 0.448, low share 0.26 to 0.69; they print `D-xxxUx-`, now in black |
| A7 | Resting bars do not change the vote on the bars that hold | **Refuted as worded** | The vote reads only holding bars, so leaving bars out changes it: 54 holding bars in seven members print a new row, and two intros (Chelsea Dagger, Need You Tonight) and one instrumental (Pour Some Sugar On Me) flip from uncertain to certain. No unit-2 member has an interior resting bar, so the compressed-list pairing never applied |
| A8 | Removing sustain lines loses nothing the ear wanted | **Held** (built) | No `class="sustain"` on any of the ten sheets (1,210 lines in 1.6) |
| A9 | The mixed strokes on a two-part section are the riff's rhythm | Unchanged, unverified here | No two-part section changed; AC/DC prints as in 1.6 apart from sustain lines |
| A10 | No ear-passed pattern changes | **Held** | Every changed row is in a member with a resting bar; none of the 1.6 listening pass's accepted patterns changed |
| A11 | 1.6 files render under the new page | **Verified** | `test_a_1_6_score_renders_without_sustain_or_labels` (a 1.6 `score.json` fixture through the 1.7 render stage) passes in the full suite; in addition, all ten baseline 1.6 `score.json` files rendered through the 1.7 render stage (`a11_render.py`, PDF stubbed) with 0 sustain lines and 0 labels each |

## Where the figures live

All under `%TEMP%\youkulele-v17-validation\`: `rerun.py`, `rerun.out`, `rerun-times.json` (and `-fix1`), `logs\` (one per run); `probe.py`, `probe.out`, `probe\<song>.json`; `measure.py`, `measure\<song>.json|.txt`, `measure\all.json`, `measure-all.txt`; `summarise.py`, `summary.txt`; `evaluate_all.py`, `evaluate\<song>.txt` and `evaluate\compare-<song>.txt`; `chroma-passers.txt`, `near-floor.txt`, `resting-onsets.json`; `a11_render.py`, `a11.out`, `a11\`; `render_check.py`, `render-check.txt`; `pages\<song>\p<n>.png`; the first round in `snapshot-round1\`, `measure-round1\`, `pages-round1\`, `evaluate-round1\`; the baselines in `baseline\`.

## What the published sources must cover

Written before the runs. For every item, the sources step looks up what published guitar lessons and tab transcriptions say the part is, and compares the chain's output to it.

- **Riff flags that change (spec 4.3):** Pat Benatar "All Fired Up" 61-90; The Beatles "Day Tripper" 52-58; Summer of '69 0-4; The Cars "You Might Think" 0-11. Added after the runs: Pour Some Sugar On Me 67-77 (the fifth flag).
- **Resting stretches of more than two bars (spec 5):** INXS "Need You Tonight" 0-7; Wet Leg "mangetout" 18-25 and 109-112; Pour Some Sugar On Me 7-10, 15-18, 66-68 and 77-79; Chelsea Dagger 0-6.
- **AC/DC "You Shook Me All Night Long", all seven planned sections:** Intro 0-16, Chorus 16-34, Verse 34-43, Verse 43-57, Verse 57-74, Instrumental 74-90, Verse 90-113.
- **The blind song's sections**, once it has run.

## Ground truth from published sources

Two research passes on 2026-10-06 (full tables with every URL in the plan workspace file `sources-ground-truth.md`, copied below in summary). Plain fetching returned no tab content from ultimate-guitar.com and was refused by justinguitar.com and ukutabs.com; a second pass read ultimate-guitar tab text and Songsterr per-track note data in a browser, which answered every row. Songsterr rows are user transcriptions; their bar numbers count from 1 and their tempo is the tab's, so chain bar N is taken as about tab bar N+1 and alignment is by section where the counts disagree (Wet Leg's tab has 76 bars against the chain's 113). No lyrics were read into any record.

| Item | Chain, 1.7 | Published source says | Agree? | Source |
|---|---|---|---|---|
| Summer of '69 0-4, new riff flag | riff heard, not transcribed | Songsterr: tab bar 1 empty, a lead guitar plays chords in tab bars 2-19, the rhythm guitar enters at 12; a songnotes.net lesson describes a picked arpeggio, but of the acoustic Unplugged version | sources disagree with each other; the owner's ear (2026-10-06, `a3_intro_0-4`) heard a picked single-note riff, which stands | songsterr.com/a/wsa/bryan-adams-summer-of-69-tab-s24235; songnotes.net/lessons/25 |
| All Fired Up 61-90, new riff flag | riff heard, not transcribed | Songsterr: one rhythm guitar of chords and power-chord dyads in every bar to tab bar 102; the second guitar is silent to tab bar 90; the single-note riff is at tab bars 97-108 | source contradicts the chain; the owner's 1.6 ear truth for 61-90 was "riff", so ear and source disagree; alignment uncertain (the tab's tempo puts these bars 20 s earlier than the recording) | songsterr.com/a/wsa/pat-benatar-all-fired-up-tab-s233897 |
| All Fired Up 97-104, riff member (1.6) | riff member inside a riff-headed section | Songsterr: continuous single-note sixteenth riff at tab bars 97-108 over bass and drums | agrees | same |
| The Cars 0-11, new riff flag | riff heard, not transcribed | Songsterr: palm-muted eighth-note two-note power-chord dyads on the rhythm guitar from tab bar 1, the lead joining at bar 5 | agrees with the owner ("those are power chords"); a two-note hook the test flags and the gate rejects, as spec A3 says | songsterr.com/a/wsa/cars-you-might-think-tab-s5011 |
| The Cars 52-68, riff (1.6) and bar 62 rests | riff heard; bar 62 empty | Songsterr: bridge tab bars 52-61 a staccato single-note lead riff over synth chords with the rhythm guitar resting; tab bar 63 has no guitar note at all | agrees on both | same |
| Day Tripper 52-58, new riff flag | riff heard, not transcribed | Songsterr: "Solo" marker tab bars 47-58; a solo guitar plays single notes over a rhythm guitar playing chords | agrees (a riff over a strum, as the owner heard in 1.6) | songsterr.com/a/wsa/beatles-day-tripper-tab-s354 |
| Pour Some Sugar On Me 67-77, fifth flag | riff heard, not transcribed; bars 67-68 rest | Songsterr: tab bars 66-68 are an interlude where both guitars play chords; a lead line arrives over the final chorus from tab bar 79 | source contradicts the chain on both the flag and the two rests | songsterr.com/a/wsa/def-leppard-pour-some-sugar-on-me-tab-s5973 |
| Need You Tonight 0-7 rest | eight empty bars | Songsterr: tab bars 1-4 no guitar; a clean guitar plays chords in tab bars 5-8; the riff guitar enters at tab bar 9. Mix magazine: the groove was a drum machine, a sampled bass and the riff | source supports rests on 0-3 and contradicts them on 4-7 (a clean chord guitar), at ratios 0.0001 to 0.020 | songsterr.com/a/wsa/inxs-need-you-tonight-tab-s9844; mixonline.com classic track |
| Need You Tonight 84-85 rest (trailing) | not printed | Songsterr: the tab ends at 82 bars; both guitars silent in its last two bars | agrees as far as the tab goes | same |
| Need You Tonight 13-24 tab | tab printed, as 1.6 | Songsterr: the riff guitar is single notes continuously from tab bar 9; a Lick Library lesson names double stops and palm muting in the riff | agrees that it is the riff; the lesson's double stops are not in the printed tab | same; licklibrary.com top funk riffs |
| Wet Leg 18-25 rest | eight empty bars | Songsterr: the rhythm guitar is silent through verse 1 (tab bars 17-32) and verse 2; bass and drums play | agrees; the owner's 1.6 clip `held_verse_18` heard a cut stroke on bar 18, which carries 6 detected onsets at ratio 0.029 | songsterr.com/a/wsa/wet-leg-wet-dream-tab-s507662 |
| Wet Leg 58-65, riff member, labelled | label "riff heard" on bar 58 | Songsterr: the bridge (tab bars 57-64) carries a continuous single-note lead line with the rhythm guitar silent | agrees | same |
| Wet Leg 109-112 rest (silent Outro, not printed) | not printed | Songsterr's outro has rhythm chords and lead to the end, but its 76 bars do not map onto the chain's 113; by count the chain's bars 109-112 may be the tab's bridge, where the rhythm guitar is silent | undecidable from the source | same |
| Pour Some Sugar On Me 0 and 7-10 rest | empty | Guitar Player: the intro is a picked single-note country figure; Songsterr: tab bars 7-10 have no guitar in either guitar track, two-note shapes from tab bar 11 | agrees on 7-10; bar 0 undecided (the picked figure may start later) | guitarplayer.com Phil Collen interview; songsterr s5973 |
| Pour Some Sugar On Me 15-18 rest | empty | Songsterr: verse 1 continues with two-note guitar shapes from tab bar 11 | source contradicts the rests | songsterr s5973 |
| Pour Some Sugar On Me 66 and 77-79 rest | empty | Songsterr: tab bars 66-68 both guitars on chords; tab bars 75-78 (pre-chorus 3) and 79 on, both guitars on chords with a lead line arriving | source contradicts the rests; the owner's 1.6 clip `held_verse_77` heard a note play through | songsterr s5973 |
| Chelsea Dagger 0-6 rest | empty, chords printed | Songsterr markers: drums from tab bar 1, bass from 5, guitar from 9 (chain bar 8), a pick-up chord at tab bar 8 | agrees | songsterr.com/a/wsa/fratellis-chelsea-dagger-tab-s55960 |
| Chelsea Dagger 10-11 rest | empty | Songsterr: short staccato eighth-note chord stabs from tab bar 9, each followed by a rest | source contradicts the rests (the stem reads ratio 0.0001 on both bars, so the stabs are not in the guitar stem there) | same |
| Chelsea Dagger 13-19 | `D-xxxUx-` black | Songsterr: staccato chord stabs; the owner: power chords | agrees | same |
| Summer of '69 111-121 (unflagged riff, spec 6) | strum | Songsterr: rhythm guitar chords throughout with single-note lead and solo lines on top | the strum print is defensible; a two-part passage | songsterr s24235 |
| Summer of '69 0 (pickup) and 120 rest | 0 empty; 120 trailing, not printed | Songsterr: tab bar 1 empty; tab bar 121 has rhythm chords plus two single-note lines | 0 agrees with the tab, not with the owner's clip; 120 contradicts, but is not printed | songsterr s24235 |
| Day Tripper 94 rest (tail) | empty | Songsterr: tab bar 95 is the final fading bar, riff plus rhythm chords | contradicts as notated; a fade at ratio 0.008 | songsterr s354 |
| All Fired Up 114 rest | empty | Songsterr: tab bars 113-114 guitar 1 two-note shapes, guitar 2 silent | contradicts as notated, at ratio 0.005 | songsterr s233897 |
| AC/DC, all seven sections | strums; no riff flag | yourguitaracademy and Yousician lessons: intro G to D chords with small licks; verses open chords and open power chords; chorus the same shapes arpeggiated; the main riff "single notes plus moveable power chords"; Lick Library teaches rhythm and lead as separate parts | the lessons describe a chordal rhythm part with licks, nearer the chain's print than the owner's "riff over chords" on 34-43 and 90-113; no source says whether two guitars play different parts throughout | yourguitaracademy.com live stream lesson; yousician.com blog; licklibrary.com |
| Fame, nine riff sections (1.6) | riff heard | TrueFire: four electric guitar parts in the lesson; Wikipedia (snippet): Carlos Alomar's riff | consistent with two or more guitars, not decisive | truefire.com/c1932 |

Where the source agrees with the chain (the four spec 4.3 flags apart from All Fired Up 61-90, The Cars 52-68 and bar 62, Wet Leg 58-65 and 18-25, Chelsea Dagger 0-6 and 13-19, Pour Some Sugar On Me 7-10, Need You Tonight 0-3 and the tab), no ear clip was cut. Where sources disagree with the chain or with the owner's earlier verdicts, the ear step below is the tie-break.

## Ear clips

Cut on 2026-10-06 from the 1.7 run folders (`%TEMP%\youkulele-v17-validation\clips\make_clips_v17.py`; files under `%TEMP%\youkulele-ear-v17\<song>\`, listing `listing-v17-validation.md`). Seven stem-alone clips (the guitar stem, not normalised, half a second of the preceding bar first) for resting bars where a published tab says a guitar plays or the owner heard one in 1.6; seven click clips (guitar stem with a click on each printed stroke and a tick on each beat) for the rows that changed because a bar in the member rests, and for the fifth riff flag. AC/DC's six 1.6 ear-truth clips were not re-cut: its strokes are byte-identical to 1.6, so the 1.6 verdicts stand. Verdicts are the owner's words, recorded as given.

| # | Clip | Bars | Question | Verdict |
|---|---|---|---|---|
| 1 | `need-you-tonight\rest_nyt_intro_3-8_stem.wav` | 3-7 | the tab says a clean chord guitar plays bars 4-7; the chain rests them (stem RMS 0.0014 against a peak of 0.318) | |
| 2 | `mangetout\rest_wetleg_verse_17-26_stem.wav` | 17-25 | the tab says the rhythm guitar is silent in this verse; the 1.6 clip heard a cut stroke on bar 18 | |
| 3 | `pour-some-sugar-on-me\rest_pssom_verse_14-19_stem.wav` | 14-18 | the tab says two-note shapes play through verse 1; the chain rests 15-18 | |
| 4 | `pour-some-sugar-on-me\rest_pssom_interlude_65-69_stem.wav` | 65-68 | the tab says both guitars play chords; the chain rests 66-68 | |
| 5 | `pour-some-sugar-on-me\rest_pssom_verse3_76-80_stem.wav` | 76-79 | the tab says both guitars play chords and the 1.6 clip heard a note on 77; the chain rests 77-79 | |
| 6 | `chelsea-dagger\rest_chelsea_intro_7-13_stem.wav` | 7-12 | the tab says chord stabs from bar 8; the chain rests 10 and 11 and prints strokes on 7-9 and 12 | |
| 7 | `summer-of-69\rest_summer_pickup_0-2_stem.wav` | 0-1 | the chain rests the pickup bar; the owner heard the picked riff from the start | |
| 8 | `pour-some-sugar-on-me\flag_pssom_instrumental_67-77.wav` | 67-76 | fifth riff flag, prints `DUDUxUDU-UDUDUDU` black under "riff heard"; the tab says chords | |
| 9 | `chelsea-dagger\changed_chelsea_intro_7-19.wav` | 7-18 | `D-xxxUx-` now black (was grey) | |
| 10 | `need-you-tonight\changed_nyt_intro_8-13.wav` | 8-12 | certain two-bar `D---D---D---D---` / `D-D---DU---U---U` (was one grey down stroke) | |
| 11 | `pour-some-sugar-on-me\changed_pssom_intro_1-7.wav` | 1-6 | `-UDUDUDUDUD-D-D-` (was `DUDUDUDUDUD-D-DU`), grey | |
| 12 | `pour-some-sugar-on-me\changed_pssom_verse1_19-27.wav` | 19-26 | `DUD-D-DU----D---` (was `D-D--UDU----DU--`), grey | |
| 13 | `pour-some-sugar-on-me\changed_pssom_verse3_80-84.wav` | 80-83 | `D-----D----U----` (was `D----------U----`), grey | |
| 14 | `mangetout\changed_wetleg_verse2_26-33.wav` | 26-32 | `D-D-DUDU` (was `D-D-D-DU`) | |
| 15 | `cream-badge\blind_verse1_4-12.wav` | 4-11 | blind song Verse 1, "riff heard", prints `DxxxDxDU`; the tab says a chord guitar | |
| 16 | `cream-badge\blind_verse2_61-70.wav` | 61-69 | blind song Verse 2, "riff heard" uncertain, prints `D-DUD-DU`; the tab says chords | |

(Verdicts to be recorded.)

## Blind song

Cream, "Badge" (https://www.youtube.com/watch?v=4hjVjYfLMjI), chosen by the owner on 2026-10-07 and run from ingest at commit `cbc40ad` (`logs\blind.txt`, exit 0; run folder `runs\cream-badge`). Figures recorded, not judged (expectation 8).

| Figure | Value |
|---|---|
| Grid | 70 bars, 107.9 bpm, 4/4; 7 sections: Intro 0-4, Verse 1 4-28, Instrumental 1 28-34, Chorus 1 34-50, Instrumental 2 50-56, Chorus 2 56-61, Verse 2 61-70 |
| Key | D major, confidence 0.49 (score margin 0.174; runner-up A) |
| Strums source | guitar stem, ratio 0.56, 8 slots per bar, grid fit 0.88 |
| Resting bars | none (no bar fails either test) |
| Riff flags | Verse 1 4-28 (entropy 0.70, single 0.52, pitch change 0.57, rule A; gate 0.22, 0.27, 0.71: fails); Instrumental 1 28-34 (0.82, 0.57, 0.69, rule A, uncertain; gate 0.05); Verse 2 61-70 (0.69, 0.62, 0.70, rule A, uncertain; gate 0.08). All three print "riff heard, not transcribed"; no tab |
| Other headers | Intro `DUDxDUDx` certain; Chorus 1 `--DUDUDU` certain (p 0.047); Instrumental 2 `-UD-D-DU` pattern uncertain; Chorus 2 `D-D-DUD-` certain |
| Labels, sustain lines | none, 0 |
| Pages | 2 |

Against the published sources (Songsterr s4135, 106 bpm, 71 bars; Beatles Bible; Skidmore listening guide): the tab has a chord guitar from bar 1 with the bass and piano from bar 5, no lead or arpeggio guitar until the bridge, the single-note arpeggio figure in the bridge, a solo after it, and two guitar parts throughout (the sources disagree on which player takes which). The chain's Instrumental 1 (28-34, about 1:04 to 1:17) falls where the bridge arpeggio is, and its "riff heard" agrees with the source. Its "riff heard" on Verse 1 and Verse 2 does not: the source has a chord guitar there. Both verses have pitch-change shares of 0.57 and 0.70 and single shares of 0.52 and 0.62 on the guitar stem, so either the separator put the arpeggio or lead part on the guitar stem under the verses, or the chord guitar's part is picked rather than strummed; the 1.6 limitation line about two guitars on one stem covers the print. The key the chain names (D major) differs from the researcher's reading of the tab (G major or E minor, an inference). Clips for the owner: `cream-badge\blind_verse1_4-12.wav` and `cream-badge\blind_verse2_61-70.wav` (clicks on the printed strokes).
