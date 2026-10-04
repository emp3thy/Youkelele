# Ukulele Tab Chain, Version 1.3: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the strum box trustworthy (a vote that keeps the strikes it hears, recovery of strums in loud sustained sections, a worked example tying the pattern to the chords), put chord changes on the bar lines, drop trailing non-music bars, and add the measurement harness that scores every change before and after.

**Architecture:** Eight tasks on the existing stage chain. The harness comes first (`evaluate` works with no truth and compares two runs) so every later task ships with a table. Strum changes live in `music/as_played.py` and a new `music/recall.py`, wired by `stages/strums.py`; the chord decoder gains a driver script of our own in `models/chord_driver.py`; trailing bars are decided by one function in `music/trailing.py` used by the strums and score stages; the worked example is a new SVG in `render/strum_box.py`. All schema fields default; schema version stays 1.

**Tech Stack:** Python 3.12, pydantic 2, numpy, librosa (onset strength and peak picking), mir_eval (chord segmentation measures), Jinja2 + inline SVG, Playwright PDF; vendored Chord-CNN-LSTM in a child process. uv at `C:\Users\gethi\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`.

**Spec:** `docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-3-design.md` (sections 4.1 to 4.5 stage changes, 5 sheet, 6 data, 7 validation, 8 spikes). Spike artefacts: session scratchpad `spike_beats/` and `spike_recall/` (throwaway; the plan carries what they found).

## Global Constraints

- Schema version stays 1; version 1.2 files load: every new field defaults (`SectionPattern.explained: float = 0.0`, `SectionPattern.recall_boost: bool = False`, `ScoreSection.explained: float = 0.0`, `Score.trailing_bars_dropped: int = 0`, `RunOptions.debug: bool = False`).
- Constants, with the spec's values: `STRIKE_SHARE = 1/3` (strictly greater), `DENSITY_FLOOR = 0.6`, `EXPLAINED_BELOW = 0.6`, `UNCERTAIN_BELOW = 0.45` (unchanged), `HIGH_BAND_FMIN = 3000`, `SPARSE_SHARE = 0.4`, `MERGE_MS = 60`, `MIN_GAIN = 1.0`, `FIT_TOLERANCE = 0.05`; `SILENT_BAR_SHARE` and `EXPLAINED_KEEP` are measured in Task 4 with the acceptance criterion in spec 4.3 (accept both Summer of '69 choruses and both Chelsea Dagger choruses, reject Pour Some Sugar On Me's).
- The strum source stays song-level (`Strums.source`); no per-section stem switch.
- Any detector change is gated per section; whole-song onset detection is unchanged.
- Sheet copy, verbatim: "Strum heard in this section; covers NN% of detected strokes. Up and down follow the beat"; "(uncertain)" and "same as <label>" kept; "repeatable" removed.
- Beat file for the chord model: headerless, tab-separated `time<TAB>index<TAB>position`; a pickup bar's lone beat takes the bar's last position (4 in 4/4).
- UK spelling; no em-dashes in code, copy or docs; no song lyrics anywhere; no time or effort estimates in docs. Commit trailer per the session's attribution rule.
- Runs dir for validation: `C:\Users\gethi\sources\Youkelele\runs` (absolute). The five validation songs: sEXHeTcxQy4 (Chelsea Dagger), 9f06QZCVUHg (Summer of '69), 0UIB9Y4OFPs (Pour Some Sugar On Me), lbc6CcZTp5E (Wet Leg "mangetout"), Ypgq0qdgVZA (David Bowie "Fame").

## Review Focus

1. `evaluate` on a run folder without `04_strums/strums.json` (a run stopped at harmony) prints the chord diagnostics and "n/a" for the strum ones, rather than crashing. Test in Task 1.
2. `evaluate --compare` between two runs with different `slots_per_bar` or section counts says so and compares what it can, rather than raising. Test in Task 1.
3. The recall gate on a section with no onsets at all today (an intro before the guitar enters) never divides by zero and never adds onsets to silent bars. Test in Task 4.
4. The trailing-bars rule never empties a section or the song: if every bar is `N`, nothing is dropped. Test in Task 5.
5. Beat-aware decoding with a grid whose pickup bar has one beat numbers it as the last position, and with an empty beat list decodes as today. Test in Task 6.

---

### Task 1: Truth-free `evaluate` and `--compare`

**Confidence:** 92%

**Files:**
- Modify: `src/youkelele/evaluate.py` (`Report` lines 23-29, `evaluate_run` lines 101-130, `format_report` lines 136-146), `src/youkelele/commands.py:126-140` (`evaluate_command`), `src/youkelele/cli.py:62-67` (`--truth` becomes optional, add `--compare`), `src/youkelele/music/as_played.py` (add `explained_onsets`)
- Test: `tests/test_evaluate.py`, `tests/test_as_played.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `Grid`, `Chords`, `Strums` models; `mir_eval.chord.overseg`, `underseg`, `seg`, `evaluate`.
- Produces: `explained_onsets(bars: Sequence[Sequence[StrikeClass]], vector: Sequence[StrikeClass]) -> float` in `as_played.py` (share of strikes `S`/`x` in `bars` whose slot is struck in `vector`; 0.0 when `bars` has no strikes). `Report` gains `n_share: float | None`, `all_n_bars: int | None`, `filled_bars: int | None`, `changes_on_bar_share: float | None`, `sub_beat_events: int | None`, `key_confidence: float | None`, `boxes_mostly_rests: int | None`, `sections: list[SectionDiag]` with `@dataclass SectionDiag(index: int, label: str, strikes_per_bar: float, explained: float, rest_share: float, uncertain: bool, recall_boost: bool)`; `evaluate_run(run_dir: Path, truth_dir: Path | None = None) -> Report`; `compare_runs(a: Path, b: Path) -> Comparison` with `@dataclass Comparison(overseg: float | None, underseg: float | None, seg: float | None, majmin: float | None, sections: list[tuple[SectionDiag | None, SectionDiag | None]], notes: list[str])`; `format_report(r: Report) -> str`; `format_comparison(c: Comparison) -> str`. "Changes on bar" counts chord changes (consecutive events with different labels) whose start is within 60 ms of a bar start, over all changes; a sub-beat event is shorter than the median beat interval; `strikes_per_bar` and `explained` are computed from `strums.bar_onsets` over the section's bars and the section's pattern, so 1.2 runs score without stored fields; `rest_share` is the share of `-` in the pattern; `boxes_mostly_rests` counts sections printed as certain (not uncertain, not no_instrument) with `rest_share >= 0.75`.
- CLI: `evaluate <slug> [--truth DIR] [--compare SLUG]`; with neither, the truth-free report; with `--compare`, the comparison appended.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_as_played.py
def test_explained_onsets_share_of_strikes_on_pattern_slots():
    bars = [["S","-","S","-"], ["S","-","-","S"]]
    assert explained_onsets(bars, ["S","-","S","-"]) == 0.75   # 3 of 4 strikes on struck slots
def test_explained_onsets_zero_without_strikes(): ...
# tests/test_evaluate.py
def test_evaluate_without_truth_reports_chord_diagnostics(tmp_path): ...     # n_share, all_n_bars, changes_on_bar_share from a small synthetic run
def test_evaluate_without_truth_reports_strum_diagnostics(tmp_path): ...     # strikes_per_bar, explained, rest_share per section; boxes_mostly_rests
def test_evaluate_without_strums_json_reports_na(tmp_path): ...              # Review Focus 1
def test_compare_identical_runs_is_identity(tmp_path): ...                  # seg 1.0, majmin 1.0, every section pair equal
def test_compare_mismatched_slots_notes_and_continues(tmp_path): ...         # Review Focus 2
def test_format_report_prints_na_for_missing(): ...
# tests/test_cli.py
def test_evaluate_truth_is_optional_and_compare_accepted(): ...
```

- [ ] **Step 2: Run them to verify they fail** (`uv run pytest tests/test_evaluate.py tests/test_as_played.py tests/test_cli.py -q -W error`).
- [ ] **Step 3: Implement** `explained_onsets`, the `Report` fields, `evaluate_run` with optional truth, `compare_runs`, the two formatters, the CLI change. Existing truth-based tests stay green.
- [ ] **Step 4: Run tests; full fast suite green** (`uv run pytest -q -W error -m "not slow"`).
- [ ] **Step 5: Check on a real run**: `uv run youkelele evaluate 9f06qzcvuhg --runs-dir C:\Users\gethi\sources\Youkelele\runs` prints; `--compare 9f06qzcvuhg` gives seg 1.0 and majmin 1.0. Record the printed `changes_on_bar_share` and `boxes_mostly_rests` for the five runs in the report file (the 1.2 baseline numbers).
- [ ] **Step 6: Commit** `feat: truth-free evaluate diagnostics and run-to-run compare`.

---

### Task 2: Persisted raw output and `--debug`

**Confidence:** 92%

**Files:**
- Modify: `src/youkelele/options.py` (`RunOptions.debug: bool = False`), `src/youkelele/cli.py:39-50` (`run.add_argument("--debug", action="store_const", const=True, default=None)` so the manifest merge keeps working), `src/youkelele/stages/grid.py:51-66,117` (write `grid/beats_raw.json`), `src/youkelele/stages/harmony.py:66-72` (copy `work_dir/out.lab` to `harmony/spans.lab` before the `rmtree`), `src/youkelele/stages/strums.py` (write `strums/onsets.txt` when `ctx.options.debug`)
- Test: `tests/test_stage_grid.py`, `tests/test_stage_harmony.py`, `tests/test_stage_strums.py`, `tests/test_cli.py`

**Interfaces:**
- Produces: `grid/beats_raw.json` as `BeatsRaw(detected_beats: list[float], detected_downbeats: list[float], inserted_beats: list[float], dropped_beats: list[float])` in `schemas.py` (the lists come from comparing the detector's output with the result of `fill_gaps` and `normalise_octave`); `harmony/spans.lab` (the model's raw `.lab`, three tab-separated columns); `strums/onsets.txt` Audacity label track `start<TAB>end<TAB>label` with `end = start`, label `S` or `x`, and Task 4 appends `+` for an added onset. Both stages add the new file to `produces`; `GENERIC_STAGES` order is unchanged. The runner's stale logic hashes `requires`, not `produces`, so no manifest change.
- The fake recogniser in the harmony tests must write `out.lab` into `work_dir` for the copy to have a source; adjust the fake accordingly.

- [ ] **Step 1: Write the failing tests**

```python
def test_grid_stage_writes_beats_raw_with_insertions(tmp_path): ...          # detector with one missing beat -> inserted_beats has it
def test_harmony_stage_keeps_raw_spans(tmp_path): ...                        # spans.lab exists and parses to the recogniser's spans
def test_strums_stage_writes_onsets_txt_only_with_debug(tmp_path): ...       # absent by default; with options.debug, one line per onset, 'x' for mutes
def test_run_parser_debug_defaults_to_none(): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_grid.py tests/test_stage_harmony.py`.**
- [ ] **Step 4: Commit** `feat: persist raw beats and chord spans; --debug onset export`.

---

### Task 3: Strike vote, density floor and `explained` on the sheet

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/music/as_played.py` (`majority_vector` lines 40-53, `section_summary` lines 63-71, constants), `src/youkelele/schemas.py` (`SectionPattern.explained`, `ScoreSection.explained`), `src/youkelele/stages/strums.py:81-87` (uncertain rule, `explained`), `src/youkelele/music/score_builder.py:167-171` (copy `explained`), `src/youkelele/render/html.py:68-78`, `src/youkelele/render/templates/sheet.html.j2:96`
- Test: `tests/test_as_played.py` (lines 39-57 assert the old `> n/2` rule; update), `tests/test_stage_strums.py`, `tests/test_score_builder.py`, `tests/test_html.py`

**Interfaces:**
- Consumes: `explained_onsets` (Task 1).
- Produces: `STRIKE_SHARE = 1/3`, `DENSITY_FLOOR = 0.6`, `EXPLAINED_BELOW = 0.6`; `majority_vector(bars, threshold: float = STRIKE_SHARE) -> list[StrikeClass]` (struck when `strikes > threshold * n`); `fill_to_floor(vector, rates: Sequence[float], floor: int) -> list[StrikeClass]` (adds the highest-rate unstruck slots as `S` until the count reaches `floor`); `section_summary(bars, slots_per_bar, meter) -> tuple[list[Slot], float, float, float]` returning `(rendered, confidence, bar_repeat, explained)` where the vector is `fill_to_floor(majority_vector(bars), rates, round(DENSITY_FLOOR * median strikes per bar))`; stage sets `SectionPattern.explained` and `uncertain = confidence < UNCERTAIN_BELOW or explained < EXPLAINED_BELOW or not long_enough`; inherited patterns copy the donor's `explained`; `build_score` copies `explained` to `ScoreSection`; the template line becomes `Strum heard in this section; covers {{ "%d" % (section.explained * 100) }}% of detected strokes. Up and down follow the beat{% if section.uncertain %} (uncertain){% endif %}{% if section.inherited_from is not none %}, same as {{ inherited label }}{% endif %}` and `bar_repeat` no longer prints.

- [ ] **Step 1: Write the failing tests**

```python
def test_majority_vector_third_share_keeps_slots_struck_in_41_percent_of_bars(): ...   # 5 of 12 bars strike slot 0 -> S (was -)
def test_fill_to_floor_adds_highest_rate_slots(): ...                                   # vector S--- with rates [1,.3,.2,.1], floor 2 -> SS--
def test_section_summary_returns_explained(): ...
def test_dense_section_never_gets_sparser(): ...                                        # all-S bars -> SSSSSSSS, explained 1.0
def test_stage_marks_uncertain_when_explained_low(tmp_path): ...
def test_inherited_pattern_copies_explained(tmp_path): ...
def test_score_copies_explained(): ...
def test_html_prints_explained_not_repeatable(): ...                                    # "covers 85% of detected strokes"; "repeatable" absent
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green.**
- [ ] **Step 4: Commit** `feat: third-share strike vote with a density floor; explained replaces repeatable`.

---

### Task 4: Recall gate for loud sustained sections

**Confidence:** 90% (the method is spiked and confirmed by ear; two constants are measured here against a stated acceptance criterion, with a stated fallback if none separates)

**Files:**
- Create: `src/youkelele/music/recall.py`, `tests/test_recall.py`, `docs/superpowers/specs/2026-10-04-v1-3-recall-measurements.md`
- Modify: `src/youkelele/music/onsets.py:38-52` (`detect_onsets(y, sr, fmin: float | None = None)`), `src/youkelele/stages/strums.py` (gate before quantisation; `onsets.txt` `+` marks), `src/youkelele/schemas.py` (`SectionPattern.recall_boost`)
- Test: `tests/test_onsets.py`, `tests/test_stage_strums.py`

**Interfaces:**
- Consumes: `Onsets`, `quantise_bar`, `grid_fit`, `mute_mask` (onsets.py); `majority_vector`, `fill_to_floor`, `jaccard`, `explained_onsets` (Tasks 1 and 3).
- Produces, in `onsets.py`: `detect_onsets(y, sr, fmin=None)`; with `fmin`, the envelope is `librosa.onset.onset_strength(y=y, sr=sr, hop_length=512, fmin=fmin, aggregate=np.mean)` and peaks come from `librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=512, units="time", backtrack=False)`; centroid and zcr are taken at the same frames as today.
- Produces, in `recall.py`: constants `HIGH_BAND_FMIN = 3000.0`, `SPARSE_SHARE = 0.4`, `MERGE_MS = 60.0`, `MIN_GAIN = 1.0`, `FIT_TOLERANCE = 0.05`, `SILENT_BAR_SHARE` and `EXPLAINED_KEEP` (measured in Step 4, evidence comment beside each); `merge_onsets(base: Onsets, extra: Onsets, merge_ms: float, keep: np.ndarray) -> tuple[Onsets, np.ndarray]` (union sorted by time, `extra` entries within `merge_ms` of a base entry dropped, `keep` a boolean mask of extra entries allowed; returns the union and a boolean array marking added entries); `silent_bar_mask(y, sr, bars: Sequence[Bar], share: float) -> np.ndarray` (True where the bar's RMS is below `share` times the median bar RMS over the section's bars); `@dataclass SectionDecision(accepted: bool, before: float, after: float, reason: str)`; `gate_section(base: Onsets, extra: Onsets, y, sr, bars: Sequence[Bar], slots_per_bar: int, song_fit: float, meter: Meter) -> tuple[Onsets, np.ndarray, SectionDecision]` applying spec 4.3: try only if base strikes per bar `< SPARSE_SHARE * slots_per_bar`; exclude silent bars; keep the union only if strikes per bar rise by at least `MIN_GAIN`, mean Jaccard to the own vote (the Task 3 vote) does not fall, raw onsets per bar `<= slots_per_bar`, section grid fit `>= song_fit - FIT_TOLERANCE`, and `explained_onsets` of the union's own vote `>= EXPLAINED_KEEP`; `reason` names the first failing check or `"accepted"`. A section with no base onsets and no instrument is skipped (`reason "no onsets"`), never divided by zero (Review Focus 3).
- Stage: after today's `onsets = detect(y, sr)`, compute `high = detect(y, sr, fmin=HIGH_BAND_FMIN)` once; per section call `gate_section` over the section's bars and splice accepted unions into the song-level onset list (the per-section pieces do not overlap because bars partition time); then `mute_mask` on the final list, `quantise_bar` as today; `SectionPattern.recall_boost = decision.accepted`; log one line per accepted section (`recall boost: section 4, 2.9 -> 5.2 strikes per bar`); `onsets.txt` marks added onsets with `+`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_onsets.py
def test_detect_onsets_high_band_finds_click_in_sustained_tone(): ...        # synthetic: 200 Hz sustained tone + 4 kHz clicks each half beat -> high band finds the clicks the default misses
# tests/test_recall.py
def test_merge_onsets_drops_extra_within_60ms_and_marks_added(): ...
def test_silent_bar_mask_marks_bars_far_below_median(): ...
def test_gate_accepts_sparse_section_with_regular_union(): ...               # base 2/bar, union 5/bar regular -> accepted, recall_boost
def test_gate_rejects_when_union_sprays_slots(): ...                         # union explained below EXPLAINED_KEEP -> rejected, reason "explained"
def test_gate_skips_dense_section(): ...                                     # base >= SPARSE_SHARE * slots -> untouched
def test_gate_skips_section_without_onsets(): ...                            # Review Focus 3
def test_gate_adds_nothing_in_silent_bars(): ...
# tests/test_stage_strums.py
def test_stage_sets_recall_boost_and_marks_added_onsets(tmp_path): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement with provisional `SILENT_BAR_SHARE = 0.25`, `EXPLAINED_KEEP = 0.85`; tests green.**
- [ ] **Step 4: Measure the two constants on the real runs** (read-only on `C:\Users\gethi\sources\Youkelele\runs`; scripts and tables in the session scratchpad). Run the gate on the `guitar` stems of the five runs with the 1.2 grids. Tabulate per section: base and union strikes per bar, Jaccard before and after, raw onsets per bar, section fit, union `explained`, decision. Acceptance criterion (spec 4.3): Summer of '69 bars 41-53 and 83-95 accepted; Chelsea Dagger bars 9-38 and 105-142 accepted with no onsets added in bars 9-11 (silent before the guitar enters); Pour Some Sugar On Me bars 28-39, 55-67, 84-103 rejected; Wet Leg and Fame unchanged. Choose `EXPLAINED_KEEP` inside the gap between the accepted sections' lowest `explained` and the rejected sections' highest; choose `SILENT_BAR_SHARE` so Chelsea's bars 9-11 are excluded and no struck bar in any accepted section is. If no `EXPLAINED_KEEP` separates them, add the fallback from the spec (the gate also requires `slots_per_bar == 8`), record why, and keep the strictest value that accepts the four. Write the table and the chosen values to `docs/superpowers/specs/2026-10-04-v1-3-recall-measurements.md`; put the values and a one-line citation beside the constants.
- [ ] **Step 5: Full fast suite green; `uv run pytest -q -m slow tests/test_stage_strums.py` if a slow test exists there.**
- [ ] **Step 6: Commit** `feat: per-section high-band recall gate for sustained strums` (code, tests, measurements doc together).

---

### Task 5: Trailing bars that are not music

**Confidence:** 92%

**Files:**
- Create: `src/youkelele/music/trailing.py`, `tests/test_trailing.py`
- Modify: `src/youkelele/stages/strums.py` (`requires` adds `harmony/chords.json`; the last section's analysed bars exclude the trailing ones), `src/youkelele/music/score_builder.py:128-172` (the last section's `end_bar` shrinks; `Score.trailing_bars_dropped`), `src/youkelele/schemas.py` (`Score.trailing_bars_dropped: int = 0`)
- Test: `tests/test_stage_strums.py`, `tests/test_score_builder.py`, `tests/test_stage_score.py`

**Interfaces:**
- Produces: `trailing_silent_bars(chords: Chords, bars: Sequence[Bar]) -> int`: the number of bars at the end of the song that start at or after the end of the last event whose label is not `N` (filled events count as chords); 0 when there is no such event (Review Focus 4: an all-`N` song drops nothing) and never more than `len(last section) - 1` (a section is never emptied; the stage passes the last section's length as a cap: `trailing_silent_bars(chords, bars, cap: int)`).
- Strums stage: computes `drop = trailing_silent_bars(chords, grid.bars, cap=len(last section))` and analyses the last section over `bars[start_bar:end_bar - drop]`; `bar_onsets` still covers every bar (one entry per grid bar) so the score and `evaluate` indices stay aligned.
- Score builder: the same function gives `drop`; the last section's `end_bar` becomes `end_bar - drop` after phrase alignment; `Score.trailing_bars_dropped = drop`; dropped bars print nowhere (the renderer needs no change because they are not in the score).

- [ ] **Step 1: Write the failing tests**

```python
def test_trailing_silent_bars_counts_bars_after_last_chord(): ...        # last chord ends at bar 110 start of a 113-bar song -> 3
def test_trailing_silent_bars_counts_filled_as_chords(): ...
def test_trailing_silent_bars_zero_when_song_is_all_n(): ...             # Review Focus 4
def test_trailing_silent_bars_capped_to_keep_one_bar_in_the_section(): ...
def test_strums_stage_ignores_trailing_bars_in_last_section(tmp_path): ...  # pattern unaffected by noise onsets in the trailing bars
def test_score_drops_trailing_bars_and_records_count(): ...
def test_score_json_without_trailing_field_loads(): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green.**
- [ ] **Step 4: Commit** `feat: drop trailing no-chord bars from the sheet and the strum analysis`.

---

### Task 6: Beat-aware chord decoding

**Confidence:** 92% (spiked: the decoder accepts our beat file; the driver's gotchas are known)

**Files:**
- Create: `src/youkelele/models/chord_driver.py`, `tests/test_chord_driver.py`
- Modify: `src/youkelele/models/chords.py:30-54` (`recognise_chords(wav, work_dir, log, beats=None)`), `src/youkelele/stages/harmony.py:62-72,84-87` (build the beat list from `grid`, pass it, note `decoding`)
- Test: `tests/test_stage_harmony.py`

**Interfaces:**
- Produces, in `chords.py`: `recognise_chords(wav: Path, work_dir: Path, log=print, beats: Sequence[tuple[float, int]] | None = None) -> list[LabelSpan]`; `write_beat_file(beats: Sequence[tuple[float, int]], path: Path) -> None` writing `time<TAB>index<TAB>position` with a 1-based running index; `beat_positions(grid: Grid) -> list[tuple[float, int]]` giving every gap-filled beat with its 1-based position in its bar, a pickup bar's lone beat numbered `meter.numerator` (Review Focus 5). With `beats`, the child command is `[sys.executable, <abs path of chord_driver.py>, wav, out_lab, "submission", beats_lab]`; without, today's `chord_recognition.py` command, unchanged.
- Produces, in `chord_driver.py` (run as a script, cwd = model dir, `sys.path.insert(0, ".")` first): builds the `DataEntry` as the model's `chord_recognition.py` lines 15-26 do, `entry.append_file(beats_lab, BeatLabIO, "beat")`, `hmm.decode_to_chordlab(entry, probs, False, use_beats=True, use_downbeats=True)` at the model's default penalties, writes `out_lab`. `static_ffmpeg.add_paths()` is called by the parent as today.
- Harmony stage: `spans = self._recogniser(wav, work_dir, ctx.log, beats=beat_positions(grid))`; `ctx.note("decoding", "beats+downbeats")`; the fake recogniser in tests accepts the keyword.

- [ ] **Step 1: Write the failing tests**

```python
def test_beat_positions_numbers_pickup_beat_last(): ...                   # pickup bar with one beat -> (t, 4) in 4/4; full bars 1..4
def test_write_beat_file_three_tab_columns(tmp_path): ...
def test_recognise_chords_passes_beats_file_to_driver(monkeypatch, tmp_path): ...   # subprocess.run captured; argv ends with beats.lab path; without beats, chord_recognition.py
def test_harmony_stage_passes_beats_and_notes_decoding(tmp_path): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_harmony.py`.**
- [ ] **Step 4: Check on the real run**: `uv run youkelele run <Summer of '69 URL> --from harmony --to harmony --runs-dir C:\Users\gethi\sources\Youkelele\runs` then `evaluate 9f06qzcvuhg`: `changes_on_bar_share` 1.0 (was 63 of 75), label set unchanged. Record both in the report.
- [ ] **Step 5: Commit** `feat: decode chords with the chain's beats and downbeats`.

---

### Task 7: The worked example on the sheet

**Confidence:** 90%

**Files:**
- Modify: `src/youkelele/render/strum_box.py` (add `worked_example_svg`), `src/youkelele/render/html.py:49-80`, `src/youkelele/render/templates/sheet.html.j2:99-101`
- Test: `tests/test_strum_box.py`, `tests/test_html.py`, `tests/test_stage_render.py`

**Interfaces:**
- Consumes: `ScoreSection.pattern`, `ScoreBar.chords[].name/start_slot`, `Meter`; the box's `_PER_SLOT = 28`, `_H`, `_ARROWS`.
- Produces: `example_bars(section: ScoreSection) -> list[ScoreBar]`: the first two bars; if neither has more than one chord and a later bar does, that bar replaces the second; one bar if the section has one; `worked_example_svg(pattern: Sequence[Slot], bars: Sequence[ScoreBar], meter: Meter) -> str`: width `len(bars) * slots * _PER_SLOT` plus bar-line gaps, stroke row drawn with `_ARROWS` per slot, a chord row beneath placing each chord name at `start_slot` and a middle dot at every held slot, a vertical bar line between bars; the chord row uses the same `_INK`, 9 pt. `render_html` sets `"example": Markup(worked_example_svg(...))` when `show_box`, else `None`; the template prints it in the `strum-box` div under the pattern svg with class `worked-example`.

- [ ] **Step 1: Write the failing tests**

```python
def test_example_bars_prefers_a_bar_with_a_mid_bar_change(): ...
def test_example_bars_first_two_when_no_change(): ...
def test_worked_example_svg_places_second_chord_at_its_slot(): ...   # bar D(0) A(4) at 8 slots -> "A" text x = 4 * 28 + bar offset
def test_worked_example_svg_two_bars_have_a_bar_line(): ...
def test_html_prints_worked_example_under_each_box(): ...            # count of 'worked-example' == number of sections with a box
def test_html_no_example_without_instrument(): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_render.py`.**
- [ ] **Step 4: Visual check**: render Summer of '69 and Pour Some Sugar On Me from their `06_score/score.json` into the scratchpad, rasterise with `scratchpad\pwvenv\Scripts\python.exe` (PyMuPDF), look at page 1 of each: the example sits under the box, a half-bar change shows the second chord at its stroke, a 16-slot example fits the text width. Fix what is clearly wrong.
- [ ] **Step 5: Commit** `feat: worked example tying each section's strum pattern to its chords`.

---

### Task 8: Validation runs and docs

**Confidence:** 90%

**Files:**
- Create: `docs/superpowers/specs/2026-10-04-v1-3-validation.md`
- Modify: `README.md` (Known limitations, the `evaluate` and `--debug` usage), `docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-2-design.md` (one-line pointer to 1.3 at the top), `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock` (version 0.4.0)

- [ ] **Step 1: Save the 1.2 baselines**: copy the five run folders' `02_grid`, `03_harmony`, `04_strums`, `06_score` and `07_render` to the session scratchpad under `v1_2_baseline/<folder>/`, and `evaluate` each into `v1_2_baseline/<folder>/evaluate.txt`.
- [ ] **Step 2: Run the five songs** from their URLs with default settings plus `--debug`, `--runs-dir C:\Users\gethi\sources\Youkelele\runs`.
- [ ] **Step 3: Compare**: for each song, `evaluate <slug> --compare` against a copy of its baseline placed as a run folder in the scratchpad (the compare takes a run dir), and look at every page of every sheet (rasterised to the scratchpad).
- [ ] **Step 4: Write `2026-10-04-v1-3-validation.md`** against spec section 7: a summary table (song, pages 1.2 to 1.3, `boxes_mostly_rests` before and after, `changes_on_bar_share` before and after, recall-boosted sections, trailing bars dropped, verdict); per song, yes or no for every expectation with the evidence; the per-section strum table from `--compare` for Summer of '69 and Chelsea Dagger; what cannot be verified without listening; a ranked "What to improve next". No lyrics.
- [ ] **Step 5: Update README and the 1.2 spec pointer; bump the version to 0.4.0.**
- [ ] **Step 6: Run `uv run pytest -q -W error -m "not slow"` and `uv run pytest -q -m slow`; both green.**
- [ ] **Step 7: Commit** `docs: validate version 1.3 on five real songs; bump to 0.4.0`.

---

## Self-review notes

- **Spec coverage.** 4.1 harness: Tasks 1 and 2. 4.2 vote and `explained`: Task 3. 4.3 recall gate with both guards and measured constants: Task 4. 4.4 trailing bars: Task 5. 4.5 decoding: Task 6. 5 sheet (wording, worked example): Tasks 3 and 7. 6 data formats: Tasks 2 to 5. 7 validation: Task 8.
- **Rulings taken while planning:** `explained_onsets` lives in `as_played.py` from Task 1 so `evaluate` computes it from `bar_onsets` on 1.2 runs; the trailing rule is one function used by both stages, with the strums stage adding `harmony/chords.json` to its `requires`; `bar_onsets` keeps one entry per grid bar so indices stay aligned after bars are dropped from a section; the recall gate splices per-section unions into the song-level onset list before the mute medians are computed, as the spec says; `--debug` is a `store_const` so the None-default option merge keeps working.
- **Type consistency checked:** `explained_onsets(bars, vector)` (Task 1) is used by Tasks 3 and 4 and `evaluate`; `SectionPattern.explained` and `.recall_boost` (Tasks 3, 4) feed `SectionDiag` (Task 1 reads them when present, computes `explained` otherwise) and `ScoreSection.explained` (Task 3); `trailing_silent_bars(chords, bars, cap)` is the same call in both stages (Task 5); `beat_positions(grid)` and `recognise_chords(..., beats=)` (Task 6); `worked_example_svg(pattern, bars, meter)` (Task 7).
- **Review Focus:** items 1 and 2 tested in Task 1, 3 in Task 4, 4 in Task 5, 5 in Task 6.
- **Proportion:** the plan is about three times the spec's length, carried by the interface blocks and test names, with no function bodies.
