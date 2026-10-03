# Ukulele Tab Chain v1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `youkelele` sheet short and readable (a chord grid instead of a slash staff) and apply four measured stage-rule changes: a tempo cap on strum slots, a drum-backbeat test in the automatic tempo-octave rule, correct last-bar and pickup handling, and a re-weighted capo score.

**Architecture:** The chain, stages and file contracts stay as in version 1. The render stage drops alphaTab and draws a chord grid from `score.json` with plain HTML, CSS and inline SVG, still printed by Playwright. The grid stage gains a drums-stem input and two fields; `Bar` gains a `pickup` flag; the strums and arrange stages change one rule each. Every schema addition has a default, so version 1 run folders still load and can be resumed from any stage.

**Tech Stack:** Python 3.12, pydantic 2, Jinja2, librosa, numpy, Playwright 1.63.0, pytest. No new dependencies; one removed vendored bundle (alphaTab).

**Spec:** `docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-1-design.md` (read it first; it cites `docs/superpowers/specs/2026-10-03-real-run-lessons.md` for every measurement).

## Global Constraints

- All numeric rules are measured and binding: sixteen slots only when a sixteenth lasts at least 105 ms (bpm <= 140); backbeat band 1.5 to 6 kHz; halve only if bpm > 140, 60 <= bpm/2 <= 95 and (backbeat ratio < 1.0 or drums silent); drums silent when RMS < 0.003; capo score = mean over distinct chord names of the best shape cost + 0.2 per capo fret, no surcharge above fret 3; final bar ends one median beat interval after the last beat.
- Unchanged version 1 thresholds stay unchanged: 0.05 and 0.10 stem ratios, 25% odd-sixteenth share, 15% grid-fit tolerance, mute rule 0.85 and 0.65, 0.45 uncertainty floor, 0.6 stage grid-fit floor, 4-bar inheritance, shape_cost weights, 0.1 movement weight.
- Schema version stays 1; every new field has a default (`Bar.pickup = False`, `Grid.backbeat_ratio = None`, `Grid.drums_silent = False`).
- `score.json` stays bar by bar; row collapsing happens only in the renderer.
- `score.alphatex` is still written by the score stage; nothing reads it.
- The page is plain HTML, CSS and inline SVG: no scripts, no external resources; fixed `.sheet { width: 182mm }` on screen and `html, body { width: 182mm }` in print; `@page { size: A4; margin: 14mm }`.
- Fast suite runs with `-W error -m "not slow"` and must stay green at every commit; slow tests are run once per task that touches a real model or Chromium.
- Work in a worktree on a feature branch; commit per task with the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; never push from a task.
- uv: `C:\Users\gethi\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe` (not on PATH in Bash); run everything with `uv run`.
- UK spelling in user-facing text; no em-dashes in generated output.

## Confidence Summary

| Task | Confidence | Evidence |
|---|---|---|
| 1 Pickup flag and bar ends | 92% | Pure change to measured code; the pickup detection already exists in the grid stage |
| 2 Drum backbeat octave test | 90% | Measured on six songs in the lessons analysis (scripts in the scratchpad `lessons/` folder); synthetic drum tests determine the implementation |
| 3 Slot cap by tempo | 95% | One constant and one comparison; effect measured on all three songs |
| 4 Capo score re-weight | 92% | Seven variants measured on six chord lists; the winning formula and its margins are known |
| 5 CLI entry point | 98% | Standard Python |
| 6 Chord-grid sheet, alphaTab removed | 90% | Row collapse and cells are simple; print CSS for rows uses the same `break-inside` rule that held for sections in version 1; the risk is only visual polish, checked by eye in the slow test |
| 7 Validation runs and docs | 90% | Re-runs use existing run folders from the grid stage; expectations come from the spec table |

## Review Focus

1. **A song with no drums at 150 bpm detected** (solo ukulele or voice and guitar). Expected: the automatic rule halves it, as before, because the drums stem is silent. Test in Task 2.
2. **A section whose bars are all identical** (a twelve-bar one-chord vamp). Expected: one grid row with `×3`, not an empty section and not twelve rows. Test in Task 6.
3. **A section of one bar, or a section containing only the pickup bar.** Expected: a one-cell row, or just the pickup cell, never an index error. Test in Task 6.
4. **Tempo exactly 140.** Expected: sixteenths still allowed (the spec says 140 and below). Test in Task 3.
5. **Two capos with equal score.** Expected: the lower capo wins, as in version 1. Test in Task 4.

---

### Task 1: Grid bar ends and pickup flag

**Confidence:** 92%

**Files:**
- Modify: `src/youkelele/schemas.py` (`Bar`), `src/youkelele/music/tempo.py` (`build_bars`), `src/youkelele/stages/grid.py`
- Test: `tests/test_tempo.py`, `tests/test_schemas.py`, `tests/test_stage_grid.py`

**Interfaces:**
- Consumes: `build_bars(beats, downbeat_idx, meter, duration, chroma_per_beat=None) -> list[Bar]` (tempo.py:166), `Bar(index, start, end, beats)`.
- Produces: `Bar.pickup: bool = False`; `build_bars` unchanged in signature, with two new behaviours: a leading partial bar is returned with `pickup=True`; the final bar ends at `min(duration, last_beat + median_interval)` where `median_interval` is the median of consecutive beat differences, instead of at `duration`. The grid stage's own pickup detection (`grid.py:70-71`) is replaced by `bars[0].pickup`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tempo.py
def test_build_bars_marks_leading_partial_bar_as_pickup():
    bars = build_bars([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5], [1, 5], Meter(numerator=4, denominator=4), 5.0)
    assert bars[0].pickup is True and bars[0].beats == [0]
    assert all(b.pickup is False for b in bars[1:])

def test_build_bars_final_bar_ends_one_beat_after_last_beat_not_at_duration():
    beats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]        # 8 beats, 0.5 s apart
    bars = build_bars(beats, [0, 4], Meter(numerator=4, denominator=4), duration=13.5)
    assert bars[-1].end == pytest.approx(4.0)                # 3.5 + 0.5, not 13.5

def test_build_bars_final_bar_never_ends_after_duration():
    bars = build_bars([0.0, 0.5, 1.0, 1.5], [0], Meter(numerator=4, denominator=4), duration=1.7)
    assert bars[-1].end == pytest.approx(1.7)

# tests/test_schemas.py
def test_bar_pickup_defaults_false_so_version_1_files_load(): ...   # Bar(index=0, start=0, end=1, beats=[0]).pickup is False

# tests/test_stage_grid.py
def test_grid_stage_pickup_comes_from_bar_flag(tmp_path): ...       # fake detector with a 1-beat pickup -> grid.bars[0].pickup True and downbeats exclude it
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tempo.py tests/test_schemas.py tests/test_stage_grid.py -q -W error -m "not slow"`
Expected: FAIL on `pickup` attribute and on the final bar end.

- [ ] **Step 3: Add `pickup: bool = False` to `Bar`; in `build_bars` set `pickup=True` on the leading partial bar and compute the final bar end as described; in `grid.py` replace the local pickup detection with `bars[0].pickup` and use it for the `downbeats` list and the median bar length.**

- [ ] **Step 4: Run tests to verify they pass**

Run: the same command. Expected: PASS, whole fast suite green.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/schemas.py src/youkelele/music/tempo.py src/youkelele/stages/grid.py tests/test_tempo.py tests/test_schemas.py tests/test_stage_grid.py
git commit -m "fix: end the last bar one beat after the last beat and flag the pickup bar"
```

---

### Task 2: Drum backbeat test in the automatic octave rule

**Confidence:** 90%

**Files:**
- Create: `src/youkelele/music/backbeat.py`, `tests/test_backbeat.py`
- Modify: `src/youkelele/music/tempo.py` (`decide_octave`), `src/youkelele/schemas.py` (`Grid`), `src/youkelele/stages/grid.py`
- Test: `tests/test_tempo.py`, `tests/test_stage_grid.py`

**Interfaces:**
- Consumes: `decide_octave(bpm: float, mode: OctaveMode) -> OctaveDecision` (tempo.py:53); `GridStage.requires = ("ingest/audio.wav",)`; stems at `separate/stems/drums.wav` produced by the separate stage.
- Produces, in `backbeat.py`: `DRUMS_SILENT_RMS = 0.003`; `BACKBEAT_BAND_HZ = (1500.0, 6000.0)`; `drums_silent(y: np.ndarray) -> bool` (RMS below `DRUMS_SILENT_RMS`); `backbeat_ratio(y: np.ndarray, sr: int, beats: Sequence[float], numerator: int) -> float | None`: band-limited spectral flux (`librosa.onset.onset_strength` on an STFT restricted to the band, or `librosa.feature.spectral_flux` on the band-passed signal) sampled at each beat time, summed over beats whose index within the bar (`i % numerator`) is 1 or 3 divided by the sum over indices 0 and 2, with the bar phase taken from the first downbeat index passed as beat index 0; `None` when fewer than 8 beats or the denominator is 0. For a 3/4 meter use indices 1 and 2 against 0.
- Produces, in `tempo.py`: `decide_octave(bpm: float, mode: OctaveMode, backbeat_ratio: float | None = None, drums_silent: bool = False) -> OctaveDecision`: `auto` returns `half` iff `bpm > 140 and 60 <= bpm/2 <= 95 and (drums_silent or backbeat_ratio is None or backbeat_ratio < 1.0)`; other modes pass through. (`None` ratio counts as no evidence against halving, so a missing drums stem keeps the version 1 behaviour.)
- Produces, in `schemas.py`: `Grid.backbeat_ratio: float | None = None`, `Grid.drums_silent: bool = False`.
- Produces, in `grid.py`: `GridStage.requires = ("ingest/audio.wav", "separate/stems/drums.wav")`; the stage reads the drums stem mono, computes `drums_silent` and `backbeat_ratio` on the gap-filled beats BEFORE the octave decision (beats at the detected octave, bar phase from the first detected downbeat), passes them to `decide_octave`, logs `backbeat ratio X.XX` or `drums silent`, and writes both fields.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_backbeat.py
def _drum_track(sr, bpm, seconds, hit_beats):   # noise bursts (20 ms, 2 to 5 kHz band-limited) on the given beat indices within each 4-beat bar
    ...
def test_backbeat_ratio_above_one_for_snare_on_two_and_four(): ...   # hits on beats 1,3 (0-based) -> ratio > 1.5
def test_backbeat_ratio_below_one_for_hits_on_one_and_three(): ...   # hits on 0,2 -> ratio < 0.7
def test_backbeat_ratio_none_for_fewer_than_eight_beats(): ...
def test_drums_silent_true_for_near_silence_false_for_hits(): ...    # zeros + 1e-4 noise -> True; the drum track -> False

# tests/test_tempo.py
def test_decide_octave_auto_keeps_150_with_strong_backbeat(): assert decide_octave(150, "auto", backbeat_ratio=2.1) == "none"
def test_decide_octave_auto_halves_150_with_weak_backbeat(): assert decide_octave(150, "auto", backbeat_ratio=0.57) == "half"
def test_decide_octave_auto_halves_150_when_drums_silent(): assert decide_octave(150, "auto", backbeat_ratio=None, drums_silent=True) == "half"
def test_decide_octave_auto_halves_150_with_no_evidence(): assert decide_octave(150, "auto") == "half"
def test_decide_octave_never_halves_139_or_outside_band(): assert decide_octave(139, "auto", 0.2) == "none"; assert decide_octave(200, "auto", 0.2) == "none"

# tests/test_stage_grid.py
def test_grid_stage_requires_drums_stem_and_records_backbeat(tmp_path): ...  # fake detector at 150 bpm; synthetic drums stem with hits on 2 and 4 -> octave "none", grid.backbeat_ratio > 1, drums_silent False
def test_grid_stage_halves_when_drums_stem_silent(tmp_path): ...             # same beats, silent stem -> octave "half", drums_silent True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_backbeat.py tests/test_tempo.py tests/test_stage_grid.py -q -W error -m "not slow"`
Expected: FAIL with `ImportError` for `backbeat` and `TypeError` on the new `decide_octave` arguments.

- [ ] **Step 3: Implement `backbeat.py`, extend `decide_octave`, add the `Grid` fields, and wire the stage (read `separate/stems/drums.wav` via `soundfile`, mono average).**

Reference: the measurement script from the lessons analysis at `C:\Users\gethi\AppData\Local\Temp\claude\C--Users-gethi-sources-Youkelele\220af8bd-a800-4337-8952-bc02c39eceb8\scratchpad\lessons\` (read-only; copy the band-limited flux logic, not the file).

- [ ] **Step 4: Run tests to verify they pass; then the slow grid test**

Run: the fast command above; then `uv run pytest -q -m slow tests/test_stage_grid.py` (the click-track test now needs a drums stem fixture: give it a silent one and assert the 120 bpm click is not halved because 120 is below 140).
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/backbeat.py src/youkelele/music/tempo.py src/youkelele/schemas.py src/youkelele/stages/grid.py tests/test_backbeat.py tests/test_tempo.py tests/test_stage_grid.py
git commit -m "feat: gate automatic tempo halving on a drum backbeat test"
```

---

### Task 3: Strum slot cap by tempo

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/music/onsets.py` (`choose_slots_per_bar`), `src/youkelele/stages/strums.py`
- Test: `tests/test_onsets.py`, `tests/test_stage_strums.py`

**Interfaces:**
- Consumes: `choose_slots_per_bar(onsets, bars, meter) -> int` (onsets.py:90); the strums stage has `grid.bpm`.
- Produces: `SIXTEENTH_MIN_MS = 105.0`; `choose_slots_per_bar(onsets: Onsets, bars: Sequence[Bar], meter: Meter, bpm: float) -> int` returning `meter.numerator * 2` whenever `60000.0 / bpm / 4 < SIXTEENTH_MIN_MS` (that is bpm above 140 at 4/4), otherwise the version 1 rule. The stage passes `grid.bpm`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_onsets.py
def test_choose_slots_caps_at_eighths_above_140_bpm(): ...        # onsets with 40% odd sixteenths, bpm 158 -> 8
def test_choose_slots_allows_sixteenths_at_exactly_140(): ...     # same onsets, bpm 140 -> 16   (Review Focus 4)
def test_choose_slots_allows_sixteenths_at_86_bpm(): ...          # same onsets, bpm 86 -> 16
def test_choose_slots_eighths_when_share_low_regardless_of_tempo(): ...  # 10% odd, bpm 86 -> 8
# tests/test_stage_strums.py
def test_strums_stage_passes_grid_bpm_to_slot_choice(tmp_path): ...  # grid bpm 158 with sixteenth-heavy fake onsets -> slots_per_bar 8
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_onsets.py tests/test_stage_strums.py -q -W error -m "not slow"`
Expected: FAIL with `TypeError` (new argument) and wrong slot counts.

- [ ] **Step 3: Implement the constant and the cap; update every caller and existing test to pass `bpm` (existing tests use 120 bpm fixtures, so their expectations do not change).**

- [ ] **Step 4: Run tests to verify they pass**

Run: the same command plus `uv run pytest -q -W error -m "not slow"`. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/onsets.py src/youkelele/stages/strums.py tests/test_onsets.py tests/test_stage_strums.py
git commit -m "fix: never choose sixteenth strum slots above 140 bpm"
```

---

### Task 4: Capo score re-weight

**Confidence:** 92%

**Files:**
- Modify: `src/youkelele/music/arrange.py` (`score_capo`)
- Test: `tests/test_arrange.py`

**Interfaces:**
- Consumes: `score_capo(labels, capo, db) -> float` (arrange.py:34), `choose_capo` (unchanged, still breaks ties on the lower capo).
- Produces: `CAPO_FRET_PENALTY = 0.2`; `score_capo` = mean over `dict.fromkeys(labels)` (distinct labels in first-appearance order, excluding `N` and `X`) of `_best_cost(transpose_label(label, -capo))` with `_NO_SHAPE_COST` for no shape, plus `CAPO_FRET_PENALTY * capo`; no term above fret 3.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_arrange.py (replace the existing capo tests' expectations only where the brief below says)
PSSOM_RUN_LABELS = ["C#:maj"] * 6 + ["B:maj"] * 4 + ["E:maj"] * 3 + ["A:maj"] * 2 + ["F#:maj"]   # the run's label mix by frequency
PSSOM_SPIKE_LABELS = ["C#:min", "E:maj", "B:maj", "A:maj"]
CHELSEA_LABELS = ["G:maj"] * 7 + ["D:maj"] * 6 + ["E:min"] * 2 + ["B:min", "C:maj", "A:maj", "A:min", "B:maj"]

@pytest.mark.parametrize("labels,capo", [(S69_LABELS, 0), (PSSOM_RUN_LABELS, 4), (PSSOM_SPIKE_LABELS, 4), (CHELSEA_LABELS, 0), (RIPTIDE_LABELS, 0), (["C:maj","G:maj","A:min","F:maj"], 0)])
def test_choose_capo_matches_published_charts_with_unique_label_mean(labels, capo): ...
def test_score_capo_is_mean_over_distinct_labels_plus_0_2_per_fret(): ...   # repeated labels do not change the mean; capo 4 adds exactly 0.8
def test_choose_capo_tie_goes_to_lower_capo(): ...                           # Review Focus 5: a label set where capo 0 and capo 2 score equal -> 0
def test_s69_margin_at_least_0_3(): ...                                      # score_capo(S69_LABELS, 2) - score_capo(S69_LABELS, 0) >= 0.3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_arrange.py -q -W error`
Expected: FAIL on PSSOM run labels (version 1 picks capo 2) and on the formula test.

- [ ] **Step 3: Implement the new `score_capo`; remove the `0.3 * max(0, capo - 3)` term.**

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_arrange.py tests/test_stage_arrange.py -q -W error`. Expected: PASS (the stage test's flat-label progression stays at capo 0).

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/arrange.py tests/test_arrange.py
git commit -m "fix: score capo by the mean over distinct chords plus 0.2 per fret"
```

---

### Task 5: Command line module entry point

**Confidence:** 98%

**Files:**
- Create: `src/youkelele/__main__.py`
- Modify: `src/youkelele/cli.py` (add the guard)
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `python -m youkelele --version` and `python -m youkelele.cli --version` print the version and exit 0; `__main__.py` is `from youkelele.cli import main; raise SystemExit(main())`; `cli.py` ends with `if __name__ == "__main__": raise SystemExit(main())`.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("module", ["youkelele", "youkelele.cli"])
def test_module_entry_point_runs_main(module):
    proc = subprocess.run([sys.executable, "-m", module, "--version"], capture_output=True, text=True)
    assert proc.returncode == 0 and "0.1.0" in proc.stdout
```

- [ ] **Step 2: Run test to verify it fails** (both parametrisations: `youkelele` fails with "No module named youkelele.__main__", `youkelele.cli` exits 0 with empty stdout).

- [ ] **Step 3: Add `__main__.py` and the guard.**

- [ ] **Step 4: Run test to verify it passes.**

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/__main__.py src/youkelele/cli.py tests/test_cli.py
git commit -m "fix: make python -m youkelele run the CLI"
```

---

### Task 6: Chord-grid sheet, alphaTab removed

**Confidence:** 90%

**Files:**
- Create: `src/youkelele/render/grid.py`, `tests/test_render_grid.py`
- Modify: `src/youkelele/render/html.py`, `src/youkelele/render/templates/sheet.html.j2`, `src/youkelele/stages/render.py`, `src/youkelele/render/pdf.py` (only if it waits on `window.__rendered`: it must now wait on `document.fonts.ready` alone), `README.md` (remove the Chromium-plus-alphaTab wording; keep Chromium)
- Delete: `src/youkelele/vendor/alphatab/` (all files), the `assets` copy in the render stage, `ALPHATAB_VERSION`
- Test: `tests/test_html.py`, `tests/test_stage_render.py`

**Interfaces:**
- Consumes: `Score`, `ScoreSection(label, pattern, uncertain, bar_repeat, no_instrument, inherited_from, bars)`, `ScoreBar(index, chords)`, `ScoreChord(name, diagram, start_slot, slots)`, `Bar.pickup` via the grid? No: the score has no `Bar`; so `score_builder` must copy the flag. Add `ScoreBar.pickup: bool = False` (schemas.py) and set it in `build_score` from `grid.bars[bar.index].pickup`.
- Produces, in `render/grid.py`: `@dataclass Cell(text: str, nc: bool, pickup: bool)`; `@dataclass Row(cells: list[Cell], repeat: int)`; `cell_for(bar: ScoreBar) -> Cell` (one chord: its name; several: names in `start_slot` order joined by ` / `; none or only `N.C.`: text `N.C.`, `nc=True`; `pickup` copied); `grid_rows(section: ScoreSection, per_row: int = 4) -> list[Row]`: the pickup bar, if first, becomes its own one-cell row with `pickup=True`; the remaining bars are chunked into rows of `per_row`; consecutive rows with identical cell texts collapse into one row with `repeat` = count (a final short row never merges with a full row).
- Produces, in `html.py`: `render_html(score: Score) -> str` (the `alphatex` and `assets_rel` parameters are removed); per section the template receives `label`, `uncertain`, `no_instrument`, `repeat`, `inherited_from`, `svg` (the strum box, `None` when uncertain or no instrument) and `rows`; the header receives `capo_note` ("Shapes are relative to the capo") and `sounding_key` when capo > 0.
- Produces, in the template: no `<script>` elements; CSS `.row { display: grid; grid-template-columns: repeat(4, 1fr) auto; break-inside: avoid; }`, `.cell { border: 1px solid; padding: 2mm; font-size: 12pt; }`, `.cell.nc { color: var(--muted); }`, `.cell.pickup { grid-column: span 1; font-size: 9pt; }`, `.repeat { font-size: 10pt; align-self: center; }`, the section `break-inside: avoid-page` rule REMOVED, `.section-head { break-after: avoid }` kept.
- Produces, in `stages/render.py`: no `copytree`, no assets note; `html_path.write_text(render_html(score))`; `requires` unchanged (`score/score.alphatex` may stay required or be dropped: drop it, since nothing reads it; update `produces`/`requires` tests accordingly).
- Produces, in `pdf.py`: `html_to_pdf` waits for `document.fonts.ready` then prints; the `window.__rendered` wait is removed.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_render_grid.py
def test_cell_single_chord_name(): ...
def test_cell_mid_bar_change_joins_names_with_slash(): ...        # ScoreChord C at 0, G at 4 -> "C / G"
def test_cell_nc_bar(): ...                                        # name "N.C." diagram -1 -> text "N.C.", nc True
def test_grid_rows_chunks_into_fours(): ...                        # 10 bars -> rows of 4, 4, 2
def test_grid_rows_collapses_identical_consecutive_rows(): ...     # 12 bars G D G D -> one row repeat 3   (Review Focus 2)
def test_grid_rows_does_not_merge_short_final_row_into_full_row(): ...
def test_grid_rows_one_bar_section(): ...                          # Review Focus 3
def test_grid_rows_pickup_bar_is_its_own_cell(): ...               # first ScoreBar pickup True -> rows[0] has one pickup cell, then fours
# tests/test_html.py (replace the alphaTab-era tests)
def test_html_has_no_scripts_and_no_assets(): ...                  # "<script" not in html; "alphaTab" not in html
def test_html_renders_grid_rows_with_repeat_marker(): ...          # "×3" present for the collapsed chorus
def test_html_uncertain_section_has_heading_note_and_no_strum_box(): ...
def test_html_capo_header_notes(): ...                             # capo 4 -> "Shapes are relative to the capo" and "Sounding key"
def test_html_fixed_sheet_width_for_print(): ...                   # unchanged expectation
# tests/test_stage_render.py
def test_render_stage_writes_html_and_pdf_without_assets(tmp_path): ...  # no assets/ folder; fake pdf writer called
@pytest.mark.slow
def test_real_chromium_prints_120_bar_score_in_at_most_three_pages(tmp_path): ...  # PyMuPDF is NOT a dependency: count pages by reading the PDF's "/Type /Page" occurrences, or add pypdf to the dev group (ruling: add `pypdf` to dev dependencies)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_render_grid.py tests/test_html.py tests/test_stage_render.py -q -W error -m "not slow"`
Expected: FAIL with `ImportError` for `render.grid` and on the removed signature.

- [ ] **Step 3: Implement `render/grid.py`; add `ScoreBar.pickup` and set it in `music/score_builder.py`; rewrite the template; update `render_html`, the render stage and `html_to_pdf`; delete the vendored folder; update the README wording.**

- [ ] **Step 4: Run tests; then the slow render and end-to-end tests**

Run: the fast command; `uv run pytest -q -W error -m "not slow"`; `uv run pytest -q -m slow tests/test_stage_render.py tests/test_end_to_end.py`. Open page 1 of the slow test's PDF as an image (PyMuPDF from the scratchpad `pwvenv` if needed) and confirm by eye: legend, one strum box per section, grid rows with chord names, `×N` markers, no staff.
Expected: PASS; at most three pages.

- [ ] **Step 5: Commit**

```bash
git add -A src/youkelele/render src/youkelele/stages/render.py src/youkelele/schemas.py src/youkelele/music/score_builder.py README.md pyproject.toml uv.lock tests/test_render_grid.py tests/test_html.py tests/test_stage_render.py
git rm -r src/youkelele/vendor/alphatab
git commit -m "feat: render the sheet as a chord grid and remove alphaTab"
```

---

### Task 7: Validation runs and documentation

**Confidence:** 90%

**Files:**
- Modify: `tests/test_end_to_end.py` (add the page-count ceiling of two), `README.md` (usage unchanged; "Known limitations" updated: the slash staff is gone; the strike-threshold spike noted), `docs/superpowers/specs/2026-10-03-ukulele-tab-chain-design.md` (a one-paragraph note at the top pointing to the v1.1 spec for the sheet and the four rules)
- Create: `docs/superpowers/specs/2026-10-03-v1-1-validation.md`

**Interfaces:**
- Consumes: the three existing run folders under `C:\Users\gethi\sources\Youkelele\runs\` (`sexhetcxqy4`, `9f06qzcvuhg`, `0uib9y4ofps`) and the new URL `https://www.youtube.com/watch?v=lbc6CcZTp5E`.

- [ ] **Step 1: Add the end-to-end page assertion**

```python
    pdf_bytes = (run / "07_render" / "sheet.pdf").read_bytes()
    assert count_pages(pdf_bytes) <= 2        # helper from Task 6's slow test
```

- [ ] **Step 2: Run the three existing songs from the grid stage and the new song from scratch**

Run, from the repo root with the plan's worktree checked out:
```
uv run youkelele run "https://www.youtube.com/watch?v=sEXHeTcxQy4" --from grid --beat-octave auto --runs-dir C:\Users\gethi\sources\Youkelele\runs
uv run youkelele run "https://www.youtube.com/watch?v=9f06QZCVUHg" --from grid --runs-dir C:\Users\gethi\sources\Youkelele\runs
uv run youkelele run "https://www.youtube.com/watch?v=0UIB9Y4OFPs" --from grid --runs-dir C:\Users\gethi\sources\Youkelele\runs
uv run youkelele run "https://www.youtube.com/watch?v=lbc6CcZTp5E" --runs-dir C:\Users\gethi\sources\Youkelele\runs
```
(The first three reuse their separated stems; `--from grid` is needed because the grid stage now reads the drums stem and the octave rule changed. The run folders live in the main checkout, hence the explicit `--runs-dir`.)

- [ ] **Step 3: Record results against the spec's validation table**

Write `docs/superpowers/specs/2026-10-03-v1-1-validation.md`: per song, the octave decision and backbeat ratio, bpm, key, capo and shapes, slots per bar and grid fit, section count, page count, and a yes/no against each expectation in spec section 6; for Wet Leg "mangetout" record everything and a by-eye judgement of the grid against the record. Rasterise page 1 and 2 of each PDF and describe them in one line each. Any expectation not met is reported as such, not adjusted.

- [ ] **Step 4: Run the whole fast suite and the slow suite once**

Run: `uv run pytest -q -W error -m "not slow"`; `uv run pytest -q -m slow`. Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_end_to_end.py README.md docs/superpowers/specs/2026-10-03-ukulele-tab-chain-design.md docs/superpowers/specs/2026-10-03-v1-1-validation.md
git commit -m "docs: validate version 1.1 on four real songs"
```

---

## Self-review notes

- **Spec coverage.** 3.1 section block, 3.2 header, 3.3 alphaTab removed, 3.4 page target: Task 6 (and 7 for the ceiling). 4.1 slot cap: Task 3. 4.2 backbeat: Task 2. 4.3 bar ends and pickup: Task 1 (with `ScoreBar.pickup` carried in Task 6). 4.4 capo: Task 4. 4.5 entry point: Task 5. 5 data formats: Tasks 1, 2, 6. 6 validation: Task 7. 7 follow-on spike: documented, not built. 8 decisions: reflected in Global Constraints.
- **Rulings taken while planning:** `ScoreBar.pickup` is added so the renderer need not read `grid.json` (score stays the renderer's single input); `pypdf` is added to the dev dependency group for page counting in tests; `score/score.alphatex` is dropped from the render stage's `requires` since nothing reads it; a `None` backbeat ratio keeps version 1's halving behaviour so a run folder without a drums stem still resumes.
- **Type consistency checked:** `decide_octave(bpm, mode, backbeat_ratio=None, drums_silent=False)` in Tasks 2 and 7; `choose_slots_per_bar(onsets, bars, meter, bpm)` in Task 3; `render_html(score)` in Task 6 and the stage; `grid_rows` and `Row.repeat` used by the template tests.
- **Proportion:** the plan is about the spec's length plus test names; bodies appear only where the signature and tests leave a choice.
