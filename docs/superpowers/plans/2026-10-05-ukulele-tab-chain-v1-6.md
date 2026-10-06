# Ukulele Tab Chain 1.6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every bar on the sheet carries its own chord and strokes with held strokes drawn as held; a section's pattern is a real bar when that represents it better than the vote; members of a merged section print their own pattern when it differs; a riff prints as ukulele tab only when its extracted line passes a gate, otherwise the sheet says "riff heard, not transcribed".

**Architecture:** The strums stage gains a hybrid majority/medoid vote, a two-bar unit rule, per-member patterns, a per-section ring flag from stroke decay, and the pitch-change riff test, and writes a per-bar record to `strums.json` (schema 2). A new riff stage between strums and arrange names a pitch at each trusted onset, reduces the bars to a one- or two-bar riff by the same vote, gates it, maps it to strings and frets, and writes `riff.json`. The score builder emits per-bar strokes, ring flags, grey and tab (schema 2) and backfills 1.5 files. The renderer is rewritten around a bar box drawn as inline SVG; the strip, example-bar and row-folding code is deleted.

**Tech Stack:** Python 3.12 via uv, pydantic 2, numpy, librosa (`pyin`, constant-Q), Jinja2 and inline SVG, Playwright Chromium PDF, pytest.

**Spec:** `docs/superpowers/specs/2026-10-05-ukulele-tab-chain-v1-6-design.md` (cited as "spec N"). Research under `docs/superpowers/research/2026-10-05-v1-6/` (listening pass, pattern-vote, riff-pitch, assumption-pass, lyrics).

## Global Constraints

- Schema version 2 for `strums.json` and `score.json`; every 1.3, 1.4 and 1.5 artifact loads, and a 1.5 `strums.json` or `score.json` renders under the new page via backfill (spec 7, A17).
- Nothing reads a song's title, id, duration or any other identity; every rule applies to any input; unit tests use synthetic inputs or measured numbers as examples of a rule (spec 1, Generality).
- Chords, beats, bars and `bar_onsets` are byte-identical to 1.5 on every re-run song (spec 6, A16): nothing in `music/onsets.py`, `music/recall.py`, `music/relabel.py`, `music/riff.py`'s two features, or the grid and harmony stages changes.
- Constants, verbatim from the spec: `HYBRID_DELTA = 0.04`; `MEDOID_MIN_STROKES = 2` (down or up strokes, mutes excluded); `PERIOD2_MARGIN = 0.10`; `PERIOD2_MIN_STRIKES = 2` (non-rest cells); `MEMBER_AGREE = 0.35`; `RING_SECTION_DB = 5`; `PITCH_CHANGE_MIN = 0.4`; `RIFF_AGREE_MIN = 0.70`; `RIFF_SUPPORT_MIN = 0.75`; `RIFF_NAMED_MIN = 0.6`; pyin `fmin 82.4`, `fmax 1318.5`, `frame_length 2048`, `hop_length 256` at 22 050 Hz; note window 20 ms after the onset to 10 ms before the next, at least half the frames voiced; comfortable range MIDI 60 to 81; `RIFF_ENTROPY_MAX` and `RIFF_SINGLE_PC_MIN` unchanged.
- Header phrases, verbatim (spec 3.2): "pattern uncertain", "riff", "riff heard, not transcribed", "no strummed instrument detected", "written an octave up", "written an octave down". Legend line when any tab prints: "Tab: A E C G top to bottom; numbers are frets." Repeat mark: "play twice", "play three times", "play N times" (N spelled as a digit from four).
- UK spelling; no em-dashes; no song lyrics in code, tests or documents; no time or effort estimates in documents.
- Package version 0.7.0 in `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock`; the nine manifests at 0.7.0 after validation.
- Run folders under `C:\Users\gethi\sources\Youkulele\runs\` are touched only by Task 13.
- Work happens in the worktree `C:\Users\gethi\sources\Youkulele\.claude\worktrees\v1-6` on branch `worktree-v1-6`; the spec and this plan live on main and are amended there. Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. The shell guard refuses compound bash containing git: plain separate git commands only. Write files with the Write tool, not Bash heredocs.

## Review Focus

1. A section of one bar, or one whose bars are all rests: the medoid equals the majority, the two-bar rule does not fire, confidence and p are computed without division by zero, and the bar prints greyed with its own vote (spec 4.5). Tests in Tasks 2 and 4.
2. A 1.5 `strums.json` (no `bars`) and a 1.5 `score.json` (no per-bar strokes): both render under the new page, every bar carrying its section's pattern with `rings` true, and no section carrying a `state` it never had. Tests in Tasks 8 and 10.
3. A riff section whose onsets are all unvoiced, or that has no onsets at all: `named_share` is 0, nothing is printable, no exception, and the sheet prints "riff heard, not transcribed". Test in Task 7.
4. A riff with notes below the instrument's range after the best shift (bass bleed), or above it: every note moves by whole octaves into range, no fret is negative, and the header names the shift. Test in Task 7.
5. A line that would hold eight bars but one of them has two chords, a sixteenth-grid song, and a section opening with a pickup bar: the line holds four, the count row prints `1 e & a`, and the pickup bar is drawn narrower with its label. Tests in Task 9.

---

### Task 1: Schemas for the per-bar record, the riff file and the score's bars

**Confidence:** 96%

**Files:**
- Modify: `src/youkelele/schemas.py` (`Slot` area, `SectionPattern`, `Strums`, `ScoreBar`, `ScoreSection`; new `Stroke`, `BarStrums`, `RiffNote`, `TabNote`, `RiffSection`, `Riffs`)
- Test: `tests/test_schemas.py`
- Fixtures: copy one 1.5 `strums.json` and one 1.5 `score.json` from `C:\Users\gethi\sources\Youkulele\runs\all-fired-up\` into `tests/fixtures/v15_strums.json` and `tests/fixtures/v15_score.json` (check `tests/fixtures` first; keep the 1.3 and 1.4 fixtures Task 1 of 1.5 added).

**Interfaces:**
- Produces, all `_Artifact` subclasses with `schema_version` defaulting to 1 and written as 2 by the stages that produce them:
  - `class Stroke: slot: int; kind: Literal["D", "U", "x"]; rings: bool = True; decay_db: float | None = None`
  - `class BarStrums: index: int; member: int; strokes: list[Stroke]; pattern: list[Slot]; unit: int = 1; confidence: float = 0.0; chance_p: float | None = None; uncertain: bool = True; riff: bool = False` (`member` indexes the planned section's `members` list; `pattern` is the slot vector this bar prints)
  - `SectionPattern` gains `candidate: Literal["majority", "medoid"] = "majority"`, `score_majority: float | None = None`, `score_medoid: float | None = None`, `unit: int = 1`, `pitch_change_share: float | None = None`, `rings: bool = True`, `ring_decay_db: float | None = None`
  - `Strums.bars: list[BarStrums] = []` (empty in files before 1.6)
  - `class RiffNote: slot: int; midi: int | None`
  - `class TabNote: slot: int; midi: int; string: int; fret: int; rings: bool = True` (`string` is the index into the instrument's tuning in diagram order, 0 = G)
  - `class RiffSection: section: int; start_bar: int; end_bar: int; unit: int; onsets: list[list[RiffNote]]; riff: list[TabNote]; agreement: float; support: float; named_share: float; candidate: Literal["majority", "medoid"]; octave_shift: int; printable: bool; reason: str | None = None`
  - `class Riffs: sections: list[RiffSection] = []`
  - `ScoreBar` gains `strokes: list[Stroke] = []`, `tab: list[TabNote] | None = None`, `grey: bool = False`
  - `ScoreSection` gains `state: str = ""` (one of the spec 3.2 phrases or empty), `octave_shift: int = 0`
- Validators: `Strums._check_slot_lengths` also checks every `bars[i].pattern` has `slots_per_bar` entries and every stroke's `slot` is in range; `Riffs` checks each `TabNote.fret >= 0` and `0 <= string < 4`.

- [ ] **Step 1: Write the failing tests**

```python
def test_strums_v15_fixture_loads_with_empty_bars_and_defaults():
    s = load_model(FIXTURES / "v15_strums.json", Strums)
    assert s.bars == [] and s.patterns[0].candidate == "majority" and s.patterns[0].rings is True

def test_bar_strums_round_trips_and_checks_slot_length():
    bar = BarStrums(index=3, member=0, strokes=[Stroke(slot=0, kind="D", rings=False, decay_db=12.5)], pattern=list("D-D-D-DU"))
    s = Strums(slots_per_bar=8, source="guitar_stem", source_ratio=0.4, grid_fit=0.9, uncertain=False, patterns=[], bar_onsets=[], bars=[bar])
    assert Strums.model_validate_json(s.model_dump_json()).bars[0].strokes[0].decay_db == 12.5
    with pytest.raises(ValidationError):
        Strums(slots_per_bar=8, source="guitar_stem", source_ratio=0.4, grid_fit=0.9, uncertain=False, patterns=[], bar_onsets=[], bars=[bar.model_copy(update={"pattern": list("D-D-")})])

def test_riffs_round_trip_and_reject_negative_fret():
    note = TabNote(slot=2, midi=62, string=1, fret=2)
    sec = RiffSection(section=1, start_bar=13, end_bar=24, unit=1, onsets=[[RiffNote(slot=0, midi=60)]], riff=[note], agreement=0.74, support=0.8, named_share=0.91, candidate="medoid", octave_shift=0, printable=True)
    assert Riffs.model_validate_json(Riffs(sections=[sec]).model_dump_json()).sections[0].riff[0].fret == 2
    with pytest.raises(ValidationError):
        TabNote(slot=2, midi=62, string=1, fret=-1)

def test_score_v15_fixture_loads_with_empty_strokes_and_state():
    sc = load_model(FIXTURES / "v15_score.json", Score)
    bar = sc.sections[0].bars[0]
    assert bar.strokes == [] and bar.tab is None and bar.grey is False and sc.sections[0].state == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schemas.py -q`
Expected: FAIL with `ImportError` for `BarStrums` / `Riffs`.

- [ ] **Step 3: Add the classes and fields to `schemas.py`** with the defaults in Interfaces and a one-line comment per field in the file's style. `Stroke` and `BarStrums` go above `Strums`; `RiffNote`, `TabNote`, `RiffSection`, `Riffs` go after `Strums`.

- [ ] **Step 4: Run the schema suite**

Run: `uv run pytest tests/test_schemas.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/schemas.py tests/test_schemas.py tests/fixtures
git commit -m "feat: schema fields for per-bar strokes, the riff file and the score's bars"
```

---

### Task 2: The hybrid vote and the two-bar unit

**Confidence:** 94%. The rule and its constants are measured on all 68 sections (spec 4.1, 4.2, A1, A3); the scoring functions are specified exactly, and the only open choice (which majority the leave-one-out uses) is fixed below as the topped vote the stage prints.

**Files:**
- Create: `src/youkelele/music/vote.py`
- Test: `tests/test_vote.py`

**Interfaces:**
- Consumes: `jaccard`, `_topped_vote`, `bar_repeat` from `music/as_played.py`; `StrikeClass` from `music/onsets.py`.
- Produces, in `music/vote.py`:
  - `HYBRID_DELTA = 0.04`, `MEDOID_MIN_STROKES = 2`, `PERIOD2_MARGIN = 0.10`, `PERIOD2_MIN_STRIKES = 2`
  - `@dataclass(frozen=True) class VoteResult: vector: list[StrikeClass]; candidate: Literal["majority", "medoid"]; score_majority: float; score_medoid: float; unit: int` (`vector` has `unit * slots_per_bar` cells)
  - `def medoid(bars: Sequence[Sequence[StrikeClass]]) -> tuple[list[StrikeClass], float]`: the bar with the highest mean `jaccard` to the others (ties to the earliest); its score; a single bar scores 1.0.
  - `def majority_loo_score(bars) -> float`: mean over bars of `jaccard(bar, _topped_vote(bars without bar))`; with one bar, `jaccard(bar, _topped_vote([bar]))`.
  - `def period_margin(bars) -> float`: mean `jaccard` at lag 2 minus mean at lag 1; 0.0 with fewer than 4 bars.
  - `def best_pair(bars) -> tuple[int, int]`: the start index of the consecutive pair with the highest mean agreement to the other pairs at even offsets, and that score.
  - `def choose_unit(bars) -> int`: 2 when `period_margin >= PERIOD2_MARGIN` and each bar of `best_pair` has at least `PERIOD2_MIN_STRIKES` non-rest cells, else 1.
  - `def choose_pattern(bars: Sequence[Sequence[StrikeClass]]) -> VoteResult`: unit by `choose_unit`; with unit 2 the "bars" voted over are consecutive pairs concatenated (an odd last bar is left out of the vote); medoid when `score_medoid - score_majority >= HYBRID_DELTA` and the medoid has at least `MEDOID_MIN_STROKES` `S` cells, else majority (`_topped_vote`).

- [ ] **Step 1: Write the failing tests**

```python
def test_medoid_is_a_real_bar_with_best_mean_agreement():
    bars = [list("S-S-S-SS"), list("S-S-S-SS"), list("S-SS-S-S")]
    vector, score = medoid(bars)
    assert vector == list("S-S-S-SS") and abs(score - (1.0 + jaccard(bars[0], bars[2])) / 2) < 1e-9

def test_majority_erases_pushes_that_move_and_medoid_keeps_them():
    # three bars each with one push on a different off-beat: the vote keeps only the beats
    bars = [list("S-S-SSS-"), list("S-SSS-S-"), list("SSS-S-S-")]
    assert _topped_vote(bars) == list("S-S-S-S-")
    assert "S" in medoid(bars)[0][1::2]  # the medoid is one of the bars, pushes included

def test_choose_pattern_picks_majority_below_delta_and_medoid_at_or_above():
    bars_tie = [list("S-S-S-S-")] * 4
    r = choose_pattern(bars_tie)
    assert r.candidate == "majority" and r.vector == list("S-S-S-S-") and r.unit == 1
    # a shared core with one extra push per bar in scattered places: the leave-one-out vote
    # keeps changing (0.635 mean agreement) while the medoid is a real bar (0.733)
    core = list("S-S-S-S-")
    bars = []
    for extra in (1, 3, 5, 7, 1, 3):
        bar = list(core); bar[extra] = "S"; bars.append(bar)
    r = choose_pattern(bars)
    assert r.score_medoid - r.score_majority >= HYBRID_DELTA and r.candidate == "medoid"
    assert r.vector == list("SSS-S-S-")  # the earliest of the tied best bars

def test_choose_pattern_never_switches_to_a_medoid_under_the_stroke_floor():
    bars = [list("--------")] * 3 + [list("x-------")] * 3 + [list("S-------")]
    r = choose_pattern(bars)
    assert r.candidate == "majority"  # the all-rest and all-mute medoids have fewer than 2 S cells

def test_period_margin_and_unit_two_on_alternating_bars():
    a, b = list("S--S--S-"), list("SSS-SSS-")
    assert period_margin([a, b] * 4) >= PERIOD2_MARGIN and choose_unit([a, b] * 4) == 2
    assert choose_unit([a, list("-------S")] * 4) == 1  # the sparse bar fails the strike floor
    r = choose_pattern([a, b] * 4)
    assert r.unit == 2 and r.vector == a + b

def test_single_bar_and_all_rest_sections_do_not_raise():
    assert choose_pattern([list("S-S-----")]).vector == _topped_vote([list("S-S-----")])
    r = choose_pattern([list("--------")] * 3)
    assert r.candidate == "majority" and r.vector == list("--------")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_vote.py -q`
Expected: FAIL with `ModuleNotFoundError: youkelele.music.vote`.

- [ ] **Step 3: Implement `music/vote.py`** with the signatures above. The leave-one-out majority is `_topped_vote` so the score compares what would print. For unit 2 build `pairs = [bars[i] + bars[i + 1] for i in range(0, len(bars) - 1, 2)]` and run the same two candidates over the pairs.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_vote.py tests/test_as_played.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/vote.py tests/test_vote.py
git commit -m "feat: hybrid majority/medoid vote with a stroke floor and a two-bar unit rule"
```

---

### Task 3: Stroke decay and the ring flag

**Confidence:** 93%. The measurement is defined and its band measured on 2,114 strokes (A5); the one choice left open, the RMS frame, is fixed below.

**Files:**
- Create: `src/youkelele/music/ring.py`
- Test: `tests/test_ring.py`

**Interfaces:**
- Produces, in `music/ring.py`:
  - `RING_SECTION_DB = 5`, `RING_MIN_GAP_SLOTS = 1.5`, `_FRAME_S = 0.010`, `_HOP_S = 0.005`
  - `def stroke_decay_db(y: np.ndarray, sr: int, onset: float, next_onset: float | None, slot_seconds: float) -> float | None`: RMS over 10 ms frames hopped 5 ms from `onset`; the peak frame is the loudest within the first half slot after the onset; the decay is `20 * log10(rms_peak / rms_at(peak_time + slot_seconds))`, clipped at 0 from below; None when `next_onset` is nearer than `RING_MIN_GAP_SLOTS` slots or the signal ends first.
  - `def section_rings(decays: Sequence[float | None]) -> tuple[bool, float | None]`: `(median < RING_SECTION_DB, median)` over the non-None values; `(True, None)` when there are none.

- [ ] **Step 1: Write the failing tests**

```python
def _pluck(sr, seconds, tau):  # an exponentially decaying 220 Hz tone
    t = np.arange(int(sr * seconds)) / sr
    return np.sin(2 * np.pi * 220 * t) * np.exp(-t / tau)

def test_slow_decay_measures_small_and_fast_decay_large():
    sr, slot = 22050, 0.25
    slow = stroke_decay_db(_pluck(sr, 2.0, tau=1.0), sr, 0.0, None, slot)
    fast = stroke_decay_db(_pluck(sr, 2.0, tau=0.05), sr, 0.0, None, slot)
    assert slow is not None and fast is not None and slow < 5 < fast

def test_decay_is_none_when_the_next_stroke_is_too_close():
    assert stroke_decay_db(_pluck(22050, 2.0, 0.5), 22050, 0.0, 0.3, 0.25) is None  # 1.2 slots
    assert stroke_decay_db(_pluck(22050, 2.0, 0.5), 22050, 0.0, 0.4, 0.25) is not None  # 1.6 slots

def test_section_rings_by_median_and_defaults_true_without_strokes():
    assert section_rings([2.0, 3.0, 12.0]) == (True, 3.0)
    assert section_rings([9.0, 12.0, None]) == (False, 10.5)
    assert section_rings([None, None]) == (True, None)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_ring.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `music/ring.py`** (pure numpy).

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_ring.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/ring.py tests/test_ring.py
git commit -m "feat: stroke decay per slot and the per-section ring flag"
```

---

### Task 4: Pitch naming at the onsets and the pitch-change share

**Confidence:** 92%. The tracker call and window are the spike's exact ones (A12) and the owner confirmed the pitches it produced; the synthetic test uses pure tones, which pyin names reliably.

**Files:**
- Create: `src/youkelele/music/pitch.py`
- Test: `tests/test_pitch.py`

**Interfaces:**
- Produces, in `music/pitch.py`:
  - `PITCH_SR = 22050`, `PYIN_FMIN = 82.4`, `PYIN_FMAX = 1318.5`, `PYIN_FRAME = 2048`, `PYIN_HOP = 256`, `NOTE_SKIP_IN_S = 0.020`, `NOTE_SKIP_OUT_S = 0.010`, `NOTE_VOICED_MIN = 0.5`, `PITCH_CHANGE_MIN = 0.4`
  - `@dataclass class PitchTrack: times: np.ndarray; midi: np.ndarray` (nan where unvoiced)
  - `def track_pitch(y: np.ndarray, sr: int) -> PitchTrack`: resample to `PITCH_SR` if needed, `librosa.pyin(y, fmin=PYIN_FMIN, fmax=PYIN_FMAX, sr=PITCH_SR, frame_length=PYIN_FRAME, hop_length=PYIN_HOP)`, `midi = librosa.hz_to_midi(f0)` with nan where `voiced_flag` is false.
  - `def name_notes(track: PitchTrack, onsets: Sequence[float], ends: Sequence[float]) -> list[int | None]`: for each onset `i` the rounded median of `track.midi` over frames in `[onset + NOTE_SKIP_IN_S, ends[i] - NOTE_SKIP_OUT_S)`, where `ends[i]` is the next onset or the bar end the caller passes; None when fewer than `NOTE_VOICED_MIN` of those frames are voiced or the window is empty.
  - `def pitch_change_share(notes: Sequence[int | None]) -> float | None`: over consecutive pairs where both are named, the share whose pitches differ; None with no such pair.

- [ ] **Step 1: Write the failing tests**

```python
def _tone_sequence(sr, midis, seconds_each):
    parts = [np.sin(2 * np.pi * librosa.midi_to_hz(m) * np.arange(int(sr * seconds_each)) / sr) for m in midis]
    return np.concatenate(parts).astype(np.float32)

def test_name_notes_recovers_a_c_d_eflat_sequence():
    sr = 22050
    y = _tone_sequence(sr, [60, 62, 63, 62], 0.5)
    track = track_pitch(y, sr)
    onsets = [0.0, 0.5, 1.0, 1.5]
    assert name_notes(track, onsets, [0.5, 1.0, 1.5, 2.0]) == [60, 62, 63, 62]

def test_unvoiced_window_names_none():
    sr = 22050
    y = np.concatenate([_tone_sequence(sr, [60], 0.5), np.zeros(int(sr * 0.5), dtype=np.float32)])
    track = track_pitch(y, sr)
    assert name_notes(track, [0.0, 0.5], [0.5, 1.0]) == [60, None]

def test_pitch_change_share_counts_named_pairs_only():
    assert pitch_change_share([60, 60, 62, None, 62, 63]) == 2 / 3  # pairs (60,60) (60,62) (62,63)
    assert pitch_change_share([60]) is None and pitch_change_share([None, None]) is None
    assert pitch_change_share([43] * 8) == 0.0  # a power-chord root read as one note: a strum
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_pitch.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `music/pitch.py`**; librosa is imported inside `track_pitch` as `music/riff.py` does.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_pitch.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/pitch.py tests/test_pitch.py
git commit -m "feat: pitch named at each onset and the pitch-change share"
```

---

### Task 5: The strums stage on the plan's members, with the vote, the ring flag and the riff test

**Confidence:** 91%. The stage's loop is rewritten around members; every rule it applies is specified and tested in Tasks 2 to 4, and the member threshold's band is measured (A4). The remaining uncertainty is the interaction of per-member certainty with the existing `uncertain` flags, which the tests below pin.

**Files:**
- Modify: `src/youkelele/stages/strums.py` (the loop from the section plan to `save_model`), `src/youkelele/music/as_played.py` (remove `MIN_SECTION_BARS` inheritance use; keep the constant for 1.5 files)
- Test: `tests/test_stage_strums.py`

**Interfaces:**
- Consumes: `choose_pattern`, `VoteResult` (Task 2); `stroke_decay_db`, `section_rings` (Task 3); `track_pitch`, `name_notes`, `pitch_change_share`, `PITCH_CHANGE_MIN` (Task 4); `is_riff`, `riff_features` (unchanged); `structure_test`, `explained_onsets`, `render_directions` (unchanged).
- Produces: `strums.json` schema 2 with `bars` filled for every bar of every planned section, `patterns[k]` carrying `candidate`, `score_majority`, `score_medoid`, `unit`, `pitch_change_share`, `rings`, `ring_decay_db`; `inherited_from` always None. New constant `MEMBER_AGREE = 0.35` in `stages/strums.py`.
- Rules, in order, per planned section `k` with members `m_0..m_n` (grid section spans), the longest member `L`:
  1. Per member: `classes[m]` are its bars' strike classes; `vote_m = choose_pattern(classes[m])`; `structured_m, p_m, density_m = structure_test(classes[m], vote_m.vector[:slots], seed=start_m)` (a unit-2 vector is tested by its first bar as the vote's representative); `confidence_m` = mean `jaccard` of the member's bars with `vote_m.vector` (bars paired against the matching half when unit 2); `uncertain_m = confidence_m < floor or explained_m < EXPLAINED_BELOW or not structured_m` (no `long_enough` term: short members print their own greyed vote, spec 4.5).
  2. The section's figures are `L`'s: `patterns[k].slots = render_directions(vote_L.vector[:slots])` for unit 1, or the first bar of a unit-2 vector with `unit = 2`; `candidate`, `score_majority`, `score_medoid` from `vote_L`.
  3. Riff test per member: `entropy, single = riff_features(chroma[inside_m])`; `pcs_m = pitch_change_share(name_notes(track, onsets in m before the recall gate, next onset or bar end))` where `track = track_pitch(y, sr)` is computed once per song only if any member passes `is_riff(entropy, single)`; `riff_m = is_riff(entropy, single) and pcs_m is not None and pcs_m >= PITCH_CHANGE_MIN`. `patterns[k].riff = riff_L`, `pitch_change_share = pcs_L`.
  4. Ring per member: `decays = [stroke_decay_db(y, sr, t, next_t, slot_seconds) for each onset t in the member's bars]` (next_t the next onset of the song; slot_seconds = bar length / slots); `rings_m, median_m = section_rings(decays)`; on `source == "mix"` `rings_m = True`. `patterns[k].rings = rings_L`, `ring_decay_db = median_L`.
  5. Which pattern a member's bars print: the section's (`L`'s) when `jaccard(strike classes of vote_m.vector[:slots], strike classes of vote_L.vector[:slots]) >= MEMBER_AGREE` or `m == L`; otherwise its own. A bar's `BarStrums.pattern` is `render_directions` of the chosen vector's bar at `(bar_index - member_start) % unit`; `uncertain` is `uncertain_L` when printing the section's, else `uncertain_m`; `riff = riff_m`; `confidence` and `chance_p` follow the same choice.
  6. `BarStrums.strokes`: one `Stroke` per non-rest cell of `bar_onsets[bar]` with `kind` the rendered direction or `x`, `rings = rings_m`, `decay_db` the stroke's measured decay (None when unmeasurable).
  7. No-instrument members and the empty outro: as 1.5, with `bars` entries carrying an all-rest pattern, `uncertain=True`, no strokes.
  8. Delete the inheritance block (`short`, `donor`); `MIN_SECTION_BARS` stays exported for the evaluate text of 1.5 files.

- [ ] **Step 1: Write the failing tests** (extend the existing fixtures in `tests/test_stage_strums.py`: `_grid`, `_chords`, `_ctx`, the sine-burst stems; add a helper `_bursts(pattern: str, bars: int, bar_seconds: float, tau: float)` writing one decaying 220 Hz burst per `S` cell so decay is controllable)

```python
def test_bars_record_every_bar_with_its_pattern_and_strokes(tmp_path):
    # one section of 8 bars playing S-S-S-SS throughout, ringing (tau 1.0 s)
    ... run the stage ...
    s = load_model(path, Strums)
    assert s.schema_version == 2 and len(s.bars) == 8
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars) and all(b.member == 0 for b in s.bars)
    assert [k.slot for k in s.bars[0].strokes] == [0, 2, 4, 6, 7] and all(k.rings for k in s.bars[0].strokes)
    assert s.patterns[0].candidate == "majority" and s.patterns[0].unit == 1 and s.patterns[0].rings is True

def test_muted_playing_marks_the_section_short(tmp_path):
    # same pattern, bursts with tau 0.02 s (decay well over 5 dB per slot)
    assert s.patterns[0].rings is False and all(not k.rings for k in s.bars[0].strokes) and s.patterns[0].ring_decay_db > RING_SECTION_DB

def test_member_prints_its_own_pattern_when_it_disagrees(tmp_path):
    # grid sections: verse 8 bars S-S-S-SS, verse 4 bars S------- (a fragment, same chords, merges);
    # the fragment's own vote agrees under MEMBER_AGREE with the section's
    merged = s.plan[0]; assert merged.members == [0, 1]
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars[:8])
    assert all(b.pattern == list("D-------") for b in s.bars[8:12]) and all(b.uncertain for b in s.bars[8:12])

def test_member_prints_the_sections_pattern_when_it_agrees(tmp_path):
    # fragment plays S-S-S-S- (agreement with S-S-S-SS is 0.8)
    assert all(b.pattern == list("D-D-D-DU") for b in s.bars[8:12])

def test_short_section_keeps_its_own_vote_greyed_not_a_neighbours(tmp_path):
    # sections of 8, 2 and 8 bars with different chords (no merge): the 2-bar one is uncertain and keeps its own slots
    assert s.patterns[1].inherited_from is None and s.patterns[1].uncertain and s.patterns[1].slots != s.patterns[0].slots

def test_riff_flag_needs_the_pitch_change_share(tmp_path):
    # guitar stem: bursts of ONE pitch per section (a power-chord root) versus alternating 60/62/63 pitches
    assert s.patterns[0].riff is False and s.patterns[0].pitch_change_share == 0.0
    assert s.patterns[1].riff is True and s.patterns[1].pitch_change_share >= PITCH_CHANGE_MIN

def test_single_bar_and_all_rest_members_do_not_raise(tmp_path):
    # a 1-bar section and a silent section both produce a bars record with an all-rest or own pattern and uncertain True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stage_strums.py -q`
Expected: the new tests FAIL (`bars` empty, `candidate` missing); the existing ones PASS.

- [ ] **Step 3: Rewrite the loop in `stages/strums.py`** per the rules above, calling the Task 2 to 4 functions; keep the recall gate, has-instrument, trailing-drop, plan and chroma code as it is. Write `schema_version=2`.

- [ ] **Step 4: Run the stage and music suites**

Run: `uv run pytest tests/test_stage_strums.py tests/test_as_played.py tests/test_vote.py -q`
Expected: PASS. Two existing tests about inheritance (`inherited_from`) will fail; update them to assert the new behaviour (own vote, greyed) and name the spec section (4.5) in a comment.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/stages/strums.py src/youkelele/music/as_played.py tests/test_stage_strums.py
git commit -m "feat: strums stage votes per member, records every bar, flags ring and riff by pitch change"
```

---

### Task 6: Riff reduction, the gate, and the tab mapping

**Confidence:** 92%. The reduction reuses Task 2's vote with an exact-pitch agreement; the gate constants are the spec's (A9 to A11); the mapping is a rule of the instrument with the verified riff as its example.

**Files:**
- Create: `src/youkelele/music/riff_line.py`, `src/youkelele/music/tab.py`
- Test: `tests/test_riff_line.py`, `tests/test_tab.py`

**Interfaces:**
- Produces, in `music/riff_line.py`:
  - `RIFF_AGREE_MIN = 0.70`, `RIFF_SUPPORT_MIN = 0.75`, `RIFF_NAMED_MIN = 0.6`
  - `NoteBar = list[int | None]` (one entry per slot: a MIDI note starting there or None)
  - `def note_jaccard(a: NoteBar, b: NoteBar) -> float`: over slots where either has a note, 1 for the same pitch, 0 otherwise; 1.0 when neither has a note.
  - `@dataclass(frozen=True) class RiffChoice: unit: int; notes: NoteBar; candidate: Literal["majority", "medoid"]; agreement: float; support: float`
  - `def choose_riff(bars: Sequence[NoteBar]) -> RiffChoice`: unit by Task 2's `choose_unit` applied to the bars' strike shape (`S` where a note, `-` where None); majority per slot = the most common pitch among bars that have a note there when at least half of all bars do; medoid = the real bar (or pair) with the highest mean `note_jaccard` to the others; hybrid rule with `HYBRID_DELTA` and a floor of `MEDOID_MIN_STROKES` named notes; `support` = mean over the chosen bar's notes of the share of bars with that pitch in that slot.
  - `def gate(choice: RiffChoice, named_share: float, riff_flag: bool) -> tuple[bool, str | None]`: `(True, None)` when `choice.agreement >= RIFF_AGREE_MIN and choice.support >= RIFF_SUPPORT_MIN and named_share >= RIFF_NAMED_MIN and riff_flag`, else `(False, reason)` with reason one of `"agreement 0.52 < 0.70"`, `"support ..."`, `"named ..."`, `"not a riff"` (the first that fails).
- Produces, in `music/tab.py`:
  - `RANGE_LO, RANGE_HI = 60, 81`
  - `def tuning_midis(pitches: Sequence[str]) -> list[int]` (`("G4","C4","E4","A4") -> [67, 60, 64, 69]`)
  - `def octave_shift(midis: Sequence[int]) -> int`: the shift in `[-2, 2]` (whole octaves) that puts the most notes inside `[RANGE_LO, RANGE_HI]`; ties to the smaller absolute shift, then to the positive one.
  - `def into_range(midi: int) -> int`: moved by whole octaves until inside the range (a note that cannot fit, none exist for a 21-semitone range, raises).
  - `def string_fret(midi: int, tuning: Sequence[int]) -> tuple[int, int]`: the string with the lowest non-negative fret; ties to the lower-numbered string in diagram order.
  - `def to_tab(notes: NoteBar, rings: bool, tuning: Sequence[int]) -> tuple[list[TabNote], int]`: `(tab, shift)`.

- [ ] **Step 1: Write the failing tests**

```python
NYT = [60, 60, 62, None, None, None, 62, None, 60, None, 62, 63, None, 62, None, 60]  # the verified riff, 16 slots

def test_choose_riff_on_steady_bars_passes_the_gate():
    bars = [NYT] * 6 + [NYT[:10] + [None] * 6]
    c = choose_riff(bars)
    assert c.unit == 1 and c.notes == NYT and c.agreement >= RIFF_AGREE_MIN and c.support >= RIFF_SUPPORT_MIN
    assert gate(c, named_share=0.91, riff_flag=True) == (True, None)

def test_unsteady_bars_fail_on_agreement_with_a_reason():
    rng = random.Random(3)
    bars = [[rng.choice([None, 55, 57, 60, 62, 64]) for _ in range(16)] for _ in range(8)]
    c = choose_riff(bars)
    ok, reason = gate(c, named_share=0.8, riff_flag=True)
    assert not ok and reason.startswith("agreement")

def test_gate_rejects_a_strum_even_when_steady():
    bars = [[43] + [None] * 7] * 8
    assert gate(choose_riff(bars), named_share=0.95, riff_flag=False) == (False, "not a riff")

def test_tab_maps_the_verified_riff_onto_the_c_string_without_a_shift():
    tab, shift = to_tab(NYT, True, tuning_midis(("G4", "C4", "E4", "A4")))
    assert shift == 0 and [(n.string, n.fret) for n in tab] == [(1, 0), (1, 0), (1, 2), (1, 2), (1, 0), (1, 2), (1, 3), (1, 2), (1, 0)]

def test_octave_shift_lifts_a_guitar_register_riff_and_moves_outliers():
    assert octave_shift([56, 56, 63, 63, 60, 62]) == 1  # G#3 to D#4 sits an octave low
    tab, shift = to_tab([44, 56, 63], True, tuning_midis(("G4", "C4", "E4", "A4")))
    assert shift == 1 and all(RANGE_LO <= n.midi <= RANGE_HI for n in tab) and all(n.fret >= 0 for n in tab)

def test_string_fret_prefers_the_lowest_fret_and_treats_g_as_high():
    t = tuning_midis(("G4", "C4", "E4", "A4"))
    assert string_fret(67, t) == (0, 0) and string_fret(69, t) == (3, 0) and string_fret(65, t) == (2, 1)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_riff_line.py tests/test_tab.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement both modules.**

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_riff_line.py tests/test_tab.py tests/test_vote.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/riff_line.py src/youkelele/music/tab.py tests/test_riff_line.py tests/test_tab.py
git commit -m "feat: riff reduction by the hybrid vote, the printable gate, and the string and fret mapping"
```

---

### Task 7: The riff stage

**Confidence:** 93%. It composes Tasks 4 and 6 over the artifacts Task 5 writes; the one decision not in the spec (always writing `riff.json`) is made here and amended into spec 7.

**Files:**
- Create: `src/youkelele/stages/riff.py`
- Modify: `src/youkelele/profiles/ukulele.py` (insert `RiffStage()` after `StrumsStage()`), `src/youkelele/evaluate.py:292-300` (`_load_strums` and the `_diagnose` paths: `04_strums` stays; add `_load_riffs` at `05_riff/riff.json`), `src/youkelele/runner.py:63-76` (`check_requirements`) and `src/youkelele/commands.py:64-70` (the start stage), any test or module that hard-codes `05_arrange`, `06_score`, `07_render` (grep `0[5-7]_` under `src/` and `tests/`; they move to `06_`, `07_`, `08_`)
- Spec 7's `riff.json` paragraph already says (amended with this plan): written on every run, `sections` empty when the song has no riff section, and a pre-1.6 folder resumed from arrange or later starts from the riff stage.
- Test: `tests/test_stage_riff.py`, `tests/test_runner.py` (stage order and numbering)

**Interfaces:**
- Produces: `class RiffStage(Stage)`: `name = "riff"`, `requires = ("separate/stems/guitar.wav", "separate/stems/other.wav", "ingest/audio.wav", "grid/grid.json", "strums/strums.json")`, `produces = ("riff/riff.json",)`, `__init__(self, tuning: Tuning, pitch_tracker: Callable[[np.ndarray, int], PitchTrack] = track_pitch)`.
- Rules: source by `strums.source` (the same stem the strums stage used); for every planned section `k` and member whose `BarStrums.riff` is true (read from `strums.bars`): onsets per bar are the bar's `strokes` (slot times from the bar's start and `slots_per_bar`); `name_notes` over them with ends at the next stroke or the bar end; `NoteBar` per bar; `named_share` = named strokes over strokes; `choose_riff`; `gate` with `riff_flag = True`; `to_tab(choice.notes, rings of the member, tuning_midis(tuning.pitches))`; one `RiffSection` per riff member with `section = k`, `start_bar`, `end_bar` the member's span, `onsets` the per-bar `RiffNote` lists, `riff` the tab (empty when not printable), `reason`. Log one line per riff member: `section k bars a-b: agreement 0.74 support 0.80 named 0.91: printable` or `: not transcribed (agreement 0.52 < 0.70)`.
- Stage numbering: the profile's stages become `(StrumsStage(), RiffStage(UKULELE_TUNING), ArrangeStage(), ScoreStage(...))`; run folders `05_riff`, `06_arrange`, `07_score`, `08_render`. `youkelele stages` lists nine stages.
- Resuming a 1.5 folder (spec 7): `def earliest_start(chain, run_dir, start) -> int` in `runner.py` returns the lowest index among `start` and the producers of any artifact that `check_requirements` finds missing for stages `start..end`; `run_command` uses it and logs `starting from riff: riff/riff.json is missing` when it moved the start.

- [ ] **Step 1: Write the failing tests**

```python
def test_riff_stage_writes_tab_for_a_steady_single_note_line(tmp_path):
    # strums.json with one section of 8 bars, bars[].riff True, strokes on NYT's slots; guitar stem of pure tones at NYT's midis
    ... run RiffStage with the real tracker ...
    r = load_model(path, Riffs)
    sec = r.sections[0]
    assert sec.printable and sec.octave_shift == 0 and [n.fret for n in sec.riff] == [0, 0, 2, 2, 0, 2, 3, 2, 0]

def test_riff_stage_marks_unsteady_or_unvoiced_sections_not_transcribed(tmp_path):
    # (a) a stem of silence under a riff-flagged section: named_share 0, reason starts with "named"
    # (b) bars with random pitches: reason starts with "agreement"
    assert not sec.printable and sec.riff == [] and sec.reason is not None

def test_riff_stage_writes_an_empty_file_when_no_section_is_a_riff(tmp_path):
    assert load_model(path, Riffs).sections == []

def test_profile_chain_has_nine_stages_in_order():
    names = [s.name for s in build_chain(ukulele_profile())]
    assert names == ["ingest", "separate", "grid", "harmony", "strums", "riff", "arrange", "score", "render"]

def test_resume_from_arrange_on_a_folder_without_riff_json_starts_from_riff(tmp_path):
    # a run folder with 00_ingest to 04_strums present and no 05_riff: earliest_start(chain, run_dir, 6) == 5
    assert earliest_start(chain, run_dir, resolve_stage(chain, "arrange")) == resolve_stage(chain, "riff")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stage_riff.py tests/test_runner.py -q`
Expected: FAIL (`stages.riff` missing; eight stages).

- [ ] **Step 3: Implement `stages/riff.py`**, register it in the profile, move the hard-coded folder numbers, add `_load_riffs` to `evaluate.py`.

- [ ] **Step 4: Run the suites that touch stage numbering**

Run: `uv run pytest tests/test_stage_riff.py tests/test_runner.py tests/test_cli.py tests/test_evaluate.py tests/test_end_to_end.py -q`
Expected: PASS (the end-to-end test now has nine stages).

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/stages/riff.py src/youkelele/profiles/ukulele.py src/youkelele/evaluate.py tests
git commit -m "feat: riff stage names notes at the trusted onsets, gates the line and maps it to tab"
```

---

### Task 8: The score builder on per-bar strokes, tab, state, and 1.5 backfill

**Confidence:** 92%. The mapping from `strums.bars` and `riff.json` to the score is one to one; backfill is specified; the alphaTex change is small.

**Files:**
- Create: `src/youkelele/music/compat.py`
- Modify: `src/youkelele/music/score_builder.py` (`build_score`, `check_strums_match_grid`), `src/youkelele/stages/score.py` (requires `riff/riff.json`, loads it), `src/youkelele/music/alphatex.py` (riff bars emit notes)
- Test: `tests/test_score_builder.py`, `tests/test_compat.py`, `tests/test_alphatex.py`, `tests/test_stage_score.py`

**Interfaces:**
- Produces, in `music/compat.py`: `def backfill_bars(strums: Strums, grid: Grid) -> list[BarStrums]`: for a `Strums` with empty `bars`, one record per bar with `member` the index of the grid section containing it within its planned section, `pattern` the planned section's `slots`, `strokes` from `bar_onsets[bar]` with `rings=True`, `uncertain`, `confidence`, `chance_p`, `riff` from the pattern; `def with_bars(strums, grid) -> Strums` returning a copy with `bars` filled when empty.
- Score builder: `build_score(source, grid, chords, strums, arrangement, riffs: Riffs, tuning, instrument_name)`; `check_strums_match_grid(grid, strums, chords, riffs)` also requires every `RiffSection.section` to index the plan and its `start_bar`/`end_bar` to be a member span of that planned section, else `ArtifactError("riff.json describes sections the plan does not have; re-run from strums")`.
- Per bar: `ScoreBar.strokes = [Stroke(slot, kind, rings)]` from `BarStrums.pattern` (kind the slot letter) with `rings` from the bar's strokes (the member's flag), `grey = BarStrums.uncertain`, `tab` the printable `RiffSection.riff` notes for the bar's position in the unit (slot lists repeat per bar; a unit-2 riff alternates), else None. `ScoreChord.slots` stays (the chord's share of the bar's pattern) for the alphaTex export.
- Per section: `state` = `"no strummed instrument detected"` if `no_instrument`; else `"riff"` if any bar has `tab`; else `"riff heard, not transcribed"` if `pattern.riff`; else `"pattern uncertain"` if `pattern.uncertain`; else `""`. `octave_shift` from the printable riff section (0 otherwise). `inherited_from` always None.
- alphaTex: a bar with `tab` emits, per slot, `fret.string` notes (`string` 1 to 4 in alphaTex order, which is reversed diagram order) instead of chord brushes; rests elsewhere.

- [ ] **Step 1: Write the failing tests**

```python
def test_bars_carry_strokes_grey_and_state_from_strums_bars():
    # Strums with bars: 4 bars pattern D-D-D-DU rings False, 2 bars own pattern D------- uncertain
    score = build_score(_source(), _grid(6), _chords6, strums, _arrangement(), Riffs(), UKULELE_TUNING, "Ukulele")
    bars = score.sections[0].bars
    assert [k.slot for k in bars[0].strokes] == [0, 2, 4, 6, 7] and not bars[0].strokes[0].rings and not bars[0].grey
    assert [k.slot for k in bars[4].strokes] == [0] and bars[4].grey
    assert score.sections[0].state == "" and score.schema_version == 2

def test_printable_riff_puts_tab_on_every_bar_and_sets_state_riff():
    riffs = Riffs(sections=[RiffSection(section=0, start_bar=0, end_bar=4, unit=1, onsets=[], riff=[TabNote(slot=0, midi=60, string=1, fret=0), TabNote(slot=2, midi=62, string=1, fret=2)], agreement=0.8, support=0.9, named_share=0.9, candidate="medoid", octave_shift=1, printable=True)])
    score = build_score(..., riffs, ...)
    assert all(b.tab and [n.fret for n in b.tab] == [0, 2] for b in score.sections[0].bars)
    assert score.sections[0].state == "riff" and score.sections[0].octave_shift == 1

def test_unprintable_riff_sets_the_not_transcribed_state_and_no_tab():
    assert score.sections[0].state == "riff heard, not transcribed" and all(b.tab is None for b in score.sections[0].bars)

def test_riff_file_that_does_not_match_the_plan_is_refused():
    with pytest.raises(ArtifactError, match="riff.json describes sections the plan does not have"):
        check_strums_match_grid(grid, strums, chords, Riffs(sections=[RiffSection(section=7, ...)]))

def test_backfill_gives_a_v15_file_one_bar_record_per_bar_with_the_section_pattern():
    s = load_model(FIXTURES / "v15_strums.json", Strums); g = load_model(FIXTURES / "v15_grid.json", Grid)
    bars = backfill_bars(s, g)
    assert len(bars) == len(g.bars) and all(b.pattern == s.patterns[_plan_index(b.index)].slots for b in bars) and all(k.rings for b in bars for k in b.strokes)

def test_alphatex_riff_bar_emits_fret_string_notes():
    text = score_to_alphatex(score_with_tab)
    assert "0.3" in text and "2.3" in text  # the C string is alphaTex string 3 in reversed order
```

(`v15_grid.json` joins the fixtures from the same run folder.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_score_builder.py tests/test_compat.py tests/test_alphatex.py -q`
Expected: FAIL (`build_score` signature, `compat` missing).

- [ ] **Step 3: Implement** `music/compat.py`, the builder changes, the stage's new input, and the alphaTex branch.

- [ ] **Step 4: Run the suites**

Run: `uv run pytest tests/test_score_builder.py tests/test_compat.py tests/test_alphatex.py tests/test_stage_score.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/compat.py src/youkelele/music/score_builder.py src/youkelele/stages/score.py src/youkelele/music/alphatex.py tests
git commit -m "feat: score carries per-bar strokes, grey, tab and the section state; 1.5 files backfilled"
```

---

### Task 9: Bar lines, the eight-bar rule and whole-line repeats

**Confidence:** 94%. Pure functions over `ScoreSection`; the rules are exact in spec 3.1 and the page estimate (A14) fixed the eight-bar rule as mandatory.

**Files:**
- Create: `src/youkelele/render/lines.py`
- Delete: `src/youkelele/render/grid.py` (move `fret_notation` and `NC` into `render/diagrams.py`; update imports in `render/html.py`), `src/youkelele/render/strum_box.py`, `tests/test_render_grid.py`, `tests/test_strum_box.py`
- Test: `tests/test_render_lines.py`

**Interfaces:**
- Produces, in `render/lines.py`:
  - `@dataclass class Line: bars: list[ScoreBar]; repeat: int` (the count row and the tab string labels print once per line, on its first bar)
  - `def line_width(bars: Sequence[ScoreBar], start: int, slots_per_bar: int, meter: Meter) -> int`: 8 when `eighth_grid(slots_per_bar, meter)` and each of `bars[start:start + 8]` has at most one chord and none is a pickup, else 4.
  - `def pack_lines(section: ScoreSection, slots_per_bar: int, meter: Meter) -> list[Line]`: greedy from the first bar; a leading pickup bar is the first cell of a four-bar line and counts toward it.
  - `def fold_repeats(lines: list[Line]) -> list[Line]`: consecutive lines whose bars are identical in chord names and start slots, `strokes` (slot, kind, rings), `grey` and `tab` collapse into one with `repeat` the count; a line never collapses with a line of a different width.
  - `def repeat_text(n: int) -> str`: `"play twice"`, `"play three times"`, `"play 4 times"` and up.

- [ ] **Step 1: Write the failing tests**

```python
def test_eighth_grid_line_of_single_chord_bars_holds_eight():
    section = _section(_cycle("G", 16))  # one chord per bar
    lines = pack_lines(section, 8, M44)
    assert [len(l.bars) for l in lines] == [8, 8]

def test_a_split_bar_in_the_window_drops_the_line_to_four():
    bars = _cycle("G", 5) + [_bar(5, "D", "G")] + _cycle("G", 10, start=6)
    assert [len(l.bars) for l in pack_lines(_section(bars), 8, M44)] == [4, 4, 8]

def test_sixteenth_grid_and_pickup_lines_hold_four():
    assert all(len(l.bars) == 4 for l in pack_lines(_section(_cycle("C", 8)), 16, M44))
    bars = [_bar(0, "C", pickup=True)] + _cycle("C", 7, start=1)
    lines = pack_lines(_section(bars), 8, M44)
    assert len(lines[0].bars) == 4 and lines[0].bars[0].pickup

def test_identical_lines_fold_with_a_count_in_words():
    lines = fold_repeats(pack_lines(_section(_cycle("G", 24)), 8, M44))
    assert len(lines) == 1 and lines[0].repeat == 3 and repeat_text(3) == "play three times"
    assert repeat_text(2) == "play twice" and repeat_text(4) == "play 4 times"

def test_lines_that_differ_only_in_a_ring_flag_or_grey_do_not_fold():
    a = pack_lines(_section(_cycle("G", 8)), 8, M44)
    b = pack_lines(_section(_cycle("G", 8, grey=True)), 8, M44)
    assert len(fold_repeats(a + b)) == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_render_lines.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `render/lines.py`**; move `fret_notation`; delete the two old modules and their tests; fix imports.

- [ ] **Step 4: Run the render suites**

Run: `uv run pytest tests/test_render_lines.py tests/test_diagrams.py -q`
Expected: PASS; `tests/test_html.py` will fail until Task 10.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/render/lines.py src/youkelele/render/diagrams.py src/youkelele/render/html.py tests/test_render_lines.py
git rm src/youkelele/render/grid.py src/youkelele/render/strum_box.py tests/test_render_grid.py tests/test_strum_box.py
git commit -m "feat: bar lines with the eight-bar rule and whole-line repeats in words; strip and grid code removed"
```

---

### Task 10: The bar box and the new page

**Confidence:** 91%. The drawing is specified element by element (spec 3.1 to 3.5) and the mockup the owner approved fixes its look; the uncertainty is PDF height, which Task 13 measures against A14.

**Files:**
- Create: `src/youkelele/render/bar_svg.py`
- Modify: `src/youkelele/render/templates/sheet.html.j2` (the sections block and the CSS from `.section` down), `src/youkelele/render/html.py` (`render_html`)
- Test: `tests/test_bar_svg.py`, `tests/test_html.py`, `tests/test_stage_render.py`

**Interfaces:**
- Produces, in `render/bar_svg.py`:
  - `def bar_svg(bar: ScoreBar, meter: Meter, slots_per_bar: int, per_slot: int, first_in_line: bool, grey: bool, tab_rows: bool) -> str`: one inline SVG per bar: chord row (each name at its start slot, `N.C.` muted grey when none), the tab block when `tab_rows` (four lines, labelled A E C G when `first_in_line`, `fret` numbers at `TabNote.slot` on string `3 - string` from the top, a sustain line along the string through the following empty slots when `rings`), the stroke row (down, up, crossed arrows reused from the deleted strum box's `_down`, `_up`, `_muted` drawn in `#111`, or `#999` when `grey`; a sustain line from a ringing stroke through the following empty slots to the next stroke or the bar end), and the count row when `first_in_line` (`1 & 2 &` or `1 e & a`, bold on beats).
  - `def slot_px(slots_per_bar: int, bars_per_line: int) -> int`: the width that fits `bars_per_line` bars in 688 px: `min(28, 688 // (bars_per_line * slots_per_bar))`.
  - `def string_label_rows() -> list[str]`: `["A", "E", "C", "G"]`.
- Template: per section a header (`h2` display name, the `state` phrase in `.strum-label`, plus "written an octave up/down" when `octave_shift` is non-zero), then one `.line` div per `Line` holding its bar SVGs and, when `repeat > 1`, the `repeat_text` at the right edge; the legend line "Tab: A E C G top to bottom; numbers are frets." after the chord diagrams when any bar has tab; the old `.row`, `.cell`, `.block`, `.strum-box` CSS removed; `.line { display: flex; gap: 1.5mm; break-inside: avoid; margin-bottom: 1.5mm }`.
- `render_html(score)`: builds `fold_repeats(pack_lines(section, ...))` per section; `display_names` unchanged; the 1.5 `example`, `beside`, `grid`, `inherited_from` keys go.

- [ ] **Step 1: Write the failing tests**

```python
def test_bar_svg_draws_chords_strokes_and_count():
    bar = ScoreBar(index=0, chords=[_chord("D", 0, 4), _chord("G", 4, 8)], strokes=[Stroke(slot=0, kind="D"), Stroke(slot=2, kind="D"), Stroke(slot=4, kind="D"), Stroke(slot=6, kind="D"), Stroke(slot=7, kind="U")])
    svg = bar_svg(bar, M44, 8, 28, first_in_line=True, grey=False, tab_rows=False)
    assert svg.count('class="arrow down"') == 4 and svg.count('class="arrow up"') == 1
    assert ">D<" in svg and ">G<" in svg and _labels(svg) == ["1", "&", "2", "&", "3", "&", "4", "&"]
    assert svg.count('class="sustain"') == 4  # four strokes followed by an empty slot ring into it

def test_short_strokes_draw_no_sustain_and_grey_bars_use_grey_ink():
    svg = bar_svg(_bar_with(rings=False), M44, 8, 28, first_in_line=False, grey=True, tab_rows=False)
    assert 'class="sustain"' not in svg and 'stroke="#999"' in svg and 'stroke="#111"' not in svg.split("chord")[0]

def test_tab_block_puts_frets_on_the_right_string_lines():
    bar = ScoreBar(index=0, chords=[_chord("F", 0, 16)], strokes=[...], tab=[TabNote(slot=0, midi=60, string=1, fret=0), TabNote(slot=11, midi=63, string=1, fret=3)])
    svg = bar_svg(bar, M44, 16, 20, first_in_line=True, grey=False, tab_rows=True)
    assert 'class="fret" data-string="C"' in svg and svg.count('class="fret"') == 2 and ["A", "E", "C", "G"] == _string_labels(svg)
    assert _string_labels(bar_svg(bar, M44, 16, 20, first_in_line=False, grey=False, tab_rows=True)) == []

def test_render_html_prints_every_bar_in_order_with_state_phrases_and_no_strip():
    html = render_html(_score([_section("verse", 12, 0), _section("chorus", 4, 12, state="pattern uncertain", grey=True)]))
    assert html.count("<svg") >= 16 + len(diagrams) and "worked-example" not in html and "×" not in html
    assert "pattern uncertain" in html and "play " not in html

def test_render_html_folds_identical_lines_and_prints_the_tab_legend_once():
    html = render_html(_score([_section("outro", 24, 0, names=("G",))]))  # eight-bar lines, three identical
    assert html.count("play three times") == 1
    html_tab = render_html(_score([_section("verse", 8, 0, tab=True, state="riff")]))
    assert html_tab.count("Tab: A E C G top to bottom; numbers are frets.") == 1 and "written an octave" not in html_tab

def test_v15_score_fixture_renders():
    html = render_html(load_model(FIXTURES / "v15_score.json", Score))
    assert "<svg" in html  # bars with empty strokes draw their chords' slots as strokes, all ringing
```

(For a 1.5 `score.json` whose bars have empty `strokes`, `render_html` derives strokes from the chords' `slots`, all ringing, before packing lines.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_bar_svg.py tests/test_html.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement `render/bar_svg.py`, the template and `render_html`.**

- [ ] **Step 4: Run the render suites and the end-to-end test, then look at one real sheet**

Run: `uv run pytest tests/test_bar_svg.py tests/test_html.py tests/test_stage_render.py tests/test_end_to_end.py -q`
Expected: PASS. Then `uv run youkelele run "<All Fired Up's source from runs\all-fired-up\manifest.json>" --from strums --runs-dir %TEMP%\youkulele-v16-smoke` and open the PDF: bars in order, the Verse 2 header once, 90-97 grey, no strip. Note the page count against A14; do not tune anything.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/render/bar_svg.py src/youkelele/render/templates/sheet.html.j2 src/youkelele/render/html.py tests
git commit -m "feat: the bar box page: chord, strokes, sustain and tab inside every bar, count once per line"
```

---

### Task 11: `evaluate` and the compare harness on bars

**Confidence:** 94%. Additive output over fields the earlier tasks define.

**Files:**
- Modify: `src/youkelele/evaluate.py` (`SectionDiag`, `_section_diags`, `_section_line`, `compare_runs`, `format_comparison`, `_load_riffs`)
- Test: `tests/test_evaluate.py`

**Interfaces:**
- `SectionDiag` gains `candidate`, `score_majority`, `score_medoid`, `unit`, `pitch_change_share`, `rings`, `ring_decay_db`, `member_patterns: list[tuple[int, int, str, bool]]` (start, end, pattern text, prints own), `riff_gate: tuple[float, float, float, bool, str | None] | None` (agreement, support, named, printable, reason).
- `_section_line` appends: `vote medoid (0.63 vs 0.58)` or `vote majority (0.55 vs 0.54)`, `unit 2` when 2, `pcs 0.72`, `rings 2.1dB` or `short 13.5dB`, then one indented line per member that prints its own pattern (`    member 90-97 prints own xUDxxxx- (uncertain)`), then `    riff gate: agreement 0.74 support 0.80 named 0.91 printable` or `... not transcribed (agreement 0.52 < 0.70)`.
- `compare_runs`: pairs bars by index when the grids match and reports, per section pair, `pattern_changes: int` (bars whose printed pattern differs) and `candidate_changed: bool`; `format_comparison` prints `patterns changed in N bars` and `vote: majority -> medoid` on the section line. A run without `bars` (1.5) is compared through `backfill_bars`.

- [ ] **Step 1: Write the failing tests** (extend the run-folder fixtures `tests/test_evaluate.py` already builds)

```python
def test_section_line_prints_the_vote_the_ring_and_member_patterns():
    text = format_report(evaluate_run(run_dir))
    assert "vote medoid (0.63 vs 0.58)" in text and "rings 2.1dB" in text and "member 8-12 prints own D------- (uncertain)" in text

def test_section_line_prints_the_riff_gate():
    assert "riff gate: agreement 0.74 support 0.80 named 0.91 printable" in text

def test_compare_counts_bars_whose_pattern_changed_and_the_vote_switch():
    c = compare_runs(run_a, run_b)
    assert c.deltas[0].pattern_changes == 4 and c.deltas[0].candidate_changed
    assert "patterns changed in 4 bars" in format_comparison(c) and "vote: majority -> medoid" in format_comparison(c)

def test_compare_backfills_a_v15_run(tmp_path):
    # run_a is a copy of the v15 fixtures without bars: no exception, pattern_changes computed
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_evaluate.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement.**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest tests/test_evaluate.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/evaluate.py tests/test_evaluate.py
git commit -m "feat: evaluate prints the vote, the ring flag, member patterns and the riff gate; compare pairs bars"
```

---

### Task 12: Version, README and the limitation text

**Confidence:** 96%

**Files:**
- Modify: `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock` (`uv lock`), `README.md` ("How it works" stage list gains the riff stage; "Known limitations" gains the two-guitar sentence from spec 5.6 and replaces the page-count line; "Project history" gains the 1.6 line with spec and validation links; the sample sheet line says version 1.6 once Task 13 regenerates it), `tests/test_readme.py`

**Interfaces:** none.

- [ ] **Step 1: Update `tests/test_readme.py`** to assert `"1.6" in text and "0.7.0" in text`, that the stage table lists `riff`, and that the limitations contain "their notes interleave".

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_readme.py -q`
Expected: FAIL.

- [ ] **Step 3: Bump the version in the three files** (`uv lock` after `pyproject.toml`), edit the README sections named above, with the two-guitar sentence verbatim from spec 5.6.

- [ ] **Step 4: Run the full fast suite**

Run: `uv run pytest -q -W error -m "not slow"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/youkelele/__init__.py uv.lock README.md tests/test_readme.py
git commit -m "docs: version 0.7.0; README stage list, limitation and history for 1.6"
```

---

### Task 13: Validation on eight songs and one blind song

**Confidence:** 92%. The expectations are written in spec 8; the blind song is unknown by design (A15); page counts are estimated, not promised (A14).

**Files:**
- Create: `docs/superpowers/specs/2026-10-05-v1-6-validation.md` (in the worktree; it travels with the code)
- Modify: `README.md` (the history link and the sample sheet line); the eight run folders under `C:\Users\gethi\sources\Youkulele\runs\` (re-runs); `%TEMP%\youkulele-v16-validation\` (baselines, scratch); `%TEMP%\youkulele-ear-v16\` (clips)

**Interfaces:** consumes everything above through the CLI (`uv run youkelele run`, `status`, `evaluate`, `evaluate --compare`).

- [ ] **Step 1: Copy the baselines** of all eight 1.5 folders (`02_grid` to `07_render`, `manifest.json`, and `evaluate` output) to `%TEMP%\youkulele-v16-validation\baseline\<folder>\`.

- [ ] **Step 2: Re-run** the eight songs `--from strums` in place (the stage renumbering means `05_arrange` to `07_render` are replaced by `05_riff` to `08_render`; remove the stale 1.5 folders `05_arrange`, `06_score`, `07_render` from each run folder first and say so in the record). Then the blind song, chosen by the owner for a prominent single-line riff, from ingest into its own folder. Record each run's log.

- [ ] **Step 3: Measure every expectation in spec 8**: byte comparison of `grid.json`, the chord events and `bar_onsets` against the baselines; `compare_runs` baseline against new for the ten sections expected to change and the five held fixed; the member patterns of All Fired Up's Verse 2 and Wet Leg's Verse 4; per-section ring medians against the 5 dB threshold (none within 1 dB); riff flags against the list; the gate figures and tab on Need You Tonight, and the not-transcribed sections; page counts against 1.5 and the A14 estimate; every page rasterised and looked at. Yes or no per row, with the figure. Anything that misses is recorded, not tuned.

- [ ] **Step 4: Prepare the ear clips** under `%TEMP%\youkulele-ear-v16\<song>\` as the 1.5 validation did (guitar stem with a click on each printed stroke, named for what each tests): every section whose pattern changed, the three member patterns of All Fired Up's Verse 2, five held-stroke bars and five short-stroke bars, every bar of printed tab synthesised as plucks at the song's tempo (the riff-pitch spike's `synth_riffs.py` shows how), and the blind song's riff sections. List them in the record with one line each.

- [ ] **Step 5: Write the validation document**: runs and baselines; the expectations table; per song (pattern changes with their vote scores, member patterns, ring medians, riff flags, gate figures, pages 1.5 to 1.6); the blind song; "What to improve next", ranked; the clip list; the assumptions table of spec 9 with each status after the runs. Regenerate the README's sample sheet from the project's own test song and update its version line.

- [ ] **Step 6: Verify, link, commit**

Run: `uv run pytest -q -W error -m "not slow"` and `uv run pytest -q -m slow`.
Expected: both green. Then:

```bash
git add docs/superpowers/specs/2026-10-05-v1-6-validation.md README.md docs/sample
git commit -m "docs: validate version 1.6 on eight real songs and one blind song"
```
