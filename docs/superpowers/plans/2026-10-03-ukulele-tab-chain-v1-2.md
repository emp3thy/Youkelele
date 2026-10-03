# Ukulele Tab Chain v1.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten the `youkelele` chord sheet: merge short sections, collapse repeating row blocks, align rows to phrases, clean titles, fill no-chord bars where the band plays, give passing chords no diagram, show the mean tempo, and draw the pickup as a narrow cell.

**Architecture:** The chain and its file contracts are unchanged. Detection-side changes land in the stage that owns the data (grid, ingest, harmony, arrange, score); presentation changes land in `render/grid.py` and the template. Every schema addition has a default, so version 1.1 run folders still load and resume.

**Tech Stack:** Python 3.12, pydantic 2, librosa, numpy, mir_eval, Jinja2, Playwright 1.63.0, pytest, pypdf (dev).

**Spec:** `docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-2-design.md` (read it first). Evidence: `docs/superpowers/specs/2026-10-03-v1-1-validation.md`.

## Global Constraints

- Section minimum is 4 bars (`MIN_SECTION_BARS = 4`), applied in `boundaries_from_clusters` by the grid stage; the clustering constant `MIN_SEGMENT_BARS` in `music/sections.py` is unrelated and unchanged.
- Header tempo is 60 / mean gap-filled beat interval at the final octave; the octave decision keeps the median-based tempo.
- Passing chord: covers less than 2% of the song's chord time and no event longer than one bar.
- Phrase alignment moves a section start by at most one bar, later only, never past the next boundary, never leaving a section under 4 bars, never the first section.
- Filling constants (`FILL_MIN_ENERGY`, `FILL_MIN_MATCH`, `FILL_MIN_MARGIN`) are set by measurement on real stems and recorded beside the constants with their evidence; filling uses only chord labels the song already contains.
- Schema version stays 1. New fields: `SourceInfo.raw_title: str | None = None`; `ChordEvent.filled: bool = False`; `ArrangedChord.passing: bool = False`; `ChordDiagram.passing: bool = False`; `ScoreChord.filled: bool = False`; `ScoreChord.passing: bool = False`; `ScoreSection.shifted: int = 0`.
- `score.json` stays bar by bar; row and block collapsing happen only in the renderer.
- Fast suite `-W error -m "not slow"` green at every commit. Slow tests run once per task that touches a real model or Chromium.
- Worktree on a feature branch; commit per task with trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; never push from a task.
- uv: `C:\Users\gethi\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe` (not on PATH in Bash).
- UK spelling; no em-dashes in generated output; never write song lyrics anywhere (tests, docs, fixtures).

## Confidence Summary

| Task | Confidence | Evidence |
|---|---|---|
| 1 Four-bar sections, mean tempo | 95% | One constant passed through an existing parameter; one new pure function; measured effect on all four songs |
| 2 Title cleaning | 95% | Pure string function with explicit rules from the spec; the four real titles are the test cases |
| 3 No-chord filling | 90% | Chroma template matching is standard; the constants are measured on the two positive songs and two controls with a defined fallback (conservative values that touch no control bar) if no setting separates them |
| 4 Passing chords | 95% | A share-and-duration rule over existing events |
| 5 Phrase alignment and score flags | 90% | Parity counting is simple; the guard rules are explicit; Summer of '69's verse is the real test case |
| 6 Sheet: blocks, passing line, italics, pickup | 92% | Pure render changes over the existing grid module; visual check on real songs |
| 7 Validation runs and docs | 90% | Full re-runs from URLs, expectations from the spec table |

## Review Focus

1. **A song so short that every segment is under four bars** (a 12-bar clip). Expected: one section, not an empty section list or an error. Test in Task 1.
2. **A title that is nothing but upload tags** (`"(Official Video)"`) or becomes empty after cleaning. Expected: fall back to the raw title, never an empty title. Test in Task 2.
3. **A song whose chord model returned only N**. Expected: no templates, nothing filled, no crash. Test in Task 3.
4. **A song with many rare chords, so the 2% rule would mark nearly all of them passing**. Expected: the legend never drops below three diagrams; the most-used chords keep diagrams. Test in Task 4.
5. **A four-bar section whose rows are a bar out of phase**. Expected: no shift, because shifting would leave three bars. Test in Task 5.

---

### Task 1: Four-bar section minimum and mean-interval tempo

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/music/tempo.py`, `src/youkelele/stages/grid.py`
- Test: `tests/test_tempo.py`, `tests/test_sections.py`, `tests/test_stage_grid.py`

**Interfaces:**
- Consumes: `boundaries_from_clusters(cluster_ids, min_bars=2) -> tuple[list[int], list[int]]` (sections.py:145); `bpm_from_beats(beats) -> float` (median based, tempo.py).
- Produces: `MIN_SECTION_BARS = 4` in `stages/grid.py`, passed as `boundaries_from_clusters(cluster_ids, min_bars=MIN_SECTION_BARS)`; `mean_bpm(beats: Sequence[float]) -> float` in `tempo.py` (60 / mean of consecutive differences; raises `ValueError` for fewer than 2 beats); the grid stage keeps `detected_bpm = bpm_from_beats(...)` for the octave decision and writes `Grid.bpm = mean_bpm(final_beats)`; the log line shows both.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tempo.py
def test_mean_bpm_uses_mean_interval_not_median():
    beats = [0.0, 0.43, 0.86, 1.29, 1.72, 2.20]            # median 0.43 s, mean 0.44 s
    assert mean_bpm(beats) == pytest.approx(60 / 0.44)
def test_mean_bpm_needs_two_beats():
    with pytest.raises(ValueError): mean_bpm([1.0])

# tests/test_sections.py
def test_boundaries_min_four_bars_merges_two_and_three_bar_segments(): ...  # ids A*8,B*2,A*8,C*3,A*8 with min_bars=4 -> no segment under 4 bars
def test_boundaries_min_four_on_twelve_bar_song_gives_one_section(): ...    # Review Focus 1: ids A*3,B*3,C*3,D*3 -> one segment covering 12 bars

# tests/test_stage_grid.py
def test_grid_stage_sections_are_at_least_four_bars(tmp_path): ...         # fake features/clusters producing a 2-bar segment -> merged
def test_grid_stage_bpm_is_mean_interval_octave_uses_median(tmp_path): ... # uneven fake beats around 150 with drums backbeat -> octave none, grid.bpm == mean_bpm
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tempo.py tests/test_sections.py tests/test_stage_grid.py -q -W error -m "not slow"`
Expected: FAIL on missing `mean_bpm` and on short sections.

- [ ] **Step 3: Add `mean_bpm`; pass `MIN_SECTION_BARS` in the grid stage; write `Grid.bpm` from `mean_bpm`.**

- [ ] **Step 4: Run tests; full fast suite green.**

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/tempo.py src/youkelele/stages/grid.py tests/test_tempo.py tests/test_sections.py tests/test_stage_grid.py
git commit -m "feat: four-bar minimum sections and mean-interval tempo"
```

---

### Task 2: Title cleaning at ingest

**Confidence:** 95%

**Files:**
- Create: `src/youkelele/titles.py`, `tests/test_titles.py`
- Modify: `src/youkelele/schemas.py` (`SourceInfo.raw_title`), `src/youkelele/stages/ingest.py`
- Test: `tests/test_stage_ingest.py`, `tests/test_schemas.py`

**Interfaces:**
- Produces: `UPLOAD_TAG_WORDS = ("official", "video", "audio", "lyric", "lyrics", "visualiser", "visualizer", "hd", "hq", "4k", "remaster", "remastered", "live")`; `clean_title(title: str, artist: str | None) -> str` applying, in order: remove a leading `"<artist> - "`, `"<artist> – "` or `"<artist>: "` when it matches `artist` case-insensitively (after cleaning the artist's case); remove each `(...)` or `[...]` group whose text contains any tag word as a whole word, case-insensitive; strip surrounding straight or curly quotes and whitespace; if no lower-case letter remains, title-case it word by word (`w[:1].upper() + w[1:].lower()`); if the result is empty, return the original `title` stripped. `clean_artist(artist: str | None) -> str | None` applies only the title-casing rule. Ingest stores `raw_title=<original>`, `title=clean_title(...)`, `artist=clean_artist(...)`; local files store the stem as both.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_titles.py
@pytest.mark.parametrize("raw,artist,expected", [
    ("The Fratellis - Chelsea Dagger", "The Fratellis", "Chelsea Dagger"),
    ('DEF LEPPARD - "Pour Some Sugar On Me" (Official Music Video)', "DEF LEPPARD", "Pour Some Sugar On Me"),
    ("Wet Leg - mangetout (Official Video)", "Wet Leg", "mangetout"),
    ("Bryan Adams - Summer Of '69 (Official Music Video)", "Bryan Adams", "Summer Of '69"),
    ("Some Band – Song Name [HD]", "Some Band", "Song Name"),
    ("Song Name (Live at Wembley)", "Other Artist", "Song Name"),
    ("Song Name (Acoustic Version)", None, "Song Name (Acoustic Version)"),   # not an upload tag: kept
    ("SHOUTY TITLE", None, "Shouty Title"),
    ("Fame (2016 Remaster)", "David Bowie", "Fame"),
])
def test_clean_title(raw, artist, expected): assert clean_title(raw, artist) == expected
def test_clean_title_never_empty(): assert clean_title("(Official Video)", None) == "(Official Video)"   # Review Focus 2
def test_clean_artist_title_cases_capitals(): assert clean_artist("DEF LEPPARD") == "Def Leppard"; assert clean_artist(None) is None

# tests/test_stage_ingest.py
def test_ingest_url_stores_raw_and_clean_title(tmp_path): ...   # fake info title 'X - Y (Official Video)', artist 'X' -> raw_title kept, title 'Y'
# tests/test_schemas.py
def test_source_info_without_raw_title_loads(): ...            # version 1.1 source.json
```

- [ ] **Step 2: Run tests to verify they fail** (`uv run pytest tests/test_titles.py tests/test_stage_ingest.py tests/test_schemas.py -q -W error -m "not slow"`; ImportError for `titles`).

- [ ] **Step 3: Implement `titles.py`, the schema field and the ingest wiring.**

- [ ] **Step 4: Run tests; full fast suite green.**

- [ ] **Step 5: Commit**

```bash
git add src/youkelele/titles.py src/youkelele/schemas.py src/youkelele/stages/ingest.py tests/test_titles.py tests/test_stage_ingest.py tests/test_schemas.py
git commit -m "feat: clean upload titles at ingest and keep the raw title"
```

---

### Task 3: Fill no-chord bars where the band plays

**Confidence:** 90%

**Files:**
- Create: `src/youkelele/music/fill.py`, `tests/test_fill.py`
- Modify: `src/youkelele/schemas.py` (`ChordEvent.filled`), `src/youkelele/stages/harmony.py`
- Test: `tests/test_stage_harmony.py`

**Interfaces:**
- Consumes: `snap_to_beats(spans, grid) -> list[ChordEvent]` (snap.py:24); `mir_eval.chord.split` and `quality_to_bitmap`; the four stems written by the separate stage.
- Produces, in `music/fill.py`: `FILL_MIN_ENERGY`, `FILL_MIN_MATCH`, `FILL_MIN_MARGIN` (floats, values set in Step 4 with an evidence comment); `chord_template(label: str) -> np.ndarray | None` (12-bin triad template rotated to the root, `None` for N/X or unparsable); `bar_chroma(y: np.ndarray, sr: int, bars: Sequence[Bar]) -> np.ndarray` (bars x 12, mean `librosa.feature.chroma_cqt` per bar, librosa imported lazily); `bar_energy(y, sr, bars) -> np.ndarray` (RMS per bar); `fill_silent_bars(events: list[ChordEvent], bars: Sequence[Bar], chroma: np.ndarray, energy: np.ndarray) -> list[ChordEvent]`: split `N` events at bar boundaries; a bar is a candidate when every event overlapping it is `N`; it is filled when `energy[bar] >= FILL_MIN_ENERGY * median(energy over bars that have a chord)` and the best Pearson correlation between `chroma[bar]` and the templates of the song's distinct non-N labels is `>= FILL_MIN_MATCH` and beats the runner-up by `>= FILL_MIN_MARGIN`; a filled bar becomes one event `ChordEvent(bar=b, beat=0, start=bar.start, end=bar.end, label=<label>, triad=to_triad(label), confidence=<correlation>, filled=True)`; with no non-N labels, return the events unchanged (split only).
- Produces, in the harmony stage: `requires` adds `separate/stems/guitar.wav`, `separate/stems/bass.wav`, `separate/stems/piano.wav`, `separate/stems/other.wav`; after `snap_to_beats`, sum the four stems mono, compute chroma and energy over `grid.bars`, call `fill_silent_bars`; log `N bars filled`; note `filled=<N>`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_fill.py
def test_chord_template_c_major_marks_c_e_g(): ...                  # bins 0, 4, 7 set
def test_chord_template_none_for_n_x_and_bad_labels(): ...
def test_fill_fills_loud_bar_matching_a_song_chord(): ...           # bars 0-3: C,G,N,G; bar 2 chroma = C template, energy high -> bar 2 filled C:maj, filled=True
def test_fill_leaves_quiet_bar_as_n(): ...                          # same but energy low -> stays N
def test_fill_leaves_ambiguous_bar_as_n(): ...                      # chroma equidistant between C and G templates -> stays N
def test_fill_never_introduces_a_chord_not_in_the_song(): ...       # chroma = F template, song has only C and G -> stays N or C/G only if margin met (assert label != "F:maj")
def test_fill_with_only_n_returns_events_unchanged(): ...           # Review Focus 3
def test_fill_splits_multi_bar_n_event_at_bar_boundaries(): ...
# tests/test_stage_harmony.py
def test_harmony_stage_requires_harmonic_stems_and_fills(tmp_path): ...   # fake recogniser leaves one bar N; synthetic stems with a C triad there -> chords.json has a filled event
```

- [ ] **Step 2: Run tests to verify they fail** (`uv run pytest tests/test_fill.py tests/test_stage_harmony.py -q -W error -m "not slow"`).

- [ ] **Step 3: Implement `fill.py` (with provisional constants), the schema field and the stage wiring; tests green.**

- [ ] **Step 4: Measure the constants on real stems**

Use the existing run folders under `C:\Users\gethi\sources\Youkelele\runs\` (read only; write scripts and outputs to the session scratchpad): `sexhetcxqy4` (Chelsea Dagger, positive: intro bars 0 to 8 are N with guitar and bass playing), `0uib9y4ofps` (Pour Some Sugar On Me, positive: the solo, 11 of 17 bars N), `9f06qzcvuhg` (Summer of '69, control) and `lbc6ccztp5e` (Wet Leg, control). For each, load `02_grid/grid.json`, `03_harmony/chords.json` and the four stems, compute per-bar energy ratio and the best and runner-up correlations for every all-N bar, and tabulate them. Choose the three constants so that the positive songs' band-playing bars fill and no control bar that is genuinely silent or unpitched (energy ratio low, or best match low) fills. If no setting separates them, choose conservative values that fill no control bar, record that the positives were only partly filled, and report it. Write the chosen values with a comment citing the table, and save the table to `docs/superpowers/specs/2026-10-03-v1-2-fill-measurements.md`.

- [ ] **Step 5: Run tests; full fast suite green; then `uv run pytest -q -m slow tests/test_stage_harmony.py`.**

- [ ] **Step 6: Commit**

```bash
git add src/youkelele/music/fill.py src/youkelele/schemas.py src/youkelele/stages/harmony.py tests/test_fill.py tests/test_stage_harmony.py docs/superpowers/specs/2026-10-03-v1-2-fill-measurements.md
git commit -m "feat: fill no-chord bars from harmonic stems using the song's own chords"
```

---

### Task 4: Passing chords

**Confidence:** 95%

**Files:**
- Modify: `src/youkelele/schemas.py` (`ArrangedChord.passing`), `src/youkelele/music/arrange.py`, `src/youkelele/stages/arrange.py`
- Test: `tests/test_arrange.py`, `tests/test_stage_arrange.py`

**Interfaces:**
- Produces: `PASSING_SHARE = 0.02`; `MIN_DIAGRAM_CHORDS = 3`; `passing_labels(events: Sequence[ChordEvent], bar_seconds: float) -> set[str]` in `music/arrange.py`: over non-N events (filled events included), a label is passing when its total duration is below `PASSING_SHARE` of the summed non-N duration and no single event of it exceeds `bar_seconds`; if marking them would leave fewer than `MIN_DIAGRAM_CHORDS` distinct non-passing labels, unmark passing labels from the most-used down until `MIN_DIAGRAM_CHORDS` remain or none are passing. The arrange stage passes the median full-bar duration from `grid.bars` and sets `ArrangedChord.passing` for events whose (transposed) label is passing; the decision is made on the original labels before transposition.

- [ ] **Step 1: Write the failing tests**

```python
def test_passing_label_is_rare_and_short(): ...          # C 60 s, G 60 s, Am 40 s, B one 0.9 s event (bar 2 s) -> {"B:maj"}
def test_long_single_event_is_not_passing(): ...         # B one 3 s event (bar 2 s), share 1.8% -> not passing
def test_common_label_is_not_passing(): ...
def test_never_fewer_than_three_diagram_chords(): ...    # Review Focus 4: five labels each 1% -> at most two passing, the three most used keep diagrams
# tests/test_stage_arrange.py
def test_arrange_stage_flags_passing_chords(tmp_path): ...
```

- [ ] **Step 2: Run tests to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green.**
- [ ] **Step 4: Commit**

```bash
git add src/youkelele/schemas.py src/youkelele/music/arrange.py src/youkelele/stages/arrange.py tests/test_arrange.py tests/test_stage_arrange.py
git commit -m "feat: flag rare short chords as passing"
```

---

### Task 5: Phrase alignment and score flags

**Confidence:** 90%

**Files:**
- Create: `src/youkelele/music/phrase.py`, `tests/test_phrase.py`
- Modify: `src/youkelele/schemas.py` (`ScoreChord.filled`, `ScoreChord.passing`, `ChordDiagram.passing`, `ScoreSection.shifted`), `src/youkelele/music/score_builder.py`
- Test: `tests/test_score_builder.py`

**Interfaces:**
- Consumes: `build_score(source, grid, chords, strums, arrangement, tuning, instrument_name) -> Score`; `ChordEvent.filled` (Task 3); `ArrangedChord.passing` (Task 4).
- Produces, in `music/phrase.py`: `MIN_SECTION_BARS = 4`; `PHRASE_MIN_CHANGES = 4`; `PHRASE_MIN_SHARE = 0.75`; `change_bars(bar_labels: Sequence[str]) -> list[int]` (bar indices whose first chord differs from the previous bar's last chord); `aligned_starts(section_ranges: Sequence[tuple[int, int]], changes: Sequence[int]) -> list[tuple[int, int, int]]` returning `(start, end, shifted)` per section: for every section except the first, count the chord changes inside it at even and odd offsets from its start; shift its start (and the previous section's end) by +1 when the odd count is at least `PHRASE_MIN_CHANGES`, the odd share of the section's changes is at least `PHRASE_MIN_SHARE`, and both affected sections keep at least `MIN_SECTION_BARS` bars; otherwise `shifted = 0`.
- Produces, in `build_score`: sections are built from `aligned_starts` (grid.json unchanged); `ScoreSection.shifted` set; each `ScoreChord` copies `filled` from its event and `passing` from its arranged chord; `ChordDiagram.passing` is true when the diagram's chord is passing; passing chords still get a `ChordDiagram` entry (so cells can reference it) flagged passing.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_phrase.py
def test_change_bars(): assert change_bars(["D","D","A","A","D"]) == [2, 4]
def test_section_starting_mid_phrase_shifts_by_one(): ...   # sections (0,8),(8,24); second section's chords change on bars 9,11,13,...: -> (0,9,0),(9,24,1)
def test_in_phase_section_not_shifted(): ...
def test_first_section_never_shifted(): ...
def test_four_bar_section_not_shifted_to_three(): ...       # Review Focus 5
def test_shift_never_leaves_previous_section_under_four(): ...
# tests/test_score_builder.py
def test_score_copies_filled_and_passing_flags(): ...
def test_passing_diagram_flagged(): ...
def test_score_sections_use_aligned_starts_and_record_shift(): ...
def test_every_bar_still_has_slots_per_bar_slots_after_alignment(): ...
```

- [ ] **Step 2: Run tests to verify they fail.**
- [ ] **Step 3: Implement `phrase.py`, the schema fields and the score builder changes; check `check_strums_match_grid` still compares against grid sections (alignment does not change section count).**
- [ ] **Step 4: Run tests; full fast suite green.**
- [ ] **Step 5: Commit**

```bash
git add src/youkelele/music/phrase.py src/youkelele/schemas.py src/youkelele/music/score_builder.py tests/test_phrase.py tests/test_score_builder.py
git commit -m "feat: align section rows to chord-change phrases and carry filled and passing flags"
```

---

### Task 6: Sheet: repeated blocks, passing line, filled italics, narrow pickup

**Confidence:** 92%

**Files:**
- Modify: `src/youkelele/render/grid.py`, `src/youkelele/render/html.py`, `src/youkelele/render/templates/sheet.html.j2`
- Test: `tests/test_render_grid.py`, `tests/test_html.py`, `tests/test_stage_render.py`

**Interfaces:**
- Consumes: `ScoreChord.filled`, `ScoreChord.passing`, `ChordDiagram.passing`, `ScoreBar.pickup` (Task 5 and version 1.1).
- Produces, in `render/grid.py`: `Cell` gains `filled: bool = False` (true when every chord in the bar is filled); `@dataclass Block(rows: list[list[Cell]], repeat: int)`; `@dataclass SectionGrid(pickup: Cell | None, blocks: list[Block])`; `section_grid(section: ScoreSection, per_row: int = 4) -> SectionGrid`: a leading pickup bar becomes `pickup`; the remaining bars chunk into rows of `per_row`; then, scanning from the first row, at each position choose the unit length `u` in 1..4 and repeat count `r >= 2` (the unit's rows repeat exactly, comparing cell texts and row lengths) that maximise `u * r`, ties to the smaller `u`; emit `Block(rows=unit, repeat=r)` and advance; when no unit repeats, emit `Block(rows=[row], repeat=1)`. `grid_rows` is removed (update its tests to `section_grid`). `fret_notation(shape: Shape) -> str`: absolute frets in diagram order, `x` for muted, digits concatenated, or joined with `-` if any fret is 10 or more.
- Produces, in `html.py` and the template: the legend omits passing diagrams; below it `Passing: <name> <frets>, ...` when any; cells with `filled` render the text in italics (`.cell.filled { font-style: italic }`); when any cell is filled the header carries "Italic chords were inferred where the recording had no clear chord"; a block prints its rows with `×N` once on the right of the block's last row (or a bracket spanning the rows), only when `repeat > 1`; the pickup prints as a narrow leading cell (`grid-template-columns: 0.25fr repeat(4, 1fr) auto` on the first row of the section; other rows keep `repeat(4, 1fr) auto` with an empty leading track only when the section has a pickup, so columns line up).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_render_grid.py
def test_section_grid_collapses_alternating_two_row_block(): ...   # rows G-row, D-row x5 -> one Block(rows=[G,D], repeat=5)
def test_section_grid_prefers_larger_coverage_then_smaller_unit(): ...
def test_section_grid_remainder_after_block(): ...                # G,D,G,D,C -> Block([G,D],2), Block([C],1)
def test_section_grid_single_identical_rows_still_collapse(): ... # u=1 path unchanged
def test_section_grid_pickup_is_separate_from_blocks(): ...
def test_cell_filled_when_all_chords_filled(): ...
def test_fret_notation(): assert fret_notation(Shape(frets=[4,3,2,2], fingers=[3,2,1,1], base_fret=1, barres=[2])) == "4322"
# tests/test_html.py
def test_passing_chord_omitted_from_legend_and_listed(): ...      # "Passing: B 4322"
def test_filled_cell_italic_and_header_note(): ...
def test_block_repeat_marker_printed_once(): ...                  # "×5" appears once for the alternating block
def test_pickup_is_narrow_leading_cell_not_its_own_row(): ...
```

- [ ] **Step 2: Run tests to verify they fail.**
- [ ] **Step 3: Implement; tests green; full fast suite green; `uv run pytest -q -m slow tests/test_stage_render.py`.**
- [ ] **Step 4: Visual check**: re-render page 1 of the Chelsea Dagger and Summer of '69 sheets from their existing `06_score/score.json` into the session scratchpad (do not write into the run folders), rasterise with PyMuPDF from the scratchpad `pwvenv`, and look: blocks read clearly, `×N` placement is unambiguous, the pickup cell sits at the start of the first row. Fix what is clearly wrong.
- [ ] **Step 5: Commit**

```bash
git add src/youkelele/render tests/test_render_grid.py tests/test_html.py tests/test_stage_render.py
git commit -m "feat: collapse repeating row blocks, list passing chords, italicise filled chords, narrow pickup"
```

---

### Task 7: Validation runs and docs

**Confidence:** 90%

**Files:**
- Create: `docs/superpowers/specs/2026-10-03-v1-2-validation.md`
- Modify: `README.md` (Known limitations), `docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-1-design.md` (one-line pointer to v1.2 at the top)

**Interfaces:**
- Consumes: five URLs: `https://www.youtube.com/watch?v=sEXHeTcxQy4`, `https://www.youtube.com/watch?v=9f06QZCVUHg`, `https://www.youtube.com/watch?v=0UIB9Y4OFPs`, `https://www.youtube.com/watch?v=lbc6CcZTp5E`, and the new blind song `https://www.youtube.com/watch?v=Ypgq0qdgVZA` (David Bowie, "Fame (2016 Remaster)", 261 s, no earlier run folder); runs dir `C:\Users\gethi\sources\Youkelele\runs`.

- [ ] **Step 1: Save the version 1.1 sheets** (`07_render/sheet.pdf` and `06_score/score.json` of the four existing folders) to the session scratchpad under `v1_1_baseline/<folder>/`. "Fame" has no baseline.
- [ ] **Step 2: Run each of the five songs through the whole chain** with default settings from the worktree: `uv run youkelele run "<url>" --runs-dir C:\Users\gethi\sources\Youkelele\runs`. For "Fame", record everything the spec's validation row asks and state plainly what cannot be verified without listening.
- [ ] **Step 3: Evaluate against spec section 6** and write `2026-10-03-v1-2-validation.md`: a summary table (song, clean title, tempo header vs published, sections and shortest section, filled bars, passing chords, shifted sections, pages v1.1 vs v1.2, verdict); per song a yes/no for every expectation, a quality assessment and a completeness assessment; every page of every sheet looked at (rasterised from the scratchpad); a ranked "What to improve next" with evidence. No lyrics.
- [ ] **Step 4: Update README Known limitations and the v1.1 spec pointer.**
- [ ] **Step 5: Run `uv run pytest -q -W error -m "not slow"` and `uv run pytest -q -m slow`; both green.**
- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-10-03-v1-2-validation.md README.md docs/superpowers/specs/2026-10-03-ukulele-tab-chain-v1-1-design.md
git commit -m "docs: validate version 1.2 on four real songs"
```

---

## Self-review notes

- **Spec coverage.** 3.1 four-bar sections: Task 1. 3.2 mean tempo: Task 1. 3.3 titles: Task 2. 3.4 filling: Task 3 (and italics in Task 6). 3.5 passing: Task 4 (presentation Task 6). 3.6 phrase alignment: Task 5. 4 sheet: Task 6. 5 data formats: Tasks 2 to 5. 6 validation: Task 7.
- **Rulings taken while planning:** passing chords keep a `ChordDiagram` entry flagged passing so cells and the "Passing" line can find their shapes; a floor of three diagram chords prevents an empty legend (Review Focus 4); the first section is never shifted because there is no previous section to absorb its first bar; `grid_rows` is replaced by `section_grid`.
- **Type consistency checked:** `MIN_SECTION_BARS` is defined in both `stages/grid.py` and `music/phrase.py` with the same value 4 (each module owns its rule; the plan names both); `ChordEvent.filled` (Task 3) feeds `ScoreChord.filled` (Task 5) feeds `Cell.filled` (Task 6); `ArrangedChord.passing` (Task 4) feeds `ScoreChord.passing` and `ChordDiagram.passing` (Task 5) feed the legend (Task 6).
