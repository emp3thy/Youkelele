# Ukulele tab chain, version 1.5: fewer, truer sections and an honest sheet

Date: 2026-10-04. Package version 0.6.0. Builds on version 1.4 (`2026-10-04-ukulele-tab-chain-v1-4-design.md`, PR #6) and on the five research strands under `docs/superpowers/research/2026-10-04-v1-5/`: `sections-by-chords.md`, `strum-confidence.md`, `page-layout.md`, `key-hedge-and-power-note.md`, and `register-split.md` (a spike run during the design, see section 9).

## 1. Goal and scope

Version 1.4 gave the right key and the right names on the five known songs and ran two blind songs through the chain. Its validation left four things a reader notices: a one-chord-cycle song (All Fired Up) prints eight verses and three choruses over four pages; the two-bar worked-example strip costs a page on three songs; the default sheet hides a power chord; and a close tonic call (Need You Tonight) is hedged by coincidence. This version fixes those four and adds one thing the listening pass for this design found: two of the seven songs' guitar parts are riffs, not strummed chords, and the sheet should say so.

In:

- Merging section fragments by chord content, shared by the strums and score stages (section 3).
- A chance test on strum certainty; the sixteenth-grid floor re-centred; the one-versus-two-guitar question closed as a stated limitation unless the register spike changes it; a riff marker (section 4).
- A one-bar strip beside the rows, two bars above only when a chord changes inside a bar (section 5).
- The tonic chosen by two of three rules, with the loser hedged; the power-chord line on the easy sheet (section 6).
- Data formats, `evaluate`, compatibility (section 7); validation on seven songs plus one new blind song (section 8).

Out, with the reason:

- Renaming verses and choruses by chord content: where chords differ, the chord groups are the existing sound clusters (no change on four songs); where they do not, chords cannot say which part is the chorus. Measured in `sections-by-chords.md` 3.2 and 3.4.
- Merging whole sections of eight bars or more because their chords match: two verses in a row on the same chords are a real form.
- Correcting late refrain boundaries (both blind songs start their refrain a bar to a phrase before the detected boundary): unresearched; a candidate for 1.6 after a spike.
- Separating two guitars in one stem on a sixteenth grid by onset statistics: a null result after 17 more features (`strum-confidence.md` section 7). The register split (section 9, A20) is the one open route.
- The mode hedge, fill refinement, phrase shifts, and the 1.3 carry-over on sustained strums on sixteenth grids: unchanged from 1.4's limitations.

House rules unchanged: schema version 1 and every 1.3 and 1.4 file loads; UK spelling; no em-dashes; no song lyrics anywhere in code, tests or documents; no time or effort estimates in documents.

## 2. What listening established on 2026-10-04

The owner listened to twelve clips cut from the run folders (guitar stem with clicks on the printed pattern, mix excerpts followed by a synthesised triad, and mix excerpts with a beep at a detected boundary). These are the ear facts this design rests on:

| Song | Fact | Bearing |
|---|---|---|
| Need You Tonight | Home chord is F major ("C sounds too low"). | The 1.4 score rule's C (margin 0.327) was wrong; the pair rule's chroma tie-break (F) and the mix estimate (F) were right. Section 6. |
| Need You Tonight | The first eight bars are drums and voice before the chords start. | The N.C. intro is right; nothing to fill. |
| Need You Tonight | The guitar stem is a single-note riff; the printed pattern's clicks are "perfect" on it. | The pattern is the riff's rhythm, not a strum. Section 4.4. |
| Need You Tonight | The chorus starts before bar 24 (the beep at 53 s fell mid-chorus); it ends exactly at bar 31. | The start boundary is late. Out of scope; recorded. |
| All Fired Up | G major fits the sung pitch. | Key confirmed. |
| All Fired Up | Verse `DUDUDUDU` (bars 33 to 49) is "exactly" right. | Ear-accepted strum. |
| All Fired Up | Section 9 (bars 110 to 124) is a strummed start, a pause, then loud sustained power chords. | No single pattern fits; "uncertain" is the right call. |
| All Fired Up | The first refrain boundary (bar 49) falls mid-phrase, late; the refrain end (bar 55) is a bar late. The song is a recurring melody punctuated by a short refrain over one chord cycle. | Its "chorus" sections are the refrain punctuations. Section 3. |
| Fame | The guitar stem holds two guitars: the signature riff and a second repeating one higher note for emphasis; no chord strumming. | Fame belongs with Need You Tonight on the riff side. Section 4.4. |
| Fame, Pour Some Sugar On Me | Where two parts share a stem, the second part plays consistently higher notes than the first. | The register-split spike (A20). |

Carried from 1.3 and 1.4: ear-accepted strums on Summer of '69 bars 41 to 53 and 83 to 95 and Chelsea Dagger 9 to 38 and 105 to 142; ear-rejected two-guitar sections on Pour Some Sugar On Me 28 to 39, 55 to 67 and 84 to 103.

## 3. Sections: the plan

### 3.1 Rules

The grid stage keeps producing sections and labels as today (`music/sections.py`, `label_sections`). A **section plan** is computed from `grid.json`, `chords.json` and the existing bridge rule (`music/relabel.py`, `refine_labels`), and is the single list of sections the strums stage and the score builder use, as `trailing_silent_bars` already is. Two merge rules, applied until nothing changes:

1. **Sandwich.** A `verse` shorter than `FRAGMENT_BARS` between two `chorus` sections, whose chord-bars all hold triads both neighbours play (pair novelty 0 against each), joins them into one `chorus`. `verse` is the labeller's fall-through (`sections.py:416`) and `chorus` a positive choice (`sections.py:383`), so the fragment's own label carries no evidence against the merge.
2. **Fragment.** A `verse` or `chorus` shorter than `FRAGMENT_BARS` joins a same-label neighbour that is at least as long and plays every triad the fragment plays (pair novelty 0). With two eligible neighbours it joins the one with the lower containment edit distance over bar-triad strings (`sections-by-chords.md` 3.1, "M2").

`intro`, `instrumental`, `outro` and `bridge` never merge. Whole sections of `FRAGMENT_BARS` or more never merge on chord match alone. No label is renamed by chord content. `display_names` numbers the planned sections by occurrence as today.

Pair novelty is `section_novelty`'s notion (`relabel.py:31-47`) applied to a pair: the share of the fragment's chord-bars holding a triad its neighbour never plays. A fragment that brings a new chord stays a candidate for the bridge rule and never merges.

### 3.2 Constants and bands

| Constant | Value | Band on the seven songs | Evidence |
|---|---|---|---|
| `FRAGMENT_BARS` | 8 | above 7, at most 16 | the largest fragments that must merge are 7 bars (All Fired Up 90 to 97, 97 to 104); the shortest same-label neighbours that must stay whole are 16 (Wet Leg 42 to 58, All Fired Up 33 to 49); at 6 All Fired Up keeps 10 sections, at 8 or 10 it has 6; one phrase in the structure literature is 32 beats |
| pair novelty for a merge | 0 (strict) | every merged fragment measured 0.00; no fragment with a same-label neighbour measured above 0 | `sections-by-chords.md` 3.8 |
| neighbour choice (M2) | lower wins | 0.29 against 0.43 on the one two-neighbour case (Wet Leg) | same, 3.1 |

### 3.3 Where it runs

- `music/relabel.py`: `section_plan(grid: Grid, chords: Chords) -> list[PlannedSection]` beside `refine_labels`, where `PlannedSection` carries `start_bar`, `end_bar` (exclusive), `label`, `members` (the grid section indices it absorbed, in order). `refine_labels` runs first, then the two rules to a fixed point.
- `stages/strums.py`: loops over the plan instead of `grid.sections`; the plan is written to `strums.json` (section 7). A merged section's pattern, confidence, chance test and riff features are computed over the bars of its **longest member** (the earlier one on a tie), not over all its bars: the fragment is absorbed for naming, not for strumming. Measured reason (A4): a vote over all of All Fired Up's merged Verse 1 blends the five-bar `DUxxxUxU` fragment into the sixteen-bar `DUDUDUDU` the ear confirmed, giving `DUDxDUxU` with p 0.262, uncertain; the longest member keeps `DUDUDUDU` certain. The stage already requires `harmony/chords.json`, so staleness is already tracked.
- `music/score_builder.py`: builds sections from the plan read back from `strums.json` (never recomputed, so the two stages cannot disagree); phrase alignment takes the plan's spans; `check_strums_match_grid` compares the pattern count with the plan's length. `grid.json` is unchanged.
- `evaluate.py`: prints each planned section with its member grid sections and the grid label of each, in the form `Verse 2 (grid 4, 5, 6, 7, 8: verse, verse, verse, verse, verse)`.
- The manifest's strums record notes the merges (`merged 7 grid sections into 2`), and the one-loop fact when the largest chord group holds at least `ONE_LOOP_SHARE = 0.85` of the sung bars (`verse and chorus share their chords, share 0.96`; band 0.77 to 0.93 on the seven songs). Nothing about this prints on the sheet.

### 3.4 Expected effect

| Song | Sections before | After | Printed after |
|---|---:|---:|---|
| Summer of '69 | 12 | 12 | unchanged |
| Chelsea Dagger | 7 | 7 | unchanged |
| Pour Some Sugar On Me | 8 | 8 | unchanged |
| Wet Leg "mangetout" | 9 | 8 | Verse 4 (58 to 100) absorbs the old Verse 5 |
| Fame | 9 | 9 | unchanged |
| All Fired Up | 13 | 6 | Intro 0 to 28, Verse 1 28 to 49, Chorus 1 49 to 55, Verse 2 55 to 110, Chorus 2 110 to 132, Outro 132 to 156 |
| Need You Tonight | 7 | 7 | unchanged |

## 4. Strums: certainty, limitation, riff

### 4.1 The chance test

The printed patterns do not change: `majority_vector`, `fill_to_floor` and `jaccard` are untouched. Today's tests stay (confidence floor, `explained` at least 0.6, four bars or more). One test is added, in `music/as_played.py` and `stages/strums.py`:

```
full       = every slot of the topped-up vote is struck
structured = strike_density >= FULL_VOTE_DENSITY   if full
             else chance_p <= CHANCE_ALPHA
uncertain  = confidence < floor(grid) or explained < EXPLAINED_BELOW
             or too short or not structured
```

- `chance_p(bars, seed)`: `(b + 1) / (m + 1)`, where `b` is the number of the `m = CHANCE_SHUFFLES` slot-shuffled copies of the section whose confidence is at least the section's own (Phipson and Smyth's correction, never zero). Each bar's cells are permuted, so its strikes and mutes are kept; the vote, the density floor and the confidence are recomputed per copy exactly as `section_summary` does. The generator is seeded from the section's start bar, so a re-run writes identical files.
- `strike_density`: the share of the section's cells that are not rests, mutes counted as strikes.
- The exemption exists because a vote that strikes every slot gives a shuffled baseline equal to the bar density, so the correction is zero by construction (the kappa prevalence paradox, `strum-confidence.md` section 5); "every slot" is a claim about density, not structure, and is tested as one.

| Constant | Value | Band | Evidence |
|---|---|---|---|
| `CHANCE_ALPHA` | 0.05 | (0.021, 0.064) | kept certain sections have p up to 0.021 (Summer of '69 75 to 83); the lowest p among flipped sections is 0.064 (All Fired Up 55 to 61); 0.05 is the calibrated 5 percent on random sprays |
| `CHANCE_SHUFFLES` | 1000 | Monte Carlo error near 0.05 about 0.007 | with 200 it is 0.015 and could move All Fired Up 55 to 61 across the line between seeds |
| `FULL_VOTE_DENSITY` | 0.6 | (0.547 spray median, 0.625 lowest real) | the weakest threshold in this version: All Fired Up 28 to 33 (0.625) and 33 to 49 (0.672) sit inside the spray tail (p95 0.625 at 8 bars) |
| `UNCERTAIN_BELOW_SIXTEENTH` | 0.55 to **0.53** | (0.504, 0.552) | centred between Pour Some Sugar On Me's instrumental 67 to 77 (0.504) and Fame 47 to 61 (0.552); flips nothing; the 1.3 reason for 0.55 (rejecting sprays) is now the chance test's job |

Expected effect on the seven songs: three certain-to-uncertain flips, all sections of four to six bars, nothing else. Summer of '69 53 to 58 (`DU-UDUDU`, p 0.332, defensible); All Fired Up 55 to 61 (`D-Dx-U-U`, p 0.064, right: no bar matches the pattern); All Fired Up 128 to 132 (`D---DUD-`, p 0.208, probably wrong at four bars, low stakes). Every ear-accepted section and every sixteenth-grid certain section stays certain. Random half-density sprays printing certain fall from 92 to 8 percent at 8 slots and from 30 to 5 percent at 16 slots.

### 4.2 Stated limitation

Unless the register split (A20) separates the parts, the README's limitation reads: "When one separated guitar stem holds two players, one strumming and one playing a riff over the chords, nothing measured tells them apart on a sixteenth-note grid: the section's confidence is held under the floor and the box prints as uncertain. Seventeen onset and pitch features were tried; none separates the ear-rejected sections from the ear-accepted ones."

### 4.3 The riff marker

A section is marked `riff` when its guitar-stem onsets play single notes rather than chords. Two features are computed in the strums stage on the stage's own onsets, in a 40 to 130 ms window after each onset over a constant-Q spectrum from C2 over six octaves:

- `riff_entropy`: the normalised entropy of the section's mean onset chroma (low means one or two pitch classes at a time).
- `riff_single_share`: the share of onsets whose chroma has only one pitch class at half the maximum or more.

```
riff = riff_entropy <= RIFF_ENTROPY_MAX and riff_single_share >= RIFF_SINGLE_PC_MIN
```

| Constant | Value | Riff side (Fame, Need You Tonight) | Strum side (ear-accepted) | Two-guitar side (Pour Some Sugar On Me) |
|---|---|---|---|---|
| `RIFF_ENTROPY_MAX` | 0.80 | 0.540 to 0.788 | 0.872 to 0.922 | 0.780 to 0.927 |
| `RIFF_SINGLE_PC_MIN` | 0.45 | 0.466 to 0.783 | 0.264 to 0.478 | 0.153 to 0.426 |

Neither feature separates alone: Pour Some Sugar On Me's entropy overlaps Fame's, and Summer of '69's 83 to 95 single share (0.478) exceeds Fame's lowest (0.466). Together they classify every section of the seven songs as the ear did, with the Pour Some Sugar On Me margin on the second feature only 0.04 (0.426 against 0.466). This is the weakest threshold after `FULL_VOTE_DENSITY`, and A17 records the spike that re-measures it on every section with the stage's own code before the plan is written.

On the sheet, a riff section prints its pattern and strip as today, with the strum label replaced by "riff: strum the chord to this rhythm". `evaluate` prints both features per section. The marker is independent of certainty: an uncertain riff section prints the uncertain box as today with the riff wording.

## 5. The page

### 5.1 The strip rule

The strip draws one bar unless one of the first two bars changes chord inside the bar; then it draws both, as today.

```python
def strip_bars(section: ScoreSection) -> list[ScoreBar]:
    bars = example_bars(section)
    return bars if any(len(b.chords) > 1 for b in bars) else bars[:1]
```

`example_bars` and its tests are unchanged. The bar-to-bar change the second bar used to show is already in the grid beneath.

### 5.2 Placement

A one-bar strip sits beside the section's rows: the section body becomes a two-column grid, rows on the left, the strip on the right, 4 mm apart, aligned to the top. A two-bar strip stays above the rows. No font size, cell padding, section gap or `slot_px` changes.

```css
.section-body.beside { display: grid; grid-template-columns: minmax(0, 1fr) auto; column-gap: 4mm; align-items: start; }
.section-body.beside > .strum-box { grid-column: 2; grid-row: 1; margin: 0; }
.section-body.beside .grid.has-pickup .row { grid-template-columns: minmax(13mm, 0.25fr) repeat(4, minmax(0, 1fr)) auto; }
```

`html.py` calls `strip_bars` in place of `example_bars` and adds `beside = show_box and len(bars) == 1` to the section context. `.section-head` keeps `break-after: avoid`.

### 5.3 Measured effect and costs

| Song | Pages today | Pages after | Last page used |
|---|---|---|---|
| Summer of '69 | 3 | 2 | 0.96 |
| Chelsea Dagger | 3 | 3 | 0.33 |
| Pour Some Sugar On Me | 2 | 2 | 0.79 |
| Wet Leg "mangetout" | 3 | 2 | 0.69 |
| Fame | 3 | 2 | 0.95 |
| All Fired Up | 4 | 3 (before the section merge) | 0.29 |
| Need You Tonight | 2 | 2 | 0.61 |

Twenty pages become sixteen; no cell wraps on any sheet. Costs: in a section with its strip beside it the cells narrow from 41 mm to 25 mm (eighth grid) or 19 mm (sixteenth grid), so column widths differ between sections on a page; a long two-chord cell such as "C#m7 / G#m" would wrap in those sections and add about 5 mm; the repeat mark sits between the cells and the strip. Fame and Summer of '69 end at 95 percent of their last page. The tighter metrics (section gap 3.5 mm, cell padding 1.5 mm) are held back as an option: same counts, 30 mm spare.

## 6. Key and the power-chord note

### 6.1 Three votes

The harmony stage already computes three tonic opinions: the chord-time score (`decide_tonic`), the diatonic pair rule over every candidate with its chroma tie-break (`pair_rule`, `TonicDecision.pair_tonic`), and the mix estimate (`Key.mix`). Today the score leads whenever its margin is at least `KEY_TIE_MARGIN`, and the pair rule decides only a close score. The new rule:

1. Score margin under `KEY_TIE_MARGIN` (0.05): the pair rule decides among the close candidates, as today.
2. Otherwise, if the score's and the pair rule's tonics agree: that tonic.
3. Otherwise the mix estimate decides between the two; if it names neither, the score's tonic leads.

The mode, the mode tie-break and `hedge_mode` are unchanged and computed at whichever tonic leads. `Key` gains `pair_tonic` and `tonic_votes` (`score`, `pair`, `mix`, and `decided_by`: `"agreement"`, `"pair rule"`, `"mix"` or `"score"`), all defaulted.

### 6.2 Hedge

`_hedge` has three rungs, in order:

1. A close score margin names the runner-up (unchanged).
2. A chord rule that lost under 6.1 names its tonic: `pair_tonic` when the score led, the score's tonic when the pair rule led.
3. The mix estimate differing from the printed tonic names the mix tonic (unchanged).

No new constants. `hedge_text` prints the alternative with its own stored mode; a file without `pair_tonic` never reaches rung 2.

Expected headers: Summer of '69 "D major", Chelsea Dagger "G major (or D major)" (the pair rule agrees with G; the mix hedges), Pour Some Sugar On Me "C# minor", Wet Leg "C major" (a pair tie whose chroma winner is C, agreement), Fame "F major", All Fired Up "G major", Need You Tonight **"F major (or C major)"** (score C, pair F, mix F: two of three; the score hedges). On the five known songs the chord rules never disagree, so nothing changes.

### 6.3 The power-chord line on the easy sheet

The easy tier prints one legend line per power-chord name, under the passing and no-capo lines, gated as the full tier's line is (any use of the name is a power chord): `POWER_LEGEND_EASY = "{name} is a power chord (root and fifth) on the record; this sheet prints the triad."` The raised-5 badge stays full-tier only. Measured on Pour Some Sugar On Me, the only song with a power chord: one line costs 18 pt of 64 pt slack on page 1; page 2 unchanged; no other song can change. The README's limitation bullet and spec 1.4 section 4's sentence about the easy tier are updated.

## 7. Data formats, compatibility, tooling

Schema version stays 1. Every new field is defaulted, so 1.3 and 1.4 files load and render.

| Artefact | New fields | Default behaviour on an old file |
|---|---|---|
| `Key` (`chords.json`) | `pair_tonic: str \| None`, `tonic_votes: TonicVotes \| None` | hedge rung 2 is skipped; the header prints as 1.4 did |
| `SectionPattern` (`strums.json`) | `chance_p: float \| None`, `strike_density: float \| None`, `riff: bool = False`, `riff_entropy: float \| None`, `riff_single_share: float \| None` | no chance test recorded; no riff marker |
| `Strums` | `plan: list[PlannedSection] = []` | an empty plan is read as one planned section per grid section, so a 1.4 `strums.json` still builds a score |
| `ScoreSection` (`score.json`) | `riff: bool = False`, `members: list[int] = []` | strum wording; `evaluate` prints no members |

Stage boundaries: the plan and the riff features are computed in the strums stage (it has the chords and the guitar stem); the votes in harmony; the strip rule and the beside layout in the renderer, from the score alone (not stored). Staleness: a 1.4 run re-runs from strums for the plan and the riff marker, from harmony for the new tonic rule; no re-separation.

`evaluate` prints per planned section: its members and their grid labels, pattern, confidence, `explained`, `chance_p`, `strike_density`, riff features and the riff flag; and for the key, the three votes and `decided_by`. The compare harness (`compare_runs`) carries the new columns so the 1.4 to 1.5 differences are visible run to run. Package version 0.6.0; `pyproject.toml`, `__init__`, `uv.lock` and the eight manifests after validation.

## 8. Validation

Written before the runs, checked after. The seven 1.4 folders are the baseline; `02_grid` to `07_render` and the manifest are copied aside with each folder's `evaluate` output before any re-run. Re-runs: Need You Tonight from harmony (new tonic rule), the other six from strums; the blind song from ingest.

| Expectation | Songs | Yes or no criterion |
|---|---|---|
| Section counts 12, 7, 8, 8, 9, 6, 7 | all seven, in the order of section 3.4 | exact |
| All Fired Up's merged Verse 1 prints 29 to 49 (phrase alignment, A5) with the `DUDUDUDU` pattern of its longest member, certain | one | exact |
| Pages 2, 3, 2, 2, 2, at most 3, 2 | all seven | exact, All Fired Up at most 3 |
| Certainty flips: exactly Summer of '69 53 to 58, All Fired Up 55 to 61 and 128 to 132 | all seven | no other section changes certainty |
| Riff marker on Fame's and Need You Tonight's sections that have their own pattern, and nowhere else | all seven | exact |
| Headers unchanged except Need You Tonight "F major (or C major)" | all seven | exact |
| Power line on Pour Some Sugar On Me's easy sheet; no other sheet has one | all seven | exact |
| Chords, beats, bars and onsets identical to 1.4 | the six re-run from strums | bar-by-bar compare |
| Blind song `https://www.youtube.com/watch?v=3dOx510kyOs` runs to a sheet with exit 0 | one | the key, sections, riff flags, certainty, pages and the power gates recorded, not judged in advance |

Then a light listening pass: the merged All Fired Up sections' patterns, every section whose certainty flipped, the blind song's key and one strummed section. Anything that misses is recorded in `2026-10-04-v1-5-validation.md`, not tuned away.

## 9. Assumptions

Status after the automatic validation pass run on this machine after the initial spec (probes under `%TEMP%\youkelele-v15-research\`); the research documents hold the measurements.

| # | Assumption | Status | Evidence | Cost if wrong |
|---|---|---|---|---|
| A1 | The grid's clusters are the chord groups wherever chords differ, so renaming by chords changes nothing on those songs | **Verified** | recomputed clusters reproduce `grid.json` on 7 of 7; chord groups equal clusters on the four chord-distinct songs (`sections-by-chords.md` 3.2) | a song where a chord group crosses clusters would want renaming this version does not do |
| A2 | A same-label section under 8 bars that adds no chord is a fragment of its neighbour | **Measured**, unverified by ear | 7 merges on two songs, none on the five referenced; `FRAGMENT_BARS` band above 7 to 16 | a real short part loses its heading; the listening pass checks All Fired Up's merged sections |
| A3 | A verse fragment between two choruses on their chords is chorus | **Measured once** | All Fired Up 124 to 128, the loudest sung passage of the song; the labeller's fall-through argument in code | a short verse prints inside a chorus |
| A4 | A merged section's strip should come from its longest member, not a vote over all its bars | **Measured, design amended** (probe `validate/probes.py` on the stored `bar_onsets`) | all-bar votes on All Fired Up: Verse 1 28 to 49 `DUDxDUxU` conf 0.548 p 0.262 (uncertain; members 0.56 and 0.55 certain, `DUDUDUDU` ear-confirmed); Verse 2 55 to 110 `DxDxDUDU` conf 0.477 p 0.003 (a blend of five members' patterns); Chorus 2 110 to 132 conf 0.162 (uncertain, rightly); hence the longest-member rule in 3.3 | the strip describes the longest member and says nothing about a distinct shorter stretch (All Fired Up 90 to 110) |
| A5 | Phrase alignment behaves on the plan's spans as on grid spans | **Measured: one shift** (same probe) | All Fired Up's merged Verse 1 shifts to start at bar 29 (its intro ends at 29); on the grid spans no section shifted; Wet Leg's shifts are identical on both | the validation expects All Fired Up's Verse 1 at 29 to 49; any other moved boundary is a miss |
| A6 | The shuffle p-value is a calibrated noise test | **Measured** | about 5 percent of random sprays pass at any density, grid or length; the bare correction cannot replace the confidence (kappa paradox) | none for calibration; a metre-aware null would flip more short sections |
| A7 | `CHANCE_ALPHA` 0.05 sits in an empty band | **Measured** on 64 sections | (0.021, 0.064) | a song with many short, noisy but real sections loses strips |
| A8 | `FULL_VOTE_DENSITY` 0.6 separates real full votes from dense sprays | **Measured, narrow** | lowest real 0.625; spray median 0.547, p95 0.625 at 8 bars | dense sprays print certain about 8 percent instead of 5; a real full-vote section at 0.6 goes uncertain |
| A9 | Seeded shuffles make runs reproducible | Verified in design (seed from the start bar) | the validation's byte compare will show it | a re-run differs by a flipped short section |
| A10 | The sixteenth floor at 0.53 flips nothing | **Measured** | band (0.504, 0.552) | a section between 0.53 and 0.55 prints certain; none exists on the seven songs |
| A11 | No onset statistic tells one guitar from two on a sixteenth grid | **Measured as null** | 17 features, `strum-confidence.md` 7.2; the register split (A20) is the open route | the limitation is stated where a rule could have been |
| A12 | Fame's and Need You Tonight's guitar parts are riffs, not strums | **Verified by ear** | section 2 | none |
| A13 | The two riff features classify every section of the seven songs as the ear did | **Measured** on the research's features | riff side entropy at most 0.788 and single share at least 0.466; strum side entropy at least 0.872; Pour Some Sugar On Me single share at most 0.426 | the Pour Some Sugar On Me margin is 0.04: a two-guitar section could be marked riff; A17 re-measures with the stage's own code |
| A14 | One bar is enough in the strip when no bar changes inside it | Unverified with a player | the grid shows bar-to-bar changes | revert to a one-bar strip only when both bars show one chord: Summer of '69 stays at 3 pages |
| A15 | Players accept differing cell widths between sections | Unverified | the Fame crops in `page-layout.md` | reserve the strip column in every section with a strip |
| A16 | Cells as narrow as 18.8 mm hold every chord cell without wrapping | **Measured** on the seven sheets | no wraps | a wrapped row adds about 5 mm; a sheet at 95 percent could regain a page |
| A17 | The riff thresholds hold when computed by the stage's own code on every section | **Spike to run during planning** | the research computed them in a scratch script on the stage's onsets | the constants move inside their bands or the rule needs a third feature |
| A18 | Two of three rules name the right tonic when the chord rules disagree, and the chord rules agree on the five known songs | **Verified on the stored decisions** (same probe) | the pair rule agrees with the score on six of seven (Summer of '69 D, Chelsea G, Pour Some Sugar On Me C#, Wet Leg C by chroma from a tie, Fame F, All Fired Up G); Need You Tonight alone disagrees (score C, pair F by chroma, mix F) and the ear says F | a song where the pair rule and the mix are both wrong prints wrong-first with the right tonic hedged |
| A19 | The pair rule's chroma tie-break is stable enough to vote | Refuted within Need You Tonight (first half C by 0.009, second half F by 0.114), held on Wet Leg | `key-hedge-and-power-note.md` section 2 | the vote could flip on a different window; with two tied tonics the hedge still names the other, so the header's content is stable even when the order is not |
| A20 | Where a stem holds two parts, their onsets sit in different registers and the lower stream alone gives an ear-accepted strum pattern | **Spike running at the time of writing**; resolved in the validation pass below | the owner's ear on Fame and Pour Some Sugar On Me; `register-split.md` | if it works, section 4.2's limitation becomes a rule (strum from the lower stream) and Pour Some Sugar On Me's choruses may print certain; if null, the limitation stands |
| A21 | One extra legend line adds no page | **Measured** | Pour Some Sugar On Me 2 pages with one and with three lines; no other song has a power chord | caught by the page-count check |
| A22 | New defaulted fields keep 1.3 and 1.4 files loading | **Verified** (same probe) | subclasses of `Key`, `Chords`, `SectionPattern`, `Strums`, `ScoreSection` and `Score` with every section-7 field loaded `chords.json`, `strums.json` and `score.json` from all seven 1.4 folders and the five 1.3 folders in `runs_v13` | an old file fails to load; a test catches it |
| A23 | The blind song exercises the power-chord gates and the riff marker | Unverified by design (not listened to) | chosen by the owner for the 1.4 reviewer's request (major key, minor-pentatonic riff) | the gates are still only partly tested; recorded, not fixed |
