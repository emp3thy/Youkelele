# Ukulele Tab Chain 1.7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The sheet stops drawing sustain lines, prints an empty black stroke row on bars where the guitar is silent or out of register, labels a riff member buried in a merged section, and flags two more riffs by lowering the pitch-change floor; everything the ear passed in 1.6 prints as before.

**Architecture:** A new `music/rests.py` measures each bar's stem-to-mix energy ratio and its STFT power share below 330 Hz; the strums stage applies the rule per member before the vote, so resting bars never enter the vote, the chance test, the ring measurement or the riff features, and writes the figures and a `rests` flag on each `BarStrums`. The riff test keeps its chroma gate and lowers `PITCH_CHANGE_MIN` to 0.26; the stage also writes `root_share` and `named_share` for the next version's measurement. The score builder carries `rests` and a per-bar `label`; the renderer drops every sustain line and draws the label in the chord row. Schemas stay at version 2 with defaulted fields; 1.6 files load and render.

**Tech Stack:** Python 3.12 via uv, pydantic 2, numpy, librosa (`stft`, `resample`, `pyin`), Jinja2 and inline SVG, Playwright Chromium PDF, pytest.

**Spec:** `docs/superpowers/specs/2026-10-06-ukulele-tab-chain-v1-7-design.md` (cited as "spec N"). Research under `docs/superpowers/research/2026-10-06-v1-7/` (`strokes.md`, `riff-test.md`, `two-part-split.md`, `rests.md`, `acdc-ear-truth.md`, `assumption-clips.md`). The 1.6 plan at `docs/superpowers/plans/2026-10-05-ukulele-tab-chain-v1-6.md` names the interfaces this plan extends.

## Global Constraints

- Schema version 2 stays for `strums.json` and `score.json`; every new field has a default, so every 1.3 to 1.6 artifact loads, and a 1.6 `score.json` renders without sustain lines and without labels (spec 7, A11).
- Nothing reads a song's title, id, duration or any other identity; every rule applies to any input; unit tests use synthetic inputs or measured numbers as examples of a rule (1.6 spec 1, Generality).
- `grid.json`, the chord events and `bar_onsets` are byte-identical to 1.6 on every re-run song (spec 6, 8): nothing in `music/onsets.py`, `music/recall.py`, `music/relabel.py`, `music/vote.py`, `music/members.py`, `music/ring.py`, the chroma features in `music/riff.py`, the riff gate, or the grid and harmony stages changes. `bar_onsets` is still written from every bar, resting ones included.
- Constants, verbatim from the spec: `REST_RATIO_MIN = 0.05`; `REST_LOW_SHARE_MIN = 0.005`; low band below 330 Hz; STFT `n_fft 2048`, `hop_length 512` on the stem resampled to 22 050 Hz; `PITCH_CHANGE_MIN = 0.26`; `RIFF_ENTROPY_MAX`, `RIFF_SINGLE_PC_MIN`, the vote constants, `MEMBER_AGREE`, `RING_SECTION_DB` and the gate constants unchanged.
- Header phrases unchanged (1.6 spec 3.2). Label text, verbatim (spec 3.2): "riff" when the member's tab printed, else "riff heard"; muted grey, chord-name size, first bar of the member only.
- README lines, verbatim (spec 6): "Quiet strokes and very fast runs can be missed, so a dense passage may print sparser than it is played." and "When two guitars share one stem, the printed strokes follow the higher one, and their notes interleave, so the riff stage finds no steady line and prints the riff as heard, not transcribed."
- UK spelling; no em-dashes; no song lyrics in code, tests or documents; no time or effort estimates in documents.
- Package version 0.8.0 in `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock`; the ten manifests at 0.8.0 after validation.
- Run folders under `C:\Users\gethi\sources\Youkulele\runs\` are touched only by Task 9.
- Work happens in a worktree cut from main HEAD at `C:\Users\gethi\sources\Youkulele\.claude\worktrees\v1-7` on branch `worktree-v1-7`; the spec and this plan live on main and are amended there. Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. The shell guard refuses compound bash containing git: plain separate git commands only. Write files with the Write tool, not Bash heredocs.

## Review Focus

1. A bar shorter than one STFT frame (a fast song's pickup bar, under 2 048 samples at 22 050 Hz): `bar_low_share` must still return a number, not raise or return NaN, and the bar must not rest on that account. Test in Task 2.
2. A member whose first bars rest and whose vote is a two-bar pattern: the printed cells must alternate from the first holding bar, so bar parity does not flip when the vote skips resting bars. Test in Task 4.
3. A member every bar of which rests inside a section whose `section_has_instrument` passed: it is silent, prints all rest, and the section header reads "no strummed instrument detected" only when that member is the longest. Test in Task 4.
4. A riff member that is also the longest member: its header already says riff, so no label prints; and a riff member in a merged section whose longest member is uncertain: the label prints and the header stays "pattern uncertain". Test in Task 5.
5. A 1.5 `score.json` (no per-bar strokes, no `rests`, no `label`) and a 1.6 one (strokes with `rings` flags): both render, no `class="sustain"` anywhere, no label, and the 1.5 derived strokes still appear. Tests in Tasks 5 and 6.

---

### Task 1: Schema fields for rests, the riff rule and the bar label

**Confidence:** 96%. Additive defaulted fields; the loader behaviour is the same mechanism 1.6 relied on.

**Files:**
- Modify: `src/youkelele/schemas.py` (`BarStrums`, `SectionPattern`, `ScoreBar`)
- Test: `tests/test_schemas.py`
- Fixtures: copy `runs\need-you-tonight\04_strums\strums.json` to `tests/fixtures/v16_strums.json` and `runs\need-you-tonight\07_score\score.json` to `tests/fixtures/v16_score.json` (a 1.6 song with tab and a riff member; keep every existing fixture).

**Interfaces:**
- Produces:
  - `BarStrums` gains `rests: bool = False`, `energy_ratio: float | None = None`, `low_share: float | None = None`
  - `SectionPattern` gains `root_share: float | None = None`, `named_share: float | None = None`, `riff_rule: Literal["A", "B"] | None = None`
  - `ScoreBar` gains `label: str = ""`, `rests: bool = False`
- Comments on each field in the style of the existing ones (what it means, "None before 1.7" where that holds).

- [ ] **Step 1: Write the failing tests**

```python
def test_v16_strums_and_score_load_with_1_7_defaults():
    strums = load_model(FIXTURES / "v16_strums.json", Strums)
    assert all(not b.rests and b.energy_ratio is None and b.low_share is None for b in strums.bars)
    assert all(p.root_share is None and p.named_share is None and p.riff_rule is None for p in strums.patterns)
    score = load_model(FIXTURES / "v16_score.json", Score)
    assert all(b.label == "" and not b.rests for s in score.sections for b in s.bars)

def test_1_7_fields_round_trip():
    bar = BarStrums(index=0, member=0, strokes=[], pattern=["-"] * 8, rests=True, energy_ratio=0.01, low_share=0.0002)
    assert BarStrums.model_validate_json(bar.model_dump_json()).rests
    pattern = SectionPattern(section=0, slots=["-"] * 8, confidence=0, bar_repeat=0, uncertain=True,
                             no_instrument=False, inherited_from=None, root_share=0.9, named_share=0.5, riff_rule="A")
    assert SectionPattern.model_validate_json(pattern.model_dump_json()).riff_rule == "A"
    assert ScoreBar(index=0, chords=[], label="riff heard", rests=False).label == "riff heard"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schemas.py -k "v16 or 1_7" -v`
Expected: FAIL (missing fixture, then unexpected keyword `rests`)

- [ ] **Step 3: Copy the fixtures and add the fields**

- [ ] **Step 4: Run the whole fast suite**

Run: `uv run pytest -q -m "not slow"`
Expected: all pass (829 before this task)

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/schemas.py tests/test_schemas.py tests/fixtures/v16_strums.json tests/fixtures/v16_score.json
git commit -m "feat(schemas): rests, energy ratio and low share per bar; root share, named share and riff rule per section; bar label"
```

---

### Task 2: The rest rule in `music/rests.py`

**Confidence:** 93%. The two measurements are the spike's exact calls (`rests.md`: `rms_ratio` at the native rate per bar; `librosa.stft(n_fft=2048, hop_length=512)` on the bar's slice of the stem resampled to 22 050 Hz; power share of bins under 330 Hz) and the thresholds are the spec's. The one case the spike skipped, a bar shorter than one frame, is decided below.

**Files:**
- Create: `src/youkelele/music/rests.py`
- Test: `tests/test_rests.py`

**Interfaces:**
- Consumes: `rms_ratio(part, mix) -> float` from `music/onsets.py`; `Bar` (`start`, `end` in seconds) from `schemas.py`.
- Produces, in `music/rests.py`:
  - `REST_RATIO_MIN = 0.05`, `REST_LOW_SHARE_MIN = 0.005`, `REST_LOW_HZ = 330`, `REST_SR = 22050`, `_N_FFT = 2048`, `_HOP = 512`, each with a one-line comment giving the band from `rests.md` (ratio pinned at 0.069 to 0.09 from below; low share band 0.001 to 0.04).
  - `bar_energy_ratio(stem: np.ndarray, mix: np.ndarray, sr: int, bar: Bar) -> float`: `rms_ratio` over the bar's samples at the native rate.
  - `bar_low_share(stem_22k: np.ndarray, bar: Bar) -> float`: the bar's slice of the 22 050 Hz stem; `np.abs(librosa.stft(seg, n_fft=2048, hop_length=512)) ** 2`; sum of the rows whose centre frequency (`librosa.fft_frequencies`) is below 330 Hz over the total plus `1e-12`. A slice shorter than `_N_FFT` is zero-padded to `_N_FFT` first (decision: the spike left such bars unmeasured; padding keeps the share defined and leaves a silent short bar at 0). An all-zero slice returns 0.0.
  - `bar_holds(energy_ratio: float, low_share: float) -> bool`: `energy_ratio >= REST_RATIO_MIN and low_share >= REST_LOW_SHARE_MIN`.
  - `resample_for_rests(stem: np.ndarray, sr: int) -> np.ndarray`: `librosa.resample` to `REST_SR` (identity when `sr == REST_SR`), so the stage resamples once.

- [ ] **Step 1: Write the failing tests** (pure tones and silence; `sr = 22050` so the ratio and the share read the same array)

```python
def test_a_silent_bar_rests_by_ratio():            # stem zeros, mix a 220 Hz tone
    assert bar_energy_ratio(zeros, mix, SR, BAR) == 0.0 and not bar_holds(0.0, 0.5)

def test_a_low_tone_bar_holds():                   # stem = mix = 110 Hz tone at amplitude 0.3
    assert bar_energy_ratio(tone, tone, SR, BAR) == pytest.approx(1.0)
    assert bar_low_share(tone, BAR) > 0.9 and bar_holds(1.0, bar_low_share(tone, BAR))

def test_a_loud_bell_bar_rests_by_register():      # 2 kHz tone, full level: ratio 1.0, low share tiny
    share = bar_low_share(bell, BAR)
    assert share < REST_LOW_SHARE_MIN and not bar_holds(1.0, share)

def test_thresholds_are_inclusive():
    assert bar_holds(0.05, 0.005) and not bar_holds(0.0499, 0.005) and not bar_holds(0.05, 0.0049)

def test_a_bar_shorter_than_a_frame_still_measures():   # a 60 ms bar of 110 Hz tone (1 323 samples)
    assert bar_low_share(short_tone, SHORT_BAR) > 0.5
    assert bar_low_share(np.zeros(2048), SHORT_BAR) == 0.0

def test_resample_is_identity_at_22050_and_changes_length_otherwise():
    assert resample_for_rests(tone, 22050) is tone
    assert len(resample_for_rests(np.zeros(44100), 44100)) == 22050
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_rests.py -v`
Expected: FAIL with `ModuleNotFoundError: youkelele.music.rests`

- [ ] **Step 3: Implement `music/rests.py` as the Interfaces block specifies**

Module docstring: the rule, its two measurements, the bands, and a pointer to `rests.md`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_rests.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/rests.py tests/test_rests.py
git commit -m "feat(rests): per-bar energy ratio and low-band share with the rest rule"
```

---

### Task 3: The lower pitch-change floor, `root_share` and `named_share`

**Confidence:** 94%. The constant is the spec's; the two shares are the spike's definitions (`riff-test.md`: root = share of named pitches whose pitch class is the chord root at the onset; named = share of onsets named). The chord-root lookup reuses `music/key.py`'s pitch-class table.

**Files:**
- Modify: `src/youkelele/music/pitch.py:22` (`PITCH_CHANGE_MIN = 0.26`, comment with the band 0.24 to 0.29 and the two sides from A1)
- Modify: `src/youkelele/music/riff.py` (add `root_share`, `named_share`)
- Modify: `src/youkelele/music/key.py:112` (rename `_pitch_class` to `pitch_class`, keep `_pitch_class = pitch_class` for the module's own callers)
- Test: `tests/test_pitch.py`, `tests/test_riff.py`

**Interfaces:**
- Consumes: `name_notes(track, onsets, ends) -> list[int | None]`, `pitch_change_share(notes) -> float | None` from `music/pitch.py`; `ChordEvent` (`start`, `end`, `label` such as `"C:maj"`, `"F#:min"`, `"N"`) from `schemas.py`; `pitch_class(name: str) -> int` from `music/key.py`.
- Produces, in `music/riff.py`:
  - `chord_roots(events: Sequence[ChordEvent], times: Sequence[float]) -> list[int | None]`: for each onset time, the pitch class of the root of the chord event containing it (`label.split(":")[0]` through `pitch_class`), `None` for `"N"` or no event.
  - `root_share(notes: Sequence[int | None], roots: Sequence[int | None]) -> float | None`: over pairs where both are present, the share with `note % 12 == root`; `None` when no pair.
  - `named_share(notes: Sequence[int | None]) -> float | None`: share of entries not `None`; `None` for an empty list.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pitch.py
def test_pitch_change_floor_is_0_26():
    assert PITCH_CHANGE_MIN == 0.26

# tests/test_riff.py
def test_chord_roots_follow_the_event_under_each_onset():
    events = [_event(0.0, 2.0, "C:maj"), _event(2.0, 4.0, "N"), _event(4.0, 6.0, "F#:min")]
    assert chord_roots(events, [0.5, 2.5, 4.5, 9.0]) == [0, None, 6, None]

def test_root_share_counts_named_pairs_only():
    assert root_share([60, 62, None, 67], [0, 0, 0, None]) == 0.5
    assert root_share([None], [0]) is None

def test_named_share():
    assert named_share([60, None, 64, None]) == 0.5 and named_share([]) is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_pitch.py::test_pitch_change_floor_is_0_26 tests/test_riff.py -k "roots or share" -v`
Expected: FAIL (0.4 != 0.26; names not defined)

- [ ] **Step 3: Make the changes as the Interfaces block specifies**

- [ ] **Step 4: Run the fast suite**

Run: `uv run pytest -q -m "not slow"`
Expected: PASS. If an existing strums-stage test pinned a pitch-change share between 0.26 and 0.4 as "not a riff", change its synthetic share, not the constant, and say so in the report.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/pitch.py src/youkelele/music/riff.py src/youkelele/music/key.py tests/test_pitch.py tests/test_riff.py
git commit -m "feat(riff): pitch-change floor 0.26; root share and named share for the next measurement"
```

---

### Task 4: The strums stage applies the rest rule, writes the new figures

**Confidence:** 90%. Every rule it applies is tested in Tasks 2 and 3 and the vote is untouched; the open choices (which bars index a two-bar pattern after rests, what a resting record carries, which members are named) are decided below and pinned by tests. The remaining tenth is the interaction with trailing-bar trimming and the recall gate, which the existing stage tests guard.

**Files:**
- Modify: `src/youkelele/stages/strums.py` (`_Member`, `_vote_member`, `_ring_member`, `_riff_inside`, `_riff_test`, `_align_member`, `_section_pattern`, `_bar_records`, `StrumsStage.run`)
- Test: `tests/test_stage_strums.py`

**Interfaces:**
- Consumes: Task 2's `resample_for_rests`, `bar_energy_ratio`, `bar_low_share`, `bar_holds`; Task 3's `chord_roots`, `root_share`, `named_share`, `PITCH_CHANGE_MIN`; Task 1's fields.
- Produces: `strums.json` whose `bars[i]` carry `rests`, `energy_ratio`, `low_share`, and whose `patterns[k]` carry `root_share`, `named_share`, `riff_rule`. No signature outside the stage changes.
- Decisions this task fixes (amend into spec 5 and 7 when the task is accepted):
  - **Holding bars.** `_Member` gains `holding: list[int]` (bar indices in `[start, analysed_end)` that hold, in order) and `first_holding: int | None`. `run` measures `energy_ratio` and `low_share` for every bar once (`y` against `mix` at the native rate; `resample_for_rests(y, sr)` once for the share) and each member's `holding` is built from `bar_holds`. A member with an empty `holding` is `silent`.
  - **The vote reads holding bars only.** `_vote_member`, `_align_member` and `member_figures` read `[classes[b] for b in member.holding]`; `_ring_member` keeps only onsets whose bar is in `holding`; `_riff_inside` masks onsets to holding bars; the chance test's seed stays `member.start`.
  - **Two-bar phase.** A bar's cell index is `b - member.first_holding + offset` (not `b - member.start`), so the vote's phase, aligned to its first voted bar, lands on the first holding bar.
  - **A resting record** is `BarStrums(index=b, member=..., strokes=[], pattern=["-"] * slots, unit=1, confidence=0.0, chance_p=None, uncertain=False, riff=member.riff, rings=member.rings, rests=True, energy_ratio=..., low_share=...)`: nothing was guessed, so it is not uncertain (spec 3.3 prints it black). A holding record carries `rests=False` and its two figures.
  - **Naming for the shares.** The pitch tracker runs once whenever any member is voiced, and `name_notes` runs for every voiced member, so `root_share`, `named_share` and `pitch_change_share` are written for every section (the figures exist to measure the next version's rule on all sections, `riff-test.md`). The riff flag still requires the chroma gate (`is_riff`) and `pitch_change >= PITCH_CHANGE_MIN`; `riff_rule = "A"` when it is set, else `None`. `root_share` uses `chord_roots(chords.events, riff_times[idx])`.
  - `section_has_instrument` stays as the section-level first cut, exactly where it is.

- [ ] **Step 1: Write the failing tests** (extend the synthetic-song helpers already in `tests/test_stage_strums.py`; the stem is built per bar so a bar can be silent, a 2 kHz bell, or the normal strum signal)

```python
def test_silent_opening_bars_rest_and_leave_the_vote_to_the_bars_that_hold(tmp_path):
    # bars 0-1 zeros in the stem (mix unchanged), bars 2-7 the ISLAND strum
    s = _run_stage(tmp_path, stem_bars=[silent, silent] + [island] * 6)
    assert [b.rests for b in s.bars[:3]] == [True, True, False]
    assert s.bars[0].strokes == [] and s.bars[0].pattern == ["-"] * 8 and not s.bars[0].uncertain
    assert s.bars[0].energy_ratio == pytest.approx(0.0) and s.bars[2].energy_ratio > 0.05
    assert "".join(s.patterns[0].slots) == ISLAND_TEXT   # the vote is the six holding bars' vote
    assert s.bar_onsets[0] == ["-"] * 8                    # bar_onsets still written for every bar

def test_a_loud_high_register_bar_rests_but_keeps_its_bar_onsets(tmp_path):
    s = _run_stage(tmp_path, stem_bars=[bell_strikes] + [island] * 7)   # 2 kHz strikes on every eighth
    assert s.bars[0].rests and s.bars[0].low_share < 0.005 and s.bars[0].energy_ratio > 0.05
    assert any(c != "-" for c in s.bar_onsets[0])   # the detector saw the strikes; the record rests

def test_a_member_whose_bars_all_rest_is_silent(tmp_path):
    # two members (grid sections 0-3 and 4-7, merged by the plan); the second all zeros
    s = _run_stage(tmp_path, stem_bars=[island] * 4 + [silent] * 4, sections=two_members)
    assert all(b.rests and b.pattern == ["-"] * 8 for b in s.bars[4:])
    assert not s.patterns[0].no_instrument            # the longest member holds, so the header does not say no instrument

def test_two_bar_pattern_phase_starts_at_the_first_holding_bar(tmp_path):
    # bar 0 silent; bars 1-8 alternate A, B, A, B ... (a two-bar vote); the record on bar 1 must be A
    s = _run_stage(tmp_path, stem_bars=[silent] + [a, b] * 4)
    assert s.patterns[0].unit == 2 and s.bars[1].pattern == A_TEXT and s.bars[2].pattern == B_TEXT

def test_root_and_named_shares_are_written_for_a_strummed_section(tmp_path):
    s = _run_stage(tmp_path, stem_bars=[island] * 8)   # not a riff: chroma gate fails
    p = s.patterns[0]
    assert p.named_share is not None and p.root_share is not None and p.riff_rule is None and not p.riff

def test_a_riff_member_carries_rule_a(tmp_path):
    s = _run_stage(tmp_path, stem_bars=[riff_line] * 8)   # the existing single-note fixture whose share is 0.6
    assert s.patterns[0].riff and s.patterns[0].riff_rule == "A" and s.patterns[0].pitch_change_share >= 0.26
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stage_strums.py -k "rest or holding or shares or rule_a" -v`
Expected: FAIL (`rests` False everywhere; shares None)

- [ ] **Step 3: Implement the decisions above in `stages/strums.py`**

Log one line per member with resting bars: `  member {start}-{end}: {n} bars rest` and one stage note `rests` with the total count.

- [ ] **Step 4: Run the fast suite**

Run: `uv run pytest -q -m "not slow"`
Expected: PASS. Existing stage tests use full-level synthetic stems, so no bar of theirs rests; if one does, the stem in that test is quiet or high, and the report must say which and why before the test is changed.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/stages/strums.py tests/test_stage_strums.py
git commit -m "feat(strums): bars that rest leave the vote; root, named and rule figures per section"
```

---

### Task 5: The score builder carries rests and the riff-member label

**Confidence:** 93%. The mapping from the records to the score is one to one; the label rule is spec 3.2 word for word, with "the member's tab printed" read as a printable `RiffSection` whose span is the member's.

**Files:**
- Modify: `src/youkelele/music/score_builder.py` (`_bar_strokes`, `build_score`; new `_labels`)
- Modify: `src/youkelele/music/compat.py:26-50` (`backfill_bars` passes `rests=False` explicitly, so a 1.5 file's rebuilt records are complete)
- Test: `tests/test_score_builder.py`, `tests/test_compat.py`

**Interfaces:**
- Consumes: `BarStrums.rests`, `.member`, `.riff`; `Riffs.sections[*]` (`section`, `start_bar`, `end_bar`, `printable`); `member_spans(planned, grid)` from `music/members.py`; `_state` and the `STATE_*` phrases.
- Produces:
  - `ScoreBar.rests = record.rests`; a resting bar has `strokes=[]`, `grey=False`, `tab=None` (spec 7).
  - `_labels(k: int, planned: PlannedSection, grid: Grid, records: dict[int, BarStrums], riffs: Riffs, state: str) -> dict[int, str]`: bar index to label text. For each member span `(s, e)` of the planned section whose first record in `[s, e)` has `riff` True, when `state` does not start with `"riff"`: `"riff"` if any `RiffSection` has `section == k`, `(start_bar, end_bar) == (s, e)` and `printable`, else `"riff heard"`; keyed on `s`. Empty when the state starts with "riff".
  - `build_score` computes `state` before the bars' labels (it already needs the bars for `_state`; compute bars, then state, then set `label` on the bars `_labels` names).

- [ ] **Step 1: Write the failing tests** (the `_strums_with_runs` helper in `tests/test_score_builder.py` takes `(bars, pattern, member, rings, uncertain, riff)` runs; extend it with an optional `rests` flag)

```python
def test_a_resting_bar_prints_empty_strokes_in_black():
    score = _score(runs=[(2, ISLAND, 0, True, False, False, True), (6, ISLAND, 0, True, False, False)])
    bar = score.sections[0].bars[0]
    assert bar.rests and bar.strokes == [] and not bar.grey and bar.tab is None
    assert score.sections[0].bars[2].strokes and not score.sections[0].bars[2].rests

def test_an_embedded_riff_member_gets_one_label_on_its_first_bar():
    # merged section: member 0 bars 0-7 a strum (longest), member 1 bars 8-11 a riff that did not print
    score = _score(runs=[(8, ISLAND, 0, True, False, False), (4, RIFF_PATTERN, 1, True, False, True)], two_members=True)
    labels = [b.label for b in score.sections[0].bars]
    assert labels == [""] * 8 + ["riff heard", "", "", ""] and score.sections[0].state == ""

def test_a_printed_riff_member_makes_the_header_say_riff_so_no_label_prints():
    score = _score(runs=[(8, ISLAND, 0, True, False, False), (4, RIFF_PATTERN, 1, True, False, True)],
                   two_members=True, riffs=_riffs(section=0, start=8, end=12, printable=True))
    assert score.sections[0].state == "riff" and all(b.label == "" for b in score.sections[0].bars)

def test_labels_names_a_printed_member_riff_when_the_header_does_not():
    # the "riff" text is reachable only through _labels itself today (see the note below)
    assert _labels(0, planned, grid, records, _riffs(section=0, start=8, end=12, printable=True),
                   state="pattern uncertain") == {8: "riff"}

def test_no_label_when_the_header_already_says_riff():
    score = _score(runs=[(8, RIFF_PATTERN, 0, True, False, True)])   # the longest member is the riff
    assert score.sections[0].state == "riff heard, not transcribed" and all(b.label == "" for b in score.sections[0].bars)

def test_label_prints_under_an_uncertain_header():
    score = _score(runs=[(8, ISLAND, 0, True, True, False), (4, RIFF_PATTERN, 1, True, False, True)], two_members=True)
    assert score.sections[0].state == "pattern uncertain" and score.sections[0].bars[8].label == "riff heard"

# tests/test_compat.py
def test_backfilled_1_5_records_do_not_rest():
    assert all(not b.rests for b in backfill_bars(v15_strums, v15_grid))
```

Note: a printable riff on any member makes `_state` return "riff" (a tab bar exists in the section), so through `build_score` the `"riff"` label text is unreachable today; the branch stays because spec 3.2 names it, and the fourth test covers it on `_labels` directly.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_score_builder.py -k "rest or label" tests/test_compat.py -v`
Expected: FAIL (`rests` unexpected in the helper; labels empty)

- [ ] **Step 3: Implement `_labels`, set `rests` and `label` in `build_score`, pass `rests=False` in `backfill_bars`**

- [ ] **Step 4: Run the fast suite**

Run: `uv run pytest -q -m "not slow"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/score_builder.py src/youkelele/music/compat.py tests/test_score_builder.py tests/test_compat.py
git commit -m "feat(score): resting bars print empty; a riff member inside a merged section is labelled"
```

---

### Task 6: The renderer drops sustain lines and draws the label

**Confidence:** 93%. Deleting the sustain branches is mechanical; the label is one text element placed by the chord row's existing geometry. The one reading made here: the faint rest dots stay (spec 3 says the 1.6 box stands except the four points, and 3.1 is titled "No sustain lines"), and the tab block's note sustain lines go too (spec 7: `bar_svg` loses `rings` handling).

**Files:**
- Modify: `src/youkelele/render/bar_svg.py` (`_stroke_row`, `_tab_block`, `_chord_row`, `bar_svg` docstring, module docstring; delete `_held_until`)
- Modify: `src/youkelele/render/html.py:83-125` (docstrings only: `_derived_strokes` still sets `rings=True` for the schema, "all ringing" wording goes)
- Test: `tests/test_bar_svg.py`, `tests/test_html.py`, `tests/test_stage_render.py` (a 1.6 fixture renders)

**Interfaces:**
- Consumes: `ScoreBar.label`, `ScoreBar.rests`, `ScoreBar.strokes`, `ScoreBar.tab`.
- Produces:
  - `_stroke_row(bar, cols, top, ink)`: one arrow per stroke; a faint dot on every slot without a stroke; no `held` set, no `class="sustain"`.
  - `_tab_block(bar, cols, top, labels)`: fret numbers only; no line after a ringing note.
  - `_chord_row(chords, cols, power_badge, pickup, label: str = "")`: when `label` is non-empty, a `<text>` in `_GREY`, `_CHORD_FONT`, bold, `class="chord label"`, at the first name's x; the first chord name (or the N.C. mark) moves right by `_CHAR_PX * len(label) + 4` when the bar has a chord other than N.C., and is replaced by the label when every chord is N.C. The squeeze rule (`textLength`) reads the reduced room.
  - `bar_svg(...)` signature unchanged; it passes `bar.label` to `_chord_row`. The `grey` docstring loses "and sustain lines".

- [ ] **Step 1: Rewrite the failing tests**

In `tests/test_bar_svg.py`: `test_bar_svg_draws_chords_strokes_and_count` asserts `'class="sustain"' not in svg` and the arrow count; delete `test_sustain_runs_to_the_next_stroke_or_the_bar_end`; `test_short_strokes_draw_no_sustain_and_grey_bars_use_grey_ink` becomes `test_grey_bars_use_grey_ink`; `test_tab_notes_ring_on_their_string_and_an_empty_tab_still_draws_the_block` asserts no sustain and the block present. Add:

```python
def test_a_labelled_bar_prints_the_label_left_of_the_chord_in_grey():
    bar = ScoreBar(index=8, chords=[_chord("C", 0, 8)], strokes=_strokes(), label="riff heard")
    svg = bar_svg(bar, M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    label_x = float(re.search(r'<text x="([\d.]+)"[^>]*class="chord label">riff heard<', svg).group(1))
    chord_x = float(re.search(r'<text x="([\d.]+)"[^>]*class="chord">C<', svg).group(1))
    assert 'fill="#999" class="chord label"' in svg and chord_x > label_x + 8 * len("riff heard")

def test_a_labelled_bar_with_no_chord_prints_the_label_in_place_of_nc():
    bar = ScoreBar(index=8, chords=[_chord("N.C.", 0, 8)], strokes=[], label="riff")
    svg = bar_svg(bar, M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    assert ">riff<" in svg and ">N.C.<" not in svg

def test_a_resting_bar_draws_a_chord_and_an_empty_black_row():
    bar = ScoreBar(index=0, chords=[_chord("G", 0, 8)], strokes=[], rests=True)
    svg = bar_svg(bar, M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    assert 'class="arrow' not in svg and svg.count('class="rest"') == 8 and 'stroke="#999"' not in svg
```

In `tests/test_html.py:116`: assert `'class="sustain"' not in html`. In `tests/test_stage_render.py` add `test_a_1_6_score_renders_without_sustain_or_labels` on `tests/fixtures/v16_score.json`: HTML produced, no `class="sustain"`, no `class="chord label"`, arrows present.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_bar_svg.py tests/test_html.py tests/test_stage_render.py -v`
Expected: FAIL (sustain still drawn; no label element)

- [ ] **Step 3: Implement the changes in `bar_svg.py`; fix the docstrings in `html.py`**

- [ ] **Step 4: Run the fast suite and the slow render tests**

Run: `uv run pytest -q -m "not slow"` then `uv run pytest -q -m slow -k render`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/render/bar_svg.py src/youkelele/render/html.py tests/test_bar_svg.py tests/test_html.py tests/test_stage_render.py
git commit -m "feat(render): no sustain lines; a grey label in the chord row for an embedded riff member"
```

---

### Task 7: `evaluate` and the compare harness report rests and the riff rule

**Confidence:** 94%. Additive output over fields the earlier tasks define, in the existing report functions.

**Files:**
- Modify: `src/youkelele/evaluate.py` (`SectionDiag`, `Report`, `SectionDelta`, `_section_diags`, `_vote_figures`, `compare_runs`, `_delta`, `format_report`)
- Test: `tests/test_evaluate.py`

**Interfaces:**
- Consumes: `SectionPattern.riff_rule`, `.root_share`, `.named_share`; `BarStrums.rests`.
- Produces:
  - `SectionDiag` gains `riff_rule: str | None = None`, `root_share: float | None = None`, `named_share: float | None = None`, `resting_bars: list[int] = field(default_factory=list)` (bar indices in the section's planned span whose record rests).
  - `_vote_figures` appends `rule A` when the flag is set, then `root {:.2f}` and `named {:.2f}` (or `n/a`).
  - `Report` gains `resting_bars: list[int]` (whole run); `format_report` prints one line `N bars rest: 0-7, 84-85` as bar ranges after the section lines, or nothing when none rest.
  - `SectionDelta` gains `rest_changes: int` (bars in the paired span whose `rests` differs; grids that match only) and `riff_rule_b: str | None`; `_delta` prints ` rests changed in N bars` and, on `riff_changed`, ` (rule A)` from the right side's rule.
  - A helper `_ranges(indices: Sequence[int]) -> str` renders `0-7, 10, 11`.

- [ ] **Step 1: Write the failing tests** (build `Strums` objects in memory as the existing evaluate tests do)

```python
def test_report_lists_resting_bars_as_ranges():
    report = _report(strums=_strums(rests={0, 1, 2, 3, 10, 11}))
    assert report.resting_bars == [0, 1, 2, 3, 10, 11] and "6 bars rest: 0-3, 10, 11" in format_report(report)

def test_section_line_prints_the_rule_and_the_shares():
    line = _section_line(_diag(riff=True, riff_rule="A", root_share=0.25, named_share=0.6))
    assert "rule A" in line and "root 0.25" in line and "named 0.60" in line

def test_compare_counts_rest_changes_and_names_the_rule(tmp_path):
    c = compare_runs(_run(tmp_path / "a", rests=set()), _run(tmp_path / "b", rests={0, 1}, riff=True, rule="A"))
    assert c.deltas[0].rest_changes == 2 and "rests changed in 2 bars" in format_comparison(c) and "(rule A)" in format_comparison(c)

def test_ranges():
    assert _ranges([0, 1, 2, 3, 10, 11]) == "0-3, 10, 11" and _ranges([]) == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_evaluate.py -k "rest or rule or ranges" -v`
Expected: FAIL

- [ ] **Step 3: Implement the additions**

- [ ] **Step 4: Run the fast suite**

Run: `uv run pytest -q -m "not slow"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/evaluate.py tests/test_evaluate.py
git commit -m "feat(evaluate): resting bars, the riff rule and the named and root shares in reports and comparisons"
```

---

### Task 8: Version 0.8.0, README and the sample sheet

**Confidence:** 96%. Copy fixed by spec 6 and 7; the sample sheet is regenerated by the existing synthetic-song path.

**Files:**
- Modify: `pyproject.toml:3`, `src/youkelele/__init__.py:1`, `uv.lock:1804` (`0.8.0`)
- Modify: `README.md` (sample-sheet captions; stage table rows `04_strums`, `07_score`, `08_render`; Known limitations; Project history)
- Modify: `tests/test_readme.py:98`
- Regenerate: the sample sheet image the README's first section embeds, from the synthetic song, with the 1.7 renderer (find the image path in `README.md:7` and the script that made it in the 1.6 history; the caption "This sample was made with version 1.7").

**Interfaces:** none.

- [ ] **Step 1: Update the README test**

`tests/test_readme.py:98` asserts `"1.7" in text and "0.8.0" in text`, and add `assert "sparser than it is played" in text and "follow the higher one" in text`.

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_readme.py -v`
Expected: FAIL

- [ ] **Step 3: Make the edits**

- Captions: remove "with a line after a stroke that rings on through the next slots" (and any held-stroke wording); "This sample was made with version 1.7."
- `04_strums` row: add "; a bar whose stem is near silent or holds no power below 330 Hz rests and prints an empty stroke row"; `07_score` row: add "a label on the first bar of a riff member inside a merged section"; `08_render` row: remove the sustain-line wording.
- Known limitations: add the under-firing line verbatim; replace the two-guitar line with the spec's; add "A riff whose notes sound chord-like to the chain (chroma entropy above the ceiling) prints as a strum."; add "A bar rests when its stem is under 5 percent of the mix's level or holds almost no power below 330 Hz, so a loud passage played high on the neck can rest and print an empty row."
- Project history: `- 1.7 (package version 0.8.0): no sustain lines; bars where the guitar is silent or out of register print an empty stroke row; a riff member inside a merged section is labelled; the riff test's pitch-change floor lowered from 0.4 to 0.26; root and named shares recorded per section.`
- Version strings in the three files.

- [ ] **Step 4: Regenerate the sample sheet and run the suite**

Run: `uv run pytest -q -m "not slow"` and `uv run pytest -q -m slow`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/youkelele/__init__.py README.md tests/test_readme.py docs/
git commit -m "chore: version 0.8.0; README stage table, limitations, history and sample sheet for 1.7"
```

---

### Task 9: Validation on ten songs and one blind song, with published-source ground truth

**Confidence:** 91%. The expectations are spec 8's eight, written before the run; the sources step is new to this project but the three lesson sites were verified reachable while the spec was written. The blind song is unknown by design.

**Files:**
- Create: `docs/superpowers/specs/2026-10-06-v1-7-validation.md` (on main, mirroring `2026-10-05-v1-6-validation.md`: runs and baselines, expectations table, per-song figures, sources table, clips, assumptions A1 to A11 re-rated)
- Scratch (not committed): `%TEMP%\youkulele-v17-validation\` with `baseline\` (copies of each run's `04_strums` to `08_render`, `manifest.json`), `measure.py` (byte comparison of `grid.json`, the chord events, and `strums.json`'s `bar_onsets` against the baseline), `evaluate\`, `logs\`, `clips\`
- Touches: `runs\` (the only task that does)

**Interfaces:**
- Consumes: the whole branch; `uv run youkelele run <folder> --from strums`; `uv run youkelele evaluate <name>` and `evaluate <baseline> --compare <name>`; the 1.6 clip maker `%TEMP%\youkulele-v16-validation\make_clips.py` (`strum_clip`, `tab_clips`, driven through an importlib wrapper as `%TEMP%\youkulele-v17-research\clips\make_assumption_clips.py` does).

- [ ] **Step 1: Write the expectations into the validation record before any run**

Spec 8's eight expectations as a table with empty "Met?" and "Figure" columns, plus the list of sections and stretches the sources step must cover: riff flags (All Fired Up 61-90, Day Tripper 52-58, Summer of '69 0-4, The Cars 0-11); resting stretches over two bars (Need You Tonight 0-7, Wet Leg 18-25 and 109-112, Pour Some Sugar On Me 7-10, 15-18, 66-68, 77-79, Chelsea Dagger 0-6); AC/DC's seven sections; the blind song's sections.

- [ ] **Step 2: Copy the baselines, then re-run the ten songs `--from strums`**

Run, per folder under `runs\`: `uv run youkelele run <folder> --from strums` with the log to `logs\<folder>.txt`.
Expected: exit 0 on all ten; `measure.py` reports `grid.json`, chord events and `bar_onsets` identical on all ten (expectation 1).

- [ ] **Step 3: Measure**

`evaluate` on all ten, `evaluate <baseline> --compare <folder>` on all ten; record per song: sections whose riff flag changed and the rule, bars that rest (against the 51 of spec 5), pattern changes (expected only where a bar rests), label bars, tab sections, page count against 1.6. Check `sheet.html` of every song for `class="sustain"` (expectation 2) and `class="chord label"` (expectation 5).

- [ ] **Step 4: Ground truth from published sources**

For each item of Step 1's list: search (`WebSearch`, then `WebFetch` on the lesson or tab page) for what published guitar lessons or tab transcriptions say the part is, on yourguitaracademy.com, licklibrary.com, yousician.com, Songsterr or Ultimate Guitar first; record in the validation record a table with the song, the bars, the source URL, the source's description in one line (no lyrics), and the chain's output (strum, riff heard, riff with tab, rests). Mark each row agrees / disagrees / source silent.

- [ ] **Step 5: Ear clips only where the sources disagree, say nothing, or contradict the chain**

Cut clicks on the printed strokes for each such section, the stem alone for each resting stretch the sources do not settle, a pluck clip for any newly printed tab, and AC/DC's six ear-truth sections on the 1.7 output; write the listing to `clips\listing.md` with one question per clip. Present the clips to the owner as the tie-break; record verdicts in the validation record.

- [ ] **Step 6: The blind song**

Ask the owner for the URL when Steps 2 to 5 are done; `uv run youkelele run <url>` from ingest; `evaluate`; record its figures without judging them (expectation 8) and its sections in the sources table.

- [ ] **Step 7: Assumptions and findings**

Re-rate A1 to A11 against the measured figures; list every section whose output the sources or the ear rejected under "Recorded, not tuned"; list any resting bar outside spec 5's 51 and any ear-verified bar that rests (expectation 4). If a finding is a code defect (not a threshold the ear disagrees with), fix it on the branch with a test, re-run the affected songs and record the fix round as the 1.6 record does.

- [ ] **Step 8: Commit the record on main; the manifests at 0.8.0 stay under `runs\`**

```bash
git add docs/superpowers/specs/2026-10-06-v1-7-validation.md
git commit -m "docs: 1.7 validation on ten songs and one blind song, with published-source ground truth"
```

---

## Self-review

- **Spec coverage.** 3.1 Task 6; 3.2 Tasks 5 and 6; 3.3 Tasks 2, 4, 5, 6; 3.4 recorded in Task 8's README and Task 9's AC/DC rows; 4.1 Task 3 (constant) and Task 4 (`riff_rule`); 4.2 nothing to build; 4.3 Task 9 expectation 3; 4.4 by the Global Constraints; 5 Tasks 2 and 4; 6 Task 8 (README lines) and the Global Constraints (rings kept, nothing else changes); 7 Tasks 1, 3, 4, 5, 6, 7, 8; 8 Task 9; 9 Task 9 Step 7.
- **Decisions the spec left open**, each made in one task and to be amended into the spec on acceptance: the short-bar STFT padding (Task 2); naming every voiced member so the shares cover every section (Task 4, at the cost of the pitch tracker running on every song); the two-bar phase from the first holding bar and the resting record's values (Task 4); the faint rest dots staying and the tab block's sustain lines going (Task 6).
- **Type consistency.** `rests`, `energy_ratio`, `low_share`, `root_share`, `named_share`, `riff_rule`, `label` are spelled the same in Tasks 1, 4, 5, 6, 7; `bar_holds(energy_ratio, low_share)` argument order matches its callers in Task 4; `_labels` returns `dict[int, str]` keyed on the member's first bar and `build_score` reads it that way.
- **Review Focus.** Each line names its owning task and the test is in that task's Step 1.
- **Proportion.** Nine tasks, test names and assertions with the spec's values, signatures without bodies; the only prose bodies are the decisions above.
