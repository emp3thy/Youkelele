# Chord recognition, no-chord handling and key detection: applied to the Youkelele code

Date: 2026-10-03. Input: `chords-research.md` (same folder) and its measurement scripts. This report checks each research finding against the code in `src/youkelele/` (main checkout and the v1.2 worktree) and the four run folders under `runs/`, then turns the ones that fit into concrete changes. Nothing under the project was edited; the two check scripts written for this report are `research/apply/chords_run_stats.py` and `research/apply/key_design_check.py`.

Line numbers refer to the main checkout unless marked "worktree" (`.claude/worktrees/v1-2`, where `stages/harmony.py` and `music/fill.py` differ).

## 1. What the runs show today

From `03_harmony/chords.json`, `02_grid/grid.json`, `05_arrange/arrangement.json` and `06_score/score.json` of the four v1.1 runs (`chords_run_stats.py`):

| Song | Events | `N` share | All-`N` bars | Chord events starting on beat 2 | Sub-beat chord events | Key printed (confidence) | Truth |
|---|---:|---:|---|---|---:|---|---|
| Chelsea Dagger `sexhetcxqy4` | 68 | 0.063 | 9 of 142 (bars 0 to 8) | 10 of 67 | 0 | D major (0.006) | D or G major, unverified |
| Summer of '69 `9f06qzcvuhg` | 76 | 0.046 | 6 of 121 (0, 116 to 120) | 2 on beat 1 | 0 | D major (0.056) | D major |
| Pour Some Sugar On Me `0uib9y4ofps` | 82 | 0.271 | 24 of 103 | 23 of 74 on beat 2, 5 on beat 1 | 5 | C# major (0.010) | C# minor |
| Wet Leg "mangetout" `lbc6ccztp5e` | 67 | 0.038 | 4 of 113 (109 to 112, non-song tail) | 4 off beat 0 | 0 | C major (0.136) | unverified, C major likely |

Every raw label is `maj`, `min` or `N` (Chelsea 8 chord labels, S69 7, PSSOM 6, Wet Leg 4), so `music/triads.py` changes nothing on these songs. Every event's snap confidence is at least 0.90 except one PSSOM event at 0.53; the median is 0.97 to 0.99, so `ChordEvent.confidence` as computed in `music/snap.py:21` carries almost no information about which labels are doubtful.

PSSOM's 24 all-`N` bars: 0, 8 to 10, 15 to 18 (a cappella intro), 43 to 46 (verse 2, "N.C." on the published chart), 66 to 71, 73, 74, 77 to 80 (solo and breakdown). The v1.2 fill (worktree `music/fill.py`, measured in `docs/superpowers/specs/2026-10-03-v1-2-fill-measurements.md`) fills 12 of them across the four songs: Chelsea 3, 4, 8; PSSOM 8, 44, 45, 68, 70, 71, 74; S69 118, 119.

The three user-facing failures the research names are all confirmed in these artifacts: a whole intro and most of a solo printed `N.C.`, a wrong key mode in the header (`score.json` key `"C# major"`, rendered by `render/html.py:72`), and the no-third riff printed as a major chord (`C#:maj` is 41.1 percent of PSSOM's chord time, printed as `A` at capo 4).

## 2. Finding-by-finding verdicts

| Research finding | Checked against | Verdict |
|---|---|---|
| Decoder is called with `use_beats=False`; beats and downbeats fix boundaries | `~/.youkelele/models/chord_cnn_lstm/chord_recognition.py:27` passes `False` only; `extractors/xhmm_ismir.py:170-184` builds `beat_arr` from `entry.beat`; `beat_decode_out/summary.json` | **Applies.** S69 75/75 changes on bar starts (was 66/75), PSSOM 84 to 75 events, sub-beat fragments 4 to 1. Section 3.1 |
| No power-chord class; chroma third test fails | `data/submission_chord_list.txt`; `third_test.py`; `music/shapes.py:11-33` has no `5` suffix and `chords-db/ukulele.json` has no `5` entries at all | **Applies, and the shapes gap is new:** a `X:5` label cannot be given a diagram today; `to_triad("C#:5")` returns `C#:maj` (`triads.py:33`). Section 3.4 |
| Mode at a fixed tonic on the harmonic stems is right 4 of 4 | `key_design_check.py` on `chroma_means.json` | **Applies, stronger than stated:** all three profiles (Krumhansl, Kostka-Payne, Albrecht-Shanahan) agree on the mode at every candidate tonic in every song; PSSOM C# minor by 0.34 to 0.38. Section 3.2 |
| Three profiles disagreeing is a confidence signal | same | **Discard.** On the harmonic stems the 24-way winners disagree on all four songs (PSSOM C#m/B/E, S69 A/D/D, Chelsea D/D/G, Wet Leg C/C/F), including the two whose key is certain, so disagreement carries no signal. Only the fixed-tonic mode vote is useful |
| Stems do not rescue Chelsea's intro; fill would print `B` on bars 2 and 6 | `stems_out/summary.json` (guitar+other `N` 1.0); fill-measurements table | **Half applies.** Stems do not help (confirmed). But bars 2 and 6 are rejected by the energy gate (ratios 0.106 and 0.013, guitar stem at most 0.004 RMS), not by the match threshold, so the research's "`FILL_MIN_MATCH` no lower than 0.5" is not needed on this evidence; the worktree's measured 0.32 / 0.05 / 0.2 stand. Section 3.3 |
| Stems rescue PSSOM's solo and recover `D:maj` | `stems_out/0uib9y4ofps_guitar_other.lab`: `D:maj` 195.1 to 200.6 s and 205.8 to 210.5 s; fill table bar 74 fills `A` at 0.334 while the unrestricted template picks `D` at 0.56 | **Applies.** The v1.2 fill will print `A` on bar 74 where the record plays `D`. Sections 3.3 and 3.5 |
| State of the art is within two points; do not swap recognisers | PyPI and licence checks in the research | **Applies.** `options.py:18` already has `chord_model: "chordmini"` and `preflight.py:93` marks it unsupported; leave it there. Section 5 |
| Rock tonic from duration-weighted chord roots, not diatonic sets | root shares measured: PSSOM C# 0.415, S69 D 0.402 vs A 0.396, Chelsea G 0.382 vs D 0.317, Wet Leg C 0.527 | **Applies with the section-end tie-break:** S69 section-end chords D 6 vs A 4 and final chord D; Chelsea section ends G 4, final G. Section 3.2 |
| Albrecht-Shanahan profiles handle minor better | `key_design_check.py` | **Marginal here.** AS gives the smallest fixed-tonic margins of the three (PSSOM 0.342, S69 0.105, Chelsea 0.102 to 0.153) and the 24-way AS winner is wrong on S69 stems (D major 0.893, right) but F major on Wet Leg. Use as a tie-break only, not as the primary profile |
| Mauch 2009 voting across repeated sections | `grid.json` sections: Chelsea choruses are 29, 10, 6 and 37 bars; S69 choruses 12, 12, 12; PSSOM choruses 11, 12, 19 | **Weak fit.** Same-label sections rarely have equal bar counts, and `Section` carries no cluster id (`schemas.py:52-56`), only the label. Section 4.1 |
| Second recogniser pass on stems for all-`N` bars | `stems_out` labs; `models/chords.py:30` takes any wav | **Applies**, with a cost of one more model run (harmony took 9.5 to 12.6 s per song). Section 3.5 |
| Chord-level decoding over beats with a duration prior | needs raw posteriors; `beat_decode_experiment.py` shows the in-process path works | Deferred; the beat-aware decoder gives most of the readability gain first. Section 4.2 |
| Essentia, madmom, Chordino, BTC weights, crema, ChordFormer, DECIBEL, madmom key CNN | licences and wheels as verified in the research | **Discard** for a CPU-only Windows Python 3.12 pipeline with permissive licences (no Windows wheels or AGPL; CC BY-NC-SA models; GPL and Linux-only wrapper; TensorFlow; no code; tab-site terms). Section 5 |

## 3. Improvements, ordered by impact per effort

### 3.1 Decode with the chain's beats and downbeats

**Touches.** `src/youkelele/models/chords.py:30-54` (`recognise_chords`), `src/youkelele/stages/harmony.py:41` (main) or worktree `:66` (the recogniser call; `grid` is already loaded two lines earlier), a new driver module `src/youkelele/models/chord_driver.py`, tests in `tests/test_stage_harmony.py:94-119`. The vendored code needs no patch: `extractors/xhmm_ismir.py:186` already accepts `use_beats` and `use_downbeats`, and `io_new/beatlab_io.py:16` reads a three-column tab file taking `tokens[0]` (time) and `tokens[2]` (position in bar).

**Evidence.** Same posteriors, decoded five ways (`beat_decode_out/summary.json`): with beats and downbeats at the default penalties 30 / (15, 45, 100), S69 changes on bar starts 66/75 to 75/75; PSSOM events 84 to 75, changes on a beat 51/83 to 73/74, `N` 0.277 to 0.264; Chelsea on-bar 54/68 to 58/68. Chord sets unchanged. In PSSOM the removed events are the sub-beat fragments at 164.1 s (0.51 s `E`), 164.6 s (0.56 s `A`), 243.2 and 243.7 s (0.58 and 0.49 s) and two 0.84 to 0.88 s `F#` slivers; the 1.42 s half-bar `E` / `A` chorus changes survive because they are on beats (the published chart writes them that way). Lower penalties (variants d, e) add fragments and inversions; keep the defaults. In the shipped run `snap_to_beats` (`music/snap.py:24`) votes per beat because the model's boundaries lag by 0.1 to 0.4 s (spike B); with beat-aware decoding the boundaries are on beats by construction and the vote becomes a safety net only.

**Design.**
1. `chord_driver.py` is a small script run as the child process instead of `chord_recognition.py`: it does `sys.path.insert(0, os.getcwd())`, builds the `DataEntry` exactly as `chord_recognition.py:15-26` does, calls `entry.append_data(beats, BeatLabIO, "beat")` when a beats file is given, and calls `hmm.decode_to_chordlab(entry, probs, False, use_beats=True, use_downbeats=True)`. `beat_decode_experiment.py:76-105` is a working template.
2. `recognise_chords(wav, work_dir, log, beats: Sequence[tuple[float, int]] | None = None)` writes `work_dir/beats.lab` as `time \t index \t position` lines and appends its path to the argv. Positions come from `grid.bars`: for `bar in grid.bars`, `for pos, bi in enumerate(bar.beats): (grid.beats[bi], pos + 1)`. A pickup bar gives position 1 alone, which `__get_beat_arr` (`xhmm_ismir.py:178-183`) tolerates; `num_beat_per_bar` is the maximum position seen, so 4/4 gets the half-bar class at position 3.
3. `HarmonyStage.run` passes the tokens. One caveat to test: between two beat frames `decode` (`xhmm_ismir.py:117-128`) forbids any change, so the beats must be the gap-filled list in `grid.beats` (they are; spec 1.2 section 3.2 uses the same list).
4. Record `ctx.note("decoding", "beats+downbeats")` so the manifest says which decoder produced the run.

**Measure.** Re-run the four songs `--from harmony`; expect S69 75/75 on bar starts, PSSOM about 75 events with at most one event under a beat, Chelsea on-bar changes 58 or more, no change to the chord sets or to `N` outside PSSOM. Add the on-beat and on-bar shares to the diagnostics in 3.6.

**Effort** small. **Impact** medium-high: every PSSOM chorus bar prints cleanly, the S69 chart is bar-exact. **Confidence** 88 percent; measured on three songs, Wet Leg not yet decoded this way.

### 3.2 Key: tonic from chord roots, mode at that tonic on the harmonic stems

**Touches.** `src/youkelele/music/key.py:17-35` (`estimate_key`, `chroma_mean_for`), worktree `src/youkelele/stages/harmony.py:70-75` (the harmonic mix and `bar_chroma` already exist there), `src/youkelele/schemas.py:100-103` (`Key`), `src/youkelele/music/score_builder.py:181` and `src/youkelele/render/html.py:31-39,72-73` (header text), `tests/test_key.py`.

**Evidence** (`key_design_check.py`). On the summed guitar, bass, piano and other stems the mode decided at a fixed tonic is right on all four songs with every profile: PSSOM at C# minor by 0.379 (Krumhansl), 0.336 (Kostka-Payne), 0.342 (Albrecht-Shanahan); S69 at D major by 0.299 / 0.148 / 0.105; Chelsea major at G by 0.313 / 0.201 / 0.153 and at D by 0.347 / 0.188 / 0.102; Wet Leg at C major by 0.220 / 0.175 / 0.118. On the mix PSSOM is a coin toss (Krumhansl major by 0.004, Albrecht-Shanahan minor by 0.026), which is why `chords.json` carries confidence 0.010. The 24-way search is unreliable on any source (stems flip S69 to A major 0.883 vs 0.807, the dominant-key tendency music21 documents for Krumhansl-Schmuckler), so the tonic must come from the chords. Tonic cues measured: root time share PSSOM C# 0.415 (next B 0.257), S69 D 0.402 vs A 0.396, Chelsea G 0.382 vs D 0.317, Wet Leg C 0.527; final sounding chord D, G, C# (a passing chord), B (PSSOM fades on V); chord sounding in each section's last bar: S69 D 6 of 11, A 4; Chelsea G 4 of 8; Wet Leg C 11 of 25, F 10; PSSOM B 3, C# 2, `N` 2. Section-start chords are not a cue (S69 choruses start on Bm).

**Design.**
1. New `estimate_key_from_chords(events, bar_chroma, bars, sections) -> Key` in `music/key.py`:
   - candidates: roots with at least 0.2 of chord time (S69 D and A; PSSOM C# and B; Chelsea G and D; Wet Leg C and F);
   - tonic score = root share + 0.10 if it is the final chord whose event lasts at least a bar (excludes Wet Leg's half-bar C#) + 0.15 times the share of sections ending on it. Measured results: PSSOM C# (0.415 + 0.043) over B (0.257 + 0.1 + 0.064); S69 D (0.402 + 0.1 + 0.082) over A (0.396 + 0.055); Chelsea G (0.382 + 0.1 + 0.075) over D (0.317 + 0.019); Wet Leg C (0.527 + 0.066) over F (0.333 + 0.06). The unverified Chelsea moves from D to G, which the detected C and Am fit better (lessons: 94.7 against 91.0 percent diatonic);
   - mode = sign of Krumhansl major minus minor correlation at that tonic on the duration-weighted mean of `bar_chroma` (already computed for the fill, so no second CQT); `confidence` = that margin, clipped to [0, 1];
   - fall back to the current `estimate_key(chroma_mean_for(wav))` when fewer than four chord events exist.
2. `Key` gains `method: Literal["mix_krumhansl", "chords_stems"] = "mix_krumhansl"` and `mix: Key | None = None` holding the old estimate for the validation table; schema version stays 1.
3. Header: print "C# minor" as today; the capo shape key in `_shape_key` (`html.py:31`) follows automatically (A minor at capo 4).

**Measure.** Expect PSSOM "C# minor" with confidence about 0.38, S69 "D major" about 0.30, Chelsea "G major" about 0.31, Wet Leg "C major" about 0.22, and the Fame blind test recorded. Keep `mix` in the JSON so the table can show both.

**Effort** small to medium. **Impact** high: fixes the one wrong header and is the prerequisite for 3.4. **Confidence** 85 percent; four songs, Chelsea's truth unverified.

### 3.3 Refine the v1.2 fill where the measurements disagree with it

**Already in progress:** `fill_silent_bars`, its three constants and the italic rendering (spec 1.2 sections 3.4 and 4). What follows amends it; it does not re-propose it.

**Touches.** Worktree `src/youkelele/music/fill.py:107-118` (`_song_chords`), `:121-131` (`_best_match`), `:160-175` (the fill loop), `tests/test_fill.py`.

**Evidence.** The fill-measurements table shows the restriction to the song's chord set choosing the wrong chord where an out-of-set chord is what the record plays: PSSOM bar 74 fills `A` at 0.334 (margin 0.081) while the unrestricted best is `D:maj` at 0.56; bar 67 would be `A` 0.442 but is energy-gated; bars 69 and 73 pick `D` at 0.37 and 0.39 unrestricted against in-set 0.23 and 0.19. The stems recogniser pass independently labels 195.1 to 200.6 s and 205.8 to 210.5 s `D:maj`. The research's threshold advice (match at least 0.5, margin 0.15) is not supported: the barre `B` on Chelsea bars 2 and 6 is already rejected by energy (ratios 0.106 and 0.013), and the two doubtful fills that do pass, PSSOM 44 and 45 (`E` at 0.655 and 0.719 in the "N.C." verse) and S69 118 and 119 (`A` 0.464, `Bm` 0.476 in the fade), pass any threshold up to 0.46, so a higher `FILL_MIN_MATCH` would only remove true positives (bars 70 and 74 at 0.38 and 0.33). Keep 0.32 / 0.05 / 0.2.

**Design.**
1. `_best_match` scores all 24 major and minor templates and returns both the in-set best and the overall best.
2. An out-of-set winner is accepted only when it beats the in-set best by at least `FILL_OUT_OF_SET_MARGIN = 0.15` **and** the same out-of-set label wins in at least one other candidate bar of the same `N` run (bars 67, 69, 73 and 74 all pick `D`; no other song has a repeated out-of-set winner, Wet Leg 109 to 112 pick in-set `C#` at 0.22 to 0.30). This "run agreement" gate is used instead of the research's "diatonic to the key" gate, because `D` is not diatonic to C# minor (it is bVII of the E Mixolydian bridge) and would be rejected.
3. For a candidate bar that passes energy but fails the match (PSSOM 69 and 73, the lead line, r 0.23 and 0.19; Wet Leg 109 to 112), set a new `ChordEvent.riff: bool = False` instead of leaving plain `N`; `render/grid.py:26-31` (`cell_for`) prints "riff" in the cell rather than "N.C.". Chelsea's bars 0 to 2 and 5 to 7 stay `N.C.` because their stems are drums only (guitar at most 0.004 RMS), which contradicts the research's picture of a melodic riff there; the per-bar stem RMS table is the better evidence.

**Measure.** PSSOM bars 67 (if energy allows after 3.5), 69, 73, 74 print `D` or `riff`, never `A`; S69, Chelsea, Wet Leg fills unchanged; count of out-of-set fills recorded in the harmony note.

**Effort** small. **Impact** medium: one wrong chord becomes right and two lead-line bars stop pretending. **Confidence** 75 percent: the `D` evidence comes from one song and two independent methods, but the run-agreement gate is tuned on it.

### 3.4 Power chords: decide by key, print the key's quality

**Touches.** Worktree `src/youkelele/stages/harmony.py` after the key (new step), `src/youkelele/music/triads.py:17-34` (`to_triad` must not turn `X:5` into `maj`), `src/youkelele/music/shapes.py:11-33` (`HARTE_TO_SUFFIX`, no `5`), `src/youkelele/music/arrange.py:123-139` (`simplify_for_tier`), `src/youkelele/schemas.py:106-114`, `tests/test_triads.py`, `tests/test_arrange.py`.

**Evidence.** PSSOM's riff is `C#:maj` for 41.1 percent of chord time and prints as `A` at capo 4; the published chart prints C#m. The chroma test proposed in lessons item 7 fails: the third-to-fifth ratio for PSSOM `C#:maj` is 0.69, above genuine major triads (0.48 to 0.63), because the fifth harmonic of a distorted root lands on the major third (`third_test.py`). The model has no `5` class. `mir_eval.chord.split("C#:5")` works and `QUALITIES["5"]` is `[1,0,0,0,0,0,0,1,0,0,0,0]`, but `to_triad("C#:5")` returns `C#:maj` (max-overlap fallback, `triads.py:33`), `harte_to_db("C#:5")` returns `None`, and `chords-db/ukulele.json` has no `5` suffix for any root, so today an `X:5` label would silently print as major.

**Design.**
1. After 3.2, in the harmony stage: when `key.mode == "minor"`, the mode margin is at least 0.2, and a `maj` label on the key's tonic covers at least 0.2 of chord time, relabel those events `label = "C#:5"`, `triad = "C#:min"` (the key's diatonic quality), and set `ChordEvent.power: bool = True`. The 0.2 share gate stops a one-bar Picardy or borrowed major tonic from being relabelled. Do not touch other `maj` labels: the research's wider rule ("a maj root diatonic only as minor") would relabel S69's and Chelsea's genuine majors in a major key, and in a minor key it would hit PSSOM's `B` and `E`, which are real major chords.
2. `to_triad`: return the label's own root with quality `5` unchanged when the quality is `5` (so arrange can see it), or accept the triad passed in from the stage; the simplest is to make the stage write `triad` explicitly and leave `to_triad` for model labels.
3. Arrange: `simplify_for_tier` maps `X:5` to the event's `triad` (C#:min) for the `easy` tier. For the `full` tier add a tiny built-in table of two-string root-fifth ukulele shapes (G C E A order, for example C#5 as `x 1 1 x` is not a true power chord on re-entrant tuning; the honest default is the minor triad, so print `C#m` and add `(power chord on the record)` to the chord legend line). chords-db cannot supply `5` shapes, so no database change.
4. Render: `ChordDiagram` for a power-chord label shows the minor shape with a small "5" badge, or nothing extra in the easy tier.

**Measure.** PSSOM: header "C# minor", riff cells `Am` at capo 4 (the `Am` shape already appears for the 0.5 s `C#:min` event), legend `Am` once; capo stays 4 (validation measured capo 4 winning by 0.47 and the lessons note the margin holds with C#m). S69, Chelsea, Wet Leg: no change (major keys).

**Effort** medium. **Impact** medium: one song's most-used chord prints as the published chart has it. **Confidence** 65 percent: a single song exercises the rule, the margin and share gates are set on it, and whether a ukulele player prefers `Am` or a two-string shape is a product decision.

### 3.5 Second recogniser pass on guitar+other for all-`N` bars

**Touches.** Worktree `src/youkelele/stages/harmony.py:64-73` (between the mix pass and the fill), `src/youkelele/models/chords.py:30` (already takes any wav path), `src/youkelele/music/snap.py:24` (reuse on the second span list), `tests/test_stage_harmony.py`.

**Evidence.** `stems_out/summary.json`: over 189.5 to 237.5 s PSSOM `N` falls from 0.683 (mix) to 0.515 (four harmonic stems) to 0.388 (guitar+other), and `D:maj` appears at 0.213 of the window; the `.lab` has `D:maj` 195.1 to 200.6 s and 205.8 to 210.5 s, `E:maj` 200.6 to 205.8 s and 211.9 to 217.3 s. The whole-song `N` share on guitar+other is *worse* (0.326 against 0.277) and the stems add spurious inversions (`F#:maj/5`, Chelsea `D:maj/5`), matching Mitoma and Furuya's finding that amplified stems create false labels; so the stems pass must only fill bars the mix pass left all-`N`. Chelsea's intro gains nothing (`N` 1.0 on guitar+other). Cost: one more model run, 9.5 to 12.6 s per song on this CPU.

**Design.**
1. Write `work_dir/guitar_other.wav` (mono sum of `guitar` and `other` stems; `harmonic_mix` already sums stems) and call the same recogniser (with beats, after 3.1).
2. Snap the stems spans with `snap_to_beats`, then for each bar that is all-`N` on the mix pass and has a chord on the stems pass with `confidence >= 0.75`, take the stems events for that bar; mark them `filled = True` and add a new `ChordEvent.source: Literal["mix", "stems", "template"] = "mix"` so the sheet and the validation table can tell the three origins apart.
3. Run the template fill afterwards for what remains; with 3.3 the `D` bars will usually be settled by this pass first.
4. Run order matters for the key (3.2): compute the key after both passes so recovered chords count.

**Measure.** PSSOM bars 67 to 74: expect `D`, `E`, `D`, `E` where the stems lab has them, `N` share below 0.22; S69, Chelsea, Wet Leg unchanged (their all-`N` bars are silent, fade or non-song audio). Record "stems pass filled k bars" in the harmony note.

**Effort** medium. **Impact** medium: fixes 6 of PSSOM's 11 solo `N` bars with the chords the record plays, not a nearest in-set guess. **Confidence** 70 percent: measured on one passage; the 0.75 confidence gate is a guess to be set on the Fame blind test as well.

### 3.6 Diagnostics for the validation table and the harmony log

**Touches.** `src/youkelele/evaluate.py:101-139` (`evaluate_run`, `Report`, `format_report`), `src/youkelele/commands.py:126-137` (`evaluate_command`), worktree `src/youkelele/stages/harmony.py:76-82` (`ctx.log` and `ctx.note`).

**Evidence.** The chain's only accuracy report needs hand truth (`chords.lab`, `beats.txt`), which exists for none of the four songs, so every number in the specs was produced by one-off scratchpad scripts (`analyse.py`, `chords_run_stats.py`, `beat_decode_experiment.py`). The numbers that decided this report are cheap: `N` share, all-`N` bar count, changes on beat 0 and on bar starts, events shorter than a beat, key margin, filled bars by source.

**Design.**
1. `Report` gains truth-free fields: `n_share`, `all_n_bars`, `changes_on_bar_share`, `sub_beat_events`, `key_confidence`, `key_mix` (from `Key.mix`), `filled_by_source`; `evaluate_run` fills them even when `truth_dir` is missing or empty, and `format_report` prints them.
2. `evaluate --compare <other run dir>` computes `mir_eval.chord.overseg`, `underseg` and `seg` plus `majmin` between the two `chords.json` files, so a change to the decoder or the fill is scored against the previous run without hand truth (a regression guard, not an accuracy claim).
3. The harmony stage logs `N` share, all-`N` bars, on-bar share and the key with its margin, and notes `decoding`, `key_method`, `filled_stems`, `filled_template`.

**Effort** small. **Impact** medium (indirect): every change in this report becomes measurable in one command. **Confidence** 90 percent.

## 4. Lower priority or deferred

### 4.1 Vote labels across repeated sections (Mauch 2009)

`Section` holds `label`, `start_bar`, `end_bar`, `confidence` only (`schemas.py:52-56`); the cluster id is not saved, so "same cluster" means "same label". Same-label sections have unequal lengths on three of four songs (Chelsea choruses 29, 10, 6, 37 bars; PSSOM 11, 12, 19), so position-wise voting rarely has partners, and the beat-aware decoder (3.1) already moves Chelsea's on-bar changes from 54 to 58 of 68. Of Chelsea's ten beat-2 changes, four are long (5.4 to 6.2 s `Em` and `Bm` in the verses, plausibly real half-bar changes or a late boundary) and six are two-beat `D` events in bars 110 to 122 of the final chorus, which could be a genuine `G / D` alternation. Without a listening check there is no ground to overwrite them. Defer until 3.1 and 3.6 show what is left. **Effort** medium, **impact** low, **confidence** 45 percent.

### 4.2 Chord-level decoding over the beat grid with a duration prior

Needs the raw posteriors in-process (`beat_decode_experiment.py:85-90` shows how) and a new Viterbi over beat tokens with a prior favouring two- and four-beat chords. Korzeniowski and Widmer measured about one WCSR point; here the readability gain (no one-beat chords unless strongly supported) is the point. After 3.1 the remaining sub-beat events are one in PSSOM and none elsewhere, so the marginal gain is small on these songs. **Effort** large, **impact** low to medium, **confidence** 55 percent.

### 4.3 ChordMini as a second opinion

The option plumbing exists (`options.py:18`, `cli.py:48`, `preflight.py:93`), the code is MIT and the student models are 2.2M to 3.03M parameters on the same torch stack, but the checkpoint licence is unstated and the teacher weights are CC BY-NC-SA, and the published numbers (Majmin 80.24) are below the vendored model. Only worth it as an agree/disagree confidence per beat, which 3.6 would then expose. Keep unsupported until the licence is clarified. **Effort** large, **impact** low, **confidence** 40 percent.

### 4.4 Albrecht-Shanahan and Kostka-Payne profiles

Measured to agree with Krumhansl on the mode at every candidate tonic; on the 24-way search they disagree with it on every song. Add them only as a three-way mode vote inside 3.2 (flag `confidence = 0` when they split), which costs two correlations. **Effort** small, **impact** low, **confidence** 60 percent that the flag ever fires on real songs.

## 5. Discarded for this pipeline

- **Essentia** (`Key`, `ChordsDetectionBeats`): no Windows wheels, AGPL.
- **madmom** chord and key models: PyPI build stops at Python 3.9, git main needs Cython and MSVC, models CC BY-NC-SA.
- **Chordino / NNLS Chroma** and `chord-extractor`: GPL, Python below 3.12, Linux binary.
- **BTC original weights**: CC BY-NC-SA. **crema**: TensorFlow and Keras dependency footprint. **ChordFormer**, **event-based seq2seq**: no code or weights.
- **DECIBEL-style tab fusion**: tab-site terms and the project's "no lyrics" rule; at most a user-supplied chord file later.
- **Fine-tuning a `5` class**: large; 3.4 covers the one measured case without training.
- **Supervised key CNN** (madmom): non-commercial licence; 3.2 reaches the right answer on all four songs with templates.
- **Raising `FILL_MIN_MATCH` to 0.5 and `FILL_MIN_MARGIN` to 0.15**: contradicted by the per-bar measurements (section 3.3).
- **Profile disagreement as a confidence flag**: no signal on these songs (section 2).

## 6. Suggested order

3.1 (beats to the decoder) and 3.6 (diagnostics) first, since together they make every later change measurable and 3.1 changes event boundaries that 3.3 and 3.5 operate on. Then 3.2 (key), which 3.4 depends on. Then 3.5 (stems pass) before 3.3's out-of-set rule, because the stems pass settles most of the PSSOM `D` bars and leaves the template rule fewer cases. 3.4 last, after the key has been checked on the Fame blind test.
