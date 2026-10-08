# Ukulele Tab Chain 1.8 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the four measured defects (the rest window, the two-pair vote union, the bass-on-stem swap, the key candidate gate), make certainty a claim the bars support, resolve title and artist from evidence, state on every sheet what is not measured, and give `evaluate` truth files and metrics to score patterns, riffs, rests, key and credits.

**Architecture:** `music/rests.py` measures on an end-trimmed window; `music/vote.py` and `music/as_played.py` gain a pair floor and a slot-support floor; new `music/candidates.py` and `music/rhythm_distance.py` measure the nearest rival; new `music/bleed.py` reads the bass stem's landing shares per member and the strums stage gates on them; `music/key.py` gains a diatonic-set veto with a relative-key hedge and a key relation; `titles.py` gains a credits resolver that ingest and the run-folder namer share; the score builder and renderer add a state phrase, a partial pickup bar, two legend lines and a provenance line; a new `truth.py` parses tracked truth files that `evaluate` scores against; `scripts/band_sweep.py` sweeps a constant with leave-one-song-out.

**Tech Stack:** Python 3.12 via uv, pydantic 2, numpy, scipy, librosa (`stft`, `resample`), mir_eval 0.8.2 (`key.weighted_score`), Jinja2 and inline SVG, Playwright Chromium PDF, pytest.

**Spec:** `docs/superpowers/specs/2026-10-08-ukulele-tab-chain-v1-8-design.md` (cited as "spec N"). Research under `docs/superpowers/research/2026-10-08-v1-8/` (the four assumption-pass records) and the reviews under `research_notes/Weak music measurements research/`. The 1.7 plan at `docs/superpowers/plans/2026-10-06-ukulele-tab-chain-v1-7.md` names the interfaces this plan extends.

## Global Constraints

- Schema version 2 stays for `strums.json` and `score.json`; every new field has a default, so every 1.3 to 1.7 artifact loads, and a 1.7 `score.json` renders with the two legend lines and no other change (spec 11).
- Nothing reads a song's title, id, duration or any other identity; every rule applies to any input; unit tests use synthetic inputs or measured numbers as examples of a rule (spec 1, Generality).
- `grid.json` and `bar_onsets` are byte-identical to 1.7 on every re-run song; the chord events are identical except `TonicVotes` (spec 12, expectation 1): nothing in `music/onsets.py`, `music/recall.py`, `music/relabel.py`, `music/riff.py`, `music/pitch.py`, `music/riff_line.py`, the recall gate, the section plan, the riff gate, or the grid stage changes.
- Constants, verbatim from the spec: `PERIOD2_MIN_PAIRS = 3`; `MIN_SLOT_SUPPORT = 2`; `MIN_VOTE_BARS = 4` (equal to `MIN_SECTION_BARS`); `BLEED_LOW_HZ = 250`; `BASS_STEM_MAX = 0.05`; `OWN_LOW_SHARE_MIN = 0.40`; bleed STFT `n_fft 4096`, `hop_length 2048`; `SET_VETO_MARGIN = 0.10`; `REST_RATIO_MIN`, `REST_LOW_SHARE_MIN`, `HYBRID_DELTA`, `PERIOD2_MARGIN`, `STRIKE_SHARE`, `UNCERTAIN_BELOW`, `EXPLAINED_BELOW`, `CHANCE_ALPHA`, `MEMBER_AGREE`, `TONIC_MIN_SHARE`, `KEY_HEDGE_MARGIN`, `MODE_TIE_MARGIN` unchanged. There is no `TOP2_MARGIN` and no `ATTACK_RISE_DB` (spec 4.2, 5.5).
- Page copy, verbatim (spec 3.1, 3.3, 3.4): legend lines "Stroke length is not measured: hold or damp each stroke as the record does." and "Arrows follow the hand: down on the beat, up between. Direction is not read from the recording."; state phrase "guitar not separated here"; provenance line "uploaded by <uploader>".
- README lines, verbatim (spec 10): "Stroke length and stroke direction are not measured; the legend says so." and "When the separator puts the bass on the guitar stem, the section prints grey under 'guitar not separated here'; the strokes are the bass line's rhythm."
- The chance test (`chance_p`, `structure_test`) is unchanged (spec 5.3).
- UK spelling; no em-dashes; no song lyrics in code, tests or documents; no time or effort estimates in documents.
- Package version 0.9.0 in `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock`; the eleven manifests at 0.9.0 after validation.
- Run folders under `C:\Users\gethi\sources\Youkulele\runs\` are touched only by Task 14.
- Work happens in a worktree cut from main HEAD at `C:\Users\gethi\sources\Youkulele\.claude\worktrees\v1-8` on branch `worktree-v1-8`; the spec and this plan live on main and are amended there. Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. Plain separate git commands only. Write files with the Write tool, not a bash heredoc.

## Review Focus

1. A run whose `01_separate/stems/bass.wav` is missing (a folder separated before six stems, or a hand-trimmed run): the strums stage must refuse through the existing `requires` check with the file's name, not raise inside `bleed_figures`. Test in Task 6.
2. A pickup bar in a meter whose slots do not divide by its beats evenly (3/4 at six slots, a two-beat pickup): `pickup_slots` must be an integer in `[1, slots_per_bar - 1]` and the box must draw at least one column. Test in Task 7.
3. A title whose tag word sits inside brackets in the tail ("The Cars - You Might Think [Official Video]") must still split, while "Song - Live at Wembley" must not. Test in Task 9.
4. A chord stream of only `N` events, or fewer than `MIN_CHORD_EVENTS`: the set veto must leave the mix key as it is and never divide by a zero total. Test in Task 8.
5. A member every bar of which rests, or a member with one voted bar: `candidates` and `top2` must return `None` margins rather than raise, and the member prints grey by `MIN_VOTE_BARS`. Test in Task 4 and Task 6.

---

### Task 1: Schema fields for the vote figures, the bass gate, the set votes, the credits and the partial pickup

**Confidence:** 96%. Every field is a defaulted addition to an existing pydantic model; the 1.7 fixture-load tests show the pattern.

**Files:**
- Modify: `src/youkelele/schemas.py` (`SectionPattern` after `riff_rule`; `ScoreBar` after `rests`; `TonicVotes`; `SourceInfo`; `Score`)
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces:
  - `SectionPattern`: `voted_bars: list[int] = []`, `dropped_bars: list[int] = []` (grid bar indices), `top2_margin: float | None = None`, `runner_up_vector: list[StrikeClass] | None = None`, `confidence_all_bars: float | None = None`, `chance_p_all_bars: float | None = None`, `bass_on_stem: bool = False`, `low_mix_share_bass: float | None = None`, `low_mix_share_source: float | None = None`, `low_own_share: float | None = None`, `bass_stem_ratio: float | None = None`, each with a one-line comment naming its spec section and "None before 1.8".
  - `ScoreBar.pickup_slots: int | None = None` (the slot columns a pickup bar draws, spec 3.2; None for a full bar and before 1.8).
  - `TonicVotes`: `set_tonic: str | None = None`, `set_share_best: float | None = None`, `set_share_decided: float | None = None`; `decided_by: Literal["agreement", "pair rule", "mix", "score", "set"] | None`.
  - `SourceInfo`: `uploader`, `channel`, `credited_artist`, `credited_track`, `artist_source`, `title_source`, `provenance`, all `str | None = None` (`provenance` is the uploader the sheet prints after "uploaded by", or None).
  - `Score.provenance: str | None = None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_section_pattern_1_8_fields_default():
    p = SectionPattern(section=0, slots=["-"] * 8, confidence=0.0, bar_repeat=0.0, uncertain=True, no_instrument=False, inherited_from=None)
    assert p.voted_bars == [] and p.dropped_bars == [] and p.top2_margin is None
    assert p.runner_up_vector is None and p.confidence_all_bars is None and p.chance_p_all_bars is None
    assert p.bass_on_stem is False and p.low_own_share is None and p.bass_stem_ratio is None

def test_score_bar_pickup_slots_defaults_to_none():
    assert ScoreBar(index=0, chords=[]).pickup_slots is None

def test_tonic_votes_admit_set():
    v = TonicVotes(decided_by="set", set_tonic="G", set_share_best=0.995, set_share_decided=0.756)
    assert v.set_tonic == "G" and TonicVotes().set_tonic is None

def test_source_info_and_score_provenance_default_to_none():
    # build a SourceInfo as tests/test_stage_ingest.py does; assert the seven new fields are None
    # and Score(...).provenance is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schemas.py -v -k "1_8 or pickup_slots or admit_set or provenance"`
Expected: FAIL with `ValidationError` or `AttributeError`

- [ ] **Step 3: Add the fields as the Interfaces block specifies**

- [ ] **Step 4: Run the whole suite to verify nothing else changed**

Run: `uv run pytest -q`
Expected: all pass (the 1.5, 1.6 and 1.7 fixtures still load)

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/schemas.py tests/test_schemas.py
git commit -m "feat(schema): vote support and rival figures, the bass gate, set votes, credits provenance, pickup slots"
```

---

### Task 2: The rest rule measures on the end-trimmed window

**Confidence:** 96%. The window is the assumption pass's exact measurement (`assumption-pass-rests.md` A1); the call sites are two list comprehensions in the strums stage.

**Files:**
- Modify: `src/youkelele/music/rests.py` (`bar_energy_ratio`, `bar_low_share`, a new `bar_window`)
- Modify: `src/youkelele/stages/strums.py:497-498` (the `energy` and `low` comprehensions pass `slots`)
- Test: `tests/test_rests.py`; `tests/test_html.py` and `tests/test_stage_strums.py` wherever the two functions are called

**Interfaces:**
- Produces, in `music/rests.py`:
  - `bar_window(bar: Bar, slots_per_bar: int) -> tuple[float, float]`: `(bar.start, bar.end - half)` with `half = (bar.end - bar.start) / slots_per_bar / 2`; never below `bar.start`.
  - `bar_energy_ratio(stem, mix, sr, bar, slots_per_bar: int) -> float` and `bar_low_share(stem_22k, bar, slots_per_bar: int) -> float`: as 1.7 built them, sliced on `bar_window`.
  - `bar_holds` and `resample_for_rests` unchanged.
- Consumes: nothing new.

- [ ] **Step 1: Write the failing tests** (`sr = 22050`, `BAR` 0.5 to 2.5 s with eight slots: a slot is 0.25 s, the window ends at 2.375 s)

```python
def test_bar_window_trims_half_a_slot_at_the_end_only():
    assert bar_window(BAR, 8) == (0.5, 2.375)

def test_energy_in_the_last_half_slot_belongs_to_the_next_bar():   # the Chelsea Dagger 7 and 12 case
    stem = np.zeros_like(mix); stem[int(2.4 * SR):int(2.5 * SR)] = tone[int(2.4 * SR):int(2.5 * SR)]
    assert bar_energy_ratio(stem, mix, SR, BAR, 8) == 0.0 and bar_low_share(stem, BAR, 8) == 0.0

def test_energy_just_before_the_bar_line_is_not_counted():        # the ringing previous stroke
    stem = np.zeros_like(mix); stem[int(0.4 * SR):int(0.5 * SR)] = tone[int(0.4 * SR):int(0.5 * SR)]
    assert bar_energy_ratio(stem, mix, SR, BAR, 8) == 0.0

def test_a_low_tone_bar_still_holds_on_the_trimmed_window():
    assert bar_energy_ratio(tone, tone, SR, BAR, 8) == pytest.approx(1.0) and bar_low_share(tone, BAR, 8) > 0.9
```

Keep the 1.7 tests, adding the `slots_per_bar` argument.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_rests.py -v`
Expected: FAIL with `TypeError` on the new argument

- [ ] **Step 3: Implement `bar_window` and thread `slots_per_bar` through both measurements; pass `slots` at the two call sites in the strums stage**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest -q`
Expected: PASS; `tests/fixtures/v16_*.json` are not regenerated here (their stored figures are data, not recomputed by tests). If a test recomputes a fixture's rest figure and fails, record the bar and the old and new values in the commit message and update the expected value.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/rests.py src/youkelele/stages/strums.py tests/test_rests.py
git commit -m "fix(rests): measure a bar's energy and low share on the window trimmed half a slot at its end"
```

---

### Task 3: The vote needs three pairs and two strikes per printed slot

**Confidence:** 95%. Both rules are one condition each; the assumption pass (`assumption-pass-vote.md` A4) measured their effect on all 100 members.

**Files:**
- Modify: `src/youkelele/music/vote.py` (`PERIOD2_MIN_PAIRS`, `unit_and_phase`, `VoteResult`, `choose_pattern`)
- Modify: `src/youkelele/music/as_played.py` (`MIN_SLOT_SUPPORT`, `majority_vector`, `MIN_VOTE_BARS`)
- Test: `tests/test_vote.py`, `tests/test_as_played.py`

**Interfaces:**
- Produces:
  - `vote.py`: `PERIOD2_MIN_PAIRS = 3` (comment: band 3 to 4; ear-passed two-bar members have four to eight pairs, spec 5.1). `unit_and_phase` returns `(1, 0)` when `len(_pairs(bars, start % 2)) < PERIOD2_MIN_PAIRS`. `VoteResult` gains `voted: list[int]` and `dropped: list[int]`, positions into the `bars` argument (unit 1: every position; unit 2: the positions the pairs cover, and the rest dropped). `choose_pattern` fills them.
  - `as_played.py`: `MIN_SLOT_SUPPORT = 2`; `majority_vector` keeps a slot only when `strikes > threshold * n and strikes >= MIN_SLOT_SUPPORT`. `MIN_VOTE_BARS = MIN_SECTION_BARS` (4) with a comment pointing at spec 5.4; the stage applies it (Task 6).
- Consumes: `_pairs` as it is.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_vote.py
def test_two_pairs_are_not_a_two_bar_vote():          # four alternating bars, margin clears, pairs 2
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 2
    assert unit_and_phase(bars) == (1, 0)

def test_three_pairs_are_a_two_bar_vote():
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 3
    assert unit_and_phase(bars) == (2, 0)

def test_vote_result_records_voted_and_dropped_positions():
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 3 + [list("S-S-S-S-")]
    r = choose_pattern(bars)
    assert r.unit == 2 and r.voted == [0, 1, 2, 3, 4, 5] and r.dropped == [6]
    r1 = choose_pattern(bars[:5])
    assert r1.unit == 1 and r1.voted == [0, 1, 2, 3, 4] and r1.dropped == []

# tests/test_as_played.py
def test_a_slot_struck_once_never_prints_at_two_bars():
    assert majority_vector([list("S-------"), list("--S-----")]) == list("--------")

def test_a_slot_struck_twice_prints_at_two_bars():
    assert majority_vector([list("S-S-----"), list("S-------")]) == list("S-------")

def test_slot_support_does_not_bind_at_six_bars():      # six bars: >n/3 already needs three
    bars = [list("S-S-S-S-")] * 4 + [list("S-------")] * 2
    assert majority_vector(bars) == list("S-S-S-S-")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_vote.py tests/test_as_played.py -v`
Expected: FAIL (`unit_and_phase` returns 2; `VoteResult` has no `voted`; the union prints)

- [ ] **Step 3: Implement the two constants, the pair floor, the support floor and the `VoteResult` fields**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest -q`
Expected: PASS. `tests/test_riff_line.py` shares `_pairs`; it is untouched.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/vote.py src/youkelele/music/as_played.py tests/test_vote.py tests/test_as_played.py
git commit -m "fix(vote): a two-bar vote needs three pairs, a printed slot two strikes; voted and dropped bars recorded"
```

---

### Task 4: The nearest rival, measured: `music/candidates.py` and `music/rhythm_distance.py`

**Confidence:** 92%. The candidate set and the score are spec 5.5's words over functions that exist (`medoid`, `_topped_vote`, `_pairs`, `jaccard`); swap distance is Toussaint's definition, which the assumption pass implemented once already.

**Files:**
- Create: `src/youkelele/music/candidates.py`, `src/youkelele/music/rhythm_distance.py`
- Test: `tests/test_candidates.py`, `tests/test_rhythm_distance.py`

**Interfaces:**
- Produces, in `music/rhythm_distance.py`:
  - `swap_distance(a: Sequence[StrikeClass], b: Sequence[StrikeClass]) -> int`: mutes count as strikes; with equal onset counts, the sum over sorted onset positions of the absolute position differences; with unequal counts, `len(a)`.
- Produces, in `music/candidates.py`:
  - `@dataclass(frozen=True) Candidate(name: str, vector: list[StrikeClass], score: float)`; names: `majority_1`, `medoid_1`, `majority_2`, `medoid_2`, `bar_best`, `bar_second`.
  - `candidate_set(bars: Sequence[Sequence[StrikeClass]], allow_two_bar: bool, phase: int) -> list[Candidate]`: the one-bar `_topped_vote` and `medoid`; when `allow_two_bar`, the same over `_pairs(bars, phase)`; and the two voted units (bars, or pairs when `allow_two_bar`) with the highest mean Jaccard to the other units. A candidate's score is its mean Jaccard agreement with every voted unit of its own length. Empty `bars` gives `[]`.
  - `top2(printed: Sequence[StrikeClass], cands: Sequence[Candidate]) -> tuple[float | None, list[StrikeClass] | None]`: the printed vector's score (the candidate whose vector equals it, else its mean Jaccard computed the same way) minus the best score among candidates whose vector differs; `(None, None)` when no candidate differs or `cands` is empty.
- Consumes: `jaccard`, `_topped_vote` from `as_played.py`; `medoid`, `_pairs` from `vote.py`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_rhythm_distance.py
def test_swap_distance_counts_a_one_slot_push_as_one():
    assert swap_distance(list("S-S-S-S-"), list("S-S-S--S")) == 1
def test_swap_distance_with_unequal_counts_is_the_slot_count():
    assert swap_distance(list("S-S-S-S-"), list("S-S-S---")) == 8
def test_swap_distance_treats_mutes_as_strikes_and_is_symmetric():
    assert swap_distance(list("x-S-"), list("S-x-")) == 0 and swap_distance(list("S---"), list("---S")) == swap_distance(list("---S"), list("S---"))

# tests/test_candidates.py
def test_candidate_set_has_six_names_with_two_bar_and_four_without():
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 3
    assert [c.name for c in candidate_set(bars, True, 0)] == ["majority_1", "medoid_1", "majority_2", "medoid_2", "bar_best", "bar_second"]
    assert [c.name for c in candidate_set(bars, False, 0)] == ["majority_1", "medoid_1", "bar_best", "bar_second"]

def test_top2_margin_is_printed_minus_best_different():
    bars = [list("S-S-S-S-")] * 5 + [list("S-S-S-SS")]
    cands = candidate_set(bars, False, 0)
    margin, runner = top2(list("S-S-S-S-"), cands)
    assert runner == list("S-S-S-SS") and margin == pytest.approx(cands[0].score - [c for c in cands if c.vector == runner][0].score)

def test_top2_is_none_when_every_candidate_agrees_or_there_are_no_bars():
    assert top2(list("S-S-S-S-"), candidate_set([list("S-S-S-S-")] * 4, False, 0)) == (None, None)
    assert candidate_set([], False, 0) == [] and top2(list("S-S-S-S-"), []) == (None, None)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_candidates.py tests/test_rhythm_distance.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement both modules as the Interfaces block specifies**

Module docstrings cite spec 5.5 and say the margin is written, not used.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_candidates.py tests/test_rhythm_distance.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/candidates.py src/youkelele/music/rhythm_distance.py tests/test_candidates.py tests/test_rhythm_distance.py
git commit -m "feat(vote): candidate set, top-two margin and swap distance, measured for the harness"
```

---

### Task 5: The bass-on-stem figures in `music/bleed.py`

**Confidence:** 94%. The four figures and the gate are the assumption pass's exact computation (`assumption-pass-bass-gate.md`); the constants and bands are the spec's.

**Files:**
- Create: `src/youkelele/music/bleed.py`
- Test: `tests/test_bleed.py`

**Interfaces:**
- Produces, in `music/bleed.py`:
  - `BLEED_LOW_HZ = 250`, `BASS_STEM_MAX = 0.05`, `OWN_LOW_SHARE_MIN = 0.40`, `_N_FFT = 4096`, `_HOP = 2048`, each with a one-line band comment from spec 6 (bass ratio 0.002 to 0.317; own share 0.376 to 0.462, one positive song).
  - `@dataclass(frozen=True) BleedFigures(low_mix_share_bass: float, low_mix_share_source: float, low_own_share: float, bass_stem_ratio: float)`.
  - `bleed_figures(source: np.ndarray, bass: np.ndarray, mix: np.ndarray, sr: int, start: float, end: float) -> BleedFigures`: over the samples in `[start, end)` seconds, STFT power of the three signals (`n_fft 4096`, `hop 2048`); the low band is the bins whose centre frequency is below 250 Hz; shares as spec 6 defines them, each with `1e-12` in the denominator; `bass_stem_ratio` is `rms_ratio(bass, mix)` over the same samples. A slice shorter than one frame is zero-padded to one.
  - `bass_on_stem(f: BleedFigures) -> bool`: `f.bass_stem_ratio <= BASS_STEM_MAX and f.low_own_share >= OWN_LOW_SHARE_MIN`.
- Consumes: `rms_ratio` from `music/onsets.py`.

- [ ] **Step 1: Write the failing tests** (`sr = 22050`, three-second signals; `low` a 100 Hz tone, `high` a 2 kHz tone, both at amplitude 0.3)

```python
def test_bass_on_the_source_stem_with_an_empty_bass_stem_fires():
    f = bleed_figures(low, zeros, low, SR, 0.0, 3.0)
    assert f.bass_stem_ratio == 0.0 and f.low_own_share > 0.9 and f.low_mix_share_source > 0.9 and bass_on_stem(f)

def test_bass_on_the_bass_stem_does_not_fire():
    f = bleed_figures(high, low, low + high, SR, 0.0, 3.0)
    assert f.bass_stem_ratio > 0.3 and f.low_own_share < 0.05 and f.low_mix_share_bass > 0.9 and not bass_on_stem(f)

def test_a_bright_source_over_an_empty_bass_stem_does_not_fire():   # the bridge-arpeggio limit
    f = bleed_figures(high, zeros, high, SR, 0.0, 3.0)
    assert f.bass_stem_ratio == 0.0 and f.low_own_share < 0.05 and not bass_on_stem(f)

def test_gate_thresholds_are_inclusive():
    assert bass_on_stem(BleedFigures(0, 0, 0.40, 0.05)) and not bass_on_stem(BleedFigures(0, 0, 0.39, 0.05)) and not bass_on_stem(BleedFigures(0, 0, 0.40, 0.0501))

def test_a_span_shorter_than_a_frame_still_measures():
    f = bleed_figures(low, zeros, low, SR, 0.0, 0.05)
    assert 0.0 <= f.low_own_share <= 1.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_bleed.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `music/bleed.py` as the Interfaces block specifies**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_bleed.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/bleed.py tests/test_bleed.py
git commit -m "feat(bleed): low-band landing shares per span and the bass-on-stem gate"
```

---

### Task 6: The strums stage earns certainty, gates on the bass stem and writes the new figures

**Confidence:** 92%. Every rule is one of spec 4.4, 5.4, 5.5 or 6 on code the assumption pass reconstructed exactly (its scripts reproduce all 100 members' rows); the one decision made here is where the gate runs relative to the rest rule, stated below.

**Files:**
- Modify: `src/youkelele/stages/strums.py` (`requires`, `_Member`, `new_member`, `_vote_member`, a new `_bleed_member`, `_riff_test`, `_section_pattern`)
- Test: `tests/test_stage_strums.py` (the `_ctx` helper writes `separate/stems/bass.wav`, silent by default)

**Interfaces:**
- Consumes: Task 2's `bar_energy_ratio(stem, mix, sr, bar, slots)` and `bar_low_share(stem_22k, bar, slots)`; Task 3's `VoteResult.voted`, `.dropped`, `MIN_VOTE_BARS`; Task 4's `candidate_set`, `top2`; Task 5's `bleed_figures`, `bass_on_stem`, `BleedFigures`; Task 1's fields.
- Produces:
  - `StrumsStage.requires` gains `"separate/stems/bass.wav"`; `run` reads it as it reads the other stems (same rate check, same truncation to `n`).
  - `_Member` gains `voted_bars: list[int]`, `dropped_bars: list[int]` (grid indices, mapped from `VoteResult.voted` and `.dropped` through `member.holding`), `top2_margin: float | None`, `runner_up_vector: list[StrikeClass] | None`, `confidence_all_bars: float | None`, `chance_p_all_bars: float | None`, `bleed: BleedFigures | None`, `bass_on_stem: bool`.
  - `new_member` computes `member.bleed = bleed_figures(y, bass, mix, sr, bars[start].start, bars[trimmed - 1].end)` and `member.bass_on_stem = bass_on_stem(member.bleed)` before `holding`; when the gate fires, `holding` keeps the bars with `energy[i] >= REST_RATIO_MIN` (the low-share test skipped, spec 6). Decision: the gate runs on the member's whole analysed span, the same span `section_has_instrument` reads, so the two cuts see one signal.
  - `_vote_member` also computes `all_bars = [classes[b] for b in range(member.start, member.analysed_end)]`, `member.confidence_all_bars, _, _ = member_figures(all_bars, vote.vector, vote.unit, slots)` and `_, member.chance_p_all_bars, _ = structure_test(all_bars, vote.vector, seed=member.start)` with `structured_all` from the same call; `member.uncertain` is True when any of: the 1.7 conditions on the holding bars; `confidence_all_bars < floor`; `not structured_all`; `len(member.voted_bars) < MIN_VOTE_BARS`; `member.bass_on_stem`. It fills `top2_margin` and `runner_up_vector` from `top2(vote.vector, candidate_set(bars, vote.unit == 2, phase))` with `phase` from `unit_and_phase(bars)`.
  - `_riff_test` sets `member.riff = False` after computing the shares when `member.bass_on_stem`.
  - `_section_pattern` writes every new `SectionPattern` field from the longest member.
- Decision recorded for the spec: when the gate fires, the rest rule still runs on energy alone, so a silent bar in a gated member still rests.

- [ ] **Step 1: Write the failing tests** (extend `_ctx` to write `bass.wav`, silent unless a test passes `bass=`)

```python
def test_stage_refuses_without_a_bass_stem(tmp_path):
    # build the context without bass.wav; expect the stage's requires check to name "separate/stems/bass.wav"

def test_a_member_with_a_low_source_and_an_empty_bass_stem_is_gated(tmp_path):
    # source stem a 100 Hz tone with strikes, bass.wav silent: the pattern has bass_on_stem True,
    # uncertain True, riff False, and the four figures written (bass_stem_ratio == 0.0)

def test_a_gated_member_still_rests_its_silent_bars(tmp_path):
    # the same, with two silent bars inside the member: those bars carry rests True

def test_certainty_needs_the_full_span_too(tmp_path, monkeypatch):
    # a member of eight bars, four of them resting noise bars the detector fires on; the holding
    # four vote certain; the all-bars reading is uncertain: the pattern is uncertain and
    # confidence_all_bars < confidence

def test_fewer_than_four_voted_bars_prints_grey(tmp_path):
    # a three-bar member with a clean pattern: uncertain True, voted_bars has three entries

def test_dropped_bars_are_recorded_for_a_two_bar_vote(tmp_path):
    # seven alternating bars: unit 2, voted_bars six grid indices, dropped_bars the seventh

def test_top2_margin_and_runner_up_are_written(tmp_path):
    # five identical bars plus one with a push: top2_margin is a float and runner_up_vector differs from slots
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stage_strums.py -v -k "bass or certainty or fewer_than or dropped or top2"`
Expected: FAIL (`requires` lacks the bass stem; the fields are defaults)

- [ ] **Step 3: Implement the stage changes as the Interfaces block specifies**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest -q`
Expected: PASS. Tests that build a strums context now need `bass.wav`: add it to the helper, not to each test.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/stages/strums.py tests/test_stage_strums.py
git commit -m "feat(strums): certainty on both readings and four voted bars, the bass-on-stem gate, the rival figures written"
```

---

### Task 7: The page: the state phrase, the partial pickup bar, the legend lines and the provenance line

**Confidence:** 91%. The state phrase and legend lines follow the 1.7 patterns exactly; the partial pickup bar is the one new drawing, and its column mapping is decided below from `quantise_bar`'s behaviour (a pickup's `n` slots span its short duration), which was read while planning.

**Files:**
- Modify: `src/youkelele/music/score_builder.py` (`STATE_NOT_SEPARATED`, `_state`, the `ScoreBar` construction, `build_score`'s `Score(...)`)
- Modify: `src/youkelele/render/bar_svg.py` (`_Cols.first`, `_stroke_row`, `_count_row`, the frame, `bar_svg`)
- Modify: `src/youkelele/render/html.py` (`STROKE_LEGEND`, `DIRECTION_LEGEND`, `_section_lines`, `render_html`), `src/youkelele/render/templates/sheet.html.j2` (the provenance line after the artist; the two legend lines after `tab_legend`)
- Modify: `src/youkelele/render/lines.py` (`_bar_key` includes `pickup_slots`)
- Test: `tests/test_score_builder.py`, `tests/test_bar_svg.py`, `tests/test_html.py`, `tests/test_render_lines.py`

**Interfaces:**
- Consumes: Task 1's `ScoreBar.pickup_slots`, `Score.provenance`, `SourceInfo.provenance`, `SectionPattern.bass_on_stem`.
- Produces:
  - `score_builder.py`: `STATE_NOT_SEPARATED = "guitar not separated here"`; `_state` returns it when `pattern.bass_on_stem`, after the no-instrument check and before the tab check. `pickup_slots(bar: Bar, slots_per_bar: int, meter: Meter) -> int | None`: None unless `bar.pickup and len(bar.beats) < meter.numerator`; else `max(1, min(slots_per_bar - 1, len(bar.beats) * max(1, slots_per_bar // meter.numerator)))`. `pickup_column(j: int, n: int, k: int) -> int`: `n - k + (j * k) // n`, the column a full-bar cell `j` of `n` maps to when only `k` columns draw. The builder maps a pickup bar's strokes and chord `start_slot`s through it, keeping the first stroke that lands on a column; a `ScoreChord`'s `slots` list is left at full length (the renderer reads `start_slot` only). `Score.provenance = source.provenance`.
  - `bar_svg.py`: `_Cols` gains `first: int = 0`; `_stroke_row` draws rest dots for `range(cols.first, n)` only; `_count_row` labels `range(cols.first, n)`; the frame rect starts at `cols.left(cols.first) - _PAD`; `bar_svg(..., pickup_slots: int | None = None)` sets `first = n - pickup_slots` when given. The "pickup" label stays.
  - `html.py`: `STROKE_LEGEND` and `DIRECTION_LEGEND` with the verbatim copy; `render_html` passes `editorial_legend=[STROKE_LEGEND, DIRECTION_LEGEND]` always; `_section_lines` passes `pickup_slots=bar.pickup_slots` and chooses the count-row bar as the first bar in the line whose `pickup_slots` is None, falling back to index 0 (so the count row starts at "1", spec 3.2): `first_in_line=i == count_index`.
  - Template: after the artist line, `{% if score.provenance %}<p class="artist provenance">uploaded by {{ score.provenance }}</p>{% endif %}`; after the tab legend, one `<p class="tab-legend editorial">` per line of `editorial_legend`.
  - `lines.py`: `_bar_key` includes `bar.pickup_slots` so a partial bar never folds into a full one.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_score_builder.py
def test_pickup_slots_for_one_beat_of_four_on_eighths_is_two():
    assert pickup_slots(Bar(index=0, start=0, end=0.5, beats=[0], pickup=True), 8, Meter(4, 4)) == 2
def test_pickup_slots_in_three_four_at_six_slots_with_two_beats_is_four():
    assert pickup_slots(Bar(index=0, start=0, end=1, beats=[0, 1], pickup=True), 6, Meter(3, 4)) == 4
def test_pickup_slots_is_none_for_a_full_bar_and_at_least_one_for_a_tiny_one():
    assert pickup_slots(Bar(index=1, start=0, end=2, beats=[0, 1, 2, 3]), 8, Meter(4, 4)) is None
    assert pickup_slots(Bar(index=0, start=0, end=0.1, beats=[0], pickup=True), 4, Meter(4, 4)) == 1
def test_pickup_column_maps_full_bar_cells_onto_the_last_columns():
    assert [pickup_column(j, 8, 2) for j in range(8)] == [6, 6, 6, 6, 7, 7, 7, 7]
def test_score_maps_a_pickup_bars_strokes_and_chord_onto_its_columns():
    # a grid whose bar 0 is a one-beat pickup with strokes at slots 0 and 5: ScoreBar.pickup_slots == 2,
    # strokes at columns 6 and 7, the chord's start_slot 6
def test_state_phrase_for_a_gated_section():
    # a pattern with bass_on_stem True: state == "guitar not separated here", no label, bars grey
def test_score_carries_provenance():
    # SourceInfo(provenance="Natan Santos") -> Score.provenance == "Natan Santos"

# tests/test_bar_svg.py
def test_a_partial_pickup_bar_draws_only_its_columns():
    # bar_svg(..., pickup_slots=2) on an eight-slot bar with no strokes: two 'class="rest"' circles,
    # the frame's x equals cols.left(6) - 2.5, and first_in_line counts show "4", "&" only

# tests/test_html.py
def test_every_sheet_prints_the_two_editorial_legend_lines():
    html = render_html(_score([plain_section]))
    assert html.count("Stroke length is not measured") == 1 and html.count("Arrows follow the hand") == 1
def test_provenance_line_prints_only_when_set():
    assert "uploaded by Natan Santos" in render_html(_score([plain_section], provenance="Natan Santos"))
    assert "uploaded by" not in render_html(_score([plain_section]))
def test_count_row_sits_under_the_first_full_bar_when_the_line_starts_with_a_pickup():
    # a line [pickup(pickup_slots=2), full, full]: exactly one count row, in the second bar's svg
def test_gated_section_prints_its_phrase_and_grey_rows():
    # ScoreSection(state="guitar not separated here", bars grey): the phrase appears once after the label

# tests/test_render_lines.py
def test_a_partial_pickup_never_folds_into_a_full_bar():
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_score_builder.py tests/test_bar_svg.py tests/test_html.py tests/test_render_lines.py -v`
Expected: FAIL (`pickup_slots` undefined; the legend lines absent)

- [ ] **Step 3: Implement the builder, the bar box, the template and the line key as the Interfaces block specifies**

- [ ] **Step 4: Run the suite, then rasterise one sheet with a pickup bar and one gated section through the render stage and look at the first page**

Run: `uv run pytest -q`; then the render stage on `tests/fixtures/v16_score.json` with `pickup_slots` set on bar 0 and one section's state set, at 110 dpi as the 1.7 sample was made.
Expected: PASS; the pickup box is two columns wide at the right of its cell with the "pickup" label; the count row sits under the next bar; the two legend lines sit under the chord diagrams.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/score_builder.py src/youkelele/render tests/test_score_builder.py tests/test_bar_svg.py tests/test_html.py tests/test_render_lines.py
git commit -m "feat(render): the guitar-not-separated phrase, a partial pickup bar, two editorial legend lines, the provenance line"
```

---

### Task 8: The key: a diatonic-set veto, the relative-key hedge and the key relation

**Confidence:** 93%. The veto's two hazards and the Badge figures are measured (`assumption-pass-key-credits.md` A7, A8); `relation` is pitch-class arithmetic cross-checked against mir_eval.

**Files:**
- Modify: `src/youkelele/music/key.py` (`SET_VETO_MARGIN`, `best_major_set`, `relation`, `relative_key`, `key_and_decision`, `_hedge`, `tonic_votes_note`), `src/youkelele/stages/harmony.py` (`_key_log` prints "set" when it decided)
- Test: `tests/test_key.py`

**Interfaces:**
- Produces, in `music/key.py`:
  - `SET_VETO_MARGIN = 0.10` (comment: Badge 0.238, Fame 0.008, the rest 0.000; spec 7.1).
  - `best_major_set(events: Sequence[ChordEvent]) -> tuple[str, float]`: the tonic name and share of the highest `_set_share` over the twelve major sets (ties to the lower pitch class); `("C", 0.0)` with no chord time.
  - `relation(tonic_a: str, mode_a: str, tonic_b: str, mode_b: str) -> Literal["same", "fifth", "relative", "parallel", "other"]`: mir_eval's categories; `fifth` is the same mode a perfect fifth apart (either direction); `relative` is a major key and the minor key three semitones below it; `parallel` is the same tonic, the other mode.
  - `relative_key(tonic: str, mode: str) -> tuple[str, str]`: the relative minor of a major key (tonic down three semitones, "minor") or the relative major of a minor key.
  - `key_and_decision`: after `decide_tonic`, compute `shares = pair_shares(events, _TONICS)`, `decided = shares[decision.tonic]`, `best_tonic, best_share = best_major_set(events)`; when `best_share - decided >= SET_VETO_MARGIN`, replace the decision's tonic with `best_tonic`, set `decided_by = "set"`, `margin = best_share - decided`, `runner_up = None`; always fill `TonicVotes.set_tonic`, `set_share_best`, `set_share_decided`. For a set decision the hedge is `relative_key(tonic, mode)`: `_hedge` gains a first rung returning `(relative tonic, "set")` when `votes.decided_by == "set"`, and `key_and_decision` sets `hedge_mode` to the relative's mode (not `_mode_of`), so the hedge is the relative key by construction.
  - `_hedge`: after the chord-rule and mix rungs, drop the hedge when `relation(key.tonic, key.mode, other, hedge mode) == "other"` and `not _close(key)` (spec 7.3).
  - `tonic_votes_note` appends `, set <tonic> (<best> vs <decided>)` when `set_tonic` is present.
- Consumes: `pair_shares`, `_set_share`, `_chords`, `_mode_of` as they are.

- [ ] **Step 1: Write the failing tests** (chord streams built with the file's existing `_events` helper)

```python
def test_best_major_set_names_the_set_that_holds_the_whole_stream():
    # Am D Em C G Bm, equal durations: ("G", 1.0)
def test_set_veto_replaces_a_dominant_heavy_tonic_with_the_sets_major_tonic():
    # D 34%, A 21%, Em 17%, C 13%, G 11%, Bm 4% with chroma that prefers major at G:
    # key.tonic == "G", mode "major", tonic_votes.decided_by == "set", set_share_best - set_share_decided >= 0.10,
    # hedge_text == "E minor"
def test_set_veto_compares_pair_shares_not_the_tonics_own_major_set():
    # a C# minor stream (C#m, E, A, B): no veto; decided_by unchanged
def test_set_veto_does_not_fire_within_the_margin():
    # a stream whose best set beats the decided tonic's pair share by 0.05: tonic unchanged, set fields filled
def test_set_veto_with_no_chord_time_or_too_few_events_leaves_the_mix_key():
    # four N events, then three real events: mix key returned, no exception
def test_relation_matches_mir_eval_categories():
    for a, b, expect in [(("G","major"),("D","major"),"fifth"), (("G","major"),("E","minor"),"relative"),
                         (("G","major"),("G","minor"),"parallel"), (("G","major"),("A","major"),"other"), (("G","major"),("G","major"),"same")]:
        assert relation(*a, *b) == expect
        assert mir_eval.key.weighted_score(f"{a[0]} {a[1]}", f"{b[0]} {b[1]}") == {"same":1.0,"fifth":0.5,"relative":0.3,"parallel":0.2,"other":0.0}[expect]
def test_relative_key_both_ways():
    assert relative_key("G", "major") == ("E", "minor") and relative_key("E", "minor") == ("G", "major")
def test_an_unrelated_hedge_is_dropped_but_a_fifth_hedge_stays():
    # a mix that disagrees by a major second with a clear margin: hedge None; by a fifth: hedge kept
def test_tonic_votes_note_prints_the_set():
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_key.py -v -k "set or relation or relative or unrelated"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement as the Interfaces block specifies; `_key_log` in `harmony.py` prints "decided by set" through `decision.decided_by`**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest -q`
Expected: PASS; `test_key_json_without_new_fields_loads` still passes (the new `TonicVotes` fields default).

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/key.py src/youkelele/stages/harmony.py tests/test_key.py
git commit -m "feat(key): the diatonic-set veto with a relative-key hedge; hedges name a related key or nothing"
```

---

### Task 9: Title and artist resolved from evidence in order

**Confidence:** 93%. The rungs, the tail condition and the channel test were run on the eleven raw titles in the assumption pass (A9); the two test cases that change are named in spec 8.4.

**Files:**
- Modify: `src/youkelele/titles.py` (`Credits`, `split_title`, `channel_is_artist`, `resolve_credits`, `_strip_artist_prefix`), `src/youkelele/models/ytdl.py` (`METADATA_FIELDS`), `src/youkelele/layout.py` (imports `METADATA_FIELDS`, names the folder from `resolve_credits`), `src/youkelele/stages/ingest.py` (merges fetched details, calls `resolve_credits`, fills the new `SourceInfo` fields)
- Test: `tests/test_titles.py`, `tests/test_stage_ingest.py`, `tests/test_layout.py`

**Interfaces:**
- Produces, in `titles.py`:
  - `@dataclass(frozen=True) Credits(title: str, artist: str | None, title_source: str, artist_source: str, uploader: str | None, provenance: str | None)`; sources are `"credited"`, `"title"`, `"channel"`, `"uploader"`, `"file"`.
  - `split_title(raw: str) -> tuple[str, str] | None`: `(artist, title)` when the raw title splits at the first of `" - "`, `" – "`, `": "` into a head of at most `_MAX_PREFIX_WORDS` words and no `UPLOAD_TAG_WORDS` word appears in the head or in the tail with its bracket groups (`_GROUP_RE`) removed; else None.
  - `channel_is_artist(uploader_id: str | None, channel: str | None, artist: str) -> bool`: True when either handle, casefolded and stripped of non-letters, contains a word of three or more letters from `_long_words(artist)`, or contains the artist's name with its non-letters removed (at least three letters), or either raw handle ends with `" - Topic"`.
  - `resolve_credits(info: Mapping[str, object]) -> Credits`: rungs of spec 8.2 over `track`, `artists` (a list; joined with ", " as yt-dlp's `artist` is), `title`, `uploader`, `uploader_id`, `channel`; the chosen title and artist pass through `clean_title`'s tag and quote stripping and `clean_artist`; `provenance` is the uploader when the artist did not come from the uploader, the uploader (casefolded, tags stripped) differs from the artist, and `channel_is_artist` is False; else None.
  - `_strip_artist_prefix(title, artist)`: the equal-prefix fast path, then `split_title` (the shared-word requirement is gone).
- Produces, in `models/ytdl.py`: `METADATA_FIELDS = ("id", "title", "uploader", "uploader_id", "channel", "channel_id", "artist", "artists", "track", "album", "release_year", "duration")`, public; `fetch_metadata` returns those.
- Produces, in `layout.py`: imports `METADATA_FIELDS`; `base = title_slug(resolve_credits(meta).title)`.
- Produces, in `stages/ingest.py`: `info = {**result.info, **{k: v for k, v in fetched.items() if v is not None}}` when the ids match; `credits = resolve_credits(info)`; `SourceInfo(title=credits.title, artist=credits.artist, raw_title=info.get("title") or stem, uploader=info.get("uploader"), channel=info.get("channel"), credited_artist=..., credited_track=..., artist_source=credits.artist_source, title_source=credits.title_source, provenance=credits.provenance, ...)`; a local file keeps `title_source="file"`, `artist_source="file"`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_titles.py
def test_split_title_takes_a_short_head_without_tag_words():
    assert split_title("The Beatles - Day Tripper (Official Video)") == ("The Beatles", "Day Tripper (Official Video)")
def test_split_title_keeps_a_tag_word_in_the_tail_whole_but_ignores_brackets():
    assert split_title("Song - Live at Wembley") is None and split_title("Live - Song") is None
    assert split_title("The Cars - You Might Think [Official Video]") == ("The Cars", "You Might Think [Official Video]")
    assert split_title("Band - Song - Live") is None
def test_channel_is_artist_cases():
    assert channel_is_artist("@PatBenatarVEVO", None, "Pat Benatar") and channel_is_artist("@bryanadams", None, "Bryan Adams")
    assert channel_is_artist("@acdc", None, "AC/DC") and channel_is_artist(None, "Oasis - Topic", "Oasis")
    assert not channel_is_artist("@rhino", "RHINO", "The Cars") and not channel_is_artist("@goldsongs7948", "Natan Santos", "The Beatles")
def test_resolve_credits_rungs_and_provenance():
    beatles = resolve_credits({"title": "The Beatles - Day Tripper", "uploader": "Natan Santos", "uploader_id": "@goldsongs7948"})
    assert (beatles.title, beatles.artist, beatles.artist_source, beatles.provenance) == ("Day Tripper", "The Beatles", "title", "Natan Santos")
    benatar = resolve_credits({"title": "Pat Benatar - All Fired Up (Official Music Video)", "uploader": "Benatar Giraldo", "uploader_id": "@PatBenatarVEVO"})
    assert (benatar.artist, benatar.provenance) == ("Pat Benatar", None)
    credited = resolve_credits({"title": "Fame (2016 Remaster)", "uploader": "David Bowie", "track": "Fame", "artists": ["David Bowie"]})
    assert (credited.title, credited.artist, credited.title_source) == ("Fame", "David Bowie", "credited")
    plain = resolve_credits({"title": "Song", "uploader": "Someone", "uploader_id": "@someone"})
    assert (plain.artist, plain.artist_source, plain.provenance) == ("Someone", "uploader", None)
# amend test_wider_artist_prefix_rule: "Of Us - Song" with "Of Them" now gives ("Song", "Of Us");
# "Pat Benatar - Song" with None now gives ("Song", "Pat Benatar"); add the two tag-word cases

# tests/test_stage_ingest.py
def test_ingest_merges_fetched_details_over_the_download_info_and_records_sources(tmp_path):
    # source_meta.json with channel and uploader_id, a downloader whose info lacks them: SourceInfo.channel is set,
    # artist_source "title", provenance set when the channel is not the artist's

# tests/test_layout.py
def test_run_folder_is_named_from_the_resolved_title(tmp_path):
    # fetch returns {"id": "x", "title": "The Beatles - Day Tripper", "uploader": "Natan Santos"}: folder "day-tripper"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_titles.py tests/test_stage_ingest.py tests/test_layout.py -v`
Expected: FAIL with `ImportError` on `split_title`

- [ ] **Step 3: Implement as the Interfaces block specifies**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest -q`
Expected: PASS; `test_runner_leaves_source_meta_alone` unchanged; `KNOWN_TITLES` unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/titles.py src/youkelele/models/ytdl.py src/youkelele/layout.py src/youkelele/stages/ingest.py tests/test_titles.py tests/test_stage_ingest.py tests/test_layout.py
git commit -m "feat(ingest): title and artist from credits, the title split, the channel test and the uploader, with provenance"
```

---

### Task 10: The truth files for the eleven songs

**Confidence:** 90%. The verdicts exist in the validation records and the reviews; the work is transcription with a line-by-line check (spec 9.1, A11). What could still bite is an ambiguous range in a record; the rule for those is stated below.

**Files:**
- Create: `truth/README.md` (the five formats, verbatim from spec 9.1), `truth/<slug>/patterns.txt`, `riffs.txt`, `rests.txt`, `key.txt`, `credits.txt` for the eleven run folder names under `runs\` (`all-fired-up`, `chelsea-dagger`, `cream-badge`, `fame`, `mangetout`, `need-you-tonight`, `pour-some-sugar-on-me`, `summer-of-69`, `the-beatles-day-tripper`, `the-cars-you-might-think`, `you-shook-me-all-night-long`)
- Create: `tests/fixtures/ground_truth/example/` gains the five files for the 4-bar example clip (two pattern ranges, one riff label, one rest range, a key, credits), used by Task 11's tests.

**Interfaces:**
- Produces: the files, in the formats of spec 9.1. Sources, in this order: the listening-pass tables of `docs/superpowers/specs/2026-10-05-v1-6-validation.md` (clips 1 to 37) and `2026-10-06-v1-7-validation.md` (clips 1 to 16, the sources table, the Badge section); `docs/superpowers/research/2026-10-06-v1-7/acdc-ear-truth.md`; the review truth tables in `research_notes/Weak music measurements research/review_pattern_vote_and_direction.md` (section C), `review_riff_versus_strum.md` (C), `review_rests_and_activity.md` (C), `review_key_and_metadata.md` (C, the key table). A verdict the records give as MOSTLY is MOSTLY; a range two records judge differently keeps the later record's verdict with a `#` comment naming both; a range a record leaves ambiguous is omitted with a `#` comment, never guessed.

- [ ] **Step 1: Write `truth/README.md` and the example fixture files**

- [ ] **Step 2: Transcribe the eleven songs' files from the sources above**

- [ ] **Step 3: Check every line against its record**

A second pass reading each file beside its source table; every `patterns.txt` line cites its clip number in a trailing `#` comment; every `riffs.txt` and `rests.txt` line cites a clip or a source-table row; `key.txt` cites the source URL from the key review's table; `credits.txt` holds the expected printed title and artist.

- [ ] **Step 4: Commit**

```bash
git add truth tests/fixtures/ground_truth/example
git commit -m "docs(truth): pattern, riff, rest, key and credit truth for the eleven songs, from the listening passes and sources"
```

---

### Task 11: `evaluate` scores against the truth files and prints the new figures

**Confidence:** 91%. Each metric is one of spec 9.2's lines over functions that exist (`jaccard`, Task 4's `swap_distance`, `mir_eval.key.weighted_score`, Task 8's `relation`); the parsers are plain text. The file is large already, so the parsers and scorers go in a new module.

**Files:**
- Create: `src/youkelele/truth.py` (parsers and scorers), `tests/test_truth.py`
- Modify: `src/youkelele/evaluate.py` (`SectionDiag`, `_section_diags`, `Report`, `evaluate_run`, `_section_line`, `_vote_figures`, `_key_line`, `format_report`, `SectionDelta`, `compare_runs`, `format_comparison`)
- Test: `tests/test_evaluate.py`

**Interfaces:**
- Produces, in `truth.py`:
  - `@dataclass PatternTruth(start: int, end: int, verdict: Literal["YES", "MOSTLY", "NO"], figure: list[str] | None)`; `RangeLabel(start: int, end: int, label: str)`; `KeyTruth(tonic: str, mode: str, source: str, alternative: tuple[str, str] | None)`; `CreditsTruth(title: str, artist: str)`.
  - `read_patterns(path) -> list[PatternTruth]`, `read_labels(path) -> list[RangeLabel]` (for `riffs.txt` and `rests.txt`), `read_key(path) -> KeyTruth`, `read_credits(path) -> CreditsTruth`; each raises `TruthFormatError` (the existing class, moved here and re-exported by `evaluate.py`) on a malformed line; a missing file is the caller's `None`.
  - `@dataclass PatternScore(start, end, verdict, printed: list[str], figure: list[str] | None, jaccard: float | None, swap: int | None, certain: bool, voted_bars: int, top2_margin: float | None)`; `score_patterns(truth, strums: Strums, grid: Grid) -> list[PatternScore]` using the printed row of the range's first bar (`strums.bars`), one or two bars as the figure's length; `false_certain(scores) -> int` (NO and certain), `false_grey(scores) -> int` (YES or MOSTLY and not certain); `discontinuity(strums) -> float` (printed pattern changes per bar over the song).
  - `score_flags(truth: list[RangeLabel], strums, grid) -> tuple[float | None, float | None, float, float]`: `(precision, recall, baseline_not_riff, baseline_riff)` over the labelled ranges, a section counted flagged when its planned section's pattern `riff` is True (or the member's bar records), `mixed` counted as a hit, `bleed` counted as not-riff.
  - `score_rests(truth, strums) -> tuple[float | None, float | None, int, int, float | None]`: `(precision, recall, deletions, insertions, event_f)` over labelled bars; `tail` counts as rest; `contested` is skipped; `event_f` with a one-beat collar on region edges computed on bar indices (a region's edge bar matches within one bar).
  - `score_key(truth: KeyTruth, key: Key) -> tuple[float, str, bool | None]`: `(weighted score against the better of the truth and its alternative, category from relation(), hedge_related or None when no hedge)`.
  - `score_credits(truth: CreditsTruth, source: SourceInfo) -> tuple[bool, bool]` after casefold and tag stripping.
- Produces, in `evaluate.py`:
  - `SectionDiag` gains `voted_bars: list[int]`, `dropped_bars: list[int]`, `top2_margin`, `runner_up_vector`, `confidence_all_bars`, `chance_p_all_bars`, `bass_on_stem`, `low_own_share`, `bass_stem_ratio`, `low_mix_share_bass`, `low_mix_share_source`, copied from the pattern; `_vote_figures` prints `voted N (dropped M)`, `rival <vector> margin X`, `all-bars conf X p Y`, and `bass-on-stem` with the four figures when the gate fired.
  - `Report` gains `pattern_scores`, `false_certain`, `false_grey`, `discontinuity`, `riff_scores`, `rest_scores`, `key_score`, `credits_match`, each None without its truth file; `evaluate_run` reads `ingest/source.json` for the credits; `format_report` prints one block per truth kind with `n/a` when absent; `_key_line` adds the set votes.
  - `SectionDelta` gains `voted_bars_changed: bool`, `bass_gate_changed: bool`, `certainty_readings: tuple[bool | None, bool | None]`; `format_comparison` prints them.
- Consumes: Task 1's fields, Task 4's `swap_distance`, Task 8's `relation`, `jaccard`.

- [ ] **Step 1: Write the failing tests** (`tests/test_truth.py` on the example fixture; `tests/test_evaluate.py` through `evaluate_run` and the CLI)

```python
def test_read_patterns_parses_ranges_verdicts_and_optional_figures(): ...
def test_malformed_truth_line_raises_truth_format_error(): ...
def test_score_patterns_reports_jaccard_swap_and_false_certain(): ...
def test_score_flags_counts_mixed_as_a_hit_and_prints_both_baselines(): ...
def test_score_rests_counts_deletions_and_insertions_apart_and_skips_contested(): ...
def test_score_key_takes_the_better_of_truth_and_alternative(): ...
def test_score_credits_ignores_case_and_tags(): ...
def test_evaluate_with_truth_prints_the_five_blocks_and_na_for_missing_files(tmp_path): ...
def test_section_line_prints_voted_rival_all_bars_and_bass_gate(tmp_path): ...
def test_compare_reports_voted_bars_and_bass_gate_changes(tmp_path): ...
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_truth.py tests/test_evaluate.py -v`
Expected: FAIL with `ModuleNotFoundError: youkelele.truth`

- [ ] **Step 3: Implement `truth.py` and the `evaluate.py` additions as the Interfaces block specifies**

- [ ] **Step 4: Run the suite, then `evaluate` on one real run with its truth folder**

Run: `uv run pytest -q`; `uv run youkelele evaluate need-you-tonight --truth truth/need-you-tonight`
Expected: PASS; the report prints every block of spec 9.2 with figures.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/truth.py src/youkelele/evaluate.py tests/test_truth.py tests/test_evaluate.py
git commit -m "feat(evaluate): pattern, riff, rest, key and credit scores against truth files; the vote and bass-gate figures"
```

---

### Task 12: `scripts/band_sweep.py` with leave-one-song-out

**Confidence:** 90%. The sweep recomputes rests and the bass gate from figures already stored in `strums.json`, and re-votes from `bar_onsets` as the assumption-pass scripts did (they reproduced every printed row). The uncertainty is only in how much of the re-vote path to expose; the scope below is fixed to the five constants named.

**Files:**
- Create: `scripts/band_sweep.py`, `tests/test_band_sweep.py`

**Interfaces:**
- Produces: a CLI `uv run python scripts/band_sweep.py --runs runs --truth truth --constant <name> --from A --to B --step S`, where `<name>` is one of `REST_RATIO_MIN`, `REST_LOW_SHARE_MIN` (metric: per-bar rest F from `score_rests`, recomputed from the stored `energy_ratio` and `low_share`), `BASS_STEM_MAX`, `OWN_LOW_SHARE_MIN` (metric: gate precision and recall against `riffs.txt`'s `bleed` labels, from the stored four figures), `PERIOD2_MIN_PAIRS`, `MIN_SLOT_SUPPORT`, `MIN_VOTE_BARS` (metric: `false_certain` and `false_grey` from `score_patterns`, re-voting each member from `bar_onsets` and the stored `rests` flags with the stage's own functions). Output: a table of the constant's values against the pooled metric, then one line per held-out song with its best value, then whether the current value sits inside every held-out best's band. Functions: `sweep(constant: str, values: list[float], runs: dict[str, Path], truths: dict[str, Path]) -> SweepResult` and `format_sweep(r) -> str`, so tests run it on fixtures.
- Consumes: Task 11's scorers; `youkelele.music.rests.bar_holds`, `bleed.bass_on_stem`, the vote functions, through `monkeypatch`-style attribute setting on the modules.

- [ ] **Step 1: Write the failing tests** (two tiny synthetic "runs" built from the fixtures with truth folders)

```python
def test_sweep_rest_ratio_reports_pooled_curve_and_per_song_best(): ...
def test_sweep_restores_the_constant_after_running(): ...
def test_sweep_unknown_constant_is_a_clear_error(): ...
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_band_sweep.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the script as the Interfaces block specifies**

- [ ] **Step 4: Run the tests, then one real sweep**

Run: `uv run pytest tests/test_band_sweep.py -v`; `uv run python scripts/band_sweep.py --runs runs --truth truth --constant REST_RATIO_MIN --from 0.02 --to 0.10 --step 0.005`
Expected: PASS; a curve with a flat region around 0.05 and the per-song bests printed.

- [ ] **Step 5: Commit**

```bash
git add scripts/band_sweep.py tests/test_band_sweep.py
git commit -m "feat(tooling): band_sweep sweeps a constant against the truth files with leave-one-song-out"
```

---

### Task 13: Version 0.9.0, README and the sample sheet

**Confidence:** 95%. The 1.7 plan's Task 8 is the template; the README lines are verbatim in the spec.

**Files:**
- Modify: `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock` (version); `README.md` (stage table row for strums naming the bass stem and the gate; limitations: the two new lines, and the chance-test limitation reworded as spec 5.3 says; history line for 1.8 with links to the spec and the validation record to come); `docs/images/sample-sheet.png` regenerated as the 1.7 Task 8 did
- Test: `tests/test_readme.py`, `tests/test_vendoring.py` (version)

- [ ] **Step 1: Update the version in the three places and run `uv lock`**

- [ ] **Step 2: Update the README as listed; the history line: "1.8 (package version 0.9.0): the rest rule measures on the quantiser's window; a two-bar vote needs three pairs and a printed slot two strikes; certainty must hold on the full span and on at least four bars; a stem that carries the bass prints grey under 'guitar not separated here'; the chord set may veto the tonic; title and artist resolved from credits, the title and the channel; the legend says stroke length and direction are not measured; truth files and new evaluate scores."**

- [ ] **Step 3: Regenerate the sample sheet and check the two legend lines are on page 1**

- [ ] **Step 4: Run the suite**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/youkelele/__init__.py uv.lock README.md docs/images/sample-sheet.png
git commit -m "chore: version 0.9.0; README stage table, limitations, history and sample sheet for 1.8"
```

---

### Task 14: Validation on eleven songs and one blind song

**Confidence:** 90%. The expectations are spec 12's ten, written before the run, with every figure already predicted by the assumption pass; the three blind-song re-runs from ingest need the network, and the blind song is unknown by design.

**Files:**
- Create: `docs/superpowers/specs/2026-10-08-v1-8-validation.md` (on main, mirroring the 1.7 record: runs and baselines, the expectations table, per-song figures, the `evaluate --truth` totals before and after, sources, clips, A1 to A12 re-rated)
- Scratch (not committed): `%TEMP%\youkulele-v18-validation\` with `baseline\` (copies of each run's `03_harmony` to `08_render`, `manifest.json`, `source_meta.json`, `00_ingest\source.json`), `measure.py` (byte comparison of `grid.json`, `bar_onsets`, the chord events less `key`), `evaluate\`, `logs\`, `clips\`
- Touches: `runs\` (the only task that does)

**Interfaces:**
- Consumes: the whole branch; `uv run youkelele run <folder> --from harmony`; `uv run youkelele run <url>` for the three blind songs and the new one; `uv run youkelele evaluate <name> --truth truth/<name>` and `evaluate <baseline> --compare <name>`; the 1.7 clip maker.

- [ ] **Step 1: Write the ten expectations into the record before any run, and record `evaluate --truth` totals on the 1.7 baseline runs (expectation 9)**

- [ ] **Step 2: Copy the baselines; re-run the eight known songs `--from harmony`; re-run The Cars, Day Tripper and Badge from ingest with their URLs from the manifests**

Expected: exit 0 on all eleven; `measure.py` reports `grid.json` and `bar_onsets` identical and the chord events identical except `key` on all eleven (expectation 1); the three fresh `source_meta.json` files hold `uploader_id` and `channel`.

- [ ] **Step 3: Measure every expectation**

`evaluate --truth` and `evaluate <baseline> --compare` on all eleven; record per song: the rest flags that changed (expectation 2: Chelsea Dagger 7 and 12, The Cars 63, Pour Some Sugar On Me 80 rest; 7 holds; 54 on the ten); the members whose vector or certainty changed (expectation 3: Need You Tonight 0-13, The Cars 72-76, Summer of '69 0-4, Chelsea Dagger 7-19 grey; false certain 8 of 16, false grey 4 of 8); the bass gate (expectation 4: five Badge members); the key (expectation 5: Badge "G major (or E minor)", ten leads unchanged, three hedges unchanged); the credits (expectation 6); the pickup bars and page counts (expectation 7); the legend lines on every sheet (expectation 8).

- [ ] **Step 4: Sources, then ear clips where sources disagree, say nothing, or contradict the chain**

Stem-alone clips for Pour Some Sugar On Me 7 and 80 and The Cars 63; stem-alone and click clips for Badge's five gated members (the three unjudged first); clicks for any member whose row changed outside the truth files; the listing with one question per clip. Record verdicts.

- [ ] **Step 5: The blind song**

Ask the owner for the URL when Steps 2 to 4 are done; run from ingest; `evaluate`; record its figures without judging them (expectation 10); write its `truth/` folder from published sources and the owner's verdicts afterwards.

- [ ] **Step 6: Assumptions and findings**

Re-rate A1 to A12; list every row the sources or the ear rejected under "Recorded, not tuned"; if a finding is a code defect, fix it on the branch with a test, re-run the affected songs and record the fix round as the 1.7 record does. Amend the spec on main with the decisions this plan made (Task 6's gate order; Task 7's column mapping and count-row placement).

- [ ] **Step 7: Commit the record on main; the manifests at 0.9.0 stay under `runs\`**

```bash
git add docs/superpowers/specs/2026-10-08-v1-8-validation.md truth
git commit -m "docs: 1.8 validation on eleven songs and one blind song against the truth files"
```

---

## Self-review

- **Spec coverage.** 3.1 Task 7; 3.2 Tasks 1 and 7; 3.3 Tasks 6 and 7; 3.4 Tasks 1, 7, 9; 3.5 nothing to build; 4.1 Task 2; 4.2 nothing to build (no tail flag anywhere: Task 1 adds none); 4.3 Task 7; 4.4 Task 6; 4.5 by the Global Constraints; 5.1 and 5.2 Task 3; 5.3 by the Global Constraints and Task 13's README wording; 5.4 Tasks 3 and 6; 5.5 Tasks 4 and 6; 5.6 by the Global Constraints; 5.7 Task 14 expectation 3; 6 Tasks 5, 6, 7; 7.1 to 7.4 Task 8; 7.5 by the Global Constraints; 8.1 to 8.3 Task 9; 8.4 Task 9's test changes; 9.1 Task 10; 9.2 Task 11; 9.3 Task 12; 10 Task 13 (README lines); 11 Tasks 1, 6, 8, 9, 13; 12 Task 14; 13 Task 14 Step 6.
- **Decisions the spec left open**, each made in one task and to be amended into the spec on acceptance: the bass gate runs on the member's whole analysed span before the rest rule, and a gated member's rests use the energy floor alone (Task 6); a pickup bar's full-bar cells map onto its last `pickup_slots` columns by `pickup_column`, and the count row sits under the line's first full bar (Task 7); the credits sources are the five names in Task 9 and `provenance` is decided at ingest, not at render; `truth.py` holds the parsers and scorers so `evaluate.py` does not grow further (Task 11); the sweep covers the seven constants named in Task 12.
- **Type consistency.** `voted_bars`, `dropped_bars`, `top2_margin`, `runner_up_vector`, `confidence_all_bars`, `chance_p_all_bars`, `bass_on_stem`, `low_mix_share_bass`, `low_mix_share_source`, `low_own_share`, `bass_stem_ratio`, `pickup_slots`, `provenance` are spelled the same in Tasks 1, 6, 7, 9, 11; `VoteResult.voted` and `.dropped` (positions) are mapped to grid indices in Task 6 and stored as `voted_bars` and `dropped_bars`; `bleed_figures(source, bass, mix, sr, start, end)` matches its call in Task 6; `bar_energy_ratio(stem, mix, sr, bar, slots_per_bar)` matches Task 2's callers; `relation(tonic_a, mode_a, tonic_b, mode_b)` is called that way in Tasks 8 and 11; `METADATA_FIELDS` is public in Task 9 and imported by `layout.py`.
- **Review Focus.** Line 1 Task 6's first test; line 2 Task 7's three-four test; line 3 Task 9's bracket test; line 4 Task 8's no-chord-time test; line 5 Task 4's none test and Task 6's three-bar test.
- **Proportion.** Fourteen tasks, test names and assertions carrying the spec's values, signatures without bodies; the only prose bodies are the decisions above and `pickup_column`'s one-line formula.
