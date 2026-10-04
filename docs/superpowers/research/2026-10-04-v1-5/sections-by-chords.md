# Version 1.5 research: naming verses and choruses by chord content

Date: 2026-10-04. Strand: section labels. Question: All Fired Up prints 13 sections (eight verses, three choruses) with one Em D G cycle under most of them, and Need You Tonight prints three verses and two choruses on a riff song. Should the sheet name or merge sections by their chords as well as by their sound, and if so by what rule?

Everything below was measured on the seven validation runs (`runs/<song>/02_grid/grid.json`, `03_harmony/chords.json`, `04_strums/strums.json`, `06_score/score.json`, the audio and stems) with the project's own code imported read-only. No source file, test or run folder was changed. Scratch scripts live in `%TEMP%\youkelele-v15-research\sections\` (`common.py`, `clusters.py`, `sim.py`, `calib.py`, `melody.py`, `rules.py`, `final.py`, `gate.py`, `modulate.py`, `gen_md.py`). Bars and sections are 0-based and end-exclusive, as in `grid.json`. Songs are described only by section type, order, bar counts and chord names.

## Answer in brief

- **Chord content agrees with the sound wherever it has anything to say.** On the four songs whose verse and chorus use different chords (Summer of '69, Chelsea Dagger, Pour Some Sugar On Me, Need You Tonight) the chord groups are exactly the grid's beat-chroma clusters, so naming by chord group changes no label on any of them. On the three one-loop songs (All Fired Up, Fame, Wet Leg) one chord group holds 93 to 100 percent of the sung bars, so chords cannot say which part is the chorus. A published chart for All Fired Up puts its verse and chorus on the same G Em D cycle, so renaming by chords would erase choruses that exist.
- **The chorus cannot be "the most repeated chord group".** On Summer of '69 the D A group recurs five times (verses, a hook extension, a breakdown and an outro vamp share those chords) against three for the Bm A D G group; by repetition or by vocal share the rule picks the wrong group. Mix loudness, today's rule, is right on all three songs with a reference.
- **Neither vocal level, the beat-chroma cluster nor a vocal-stem melody proxy separates a chorus sung on the verse chords.** Measured on the one known case (Summer of '69 bars 53-58, which the owner's hand list puts inside the second chorus on D A) and on All Fired Up, where same-label and different-label pairs on the same chords have the same vocal-chroma similarity (mean 0.937 against 0.936).
- **What chords can do is remove fragments.** A section shorter than one phrase (8 bars) whose label equals a neighbour's and which plays no chord that neighbour lacks is a piece of that neighbour on a chord sheet: merge it. A verse fragment between two choruses that adds no chord joins them. This takes All Fired Up from 13 sections to 6 (Intro, Verse 1, Chorus 1, Verse 2, Chorus 2, Outro) and from four pages to three, Wet Leg from 9 to 8, and touches nothing on the other five songs.
- **Need You Tonight stays as it is.** Its two chord groups (F C alternation, 51 bars; C with Eb, 15 bars) are its two clusters and alternate V C V C V; chords give no reason to merge or rename. Which group is the chorus rests on a 0.03 dB loudness margin and cannot be settled without listening.

## 1. State of the code

| Where | What it does | Bearing on this strand |
|---|---|---|
| `src/youkelele/stages/grid.py:97-107` | Bar features, `segment_bars`, `boundaries_from_clusters` (4-bar minimum, `MIN_SECTION_BARS` at line 41), vocal-run boundaries, `label_sections` | Runs before harmony (stage order ingest, separate, grid, harmony, strums, arrange, score, render), so no chord can inform the grid's labels. The cluster id per bar is not written to `grid.json` |
| `src/youkelele/music/sections.py:96-121` | Recurrence graph from 4-step stacked chroma, path weights from MFCC, Laplacian eigenvectors | The cluster is mostly a chord detector: two passages on the same chords are near each other whoever plays them (see `structure-research.md` 1.1) |
| `src/youkelele/music/sections.py:378-389` | Verse = a cluster over 60% of sung bars (`SPLIT_SHARE`, line 25); chorus = the loudest recurring sung cluster with vocal share at least 0.5 (`CHORUS_MIN_VOCAL`, line 34) | The only verse/chorus decision is loudness between clusters; margins are 0.03 to 1.91 dB on the seven songs |
| `src/youkelele/music/sections.py:407-416` | Labels per segment: verse cluster, chorus cluster, once-only first/last as intro/outro, **everything else `verse`** (line 416) | `verse` is the catch-all. Two adjacent segments from different clusters both fall through to `verse`, which is how All Fired Up gets "Verse 3" to "Verse 7" in a row |
| `src/youkelele/music/sections.py:391-395` | Confidence 0.3 when the margin is under 1.5 dB (`LOW_MARGIN_DB`, line 26) | True on six of seven songs (all but Fame), so it carries no information |
| `src/youkelele/music/relabel.py:20-28` | `_bar_triads`: per bar, the triads of non-N events overlapping it | The bar-level chord string used throughout this study |
| `src/youkelele/music/relabel.py:31-47, 50-80` | `section_novelty`, `refine_labels`: one sung, inner section with at least 50% novel chord-bars becomes `bridge` | The precedent: a chord rule applied at the score stage, leaving `grid.json` alone |
| `src/youkelele/music/score_builder.py:31-49, 141-151` | `check_strums_match_grid` (one strum pattern per grid section); phrase alignment; `refine_labels` called at line 151 | Any merge must agree with the strums stage's per-section patterns |
| `src/youkelele/stages/strums.py:87-93, 118-122, 167-206` | Requires `harmony/chords.json`; calls `trailing_silent_bars` "the same way" as the score builder; one pattern per grid section | The strums stage already reads the chords, so it can share a chord-based section plan with the score builder, as it already shares `trailing_silent_bars` |
| `src/youkelele/render/html.py:31-45, 100` | `display_names`: a label that recurs is numbered by occurrence | Merging adjacent sections renumbers the rest |
| `src/youkelele/evaluate.py:205-220` | Prints refined labels per grid section | Would print the plan |

## 2. Data and method

**Reference structures.** Summer of '69 and Pour Some Sugar On Me: the owner's hand lists from spike round one (`sections_hand_list.json`, section types and start times). Summer of '69's times match the run's section starts within 1.8 s (the run's audio is the same); Pour Some Sugar On Me's run audio carries the video's 25.2 s pre-roll, and with that offset the hand list's verse 2, solo and breakdown starts land within 0.1 s of the run's. Chelsea Dagger and All Fired Up: section headings and chord names read from published user-made chord charts (sources below). Need You Tonight: one chart gives the section order but writes riffs as tab, not chord names. Wet Leg and Fame: no reference found; their verse and chorus positions are **unverified**. No reference was read for its words.

**Chord strings.** Per bar, the set of triads overlapping it (`relabel._bar_triads`, the same overlap rule as the bridge decision). A section's string is its bars' sets in order; a bar with no chord is `N`.

**Four pairwise measures** (all on the bar strings; substitution cost between two bars is one minus the Jaccard of their triad sets, so `D` against `D+G` costs 0.5):

- **M1**, normalised edit distance, global, best of no shift or one leading bar dropped from either string, divided by the longer length.
- **M2**, containment edit distance: the shorter string against its best window (length n-1 to n+1, so a one-bar shift is allowed) inside the longer, divided by the shorter length. 0 means the shorter is played inside the longer.
- **M3**, Jaccard over bar-pair bigrams (sets of consecutive-bar pairs).
- **M4**, cosine between the sections' chord-bar histograms (bag of chords).

**Sound cues.** The grid's cluster ids were recomputed from `00_ingest/audio.wav` with the stage's own functions (`bar_features`, `segment_bars` at the stored `sections_k`, `boundaries_from_clusters`, `insert_vocal_boundaries`, `label_sections`); the recomputed sections and labels equal `grid.json` on **7 of 7** songs. Vocal level is `bar_vocal_db`; vocal share uses `vocal_flags`. As a melody proxy, CQT chroma of the vocals stem was averaged per bar and compared, bar against bar, only over aligned bars that hold the same chord and are sung in both sections.

## 3. Measurements

The per-section chord strings and all four matrices for every song are in Appendix A. The summaries below are drawn from them.

### 3.1 Which measure separates same material from different material

Pairs of sung or played sections (intro and outro excluded) on the three songs with a reference, split by whether the reference gives both the same material: 26 same pairs, 50 different pairs.

| Measure | Same material: min, median, max | Different material: min, median, max | Separates? |
|---|---|---|---|
| M1 global edit distance, one-bar shift | 0.00, 0.29, 0.67 | 0.50, 0.82, 1.00 | No: overlap 0.50 to 0.67 (Summer of '69's 5-bar Verse 3 against its 16-bar Verse 5 scores 0.67 though both are D A) |
| **M2 containment edit distance** | 0.00, 0.00, **0.29** | **0.40**, 0.73, 1.00 | **Yes, gap 0.29 to 0.40** |
| M3 bar-pair Jaccard | 0.22, 1.00, 1.00 | 0.00, 0.11, 0.29 | No: overlap 0.22 to 0.29 (Pour Some Sugar On Me's choruses vary their B, E, A order) |
| M4 chord histogram cosine | **0.95**, 0.99, 1.00 | 0.00, 0.49, **0.80** | Yes, gap 0.80 to 0.95 |
| Run-length containment (repeats collapsed) | 0.00, 0.00, 0.50 | 0.33, 0.50, 1.00 | No |
| Pair chord novelty (share of the shorter's chord-bars on a chord the longer lacks) | 0.00, 0.00, 0.18 | 0.00, 0.00, 1.00 | No: a section on a subset of another's chords scores 0 |

Worst same pair under M2: Pour Some Sugar On Me's Chorus 2 against Chorus 3 (0.29). Closest different pair: Summer of '69's 5-bar Verse 3 (A A D D A) against the Bm A D G block (0.40). A match is therefore **M2 at most 0.35 and M4 at least 0.90** (both mid-gap); either alone also separates these three songs.

### 3.2 Chord groups per song against the reference (question 2)

Groups are connected components of matching sung sections labelled verse or chorus. "Share" is the group's part of the sung bars.

| Song | Chord groups (section indices, chords) | Share | Clusters in the group | Reference | Does grouping give the right verse/chorus split? |
|---|---|---|---|---|---|
| Summer of '69 | {1, 3, 5, 8, 10} D A; {2, 4, 9} Bm A D G | 0.60, 0.40 | {2}; {1} | Hand list: verse on D A; the Bm A D G block is pre-chorus plus a 2-bar hook (published charts call the block the chorus); 5 is the hook extended over D A, 8 a breakdown, 10 the sung outro, all on D A | The harmonic split, yes, and identical to the clusters. Functions of 5, 8 and 10 are not in the chords |
| Chelsea Dagger | {1, 3, 6} G D vamp; {2, 4} G A C B(m) Em D | 0.58, 0.42 | {1}; {0} | Chart: intro G D, verse G A7 C7 B Em D, chorus G D, bridge G C D, outro G D | Yes, identical to the clusters. Section 6 (34 bars) opens with about 16 bars of the chart's bridge (G C Am D) that neither cue splits off |
| Pour Some Sugar On Me | {1, 3} C#m riff; {2, 4, 7} B E A; {6} alone (N x4, E E, B+F#) | 0.40, 0.51, 0.09 | {1}; {0}; {1} | Hand list: verses on the riff, choruses, solo, breakdown at section 6 | Yes for verse and chorus. Section 6 matches no other section by chords (M2 0.43 to 0.86) yet prints "Verse 3"; the hand list calls it a breakdown. The one place where chords were right and sound wrong, on a section with 4 of 7 bars chordless |
| Need You Tonight | {1, 3, 5} F C alternation; {2, 4} C with Eb (Cm, Gm) | 0.77, 0.23 | {0}; {1} | Chart order: intro, verse, pre-chorus, chorus, bridge, pre-chorus, chorus, outro, riffs only | Grouping equals the clusters. Bar positions of the chart's parts unverified |
| Wet Leg | {0 to 6} C F Dm; {7} | 0.93, 0.07 | {0, 1, 2, 4}; {1} | None found | One loop: chords cannot split |
| Fame | {1, 3, 5, 6, 8} F (Bb) | 1.00 | {0, 1, 4} | None found | One loop: chords cannot split |
| All Fired Up | {1 to 10} G Em D; {11} Em Em D D | 0.96, 0.04 | {0, 1, 3, 4}; {0} | Chart: intro, verse, chorus, verse, chorus, a final section, outro, every part on G Em D | One loop: chords cannot split, and the chart says the parts do share chords |

So labelling by chord group gives the right split on the three referenced songs only because it reproduces what the clusters already give; on the one-loop songs it gives no split at all.

### 3.3 Where chord content and loudness disagree, which is right? (question 3)

They disagree in two ways.

1. **Same chords, different sound label.** All Fired Up (verse and chorus labels on one cycle), Wet Leg and Fame. The chord evidence is right that the reader plays the same chords, and the published All Fired Up chart confirms that a real verse and chorus share them there; it cannot say where the chorus is. The loudness labels pick a chorus cluster by 0.58 dB (All Fired Up), 0.22 dB (Wet Leg) and 1.91 dB (Fame). Van Balen et al. found loudness alone not significant as a chorus cue (coefficient 0.03, interval -0.01 to 0.06; as cited in `structure-research.md` 1.4). Neither cue is verified on these songs; the names there come from sound alone.
2. **Different chords, same sound label.** Pour Some Sugar On Me section 6: chords say it is unlike any verse, the cluster puts it with the verses, the hand list says breakdown. Chords were right. One case, with three chord-bars, is too little to found a rule; it is recorded, not proposed (see 4.4).

On the four chord-distinct songs the two never disagree at the group level.

### 3.4 Can the chorus be the matched group with the highest repetition and vocal share? (question 4, first part)

| Song | Chorus by repetition (occurrences) | By vocal share | By median vocal dB | By mix loudness (today) | Reference |
|---|---|---|---|---|---|
| Summer of '69 | D A group (5 against 3) **wrong** | D A group (0.98 against 0.97) **wrong** | Bm A D G (-16.6 against -18.3 dB) | Bm A D G (-12.0 against -12.7 dB) | Bm A D G block |
| Chelsea Dagger | G D (3 against 2) | tie (1.00, 1.00) | verse group (-24.9 against -26.4 dB) **wrong** | G D (-19.5 against -19.9 dB) | G D |
| Pour Some Sugar On Me | B E A (3 against 2) | B E A (0.98 against 0.91) | B E A (-26.2 against -29.5 dB) | B E A (-21.8 against -22.9 dB) | B E A |
| Need You Tonight | F C group (3 against 2), flips today's label | F C group (1.00 against 0.87), flips | C Eb group (-20.1 against -21.4 dB) | C Eb group, margin 0.03 dB | Unverified |

Repetition fails on Summer of '69 because every passage on the verse chords counts towards the verse group: post-chorus riff, breakdown and outro vamp. Goto's RefraiD outputs "the group that appears most frequently" but counts repeats of the whole sound, melody included, not of the chords (ICASSP 2003). Vocal share is near 1 for both groups on every song. **Answer: no.** Mix loudness between groups is right on 3 of 3 referenced songs and is what the code already does; on the chord-distinct songs the groups are the clusters, so today's rule already is "the loudest chord group".

### 3.5 A chorus on the verse chords: does vocal level, the cluster or the melody still separate it? (question 5, second risk)

The common case in pop. The project's known songs hold one verified instance: Summer of '69 bars 53-58 (A A D D A), which the owner's hand list places inside the second chorus (it marks the second chorus from 83.6 s to 99.2 s, covering the last bars of the Bm A D G block and this stretch).

| Cue | Bars 53-58 | The verses (D A) | The Bm A D G blocks | Separates? |
|---|---|---|---|---|
| Beat-chroma cluster | 2 | 2 (all five) | 1 | No |
| Median vocal dB | -18.3 | -20.1 to -17.0 | -18.1 to -15.7 | No |
| Mix dB | -11.9 | -15.0 to -11.6 | -12.6 to -11.4 | No |
| Vocal-chroma cosine to the verses, same-chord bars | 0.81 to 0.95 | verse against verse 0.83 to 0.96 | | No |

On All Fired Up, every pair of sung sections whose chords match was compared: pairs with the same label have a mean vocal-chroma cosine of 0.937 (0.859 to 0.992, 23 pairs), pairs with different labels 0.936 (0.870 to 0.991, 12 pairs). Median vocal dB per section runs -27.2 to -16.8 for verse-labelled sections and -21.8 to -16.6 for chorus-labelled ones; mix dB -16.9 to -13.5 against -15.4 to -13.7. The clusters do split the cycle into four ids, but the split does not follow vocal level or the melody proxy. Wet Leg (same label 0.72 to 0.97, different 0.77 to 0.97) and Fame (0.90 to 0.98 against 0.91 to 0.96) show the same. **None of the three cues separates same-chord sections on these songs.** A bar-averaged vocal chroma is a blunt melody proxy; a pitch tracker on the vocal stem might do better, which this study did not test (assumption A12).

### 3.6 A modulating song (question 5, first risk)

None of the seven modulates. Simulated: Summer of '69's sections 9 to 11 (the third Bm A D G block onwards) transposed up a whole tone, as in a last-chorus lift. M2 from the lifted block to Chorus 1 rises from 0.00 to 0.92, so an exact-chord match no longer finds it; taking the minimum over the twelve transpositions brings it back to 0.00 (and the lifted D A vamp to Verse 1 at 0.07). The bridge rule is unaffected: the lifted chords recur across the three lifted sections, so none of them is novel, and the real bridge keeps novelty 0.80. Goto handles modulated choruses the same way, by "considering twelve kinds of shifts" of chroma (ICASSP 2003). The proposed merge (section 4) only compares a fragment with its own neighbour, so a key change between sections makes the pair novel and blocks the merge, which is the safe outcome.

### 3.7 A song with no repeats (question 5, third risk)

None of the seven is through-composed. Reasoned from the code: with no recurring cluster, `label_sections` takes the largest sung cluster as chorus (sections.py:384-386) and names the rest `verse`. Chord groups would all be singletons, so a chord-group naming rule has nothing to work with. The proposed merge needs a same-label neighbour that plays every chord of a short section; on a through-composed song that can fire only where a short section repeats its neighbour's chords, which is then the right call.

### 3.8 Fragments on the seven songs

Sections shorter than 8 bars (the proposed `FRAGMENT_BARS`), with their neighbours.

| Song | Fragment (bars) | Label | Neighbours | Same-label neighbour that plays all its chords? | Merged? |
|---|---|---|---|---|---|
| Summer of '69 | 0-4, 53-58, 68-75 | intro, verse, instrumental | none, chorus/bridge, bridge/verse | No | No |
| Pour Some Sugar On Me | 77-84 | verse | instrumental/chorus | No | No |
| Fame | 29-35, 81-85 | instrumental | verses | No (label not verse or chorus) | No |
| Need You Tonight | 24-31, 79-86 | chorus, outro | verses; verse | No | No |
| Wet Leg | 0-5, 58-65, 108-113 | verse, verse, outro | chorus; verse 42-58 and verse 65-100; chorus | 58-65: both (C, Dm); better match 65-100 (M2 0.29 against 0.43) | 58-65 into 65-100 |
| All Fired Up | 28-33, 55-61, 90-97, 97-104, 104-110 | verse | a verse on at least one side | Yes, novelty 0.00 against it in every case | Yes |
| All Fired Up | 124-128 (G x4) | verse | chorus 110-124 and chorus 128-132 | Its G is in both | Yes, by the sandwich rule |
| All Fired Up | 49-55, 128-132 | chorus | verses; verse/outro | 49-55 no; 128-132 joins via the sandwich | 49-55 no |

On the three referenced songs no section has a same-label neighbour at all, so the rule cannot touch them.

## 4. Proposal

### 4.1 Verdict on merging and renaming

- **Merging adjacent same-chord same-label sections is right when one of them is a fragment.** A section shorter than a phrase that adds no chord to its same-label neighbour carries no information a chord-sheet reader can use; printing it as its own "Verse" is what makes All Fired Up read as eight verses. The typical section is 8 bars or more (Shibata et al. set the expected section length to 32 beats, 8 measures; Marmoret et al. give zero cost at 8 bars; both as cited in `structure-research.md` 1.2).
- **Merging two whole sections (8 bars or more) because their chords match is not decidable from chords.** Two verses in a row on the same chords are a real form, and on Wet Leg such a merge would join a 16-bar section to a 35-bar one in a different bar pattern. Not proposed.
- **Renaming by chord group is not right.** Where chords differ it reproduces the clusters (no change); where they do not, it would print one label for the whole song and drop choruses that, on All Fired Up, a published chart has.

### 4.2 The rule

A section plan, computed after harmony from `grid.json`, `chords.json` and `refine_labels`, applied until nothing changes:

1. **Sandwich.** A `verse` section shorter than `FRAGMENT_BARS` between two `chorus` sections, whose chord-bars all hold triads both neighbours play (pair novelty 0), joins them into one `chorus`. `verse` is the labeller's fall-through (sections.py:416) and `chorus` a positive choice (sections.py:383), so the fragment's own label carries no evidence against it. On All Fired Up the fragment (124-128) is also the loudest sung section by vocal and mix level (-16.8 dB, -13.5 dB), as loud as the choruses either side.
2. **Fragment merge.** A `verse` or `chorus` section shorter than `FRAGMENT_BARS` joins a neighbour with the same label that is at least as long and plays every triad it plays (pair novelty 0). With two such neighbours it joins the one with the lower M2.
3. **Labels and names are untouched otherwise**: intro, instrumental, outro and bridge never merge; `display_names` numbers the result.

In code terms (a sketch for `music/relabel.py`, beside `refine_labels`):

```python
FRAGMENT_BARS = 8  # a same-label section shorter than one phrase that adds no chord is a fragment

@dataclass(frozen=True)
class PlannedSection:
    start_bar: int
    end_bar: int  # exclusive
    label: str
    members: tuple[int, ...]  # grid section indices

def section_plan(grid: Grid, chords: Chords) -> list[PlannedSection]:
    """refine_labels, then the sandwich and fragment merges until stable."""
```

### 4.3 Where it runs

The plan must be shared by the strums stage and the score builder, as `trailing_silent_bars` already is (score_builder.py:145-148, strums.py:118-122):

- `stages/strums.py:130-206`: loop over `section_plan(grid, chords)` instead of `grid.sections`, so each merged section gets one pattern voted over all its bars. The stage already requires `harmony/chords.json`.
- `music/score_builder.py:31-49`: `check_strums_match_grid` compares the pattern count with the plan; `music/score_builder.py:141-199`: build sections from the plan (phrase alignment takes the plan's spans).
- `evaluate.py:205-220`: print the plan with the member grid sections.
- `grid.json` keeps the labeller's own sections, as it already does for the bridge (score_builder.py:150). A `strums.json` made before the change has one pattern per grid section and fails the existing "re-run from strums" check on the two songs whose plan differs.

A score-only alternative (merge at the score stage and keep the longest member's pattern) avoids touching the strums stage, but the merged section then shows a pattern voted over part of its bars; on All Fired Up the members' patterns differ (for example `D-D-D-DU` over 29 bars against `xxDxDxDx` and `Dxxxxxxx` over 7 and 6), so the strip would be voted over 29 of the merged Verse 2's 55 bars.

### 4.4 Constants and the band each sits in

| Constant | Value | Measured band | Evidence |
|---|---|---|---|
| `FRAGMENT_BARS` | 8 | Above 7, at most 16 | The largest fragments that must merge on All Fired Up are 7 bars (90-97, 97-104); the shortest same-label neighbours that must stay whole are 16 bars (Wet Leg 42-58, All Fired Up 33-49). At 6, All Fired Up stays at 10 sections; at 8 or 10, 6. One phrase in the literature (32 beats) |
| Pair novelty for a merge | 0 (strict) | Every merged fragment measured 0.00; no fragment with a same-label neighbour measured above 0 | Same notion as `section_novelty` (relabel.py:31-47), so a fragment that brings a new chord stays a candidate for the bridge rule |
| Chord match (M2 / M4) | at most 0.35 / at least 0.90 | 0.29 to 0.40 / 0.80 to 0.95 | Section 3.1, 76 pairs on three songs. In the rule M2 only chooses between two eligible neighbours (Wet Leg 0.29 against 0.43), and both measures define the groups for 4.5 |
| One-loop share (for 4.5) | 0.85 | 0.77 to 0.93 | Largest chord group: 0.51 to 0.77 on the four chord-distinct songs, 0.93 to 1.00 on the three one-loop songs |

Not proposed, with reasons: a 6 dB vocal-level gate on the fragment merge (keeps All Fired Up's quietly sung 90-97 apart, 8 sections instead of 6, still three pages; same-type section pairs on the referenced songs differ by up to 3.1 dB and this fragment by 8.6, a single case; see risk 3); a "singleton chord group is a breakdown" rename (one case, Pour Some Sugar On Me section 6, with three chord-bars).

### 4.5 Optional: say when the names come from sound alone

When the largest chord group holds at least 0.85 of the sung bars, the verse/chorus names on that sheet rest on loudness alone. `evaluate` and the manifest could record "verse and chorus share their chords (one chord group, share 0.96)" for Wet Leg, Fame and All Fired Up. A one-line sheet note ("Verse and chorus use the same chords here") would tell the reader that the names do not change what they play; it costs a line on sheets the page-layout strand is trying to shorten, so it is offered, not recommended. This would replace `labels_low_confidence` as the signal worth reading, since that flag is set on six of seven songs.

## 5. Expected effect per song

Measured by applying the rule to each run's sections (`final.py`); pages from rendering a merged copy of `score.json` with the project's `render_html` and `html_to_pdf` in the scratch folder (merged sections keep the longest member's pattern; the baseline renders reproduce 4 and 3 pages).

| Song | Sections before | Sections after | Printed after | Pages before, after |
|---|---:|---:|---|---|
| Summer of '69 | 12 | 12 | unchanged | 3, 3 (not rendered) |
| Chelsea Dagger | 7 | 7 | unchanged | 3, 3 (not rendered) |
| Pour Some Sugar On Me | 8 | 8 | unchanged | 2, 2 (not rendered) |
| Wet Leg | 9 | 8 | Verse 1, Chorus 1, Verse 2, Chorus 2, Verse 3 (42-58), Verse 4 (58-100, was Verse 4 and Verse 5), Chorus 3, Outro | 3, 3 |
| Fame | 9 | 9 | unchanged | 3, 3 (not rendered) |
| All Fired Up | 13 | 6 | Intro (0-28), Verse 1 (28-49), Chorus 1 (49-55), Verse 2 (55-110), Chorus 2 (110-132), Outro (132-156) | 4, 3 |
| Need You Tonight | 7 | 7 | unchanged | 2, 2 (not rendered) |

All Fired Up after the rule reads intro, verse, chorus, verse, chorus, outro; the chart's order is intro, verse, chorus, verse, chorus, a final section, outro. Whether the chart's final section is inside the merged Verse 2 (90-110 is where the singing drops) is a listening question (risk 3). With the page-layout strand's A2 + R the page-layout study already reaches three pages for All Fired Up without any merge; the merge removes five section heads and gaps on top of that.

## 6. Risks

1. **A real short section is folded away.** A 4- to 7-bar pre-chorus or tag that the labeller called `verse` next to a verse, on the verse's chords, would lose its heading. None of the three referenced songs has such a pair (section 3.8); the cost is a missing heading, not a wrong chord.
2. **The sandwich puts a short verse inside a chorus.** Only one case fired (All Fired Up 124-128), where the section's own levels are chorus-like. On a song with a short verse between two choruses on chorus chords it would print the verse as chorus.
3. **All Fired Up 90-110.** The merged Verse 2 spans bars where the vocal share falls to 0.57 and the median vocal level to -27.2 dB (90-97), and two sections whose strums print mostly muted strokes (97-104, 104-110). If listening shows a separate part there, the 6 dB vocal gate (section 4.4) keeps 90-97 apart: 8 sections, still three pages.
4. **The chorus stays a loudness call on one-loop songs.** The rule does not make All Fired Up's, Wet Leg's or Fame's chorus names any surer (section 3.3).
5. **Modulation.** A key change between a fragment and its neighbour blocks the merge (safe). Any future chord-group naming must match over the twelve transpositions (section 3.6).
6. **Strum patterns change on merged sections.** One pattern is voted over the merged bars; a fragment with a distinct strum (All Fired Up's muted-stroke 97-110) is outvoted.
7. **A wrong chord string.** On the blind songs the chord names are unverified (validation "What cannot be verified"). A spurious chord in a fragment makes its novelty non-zero and blocks the merge (safe); a missed chord can let a real new part merge.
8. **Need You Tonight's chorus.** Unchanged by this rule. Its chorus pick has the smallest loudness margin of the seven (0.03 dB); the vocal level agrees with it (+1.3 dB), vocal share and repetition disagree (section 3.4). Not settled without listening.

## Assumptions

| # | Assumption | Status | Cost if wrong |
|---|---|---|---|
| A1 | The recomputed cluster ids are the grid stage's | Verified: recomputed sections and labels equal `grid.json` on 7 of 7 songs | The cluster columns and the cluster-against-chords comparisons would be off |
| A2 | The hand lists for Summer of '69 and Pour Some Sugar On Me describe the run audio | Verified for Summer of '69 (section starts within 1.8 s); measured for Pour Some Sugar On Me (25.2 s pre-roll offset, three starts within 0.1 s) | Reference groups in 3.1 and 3.2 shift; the M2 band (0.29 to 0.40) could narrow or close |
| A3 | The user-made charts for Chelsea Dagger and All Fired Up reflect the records' section types and chords | Unverified (community charts, section headings and chord names only) | If All Fired Up's verse and chorus differ in chords, chords could split it and 4.1's third verdict would be revisited for that song |
| A4 | A same-label section under 8 bars that adds no chord is a fragment of its neighbour | Measured on the seven songs (6 merges on All Fired Up, 1 on Wet Leg, none on the referenced songs); unverified by listening | A real short part loses its heading (risk 1) |
| A5 | `verse` is the labeller's fall-through, so a verse fragment between choruses can take the chorus label | Verified in code (sections.py:407-416); measured once | A short verse prints inside a chorus (risk 2) |
| A6 | `FRAGMENT_BARS` 8 generalises | Measured band above 7 to 16 on two songs | At 6 All Fired Up keeps 10 sections; above 16 whole sections start merging |
| A7 | M2 0.35 and M4 0.90 generalise | Measured on 76 pairs of three songs; the M2 gap is 0.11 wide | Only the neighbour choice (one case) and the optional one-loop note depend on them |
| A8 | One-loop share 0.85 | Measured band 0.77 to 0.93 on seven songs | The optional note prints on a wrong song or is missing; text only |
| A9 | A pattern voted over a merged section is a fair strip for it | Unverified; members' patterns differ on All Fired Up | The strip describes the majority and hides a distinct stretch (risk 6) |
| A10 | Phrase alignment (`aligned_starts`) behaves on the plan's spans as on grid spans | Unverified; the what-if concatenated the score's already-aligned sections | A merged boundary could move by a bar |
| A11 | The page what-if stands for the real change | Measured with the project's renderer; merged sections keep the longest member's pattern and certainty | A strip shown or hidden differently could move the last page by a few rows; the page-layout study made the same assumption for its merge variant |
| A12 | Bar-averaged vocal-stem chroma is a fair melody proxy | Unverified; it scores verse against verse 0.83 to 0.96 on Summer of '69 | The negative result in 3.5 may understate what a pitch tracker could separate |
| A13 | No song in the set modulates or lacks repeats | Verified for modulation by the chord strings; through-composed form reasoned from code only | The risks in 3.6 and 3.7 are simulated or reasoned, not measured |

## Sources

Project (read-only): `src/youkelele/music/sections.py`, `music/relabel.py`, `music/score_builder.py`, `stages/grid.py`, `stages/strums.py`, `render/html.py`, `evaluate.py`; `docs/superpowers/specs/2026-10-04-v1-4-validation.md` ("Per song", "What to improve next" item 1); `docs/superpowers/research/2026-10-03-quality/strands/structure-research.md` and `structure-applied.md`; `docs/superpowers/research/2026-10-04-v1-5/page-layout.md` (merge variants D1 and D2); the owner's hand lists `sections_hand_list.json` from spike round one (session scratchpad).

Literature and references (verified by reading unless marked):

- Goto, "A Chorus-Section Detecting Method for Musical Audio Signals", ICASSP 2003: chorus as the most frequently appearing group of repeated sections; modulated repeats found by twelve chroma shifts; correct chorus sections in 80 of 100 songs. https://staff.aist.go.jp/m.goto/PAPER/ICASSP2003goto.pdf
- Wang, Hung, Smith, "To Catch a Chorus, Verse, Intro, or Anything Else", ICASSP 2022: "some songs have the same chord progression for both the verse and chorus" (as quoted and verified in `structure-research.md` 1.1). https://arxiv.org/pdf/2205.14700
- Shibata, Nishikimi, Nakamura, Yoshii, ISMIR 2019, and Marmoret, Cohen, Bimbot, TISMIR 2023: section length prior of 32 beats (8 measures) and the 8-bar zero-cost size (as cited in `structure-research.md` 1.2).
- Van Balen, Burgoyne, Wiering, Veltkamp, ISMIR 2013: loudness not significant on its own as a chorus feature (as cited in `structure-research.md` 1.4).
- Mauch, Noland, Dixon, "Using Musical Structure to Enhance Automatic Chord Transcription", ISMIR 2009: chroma shared between repeated segments such as verses (from the abstract only). https://ir.webis.de/anthology/2009.ismir_conference-2009.36
- Chord charts, read for section headings and chord names only: All Fired Up https://www.chordie.com/chord.pere/www.guitaretab.com/p/pat-benatar/165041.html ; Chelsea Dagger https://www.chordie.com/chord.pere/www.guitaretab.com/t/the-fratellis/352196.html ; Need You Tonight https://pg.zachmanson.com/tab/inxs/need-you-tonight-chords-2895989 and https://guitaralliance.net/wp-content/uploads/2023/09/Quick-Notes-Need-You-Tonight-INXS.pdf

## Appendix A. Per-section chord strings and similarity matrices

For each song: the sections as printed today (index, printed name, bar range, length, recomputed cluster, vocal share, median vocal dB, mean mix dB, bar triads run-length coded, `x3` meaning three bars), then two combined matrices. In the first, cells below the diagonal are M2 (containment edit distance, 0 = same) and cells above are M3 (bar-pair Jaccard, 1 = same). In the second, below is M1 (global edit distance with a one-bar shift, 0 = same) and above is M4 (chord histogram cosine, 1 = same). `N` is a bar with no chord; `D+G` a bar holding both.

#### summer-of-69

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Intro | 0-4 | 4 | 3 | 0.25 | -76.6 | -20.6 | N Dx3 |
| 1 | Verse 1 | 4-19 | 15 | 2 | 1.00 | -17.4 | -15.0 | D Ax2 Dx2 Ax2 Dx2 Ax2 Dx2 Ax2 |
| 2 | Chorus 1 | 19-31 | 12 | 1 | 0.92 | -18.1 | -12.6 | Bm A D G Bm A D G Bm A Dx2 |
| 3 | Verse 2 | 31-41 | 10 | 2 | 0.90 | -18.0 | -12.2 | Ax2 Dx2 Ax2 Dx2 Ax2 |
| 4 | Chorus 2 | 41-53 | 12 | 1 | 1.00 | -15.7 | -11.4 | Bm A D G Bm A D G Bm A Dx2 |
| 5 | Verse 3 | 53-58 | 5 | 2 | 1.00 | -18.3 | -11.9 | Ax2 Dx2 A |
| 6 | Bridge | 58-68 | 10 | 3 | 1.00 | -15.3 | -10.8 | A F Bb C Bb F Bb Cx2 D |
| 7 | Instrumental | 68-75 | 7 | 2 | 0.00 | -74.8 | -12.4 | D Ax2 Dx2 Ax2 |
| 8 | Verse 4 | 75-83 | 8 | 2 | 1.00 | -17.0 | -11.7 | Dx2 Ax2 Dx2 Ax2 |
| 9 | Chorus 3 | 83-95 | 12 | 1 | 1.00 | -15.9 | -11.9 | Bm A D G Bm A D G Bm A Dx2 |
| 10 | Verse 5 | 95-111 | 16 | 2 | 1.00 | -20.1 | -11.6 | Ax2 Dx2 Ax2 Dx2 Ax2 Dx2 Ax2 Dx2 |
| 11 | Outro | 111-121 | 10 | 0 | 0.60 | -28.2 | -13.7 | Ax2 Dx2 Nx3 A Bm N |

summer-of-69: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.20 | 0.17 | 0.20 | 0.17 | 0.20 | 0.00 | 0.20 | 0.20 | 0.17 | 0.20 | 0.11 |
| **1** | 0.50 | · | 0.29 | 1.00 | 0.29 | 1.00 | 0.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.33 |
| **2** | 0.50 | 0.42 | · | 0.29 | 1.00 | 0.29 | 0.00 | 0.29 | 0.29 | 1.00 | 0.29 | 0.18 |
| **3** | 0.50 | 0.00 | 0.50 | · | 0.29 | 1.00 | 0.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.33 |
| **4** | 0.50 | 0.42 | 0.00 | 0.50 | · | 0.29 | 0.00 | 0.29 | 0.29 | 1.00 | 0.29 | 0.18 |
| **5** | 0.50 | 0.00 | 0.40 | 0.00 | 0.40 | · | 0.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.33 |
| **6** | 0.75 | 0.80 | 0.80 | 0.90 | 0.80 | 0.80 | · | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **7** | 0.50 | 0.00 | 0.57 | 0.00 | 0.57 | 0.00 | 0.86 | · | 1.00 | 0.29 | 1.00 | 0.33 |
| **8** | 0.50 | 0.00 | 0.50 | 0.00 | 0.50 | 0.00 | 1.00 | 0.00 | · | 0.29 | 1.00 | 0.33 |
| **9** | 0.50 | 0.42 | 0.00 | 0.50 | 0.00 | 0.40 | 0.80 | 0.57 | 0.50 | · | 0.29 | 0.18 |
| **10** | 0.50 | 0.07 | 0.42 | 0.00 | 0.42 | 0.00 | 0.80 | 0.00 | 0.00 | 0.42 | · | 0.33 |
| **11** | 0.50 | 0.60 | 0.70 | 0.60 | 0.70 | 0.20 | 0.90 | 0.43 | 0.62 | 0.70 | 0.60 | · |

summer-of-69: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.66 | 0.65 | 0.55 | 0.65 | 0.55 | 0.20 | 0.60 | 0.71 | 0.65 | 0.71 | 0.53 |
| **1** | 0.79 | · | 0.79 | 0.99 | 0.79 | 0.99 | 0.29 | 1.00 | 1.00 | 0.79 | 1.00 | 0.96 |
| **2** | 0.73 | 0.50 | · | 0.76 | 1.00 | 0.76 | 0.23 | 0.78 | 0.80 | 1.00 | 0.80 | 0.87 |
| **3** | 0.67 | 0.29 | 0.58 | · | 0.76 | 1.00 | 0.28 | 1.00 | 0.98 | 0.76 | 0.98 | 0.96 |
| **4** | 0.73 | 0.50 | 0.00 | 0.58 | · | 0.76 | 0.23 | 0.78 | 0.80 | 1.00 | 0.80 | 0.87 |
| **5** | 0.50 | 0.64 | 0.64 | 0.44 | 0.64 | · | 0.28 | 1.00 | 0.98 | 0.76 | 0.98 | 0.96 |
| **6** | 0.89 | 0.86 | 0.82 | 0.90 | 0.82 | 0.90 | · | 0.29 | 0.29 | 0.23 | 0.29 | 0.27 |
| **7** | 0.57 | 0.50 | 0.64 | 0.22 | 0.64 | 0.17 | 0.90 | · | 0.99 | 0.78 | 0.99 | 0.96 |
| **8** | 0.62 | 0.43 | 0.64 | 0.11 | 0.64 | 0.29 | 1.00 | 0.00 | · | 0.80 | 1.00 | 0.94 |
| **9** | 0.73 | 0.50 | 0.00 | 0.58 | 0.00 | 0.64 | 0.82 | 0.64 | 0.64 | · | 0.80 | 0.87 |
| **10** | 0.80 | 0.12 | 0.53 | 0.33 | 0.53 | 0.67 | 0.87 | 0.53 | 0.47 | 0.53 | · | 0.94 |
| **11** | 0.78 | 0.64 | 0.75 | 0.60 | 0.75 | 0.50 | 0.90 | 0.50 | 0.60 | 0.75 | 0.67 | · |

#### chelsea-dagger

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Intro | 0-20 | 20 | 1 | 0.00 | -96.5 | -24.7 | Nx3 Cx2 Nx3 Gx9 Dx3 |
| 1 | Chorus 1 | 20-38 | 18 | 1 | 1.00 | -26.9 | -19.8 | D Gx4 Dx4 Gx4 Dx4 G |
| 2 | Verse 1 | 38-61 | 23 | 0 | 1.00 | -24.9 | -20.0 | G Ax2 C Bm Em D Gx2 Ax2 C B Em D Emx4 Bm+Em Bmx3 |
| 3 | Chorus 2 | 61-71 | 10 | 1 | 1.00 | -26.7 | -19.6 | Gx4 Dx4 Gx2 |
| 4 | Verse 2 | 71-93 | 22 | 0 | 1.00 | -25.0 | -19.9 | Ax2 C Bm Em D Gx2 Amx2 C B Em D D+Em Emx3 Bm+Em Bmx3 |
| 5 | Instrumental | 93-108 | 15 | 1 | 0.00 | -94.4 | -21.1 | Gx4 Dx4 Gx4 Dx3 |
| 6 | Chorus 3 | 108-142 | 34 | 1 | 1.00 | -26.0 | -19.4 | D G C+D G C+D G C+D Am D G C+D G C+D G C+D Am D Gx4 Dx4 Gx4 Dx4 G |

chelsea-dagger: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.33 | 0.05 | 0.33 | 0.04 | 0.33 | 0.23 |
| **1** | 0.61 | · | 0.12 | 1.00 | 0.10 | 1.00 | 0.50 |
| **2** | 0.85 | 0.78 | · | 0.12 | 0.65 | 0.12 | 0.10 |
| **3** | 0.40 | 0.00 | 0.60 | · | 0.10 | 1.00 | 0.50 |
| **4** | 0.90 | 0.78 | 0.11 | 0.70 | · | 0.10 | 0.08 |
| **5** | 0.40 | 0.00 | 0.73 | 0.00 | 0.80 | · | 0.50 |
| **6** | 0.57 | 0.00 | 0.76 | 0.00 | 0.80 | 0.00 | · |

chelsea-dagger: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.88 | 0.37 | 0.94 | 0.32 | 0.90 | 0.87 |
| **1** | 0.68 | · | 0.34 | 0.98 | 0.35 | 1.00 | 0.96 |
| **2** | 0.87 | 0.83 | · | 0.35 | 0.95 | 0.34 | 0.37 |
| **3** | 0.74 | 0.41 | 0.83 | · | 0.33 | 0.99 | 0.93 |
| **4** | 0.91 | 0.86 | 0.11 | 0.83 | · | 0.35 | 0.41 |
| **5** | 0.58 | 0.12 | 0.78 | 0.33 | 0.83 | · | 0.96 |
| **6** | 0.61 | 0.45 | 0.82 | 0.70 | 0.82 | 0.55 | · |

#### pour-some-sugar-on-me

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Intro | 0-11 | 11 | 2 | 1.00 | -35.1 | -27.6 | N C#mx6 N C#m Nx2 |
| 1 | Verse 1 | 11-28 | 17 | 1 | 0.82 | -30.4 | -23.1 | C#mx4 Nx4 C#mx8 B+F# |
| 2 | Chorus 1 | 28-39 | 11 | 0 | 1.00 | -26.2 | -22.0 | B A+E A+B A+E B A+E B A+E B C#mx2 |
| 3 | Verse 2 | 39-55 | 16 | 1 | 1.00 | -28.6 | -22.7 | C#mx4 N Ex2 N C#mx8 |
| 4 | Chorus 2 | 55-67 | 12 | 0 | 1.00 | -26.5 | -22.3 | B+F# B A+E A+B A+E B A+E B A+E B C#m N |
| 5 | Instrumental | 67-77 | 10 | 1 | 0.00 | -74.8 | -22.7 | N A N A Ex2 N A Ex2 |
| 6 | Verse 3 | 77-84 | 7 | 1 | 1.00 | -28.5 | -22.0 | Nx4 Ex2 B+F# |
| 7 | Chorus 3 | 84-103 | 19 | 0 | 0.95 | -26.0 | -21.4 | B A+E B+E A+E B A+E B A+E B A+E B A+E B A+E B A+E B A+E B |

pour-some-sugar-on-me: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.80 | 0.11 | 0.43 | 0.10 | 0.00 | 0.14 | 0.00 |
| **1** | 0.27 | · | 0.10 | 0.38 | 0.09 | 0.00 | 0.12 | 0.00 |
| **2** | 0.91 | 0.82 | · | 0.09 | 0.62 | 0.00 | 0.00 | 0.25 |
| **3** | 0.36 | 0.12 | 0.73 | · | 0.08 | 0.22 | 0.25 | 0.00 |
| **4** | 0.82 | 0.92 | 0.09 | 0.83 | · | 0.00 | 0.00 | 0.22 |
| **5** | 0.90 | 0.80 | 0.80 | 0.60 | 0.80 | · | 0.12 | 0.00 |
| **6** | 0.86 | 0.43 | 0.86 | 0.57 | 0.86 | 0.43 | · | 0.00 |
| **7** | 1.00 | 0.97 | 0.23 | 0.97 | 0.29 | 0.75 | 0.86 | · |

pour-some-sugar-on-me: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.99 | 0.24 | 0.99 | 0.11 | 0.00 | 0.00 | 0.00 |
| **1** | 0.56 | · | 0.29 | 0.98 | 0.18 | 0.00 | 0.07 | 0.05 |
| **2** | 0.91 | 0.88 | · | 0.31 | 0.98 | 0.74 | 0.63 | 0.96 |
| **3** | 0.53 | 0.18 | 0.83 | · | 0.18 | 0.13 | 0.13 | 0.10 |
| **4** | 0.91 | 0.94 | 0.09 | 0.90 | · | 0.70 | 0.69 | 0.97 |
| **5** | 0.82 | 0.88 | 0.82 | 0.80 | 0.82 | · | 0.65 | 0.80 |
| **6** | 0.82 | 0.69 | 0.85 | 0.80 | 0.86 | 0.60 | · | 0.73 |
| **7** | 1.00 | 0.97 | 0.53 | 0.94 | 0.50 | 0.81 | 0.92 | · |

#### mangetout

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Verse 1 | 0-5 | 5 | 2 | 0.60 | -22.4 | -10.2 | Cx4 F |
| 1 | Chorus 1 | 5-18 | 13 | 1 | 0.62 | -21.3 | -8.8 | F Cx2 Fx2 Cx2 Fx2 Cx2 Fx2 |
| 2 | Verse 2 | 18-33 | 15 | 0 | 1.00 | -20.3 | -8.8 | Cx2 Fx2 Cx2 Fx2 Dm F Cx2 Dm F C |
| 3 | Chorus 2 | 33-42 | 9 | 1 | 1.00 | -21.0 | -8.6 | Cx3 Fx2 Cx2 Fx2 |
| 4 | Verse 3 | 42-58 | 16 | 0 | 0.69 | -19.5 | -8.9 | Cx2 Fx2 Cx2 Fx2 Dm F Cx2 Dm F Cx2 |
| 5 | Verse 4 | 58-65 | 7 | 2 | 1.00 | -20.4 | -9.1 | Cx6 Dm |
| 6 | Verse 5 | 65-100 | 35 | 4 | 1.00 | -18.5 | -10.5 | F Cx2 Dm F Cx2 Dm F Cx2 Dm F Cx2 Dm F Cx2 Dm F Cx2 Dm F Cx2 Dm F Cx2 Dm F Cx2 |
| 7 | Chorus 3 | 100-108 | 8 | 1 | 1.00 | -17.1 | -8.4 | Dm F Cx4 F C#+F |
| 8 | Outro | 108-113 | 5 | 3 | 0.00 | -78.2 | -12.2 | Nx5 |

mangetout: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.50 | 0.29 | 0.50 | 0.29 | 0.33 | 0.20 | 0.40 | 0.00 |
| **1** | 0.40 | · | 0.57 | 1.00 | 0.57 | 0.20 | 0.33 | 0.50 | 0.00 |
| **2** | 0.40 | 0.31 | · | 0.57 | 1.00 | 0.29 | 0.57 | 0.50 | 0.00 |
| **3** | 0.20 | 0.11 | 0.11 | · | 0.57 | 0.20 | 0.33 | 0.50 | 0.00 |
| **4** | 0.40 | 0.31 | 0.00 | 0.11 | · | 0.29 | 0.57 | 0.50 | 0.00 |
| **5** | 0.20 | 0.43 | 0.43 | 0.43 | 0.43 | · | 0.50 | 0.17 | 0.00 |
| **6** | 0.40 | 0.23 | 0.27 | 0.33 | 0.25 | 0.29 | · | 0.50 | 0.00 |
| **7** | 0.00 | 0.44 | 0.38 | 0.44 | 0.38 | 0.43 | 0.38 | · | 0.00 |
| **8** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | · |

mangetout: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.82 | 0.87 | 0.91 | 0.90 | 0.96 | 0.91 | 0.89 | 0.00 |
| **1** | 0.58 | · | 0.97 | 0.98 | 0.96 | 0.64 | 0.86 | 0.94 | 0.00 |
| **2** | 0.64 | 0.27 | · | 0.98 | 1.00 | 0.77 | 0.96 | 0.98 | 0.00 |
| **3** | 0.38 | 0.25 | 0.43 | · | 0.98 | 0.77 | 0.91 | 0.96 | 0.00 |
| **4** | 0.67 | 0.31 | 0.06 | 0.47 | · | 0.81 | 0.97 | 0.98 | 0.00 |
| **5** | 0.33 | 0.50 | 0.53 | 0.44 | 0.56 | · | 0.88 | 0.79 | 0.00 |
| **6** | 0.85 | 0.62 | 0.56 | 0.74 | 0.53 | 0.79 | · | 0.95 | 0.00 |
| **7** | 0.29 | 0.46 | 0.57 | 0.39 | 0.60 | 0.43 | 0.78 | · | 0.00 |
| **8** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | · |

#### fame

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Intro | 0-17 | 17 | 0 | 0.00 | -87.2 | -18.8 | Fmx2 Cm+Fm Bbx2 Fx12 |
| 1 | Verse 1 | 17-29 | 12 | 1 | 1.00 | -20.5 | -16.1 | Fx8 Bbx2 Fx2 |
| 2 | Instrumental 1 | 29-35 | 6 | 1 | 0.00 | -81.1 | -17.2 | Fx6 |
| 3 | Verse 2 | 35-47 | 12 | 1 | 1.00 | -19.7 | -16.4 | Fx8 Bbx2 Fx2 |
| 4 | Instrumental 2 | 47-61 | 14 | 3 | 0.00 | -87.9 | -18.0 | Fx6 Cm+Fm Bb+Cm Bb Bb+F Fx4 |
| 5 | Chorus | 61-71 | 10 | 0 | 0.90 | -27.1 | -17.2 | Fx10 |
| 6 | Verse 3 | 71-81 | 10 | 4 | 1.00 | -20.4 | -16.5 | Fx5 Bb+F Bb Bb+F Fx2 |
| 7 | Instrumental 3 | 81-85 | 4 | 1 | 0.00 | -67.0 | -18.3 | Fx4 |
| 8 | Verse 4 | 85-101 | 16 | 1 | 0.50 | -32.3 | -23.3 | Fx15 N |

fame: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.43 | 0.17 | 0.43 | 0.09 | 0.17 | 0.10 | 0.17 | 0.14 |
| **1** | 0.17 | · | 0.25 | 1.00 | 0.11 | 0.25 | 0.12 | 0.25 | 0.20 |
| **2** | 0.00 | 0.00 | · | 0.25 | 0.17 | 1.00 | 0.20 | 1.00 | 0.50 |
| **3** | 0.17 | 0.00 | 0.00 | · | 0.11 | 0.25 | 0.12 | 0.25 | 0.20 |
| **4** | 0.32 | 0.21 | 0.00 | 0.21 | · | 0.17 | 0.38 | 0.17 | 0.14 |
| **5** | 0.00 | 0.20 | 0.00 | 0.20 | 0.35 | · | 0.20 | 1.00 | 0.50 |
| **6** | 0.20 | 0.10 | 0.08 | 0.10 | 0.17 | 0.20 | · | 0.20 | 0.17 |
| **7** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | · | 0.50 |
| **8** | 0.25 | 0.17 | 0.00 | 0.17 | 0.25 | 0.00 | 0.20 | 0.00 | · |

fame: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.97 | 0.95 | 0.97 | 0.98 | 0.95 | 0.96 | 0.95 | 0.95 |
| **1** | 0.38 | · | 0.98 | 1.00 | 0.98 | 0.98 | 0.99 | 0.98 | 0.98 |
| **2** | 0.62 | 0.45 | · | 0.98 | 0.95 | 1.00 | 0.95 | 1.00 | 1.00 |
| **3** | 0.38 | 0.00 | 0.45 | · | 0.98 | 0.98 | 0.99 | 0.98 | 0.98 |
| **4** | 0.47 | 0.32 | 0.54 | 0.32 | · | 0.95 | 0.98 | 0.95 | 0.95 |
| **5** | 0.38 | 0.17 | 0.33 | 0.17 | 0.27 | · | 0.95 | 1.00 | 1.00 |
| **6** | 0.50 | 0.18 | 0.33 | 0.18 | 0.28 | 0.20 | · | 0.95 | 0.95 |
| **7** | 0.75 | 0.64 | 0.20 | 0.64 | 0.69 | 0.56 | 0.56 | · | 1.00 |
| **8** | 0.31 | 0.33 | 0.60 | 0.33 | 0.30 | 0.33 | 0.47 | 0.73 | · |

#### all-fired-up

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Intro | 0-28 | 28 | 2 | 0.00 | -89.9 | -19.9 | Amx13 Gx8 Emx2 Dx2 Gx3 |
| 1 | Verse 1 | 28-33 | 5 | 1 | 1.00 | -23.2 | -15.4 | Gx5 |
| 2 | Verse 2 | 33-49 | 16 | 3 | 1.00 | -20.4 | -15.4 | Emx2 Dx2 Gx4 Emx2 Dx2 Gx4 |
| 3 | Chorus 1 | 49-55 | 6 | 0 | 0.67 | -21.8 | -15.4 | Emx2 Dx2 Gx2 |
| 4 | Verse 3 | 55-61 | 6 | 1 | 0.83 | -23.7 | -16.0 | Gx6 |
| 5 | Verse 4 | 61-90 | 29 | 3 | 0.97 | -18.6 | -14.8 | Emx2 Dx2 Gx4 Emx2 Dx2 Gx4 Emx2 Dx2 Gx4 Emx2 Dx3 |
| 6 | Verse 5 | 90-97 | 7 | 1 | 0.57 | -27.2 | -16.9 | D+G Gx6 |
| 7 | Verse 6 | 97-104 | 7 | 4 | 1.00 | -20.3 | -16.6 | Em+G Em D+G Gx2 Emx2 |
| 8 | Verse 7 | 104-110 | 6 | 3 | 1.00 | -19.1 | -16.4 | Dx2 Gx4 |
| 9 | Chorus 2 | 110-124 | 14 | 0 | 1.00 | -17.8 | -14.3 | Emx2 D+Em D Nx2 Gx4 Emx2 Dx2 |
| 10 | Verse 8 | 124-128 | 4 | 3 | 1.00 | -16.8 | -13.5 | Gx4 |
| 11 | Chorus 3 | 128-132 | 4 | 0 | 1.00 | -16.6 | -13.7 | Emx2 Dx2 |
| 12 | Outro | 132-156 | 24 | 0 | 0.00 | -81.7 | -15.5 | Gx4 Emx2 Dx2 Gx4 Emx2 Dx2 Gx8 |

all-fired-up: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.12 | 0.75 | 0.62 | 0.12 | 0.75 | 0.11 | 0.27 | 0.38 | 0.38 | 0.12 | 0.38 | 0.75 |
| **1** | 0.00 | · | 0.17 | 0.20 | 1.00 | 0.17 | 0.50 | 0.17 | 0.33 | 0.10 | 1.00 | 0.00 | 0.17 |
| **2** | 0.31 | 0.20 | · | 0.83 | 0.17 | 1.00 | 0.14 | 0.33 | 0.50 | 0.45 | 0.17 | 0.50 | 1.00 |
| **3** | 0.00 | 0.60 | 0.00 | · | 0.20 | 0.83 | 0.17 | 0.22 | 0.60 | 0.36 | 0.20 | 0.60 | 0.83 |
| **4** | 0.00 | 0.00 | 0.33 | 0.67 | · | 0.17 | 0.50 | 0.17 | 0.33 | 0.10 | 1.00 | 0.00 | 0.17 |
| **5** | 0.71 | 0.20 | 0.00 | 0.00 | 0.33 | · | 0.14 | 0.33 | 0.50 | 0.45 | 0.17 | 0.50 | 1.00 |
| **6** | 0.07 | 0.00 | 0.36 | 0.67 | 0.00 | 0.36 | · | 0.33 | 0.25 | 0.09 | 0.50 | 0.00 | 0.14 |
| **7** | 0.29 | 0.40 | 0.29 | 0.33 | 0.50 | 0.29 | 0.57 | · | 0.12 | 0.23 | 0.17 | 0.12 | 0.33 |
| **8** | 0.17 | 0.20 | 0.00 | 0.50 | 0.33 | 0.00 | 0.25 | 0.58 | · | 0.18 | 0.33 | 0.20 | 0.50 |
| **9** | 0.43 | 0.20 | 0.25 | 0.42 | 0.33 | 0.25 | 0.36 | 0.29 | 0.33 | · | 0.10 | 0.30 | 0.45 |
| **10** | 0.00 | 0.00 | 0.00 | 0.50 | 0.00 | 0.00 | 0.00 | 0.38 | 0.00 | 0.00 | · | 0.00 | 0.17 |
| **11** | 0.00 | 1.00 | 0.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.50 | 0.75 | 0.00 | 1.00 | · | 0.50 |
| **12** | 0.67 | 0.00 | 0.00 | 0.00 | 0.00 | 0.17 | 0.07 | 0.29 | 0.00 | 0.25 | 0.00 | 0.00 | · |

all-fired-up: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.64 | 0.61 | 0.50 | 0.64 | 0.57 | 0.65 | 0.54 | 0.62 | 0.48 | 0.64 | 0.16 | 0.66 |
| **1** | 0.81 | · | 0.82 | 0.58 | 1.00 | 0.71 | 0.99 | 0.70 | 0.89 | 0.53 | 1.00 | 0.00 | 0.94 |
| **2** | 0.63 | 0.67 | · | 0.94 | 0.82 | 0.98 | 0.87 | 0.92 | 0.91 | 0.92 | 0.82 | 0.58 | 0.96 |
| **3** | 0.78 | 0.60 | 0.60 | · | 0.58 | 0.98 | 0.65 | 0.90 | 0.77 | 0.99 | 0.58 | 0.82 | 0.82 |
| **4** | 0.78 | 0.00 | 0.60 | 0.67 | · | 0.71 | 0.99 | 0.70 | 0.89 | 0.53 | 1.00 | 0.00 | 0.94 |
| **5** | 0.66 | 0.82 | 0.43 | 0.79 | 0.79 | · | 0.77 | 0.91 | 0.87 | 0.97 | 0.71 | 0.71 | 0.90 |
| **6** | 0.76 | 0.17 | 0.57 | 0.67 | 0.00 | 0.77 | · | 0.71 | 0.95 | 0.60 | 0.99 | 0.10 | 0.97 |
| **7** | 0.81 | 0.57 | 0.62 | 0.57 | 0.57 | 0.79 | 0.57 | · | 0.70 | 0.92 | 0.70 | 0.62 | 0.86 |
| **8** | 0.85 | 0.20 | 0.60 | 0.50 | 0.33 | 0.79 | 0.33 | 0.58 | · | 0.71 | 0.89 | 0.32 | 0.95 |
| **9** | 0.70 | 0.69 | 0.41 | 0.61 | 0.69 | 0.59 | 0.65 | 0.57 | 0.58 | · | 0.53 | 0.84 | 0.78 |
| **10** | 0.85 | 0.00 | 0.73 | 0.60 | 0.20 | 0.86 | 0.33 | 0.57 | 0.20 | 0.69 | · | 0.00 | 0.94 |
| **11** | 0.85 | 1.00 | 0.73 | 0.33 | 1.00 | 0.86 | 1.00 | 0.71 | 0.83 | 0.69 | 1.00 | · | 0.33 |
| **12** | 0.71 | 0.78 | 0.30 | 0.74 | 0.74 | 0.29 | 0.72 | 0.74 | 0.74 | 0.59 | 0.83 | 0.83 | · |

#### need-you-tonight

| # | Printed | Bars | Len | Cluster | Vocal share | Vocal dB (median) | Mix dB | Bar triads (run-length) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 0 | Intro | 0-13 | 13 | 1 | 0.00 | -91.7 | -15.3 | Nx8 C C+Eb C C+Eb C |
| 1 | Verse 1 | 13-24 | 11 | 0 | 1.00 | -19.9 | -13.4 | F C F C F C F C F Cx2 |
| 2 | Chorus 1 | 24-31 | 7 | 1 | 1.00 | -20.5 | -13.6 | C C+Eb C C+Eb C C+Eb C |
| 3 | Verse 2 | 31-48 | 17 | 0 | 1.00 | -21.9 | -13.4 | F C F C F C+F F C F C F C F C F C Cm |
| 4 | Chorus 2 | 48-56 | 8 | 1 | 0.75 | -19.7 | -13.3 | Cm C+Eb C Eb+Gm C C+Eb C F |
| 5 | Verse 3 | 56-79 | 23 | 0 | 1.00 | -21.8 | -13.6 | C F C F C F C F C F C F C F C F C F C F C Fx2 |
| 6 | Outro | 79-86 | 7 | 2 | 1.00 | -18.6 | -13.9 | F C+Eb C F C Nx2 |

need-you-tonight: below the diagonal M2 (containment edit distance, 0 = same), above it M3 (bar-pair Jaccard, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.00 | 0.50 | 0.00 | 0.25 | 0.00 | 0.25 |
| **1** | 0.68 | · | 0.00 | 0.33 | 0.12 | 0.50 | 0.29 |
| **2** | 0.29 | 0.43 | · | 0.00 | 0.33 | 0.00 | 0.14 |
| **3** | 0.77 | 0.09 | 0.43 | · | 0.10 | 0.33 | 0.22 |
| **4** | 0.46 | 0.50 | 0.24 | 0.50 | · | 0.12 | 0.20 |
| **5** | 0.77 | 0.09 | 0.43 | 0.09 | 0.50 | · | 0.29 |
| **6** | 0.71 | 0.43 | 0.57 | 0.43 | 0.57 | 0.43 | · |

need-you-tonight: below the diagonal M1 (global edit distance with a one-bar shift, 0 = same), above it M4 (chord-bar histogram cosine, 1 = same)

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | · | 0.71 | 1.00 | 0.61 | 0.95 | 0.63 | 0.84 |
| **1** | 0.75 | · | 0.71 | 0.99 | 0.74 | 0.99 | 0.96 |
| **2** | 0.58 | 0.50 | · | 0.61 | 0.95 | 0.62 | 0.84 |
| **3** | 0.76 | 0.31 | 0.66 | · | 0.68 | 1.00 | 0.93 |
| **4** | 0.72 | 0.59 | 0.33 | 0.69 | · | 0.68 | 0.88 |
| **5** | 0.82 | 0.50 | 0.75 | 0.30 | 0.77 | · | 0.94 |
| **6** | 0.83 | 0.55 | 0.57 | 0.72 | 0.62 | 0.80 | · |