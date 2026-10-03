# Song structure segmentation and section labelling: applied to the Youkelele code

Date: 2026-10-03. Apply agent for the strand "Song structure segmentation and section labelling". Input: `structure-research.md` (same folder). Code read: `src/youkelele/music/sections.py`, `stages/grid.py`, `stages/strums.py`, `stages/score.py`, `music/score_builder.py`, `render/html.py`, `render/grid.py`, `render/templates/sheet.html.j2`, `schemas.py`, `evaluate.py`, `cli.py`, `tests/test_sections.py`, `tests/test_stage_grid.py`, plus the version 1.2 worktree's `stages/grid.py` and `music/fill.py` (read only). Run artefacts read: `runs/{sexhetcxqy4,9f06qzcvuhg,0uib9y4ofps,lbc6ccztp5e}/02_grid/grid.json`, `03_harmony/chords.json`, `04_strums/strums.json`, `06_score/score.json`, and the six stems under `01_separate/stems/`. Nothing under the project was changed.

Line numbers refer to `main` (`C:\Users\gethi\sources\Youkelele\src\youkelele\...`) unless marked "worktree", which means `.claude\worktrees\v1-2`.

## 0. How the findings were tested

Rather than reason from the research alone, every finding that could be measured on this pipeline was measured. Four scripts in this folder (`structure_experiments.py`, `structure_experiments2.py`, `structure_experiments3.py`, `structure_experiments4.py`) import the project's own `sections.py` from `main`, recompute the bar features from `00_ingest/audio.wav` with `bar_features`, and re-run `_embedding`, `_cluster`, the split-k rule and `boundaries_from_clusters` exactly as the grid stage does. Sanity check: with `min_bars=2` the recomputed boundaries equal the stored `sections` on all four songs (same k: 3, 4, 3, 5), so every variant below is a controlled change against the shipped method. Boundary scores use `mir_eval.segment.detection` (installed 0.8.2) with `window = median bar seconds + 0.05`, `beta = 0.58`, `trim = True`, against the owner hand lists `spike_grid3/ref_s69.json` (13 boundaries) and `ref_pssom.json` (12 boundaries, shifted +25.2 s for the music-video upload). "hits@1" counts reference boundaries with an estimate within one bar. Chelsea Dagger and Wet Leg have no reference; their results are reported as section lists.

Per-bar stem levels (RMS of each stem over the bar, divided by the mix RMS) were computed from the six Demucs stems, which already exist before the grid stage runs. Chord-based measurements use the version 1.1 `chords.json` events.

## 1. Where the stage stands today (measured)

| Song | bars | k | largest share | chorus margin dB | sections (v1.1, min 2 bars) | sections at min 4 bars (v1.2 rule, recomputed) | F0.58 at one bar (v1.2 rule) | hits@1 |
|---|---|---|---|---|---|---|---|---|
| Chelsea Dagger | 142 | 3 | 0.577 | 1.43 | 8, lengths 9 29 23 10 22 6 6 37 | 8, unchanged | no reference | |
| Summer of '69 | 121 | 4 | 0.496 | 0.70 | 11, lengths 4 15 12 10 12 5 11 14 12 16 10 | 11, unchanged | 0.609 (P 0.636, R 0.538) | 8/13 |
| Pour Some Sugar On Me | 103 | 3 | 0.485 | 0.93 | 7, lengths 11 17 11 16 12 17 19 | 7, unchanged | 0.484 (P 0.571, R 0.333) | 4/12 |
| Wet Leg "mangetout" | 113 | 5 | 0.425 | 0.75 | 25, 17 of them 2 or 3 bars | 9, lengths 5 13 15 9 16 7 35 8 5 | no reference | |

All four runs carry `labels_low_confidence: true` and every one of the 51 sections has `confidence: 0.3` (`sections.py:226`). Section lengths that are not a multiple of four bars: Chelsea 8 of 8, Summer of '69 6 of 11, Pour Some Sugar 5 of 7, Wet Leg (at min 4) 9 of 9.

Labels that are wrong against the stems or the published form:

- Chelsea: `verse 0-9` and `chorus 9-38` while the vocal stem is silent for bars 0 to 19 (vocal/mix ratio 0.00 on every one of those bars); `chorus 93-99` and `bridge 99-105` have vocal share 0.00 (the 16-bar instrumental break, bars 93 to 107).
- Summer of '69: `verse 2 0-4` is the guitar intro (vocal share 0.25); `verse 2 58-69` is the F Bb C bridge; the solo (hand list 114.8 to 128.6 s, bars 67 to 74) is inside `verse 69-83`, whose vocal share is 0.57 because bars 69 to 74 have no vocal.
- Pour Some Sugar: the solo and breakdown print as `verse 67-84` (vocal share 0.41; bars 67 to 76 have vocal/mix 0.00 to 0.08 and drums 0.83 to 0.97).
- Wet Leg: at the v1.2 four-bar minimum the once-only cluster covering bars 65 to 100 (35 bars, the whole second half of the song) is labelled `bridge` by the once-only rule at `sections.py:235-242`; the opening is `verse 2`.

## 2. Research findings against this codebase

| Research finding | Verdict here | Measured evidence |
|---|---|---|
| 1. Chroma recurrence cannot separate sections sharing a progression; arrangement cues (stems) are needed | Applies, but as a post-pass on vocal runs, not as extra embedding features | Vocal-run boundaries lift Summer of '69 to F 0.735 (hits@1 10/13) and Pour Some Sugar to 0.555 (5/12); adding stem levels to the embedding's path graph changes nothing, adding them to the recurrence graph lowers Summer of '69 to 0.588 and Pour Some Sugar to 0.363 |
| 2. Loudest-cluster chorus is weak; use a Van Balen chorusness score | Discard the score; keep loudness; replace only the flag | The z-scored chorusness (loudness, centroid, MFCC variance, vocal, minus loudness IQR) flips Chelsea's correct chorus to the verse cluster (verse cluster: MFCC variance 327 against 199, IQR 0.5 against 0.9, vocal 0.83 against 0.74). Loudness alone is right on the 3 of 3 verifiable songs; the 1.5 dB flag fires on 4 of 4 |
| 3. Pop sections are 8-bar regular; add a length prior or snap | Discard as a boundary-moving post-pass | Chroma-novelty snap (shift up to 2) raises Summer of '69 0.609 to 0.695 but drops Pour Some Sugar 0.484 to 0.121 (hits@1 4 to 1); shift 1: 0.363; stem-novelty snap: 0.363; regularity-only snap: neutral on Pour Some Sugar, mixed on Summer of '69 |
| 4. Section fusion by the k-1 labelling (Salamon 2021) | Low value here | On Wet Leg 10 of 11 short-segment decisions are the trivial "both neighbours share a cluster" case; 1 is decided by k = 3; on the two scored songs the result equals merge-forward (0.609, 0.484) |
| 5. Snap to downbeats; novelty-grid snapping | Already bar-level; snapping is unsafe (see 3) | Novelty peaks sit within one bar of 9 of 13 (Summer of '69) and 7 of 12 (Pour Some Sugar) reference boundaries, but the peaks nearest the current boundaries are often the pre-chorus, two bars early |
| 6. Pre-chorus rule | Defer | Neither pre-chorus is its own cluster at any k from 3 to 6 (Summer of '69's shares Bm A D G with the chorus; Pour Some Sugar's is 4 bars inside the k = 3 verse cluster) |
| 7. State of the art 0.6 to 0.7 HR at 0.5 s; one-bar tolerance 0.6 to 0.7 is good enough | Agrees with the measured floor | Current F0.58 at one bar: 0.609 and 0.484; with items 1 to 3 below: 0.735 and 0.555 |
| 8. allin1 / LinkSeg / SongFormer backends | Discard for now | allin1 needs NATTEN built from source on Windows and madmom from git, no CPU timing; LinkSeg's ONNX port has unverified features and cost; SongFormer is GPU-bound. Not a fit for a CPU-only Windows CLI with a 150 s budget per song |
| 9. Apps: boundaries more reliable than labels; numbered labels | Applies to naming | Wet Leg prints `verse 3` first and `verse`/`verse 2` by cluster id; chart convention numbers by occurrence |
| 10. Bar-rate smoothing scales (9, 7, 3) may smear boundaries | Discard; measured no gain | Eigenvector filter 3 or time-lag filter 3: Summer of '69 falls from 0.609 to 0.522 (0.465 with no filtering); Pour Some Sugar unchanged at 0.484; Wet Leg fragments from 25 to 35 to 49 segments at min 2 bars; Chelsea's k rises to 5 with 17 segments. The present sizes are the right ones at bar rate |

## 3. Improvements, ordered by impact per effort

### 3.1 Vocal-run boundaries and vocal-aware labels (instrumental, intro, outro; vocal-gated chorus)

Touches:
- `stages/grid.py:42` `GridStage.requires`: add `"separate/stems/vocals.wav"` beside the drums stem; read it as the drums stem is read at `grid.py:64-68`.
- `music/sections.py`: new `bar_stem_db(y, sr, bars) -> list[float]` (the worktree's `music/fill.py:71-78` `bar_energy` already does the per-bar RMS; reuse it and convert to dB), new `vocal_flags(vocal_db) -> list[bool]`, new `insert_vocal_boundaries(boundaries, flags, n, min_bars) -> list[int]`, and a new parameter `vocal: Sequence[bool] | None` on `label_sections` (`sections.py:182-186`).
- `stages/grid.py:84-87` (worktree `grid.py:87-90`): call `insert_vocal_boundaries` after `boundaries_from_clusters(..., min_bars=MIN_SECTION_BARS)` and before `label_sections`.
- `schemas.py:58-72` `Grid`: add `bar_vocal_db: list[float] = []` for inspection and hand editing (optional, schema version stays 1).
- `tests/test_stage_grid.py:26-43` `_ctx`: write a vocals stem (a silent file is enough for the existing tests; a sine burst over chosen bars for the new ones). `tests/test_sections.py:142-181`: new labeller cases.

Evidence: vocal threshold = median per-bar vocal dB (over bars above -60 dB) minus 12 dB, flags median-filtered over 3 bars, runs of at least 4 non-vocal bars. Runs found: Chelsea (0, 20) and (93, 108); Summer of '69 (0, 3), (30, 32), (69, 75), (114, 118), and with the 3-bar median (67, 75); Pour Some Sugar (12, 15) and (67, 77); Wet Leg (0, 2), (16, 18), (48, 50), (108, 113). The runs of 4 bars or more coincide with the known arrangement: Chelsea's intro and instrumental break (lessons document: vocals silent bars 0 to 19 and 93 to 108), Summer of '69's solo (hand list 67 to 74), Pour Some Sugar's solo (hand list 67 to 76, exact). The short runs (2 to 3 bars) are riffs and the rule ignores them.

Prototype result (`structure_experiments3.py`, same segmentation as v1.2, then the vocal post-pass):

| Song | today (v1.2 rule) | with vocal runs | F0.58 at one bar | hits@1 |
|---|---|---|---|---|
| Chelsea | verse 0-9, chorus 9-38, verse, chorus, verse, chorus 93-99, bridge 99-105, chorus 105-142 | intro 0-9, instrumental 9-20, chorus 20-38, verse 38-61, chorus 61-71, verse 71-93, instrumental 93-108, chorus 108-142 | no reference | |
| Summer of '69 | verse 2 0-4, ..., verse 69-83, ..., outro 111-121 | intro 0-4, ..., bridge 58-68 (with 3.2), instrumental 68-75, verse 75-83, ..., outro | 0.609 to 0.735 | 8 to 10 of 13 |
| Pour Some Sugar | intro, verse, chorus, verse, chorus, verse 67-84, chorus | intro, verse, chorus, verse, chorus, instrumental 67-77, verse 77-84, chorus | 0.484 to 0.555 | 4 to 5 of 12 |
| Wet Leg | unchanged | unchanged (no run of 4 bars inside the song) | no reference | |

Design:
1. `vocal_flags`: `db = 20 log10(max(rms, 1e-6))`; `thr = median(db[db > -60]) - 12`; `flags = median_filter(db > thr, size 3)`. Constants `VOCAL_BELOW_MEDIAN_DB = 12`, `VOCAL_RUN_MIN_BARS = MIN_SECTION_BARS`.
2. `insert_vocal_boundaries`: for each non-vocal run of at least 4 bars whose edges lie strictly inside the song, insert the edge as a boundary when both resulting pieces are at least 4 bars; otherwise move the nearest existing boundary onto the edge when the move is at most 3 bars and keeps both neighbours at 4 bars or more. Do not move or insert for the trailing run (the prototype moved Summer of '69's 111 to 114 inside the fade, which the hand list does not support) and do not touch the first boundary.
3. `label_sections` with `vocal`: segment vocal share `v`. A segment with `v < 0.25`, or the first or last segment with `v < 0.5`, is `intro` (first), `outro` (last) or `instrumental` (middle) regardless of cluster. Chorus candidates are recurring clusters whose bar-weighted vocal share is at least 0.5 (on these four songs every recurring cluster passes, 0.70 to 0.98, so the gate changes nothing today; it is the guard for the Riptide-type case in spike round 3 where a quiet intro/breakdown cluster competed). Adjacent `intro`/`instrumental`/`outro` segments merge; an `instrumental` segment adjacent to the intro merges into it, so Chelsea prints `intro 0-20`.
4. `solo` is not attempted: guitar/mix in the two solos is 0.23 (Pour Some Sugar) and 0.44 to 0.63 (Summer of '69) against song medians of about 0.27 and 0.40, too close for a rule. `instrumental` is the chart term (Chordonomicon's eight names include it).

Measurement: the regression harness of 3.4 on the two hand lists (floors 0.609 and 0.484, targets 0.735 and 0.555) plus assertion lists for Chelsea (intro ends at bar 20, no `chorus` before bar 20, bars 93 to 108 instrumental) and Wet Leg (unchanged boundaries). Effort: medium. Impact: high. Confidence: 85%.

### 3.2 Bridge by chord novelty, applied where the chords exist (score stage)

Touches:
- `music/score_builder.py:91-150` `build_score`, or a new `music/relabel.py` called from it before the `ScoreSection` loop at `score_builder.py:114-150`: `refine_labels(grid: Grid, chords: Chords) -> list[str]`. `ScoreSection.label` (`schemas.py:220-227`) takes the refined label; `grid.json` keeps the cluster label, so hand edits to the grid still win if the person sets a label by hand (a `label_locked` or simply "only refine labels in the set {verse, chorus, bridge, verse N}").
- Ordering reason: `HarmonyStage.requires` is `("ingest/audio.wav", "grid/grid.json")` (`stages/harmony.py:23`), so the grid stage cannot see chords. The score stage already reads grid and chords together (`stages/score.py:15-21`) and version 1.2 already moves section starts there (phrase alignment, spec 3.6), so it is the established place for chord-informed section edits.

Evidence: per section, the fraction of chord-bars whose triad occurs in no other section (events expanded to the bars they cover, `N` ignored). Summer of '69 bars 58-69: 0.73 (F, Bb, C). Every other section on all four songs: 0.00 to 0.05 (49 sections). Threshold 0.5 sits in an empty band. A chroma-only proxy inside the grid stage (pitch classes present in at least 40% of the segment's bars and under 10% elsewhere) also finds the bridge (score 0.55) but fires on Summer of '69's fade-out (1.00, noise), Wet Leg's tail (5.00, non-song audio) and Wet Leg bars 58-65 (0.43, the C# passing chord), so the chord-based rule at the score stage is the one to build.

Design: `novelty(section) >= BRIDGE_NOVEL_CHORDS = 0.5`, section is neither first nor last, and (after 3.1) its vocal share is at least 0.5 (needs `bar_vocal_db` in `grid.json`, or skip the vocal condition until 3.1 lands) -> `bridge`. At most one `bridge` per song by this rule; a second candidate keeps its cluster label. Measurement: Summer of '69 bars 58-69 print `bridge`; no other section on the four songs changes. Effort: small. Impact: medium (the one known wrong label on the best-quality song, and the validation document's item 8). Confidence: 90%.

### 3.3 A once-only cluster is not a bridge; verse numbering by occurrence at render

Touches:
- `music/sections.py:235-242`: the once-only branch. Keep `intro` for the first segment and `outro` for the last; label a middle once-only segment `verse` (not `bridge`), leaving `bridge` to 3.2 and `instrumental` to 3.1. Remove `n_bridge` and `bridge 2`.
- `music/sections.py:244`: `f"verse {others.index(c) + 2}"` becomes `"verse"`; the cluster id is no longer encoded in the label.
- `render/html.py:47-66`: compute the display name per section by occurrence (`Verse 1`, `Verse 2`, `Chorus`, `Instrumental 1`); `score.json` and `grid.json` keep the bare label. `render/templates/sheet.html.j2:79` prints it. `music/alphatex.py:69-70` can keep the bare label.
- `stages/strums.py:91-106`: unaffected (inheritance uses indices), but the render's "inherited from verse 3" text (`html.py:49-54`) becomes "inherited from Verse 2".
- `tests/test_sections.py:157-173` (`test_label_sections_order_intro_bridge_outro`) changes expectations.

Evidence: Wet Leg at the v1.2 minimum labels bars 65-100 (35 bars, 31% of the song) `bridge` because the cluster occurs once; its chord set (Dm F C) is the verse set (novelty 0.00). Summer of '69's intro and bridge share a cluster and both print `verse 2`; Wet Leg opens with `verse 3`. The research is unanimous that charts number sections by occurrence (Chordonomicon's eight names; the practitioner VRS1/VRS2 habit) and never by cluster id. Effort: small. Impact: medium. Confidence: 85%.

### 3.4 A one-bar-window regression harness in `evaluate.py`

Touches:
- `evaluate.py:23-29` `Report`: add `section_f`, `section_precision`, `section_recall`, `section_pairwise_f`; `evaluate_run` (`evaluate.py:101-124`): read an optional `sections.txt` from the truth folder (`start<TAB>end<TAB>label`, the same shape as `chords.lab`, parsed by a sibling of `_read_chords` at `evaluate.py:51-68`); score with `mir_eval.segment.detection(ref, est, window=median_bar_seconds + 0.05, beta=0.58, trim=True)` and `mir_eval.segment.pairwise` over the labels; `format_report` (`evaluate.py:131-140`) prints them. `cli.py:62-66` needs no change.
- `tests/fixtures/ground_truth/README.md`: document `sections.txt`. Commit the owner's hand lists as `tests/fixtures/ground_truth/9f06qzcvuhg/sections.txt` and `0uib9y4ofps/sections.txt` (shifted +25.2 s for the video upload; they are the owner's own annotations, so no licence question; do not copy Hooktheory's section data, whose terms forbid redistribution, see `research_notes/gap_analysis/verification_web_pages.md` section 5).
- A `@pytest.mark.slow` test that runs `evaluate_run` on the two run folders when `runs/` is present and asserts the one-bar precision floor per song.

Evidence: the measured floors are Summer of '69 P 0.636, R 0.538, F0.58 0.609 and Pour Some Sugar P 0.571, R 0.333, F0.58 0.484; the targets after 3.1 and 3.2 are 0.735 and 0.555. Nieto 2014 and MSAF: rankings depend on the metric, and precision matters more than recall for listeners, so the metric is fixed before more rules are added. Without this harness the snap in finding 3 would have shipped on its Summer of '69 gain and halved Pour Some Sugar's recall. Effort: small to medium. Impact: medium (enabler for every other item). Confidence: 90%.

### 3.5 A "not music" class for trailing (and leading) non-song audio

Touches: `music/sections.py` `label_sections` (new `stems_present: Sequence[bool]` argument computed in `stages/grid.py` from the drums, bass and guitar stems, which `GridStage.requires` would list); `schemas.py:51-55` `Section` unchanged (label `tail` or `pre-roll`); `music/score_builder.py:114-150` skips or marks those sections; `render/html.py:47-66` prints one line ("4 bars of non-song audio omitted").

Evidence: Wet Leg bars 109-112: drums 0.00 to 0.01, bass 0.00, guitar 0.00 of the mix, `other` 0.82 to 0.83, while the song's bars have drums 0.3 to 0.6 and bass 0.3 to 0.9. Rule: a leading or trailing run where drums, bass and guitar are each under 8% of their own song median (stems whose song median is itself negligible are ignored; the piano stem is 0.00 on all four songs). Fires on Wet Leg 109-112 and Pour Some Sugar bar 0 only. It does not catch Pour Some Sugar's 25.2 s video pre-roll (bars 0 to 8): Demucs puts the pre-roll's audio into the guitar stem at 0.56 to 0.91 of the mix (-28 to -37 dB) and the drum-and-voice intro begins before the album audio does, so there is no stem signature; the only cue there is the mix level (-28 to -37 dB against -22 to -24 dB afterwards), which is the version 1.2 title hint's territory ("Video" in the title). Effort: small. Impact: low to medium (Wet Leg's sheet loses a `No strummed instrument detected` outro of four N.C. bars). Confidence: 70%, because only one of four songs benefits.

### 3.6 Replace the 1.5 dB chorus flag with cue-agreement confidence

Touches: `music/sections.py:24` `LOW_MARGIN_DB`, `sections.py:222-226` (margin and confidence), `stages/grid.py:95-96,110` (log line and `labels_low_confidence`), `schemas.py:69-70`.

Evidence: the flag fired on 4 of 4 songs (1.43, 0.70, 0.93, 0.75 dB; at the four-bar minimum Wet Leg's margin is 0.22 dB) while the chorus was right on 6 of 6 verifiable choruses, so it carries no information; nothing on the sheet reads `confidence` (`sheet.html.j2` prints only `uncertain` for strums), so the impact is on the log and on future tooling. Replacing loudness by the Van Balen score is ruled out by the Chelsea flip in section 2, finding 2.

Design: per-section confidence from provenance rather than from one dB margin: `bridge` by chord novelty = the novelty fraction (0.73); `instrumental`/`intro`/`outro` by vocals = 1 minus the segment's vocal share; `chorus` = 0.5 plus 0.25 if the loudest recurring cluster is also the recurring cluster with the highest vocal share, plus 0.25 if its margin exceeds the pooled within-cluster loudness IQR (Chelsea 1.43 dB against 0.5 to 0.9, Summer of '69 0.70 against 1.0 to 1.6); `verse` = 0.5. Keep `chorus_margin_db` in `grid.json`; drop `labels_low_confidence` or define it as "chorus confidence under 0.75". Measurement: none possible beyond "6 of 6 right"; the value is honesty in the log and the README line "Section labels are low confidence" (README.md:50) can then say what is and is not confident. Effort: small. Impact: low. Confidence: 60%, because with every verifiable chorus already right there is nothing to calibrate against.

### 3.7 Keep every k level in `grid.json` for hand editing

Touches: `music/sections.py:125-142` `segment_bars` (return the labelling for every k from 3 to the chosen k, which the loop at `sections.py:137-142` already computes and discards); `schemas.py:58-72` `Grid`: `section_levels: list[list[Section]] = []` (or `levels: dict[int, list[int]]` of cluster ids per bar); `stages/grid.py:84-87`; `options.py:15` and `cli.py:45`: `--sections-k` already exists and stays as the way to pick a level.

Evidence: Summer of '69 at k 3: F 0.428; k 4 (chosen): 0.609; k 5 and 6: 0.571. Pour Some Sugar at k 3 (chosen): 0.484 with hits@1 4/12; k 5: 0.476 with hits@1 5/12. Wet Leg at k 4: lengths 5 17 12 12 12 7 36 7 5 (a 12-bar periodic middle) against the chosen k 5: 5 13 15 9 16 7 35 8 5. No level is best on every song, which is Salamon 2021's and MSAF's point; the design spec already says sections "live in an editable file" because shared progressions cannot be separated from audio. Storing the levels makes a hand fix a one-number edit (`--sections-k 4`) that the person can judge from the printed level lengths in the log, rather than retyping boundaries. Effort: medium. Impact: medium for hand editing, none automatic. Confidence: 65%, because the gain depends on a person using it.

### 3.8 Multi-cue boundary candidates with a duration prior (deeper option, measured recall only)

Touches: a new `music/boundaries.py` with a bar-level Foote novelty on the chroma+MFCC self-similarity (the matrix `_embedding` already builds at `sections.py:93-99`), a stem-level novelty (vocals, drums, bass, guitar dB over 4-bar windows), and a dynamic programme over bars choosing boundaries from the union of peaks with a modulo-4 length penalty (Marmoret 2023: 0 at 8, 1/4 for multiples of 4, 1/2 even, 1 odd) and the existing cluster boundaries as strong candidates; `stages/grid.py:84-87` would call it between `segment_bars` and `label_sections`.

Evidence for the ceiling: within one bar of a reference boundary there is a chroma-novelty peak for 9 of 13 (Summer of '69) and 7 of 12 (Pour Some Sugar) boundaries, a stem-novelty peak for 5 of 13 and 6 of 12, and the union covers 9 of 12 on Pour Some Sugar (bars 15, 20, 24, 28, 39, 52, 67, 76, 80) against 4 of 12 today. Evidence against a naive version: both snap variants in section 2, finding 3 lowered Pour Some Sugar's precision, because the peaks nearest the current boundaries are the pre-chorus centres. This item is only worth building behind the 3.4 harness, scored on precision at one bar first. Effort: large. Impact: medium to high (it is the only route to the shared-progression boundaries other than hand editing). Confidence: 55%, because candidate recall is not boundary precision and two songs are too few to tune a prior.

### 3.9 Pre-chorus rule (deferred)

Touches: `music/sections.py` `label_sections`, after the chorus is fixed. Rule as in the research: a recurring non-chorus cluster followed by the chorus in at least two of three occurrences, shorter than the chorus, with vocals, is `pre-chorus`.

Evidence against doing it now: Summer of '69's pre-chorus (hand list bars 18-26 and 39-48) shares Bm A D G with the chorus and is in the chorus cluster at every k from 3 to 6; Pour Some Sugar's 4-bar pre-chorus (24-28, 48-52) is inside the k 3 verse cluster and is not split at k 4 to 6 either (the extra segments at k 5 fall at bars 39-44 and 44-49). The rule has no case to fire on and nothing to be measured against until 3.8 or a hand edit produces a pre-chorus segment. Effort: small. Impact: low today. Confidence: 40%.

### 3.10 Section fusion by lower-level vote (deferred)

Touches: `music/sections.py:145-179` `boundaries_from_clusters` (worktree `grid.py:36,89` set `min_bars=4`), using the levels from 3.7.

Evidence: on Wet Leg at k 5 the 11 short segments resolve as 10 "both neighbours share a cluster" merges and 1 vote at k 3; the Salamon rule and merge-forward give the same boundaries on both scored songs (0.609, 0.484) and differ on Wet Leg only in where the 5-33 region is cut (forward: 5-18 and 18-33; fusion: 5-33), with no reference to say which is right. The cosine-nearest-neighbour variant was needed once (Chelsea with small filters) and never with the shipped filters. Effort: small to medium once 3.7 exists. Impact: low. Confidence: 40%.

## 4. Discarded, with reasons

- **Chorusness score replacing loudness (finding 2).** Measured flip on Chelsea Dagger (section 2). Van Balen's coefficients come from Billboard sections scored by listeners; on this pipeline the verse cluster has the higher MFCC variance and the lower loudness IQR. Keep loudness; add the vocal gate (3.1) and provenance confidence (3.6).
- **Smaller smoothing filters at bar rate (finding 10).** Measured losses on Summer of '69 (0.609 to 0.522, 0.465 with none) and fragmentation on Wet Leg (25 to 49 segments at min 2). The librosa example's beat-rate sizes happen to be right at bar rate too; leave `sections.py:99,109` alone.
- **Stem levels as embedding features (finding 1, Salamon's pattern).** In the path graph: no change on any song. In the recurrence graph: Summer of '69 0.588 (k jumps to 6), Pour Some Sugar 0.363. The recurrence graph should stay harmonic; arrangement belongs in the post-pass (3.1).
- **Novelty or regularity snapping of existing boundaries (findings 3 and 5).** Pour Some Sugar 0.484 to 0.121 (chroma, shift 2), 0.363 (shift 1 or stem novelty). The boundaries that are right today sit one bar after a novelty peak because of the pre-chorus. Any snap needs the harness (3.4) and the multi-cue design (3.8), not a post-hoc move.
- **allin1, LinkSeg, SongFormer, barwise CBM.** allin1 requires NATTEN built from source on Windows and madmom from git, runs its own Demucs, publishes no CPU timing (the project's whole run is 117 to 169 s per song, 76 to 84% of it Demucs); LinkSeg's ONNX port is CC-BY 4.0 but its front end and CPU cost are unverified; SongFormer is GPU-bound with MuQ/MusicFM front ends; barwise CBM's licence and packaging are unverified. A one-day spike of allin1 in a separate venv on the four songs is the only reasonable next step, and only after 3.4 gives it something to be scored against.
- **Deep embeddings (OpenL3, VGGish).** Both bring TensorFlow (OpenL3) or a second PyTorch model and a model download into a 44-package CPU install for a gain the stems already deliver on the measured songs.
- **A "solo" label.** Guitar/mix in the two solos is not separable from the song medians (3.1).
- **Hooktheory labels in the harness.** Terms forbid redistribution; the owner hand lists carry labels (intro, verse, prechorus, chorus, riff, bridge, solo, breakdown, outro) and are enough for `pairwise` scoring.

## 5. Already in progress in version 1.2 (not proposed again)

Four-bar minimum section (`worktree grid.py:36,89`); mean-interval tempo (`worktree grid.py:83`); title cleaning and the "Video" hint (the only answer to Pour Some Sugar's pre-roll, see 3.5); filling no-chord bars from the harmonic stems (`worktree music/fill.py`, whose `bar_energy` 3.1 reuses); passing chords; phrase alignment at the score stage (the precedent for 3.2's placement); repeated row blocks.

## 6. Suggested order of work

1. 3.4 harness (so 2 to 4 are measured, not argued).
2. 3.1 vocal runs and vocal-aware labels (biggest measured gain: 0.609 to 0.735 and 0.484 to 0.555, Chelsea's intro and break named correctly).
3. 3.3 and 3.2 together (labels become chart-conventional; Summer of '69's bridge named).
4. 3.6 and 3.5 as small follow-ups.
5. 3.7, then 3.10 and 3.8 only if hand editing of levels is still too slow after the above.

## 7. Appendix: raw numbers

Prototype vocal threshold per song (median vocal dB minus 12): Chelsea -37.8, Summer of '69 -29.7, Pour Some Sugar -40.5, Wet Leg -31.8.

Stored-section vocal shares (Chelsea): verse 0-9 0.00, chorus 9-38 0.62, verse 38-61 1.00, chorus 61-71 1.00, verse 71-93 1.00, chorus 93-99 0.00, bridge 99-105 0.00, chorus 105-142 0.89.

Per-cluster features at the four-bar minimum (loudness dB, IQR, centroid Hz, MFCC variance, vocal share): Chelsea c0 (verse) -21.4, 0.5, 3287, 327, 0.83; c1 (chorus) -20.0, 0.9, 3309, 199, 0.74. Summer of '69 c1 (chorus) -12.0, 1.0, 3300, 16, 0.97; c2 (verse) -12.7, 1.6, 3403, 79, 0.87; c3 (intro+bridge) -13.5, 4.0, 3057, 484, 0.67. Pour Some Sugar c0 (chorus) -21.8, 1.0, 3362, 102, 0.98; c1 (verse) -22.7, 1.1, 3206, 36, 0.70. Wet Leg c1 (chorus) -8.6, 0.5, 2781, 80, 0.80; c0 -8.8, 0.3, 3108, 116, 0.84.

Embedding variants, F0.58 at one bar (Summer of '69 / Pour Some Sugar), min 4 bars: base (9, 7, 3) 0.609 / 0.484; evec 3: 0.609 / 0.484; lag 3: 0.522 / 0.484; evec 3 lag 3: 0.522 / 0.484; evec 5 lag 3: 0.522 / 0.484; no filters: 0.465 / 0.484. Wet Leg segment counts at min 2 bars: 25, 35, 33, 47, 42, 49.

Levels (min 4 bars): Summer of '69 k 3 0.428, k 4 0.609, k 5 0.571, k 6 0.571; Pour Some Sugar k 3 0.484, k 4 0.410, k 5 0.476, k 6 0.476.

Snap variants on Pour Some Sugar (before 0.484, hits@1 4/12): chroma shift 2 0.121 (1/12); chroma shift 1 0.363 (3/12); chroma shift 2 margin 1.0 0.121; stem novelty shift 2 0.363; shift 1 0.363; regularity only 0.484 (4/12). On Summer of '69 (before 0.609, 8/13): chroma shift 2 0.695 (9/13); shift 1 0.609; stem novelty 0.609 (7/13); regularity only shift 2 0.695 (8/13).

Chord novelty per section (fraction of chord-bars with a triad found nowhere else): Summer of '69 58-69 0.73; the maximum elsewhere is 0.05 (Pour Some Sugar 55-67, one C#:min event; Chelsea 71-93, one B:maj event).

Scripts and caches: `structure_experiments.py` (stems, variants, fusion, snap, chorusness), `structure_experiments2.py` (per-bar stems, safer snaps, chord novelty), `structure_experiments3.py` (levels, stem-augmented embedding, prototype labeller), `structure_experiments4.py` (chroma-only novelty proxy), `feat_<song>.npz` (bar features, loudness, per-bar stem RMS, centroid), `structure_experiments.json`.
