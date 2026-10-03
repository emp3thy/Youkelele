# Beat tracking, tempo octave, downbeats and the bar grid: applied report

Date: 2026-10-03. Apply agent for the strand "Beat tracking, tempo octave, downbeats and the bar grid". Input: `beats-research.md` (same folder). Code read: `src/youkelele/stages/grid.py`, `music/tempo.py`, `music/backbeat.py`, `music/snap.py`, `music/sections.py`, `music/onsets.py`, `music/score_builder.py`, `models/beats.py`, `models/chords.py`, `schemas.py`, `options.py`, `cli.py`, `render/html.py`, `render/grid.py`, `render/templates/sheet.html.j2`, the tests in `tests/test_tempo.py`, `tests/test_stage_grid.py`, `tests/test_backbeat.py`, `tests/audio_fixtures.py`, and the version 1.2 worktree diff (`mean_bpm`, `MIN_SECTION_BARS`). Line numbers refer to `main` unless marked (v1.2 worktree), where `stages/grid.py` is shifted by about three lines.

Everything marked **measured** below was computed in this session with scripts in `scratchpad/research/beats_apply/` (`analyse_json.py`, `measure_audio.py`, `measure_spike.py`, `chord_lag.py`, `meter_synth.py`); they read the run folders and the spike audio and wrote only to the scratchpad. Raw Beat This! output per run is saved as `beats_apply/raw_<slug>.json` and the chord model's raw spans as `beats_apply/<slug>.lab`.

---

## 0. Verdict on the research findings

| Research finding | Applies to this codebase? | Result |
|---|---|---|
| 20 ms lattice biases the median tempo | Yes, confirmed: Chelsea intervals are only 0.38 s (317) and 0.40 s (230), Summer of '69 only 0.42 (165) and 0.44 (301) | Already in progress (v1.2 `mean_bpm`). Regression adds nothing to the header: regression equals the mean within 0.02 bpm on all four songs. Keep only the residual as a diagnostic (improvement 7) |
| Octave errors are the dominant residual error | Yes: the two known failures (I'm Yours, Over the Rainbow) are both doubled ballads | Improvement 1 replaces the band gate; measured 7 of 7 |
| Multi-hypothesis tempo over fixed gates | Partly. Scoring half and double by backbeat ratio works only when the comparison is restricted: the doubled hypothesis scores 2 to 15 on every song because its odd positions fall on real beats | Improvement 1 uses a two-sided test (detected and halved), not a max over three hypotheses |
| Half-time feel trap (snare on 3) | Confirmed on I'm Yours: beat profile at the detected grid [0.76, 1.01, 1.81, 0.42] | Covered by improvement 1 |
| Beat Critic quaver alternation | Carries the same information as the backbeat ratio here (negative at the halved grid on all five correct songs, positive on both doubled ones). Not an independent cue | Optional second vote in improvement 1; not required |
| Regularise beats (local 0.5x and 2x runs) before the global decision | Prototype finds Over the Rainbow's two 2x stretches (59.7 to 89.3 s and 178.5 to 209.4 s) and is a no-op on the other six songs. No song in the set needs it while the global decision is "none" | Improvement 5, latent value |
| Downbeat F1 85 percent, weak openings | Partly. On these songs the downbeats are strong (modal share 0.87 to 1.00). The weakness is extra mid-bar downbeats (19 percent of PSSOM spacings are 2 beats) and the one-beat Summer of '69 pickup | Improvement 4 (pickup), note in improvement 6 (meter) |
| No meter detection | Confirmed: `options.meter` default "4/4", `Meter.parse` only. Downstream is already meter-aware (`backbeat_ratio`, `choose_slots_per_bar`, `score_builder` check) | Improvement 6 as a logged suggestion, not an automatic switch: Beat This! changed metrical level on two of four synthetic meter clips |
| Chord boundaries lag by 0.1 to 0.4 s, fixed lag shift | **Refuted on real songs.** Boundaries are early: median signed offset to the nearest beat is -44, -27, -39, -31 ms; none beyond half a beat. The 0.1 to 0.4 s lag was measured on the synthetic sine clip (no attack transients) | Discard the lag shift. Position-dependent re-snap kept as a small optional item (improvement 8) because only about five events in four songs qualify |
| Bar-phase confidence from chord positions | Phase is right on 4 of 4; a shift would put 0 changes on beat 0 in three songs and 25 in PSSOM (real half-bar changes) | Fold into the cue record of improvement 2; no separate work |
| Tempo drift is a non-issue, annotate instead | Confirmed on the four runs (section tempo range 0.2 to 1.6 percent). Riptide ranges 98.5 to 107 bpm per 32 beats (8 percent), so "about" is justified there | Improvement 7 |
| Licence and CPU constraints | madmom, BeatNet, allin1, Essentia, BeatFM all fail the CPU-Windows-3.12-permissive test | Discarded, see section 3 |

---

## 1. Measurements made in this session

### 1.1 Tempo estimators on the four runs (from `02_grid/grid.json`)

| Song | stored (median) | mean | least-squares regression | residual std | max residual | section tempo range |
|---|---|---|---|---|---|---|
| Chelsea Dagger (`sexhetcxqy4`) | 157.89 | 154.68 | 154.55 | 33.4 ms | 162 ms | 153.8 to 156.3 (1.6 percent; intro faster) |
| Summer of '69 (`9f06qzcvuhg`) | 136.36 | 138.56 | 138.57 | 16.4 ms | 46 ms | 138.3 to 138.9 |
| Pour Some Sugar On Me (`0uib9y4ofps`) | 85.71 | 84.94 | 84.95 | 11.1 ms | 73 ms | 84.8 to 85.0 |
| Wet Leg "mangetout" (`lbc6ccztp5e`) | 130.43 | 128.02 | 128.00 | 11.5 ms | 55 ms | 127.5 to 128.5 |

Interval values are a 20 ms lattice plus the `fill_gaps` midpoints (Summer of '69 two 0.43 s intervals, Wet Leg eight 0.465 s intervals). The 1-beat Summer of '69 pickup (0.02 to 0.44 s) and the final 1- or 2-beat bars in every song are the only irregular bars; `max/median` bar length is 1.01 to 1.02 everywhere.

### 1.2 Octave cues on seven songs with drum stems (Beat This! re-run or spike `beats.json`; `backbeat_ratio` from `music/backbeat.py`)

"Modal" is the ratio at the modal downbeat phase (what `grid.py:71` computes today). "Half best" is the maximum over the four phases on the `normalise_octave` output; "double best" the same on `double_beats` output. Quaver alternation is the Beat Critic measure on an 8-slot bar of the drum stem's high-band flux (on-slot minus off-slot energy, normalised), at the modal phase.

| Song | detected bpm | truth | ratio modal (detected) | half best | double best | quaver alt at detected / half | current rule | two-sided rule (improvement 1) |
|---|---|---|---|---|---|---|---|---|
| Chelsea Dagger | 157.9 | keep | 2.06 | 1.03 | 4.28 | +0.62 / -0.35 | keep | keep |
| Summer of '69 | 136.4 | keep | 2.14 | 1.22 | 4.93 | +0.66 / -0.36 | keep | keep |
| Pour Some Sugar | 85.7 | keep | 2.14 | 1.57 | 2.19 | +0.37 / -0.37 | keep | keep |
| Wet Leg | 130.4 | keep | 1.94 | 1.03 | 2.11 | +0.36 / -0.32 | keep | keep |
| Riptide (spike) | 103.4 | keep | 1.12 | 1.15 | 1.15 | -0.07 / -0.03 | keep | keep |
| I'm Yours (spike) | 150.0 | halve | 0.56 | 2.39 | 14.89 | +0.87 / +0.27 | halve | halve |
| Over the Rainbow (spike) | 166.7 | halve | 0.14 (stem RMS below `DRUMS_SILENT_RMS`, so today it reads "silent") | 2.71 | 8.24 | +0.78 / +0.89 | halve (band, no evidence) | halve (with evidence) |

Three facts follow. (a) The current ratio at the modal phase is the discriminating cue: 1.94 to 2.14 on rock, 1.12 on the soft Riptide, 0.56 and 0.14 on the doubled songs. (b) The halved grid gives a second, independent reading: 1.03 to 1.57 on correct songs against 2.39 and 2.71 on doubled ones. (c) The doubled hypothesis is never comparable: its ratio is 2 to 15 on every song, so any "pick the maximum" rule picks double. Onset autocorrelation (the tempogram cue) is stronger at the half lag than at the beat lag on three of the four correct songs (Chelsea 0.407 vs 0.245, Summer of '69 0.435 vs 0.430, PSSOM 0.554 vs 0.487), confirming the spike: it cannot flag ambiguity.

### 1.3 Chord boundary offset against the beat grid (chord model re-run on the four run audios, `chord_lag.py`)

| Song | chord-to-chord boundaries | median signed offset to nearest beat | p25 / p75 | share late (after the beat) | share beyond half a beat | position inside the beat, median |
|---|---|---|---|---|---|---|
| Chelsea Dagger | 66 | -44 ms | -64 / -30 | 0.08 | 0.00 | 0.87 of a beat (just before the next beat) |
| Summer of '69 | 73 | -27 ms | -47 / -5 | 0.11 | 0.00 | 0.90 |
| Pour Some Sugar | 67 | -39 ms | -72 / +11 | 0.28 | 0.00 | 0.89 |
| Wet Leg | 65 | -31 ms | -34 / -9 | 0.17 | 0.02 | 0.93 |

The chord model is early by about one frame, not late. `snap_to_beats`' per-beat overlap vote (`snap.py:24-56`) therefore already puts the change on the right beat; the changes recorded on beats 1 and 3 in `chords.json` (Summer of '69: 3; PSSOM: 7 on beat 1 and 2 on beat 3; Wet Leg: 2 and 2; Chelsea: 0) are whole-beat label decisions by the model, not sub-beat lag. Of those 16, 6 are `N` starts (drop-outs), 3 are PSSOM's `B:maj` at bars 28, 56 and 86 (each 3.1 beats long, confidence 0.84 to 0.89, which the published chart writes as a full bar), and the rest are one-off.

### 1.4 Downbeat structure (raw Beat This! output)

| Song | raw downbeats | within 70 ms of a beat | beats between consecutive downbeats | modal phase share after `fill_gaps` |
|---|---|---|---|---|
| Chelsea Dagger | 142 | 142 (offset 0 ms) | {4: 141} | 1.00 |
| Summer of '69 | 121 | 121 | {1: 1, 3: 1, 4: 118} | 0.99 (counts [1, 120, 0, 0]) |
| Pour Some Sugar | 119 | 119 | {1: 6, 2: 22, 3: 2, 4: 88} | 0.87 (counts [103, 1, 12, 3]) |
| Wet Leg | 112 | 112 | {1: 1, 3: 1, 4: 109} | 1.00 |
| I'm Yours | 153 | 153 | {1: 1, 4: 151} | 0.99 |
| Over the Rainbow | 135 | 135 | {2: 18, 3: 1, 4: 115} | 0.52 |
| Riptide | 84 | 84 | {2: 1, 3: 1, 4: 80, 5: 1} | 0.81 after 4 inserted beats |

Downbeats are always exactly on a beat because the minimal post-processor snaps them (`beat_this/model/postprocessor.py`, verified in the installed package: `fps=50`, downbeats moved to the nearest beat). Mid-bar extra downbeats are the common defect (PSSOM 22, Over the Rainbow 18), not missing ones.

### 1.5 Synthetic meter clips through Beat This! (`meter_synth.py`: chord loop plus noise-burst drums with an accent on beat 1, 48 s)

| Clip | beats found / expected | median bpm | downbeat spacing |
|---|---|---|---|
| 4/4 at 120 | 96 / 96 | 120.0 | {4: 23, 3: 1} |
| 3/4 at 96 | 77 / 76 | 96.8 | {3: 25} |
| 3/4 at 120 | 65 / 96 | 81.1 | {2: 32} (tracked two dotted-crotchet "beats" per bar; downbeats right, beat level wrong) |
| 6/4 at 150 | 61 / 120 | 75.0 | {3: 20} (tracked at half tempo, three per bar) |

So the downbeats are reliable on these clips but the beat level moves with tempo, which is why meter detection from spacing alone must stay a suggestion (improvement 6).

### 1.6 Pickup energy (Summer of '69 bar 0, beat 0.02 to 0.44 s)

Mix RMS 0.144 against the song's 10th percentile per-beat RMS 0.183; drum stem RMS 0.121 against its 10th percentile 0.0066. The chord model labels 0.02 to 0.88 s as `N` and starts `D:maj` at 0.88 s (bar 1, beat 1). An energy test is ambiguous on the only example (mix says drop, drums say keep); the chord test says drop.

### 1.7 Regularise-beats prototype (`measure_spike.py: regularise_beats`, dominant interval from the middle 80 percent of intervals, runs of at least 8 intervals within 10 percent of 0.5x or 2.0x)

Over the Rainbow: dominant 0.360 s; repairs at 59.7 to 89.3 s (42 intervals, 2.0x) and 178.5 to 209.4 s (44 intervals, 2.0x); bars before 126 with max/median 2.01, after 147 with max/median 1.01 (before the global half decision). No-op on the four runs, I'm Yours and Riptide.

---

## 2. Improvements, ordered by impact per effort

### 1. Replace the octave band gate with a two-sided backbeat test and record the cues

**Files and functions.** `music/tempo.py: decide_octave` (lines 53 to 71); `stages/grid.py` lines 69 to 79 (ratio, decision, `normalise_octave`); `music/backbeat.py: backbeat_ratio` (28 to 71) unchanged; `schemas.py: Grid` (58 to 72) gains `octave_cues: dict[str, float | None] = {}`; `tests/test_tempo.py` lines 37 to 47 and 143 to 170 (decide_octave tests); `tests/test_stage_grid.py` (`_fake_detector`, `write_drum_stem` at `tests/audio_fixtures.py:90`).

**Evidence.** Section 1.2. Today's rule (`bpm > 140 and 60 <= bpm/2 <= 95`, then `ratio < 1.0 or silent`) is right on 7 of 7, but the band is a genre prior: a doubled ballad detected at 130 (true 65) or at 200 (true 100) is never halved, and the lessons document records the first Chelsea run halving 157.9 to 76.9 before the backbeat test existed. The halved-grid ratio gives a second reading that is independent of the band: 1.03 to 1.57 on correct songs, 2.39 and 2.71 on the doubled ones, including Over the Rainbow whose stem fails the silence test.

**Design.**
```python
HALF_BAND = (50.0, 110.0)      # halved tempo must land here (was 60 to 95 with bpm > 140)
DETECTED_MAX_RATIO = 1.0       # snare not on 2 and 4 at the detected grid (unchanged)
HALF_MIN_RATIO = 1.5           # snare on 2 and 4 at the halved grid
AMBIGUOUS_MARGIN = 0.25        # |ratio - threshold| below this sets tempo_ambiguous

@dataclass
class OctaveCues:
    bpm: float
    ratio_detected: float | None   # modal phase, as today
    ratio_half: float | None       # max over phases on normalise_octave output
    drums_silent: bool

def decide_octave(cues: OctaveCues, mode: OctaveMode) -> tuple[OctaveDecision, bool]:
    if mode != "auto": return mode, False
    half_bpm = cues.bpm / 2
    if not HALF_BAND[0] <= half_bpm <= HALF_BAND[1]: return "none", False
    if cues.ratio_detected is None and cues.ratio_half is None:   # no drum evidence at all
        return ("half" if cues.bpm > 140 and 60 <= half_bpm <= 95 else "none"), False   # old prior
    detected_says_halve = cues.ratio_detected is None or cues.ratio_detected < DETECTED_MAX_RATIO
    half_says_halve = cues.ratio_half is None or cues.ratio_half >= HALF_MIN_RATIO
    ambiguous = (cues.ratio_detected is not None and abs(cues.ratio_detected - DETECTED_MAX_RATIO) < AMBIGUOUS_MARGIN) \
             or (cues.ratio_half is not None and abs(cues.ratio_half - HALF_MIN_RATIO) < AMBIGUOUS_MARGIN)
    return ("half" if detected_says_halve and half_says_halve else "none"), ambiguous
```
In `grid.py`, compute `ratio_half` by running `normalise_octave` speculatively and taking `max(backbeat_ratio(drums, sr, half_beats[p:], n) for p in range(n))`; compute the flux cues even when `drums_silent` is true (Over the Rainbow shows the ratio is informative at RMS below 0.003), but keep `drums_silent` in the record. Store `octave_cues` (bpm, both ratios, silent flag, decision, ambiguous) in `grid.json` and log them on one line. Keep `--beat-octave` as the override. Do not score "double": no example exists and the doubled ratios are uninformative (section 1.2 c).

**Measurement.** The seven-song table must read keep x5, halve x2 (it does with the constants above: Riptide fails the band at 51.7 and its detected ratio 1.12 is above 1.0; PSSOM's half ratio 1.57 passes `HALF_MIN_RATIO` but its detected ratio 2.14 blocks). Unit tests: detector at 150 bpm with `write_drum_stem(bpm=75, hit_beats=(1, 3))` must halve; the same stem at `(1, 3)` of a 150 bpm bar must keep; a 130 bpm detector with a 65 bpm backbeat stem must now halve (new case outside the old band). Record the margin: PSSOM's 1.57 is the nearest correct song to the threshold, so the next validation song with half-bar riff chords should be checked first.

**Effort** small. **Impact** high. **Confidence** 75: only two doubled examples exist, both ballads with a clear snare at the halved grid; a doubled song with brushes or no snare would still fall back to the band prior.

### 2. Persist raw detector output and decision cues in the stage folders

**Files.** `stages/grid.py: GridStage.run` (48 to 115): write `grid/beats_raw.json` (`detected.beats`, `detected.downbeats`, `fill_gaps` insertions, `normalise_octave` drops) next to `grid.json`; `produces` tuple at line 43. `stages/harmony.py: HarmonyStage.run` (34 to 50): copy `work_dir/out.lab` to `harmony/spans.lab` before `shutil.rmtree`. `schemas.Grid` gains `octave_cues` (improvement 1) and `downbeat_spacing: dict[str, int]` (section 1.4) and `downbeat_modal_share: float`.

**Evidence.** `grid.json` holds only gap-filled beats and bar-derived `downbeats` (line 102: `[bar.beats[0] for bar in bars]`), so the modal share, the spacing histogram and the raw first downbeats are lost; every measurement in section 1 required re-running Beat This! (2.6 to 5.2 s per song) and the chord model (7.5 to 8.8 s). The thresholds in improvements 1, 4 and 6 can only be re-fitted from saved cues as new songs are run.

**Design.** Pure bookkeeping; no decision changes. `beats_raw.json` is a plain dict (no pydantic model needed); `spans.lab` is the model's own format, parsed by the existing `parse_lab`. Add the two files to `produces` so the runner tracks them.

**Effort** small. **Impact** medium (it makes every later threshold change measurable without model reruns). **Confidence** 90.

### 3. Tempo alternative in the header and an ambiguity flag

**Files.** `schemas.Grid` (+ `tempo_alternative: float | None = None`, `tempo_ambiguous: bool = False`); `schemas.Score` (230 to 242, + `bpm_alternative: float | None = None`); `music/score_builder.py` lines 160 to 163 (copy from grid); `render/html.py:74` (`tempo=round(score.bpm)`) and `render/templates/sheet.html.j2:58` (`<span><b>Tempo</b> {{ tempo }} bpm</span>`); `stages/grid.py` log line 91 to 94 (add the `--beat-octave` hint).

**Evidence.** The lessons and validation documents could only judge the octave by comparing three estimates; a player with the sheet has no hint when the chart counts at the other level. Section 1.2 shows the margin is small on PSSOM (half ratio 1.57) and Riptide (detected 1.12), so an honest flag will fire occasionally on correct songs.

**Design.** `tempo_alternative = bpm / 2` when the decision was "none" and the halved tempo is inside 60 to 110, or `bpm * 2` when the decision was "half". Set `tempo_ambiguous` from improvement 1's margin. The header prints "139 bpm" normally and "158 bpm (or 79 counted in half time)" only when `tempo_ambiguous`; the CLI log always prints the alternative with "use --beat-octave half|none to switch". Do not use the tempogram ratio (section 1.2, last paragraph).

**Measurement.** On the four runs the header must not change (none is ambiguous under the constants above: nearest margins are PSSOM 1.57 vs 1.5 at 0.07, which is inside 0.25, so PSSOM would print the alternative; if that is unwanted, define the margin on the detected ratio only, where PSSOM sits at 2.14). State the choice in the constant's comment.

**Effort** small. **Impact** medium. **Confidence** 70: the flag's usefulness depends on how often it fires on correct songs; the constants need the next two or three validation songs.

### 4. Pickup hygiene: drop a leading partial bar that carries no chord, and ignore opening downbeats in the phase vote

**Files.** `music/tempo.py: build_bars` lines 201 to 203 (`phase`, `starts = ([0] if phase > 0 else []) + ...`) and 217 (`pickup=number == 0 and phase > 0`); `music/tempo.py: modal_phase` (93 to 99) or `_choose_phase` (159 to 177) for the vote filter; `music/score_builder.py` around line 164 (`ScoreBar(..., pickup=grid.bars[bar_idx].pickup)`) for the chord-based drop; `render/grid.py: grid_rows` lines 34 to 52 (pickup row; v1.2 replaces it with a narrow cell).

**Evidence.** Summer of '69's bar 0 is one beat at 0.02 to 0.44 s, labelled `N` (chords start at 0.88 s); the chart has no pickup there. Downbeats at 0.02 and 0.44 s are one beat apart (section 1.4), the detector's known opening weakness. The energy test proposed by the research is ambiguous on this example (section 1.6), so the chord test is the usable one.

**Design.** (a) In `build_bars`, exclude downbeat indices below 2 from the modal vote when more than 8 downbeats exist (no effect on the seven songs: Summer of '69 counts are [1, 120, 0, 0]). (b) In `score_builder.build_score`, when `grid.bars[0].pickup` and every event in bar 0 is `N`, omit bar 0 from the score and shift `start_bar`/`end_bar` of the sections by one (sections are bar-indexed; `Grid` validation requires `sections[0].start_bar == 0`, so do the shift on the `ScoreSection` side, not in `grid.json`). (c) Keep the pickup when it has a chord (a real anacrusis). Log "dropped a 1-beat N.C. pickup at 0.02 s".

**Measurement.** Summer of '69 loses the "pickup N.C." cell; the other three runs have no pickup and are unchanged; the existing `test_build_bars_marks_leading_partial_bar_as_pickup` still passes because the grid keeps the bar.

**Effort** small. **Impact** low to medium (v1.2's narrow cell already shrinks the harm). **Confidence** 65: one example.

### 5. General metrical-level regularisation before the global octave decision

**Files.** `music/tempo.py`: new `regularise_beats(beats, downbeat_idx) -> tuple[list[float], list[int], list[Repair]]` placed between `fill_gaps` (23 to 43) and `bpm_from_beats`; `stages/grid.py:61` (`beats = fill_gaps(beats)` becomes `fill_gaps` then `regularise_beats`); `normalise_octave` (102 to 132) unchanged; `Grid.repairs: list[Repair]` in `schemas.py` for the audit trail; test in `tests/test_tempo.py` beside `test_normalise_octave_repairs_half_doubled_list` (line 56).

**Evidence.** Section 1.7: the prototype repairs Over the Rainbow's two 2x stretches (bars max/median 2.01 to 1.01) and is a no-op on the six other songs. Today the repair happens only inside `normalise_octave`, that is only when the global decision is "half"; a song whose global level is right but which the detector doubles or halves for a stretch would keep 2x or 0.5x bars. No song in the set shows that case, which is why this is latent.

**Design.** Dominant interval = median of intervals between the 10th and 90th percentiles. Classify each interval as 0.5x (within 5 percent of half the dominant), 2.0x (within 20 percent of double) or normal. Runs of at least 8 consecutive 0.5x intervals: drop every other beat, starting on the beat whose index parity matches the run's downbeats (reuse the parity logic of `normalise_octave` lines 123 to 126). Runs of at least 8 consecutive 2.0x intervals: insert midpoints (as `double_beats` does per pair). Shorter runs are left alone (they are `fill_gaps` territory). Return the repairs with start, end, ratio and count, and log them. Then `bpm_from_beats` and the octave decision run on the regularised list as now.

**Measurement.** Over the Rainbow's beat list (spike `beats.json`) must come out with one bar length throughout even with `--beat-octave none`; the four runs, I'm Yours and Riptide must be byte-identical before and after. Synthetic test: a 150 bpm click list whose middle 40 beats are at 75 bpm.

**Effort** small to medium. **Impact** medium (latent; fixes a class of failure the spike observed only on Over the Rainbow). **Confidence** 55: no positive example where the global decision is "none".

### 6. Meter suggestion from downbeat spacing (`--meter auto` logs, does not switch)

**Files.** `stages/grid.py` after `db_idx = downbeat_indices(...)` (line 69): spacing histogram; `options.py:16` (`meter: str = "4/4"`, allow `"auto"`); `cli.py:46` help text; `schemas.Grid` (+ `meter_shares: dict[str, float]`, `meter_suggested: str | None`); `Meter.parse` (`schemas.py:23-28`) must map "auto" to 4/4 for now. No downstream change: `backbeat_ratio` takes `numerator` (`backbeat.py:56-57`), `choose_slots_per_bar` uses `meter.numerator * 2` (`onsets.py:92`), `score_builder` checks `(2 * num, 4 * num)` (lines 41 to 45), and the renderer rows are bar-based.

**Evidence.** Sections 1.4 and 1.5. Share of 4-beat spacings is 0.75 to 1.00 on the seven real songs; the synthetic 3/4 at 96 bpm gives {3: 25} cleanly, but 3/4 at 120 is tracked at 81 bpm with 2 "beats" per bar, so an automatic switch to 2/4 or 3/4 from spacing alone would be wrong in that case. Two-beat spacings are 13 to 19 percent on PSSOM and Over the Rainbow (mid-bar downbeats), so "2" must never trigger.

**Design.** `meter_shares = {k: count/total}` over spacings; if `shares["3"] >= 0.6 and shares["4"] < 0.2`, set `meter_suggested = "3/4"` and log "3 beats per downbeat in 6x percent of bars; run with --meter 3/4 if the song is a waltz"; otherwise `None`. Also, when `shares["2"] >= 0.5` and the tempo is under 100, log "downbeats every 2 beats at N bpm: possible 3/4 tracked at the dotted-crotchet level or 2/4" (the synthetic 3/4 at 120 case). Promote to an automatic switch only after one real 3/4 and one 6/8 song are in the validation set.

**Effort** small. **Impact** low to medium (latent; every validation song is 4/4). **Confidence** 50 that spacing alone suggests the right meter on real waltzes.

### 7. Tempo diagnostics: regression residual and section tempo range, with "about" in the header

**Files.** `music/tempo.py`: new `tempo_fit(beats) -> tuple[float, float]` (bpm by least squares, residual std in ms) next to `mean_bpm` (v1.2 worktree line 53); `stages/grid.py` after `bpm = mean_bpm(beats)` (v1.2 line 83); `schemas.Grid` (+ `tempo_jitter_ms: float`, `tempo_range: tuple[float, float] | None`); `render/html.py:74` prints "about N bpm" when the range exceeds 3 percent.

**Evidence.** Section 1.1: regression and mean agree within 0.02 bpm on all four songs, so the header is already handled by v1.2; the residual separates Chelsea (33 ms, max 162 ms, intro 156.3 vs body 154.5) from the others (11 to 16 ms), and Riptide's per-32-beat tempo spans 98.5 to 107 (8 percent) where one number misleads.

**Design.** Per-section tempo by regression over the section's beats (needs at least 8); `tempo_range = (min, max)`; header "about 103 bpm" when `(max - min) / mean > 0.03`, and the exact value otherwise. Do not add `Bar.free_time`: no song in the set has a rubato stretch (Over the Rainbow's irregular bars are detector octave switches, handled by improvement 5), so there is nothing to measure it on.

**Effort** small. **Impact** low. **Confidence** 60 that players notice the difference; the diagnostics themselves are certain.

### 8. Optional: position-dependent re-snap of chord starts on beats 1 and 3 (no lag shift)

**Files.** `music/snap.py: snap_to_beats` (24 to 56), after the runs are built; `schemas.ChordEvent` (+ `snapped_from: int | None = None`).

**Evidence.** Section 1.3 refutes the lag shift. The remaining candidates are few: PSSOM `B:maj` at bars 28, 56 and 86 (3.1 beats each, where the chart has a full bar), Wet Leg `C:maj` at bar 18 beat 1 (7.1 beats), Summer of '69 `D:maj` at bar 113 beat 1. About 5 of roughly 290 changes (under 2 percent).

**Design.** For a run that starts on beat 1 or 3 and lasts at least 3 beats, if the previous run's share on the preceding even beat is under 0.75 (`_beat_label` returns the share, `snap.py:21`), move the start back one beat and set `snapped_from`. Never move `N` starts, never move runs shorter than 3 beats (PSSOM's real two-beat riff chords).

**Measurement.** PSSOM's three `B:maj` events move to beat 0 and keep their 25 beat-2 changes; the other songs change by at most one event. Needs the raw spans from improvement 2 to check the shares.

**Effort** small. **Impact** low. **Confidence** 50: the share condition is untested; it may not fire if the model is confident about the wrong label on that beat.

### 9. Deeper option, measure first: Beat This! checkpoint ensemble on logits

**Files.** `models/beats.py: detect_beats` (19 to 29): use `beat_this.inference.Audio2Frames` for `final0`, `final1`, `final2`, average logits, then `Postprocessor("minimal")`; `CHECKPOINT` constant (line 10) becomes a tuple; `GridStage` note at `grid.py:115`.

**Evidence.** The detector takes 2.6 to 5.2 s per song here, so three passes stay under 20 s. Beat This! issue #13 reports Accuracy1 89.3 to 90.9 percent with an ensemble on EDM. The defect it could reduce here is the mid-bar extra downbeats (PSSOM 22, Over the Rainbow 18), which averaged logits tend to suppress; not measured locally because `final1` and `final2` are not cached.

**Effort** medium (checkpoint download, logits API, tests with a fake). **Impact** low to medium. **Confidence** 35.

---

## 3. Discarded, with reasons

- **Fixed chord lag compensation (`CHORD_LAG_S`).** Refuted: boundaries are 27 to 44 ms early on all four real songs (section 1.3). Shifting spans earlier would move changes onto the previous beat.
- **Tempogram or onset-autocorrelation ambiguity flag.** The half-tempo lag is stronger than the beat lag on three of four correct songs (section 1.2) and the spike's A1 table showed the same; it would flag nearly every song.
- **Harmonic-rhythm vote (median chord duration between 0.5 and 2 bars).** PSSOM's median chord lasts 0.51 bars at the correct level (riff chords change every two beats), so the rule would vote to double it. Not safe without the published chart.
- **Maximum backbeat ratio over {half, detected, double}.** The doubled hypothesis scores 2 to 15 on every song (section 1.2 c).
- **Regression instead of mean for the header.** Identical within 0.02 bpm on all four songs; mean is already in v1.2.
- **madmom DBN (`dbn=True`).** PyPI release needs Python below 3.10; the spike could not import it; model files are CC BY-NC-SA. The coherence benefit is obtained more cheaply by improvement 5.
- **BeatNet.** Depends on madmom and PyAudio.
- **allin1.** NATTEN must be built from source on Windows.
- **Essentia.** AGPL and no Windows wheels; **BeatFM** has no public code; **masked diffusion beat tracking** has no code seen.
- **Automatic 2/4 or 6/8 detection.** 13 to 19 percent two-beat spacings on correct 4/4 songs; the synthetic 3/4 at 120 was tracked at the dotted-crotchet level.
- **`Bar.free_time`.** No rubato example in seven songs; the only irregular stretches are detector octave switches.

## 4. Already in progress (version 1.2), not proposed again

Header tempo from the mean interval (`mean_bpm`); four-bar minimum sections; pickup drawn as a narrow leading cell; filling no-chord bars; passing chords; phrase alignment; repeated row blocks; title cleaning.

## 5. Measurement plan before changing constants

1. Run improvement 2 first so `beats_raw.json`, `spans.lab` and `octave_cues` exist for every later song.
2. Re-check the seven-song table (section 1.2) with the final `decide_octave`; add the next validation song (Bowie "Fame", 261 s) before merging.
3. Keep `scratchpad/research/beats_apply/measure_audio.py` and `measure_spike.py` as the reference scripts for the cue table; they take under a minute for all seven songs on CPU.
4. For improvement 6, find one real waltz and one 6/8 recording and record their spacing histograms before promoting the suggestion to a switch.
