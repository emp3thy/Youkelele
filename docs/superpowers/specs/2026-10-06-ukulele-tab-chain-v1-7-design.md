# Ukulele tab chain, version 1.7: an honest stroke row, a wider riff test, and bars that rest

Date: 2026-10-06. Amends the 1.6 spec (`2026-10-05-ukulele-tab-chain-v1-6-design.md`) in sections 3.1, 4.4, 5.1 and 7; everything not named here stays as 1.6 built it. Research for this version: `docs/superpowers/research/2026-10-06-v1-7/` (the strokes spike, the riff-test spike, the two-part split spike, the rests spike, the AC/DC ear truth) and the 1.6 listening pass at the end of `2026-10-05-v1-6-validation.md`.

## 1. Goal and scope

The 1.6 listening pass verified the riff path (Need You Tonight's verse tab is the riff, notes and rhythm) and refuted the strum side: nine of fourteen changed patterns were wrong, sustain lines overstated four of six held strokes, the riff test missed riffs on one or two pitches and riffs over a strum, and a section with no guitar in it printed a damped pattern. Four spikes then measured what can be fixed from the audio and what cannot.

Version 1.7 therefore:

- **Stops drawing what cannot be measured.** No sustain lines: stroke length cannot be read from the stem's energy (the strokes spike, section 2 here). The ring measurement stays in the data for evaluate.
- **Widens the riff test** with a lower pitch-change floor, recovering two riffs on one or two pitches, and labels a riff member inside a merged section where it starts. A second, chroma-free rule was measured and dropped (4.2).
- **Rests bars with no strummed instrument**, per bar, so near-silent song openings and a bell in the stem print chords without invented strokes.
- **Prints two-part sections honestly.** Where a riff or solo sits over a strum, the strokes follow the higher part (two-part spike), and the header says "riff heard, not transcribed" when the test fires. Separating the two parts is 1.8's research question (section 6).
- **Records what the detector cannot do** rather than tuning it: weak strokes and fast runs are missed, and a stem that carries two guitars prints the higher one.

Out of scope: lyrics (1.8; spike in `research/2026-10-05-v1-6/lyrics.md`); splitting two guitar parts (1.8; `two-part-split.md`); any change to chords, beats, bars, onsets, the recall gate, the section plan, the vote, the chance test or the tab gate.

Package version 0.8.0. Schema version stays 2; every new field defaults so 1.6 files load.

**Generality (owner's rule, 2026-10-04).** The validation songs are where patterns are learnt, never what the program is built for. No code path, constant or test may depend on which song is processed; every constant sits inside a band measured across every available section, and the constants whose band rests on one or two examples are named in section 9: the pitch-change floor (A1), Rule B's root band (A2), the rest rule's two thresholds (A4, A5), and the unheard flags (A3).

## 2. What listening and the spikes established on 2026-10-06

| Fact | Source | Consequence here |
|---|---|---|
| On eleven ear-judged bars, "cut" and "rings" overlap completely on every decay statistic (fall to 10 or 20 dB as a share of the gap, any band); the best honest rule scores 8 of 11, the same as drawing no line; the ear truth contradicts itself on one bar. | strokes spike, section 1 | Sustain lines removed (3.1). |
| Summer of '69's over-dense sections have onsets one eighth slot apart, no double triggers, no decay retriggers, and look like the ear-passed section in every measure; no filter reaches the ear's density without changing ear-passed patterns. | strokes spike, section 2 | Density is not tuned; the two-guitar limitation is stated (6). |
| The detector under-fires: Need You Tonight's chorus run loses 7 of 36 fast notes below the default threshold; The Cars 72-76's weak strokes sit below it; raising sensitivity breaks other sections. | strokes spike, section 3 | Recorded as a limitation (6). |
| Lowering the pitch-change floor to 0.26 recovers All Fired Up 61-90 (0.289) and Day Tripper 52-58 (0.292); the strum nearest below is All Fired Up 55-61 at 0.238. | riff-test spike | Rule A (4.1). |
| Day Tripper's intro and Summer of '69's outro are riffs whose chroma entropy (0.86, 0.90) fails the gate; a chroma-free rule on pitch change, root share and named share catches them on nine songs, but on AC/DC it flags a plain strum (pitch change 0.65, root share 0.31) and misses three riffs over chords. | riff-test spike and its AC/DC check | The rule is dropped (4.2); the two riffs stay known misses (6). |
| No measured feature flags a riff over a strum across songs; the one splitter that separates AC/DC's four two-part sections needs a note detector the install cannot carry and is fitted to that song; the mixed pattern equals the high band's pattern nearly everywhere. | two-part spike | Two-part sections print the mixed strokes as the riff's rhythm (3.4); the split waits (6). |
| Chelsea Dagger's intro is ten near-silent bars, a bell at MIDI 75 to 105, then seven bars of real power chords; a section-level cut cannot separate it from intros where the guitar enters late. | riff-test spike | The rest rule is per bar (5). |
| A bar holds a strummed instrument when its guitar/mix energy is at least 0.05 and its energy share below 330 Hz is at least 0.005; band 0.001 to 0.04; 49 near-silent bars and the bell bars rest, no ear-verified bar does. | rests spike | Rule and constants (5). |
| AC/DC: four of six sections are a riff or solo over chords; the intro's mixed clicks fit the riff; no section was flagged. | AC/DC ear truth | AC/DC joins the known set (8); the honest two-part print (3.4). |

## 3. The page

Everything about the 1.6 bar box stands except these four points.

### 3.1 No sustain lines

The stroke row shows down, up and muted arrows; an empty slot shows nothing. The `rings` flags stay in `strums.json` and `score.json` (6) but the renderer ignores them. The legend and header phrases are unchanged.

### 3.2 A label on an embedded riff member

When a member of a merged section is a riff by section 4 and the section's state phrase does not already begin with "riff", the member's first bar carries a label in the chord row, in the muted grey of the N.C. mark and the same size as a chord name: "riff" when the member's tab printed, else "riff heard". One label per member, on its first bar only, left of the first chord name or in its place when the bar has no chord. The section header is unchanged by this: it still follows the longest member (1.6 spec 4.3). The label rule takes precedence over 8's list of expected labels: a riff member whose section header comes to say riff (because the longest member is flagged too) carries no label, as All Fired Up 97-104 does once 61-90 is flagged (amended after validation, 2026-10-06). The label is wider than an eight-bar line's box, so a line holding a labelled bar prints four bars wide and never folds into an unlabelled line (validation fix round).

### 3.3 Bars that rest

A bar that fails the rest rule (5) prints its chord row as usual and an empty stroke row, in full black, not grey: nothing was guessed. A section every bar of which rests prints the existing phrase "no strummed instrument detected"; a section with some resting bars prints its header from the bars that hold.

### 3.4 Two-part sections

Where a riff or solo plays over a strum in one stem, the detected onsets follow the higher part, so the stroke row is the riff's rhythm. When the riff test fires the header says "riff heard, not transcribed" (or "riff" with tab); the strokes are not altered. The README's limitation line says so (6).

## 4. The riff test

A section or member is a riff when Rule A fires. It reads the detector's own onsets before the recall gate, as 1.6 does, and the named pitches from the 1.6 pitch stage.

### 4.1 Rule A: the 1.6 test with a lower floor

`riff_entropy <= RIFF_ENTROPY_MAX` (0.82) and `riff_single_share >= RIFF_SINGLE_PC_MIN` (0.45), unchanged, and `pitch_change_share >= PITCH_CHANGE_MIN` with `PITCH_CHANGE_MIN = 0.26` (was 0.40). The band is 0.24 to 0.29: the recovered riffs sit at 0.289 and 0.292, the nearest strum below at 0.238 (A1).

### 4.2 A chroma-free rule, considered and dropped

The riff-test spike proposed a second rule for riffs whose chroma entropy fails the gate (Day Tripper's intro, Summer of '69's outro): pitch-change share at least 0.55, share of named pitches on the chord root at most 0.40, named share at least 0.50. On the nine songs it measured, it caught both and added eleven unheard flags. On the tenth song, AC/DC, it fires on a plain strum (verse 43-57: pitch change 0.65, root share 0.31) and misses all three riff-over-chords sections (root shares 0.46 to 0.49), while the two features overlap between its strums and its riffs. A rule with a measured false positive on the first new song fails the generality rule, so it is not adopted. Day Tripper's intro and Summer of '69's outro remain known misses (6), and the rule's figures stay in `riff-test.md` as 1.8's lead. `root_share` and `named_share` are still computed and written (7) so the next version can measure further without re-running.

### 4.3 Expected flag changes on the known songs

Rule A adds four flags: All Fired Up 61-90 and Day Tripper 52-58 (both riffs by ear), Summer of '69 0-4 (a picked riff by ear) and The Cars 0-11 (a hook of palm-muted power chords, which the owner counts as a riff; the chain's test sees two pitch classes). No 1.6 flag is removed. On AC/DC no section passes the chroma gate (entropy 0.84 to 0.95, single share at most 0.39), so none is flagged; its four riff-over-chords sections print as strums, which the validation records against its ear truth. Every changed flag gets an ear clip (A3).

Amended after validation (2026-10-06): the rest rule (5) also moves the riff features, because a resting bar's onsets leave them. On the ten songs this added a fifth flag the spike could not predict (it measured every bar): Pour Some Sugar On Me 67-77, whose single share rises from 0.426 to 0.468 once bars 67 and 68 rest. So Rule A plus the rest rule add five flags, not four; the published tab for that passage shows chords, and the owner's ear decides it. AC/DC's lowest entropy measured 0.835.

### 4.4 What does not change

The reduction, the gate (`RIFF_AGREE_MIN` 0.70, `RIFF_SUPPORT_MIN` 0.75, `RIFF_NAMED_MIN` 0.6) and the tab mapping. A newly flagged section prints tab only if its own line passes the gate; otherwise it prints "riff heard, not transcribed" over its strokes. A riff member of a merged section prints its own pattern as 1.6 amended (1.6 spec 4.3) and now carries the 3.2 label.

## 5. Bars that rest

Per bar, on the stage's source stem, before the member vote:

- `energy_ratio`: the bar's stem RMS over the bar's mix RMS, as `section_has_instrument` computes it per section today; the bar holds only if `energy_ratio >= REST_RATIO_MIN` (0.05).
- `low_share`: the share of the bar's STFT power (n_fft 2048, hop 512, at 22 050 Hz) below 330 Hz; the bar holds only if `low_share >= REST_LOW_SHARE_MIN` (0.005).

A bar that fails either test rests: it is left out of its member's bars for the vote, the chance test, the riff features and the ring measurement, and prints as 3.3. A member every bar of which rests is a silent member (1.6 spec 4.3, rule 7).

How the stage applies it (amended from the implementation rulings, 2026-10-06):

- A bar shorter than one STFT frame (2 048 samples at 22 050 Hz, a fast song's pickup) is zero-padded to one frame before the low-share measurement; an all-zero slice has low share 0.
- Each member keeps its *holding* bars in order; the vote, the alignment to the section's pattern and the member figures read that list, so the vote pairs bars by their position in it. The sheet prints each bar's cell by absolute parity counted from the member's first holding bar, which is the musical truth. An odd-length run of resting bars inside a two-bar member therefore puts the vote's figures on a mixed phase, which can only lower its confidence and grey it, never move the printed phase; on short members it defeats the two-bar rule and the vote falls to one bar. No such member occurred on the ten songs.
- Because the vote reads only holding bars, the holding bars' own pattern changes wherever resting bars used to vote (they held noise or nothing): on the ten songs 54 holding bars in seven members printed a new row, and two intros and one instrumental flipped from uncertain to certain. A7 is reworded accordingly.
- The per-bar rule runs only inside sections that pass the section-level `section_has_instrument` cut, as the last sentence says; a member silent through that cut carries `rests` False on every bar (its figures are still recorded), while a member silent because no bar holds carries `rests` True on every bar and keeps `uncertain` True, the 1.6 meaning of a silent member. A resting bar inside a holding member is `uncertain` False: nothing was guessed.
- The riff stage still reads a riff member's resting bars as empty note bars when it reduces and gates the riff; the score builder prints no tab on a resting bar. Leaving resting bars out of the reduction is a 1.8 item; no song in the ten hit it. Bands: the ratio floor is pinned from below by Need You Tonight's verified tab bars at 0.069 to 0.09 (A4); the low-share band is 0.001 to 0.04, with the bell bars at 0.0002 to 0.0006 and the lowest ear-verified bar at 0.040, a decaying tail at a section's end (A5). Expected on the ten songs: 51 bars rest, nearly all song openings and tails (Need You Tonight 0-7 and 84-85; Wet Leg 18-25 and 109-112; Pour Some Sugar On Me 0, 7-10, 15-18, 66-68, 77-79; Chelsea Dagger 0-6, 10, 11; single bars in All Fired Up, Summer of '69, Day Tripper and The Cars). The existing section-level `section_has_instrument` rule stays as the first cut; the per-bar rule runs inside sections that pass it.

## 6. Recorded, not changed

- **Rings.** `stroke_decay_db`, `section_rings` and the `rings` fields stay and are still computed and written; the renderer ignores them. The per-song muted-versus-ringing verdict was right on four of five short clips and may serve later; the per-stroke claim it drew was wrong on four of six and is withdrawn.
- **Under-firing.** The onset detector misses strokes whose envelope peak is below librosa's default threshold (weak strokes, fast sixteenth runs). Raising sensitivity re-normalises the envelope and changes ear-passed sections, so no change is made. The README's limitations gain: "Quiet strokes and very fast runs can be missed, so a dense passage may print sparser than it is played."
- **Riffs the test still misses.** Day Tripper's intro and Summer of '69's outro (chroma entropy above the ceiling) and AC/DC's three riffs over chords (no feature separates them from its strums) print as strums. The validation record lists them; the README's limitation says a riff that sounds chord-like to the chain prints as a strum.
- **Two guitars in one stem.** The strokes follow the higher part. The README's two-guitar line becomes: "When two guitars share one stem, the printed strokes follow the higher one, and their notes interleave, so the riff stage finds no steady line and prints the riff as heard, not transcribed." The two-part split spike's measured leads (a polyphonic note split at MIDI 60 separates AC/DC's two-part sections; the high band's pitch-change share minus the low band's catches Day Tripper's verse) are 1.8's starting point.
- **Chords, beats, bars, onsets, the recall gate, the section plan, the vote and its constants, the chance test, the tab gate**: unchanged. Chords and bars must be byte-identical to 1.6 on every re-run song.

## 7. Data formats, stages, compatibility, tooling

- **strums.json** (schema 2): `BarStrums` gains `rests: bool = False`, `energy_ratio: float | None = None`, `low_share: float | None = None`; `SectionPattern` gains `root_share: float | None = None`, `named_share: float | None = None`, `riff_rule: Literal["A", "B"] | None = None`. `bar_onsets` is unchanged (written from all bars, resting ones included, so the regression line holds).
- **score.json** (schema 2): `ScoreBar` gains `label: str = ""` and `rests: bool = False`. A resting bar has empty `strokes`, `grey` False, `tab` None.
- **Stages.** `stages/strums.py`: the rest rule in a new `music/rests.py` (`bar_energy_ratio`, `bar_low_share`, `bar_holds`, `resample_for_rests`), applied per member before the vote; `music/riff.py` gains `chord_roots`, `root_share` and `named_share` (computed and written for the next version's measurement, not used in the test); `PITCH_CHANGE_MIN` moves to 0.26 in `music/pitch.py`; `riff_rule` is "A" when the flag is set. So that the shares cover every section, the pitch tracker runs once on every song with a voiced member and names the onsets of every voiced member (amended 2026-10-06; it adds 18 to 25 s to the strums stage on a song that had no riff candidate, and the riff stage runs it again on riff songs, a 1.8 item). The riff stage is unchanged. The score builder sets `rests` and `label`, prints `grey` only on an uncertain bar that neither rests nor carries tab, and prints no tab on a resting bar. The renderer drops the sustain drawing (`bar_svg` loses `rings` handling, in the tab block too; the faint rest dots stay) and draws the label.
- **evaluate and compare.** Per section: `riff_rule`, `root_share`, `named_share`; per bar: rests; compare counts bars whose rest state changed and sections whose flag changed, with the rule.
- **Compatibility.** 1.6 files load with the defaults; a 1.6 `score.json` renders without sustain lines and without labels. No new dependency: STFT and RMS are librosa and numpy.
- **Version** 0.8.0; README stage table, limitations (6) and history; the sample sheet regenerated.

## 8. Validation

Ten known songs (the 1.6 eight, Day Tripper, AC/DC) re-run from the strums stage; `grid.json`, the chord events and `bar_onsets` byte-identical to 1.6 (AC/DC and Day Tripper to their 1.6 runs). One blind song chosen by the owner, run from ingest.

Expectations written before the run:

1. Byte identity as above on all ten songs.
2. No sustain line on any sheet; the stroke rows of the eight 1.6 songs otherwise unchanged except in members that contain a resting bar (whose vote reads fewer bars; amended 2026-10-06, see 5), and no pattern the 1.6 listening pass accepted changes.
3. Riff flags change as 4.3 lists (four added by Rule A, none removed, plus any flag the rest rule moves, which on these runs was Pour Some Sugar On Me 67-77); AC/DC gains none, and its sections are recorded against its ear truth (intro, 34-43, 74-90, 90-113 riffs over chords; 16-34, 43-57 strums).
4. The 51 bars of section 5 rest and no bar of an ear-verified section rests; Chelsea Dagger's intro prints chords with empty strokes on bars 0-6, 10 and 11 and power-chord strokes from bar 13.
5. The label appears on the first bar of every riff member whose section header does not say riff, and nowhere else; on these runs that is Wet Leg 58-65 only, since All Fired Up's Verse 2 header says riff once 61-90 is flagged (3.2 governs; amended 2026-10-06).
6. Tab prints on Need You Tonight's verse as before; any newly flagged section that passes the gate is recorded, with its tab clip.
7. Pages recorded against 1.6 (no sustain lines and empty rows do not change height).
8. The blind song runs to a sheet with exit 0; its figures recorded, not judged.

**Ground truth from published sources first.** For every section whose flag changes, every resting stretch of more than two bars, and every AC/DC and blind-song section, the validation looks up what published guitar lessons and tab transcriptions say the part is (single-note riff, power-chord hook, strummed chords, no guitar, two guitars), records the source and its description in the validation record, and compares the chain's output to it. The owner's ear is asked only where sources disagree, say nothing, or contradict the chain (owner's instruction, 2026-10-06). No lyrics are copied.

Ear clips, for those cases: clicks on the printed strokes, a pluck clip for any tab, the stem alone for a resting stretch; AC/DC's six sections re-cut on the 1.7 output. The listening pass remains the acceptance test; a flag the sources or the ear reject is recorded, not tuned.

## 9. Assumptions

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | `PITCH_CHANGE_MIN` 0.26 separates riffs from strums | Measured on 68 sections; band 0.24 to 0.29 **rests on one strum below** (All Fired Up 55-61, ear "mostly fits") and two riffs above | A dense strum gains a riff flag, or a one-pitch riff is still missed; the gate still decides what prints |
| A2 | A chroma-free riff rule can be made general | **Refuted on the tenth song** (AC/DC verse 43-57 false positive; three riffs over chords missed); dropped from this version | Day Tripper's intro and Summer of '69's outro stay unflagged and print as strums |
| A3 | The two new flags Rule A adds are riffs | **Verified by the owner** (research `assumption-clips.md`): Summer of '69 0-4 is a picked single-note riff; The Cars 0-11 is a hook of staccato palm-muted power chords, a riff to the owner though chordal to the chain | None on these two; the chordal case shows the test can flag a two-note power-chord hook, which prints only the phrase |
| A4 | `REST_RATIO_MIN` 0.05 | **Pinned by one song**: Need You Tonight's verified tab bars at 0.069 to 0.09 | Quiet real bars rest, losing their strokes; or near-silent bars print invented strokes |
| A5 | `REST_LOW_SHARE_MIN` 0.005 marks a bar as outside a guitar's register | Measured on all bars of ten songs; band 0.001 to 0.04; the lowest verified bar is a decaying tail | A loud high-register bar rests (Day Tripper bar 1 at the looser 0.01); depends on the stem holding content below 330 Hz |
| A6 | Chelsea Dagger bars 13-19 hold a real guitar | **Verified by the owner** ("those are power chords"); measured at ratio 0.23 to 0.31 | None |
| A7 | Resting bars leave the vote; the holding bars' pattern changes wherever resting bars used to vote | **Reworded after validation**: the earlier wording ("do not change the vote on the bars that hold, by construction") confused "resting bars contribute nothing" with "holding bars print as before"; on the ten songs 54 holding bars in seven members printed a new row and three sections flipped from uncertain to certain | A member with few holding bars prints a thinner-evidence pattern; a changed row the ear rejects is recorded, not tuned |
| A8 | Removing sustain lines loses nothing the ear wanted | Verified: 4 of 6 held clips contradicted the lines | None |
| A9 | The mixed strokes on a two-part section are the riff's rhythm | Measured (mixed equals the high band's pattern in nearly every section) and heard on AC/DC's intro | A strummer reads the riff's rhythm as a strum; the header phrase says so |
| A10 | No ear-passed pattern changes | By construction (vote, onsets and gate untouched) except where a bar rests; validation lists every changed row | A regression the ear would catch |
| A11 | 1.6 files render under the new page | Loader defaults; unverified until built | Old folders re-run from strums; cheap |
