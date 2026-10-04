# Ukulele Tab Chain, Version 1.4: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Right notes and right names: a key taken from the chord stream with its mode from the harmonic stems and a hedge when close; tonic power chords printed as the chord they stand for; sections bounded and named with the vocal stem and chart conventions; the no-capo alternative on the sheet; run folders named after the song; install-and-run scripts for people who do not code; a README for a visitor; an MIT licence.

**Architecture:** Nine tasks on the existing stage chain. Evidence is computed once where it is cheapest (harmonic chroma in harmony, vocal levels in grid) and decisions are made where the chord stream exists (key and power chords in harmony, names in score). Run-folder naming moves from the video id to the cleaned title, resolved by a manifest scan then a metadata-only fetch. `setup` fetches the chord model as a zip so git is not needed; Windows scripts wrap install and run. All new fields default; schema version stays 1.

**Tech Stack:** Python 3.12, pydantic 2, numpy, librosa (`chroma_cqt`), yt-dlp (metadata fetch), Jinja2 + inline SVG, Playwright PDF, PowerShell and cmd for the Windows scripts. uv at `C:\Users\gethi\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`.

**Spec:** `docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-4-design.md` (sections 3.1 to 3.7 stage changes, 4 sheet, 5 README, 6 data, 7 validation, 9 assumptions with the measured values).

## Global Constraints

- Schema version stays 1; version 1.3 files load: every new field defaults (`Key.method`, `Key.margin`, `Key.mode_margin`, `Key.runner_up`, `Key.mix`, `ChordEvent.power`, `ArrangedChord.power`, `Grid.bar_vocal_db`, `Score.alternative_diagrams`, `Manifest.video_id`, `Manifest.title_slug`).
- Constants, verbatim from the spec: `TONIC_MIN_SHARE = 0.2`, `FINAL_CHORD_BONUS = 0.10`, `SECTION_END_WEIGHT = 0.15`, `KEY_TIE_MARGIN = 0.05`, `KEY_HEDGE_MARGIN = 0.05`, `MODE_TIE_MARGIN = 0.05`, `POWER_MODE_MARGIN = 0.2`, `POWER_MIN_SHARE = 0.2`, `VOCAL_BELOW_MEDIAN_DB = 12`, `VOCAL_RUN_MIN_BARS = 4`, `INSTRUMENTAL_BELOW = 0.25`, `BRIDGE_NOVEL_CHORDS = 0.5`.
- Measured expectations on the 1.3 runs (spec 9): tonics Chelsea G by 0.150, PSSOM C# by 0.144, Wet Leg C by 0.209, Summer of '69 D by the pair rule (0.052, not hedged), Fame F (sole candidate); modes PSSOM minor by 0.423, S69 major 0.302, Chelsea major 0.299, Wet Leg major 0.216, Fame a 0.003 tie broken to major by its chords; vocal runs Chelsea (0, 20) and (93, 108), S69 (68, 75) and (114, 118), PSSOM (67, 77), Wet Leg trailing only, Fame (0, 17), (29, 35), (47, 61), (81, 85), (93, 101); bridge novelty 0.73 for S69 bars 58-69, 0.00 to 0.05 elsewhere.
- Sheet copy verbatim: hedge `Key: G major (or D major)`; no-capo line `Without a capo: C# 1114 (barre), F# 3124, ...`; badge legend line `C#m is a power chord on the record`; display names `Verse 1`, `Verse 2`, `Chorus`, `Instrumental 1`, `Bridge`, `Outro` (no number when a label occurs once).
- Run folder slug: cleaned title lowercased, ASCII-folded, non-alphanumerics to single hyphens, trimmed; empty falls back to the video id; collisions get `-2`, `-3`; the manifest scan by `source` comes before any network.
- `setup` must not call git. The installer assumes only Windows 10 or 11 with internet; Python is installed by uv.
- Licence: MIT (`LICENSE` file, `license = "MIT"` in `pyproject.toml`).
- UK spelling; no em-dashes in code, copy or docs; no song lyrics anywhere; no time or effort estimates in docs. Commit trailer per the session's attribution rule. Validation runs dir: `C:\Users\gethi\sources\Youkelele\runs` (absolute). Seven songs: sEXHeTcxQy4, 9f06QZCVUHg, 0UIB9Y4OFPs, lbc6CcZTp5E, Ypgq0qdgVZA, PsnYrH3BUP8 (Pat Benatar, All Fired Up), w-rv2BQa2OU (INXS, Need You Tonight).

## Review Focus

1. A song whose chord stream is all `N` (or fewer than four events) keeps today's mix-based key and prints no hedge-induced crash. Test in Task 1.
2. A vocals stem that is silent throughout (an instrumental track) must not label every section `instrumental`: when no bar is vocal, the labeller behaves as today. Test in Task 3.
3. A second song with the same cleaned title gets `-2`, and a re-run of the first still finds its own folder by `source`. Test in Task 6.
4. `install.ps1` run a second time on a prepared machine installs nothing and still ends with "Ready". Test in Task 7 (script-level check in a fresh folder).
5. A minor-key song whose tonic is genuinely major for part of the time (a Picardy cadence under 20 percent of chord time) is not relabelled. Test in Task 2.

---

### Task 1: Harmonic chroma once, key from the chord stream, hedged header

**Confidence:** 95% (every rule measured on the five 1.3 runs; spec 9 A1 to A3)

**Files:**
- Create: `src/youkelele/music/chroma.py`, `tests/test_chroma.py`
- Modify: `src/youkelele/music/key.py` (keep `estimate_key`, `chroma_mean_for`; add the chord-stream functions), `src/youkelele/music/fill.py:54-79` (`bar_chroma`, `bar_energy` become thin wrappers over `HarmonicChroma`), `src/youkelele/stages/harmony.py:29-45,62-90`, `src/youkelele/schemas.py:109-112` (`Key`), `src/youkelele/render/html.py:32-41,93-100`, `src/youkelele/render/templates/sheet.html.j2:65,74`, `src/youkelele/evaluate.py` (print key method and margins)
- Test: `tests/test_key.py`, `tests/test_fill.py`, `tests/test_stage_harmony.py`, `tests/test_html.py`, `tests/test_evaluate.py`

**Interfaces:**
- Produces, in `chroma.py`: `@dataclass HarmonicChroma(frames: np.ndarray, times: np.ndarray, sr: int)` with `bar_means(bars: Sequence[Bar]) -> np.ndarray` (bars x 12), `bar_energy(y_rms_per_bar)`: keep energy on the signal, so `harmonic_chroma(stems: Sequence[np.ndarray], sr: int) -> tuple[HarmonicChroma, np.ndarray]` returns the chroma and the summed mono signal; `HarmonicChroma.mean(mask: np.ndarray) -> np.ndarray` (mean over frames whose bar passes `mask`, falling back to all frames when the mask is empty). `chroma_cqt` with `hop_length=512`.
- Produces, in `key.py`: `TONIC_MIN_SHARE`, `FINAL_CHORD_BONUS`, `SECTION_END_WEIGHT`, `KEY_TIE_MARGIN`, `KEY_HEDGE_MARGIN`, `MODE_TIE_MARGIN`; `tonic_scores(events: Sequence[ChordEvent], bars: Sequence[Bar], sections: Sequence[Section]) -> dict[str, float]` (roots with at least `TONIC_MIN_SHARE` of non-N chord time; score = share + bonus when the final event's root matches and lasts at least the median full-bar length + `SECTION_END_WEIGHT` x share of sections whose last event has that root); `pair_shares(events, candidates: Sequence[str]) -> dict[str, float]` (time-weighted diatonic share of each candidate's relative-major pair, half credit for a diatonic root of the wrong quality); `mode_at(tonic: str, chroma_mean: np.ndarray) -> tuple[Literal["major", "minor"], float]` (Krumhansl major minus minor correlation at the tonic; the margin is the absolute difference); `tonic_chord_mode(tonic, events) -> Literal["major", "minor"] | None` (quality with more of the tonic root's time, sevenths by their third, None when the tonic has no chords); `key_from_chords(events, bars, sections, chroma_mean: np.ndarray, mix_key: Key) -> Key` applying spec 3.1: fewer than four non-N events returns `mix_key` with `method="mix_krumhansl"`; otherwise tonic by score, tie-break by pair share when the score margin is under `KEY_TIE_MARGIN`, mode by `mode_at` with `tonic_chord_mode` deciding under `MODE_TIE_MARGIN`; `Key(method="chords_stems", margin=<deciding margin>, mode_margin, runner_up, mix=mix_key, confidence=<mode margin>)`; `hedged(key: Key) -> bool` = `margin < KEY_HEDGE_MARGIN or (key.mix is not None and key.mix.tonic != key.tonic)`.
- Produces, in `schemas.py`: `Key.method: Literal["mix_krumhansl", "chords_stems"] = "mix_krumhansl"`, `Key.margin: float | None = None`, `Key.mode_margin: float | None = None`, `Key.runner_up: str | None = None`, `Key.mix: "Key | None" = None`.
- Harmony stage: computes `harmonic_chroma` once after reading the stems; the fill uses its bar means and `bar_energy` of the summed signal; the key is computed after the fill with the chroma mean masked to bars at or above `FILL_MIN_ENERGY` x the chorded median energy; `mix_key = estimate_key(self._chroma(wav))` as today; notes `key_method`, `key_margin`, `tonic_pair_rule` (the pair-rule winner and margin, always computed). Log: `key D major (chords+stems, margin 0.052 by pair rule)`.
- Render: `key_text(key: Key) -> str` giving `D major` or `G major (or D major)` when hedged; `_shape_key` hedged the same way under a capo (both tonics shifted). `Score.key` stays the plain string for 1.3 files; `Score` gains `key_hedge: str | None = None` carrying the runner-up's name when hedged, set by `build_score` from `chords.key`.
- `evaluate`: the key line prints `tonic mode (method, margin, mode margin, runner-up)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_chroma.py
def test_harmonic_chroma_bar_means_shape_and_mask_mean(): ...
# tests/test_key.py
def test_tonic_scores_root_share_final_bonus_and_section_ends(): ...   # synthetic: D 0.40, A 0.39, final D lasting a bar, 6 of 11 sections end on D -> D first
def test_tonic_tie_breaks_by_pair_share(): ...                           # D and A within 0.05 -> pair share decides D
def test_mode_at_tonic_major_and_minor(): ...                            # chroma built from a D major triad -> major; D minor -> minor
def test_mode_tie_falls_back_to_tonic_chord_quality(): ...               # flat chroma, tonic chords F:maj and F:7 -> major, margin recorded
def test_key_from_chords_falls_back_with_fewer_than_four_events(): ...   # Review Focus 1: method mix_krumhansl, mix key returned
def test_hedged_when_margin_small_or_mix_disagrees(): ...
def test_key_json_without_new_fields_loads(): ...
# tests/test_fill.py
def test_bar_chroma_and_energy_match_shared_chroma(): ...                # wrappers give the same arrays as before
# tests/test_stage_harmony.py
def test_harmony_stage_key_from_chords_and_notes(tmp_path): ...          # fake recogniser emits a D-major stream; key.method chords_stems; notes present
# tests/test_html.py
def test_header_hedges_key_and_shape_key_under_capo(): ...               # "Key G major (or D major)"; capo 2: "F major (or C major) (shapes)"
# tests/test_evaluate.py
def test_evaluate_prints_key_method_and_margins(tmp_path): ...
```

- [ ] **Step 2: Run them to verify they fail** (`uv run pytest tests/test_chroma.py tests/test_key.py tests/test_fill.py tests/test_stage_harmony.py tests/test_html.py tests/test_evaluate.py -q -W error -m "not slow"`).
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_harmony.py`.**
- [ ] **Step 4: Check on the real runs** (read-only on `C:\Users\gethi\sources\Youkelele\runs`): a scratch script calling `key_from_chords` on each of the five `chords.json` and `grid.json` with the harmonic chroma of the stems reproduces the spec 9 values (tonics and modes above; S69 decided by the pair rule and not hedged; Fame F major by its chords). Record the table in the report; if a value differs, stop and report rather than retune.
- [ ] **Step 5: Commit** `feat: key from the chord stream with mode from the harmonic stems and a hedged header`.

---

### Task 2: Tonic power chords

**Confidence:** 92% (gates measured on one song; the two new blind songs test them; the chroma third test was measured and rejected by the research, so no alternative is pending)

**Files:**
- Modify: `src/youkelele/music/triads.py:17-34` (`to_triad("X:5")` returns `"X:5"`-aware handling: no collapse to major), `src/youkelele/music/key.py` (add `power_chord_events(events, key, chroma_mean) -> list[int]`), `src/youkelele/stages/harmony.py` (relabel after the key), `src/youkelele/schemas.py` (`ChordEvent.power: bool = False`, `ArrangedChord.power: bool = False`, `ChordDiagram.power: bool = False`), `src/youkelele/music/arrange.py:123-139` (`simplify_for_tier` maps `X:5` to the key's quality in both tiers), `src/youkelele/stages/arrange.py` (copy `power`), `src/youkelele/music/score_builder.py` (copy to `ScoreChord.power` and `ChordDiagram.power`), `src/youkelele/render/html.py`, `src/youkelele/render/templates/sheet.html.j2`, `src/youkelele/render/grid.py` (`Cell.power`)
- Test: `tests/test_triads.py`, `tests/test_key.py`, `tests/test_stage_harmony.py`, `tests/test_arrange.py`, `tests/test_score_builder.py`, `tests/test_html.py`

**Interfaces:**
- Consumes: `Key` with `mode` and `mode_margin` (Task 1); the harmonic chroma mean (Task 1).
- Produces: `POWER_MODE_MARGIN`, `POWER_MIN_SHARE`; `power_chord_events(events: Sequence[ChordEvent], key: Key, chroma_mean: np.ndarray) -> list[int]`: indices of the tonic root's `maj` events when all four spec 3.2 gates hold (`key.mode == "minor"`; the tonic's `maj` time exceeds its `min` time; `mode_at(tonic, chroma_mean)` prefers minor by at least `POWER_MODE_MARGIN`; the tonic root holds at least `POWER_MIN_SHARE` of non-N chord time), else `[]`. The stage sets on those events `label = f"{root}:5"`, `triad = f"{root}:min"` (the key's quality), `power = True`. `to_triad` returns `f"{root}:min"` for a `:5` label only when given the key's quality? No: `to_triad` has no key; it returns the input unchanged for `X:5` labels (`"X:5"`), and the stage writes `triad` explicitly, so downstream reads `triad`. `simplify_for_tier("C#:5", tier, db)` maps to `"C#:min"` for both tiers with substitution reason `"power chord: quality from key"` (the `:5` label is replaced by the triad the stage wrote). Arrange copies `power` from the event to `ArrangedChord.power`; score copies it to `ScoreChord.power` and sets `ChordDiagram.power` when every use of the name is power. Render: a cell with `power` prints the name followed by `<sup>5</sup>` (easy tier: no badge); legend line per power diagram `{name} is a power chord on the record`.

- [ ] **Step 1: Write the failing tests**

```python
def test_to_triad_keeps_power_label(): assert to_triad("C#:5") == "C#:5"
def test_power_chord_events_fire_only_at_the_minor_tonic_with_all_gates(): ...   # synthetic PSSOM-like stream -> indices of C#:maj events
def test_power_chord_events_off_for_picardy_under_share(): ...                   # Review Focus 5: tonic major 10 percent of time -> []
def test_power_chord_events_off_in_major_key(): ...
def test_harmony_stage_relabels_power_events(tmp_path): ...                       # label C#:5, triad C#:min, power True
def test_simplify_for_tier_maps_power_to_key_quality(): ...
def test_score_sets_power_on_chord_and_diagram(): ...
def test_html_power_badge_and_legend_line(): ...                                  # "<sup>5</sup>" present in full tier, absent in easy; legend line verbatim
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green.**
- [ ] **Step 4: Check on the real run**: the scratch key script from Task 1 extended to `power_chord_events` on PSSOM returns its `C#:maj` events (about 41 percent of chord time) and `[]` on the other four. Record in the report.
- [ ] **Step 5: Commit** `feat: print tonic power chords as the key's chord with a badge`.

---

### Task 3: Vocal-aware section boundaries and labels

**Confidence:** 95% (runs measured on all five songs including the blind one; spec 9 A4)

**Files:**
- Modify: `src/youkelele/music/sections.py` (add `bar_stem_db`, `vocal_flags`, `vocal_runs`, `insert_vocal_boundaries`; `label_sections` gains `vocal: Sequence[bool] | None = None`), `src/youkelele/stages/grid.py:45,69-72,94-95,106-120`, `src/youkelele/schemas.py:59-72` (`Grid.bar_vocal_db: list[float] = []`), `src/youkelele/evaluate.py` (print vocal runs and section labels)
- Test: `tests/test_sections.py`, `tests/test_stage_grid.py`, `tests/test_evaluate.py`

**Interfaces:**
- Produces: `VOCAL_BELOW_MEDIAN_DB = 12.0`, `VOCAL_RUN_MIN_BARS = 4`, `INSTRUMENTAL_BELOW = 0.25`, `EDGE_INSTRUMENTAL_BELOW = 0.5`; `bar_stem_db(y, sr, bars) -> list[float]` (20 log10 of bar RMS, floor -120); `vocal_flags(db: Sequence[float]) -> list[bool]` (threshold = median over bars above -60 dB minus `VOCAL_BELOW_MEDIAN_DB`, then a 3-bar median filter; when no bar is above -60 dB every flag is True so nothing changes, Review Focus 2); `vocal_runs(flags) -> list[tuple[int, int]]` (non-vocal runs of at least `VOCAL_RUN_MIN_BARS` bars, excluding a run touching bar 0 only in that the first boundary never moves, and excluding the trailing run); `insert_vocal_boundaries(boundaries: list[int], runs, n_bars: int, min_bars: int = 4) -> list[int]` (each run edge becomes a boundary when both pieces keep `min_bars`; otherwise the nearest boundary moves onto the edge when the move is at most 3 bars and both neighbours keep `min_bars`; the first boundary and any boundary at or after the trailing run's start never move); `label_sections(boundaries, cluster_ids, bar_loudness_db, vocal=None)`: with `vocal`, a segment with vocal share under `INSTRUMENTAL_BELOW`, or the first or last under `EDGE_INSTRUMENTAL_BELOW`, is `intro` (first), `outro` (last) or `instrumental`; chorus candidates need bar-weighted vocal share at least 0.5; adjacent `intro`/`instrumental`/`outro` merge into one segment; with `vocal=None` behaviour is unchanged.
- Grid stage: `requires` adds `separate/stems/vocals.wav`; `Grid.bar_vocal_db` stored; `insert_vocal_boundaries` runs after `boundaries_from_clusters(..., min_bars=MIN_SECTION_BARS)` and before `label_sections(..., vocal=flags)`; the existing `_ctx` test helper writes a vocals stem. Logs the runs.
- `evaluate`: prints `vocal runs: (0, 20), (93, 108)` and each section's label beside its strum line.

- [ ] **Step 1: Write the failing tests**

```python
def test_vocal_flags_threshold_from_median_and_median_filter(): ...
def test_vocal_flags_all_true_when_stem_silent(): ...                    # Review Focus 2
def test_vocal_runs_skip_short_runs_and_trailing_run(): ...
def test_insert_vocal_boundaries_adds_edges_when_pieces_keep_four_bars(): ...
def test_insert_vocal_boundaries_moves_nearest_within_three_bars(): ...
def test_insert_vocal_boundaries_never_moves_first_boundary(): ...
def test_label_sections_instrumental_intro_and_merge(): ...              # Chelsea-shaped: first two segments non-vocal -> one "intro"
def test_label_sections_unchanged_without_vocal(): ...
def test_grid_stage_requires_vocals_and_stores_bar_vocal_db(tmp_path): ...
def test_grid_json_without_bar_vocal_db_loads(): ...
def test_evaluate_prints_vocal_runs_and_labels(tmp_path): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_grid.py`.**
- [ ] **Step 4: Check on the real runs**: a scratch script over the five `grid.json` and `vocals.wav` reproduces the spec 9 A4 runs; `label_sections` with the flags gives Chelsea `intro 0-20`, `chorus 20-38`, `instrumental 93-108`; both solos `instrumental`; Wet Leg unchanged. Record in the report.
- [ ] **Step 5: Commit** `feat: vocal-aware section boundaries and labels`.

---

### Task 4: Bridge by chord novelty and display names by occurrence

**Confidence:** 95% (novelty measured on 57 sections across five songs; spec 9 A5)

**Files:**
- Create: `src/youkelele/music/relabel.py`, `tests/test_relabel.py`
- Modify: `src/youkelele/music/sections.py:229-244` (drop `bridge 2` and the cluster-counting `verse 2`: once-only middle clusters are `verse`, other recurring clusters `verse`), `src/youkelele/music/score_builder.py` (`refine_labels` before building `ScoreSection`), `src/youkelele/render/html.py:60-80` (display names), `src/youkelele/render/templates/sheet.html.j2:92,97`
- Test: `tests/test_sections.py:157-173`, `tests/test_score_builder.py`, `tests/test_html.py`

**Interfaces:**
- Consumes: `Grid.sections` (with vocal-aware labels from Task 3), `Chords.events`, `Grid.bar_vocal_db`.
- Produces, in `relabel.py`: `BRIDGE_NOVEL_CHORDS = 0.5`; `section_novelty(grid, chords) -> list[float]` (per section, the share of its chord-bars whose triad occurs in no other section; a bar's triads are the non-N events overlapping it); `refine_labels(grid: Grid, chords: Chords) -> list[str]`: copies `grid.sections[i].label`; among sections whose label is in `{"verse", "chorus", "bridge"}`, the single section with novelty at least `BRIDGE_NOVEL_CHORDS`, not first or last, with vocal share at least 0.5 (from `bar_vocal_db` flags; when `bar_vocal_db` is empty the vocal test is skipped) becomes `bridge`; every other `bridge` becomes `verse`; `intro`, `instrumental`, `outro` and any other label pass through unchanged. `build_score` uses the refined label for `ScoreSection.label`; `grid.json` is unchanged.
- Produces, in `html.py`: `display_names(labels: Sequence[str]) -> list[str]`: `Verse 1`, `Verse 2`, `Chorus`, `Instrumental 1`, `Bridge`, `Outro`; a label occurring once has no number; capitalised. Used for section headings and the "Strum as in" reference.

- [ ] **Step 1: Write the failing tests**

```python
def test_section_novelty_counts_triads_unique_to_a_section(): ...
def test_refine_labels_names_the_one_novel_middle_vocal_section_bridge(): ...   # S69-shaped: novelty 0.73 -> bridge; others 0.0 unchanged
def test_refine_labels_turns_non_novel_bridge_into_verse(): ...                 # Wet Leg-shaped
def test_refine_labels_passes_through_intro_instrumental_outro_and_hand_labels(): ...
def test_refine_labels_at_most_one_bridge(): ...
def test_label_sections_no_cluster_numbering(): ...                             # sections.py: no "verse 2", no "bridge 2"
def test_score_uses_refined_labels(): ...
def test_display_names_number_by_occurrence(): ...                              # ["verse","chorus","verse","bridge"] -> ["Verse 1","Chorus","Verse 2","Bridge"]
def test_html_headings_and_strum_as_in_use_display_names(): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green.**
- [ ] **Step 4: Check on the real runs**: `section_novelty` on the five runs gives 0.73 for S69 bars 58-69 and at most 0.05 elsewhere (Fame all 0.00). Record in the report.
- [ ] **Step 5: Commit** `feat: bridge by chord novelty; section names numbered by occurrence`.

---

### Task 5: No-capo line, capo notes, outro without an instrument, strip on struck bars

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/music/score_builder.py` (`Score.alternative_diagrams`), `src/youkelele/schemas.py` (`Score.alternative_diagrams: list[ChordDiagram] = []`), `src/youkelele/render/html.py`, `src/youkelele/render/templates/sheet.html.j2:83-85`, `src/youkelele/stages/arrange.py:56-88` (notes `capo_margin`, `capo_scores`), `src/youkelele/music/arrange.py:49-51` (`capo_scores(labels, db, max_capo) -> list[float]`), `src/youkelele/stages/strums.py` (trimmed all-N outro), `src/youkelele/render/strum_box.py` (`example_bars` prefers struck bars)
- Test: `tests/test_arrange.py`, `tests/test_stage_arrange.py`, `tests/test_score_builder.py`, `tests/test_html.py`, `tests/test_stage_strums.py`, `tests/test_strum_box.py`

**Interfaces:**
- Produces: `capo_scores(labels, db, max_capo=5) -> list[float]` (the per-capo scores `choose_capo` minimises); arrange notes `capo_margin` (runner-up score minus chosen) and `capo_scores` (comma-joined). `build_score` fills `Score.alternative_diagrams` from `arrangement.no_capo_alternative` with the diagram dedupe used for `chord_diagrams`, only when `capo > 0`. Render: `Without a capo: C# 1114 (barre), F# 3124, ...` under the `Passing:` line using `fret_notation`, `(barre)` when `shape.barres` is non-empty, G C E A order. Strums stage: when the trailing drop leaves the last section with every analysed bar `N` in `chords` and no detected strike in its bars, the pattern is `no_instrument=True` (no inheritance). `example_bars(section, bar_onsets=None)`: when `bar_onsets` is given, the first two full bars with at least one struck slot; the substitution rule unchanged; fallback to today's choice when no bar is struck. `render_html` passes the section's `bar_onsets` slice (the score carries `bar_onsets`? No: `Score` does not; `ScoreBar` gains `struck: bool = False` set by `build_score` from `strums.bar_onsets[bar.index]`, and `example_bars` reads `bar.struck`).

- [ ] **Step 1: Write the failing tests**

```python
def test_capo_scores_and_margin_note(tmp_path): ...
def test_score_alternative_diagrams_only_under_capo(): ...
def test_html_no_capo_line_in_fret_notation_with_barre_marks(): ...      # "Without a capo: C# 1114 (barre), F# 3124"
def test_trimmed_all_n_outro_is_no_instrument(tmp_path): ...             # Wet Leg-shaped: last section one N bar, no strikes -> no_instrument, not inherited
def test_score_bar_struck_flag_from_bar_onsets(): ...
def test_example_bars_skip_unstruck_leading_bars(): ...                  # Chelsea-shaped: bars 9, 10 unstruck -> example starts at the first struck bar
def test_example_bars_fallback_when_no_bar_struck(): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_render.py`.**
- [ ] **Step 4: Commit** `feat: no-capo line, capo margin notes, outro without an instrument, strip on struck bars`.

---

### Task 6: Run folders named after the song

**Confidence:** 92% (the metadata fetch is the same extractor as the download, verified on both new ids; collision and lookup logic is deterministic)

**Files:**
- Modify: `src/youkelele/layout.py:14-23` (`slug_for` stays for local files and the id fallback; add `title_slug(title: str) -> str`), `src/youkelele/models/ytdl.py` (add `fetch_metadata(url) -> dict` with `skip_download`), `src/youkelele/commands.py:48-75` (`run_command` resolves the folder; `status`, `evaluate` accept folder name or id), `src/youkelele/manifest.py:25-31` (`Manifest.video_id: str | None = None`, `Manifest.title_slug: str | None = None`), `src/youkelele/runner.py` (write the two fields), `src/youkelele/preflight.py` (metadata failure as a Problem), `src/youkelele/titles.py:43-50` (wider artist prefix), `src/youkelele/stages/ingest.py:46-49` (reuse the fetched metadata when present)
- Test: `tests/test_layout.py`, `tests/test_titles.py`, `tests/test_cli.py`, `tests/test_cli_integration.py`, `tests/test_runner.py`

**Interfaces:**
- Produces: `title_slug(title) -> str` (lowercase, NFKD-fold to ASCII, non-alphanumerics to single hyphens, trimmed; empty string when nothing remains); `resolve_run_dir(runs_dir: Path, source: str, fetch=fetch_metadata) -> tuple[Path, dict | None]`: (1) scan `runs_dir/*/manifest.json` for `source == source` (or `video_id` equal to the URL's id) and return that folder; (2) for a local file, `slug_for(source)`; (3) otherwise `fetch(source)` and `title_slug(clean_title(title, uploader))` or the id when empty; (4) if that folder exists with a different `source`, append `-2`, `-3`; returns the metadata dict so ingest can reuse `title` and `uploader` without a second fetch. `fetch_metadata(url) -> dict` returns `{"id", "title", "uploader", "artist", "duration"}` via `yt_dlp.YoutubeDL({"skip_download": True, "quiet": True}).extract_info(url, download=False)`; failures raise `MetadataError(url, cause)`, which `run_command` turns into a preflight-style `Problem("could not read the video's details: <cause>", "check the link and your connection")` and exit code 2. `status` and `evaluate` take `<slug>` as the folder name; when no such folder exists, they look for a folder whose manifest `video_id` matches. `_strip_artist_prefix(title, artist)` keeps the equality rule and adds: a leading `X - ` (en dash or colon too) is stripped and `X` returned as the artist when `X` has at most four words and shares a word of at least three letters with the artist field, case-insensitively; `clean_title` returns the cleaned title and `clean_artist_from(title, artist)` the chosen artist. Ingest stores `title_slug`-independent `title`/`artist` as today, from the reused metadata.

- [ ] **Step 1: Write the failing tests**

```python
def test_title_slug_rules(): ...                                      # "Summer Of '69" -> "summer-of-69"; "mangetout"; "Déjà Vu" -> "deja-vu"; "" for a non-Latin title
def test_resolve_run_dir_finds_existing_folder_by_source_without_network(tmp_path): ...   # old id-named folder with manifest.source -> returned, fetch not called
def test_resolve_run_dir_names_new_folder_from_metadata(tmp_path): ...
def test_resolve_run_dir_collision_gets_suffix(tmp_path): ...         # Review Focus 3
def test_resolve_run_dir_local_file_uses_stem(tmp_path): ...
def test_wider_artist_prefix_rule(): ...                              # ("Pat Benatar - All Fired Up (Official Music Video)", "Benatar Giraldo") -> ("All Fired Up", "Pat Benatar"); the five known titles unchanged
def test_run_command_reports_metadata_failure_as_problem(monkeypatch): ...
def test_status_and_evaluate_accept_folder_name_or_id(tmp_path): ...
def test_manifest_records_video_id_and_title_slug(tmp_path): ...
def test_manifest_without_new_fields_loads(): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_end_to_end.py` (local clip still lands in `runs/clip`).**
- [ ] **Step 4: Commit** `feat: run folders named after the song; metadata fetch before the chain; wider artist-prefix rule`.

---

### Task 7: Setup without git, install and run scripts, licence

**Confidence:** 92% (the zip and its checkpoint hashes are verified, spec 9 A7; uv's managed Python verified, A8; the SmartScreen prompt is unverified, A9, and is handled by the README and tested from a browser download in Task 9)

**Files:**
- Create: `install.cmd`, `install.ps1`, `run-youkelele.cmd`, `install.sh`, `run-youkelele.sh`, `LICENSE`
- Modify: `src/youkelele/vendoring.py:82-99,117-160` (`_fetch_archive` replaces `_clone`; `_check_commit` reads a `COMMIT` marker file the fetch writes, or accepts an existing clone whose `git rev-parse` matches when git is present), `pyproject.toml` (`license = "MIT"`), `src/youkelele/preflight.py` (no git check)
- Test: `tests/test_vendoring.py`

**Interfaces:**
- Produces, in `vendoring.py`: `CHORD_MODEL_ARCHIVE = f"{CHORD_MODEL_REPO}/archive/{CHORD_MODEL_COMMIT}.zip"`; `_fetch_archive(root, log, opener=urllib.request.urlopen)`: downloads to `root.with_name(root.name + ".partial.zip")`, extracts the single top-level folder into `root.with_name(root.name + ".partial")`, writes `COMMIT` containing `CHORD_MODEL_COMMIT`, renames into place, removes the zip; `_check_commit(root)`: `COMMIT` file content, else `git rev-parse HEAD` when a `.git` folder exists and git is available, else a `VendoringError` telling the user to delete the folder and run setup; `ensure_chord_model` never requires git; `verify_checkpoints` unchanged (the archive's checkpoints hash identically to the clone's).
- Scripts: `install.cmd` = `@powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"` then `pause`. `install.ps1`: steps printed as `[1/4] Installing uv`, each skipped with `already present` when found; uv via `irm https://astral.sh/uv/install.ps1 | iex` then `$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"`; `uv sync`, `uv run youkelele setup`, `uv run playwright install chromium`; on any failure print the step, the last 20 lines, and `Send the text above to the person who gave you this tool`, exit 1; on success print `Ready. Double-click run-youkelele.cmd to make a sheet.` `run-youkelele.cmd`: if a file was dropped on it use `%~1`, else `set /p` for the link; `uv run youkelele run "<input>" --runs-dir "%~dp0runs"`; on success find the newest `runs\*\07_render\sheet.pdf` and `start "" "<pdf>"`; on failure keep the window open. `install.sh` and `run-youkelele.sh` mirror them with the uv shell installer and `xdg-open`/`open`.
- `LICENSE`: MIT text with the owner's name and 2026.

- [ ] **Step 1: Write the failing tests**

```python
def test_ensure_chord_model_fetches_archive_without_git(tmp_path, monkeypatch): ...   # fake opener serves a zip with chord_recognition.py and the checkpoint files; no subprocess called
def test_check_commit_reads_marker_file(tmp_path): ...
def test_existing_clone_without_marker_is_accepted_when_git_matches(tmp_path): ...
def test_partial_download_never_looks_complete(tmp_path): ...
def test_install_scripts_exist_and_reference_each_other(): ...                        # install.cmd calls install.ps1; run script calls youkelele run
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_vendoring.py` if a slow test exists.**
- [ ] **Step 4: Script check in a fresh folder** (outside the repository, under `%TEMP%`): copy the repository as a ZIP export (`git archive` is fine here), unpack, run `install.cmd` twice (Review Focus 4: the second run installs nothing and ends with Ready), then `run-youkelele.cmd` with the end-to-end test clip's path dropped on it; the PDF opens. Record the output in the report.
- [ ] **Step 5: Commit** `feat: setup without git; install and run scripts; MIT licence`.

---

### Task 8: README for a visitor

**Confidence:** 93% (content is fixed by spec 5; the sample image is rendered from the project's own test score; the licences of vendored components are checked from their sources during the task)

**Files:**
- Create: `docs/images/sample-sheet.png`
- Modify: `README.md`, `docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-3-design.md` (one-line pointer to 1.4 at the top)
- Test: `tests/test_readme.py` (new: every ``` command block that starts with `uv run youkelele` names a real subcommand and flag; the image path exists)

**Interfaces:**
- The README follows spec 5's twelve sections in order. The sample image is page 1 of the sheet rendered from `tests/test_stage_render.py::_realistic_120_bar_score` (through `render_html`, the PDF function and PyMuPDF at 110 dpi), committed as `docs/images/sample-sheet.png` (under 600 KB). The licence section names: this project MIT; the Chord-CNN-LSTM model (read its `LICENSE` in the model folder and quote the licence name); chords-db (MIT, from its repository); Demucs weights (read the licence note in `audio-separator` or the Demucs repository); Beat This! checkpoints (its repository); static-ffmpeg and ffmpeg (LGPL/GPL build as stated by the package). Anything non-commercial or unclear is said to be so.

- [ ] **Step 1: Write the failing test** (`tests/test_readme.py`: image exists; command blocks name real subcommands).
- [ ] **Step 2: Run it to verify it fails** (no image yet).
- [ ] **Step 3: Render the sample image; write the README per spec 5 (non-coder steps first after the image, with the SmartScreen "More info, Run anyway" note); add the 1.3 spec pointer; tests green; full fast suite green.**
- [ ] **Step 4: Commit** `docs: README for a visitor with a sample sheet and non-coder instructions`.

---

### Task 9: Validation on seven songs, non-coder path, version 0.5.0

**Confidence:** 93% (the chain completes on the five known songs; the two blind songs and the non-coder path are the uncertainty, and the task records whatever happens)

**Files:**
- Create: `docs/superpowers/specs/2026-10-04-v1-4-validation.md`
- Modify: `README.md` (Known limitations: only what is still true; download sizes measured), `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock` (version 0.5.0)

- [ ] **Step 1: Baselines**: copy `02_grid` to `07_render` and `manifest.json` of the five 1.3 run folders to the session scratchpad `v1_3_baseline\<slug>\` with each `evaluate` output.
- [ ] **Step 2: Version 0.5.0, `uv sync`.**
- [ ] **Step 3: Run the seven songs** with `uv run youkelele run "<url>" --runs-dir C:\Users\gethi\sources\Youkelele\runs`, one at a time; each lands in its title-named folder (`summer-of-69`, `chelsea-dagger`, `pour-some-sugar-on-me`, `mangetout`, `fame`, `all-fired-up`, `need-you-tonight`); record first-run download sizes from the logs for the README.
- [ ] **Step 4: Compare** each of the five with its baseline through `compare_runs` (Python API), `evaluate` each of the seven, rasterise every page and look at it.
- [ ] **Step 5: Non-coder path**: download the repository ZIP in a browser from GitHub (the branch), unpack outside the repository, double-click `install.cmd` (record whether SmartScreen appears and what the README says to do), then `run-youkelele.cmd` with one validation URL; the sheet opens. Record the exact steps and what appeared.
- [ ] **Step 6: Write `2026-10-04-v1-4-validation.md`** against spec 7: a summary table (song, folder, key with method and margin, hedged or not, sections and labels, power chords, pages 1.3 to 1.4, verdict); per song yes or no per expectation with evidence; what cannot be verified without listening; both tonic rules' results for the blind songs; the non-coder path record; a ranked "What to improve next". No lyrics.
- [ ] **Step 7: README Known limitations and download sizes; `uv run pytest -q -W error -m "not slow"` and `uv run pytest -q -m slow` green.**
- [ ] **Step 8: Commit** `docs: validate version 1.4 on seven real songs and the non-coder path; bump to 0.5.0`.

---

## Self-review notes

- **Spec coverage.** 3.1 key: Task 1. 3.2 power chords: Task 2. 3.3 vocal sections: Task 3. 3.4 bridge and numbering: Task 4. 3.5 outro: Task 5. 3.6 folders and prefix rule: Task 6. 3.7 install and no-git setup: Task 7. 4 sheet (hedge Task 1, badge Task 2, names Task 4, no-capo line and strip Task 5). 5 README and licence: Tasks 7 and 8. 6 data formats: Tasks 1 to 6. 7 validation: Task 9. 9 assumptions: A1 to A5 confirmed in Tasks 1, 3, 4 Step 4; A7 and A8 in Task 7; A9 and A10 in Task 9; A6 and A14 by the blind songs in Task 9; A11 to A13 by tests and the validation.
- **Rulings taken while planning:** `ScoreBar.struck` carries the strike information into the renderer so `example_bars` stays pure; `to_triad` keeps `X:5` unchanged and the stage writes the triad, so nothing downstream guesses; `Score.key_hedge` holds the runner-up name so the renderer needs no key logic; `_check_commit` accepts an existing clone when git is present so today's installs keep working; `status` and `evaluate` fall back to the video id so old folders stay addressable; the metadata dict from `resolve_run_dir` is handed to ingest so the title is fetched once.
- **Type consistency checked:** `HarmonicChroma` (Task 1) feeds `key_from_chords` and `power_chord_events` (Task 2); `Key.mode_margin` (Task 1) is read by Task 2's gate; `Grid.bar_vocal_db` (Task 3) is read by `refine_labels` (Task 4); `display_names` (Task 4) is used for headings and "Strum as in" (Task 5 keeps the strums side unchanged); `title_slug` and `resolve_run_dir` (Task 6) are used by `run-youkelele.cmd` only through the CLI (Task 7); `fret_notation` (1.2) formats the no-capo line (Task 5).
- **Review Focus:** 1 in Task 1, 2 in Task 3, 3 in Task 6, 4 in Task 7, 5 in Task 2.
- **Proportion:** about three times the spec's length, carried by interface blocks and test names; no function bodies.
