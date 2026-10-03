# Applied: ukulele arrangement, chord simplification and key, tested against the code and the four runs

Date: 2026-10-03. Input: `arrange-research.md` (same folder). Code read: `src/youkelele/{music,stages,render}/` and `schemas.py` in the main checkout (read-only) and the committed state of the v1.2 worktree (`d5c3b88`, which adds `music/fill.py`, `passing_labels`, `ChordEvent.filled`, `ArrangedChord.passing`). Run artifacts read: `runs/{sexhetcxqy4,9f06qzcvuhg,0uib9y4ofps,lbc6ccztp5e}/0{0,1,2,3,5,6}_*`. Nothing under the project was edited. Measurement scripts are in this folder: `analyse_runs.py`, `probe_db.py`, `third_test.py`, `dump_chroma.py`, `key_variants.py`, `run_full_dict.py`.

Line numbers refer to the main checkout unless marked `[wt]` for the v1.2 worktree.

## 1. What the runs actually show (measured today)

| | Chelsea Dagger | Summer of '69 | Pour Some Sugar On Me | Wet Leg "mangetout" |
|---|---|---|---|---|
| Key shipped (confidence) | D major (0.006) | D major (0.056) | C# major (0.010) | C major (0.136) |
| Krumhansl on the mix, top two | D 0.768, G 0.762 | D 0.844, A 0.797 | C# major 0.550, C# minor 0.546 | C 0.695, F 0.601 |
| Krumhansl on bass+guitar+piano+other, top two | D 0.845, G 0.778 | **A 0.883**, D 0.807 | **C# minor 0.716**, E 0.637 | C 0.710, F 0.604 |
| Diatonic chord-time share, top pairs (strict quality) | G/Em 0.947, D/Bm 0.910 | D/Bm 0.930, A/F#m 0.877 | F#/D#m 0.696, E/C#m 0.562 | C/Am 0.988 = F/Dm 0.988 |
| Chord time of the most used root; first and last chord | G 35.8%; G, G | D 38.3% (A 37.8%); D, D | C# 30.0%; C#, B | C 50.7%; C, C# |
| Events / N events / N time | 68 / 1 / 6.3% | 76 / 2 / 4.6% | 82 / 8 / 27.1% | 67 / 1 / 3.8% |
| Non-N events lasting one beat | 0 | 0 | 6 | 1 |
| Non-N events lasting two beats | 13 (all on beats 1 or 3) | 0 | 43 | 2 |
| Event start beat (0-based) | 0: 57, 2: 10 | 0: 72, 1: 2 | 0: 46, 2: 23, 1: 5 | 0: 62, 3: 2, 1: 1, 2: 1 |
| Score cells: N.C. / two names / three names | 9 / 10 / 0 | 6 / 2 / 0 | 24 / 26 / 1 | 4 / 4 / 0 |
| Capo; score at capo 0..5 (unique-label mean + 0.2 per fret) | 0; 1.93 3.94 2.04 3.51 3.10 3.30 | 0; 2.01 3.60 2.34 3.10 3.86 2.47 | 4; 3.28 2.32 2.92 4.27 1.85 4.57 | 0; 2.00 2.88 3.30 3.28 4.18 2.50 |
| `label != triad` events | 0 | 0 | 0 | 0 |
| `no_capo_alternative` entries written / rendered | 0 / 0 | 0 / 0 | 74 / 0 | 0 / 0 |
| Legend | G D A C Bm(barre) Em Am B(barre) | D A Bm(barre) G F Bb(barre) C | A D G C F Am (all open) | C F Dm C#(barre) |

Two measurements overturn research items as written, and one supports the research more strongly than it claimed:

**(a) The chroma "third test" for power chords does not separate PSSOM's riff from real major chords.** Per event, on the summed harmonic stems, third energy over fifth energy (`third_test.py`):

| Chord (song) | n | time | median third/fifth | min | share below 0.5 |
|---|---|---|---|---|---|
| C#:maj, the no-third riff (PSSOM) | 6 | 86.9 s | **0.63** | 0.59 | 0.00 |
| A:maj, a real triad (PSSOM) | 18 | 26.1 s | **0.38** | 0.28 | 0.89 |
| F#:maj (PSSOM) | 5 | 5.7 s | 0.32 | 0.18 | 1.00 |
| A:maj (Summer of '69) | 27 | 78.2 s | 0.46 | 0.26 | 0.67 |
| B:min (Summer of '69) | 9 | 15.7 s | 0.39 | 0.30 | 1.00 |
| C:maj (Wet Leg) | 24 | 107.0 s | 1.01 | 0.52 | 0.00 |

The distorted riff shows a stronger major third in chroma than the clean triads do (the fifth harmonic of a distorted root lands on the major third; `chroma_cqt` folds it in). Any threshold that flags C# also flags A, F#, Bm and most of Summer of '69. Research easy win 4.1 is discarded in that form; what replaces it is in improvement 1.

**(b) The vendored model cannot emit a power chord with any of its four dictionaries.** `~/.youkelele/models/chord_cnn_lstm/data/full_chord_list.txt` lists `C:5`, `C:(1,5)`, `C:1/1`, `C:5(b7)`, but `complex_chord.Chord("C:5").to_numpy()` gives triad id 73, above the network's `triad_limit*12+1 = 37`, so `XHMMDecoder.__init_known_chord_names` drops it (`if -2 in array: continue`). Running `chord_recognition.py ... full` on PSSOM (`run_full_dict.py`) returns exactly the shipped shares: C#:maj 0.295, N 0.277, B 0.193, E 0.124, A 0.089, F# 0.019, C#:min 0.002. Switching dictionaries is not a route to power chords.

**(c) Krumhansl on the harmonic stems alone is not a safe swap for the mix.** It fixes PSSOM (C# minor by 0.079 absolute instead of a 0.004 coin toss) and widens Chelsea's margin (0.067 instead of 0.006), but it flips Summer of '69 to A major (0.883 against D 0.807), which is wrong. Research easy win 4.8 is therefore adopted only as the tie-breaker inside a chord-based estimate (improvement 1), never as the primary key.

**(d) The chord stream plus a tonic rule gets all four songs right**, which the research inferred but did not test. `key_variants.py`: relative-major pairs scored by time-weighted diatonic share with half credit for a chord whose root is diatonic but whose quality is not (the model's power-chord bias is exactly a quality error on a diatonic root); pairs within 0.02 of the top broken by harmonic-stem Krumhansl; tonic within the pair by root time plus 0.1 each for opening and closing the song:

| Song | Pair chosen (share, margin) | Tonic evidence | Result | Shipped |
|---|---|---|---|---|
| Chelsea | G/Em 0.974 over D/Bm 0.929 (0.045) | G 0.582, E 0.090 | G major (chroma prefers D 0.845 over G 0.778: print the hedge) | D major |
| Summer of '69 | D/Bm 0.930 over A/F#m 0.877 (0.052) | D 0.602, B 0.079 | D major | D major, correct |
| PSSOM | E/C#m 0.781 over F#/D#m 0.697 (0.084) | C# 0.515, E 0.178 | **C# minor**; tonic root carries 41.1% of chord time as C#:maj and 0.3% as C#:min, so the tonic-quality rule fires | C# major, wrong mode |
| Wet Leg | C/Am = F/Dm 0.988, tie broken by chroma C 0.710 over F 0.604 | C 0.627, A 0.000 | C major | C major, correct |

Without the half credit PSSOM goes to F# major (0.696), as the lessons document warned; the half credit is what makes the chord-based key robust to the model's collapse of no-third chords onto `maj`.

**(e) Chelsea Dagger has no beat-level flicker.** The research counted 13 events under 1.2 s; at 157.9 bpm those are two-beat events (0.78 s = 2 x 0.388 s), all starting on beat 1 or beat 3 of bars 110 to 122, alternating C and D every half bar in the last chorus. That is harmonic rhythm, not fragmentation. Genuine one-beat fragments exist only in PSSOM (6: F# at bars 28 and 56 beat 1; E then A at bar 58 beats 1 and 2, giving the song's only three-name cell `C / F / G`; C#m at bar 65; E at bar 86) and Wet Leg (1: the C# at bar 63 beat 4, 0.48 s, already a v1.2 passing chord). Research easy win 4.3 survives in a much narrower form (improvement 7).

## 2. Finding-by-finding verdicts

| Research finding | Verdict | Why |
|---|---|---|
| 1 No `:5` class; power chords become `maj`; drags key mode | **Applies, but the proposed fix does not** | Confirmed in the model (b) and in PSSOM (C#:maj 30%). Chroma third test fails (a). Fix via key-from-chords with a tonic-quality rule (improvement 1). |
| 2 Key is a coin toss; tonic-triad weighting and chord stream beat Krumhansl | **Applies, tested, strengthened** | (d): the chord-based estimate is right on 4 of 4; the two shipped coin tosses become margins of 0.045 and 0.084. |
| 3 Recognise chords on the mix, not stems | **Applies, no change** | Supports the current design; the harmonic stems are used only for chroma witnesses. |
| 4 6s guitar and other stems weak; `htdemucs_ft` better per stem | **Discarded for now** | Strums stage reads `guitar.wav` and `other.wav` from 6s; chord recognition does not use stems; the sum of four harmonic stems is what fill and key need and it worked on 4 of 4. A four-stem model roughly doubles the 93 to 135 s separation on CPU and requires a strums redesign. Measure only if a strum-quality strand asks for it. |
| 5 Major/minor plus N is the dependable layer; sevenths and slash optional | **Applies, already how `easy` behaves** | 0 of 293 events on four songs carried a seventh, sus or inversion, so the tiers have never been exercised on real audio (background `full` runs confirm the model emits none on these songs, see section 6). |
| 6 Tools present simplification as a toggle; capo is the player's choice | **Applies in part** | Printing the no-capo alternative (improvement 2) is the file-based equivalent of a capo toggle. A `medium` tier is implementable with `shape_cost` (improvement 8) but has nothing to act on in the validation set. |
| 7 `snap.py` has no bar prior; 13 short events in Chelsea | **Mostly refuted by the run data** (e) | Only 7 one-beat fragments across four songs, one of which v1.2 already handles. A narrow one-beat rule is still cheap (improvement 7). |
| 8 `no_capo_alternative` never rendered; capo margins thin | **Applies, confirmed** | PSSOM writes 74 entries (C# 1114 barre, F# 3124, B 4322 barre, E 1402, A 2100, C#m 1444); `render/` has no reference. Chelsea's margin is 0.11, Summer of '69's 0.33, PSSOM's 0.47, Wet Leg's 0.50. |
| 9 Sharps-only transposition; mixed spellings | **Applies as a latent bug** | `transpose_label` uses `_SHARPS` (arrange.py:14, 25) and `_shape_key` too (html.py:38); no current run hits it because all four transpositions land on naturals (PSSOM capo 4: C#->A, F#->D, B->G, E->C, A->F). A song in Eb with capo 1 would print "D" shapes and a legend mixing `A#` with the model's `Bb`. |
| 10 Key changes common in 1960s to 1990s hits; chain detects none | **Deferred** | None of the five validation songs modulates (Fame does not either). No test case, so no measurable design; noted as a deeper option. |

## 3. Improvements, ordered by impact per effort

### 1. Key from the chord stream, with the harmonic-stem chroma as tie-breaker and a tonic-quality rule that fixes the power-chord mode

- **Touches:** `music/key.py` (new `key_from_chords(events, chroma_corr) -> Key`, keep `estimate_key` for the chroma scores), `stages/harmony.py:69-77 [wt]` (call after `fill_silent_bars`, reuse the harmonic mix already summed at line 70 instead of `self._chroma(wav)` on the mix), `schemas.py:99-102` (`Key` gains `runner_up: str | None = None`, `margin: float = 0.0`, `source: Literal["chords", "chroma"] = "chroma"`), `music/snap.py` or a new `music/quality.py` (the relabel), `schemas.ChordEvent` (`quality_from_key: bool = False`), `render/html.py:72` and `templates/sheet.html.j2:56` (hedge, improvement 4). Tests: `tests/test_key.py` (currently two chroma tests), `tests/test_stage_harmony.py`.
- **Evidence:** section 1 (d). Shipped: PSSOM C# major against published C# minor; Chelsea 0.006 confidence; the lessons' hand calculation now run on all four songs.
- **Design:**
  1. Over non-N events (filled events included), accumulate time per `(root_pc, triad_quality)` from `event.triad`.
  2. For each of the 12 relative-major pairs, share = sum over events of `d` when the root is diatonic and the quality matches the scale degree (I IV V major, ii iii vi minor, vii dim), `ROOT_ONLY_CREDIT * d` (0.5) when only the root is diatonic, divided by total chord time.
  3. Candidates = pairs within `PAIR_TIE = 0.02` of the best; break a tie by the larger Krumhansl correlation of either key of the pair on the **harmonic-stem** chroma (the `bar_chroma` matrix from `fill.py:54 [wt]` averaged over bars with energy above `FILL_MIN_ENERGY`, so silence and pre-roll do not vote).
  4. Tonic within the pair: root time share plus `0.1` if that root opens the song and `0.1` if it closes it (last non-N, non-passing event). Mode follows the tonic.
  5. `Key.confidence` = pair margin; `runner_up` = the other pair's key with the same mode family, or the chroma's best key when it disagrees with the chord key (Chelsea: chords G, chroma D).
  6. Tonic-quality rule: if the tonic root's chord time in the opposite quality exceeds its time in the key's quality **and** the harmonic chroma prefers the key's mode on that tonic (PSSOM: C# minor 0.716 against C# major 0.338), relabel those events' `triad` (and `label` when it equals the triad) to the key's quality and set `quality_from_key=True`. This fires only on the tonic, so borrowed chords elsewhere (Chelsea's C and Am in G, Summer of '69's F Bb C in D) are untouched; on the four songs it fires only on PSSOM's six C#:maj events (41.1% of chord time).
  7. Presentation: `easy` prints the relabelled name (C#m; Am at capo 4, the published chart); `full` prints `C#5` with a `Substitution` reason `"no-third chord: quality from key"`. Arrange already records substitutions (`stages/arrange.py:35`).
- **Capo check:** with C# minor the unique-label rule still picks capo 4 (1.80 against 2.60 for capo 2, 2.66 for capo 1, 3.02 for capo 0), so PSSOM's sheet changes only A to Am.
- **Measure:** Summer of '69 D major, Wet Leg C major unchanged; PSSOM C# minor with six relabelled events and the legend A D G C F Am becoming Am D G C F; Chelsea G major with runner-up D printed. Add these four as fixtures to `tests/test_key.py` from `chords.json` plus the dumped chroma means (`chroma_means.json` in this folder).
- **Effort:** medium. **Impact:** high (fixes the one wrong key on the set, removes two coin tosses, fixes the only wrong chord quality on the set). **Confidence:** 85%.

### 2. Render the no-capo alternative that arrange already writes, and record the capo margin

- **Touches:** `music/score_builder.py:91-168` (`Score` gains `alternative_diagrams: list[ChordDiagram] = []`, built from `arrangement.no_capo_alternative` with the same dedupe as `diagram_index`, line 107), `schemas.py:231-243` (`Score.alternative_diagrams`), `render/html.py:42-78` and `templates/sheet.html.j2:69-72` (one line under the legend), `stages/arrange.py:65` (`ctx.note("capo_margin", f"{second - best:.2f}")` from `score_capo`, and `ctx.note("capo_scores", ...)`), `music/arrange.py:47-49` (`choose_capo` returns the scores or a small `CapoChoice` so the stage can note the margin).
- **Evidence:** PSSOM `arrangement.json` carries 74 `no_capo_alternative` entries with the six distinct shapes C# 1114 (barre), F# 3124, B 4322 (barre), E 1402, A 2100, C#m 1444; `grep no_capo render/` finds nothing. Chelsea's capo 0 wins by 0.11 and the capo-2 chart (F C G A# Am Dm Gm A) would print a barre A# where the capo-0 chart prints a barre Bm and B. A reader with no capo has nothing today.
- **Design:** `Without a capo: C# 1114 (barre), F# 3124, B 4322 (barre), E 1402, A 2100, C#m 1444` in G C E A order, using the fret formatter that v1.2 Task 6 adds for the `Passing:` line, so the two lines share one function. Print it only when `capo > 0`. Mark barre shapes in the text because that is the whole reason the capo was chosen. Write the margin into `manifest.json` so a thin decision is visible without a rerun.
- **Measure:** PSSOM sheet shows the line; the other three do not; `tests/test_html.py` gains one test beside `test_html_capo_header_notes` (line 125).
- **Effort:** small. **Impact:** medium. **Confidence:** 90%.

### 3. One harmonic-chroma helper, computed once in harmony and shared by fill and key

- **Touches:** new `music/chroma.py` (`harmonic_chroma(stems: list[Path]) -> HarmonicChroma` with `.frames` (12 x T), `.times`, `.bar_means(bars)`, `.energy(bars)`, `.mean(mask)`), `stages/harmony.py:22-38 [wt]` (`harmonic_mix` moves there), `music/fill.py:54-78 [wt]` (`bar_chroma` and `bar_energy` become thin wrappers or are removed), `music/key.py:30-35` (`chroma_mean_for` on the mix is deleted; the harmony stage's `chroma` constructor argument at `stages/harmony.py:53 [wt]` is replaced by an injectable `harmonic_chroma`), `tests/test_stage_harmony.py` fakes.
- **Evidence:** the worktree harmony stage computes `chroma_cqt` twice per run (fill on the harmonic sum at `fill.py:62`, key on the full mix at `key.py:34`), and section 1 (c) shows the mix chroma is the worse witness for key. Research 4.8 and the v1.2 fill both want the same matrix; improvement 1 needs it as a tie-breaker.
- **Design:** compute `chroma_cqt(hop=512)` on the harmonic sum once; fill reads bar means; key reads the energy-masked mean. Keep `sections.py:beat_chroma` on the mix: segmentation benefits from vocals and is a different strand.
- **Measure:** harmony stage time (9.5 to 12.6 s today) does not rise; fill results identical on the four runs (`manifest.json` `filled` note unchanged).
- **Effort:** small. **Impact:** medium (it is the plumbing for improvement 1 and removes a duplicate CQT). **Confidence:** 90%.

### 4. Print a hedged key when the margin is small or the chroma disagrees

- **Touches:** `music/score_builder.py:159` (`key=f"{tonic} {mode}"` becomes a small `ScoreKey` or two fields `key` and `key_runner_up`), `render/html.py:72-73`, `templates/sheet.html.j2:56,64`.
- **Evidence:** the header printed "D major" for Chelsea at confidence 0.006 and "C# major" for PSSOM at 0.010 with no hint; `Key.confidence` exists in `chords.json` and is dropped by `build_score`.
- **Design:** `Key: G major (or D major)` when `Key.margin < KEY_HEDGE_MARGIN` (0.05, set from Chelsea 0.045 hedged and Summer of '69 0.052 not hedged, both acceptable either way) or when `Key.runner_up` is the chroma's dissenting key. With a capo, hedge the shape key the same way through `_shape_key` (html.py:31-39).
- **Measure:** Chelsea hedged, the other three not.
- **Effort:** small. **Impact:** medium. **Confidence:** 85% (depends on improvement 1 for the fields; the threshold is set on two data points).

### 5. Spell roots by key

- **Touches:** `music/arrange.py:14,20-26` (`transpose_label(label, semitones, prefer_flats: bool = False)`), `music/shapes.py:35-40,100-106` (`display_name_for(label, db, prefer_flats)` respells the root; chords-db lookup already accepts both through `ROOT_TO_DB_KEY`), `render/html.py:11,31-39` (`_shape_key` stops importing `_SHARPS` from `music.arrange` and spells from the key), `stages/arrange.py:41,44,53` (pass the flag derived from the key in `chords.key`, transposed by the capo).
- **Evidence:** `transpose_label` and `_shape_key` are sharps-only; the model itself wrote `Bb:maj` (Summer of '69) and `C#:maj` (Wet Leg, PSSOM), so the sheet already follows two conventions, and chords-db keys are flat-spelt (`A Ab B Bb C D Db E Eb F G Gb`). No current run prints a wrong spelling because every transposition landed on a natural.
- **Design:** `FLAT_KEYS = {F, Bb, Eb, Ab, Db, Gb} major and {D, G, C, F, Bb} minor`; the shape key (sounding key moved down by the capo) decides. A chromatic chord between two known neighbours spells by direction (ascending sharp, descending flat; Wet Leg's C# between C and Dm stays C#). Apply in the legend, cells, passing line and no-capo line through `display_name_for`.
- **Measure:** `tests/test_shapes.py::test_display_name_keeps_model_root_spelling` (line 74) is replaced by key-based cases; synthetic Eb-major clip at capo 1 prints D shapes and a sounding key of Eb, never D#.
- **Effort:** small. **Impact:** low to medium (latent on this set, certain on flat-key songs). **Confidence:** 75%, because no validation song exercises it yet.

### 6. Sheet hygiene for the capo and legend

- **Touches:** `templates/sheet.html.j2:52-67` (a bold `Capo 4` line under the artist when `capo > 0`), `music/score_builder.py:105-112` (legend order: shape-key I, IV, V, vi first when the song is diatonic, then first appearance), `render/grid.py:26-31` (`crowded` cells drop a one-beat fragment's name when improvement 7 did not merge it), `schemas.ChordDiagram` (`frets: str`, e.g. `"0232"`, written by `build_score` so legend, `Passing:` and `Without a capo:` share one formatter).
- **Evidence:** PSSOM's header shows the capo only in the facts row; the v1.1 validation called the capo "the first thing a player needs to set". PSSOM has one three-name cell (bar 58, `C / F / G`). Legend order today is first appearance (PSSOM: A D G C F Am), which puts the I chord of the shape key (A) first by luck and the V (E, printed C) fourth.
- **Design:** as listed. The legend rule uses the key from improvement 1; without it, keep first appearance.
- **Measure:** visual check on the four sheets plus the Fame run; no page-count change.
- **Effort:** small. **Impact:** low to medium. **Confidence:** 80%.

### 7. Absorb one-beat fragments off the strong beats, inside the bar only

- **Touches:** `music/snap.py:24-56` (a pass after run merging, before `fill_silent_bars` in `stages/harmony.py:69 [wt]`), `schemas.ChordEvent` (`merged_from: int = 0`), `tests/test_snap.py` (two tests today).
- **Evidence:** section 1 (e): 6 one-beat non-N events in PSSOM, 1 in Wet Leg, 0 in Chelsea and Summer of '69. PSSOM bar 58 (E one beat, A one beat, B two beats) is the only three-name cell on the set; Hooktheory and Ultimate Guitar write that chorus bar as E A on beats 1 and 3, so the A on beat 2 is a model slip.
- **Design:** an event of exactly one beat that starts on beat 2 or 4 (0-based `beat` 1 or 3) is absorbed into the longer neighbour **within the same bar**; a one-beat event on beat 1 or 3 is kept; nothing merges across a bar line, so Chelsea's two-beat C D alternation and PSSOM's E A half bars are untouched. `confidence` becomes the time-weighted mean. Do not add a seconds threshold (research 3.3); the beat grid is the right unit.
- **Measure:** PSSOM bar 58 becomes `C / F` (E A at capo 4) and bar 28's F# on beat 1 stays; Wet Leg bar 63's C# on beat 4 is absorbed (it is a passing chord either way); Chelsea and Summer of '69 unchanged (0 affected events).
- **Effort:** small. **Impact:** low (seven events on four songs). **Confidence:** 65%, because the bar 58 A on beat 2 might be a real anticipation and there are only seven cases to judge.

### 8. A `medium` tier that keeps a seventh or sus only when its shape is no harder

- **Touches:** `options.py:13` (`Literal["easy", "medium", "full"]`), `schemas.Arrangement.tier:189`, `music/arrange.py:96-112` (`simplify_for_tier`), `cli.py` choices, `tests/test_arrange.py:153-176`.
- **Evidence:** chords-db costs from `probe_db.py`: G7 `0212` 1.70 = G `0232` 1.70; C7 `0001` 0.40 = C `0003` 0.40; A7 `0100` 0.40 < A `2100` 1.30; E7 `1202` 1.70 < E `1402` 2.70; but D7 `2223` 3.60 (barre) > D 1.20, F7 `2313` 3.00 > F 1.30, B7 `2322` 3.60 < B 4.10. So "keep the seventh when `min shape_cost(seventh) <= min shape_cost(triad)`" is a one-line rule with the existing `_best_cost` (arrange.py:29-32). The validation set has no sevenths at all (0 of 293 events; the `full` dictionary adds none, section 6), so this changes nothing today.
- **Design:** `medium`: `to_triad` unless the label's own quality has a chords-db shape costing no more than the triad's best shape; reason `"medium tier: seventh kept, shape no harder"` or `"medium tier: reduced, seventh shape harder"`. Evaluate at capo 0 before `choose_capo` (as `simplify_for_tier` runs today), accepting the small inconsistency that the capo may change the comparison.
- **Measure:** the synthetic end-to-end clip and a blues upload; no change on the four runs.
- **Effort:** small. **Impact:** low until a song with sevenths is in the set. **Confidence:** 70%.

### 9. Slash chords: record why the bass was dropped, and show the slash only when the bass is outside the triad

- **Touches:** `music/shapes.py:79-85` (`_split_label` returns the bass as well), `music/arrange.py:96-112` (`simplify_for_tier` records `"bass dropped (not a chord tone)"` when the bass degree is outside the triad bitmap from `mir_eval.chord.quality_to_bitmap`), `display_name_for` (full tier only: `C/B`).
- **Evidence:** both tiers drop the bass silently (`shapes.py:83`); no run produced an inversion, and Deng and Kwok's 20% inversion WCSR says the model's `/3` and `/5` are not worth printing. The remaining value is the record in `substitutions` for whoever edits `chords.json`.
- **Effort:** small. **Impact:** low. **Confidence:** 80% that it is correct; it cannot be measured on the current set.

### 10. Ordinal shape difficulty instead of a weighted sum (deeper)

- **Touches:** `music/shapes.py:109-117` (`shape_cost`), consumers `music/arrange.py:32,43,72,80`, tests `tests/test_shapes.py:47-66`, `tests/test_arrange.py:56-116` (the published-chart capo tests must stay green).
- **Evidence:** E `1402` beats `4442` by 2.70 to 3.00, a 0.3 margin that a weight change flips; chords-db marks `4442` as no barre though players treat it as one. The five major and minor chords with no open, barre-free shape are exactly B, Bm, Bb, Bbm, Db (probe), and the capo search is in effect trying to remove them.
- **Design:** tier each shape `open` (base fret 1, no barre, at most three fingers, span at most two frets), `stretch` (span three or four or four fingers), `barre`, `high` (base fret above 3); score capo and voicings on `(tier, cost)` lexicographically. Keep the current weights as the within-tier cost.
- **Measure:** the seven capo cases in `tests/test_arrange.py:60-116` unchanged; E still `1402`; PSSOM still capo 4; Chelsea's margin over capo 2 reported.
- **Effort:** medium. **Impact:** low to medium. **Confidence:** 60%, because no ukulele difficulty data exists to calibrate against and the current rule is right on every validation song.

### 11. Local key and the last-chorus lift (deferred)

- **Touches would be:** `music/key.py` (per-section scoring over `grid.sections` using the chroma from improvement 3 and the chord stream from improvement 1), `stages/arrange.py` (capo per key segment, printing "same shapes, capo +1" for a one or two fret lift).
- **Why deferred:** none of the five validation songs modulates, so there is no way to set the self-transition penalty or test the lift rule. Add a modulating song to the validation set first. Until then the symptom is a compromise capo, not a wrong label.
- **Effort:** large. **Impact:** low on the current set. **Confidence:** not assessable.

## 4. Already in progress in version 1.2 (not proposed again)

Four-bar sections; mean-interval tempo; title cleaning; filling all-N bars from the harmonic stems (`music/fill.py`, `FILL_MIN_ENERGY 0.2`, `FILL_MIN_MATCH 0.32`, `FILL_MIN_MARGIN 0.05`); passing chords (`passing_labels`, `PASSING_SHARE 0.02`, `MIN_DIAGRAM_CHORDS 3`) with the `Passing: B 4322` fret line; phrase alignment; repeated row blocks; the narrow pickup cell. Improvements 2 and 6 above reuse the v1.2 fret formatter and the `filled` and `passing` flags rather than adding parallel ones.

## 5. Discarded, with reasons

- **Chroma third test for power chords** (research 4.1): measured to fail, section 1 (a). The riff's chroma has a stronger major third than real triads do.
- **Switching the model dictionary to `full` to get `:5`**: measured identical output, section 1 (b); the network's triad head has no no-third class.
- **Harmonic-stem Krumhansl as the primary key**: flips Summer of '69 to A major, section 1 (c). Used as tie-breaker only.
- **`htdemucs_ft` or a four-stem accompaniment**: doubles CPU separation time (already 76 to 84% of a run), the strums stage is built on the 6s guitar and other stems, and the summed harmonic stems already serve fill and key. Revisit only from the strums strand with a measurement.
- **BS Roformer SW guitar model**: no licence, as the project's research notes record; stays behind the unimplemented `--separator roformer-sw` flag (`preflight.py:91`).
- **Essentia key profiles, madmom key CNN**: AGPL and CC BY-NC licences; the profile idea is taken (tonic weighting in improvement 1), the libraries are not.
- **HarmTrace tie-breaking**: Haskell; the chain's equivalent is the key-aware tonic rule plus the v1.2 song-chord-set fill.
- **Replacing Chord-CNN-LSTM with BTC or ChordFormer**: neither has a `:5` class; no CPU-ready permissive weights found; four clean runs at the major/minor layer give no reason to change.
- **A seconds-based minimum chord duration** (0.5 s): the grid gives beats; a seconds rule would wrongly merge Chelsea's half-bar changes at 158 bpm.

## 6. Background check: does the model ever emit sevenths or inversions on these songs?

Run with the `full` dictionary (382 classes including sevenths, inversions, sus and extensions), `run_full_dict.py`:

- Pour Some Sugar On Me: C#:maj 0.295, N 0.277, B:maj 0.193, E:maj 0.124, A:maj 0.089, F#:maj 0.019, C#:min 0.002. No seventh, sus or inversion.
- Summer of '69: A:maj 0.381, D:maj 0.381, B:min 0.074, G:maj 0.050, N 0.047, C:maj 0.026, Bb:maj 0.024, F:maj 0.017.
- Chelsea Dagger: G:maj 0.344, D:maj 0.283, N 0.101, E:min 0.083, B:min 0.067, C:maj 0.048, A:maj 0.040, A:min 0.027, B:maj 0.007.
- Wet Leg: C:maj 0.501, F:maj 0.316, D:min 0.124, N 0.048, C#:maj 0.011.

With 382 classes available, the model still emits only major, minor and N on all four songs: no seventh, sus, inversion or extension anywhere, and the shares match the `submission` output to within 0.01.

This is why improvements 8 and 9 are low impact on this set: the `easy` and `full` tiers produce the same sheet for every validation song, and the decoder's transition penalties (`diff_trans_penalty 30`, `beat_trans_penalty (15, 45, 100)`) already favour the plain triad.

## 7. Suggested order of work

1. Improvement 3 (shared harmonic chroma), then 1 (key from chords with tonic-quality rule), then 4 (hedged header): one harmony-stage change set, measured on the four `chords.json` files plus `chroma_means.json`.
2. Improvement 2 (no-capo line and capo margin) alongside v1.2 Task 6, sharing the fret formatter.
3. Improvements 5 and 6 (spelling, header, legend order) as one render change set.
4. Improvement 7 (one-beat fragments) only with a listen to PSSOM bar 58.
5. Improvements 8, 9 and 10 when a song with sevenths or a hard-key song enters the validation set; 11 when a modulating song does.
