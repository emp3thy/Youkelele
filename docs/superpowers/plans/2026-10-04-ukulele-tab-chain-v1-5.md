# Ukulele Tab Chain 1.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fewer, truer sections and an honest sheet: fragments merge into their neighbours, strum certainty passes a chance test, riff sections say so, the strip costs no page, the tonic is chosen by two of three rules, and the easy sheet names its power chords.

**Architecture:** A section plan computed in the strums stage from the grid, the chords and the bridge rule is stored in `strums.json` and read by the score builder, so both stages print the same sections. The strums stage gains a shuffle-based structure test and two onset-pitch riff features; the harmony stage records three tonic votes and decides by majority; the renderer draws a one-bar strip beside the rows unless a bar changes chord inside it. Every new field is defaulted so 1.3 and 1.4 files load.

**Tech Stack:** Python 3.12 via uv, pydantic 2, numpy, librosa (constant-Q), Jinja2 and inline SVG, Playwright Chromium PDF, pytest.

**Spec:** `docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-5-design.md` (sections cited as "spec N"). Research under `docs/superpowers/research/2026-10-04-v1-5/`.

## Global Constraints

- Schema version stays 1; every 1.3 and 1.4 `grid.json`, `chords.json`, `strums.json`, `arrangement.json` and `score.json` loads and renders (spec 7).
- Nothing reads a song's title, id, duration or any other identity; every rule applies to any input; unit tests use synthetic inputs or measured numbers as examples of a rule (spec 1, Generality).
- UK spelling; no em-dashes; no song lyrics in code, tests or documents; no time or effort estimates in documents.
- Constants and their values, verbatim from the spec: `FRAGMENT_BARS = 8`; pair novelty for a merge `0`; `ONE_LOOP_SHARE = 0.85`; `CHANCE_ALPHA = 0.05`; `CHANCE_SHUFFLES = 1000`; `FULL_VOTE_DENSITY = 0.6`; `UNCERTAIN_BELOW_SIXTEENTH = 0.53` (was 0.55); `RIFF_ENTROPY_MAX = 0.82`; `RIFF_SINGLE_PC_MIN = 0.45`; `KEY_TIE_MARGIN = 0.05` unchanged; `POWER_LEGEND_EASY = "{name} is a power chord (root and fifth) on the record; this sheet prints the triad."`; riff wording "Riff heard in this section: strum the chord to this rhythm".
- Printed patterns are unchanged: `majority_vector`, `fill_to_floor`, `jaccard`, `render_directions` are not modified.
- Package version 0.6.0 in `pyproject.toml`, `src/youkelele/__init__.py`, `uv.lock`; the eight manifests at 0.6.0 after validation.
- Run folders under `C:\Users\gethi\sources\Youkelele\runs\` are touched only by Task 11; `runs_v13\` is read-only.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. The shell guard refuses compound bash containing git: plain separate git commands only.

## Review Focus

1. A song whose sung sections are all shorter than 8 bars: the fragment rule must not cascade into one section or merge across an intro, instrumental, outro or bridge; it terminates with every non-merging fragment left alone. Test in Task 2.
2. A 1.4 `strums.json` (no plan, patterns indexed by grid section) must still build a score, as one planned section per grid section. Test in Task 6.
3. A section with no onsets, or a no-instrument section: riff features are None and `riff` is False, and the chance test is not run; a section whose bars are all rests gets p 1.0 without a division by zero. Tests in Tasks 3 and 5.
4. A section with a pickup row and a one-bar strip beside the rows: the pickup column keeps its width and the strip does not wrap under the rows; a section whose only example bar has a mid-bar change keeps a strip beside the rows too. Test in Task 8.
5. A key with no mix estimate (1.3 file or too few chords) and a decision whose score margin is under `KEY_TIE_MARGIN`: the votes record `decided_by` without raising and the hedge behaves as 1.4 did. Test in Task 7.

---

### Task 1: Schemas for the plan, the structure test, the riff marker and the votes

**Confidence:** 96%

**Files:**
- Modify: `src/youkelele/schemas.py:112-125` (`Key`), `:160-170` (`SectionPattern`), `:172-186` (`Strums`), `:258-267` (`ScoreSection`)
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces: `class PlannedSection(_Artifact): start_bar: int; end_bar: int; label: str; members: list[int] = []` (end exclusive; members are grid section indices in order). `Strums.plan: list[PlannedSection] = []`. `SectionPattern.chance_p: float | None = None`, `strike_density: float | None = None`, `riff: bool = False`, `riff_entropy: float | None = None`, `riff_single_share: float | None = None`. `class TonicVotes(_Artifact): score: str | None = None; pair: str | None = None; mix: str | None = None; decided_by: Literal["agreement", "pair rule", "mix", "score"] | None = None`. `Key.pair_tonic: str | None = None`, `Key.tonic_votes: TonicVotes | None = None`. `ScoreSection.riff: bool = False`, `ScoreSection.members: list[int] = []`.

- [ ] **Step 1: Write the failing tests**

```python
def test_strums_plan_defaults_empty_and_round_trips():
    s = Strums.model_validate_json(FIXTURE_14_STRUMS)  # a 1.4 strums.json under tests/fixtures
    assert s.plan == []
    s2 = s.model_copy(update={"plan": [PlannedSection(start_bar=0, end_bar=8, label="verse", members=[0, 1])]})
    assert Strums.model_validate_json(s2.model_dump_json()).plan[0].members == [0, 1]

def test_section_pattern_new_fields_default():
    p = SectionPattern(section=0, slots=["-"] * 8, confidence=0.0, bar_repeat=0.0, uncertain=True, no_instrument=True, inherited_from=None)
    assert (p.chance_p, p.strike_density, p.riff, p.riff_entropy, p.riff_single_share) == (None, None, False, None, None)

def test_key_votes_default_none_and_load_1_3_and_1_4_keys():
    for fixture in (FIXTURE_13_CHORDS, FIXTURE_14_CHORDS):
        key = Chords.model_validate_json(fixture).key
        assert key.pair_tonic is None and key.tonic_votes is None
    votes = TonicVotes(score="C", pair="F", mix="F", decided_by="mix")
    assert Key(tonic="F", mode="major", confidence=0.1, tonic_votes=votes).tonic_votes.decided_by == "mix"

def test_score_section_riff_and_members_default():
    sec = ScoreSection(label="verse", pattern=["-"] * 8, uncertain=False, bars=[], bar_repeat=0.0, no_instrument=False)
    assert sec.riff is False and sec.members == []
```

Fixtures: copy one 1.3 `chords.json` (from `runs_v13`) and one 1.4 `chords.json` and `strums.json` into `tests/fixtures/` if not already there (check `tests/fixtures` first; reuse the 1.3 `key.json` fixture Task 1 of 1.4 added).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schemas.py -q`
Expected: FAIL with `ImportError` for `PlannedSection` / `TonicVotes`.

- [ ] **Step 3: Add the fields and classes to `schemas.py`** with the defaults in Interfaces; a one-line comment per field in the file's existing style. `PlannedSection` goes above `Strums`; `TonicVotes` above `Key`.

- [ ] **Step 4: Run the tests and the schema suite**

Run: `uv run pytest tests/test_schemas.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/schemas.py tests/test_schemas.py tests/fixtures
git commit -m "feat: schema fields for the section plan, the structure test, the riff marker and the tonic votes"
```

---

### Task 2: The section plan

**Confidence:** 94%. The sandwich rule rests on one measured case (spec A3); the fragment rule on seven merges over two songs (A2). Both are stated as generic rules with the band each constant sits in.

**Files:**
- Modify: `src/youkelele/music/relabel.py` (beside `refine_labels`, line 50)
- Test: `tests/test_relabel.py`

**Interfaces:**
- Consumes: `refine_labels(grid, chords) -> list[str]`, `_bar_triads(grid, chords) -> list[set[str]]` (same file); `PlannedSection` (Task 1).
- Produces: `FRAGMENT_BARS = 8`, `ONE_LOOP_SHARE = 0.85`, `CHORD_MATCH_DISTANCE = 0.35`; `bar_triad_strings(grid, chords) -> list[str]` (one token per bar: the bar's triads sorted and joined with `+`, `N` when none); `containment_distance(a: Sequence[str], b: Sequence[str]) -> float` (Levenshtein distance of the shorter sequence against every window of its length in the longer, the windows also shifted one bar before the start and one past the end with the overhang ignored, divided by the shorter length; 0.0 for two empty sequences); `pair_novelty(grid, chords, fragment: tuple[int, int], neighbour: tuple[int, int]) -> float` (share of the fragment's chord-bars holding a triad the neighbour never plays; 0.0 with no chord-bars); `default_plan(grid, chords) -> list[PlannedSection]` (one planned section per grid section with `refine_labels`' label and `members=[i]`); `section_plan(grid, chords) -> list[PlannedSection]`; `longest_member(section: PlannedSection, grid: Grid) -> tuple[int, int]` (the bar range of the member with most bars, the earlier on a tie); `one_loop_share(grid, chords) -> float` (the largest group of sung sections, verse or chorus, whose pairwise `containment_distance` over their bar-triad strings is at most `CHORD_MATCH_DISTANCE`, as a share of all sung sections' bars; 0.0 with no sung sections).

- [ ] **Step 1: Write the failing tests** (grids built with the file's existing helpers; chords as events over bar times)

```python
def test_containment_distance_finds_the_shorter_inside_the_longer_with_a_one_bar_shift():
    assert containment_distance(["Em", "D", "G"], ["C", "Em", "D", "G", "C"]) == 0.0
    assert containment_distance(["Em", "D", "G"], ["Em", "D", "G"]) == 0.0
    assert containment_distance(["Em", "D"], ["G", "C"]) == 1.0
    assert containment_distance([], []) == 0.0

def test_sandwich_verse_between_choruses_on_their_chords_becomes_one_chorus():
    # sections: chorus 0-8 (Em D G), verse 8-12 (Em D), chorus 12-20 (Em D G)
    plan = section_plan(grid, chords)
    assert [(p.start_bar, p.end_bar, p.label, p.members) for p in plan] == [(0, 20, "chorus", [0, 1, 2])]

def test_fragment_joins_a_same_label_neighbour_at_least_as_long_that_plays_its_chords():
    # verse 0-16 (Em D G), verse 16-23 (Em D): 7 bars, pair novelty 0 -> one verse 0-23
    assert [(p.start_bar, p.end_bar, p.members) for p in section_plan(grid, chords)] == [(0, 23, [0, 1])]

def test_fragment_with_a_new_chord_does_not_merge():
    # verse 0-16 (Em D G), verse 16-23 (Em D A): novelty > 0 -> two sections
    assert len(section_plan(grid, chords)) == 2

def test_whole_sections_of_eight_bars_never_merge_on_chord_match():
    # verse 0-16 and verse 16-32 on the same chords -> two sections
    assert len(section_plan(grid, chords)) == 2

def test_intro_instrumental_outro_and_bridge_never_merge():
    # intro 0-4 (Em), verse 4-20 (Em D G), instrumental 20-24 (Em D), verse 24-40, outro 40-44
    labels = [p.label for p in section_plan(grid, chords)]
    assert labels == ["intro", "verse", "instrumental", "verse", "outro"]

def test_two_eligible_neighbours_the_closer_chord_sequence_wins():
    # verse 0-16 (Em D G C), verse 16-22 (Em D), verse 22-38 (Em D Em D): the fragment joins 22-38 (distance 0.0 < 0.5)
    plan = section_plan(grid, chords)
    assert [(p.start_bar, p.end_bar) for p in plan] == [(0, 16), (16, 38)]

def test_all_fragment_song_terminates_without_cascading():
    # five verses of 4 bars each on the same chords: 4-bar fragments join a neighbour at least as long; the rule reaches a fixed point and never produces a section over an intro
    plan = section_plan(grid_all_fragments, chords)
    assert sum(p.end_bar - p.start_bar for p in plan) == 20 and plan[0].start_bar == 0

def test_default_plan_is_one_section_per_grid_section_with_refined_labels():
    assert [p.members for p in default_plan(grid, chords)] == [[i] for i in range(len(grid.sections))]

def test_longest_member_is_the_earlier_on_a_tie():
    sec = PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])  # grid sections 0-8 and 8-16
    assert longest_member(sec, grid) == (0, 8)

def test_one_loop_share_is_high_when_every_sung_section_shares_its_chords():
    assert one_loop_share(grid_one_loop, chords_one_loop) >= 0.85
    assert one_loop_share(grid_two_groups, chords_two_groups) < 0.85
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_relabel.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement the functions in `relabel.py`** with the signatures above. `section_plan`: start from `default_plan`, then loop until no change: apply the sandwich rule (a `verse` shorter than `FRAGMENT_BARS` whose both neighbours are `chorus` and whose `pair_novelty` against each is 0 becomes one `chorus` spanning the three, members concatenated), then the fragment rule (a `verse` or `chorus` shorter than `FRAGMENT_BARS` with a same-label neighbour at least as long and `pair_novelty` 0 joins it; with two eligible neighbours, the lower `containment_distance` of bar-triad strings wins, the earlier on a tie). Labels `intro`, `instrumental`, `outro`, `bridge` are never fragments and never absorb.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_relabel.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/relabel.py tests/test_relabel.py
git commit -m "feat: section plan merges fragments into their neighbours by chord content"
```

---

### Task 3: The structure test

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/music/as_played.py:17-27` (constants) and new functions beside `section_summary` (line 95)
- Test: `tests/test_as_played.py`

**Interfaces:**
- Consumes: `majority_vector`, `fill_to_floor`, `jaccard`, `DENSITY_FLOOR` (same file, unchanged).
- Produces: `CHANCE_ALPHA = 0.05`, `CHANCE_SHUFFLES = 1000`, `FULL_VOTE_DENSITY = 0.6`, `UNCERTAIN_BELOW_SIXTEENTH = 0.53`; `full_vote(vector: Sequence[StrikeClass]) -> bool` (no rest in the vector); `strike_density(bars: Sequence[Sequence[StrikeClass]]) -> float` (share of cells that are not `-`, mutes counted; 0.0 with no bars); `vote_confidence(bars) -> float` (the topped-up vote's mean Jaccard, exactly as `section_summary` computes it, factored out so both call it); `chance_p(bars, seed: int, shuffles: int = CHANCE_SHUFFLES) -> float` (`(b + 1) / (shuffles + 1)` where `b` counts shuffled copies with `vote_confidence` at least the observed; each bar's cells permuted with `random.Random(seed)`); `structure_test(bars, vector, seed) -> tuple[bool, float | None, float]` returning `(structured, chance_p or None when the vote is full, strike_density)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_full_vote_and_strike_density():
    assert full_vote(["S", "x", "S", "S"]) and not full_vote(["S", "-", "S", "S"])
    assert strike_density([["S", "-", "x", "-"], ["-", "-", "-", "-"]]) == 0.25
    assert strike_density([]) == 0.0

def test_chance_p_is_near_one_for_a_random_spray_and_small_for_a_repeated_pattern():
    rng = random.Random(1)
    spray = [[rng.choice("S-") for _ in range(8)] for _ in range(8)]
    pattern = [list("S-SS-SSS")] * 8
    assert chance_p(spray, seed=3, shuffles=200) > 0.2
    assert chance_p(pattern, seed=3, shuffles=200) <= 1 / 201 + 1e-9

def test_chance_p_is_reproducible_for_a_seed_and_never_zero():
    bars = [list("S-S-S-SS"), list("S-SS--SS"), list("S-S-S-S-"), list("--S-S-SS")]
    assert chance_p(bars, seed=7, shuffles=100) == chance_p(bars, seed=7, shuffles=100) > 0

def test_structure_test_exempts_a_full_vote_and_needs_density():
    dense = [list("SSSSSSSS")] * 6
    structured, p, density = structure_test(dense, list("SSSSSSSS"), seed=0)
    assert (structured, p, density) == (True, None, 1.0)
    sparse_full = [list("S-S-S-S-"), list("-S-S-S-S")] * 3  # the vote fills every slot, density 0.5
    structured, p, density = structure_test(sparse_full, list("SSSSSSSS"), seed=0)
    assert not structured and p is None and density == 0.5

def test_structure_test_all_rest_bars_gives_p_one():
    rests = [["-"] * 8] * 4
    structured, p, _ = structure_test(rests, ["-"] * 8, seed=0)
    assert not structured and p == 1.0

def test_sixteenth_floor_is_0_53():
    assert UNCERTAIN_BELOW_SIXTEENTH == 0.53
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_as_played.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement** the constants and functions; refactor `section_summary` to call `vote_confidence` so the two agree by construction; update the comment above `UNCERTAIN_BELOW_SIXTEENTH` to the spec's band (0.504, 0.552) and reason.

- [ ] **Step 4: Run the suite**

Run: `uv run pytest tests/test_as_played.py tests/test_stage_strums.py -q`
Expected: PASS (the stage's existing tests do not use the sixteenth floor's exact value; if one does, update its expectation to 0.53).

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/as_played.py tests/test_as_played.py
git commit -m "feat: shuffle structure test for strum certainty; sixteenth floor 0.53"
```

---

### Task 4: Riff features

**Confidence:** 92%. The thresholds were re-measured with the stage's own onsets (spec A17); the constant-Q settings below reproduce that measurement, and the spike's scripts under `%TEMP%\youkelele-v15-research\riff\` show the exact librosa calls to mirror.

**Files:**
- Create: `src/youkelele/music/riff.py`
- Test: `tests/test_riff.py`

**Interfaces:**
- Consumes: `Onsets.times` (`music/onsets.py`), a mono signal and sample rate.
- Produces: `RIFF_ENTROPY_MAX = 0.82`, `RIFF_SINGLE_PC_MIN = 0.45`, `RIFF_WINDOW = (0.040, 0.130)` (seconds after the onset), `RIFF_FMIN_NOTE = "C2"`, `RIFF_OCTAVES = 6`, `RIFF_HOP_SECONDS = 256 / 22050`; `onset_chroma(y: np.ndarray, sr: int, times: np.ndarray) -> np.ndarray` (shape `(n_onsets, 12)`: constant-Q power from C2, 12 bins per octave over 6 octaves, hop `round(sr * RIFF_HOP_SECONDS)`, folded to 12 pitch classes, averaged over the frames inside the window after each onset; a row of zeros when no frame falls inside); `riff_features(chroma: np.ndarray) -> tuple[float | None, float | None]` (the median over onsets of each onset's normalised Shannon entropy (log base 12), and the share of onsets whose chroma has exactly one pitch class at half its maximum or more; `(None, None)` with no onsets; a zero row counts as entropy 1.0 and not single); `is_riff(entropy: float | None, single_share: float | None) -> bool` (both present, entropy at most `RIFF_ENTROPY_MAX` and share at least `RIFF_SINGLE_PC_MIN`).

- [ ] **Step 1: Write the failing tests** (synthetic signals at 22050 Hz: `tone(freqs, onsets)` builds decaying sines starting at each onset)

```python
def test_single_note_onsets_read_as_riff():
    y = tone([[196.0]] * 8, onsets=[0.5 * k for k in range(8)], sr=22050)
    chroma = onset_chroma(y, 22050, np.array([0.5 * k for k in range(8)]))
    entropy, share = riff_features(chroma)
    assert entropy < 0.6 and share > 0.9 and is_riff(entropy, share)

def test_four_note_chords_do_not_read_as_riff():
    y = tone([[196.0, 246.9, 293.7, 392.0]] * 8, onsets=[0.5 * k for k in range(8)], sr=22050)
    entropy, share = riff_features(onset_chroma(y, 22050, np.array([0.5 * k for k in range(8)])))
    assert entropy > 0.82 and share < 0.2 and not is_riff(entropy, share)

def test_no_onsets_gives_no_features_and_no_riff():
    assert riff_features(np.zeros((0, 12))) == (None, None)
    assert not is_riff(None, None)

def test_onset_near_the_end_with_no_window_frames_is_a_zero_row():
    chroma = onset_chroma(np.zeros(22050), 22050, np.array([0.99]))
    assert chroma.shape == (1, 12) and not chroma.any()

def test_thresholds_are_the_spec_values():
    assert (RIFF_ENTROPY_MAX, RIFF_SINGLE_PC_MIN) == (0.82, 0.45)
    assert is_riff(0.82, 0.45) and not is_riff(0.83, 0.45) and not is_riff(0.82, 0.44)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_riff.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `riff.py`** with `librosa.cqt` (`fmin=librosa.note_to_hz("C2")`, `n_bins=72`, `bins_per_octave=12`, `hop_length=round(sr * RIFF_HOP_SECONDS)`), power (`abs ** 2`), folded with `reshape(6, 12).sum(axis=0)` per frame.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_riff.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/riff.py tests/test_riff.py
git commit -m "feat: riff features from onset pitch content"
```

---

### Task 5: The strums stage on the plan

**Confidence:** 93%

**Files:**
- Modify: `src/youkelele/stages/strums.py:100-223` (`run`)
- Test: `tests/test_stage_strums.py`

**Interfaces:**
- Consumes: `section_plan`, `longest_member` (Task 2); `structure_test`, `full_vote` (Task 3); `onset_chroma`, `riff_features`, `is_riff` (Task 4); `PlannedSection`, the new `SectionPattern` fields (Task 1).
- Produces: `strums.json` with `plan` set and one `SectionPattern` per planned section (`section` = plan index), each computed over `longest_member`'s bars: `has_instrument`, the recall gate, `section_summary`, `structure_test` (seed = the member range's start bar), the riff features (onsets whose time falls inside the member's bars), `uncertain = confidence < floor or explained < EXPLAINED_BELOW or not long_enough or not structured`; the trailing drop applies to the last planned section; short-section inheritance works over planned sections. Manifest notes: `merged` (`"<n> grid sections into <m>"`, or `"none"`), `one_loop` (`f"{share:.2f}"`, and the stage logs "verse and chorus share their chords" when the share is at least `ONE_LOOP_SHARE`).

- [ ] **Step 1: Write the failing tests** (the file's fake-stem fixtures; a grid whose sections make one fragment)

```python
def test_strums_stage_writes_the_plan_and_one_pattern_per_planned_section(tmp_path):
    # grid: verse 0-16, verse 16-22 (fragment, same chords) -> plan has one section with members [0, 1]
    strums = run_stage(tmp_path, grid_with_fragment, chords_same)
    assert [p.members for p in strums.plan] == [[0, 1]] and len(strums.patterns) == 1
    assert strums.patterns[0].section == 0

def test_merged_section_pattern_comes_from_its_longest_member(tmp_path):
    # member 0-16 strikes every eighth, member 16-22 only downbeats: the pattern is the 0-16 vote
    strums = run_stage(tmp_path, grid_with_fragment, chords_same, onsets=eighths_then_downbeats)
    assert strums.patterns[0].slots == ["D", "U"] * 4

def test_patterns_record_chance_p_and_density_and_a_random_section_is_uncertain(tmp_path):
    strums = run_stage(tmp_path, grid_two_sections, chords, onsets=pattern_then_spray)
    certain, spray = strums.patterns
    assert certain.chance_p is not None and certain.chance_p <= 0.05 and not certain.uncertain
    assert spray.chance_p is not None and spray.chance_p > 0.05 and spray.uncertain

def test_full_vote_section_records_density_and_no_p(tmp_path):
    strums = run_stage(tmp_path, grid_one_section, chords, onsets=every_eighth)
    assert strums.patterns[0].chance_p is None and strums.patterns[0].strike_density == 1.0

def test_riff_flag_and_features_are_recorded_per_section(tmp_path):
    strums = run_stage(tmp_path, grid_two_sections, chords, stem=single_notes_then_chords)
    assert strums.patterns[0].riff and not strums.patterns[1].riff
    assert strums.patterns[0].riff_entropy is not None

def test_no_instrument_section_has_no_riff_features_and_no_p(tmp_path):
    strums = run_stage(tmp_path, grid_with_silent_section, chords)
    silent = next(p for p in strums.patterns if p.no_instrument)
    assert (silent.riff, silent.riff_entropy, silent.chance_p) == (False, None, None)

def test_manifest_notes_merged_and_one_loop(tmp_path):
    notes = run_stage_notes(tmp_path, grid_with_fragment, chords_same)
    assert notes["merged"] == "2 grid sections into 1" and float(notes["one_loop"]) >= 0.85
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stage_strums.py -q`
Expected: the new tests FAIL (`plan` empty, `chance_p` None).

- [ ] **Step 3: Implement** in `run`: `plan = section_plan(grid, chords)`; replace the loops over `grid.sections` with loops over `plan`, taking `(a, b) = longest_member(sec, grid)` for every per-section computation and `analysed_end` applied to the last planned section's member when it is the last; compute the riff features once per planned section from `onsets.times` inside `[bars[a].start, bars[b - 1].end)` on `y` (the chosen source signal); write `plan` into `Strums`; add the two notes and the log lines.

- [ ] **Step 4: Run the stage suite**

Run: `uv run pytest tests/test_stage_strums.py tests/test_as_played.py -q`
Expected: PASS (existing tests whose grids have no fragments produce a plan equal to the default and are unchanged).

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/stages/strums.py tests/test_stage_strums.py
git commit -m "feat: strums stage works on the section plan with the structure test and the riff marker"
```

---

### Task 6: The score builder on the plan

**Confidence:** 93%

**Files:**
- Modify: `src/youkelele/music/score_builder.py:30-49` (`check_strums_match_grid`), `:136-205` (sections)
- Test: `tests/test_score_builder.py`

**Interfaces:**
- Consumes: `Strums.plan`, `ScoreSection.riff`, `ScoreSection.members` (Task 1); `default_plan` (Task 2); `aligned_starts` (unchanged).
- Produces: `check_strums_match_grid(grid, strums)` compares `len(strums.patterns)` with `len(plan)` where `plan = strums.plan or default_plan(grid, chords)`, and every plan span lies inside the grid (fail with the existing "re-run from strums" message); `build_score` builds one `ScoreSection` per planned section, label from the plan, `members` from the plan, `riff` from the pattern, `aligned_starts` over the plan spans, the trailing drop on the last planned section; `refine_labels` is no longer called here (the plan carries it).

- [ ] **Step 1: Write the failing tests**

```python
def test_build_score_follows_the_plan_and_records_members():
    strums = strums_with_plan([PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])], patterns=[one_pattern])
    score = build_score(source, grid_two_sections, chords, strums, arrangement, tuning, "ukulele")
    assert len(score.sections) == 1 and score.sections[0].members == [0, 1]
    assert [b.index for b in score.sections[0].bars] == list(range(16))

def test_build_score_without_a_plan_uses_one_section_per_grid_section():
    strums_14 = Strums.model_validate_json(FIXTURE_14_STRUMS)
    score = build_score(source, grid_for_fixture, chords_for_fixture, strums_14, arrangement, tuning, "ukulele")
    assert [s.members for s in score.sections] == [[i] for i in range(len(grid_for_fixture.sections))]

def test_check_strums_match_grid_compares_against_the_plan():
    strums = strums_with_plan([PlannedSection(start_bar=0, end_bar=16, label="verse", members=[0, 1])], patterns=[one_pattern, one_pattern])
    with pytest.raises(ValueError, match="re-run from strums"):
        check_strums_match_grid(grid_two_sections, strums, chords)

def test_riff_flag_reaches_the_score_section():
    score = build_score(source, grid_one_section, chords, strums_with(riff=True), arrangement, tuning, "ukulele")
    assert score.sections[0].riff
```

Note `check_strums_match_grid` gains a `chords` parameter (it needs `default_plan`); update its two callers.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_score_builder.py -q`
Expected: FAIL (`members` empty, section count mismatch).

- [ ] **Step 3: Implement** the changes in `score_builder.py`; `check_strums_match_grid(grid, strums, chords)`.

- [ ] **Step 4: Run the suites**

Run: `uv run pytest tests/test_score_builder.py tests/test_stage_score.py tests/test_end_to_end.py -q -m "not slow"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/score_builder.py src/youkelele/stages/score.py tests/test_score_builder.py
git commit -m "feat: score builder prints the planned sections with their members and riff flag"
```

---

### Task 7: Three tonic votes and the hedge

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/music/key.py:276-283` (`decide_tonic`), `:322-345` (`key_and_decision`), `:440-485` (`_hedge`, `hedge_text`); `src/youkelele/stages/harmony.py:61-64` (`_key_log`), `:140-143` (notes)
- Test: `tests/test_key.py`, `tests/test_stage_harmony.py`

**Interfaces:**
- Consumes: `TonicDecision.pair_tonic`, `pair_rule`, `_winner`, `_mode_of`, `Key.mix` (unchanged); `TonicVotes`, `Key.pair_tonic`, `Key.tonic_votes` (Task 1).
- Produces: `TonicDecision.score_tonic: str` (the score rule's winner before any override); `decide_tonic` applies spec 6.1: close score margin leaves the 1.4 behaviour (`rule="pair rule"`, `decided_by="pair rule"`); otherwise agreement (`decided_by="agreement"`), else the mix decides between the two (`decided_by="mix"`), else the score (`decided_by="score"`); `decide_tonic` gains `mix_tonic: str | None` as its last parameter. `key_and_decision` sets `pair_tonic` and `tonic_votes`. `_hedge(key) -> tuple[str, Literal["runner_up", "chord rule", "mix"]] | None` with the three rungs of spec 6.2 (rung 2 names the losing chord rule's tonic when `tonic_votes.decided_by` is `"mix"` or `"score"`). `hedge_text` unchanged in signature. `_key_log` appends `decided by <decided_by>`; harmony notes `tonic_votes` as `"score C, pair F, mix F, decided by mix"`.

- [ ] **Step 1: Write the failing tests** (events built with the file's helpers so that the score and pair rules disagree)

```python
def test_two_of_three_mix_decides_when_the_chord_rules_disagree():
    decision = decide_tonic(events_score_c_pair_f, bars, sections, chroma_f, mix_tonic="F")
    assert (decision.tonic, decision.score_tonic, decision.pair_tonic) == ("F", "C", "F")
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma_f, mix_key_f)
    assert key.tonic_votes == TonicVotes(score="C", pair="F", mix="F", decided_by="mix")
    assert key_text(key) == "F major (or C major)"

def test_score_leads_when_the_mix_names_neither():
    key, _ = key_and_decision(events_score_c_pair_f, bars, sections, chroma_f, mix_key_g)
    assert key.tonic == "C" and key.tonic_votes.decided_by == "score"
    assert key_text(key) == "C major (or F major)"

def test_agreement_records_itself_and_the_mix_only_hedges():
    key, _ = key_and_decision(events_clear_g, bars, sections, chroma_g, mix_key_d)
    assert key.tonic_votes.decided_by == "agreement" and key_text(key) == "G major (or D major)"

def test_close_score_margin_keeps_the_pair_rule_decision_and_runner_up_hedge():
    key, decision = key_and_decision(events_close_d_a, bars, sections, chroma_d, mix_key_d)
    assert decision.rule == "pair rule" and key.tonic_votes.decided_by == "pair rule"

def test_no_mix_estimate_falls_to_the_score_without_raising():
    decision = decide_tonic(events_score_c_pair_f, bars, sections, chroma_f, mix_tonic=None)
    assert decision.tonic == "C"

def test_pre_1_5_key_without_votes_hedges_as_1_4_did():
    key = Key.model_validate_json(FIXTURE_14_KEY_JSON)
    assert hedge_text(key) == EXPECTED_14_HEDGE  # the fixture's 1.4 text
```

And in `tests/test_stage_harmony.py`: the manifest note `tonic_votes` is present and the log line ends with `decided by agreement` on the stage's fixture.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_key.py tests/test_stage_harmony.py -q`
Expected: FAIL (`TypeError` on `mix_tonic`, missing `score_tonic`).

- [ ] **Step 3: Implement** per Interfaces; `hedge_mode` is computed at whichever tonic `hedge_tonic` names, as today.

- [ ] **Step 4: Run the suites**

Run: `uv run pytest tests/test_key.py tests/test_stage_harmony.py tests/test_score_builder.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/key.py src/youkelele/stages/harmony.py tests/test_key.py tests/test_stage_harmony.py
git commit -m "feat: tonic by two of three rules with the loser hedged"
```

---

### Task 8: The strip beside the rows, the riff wording and the easy power line

**Confidence:** 93%. The layout and page counts were measured with the production renderer (spec 5.3, A16); the CSS is the measured variant.

**Files:**
- Modify: `src/youkelele/render/strum_box.py` (beside `example_bars`, line 101), `src/youkelele/render/html.py:27-29` (constants), `:92-96` (power lines), `:100-125` (section context), `src/youkelele/render/templates/sheet.html.j2:21-49` (CSS), `:100-144` (section markup)
- Test: `tests/test_strum_box.py`, `tests/test_html.py`

**Interfaces:**
- Consumes: `example_bars` (unchanged), `ScoreSection.riff` (Task 1).
- Produces: `strip_bars(section: ScoreSection) -> list[ScoreBar]` (the example bars when any of them has more than one chord, else the first alone); `POWER_LEGEND_EASY` (Global Constraints); section context gains `beside: bool` (`show_box and len(bars) == 1`) and `riff: bool`; template: a `beside` strip renders inside `<div class="section-body beside">` after the grid, otherwise above the rows as today; the riff wording replaces the strum label when `section.riff`; `power_lines` uses `POWER_LEGEND` in the full tier and `POWER_LEGEND_EASY` in the easy tier; CSS exactly as spec 5.2.

- [ ] **Step 1: Write the failing tests**

```python
def test_strip_bars_is_one_bar_unless_a_shown_bar_changes_inside():
    assert len(strip_bars(section_two_plain_bars)) == 1
    assert len(strip_bars(section_with_mid_bar_change)) == 2
    assert len(strip_bars(section_single_bar_with_change)) == 1

def test_one_bar_strip_renders_beside_the_rows():
    html = render_html(score_with_plain_section)
    assert 'class="section-body beside"' in html and html.index("<div class=\"grid") < html.index("worked-example")

def test_two_bar_strip_stays_above_the_rows():
    html = render_html(score_with_mid_bar_change)
    assert "section-body beside" not in html and html.index("worked-example") < html.index("<div class=\"grid")

def test_beside_layout_keeps_the_pickup_column_and_single_row():
    html = render_html(score_with_pickup_and_one_row)
    assert ".section-body.beside .grid.has-pickup .row" in html and 'class="section-body beside"' in html

def test_riff_section_prints_the_riff_wording():
    html = render_html(score_with_riff_section)
    assert "Riff heard in this section: strum the chord to this rhythm" in html and "Strum heard in this section" not in html

def test_easy_tier_prints_the_power_line_with_the_triad_clause():
    html = render_html(score_easy_with_power)
    assert "Am is a power chord (root and fifth) on the record; this sheet prints the triad." in html
    assert "<sup>5</sup>" not in html  # badge still full-tier only

def test_full_tier_power_line_unchanged():
    assert "Am is a power chord on the record" in render_html(score_full_with_power)
```

Update `tests/test_html.py:372-376` (the easy-tier test that asserted "power chord" absent) to the new expectation.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_strum_box.py tests/test_html.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement**: `strip_bars`; `html.py` uses it, adds `beside` and `riff` to the context, chooses the power line by tier; the template moves the strip and adds the three CSS rules from spec 5.2 before `@page`; the riff `<span class="strum-label">` keeps the covers figure and the `(uncertain)` suffix as the strum wording does.

- [ ] **Step 4: Run the render suites and one real render**

Run: `uv run pytest tests/test_strum_box.py tests/test_html.py tests/test_stage_render.py tests/test_render_grid.py -q`
Expected: PASS. Then render one stored 1.4 `score.json` through `render_html` into `%TEMP%` and open it to see a beside strip (a visual check, recorded in the report).

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/render tests/test_strum_box.py tests/test_html.py
git commit -m "feat: one-bar strip beside the rows, riff wording, power line on the easy sheet"
```

---

### Task 9: `evaluate` and the compare harness

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/evaluate.py:31-48` (`SectionDiag`), `:201-237` (`_section_diags`), `:373-393` (`_section_line`, `_key_line`), `:326-364` (`compare_runs`), `:421-440` (`_cell`, `_delta`)
- Test: `tests/test_evaluate.py`

**Interfaces:**
- Consumes: `Strums.plan`, the new `SectionPattern` and `Key` fields (Task 1); `default_plan`, `longest_member` (Task 2).
- Produces: `SectionDiag` gains `members: list[int]`, `member_labels: list[str]`, `chance_p: float | None`, `strike_density: float | None`, `riff: bool`, `riff_entropy: float | None`, `riff_single_share: float | None`; `_section_diags` iterates `strums.plan or default_plan(grid, chords)` and measures over `longest_member`; `_section_line` prints `  2 verse (grid 4, 5, 6: verse, verse, verse) bars 55-110: strikes/bar 3.1, explained 100.0%, rests 25.0%, p 0.003, density 0.58, riff 0.66/0.58 riff` (the `(grid ...)` group only when there is more than one member; `p n/a` for a full vote; the trailing `riff` word only when flagged); `_key_line` appends `, votes score C pair F mix F (mix)` when `tonic_votes` is set; the comparison cell prints `p` and the riff flag beside the existing figures and marks a flag change as a delta.

- [ ] **Step 1: Write the failing tests**

```python
def test_section_line_prints_members_p_density_and_riff():
    d = SectionDiag(index=2, label="verse", strikes_per_bar=3.1, explained=1.0, rest_share=0.25, uncertain=False, recall_boost=False,
                    start_bar=55, end_bar=110, members=[4, 5, 6], member_labels=["verse"] * 3, chance_p=0.003, strike_density=0.58,
                    riff=True, riff_entropy=0.66, riff_single_share=0.58)
    assert _section_line(d) == "  2 verse (grid 4, 5, 6: verse, verse, verse) bars 55-110: strikes/bar 3.1, explained 100.0%, rests 25.0%, p 0.003, density 0.58, riff 0.66/0.58 riff"

def test_section_diags_follow_the_plan_and_a_1_4_file_has_one_per_grid_section():
    diags = _section_diags(grid, strums_with_plan, chords)
    assert [d.members for d in diags] == [[0, 1]]
    assert [d.members for d in _section_diags(grid, strums_14, chords)] == [[i] for i in range(len(grid.sections))]

def test_key_line_prints_the_votes():
    key = Key(tonic="F", mode="major", confidence=0.1, tonic_votes=TonicVotes(score="C", pair="F", mix="F", decided_by="mix"))
    assert _key_line(key).endswith("votes score C pair F mix F (mix))")

def test_comparison_cell_shows_p_and_riff_and_flags_a_change():
    c = compare_runs(run_a, run_b)  # fixtures where one section's riff flag differs
    assert "riff" in format_comparison(c) and any(delta.changed for delta in c.sections)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_evaluate.py -q`
Expected: FAIL (`TypeError` on the new `SectionDiag` fields).

- [ ] **Step 3: Implement** per Interfaces.

- [ ] **Step 4: Run the suite**

Run: `uv run pytest tests/test_evaluate.py tests/test_cli.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/evaluate.py tests/test_evaluate.py
git commit -m "feat: evaluate prints the planned sections, the structure test, the riff features and the tonic votes"
```

---

### Task 10: Version, README and the limitation text

**Confidence:** 96%

**Files:**
- Modify: `pyproject.toml:3`, `src/youkelele/__init__.py:1`, `uv.lock` (via `uv lock`), `README.md` (Known limitations, the stage table's strums and score rows, the project history list)
- Test: `tests/test_readme.py` (the existing checks on commands and the history list)

**Interfaces:** none produced; consumes nothing from code.

- [ ] **Step 1: Write the failing test**

```python
def test_readme_states_the_1_5_limitation_and_history():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "splitting the onsets by pitch register" in text  # the two-guitar limitation, spec 4.2 wording
    assert "Riff heard in this section" in text
    assert "1.5" in text and "0.6.0" in text
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_readme.py -q`
Expected: FAIL.

- [ ] **Step 3: Edit**: version 0.6.0 in the two files and `uv lock`; README Known limitations: replace the power-chord bullet (the easy sheet now prints the line; the badge stays full-tier), add the two-guitar paragraph verbatim from spec 4.2, add a riff-marker bullet (what the wording means, and that a tight power-chord strum can read as a riff); the stage table rows for strums (plan, structure test, riff) and score (sections from the plan); the history list gains a 1.5 entry pointing at the spec and, after Task 11, the validation document. No time or effort estimates.

- [ ] **Step 4: Run the suites**

Run: `uv run pytest tests/test_readme.py -q` then the fast suite `uv run pytest -q -W error -m "not slow"`.
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/youkelele/__init__.py uv.lock README.md tests/test_readme.py
git commit -m "docs: README and version 0.6.0 for 1.5"
```

---

### Task 11: Validation on seven songs and one blind song

**Confidence:** 92%. The expectations are written in spec 8; the blind song is unknown by design (A23).

**Files:**
- Create: `docs/superpowers/specs/2026-10-04-v1-5-validation.md`
- Modify: `README.md` (the validation link in the history list); the eight run folders under `C:\Users\gethi\sources\Youkelele\runs\` (re-runs), `%TEMP%\youkelele-v15-validation\` (baselines, scratch)

**Interfaces:** consumes everything above through the CLI (`uv run youkelele run`, `status`, `evaluate`, `evaluate --compare`).

- [ ] **Step 1: Copy the baselines** of all seven 1.4 folders (`02_grid` to `07_render`, `manifest.json`, and `evaluate` output) to `%TEMP%\youkelele-v15-validation\baseline\<folder>\`.

- [ ] **Step 2: Re-run**: Need You Tonight `--from harmony`; the other six `--from strums`; the blind song `https://www.youtube.com/watch?v=3dOx510kyOs` from ingest into its own folder. Record each run's log.

- [ ] **Step 3: Measure every expectation in spec 8** with the harness (`compare_runs` baseline against new, bar by bar on `grid.json`, `chords.json`, `strums.json`), `evaluate` on all eight, page counts from the PDFs, and rasterise every page (PyMuPDF venv at `…\scratchpad\pwvenv\Scripts\python.exe`, found by glob) and look at each. Yes or no per row, with the figure.

- [ ] **Step 4: Write the validation document**: runs and baselines; the expectations table with yes or no; per song (sections, pages, flips, riff flags, header, the power line); the blind song (key with its three votes, sections, riff flags, certainty, pages, power gates, what cannot be verified without listening); "What to improve next", ranked; clips prepared for the owner's listening pass (merged All Fired Up sections, flipped sections, the blind song's key and one strummed section) under `%TEMP%\youkelele-ear-v15\` with a one-line list of what each tests. Anything that misses is recorded, not tuned.

- [ ] **Step 5: Verify, link, commit**

Run: `uv run pytest -q -W error -m "not slow"` and `uv run pytest -q -m slow`.
Expected: both green. Then the README history link, and:

```bash
git add docs/superpowers/specs/2026-10-04-v1-5-validation.md README.md
git commit -m "docs: validate version 1.5 on seven real songs and one blind song"
```
