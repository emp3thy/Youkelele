# Ukulele tab chain, version 1.7: an honest stroke row, a wider riff test, and bars that rest

Date: 2026-10-06. Amends the 1.6 spec (`2026-10-05-ukulele-tab-chain-v1-6-design.md`) in sections 3.1, 4.4, 5.1 and 7; everything not named here stays as 1.6 built it. Research for this version: `docs/superpowers/research/2026-10-06-v1-7/` (the strokes spike, the riff-test spike, the two-part split spike, the rests spike, the AC/DC ear truth) and the 1.6 listening pass at the end of `2026-10-05-v1-6-validation.md`.

## 1. Goal and scope

The 1.6 listening pass verified the riff path (Need You Tonight's verse tab is the riff, notes and rhythm) and refuted the strum side: nine of fourteen changed patterns were wrong, sustain lines overstated four of six held strokes, the riff test missed riffs on one or two pitches and riffs over a strum, and a section with no guitar in it printed a damped pattern. Four spikes then measured what can be fixed from the audio and what cannot.

Version 1.7 therefore:

- **Stops drawing what cannot be measured.** No sustain lines: stroke length cannot be read from the stem's energy (the strokes spike, section 2 here). The ring measurement stays in the data for evaluate.
- **Widens the riff test** with a lower pitch-change floor and a second, chroma-free rule, recovering riffs on one or two pitches, and labels a riff member inside a merged section where it starts.
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
| Day Tripper's intro and Summer of '69's outro are riffs whose chroma entropy (0.86, 0.90) fails the gate; a chroma-free rule on pitch change (0.78, 0.60), root share (0.35, 0.11) and named share catches them; the strums sit at root share 0.86 to 0.95. | riff-test spike | Rule B (4.2). |
| No measured feature flags a riff over a strum across songs; the one splitter that separates AC/DC's four two-part sections needs a note detector the install cannot carry and is fitted to that song; the mixed pattern equals the high band's pattern nearly everywhere. | two-part spike | Two-part sections print the mixed strokes as the riff's rhythm (3.4); the split waits (6). |
| Chelsea Dagger's intro is ten near-silent bars, a bell at MIDI 75 to 105, then seven bars of real power chords; a section-level cut cannot separate it from intros where the guitar enters late. | riff-test spike | The rest rule is per bar (5). |
| A bar holds a strummed instrument when its guitar/mix energy is at least 0.05 and its energy share below 330 Hz is at least 0.005; band 0.001 to 0.04; 49 near-silent bars and the bell bars rest, no ear-verified bar does. | rests spike | Rule and constants (5). |
| AC/DC: four of six sections are a riff or solo over chords; the intro's mixed clicks fit the riff; no section was flagged. | AC/DC ear truth | AC/DC joins the known set (8); the honest two-part print (3.4). |

## 3. The page

Everything about the 1.6 bar box stands except these four points.

### 3.1 No sustain lines

The stroke row shows down, up and muted arrows; an empty slot shows nothing. The `rings` flags stay in `strums.json` and `score.json` (6) but the renderer ignores them. The legend and header phrases are unchanged.

### 3.2 A label on an embedded riff member

When a member of a merged section is a riff by section 4 and the section's state phrase does not already begin with "riff", the member's first bar carries a label in the chord row, in the muted grey of the N.C. mark and the same size as a chord name: "riff" when the member's tab printed, else "riff heard". One label per member, on its first bar only, left of the first chord name or in its place when the bar has no chord. The section header is unchanged by this: it still follows the longest member (1.6 spec 4.3).

### 3.3 Bars that rest

A bar that fails the rest rule (5) prints its chord row as usual and an empty stroke row, in full black, not grey: nothing was guessed. A section every bar of which rests prints the existing phrase "no strummed instrument detected"; a section with some resting bars prints its header from the bars that hold.

### 3.4 Two-part sections

Where a riff or solo plays over a strum in one stem, the detected onsets follow the higher part, so the stroke row is the riff's rhythm. When the riff test fires the header says "riff heard, not transcribed" (or "riff" with tab); the strokes are not altered. The README's limitation line says so (6).

## 4. The riff test

A section or member is a riff when Rule A or Rule B fires. Both read the detector's own onsets before the recall gate, as 1.6 does, and the named pitches from the 1.6 pitch stage.

### 4.1 Rule A: the 1.6 test with a lower floor

`riff_entropy <= RIFF_ENTROPY_MAX` (0.82) and `riff_single_share >= RIFF_SINGLE_PC_MIN` (0.45), unchanged, and `pitch_change_share >= PITCH_CHANGE_MIN` with `PITCH_CHANGE_MIN = 0.26` (was 0.40). The band is 0.24 to 0.29: the recovered riffs sit at 0.289 and 0.292, the nearest strum below at 0.238 (A1).

### 4.2 Rule B: chroma-free

`pitch_change_share >= RIFF_B_PITCH_CHANGE` (0.55), `root_share <= RIFF_B_ROOT_MAX` (0.40) and `named_share >= RIFF_B_NAMED_MIN` (0.50), where `root_share` is the share of named onsets whose pitch class equals the root of the chord event covering the onset (from `chords.json`; N.C. onsets count as not on the root) and `named_share` is the share of onsets the tracker named. Bands: pitch change 0.55 to 0.60 (the riffs it must catch sit at 0.60 and 0.78; strummed sections elsewhere reach 0.3 to 0.7, which is why the root test is needed); root 0.36 to 0.41 (riffs 0.10 to 0.35, strums 0.86 to 0.95, All Fired Up 61-90 at 0.95 is caught by Rule A instead); named share is a floor (A2).

### 4.3 Expected flag changes on the known songs

Rule A adds four flags: All Fired Up 61-90 and Day Tripper 52-58 (both riffs by ear), Summer of '69 0-4 and The Cars 0-11 (unheard). Rule B adds eleven: Day Tripper 0-11 and Summer of '69 111-121 (riffs by ear), Day Tripper 11-15, 26-30, 30-35, 35-46, 46-52, 58-63, 63-68 and 78-95 (unheard; the riff runs through the song), Wet Leg 33-42 and The Cars 72-76 (unheard). No 1.6 flag is removed. AC/DC's flags are measured in validation (8). Every changed flag gets an ear clip (A3).

### 4.4 What does not change

The reduction, the gate (`RIFF_AGREE_MIN` 0.70, `RIFF_SUPPORT_MIN` 0.75, `RIFF_NAMED_MIN` 0.6) and the tab mapping. A newly flagged section prints tab only if its own line passes the gate; otherwise it prints "riff heard, not transcribed" over its strokes. A riff member of a merged section prints its own pattern as 1.6 amended (1.6 spec 4.3) and now carries the 3.2 label.

## 5. Bars that rest

Per bar, on the stage's source stem, before the member vote:

- `energy_ratio`: the bar's stem RMS over the bar's mix RMS, as `section_has_instrument` computes it per section today; the bar holds only if `energy_ratio >= REST_RATIO_MIN` (0.05).
- `low_share`: the share of the bar's STFT power (n_fft 2048, hop 512, at 22 050 Hz) below 330 Hz; the bar holds only if `low_share >= REST_LOW_SHARE_MIN` (0.005).

A bar that fails either test rests: it is left out of its member's bars for the vote, the chance test, the riff features and the ring measurement, and prints as 3.3. A member every bar of which rests is a silent member (1.6 spec 4.3, rule 7). Bands: the ratio floor is pinned from below by Need You Tonight's verified tab bars at 0.069 to 0.09 (A4); the low-share band is 0.001 to 0.04, with the bell bars at 0.0002 to 0.0006 and the lowest ear-verified bar at 0.040, a decaying tail at a section's end (A5). Expected on the ten songs: 51 bars rest, nearly all song openings and tails (Need You Tonight 0-7 and 84-85; Wet Leg 18-25 and 109-112; Pour Some Sugar On Me 0, 7-10, 15-18, 66-68, 77-79; Chelsea Dagger 0-6, 10, 11; single bars in All Fired Up, Summer of '69, Day Tripper and The Cars). The existing section-level `section_has_instrument` rule stays as the first cut; the per-bar rule runs inside sections that pass it.

## 6. Recorded, not changed

- **Rings.** `stroke_decay_db`, `section_rings` and the `rings` fields stay and are still computed and written; the renderer ignores them. The per-song muted-versus-ringing verdict was right on four of five short clips and may serve later; the per-stroke claim it drew was wrong on four of six and is withdrawn.
- **Under-firing.** The onset detector misses strokes whose envelope peak is below librosa's default threshold (weak strokes, fast sixteenth runs). Raising sensitivity re-normalises the envelope and changes ear-passed sections, so no change is made. The README's limitations gain: "Quiet strokes and very fast runs can be missed, so a dense passage may print sparser than it is played."
- **Two guitars in one stem.** The strokes follow the higher part. The README's two-guitar line becomes: "When two guitars share one stem, the printed strokes follow the higher one, and their notes interleave, so the riff stage finds no steady line and prints the riff as heard, not transcribed." The two-part split spike's measured leads (a polyphonic note split at MIDI 60 separates AC/DC's two-part sections; the high band's pitch-change share minus the low band's catches Day Tripper's verse) are 1.8's starting point.
- **Chords, beats, bars, onsets, the recall gate, the section plan, the vote and its constants, the chance test, the tab gate**: unchanged. Chords and bars must be byte-identical to 1.6 on every re-run song.

## 7. Data formats, stages, compatibility, tooling

- **strums.json** (schema 2): `BarStrums` gains `rests: bool = False`, `energy_ratio: float | None = None`, `low_share: float | None = None`; `SectionPattern` gains `root_share: float | None = None`, `named_share: float | None = None`, `riff_rule: Literal["A", "B"] | None = None`. `bar_onsets` is unchanged (written from all bars, resting ones included, so the regression line holds).
- **score.json** (schema 2): `ScoreBar` gains `label: str = ""` and `rests: bool = False`. A resting bar has empty `strokes`, `grey` False, `tab` None.
- **Stages.** `stages/strums.py`: the rest rule in a new `music/rests.py` (`bar_energy_ratio`, `bar_low_share`, `bar_holds`), applied per member before the vote; the riff test in `music/riff.py` gains `root_share` and `is_riff_b`, and `is_riff` becomes the disjunction with the rule recorded. The riff stage is unchanged. The score builder sets `rests` and `label`. The renderer drops the sustain drawing (`bar_svg` loses `rings` handling) and draws the label.
- **evaluate and compare.** Per section: `riff_rule`, `root_share`, `named_share`; per bar: rests; compare counts bars whose rest state changed and sections whose flag changed, with the rule.
- **Compatibility.** 1.6 files load with the defaults; a 1.6 `score.json` renders without sustain lines and without labels. No new dependency: STFT and RMS are librosa and numpy.
- **Version** 0.8.0; README stage table, limitations (6) and history; the sample sheet regenerated.

## 8. Validation

Ten known songs (the 1.6 eight, Day Tripper, AC/DC) re-run from the strums stage; `grid.json`, the chord events and `bar_onsets` byte-identical to 1.6 (AC/DC and Day Tripper to their 1.6 runs). One blind song chosen by the owner, run from ingest.

Expectations written before the run:

1. Byte identity as above on all ten songs.
2. No sustain line on any sheet; the stroke rows of the eight 1.6 songs otherwise unchanged except where bars rest.
3. Riff flags change exactly as 4.3 lists; AC/DC's flags per section recorded against its ear truth (intro, 34-43, 74-90, 90-113 riffs over chords; 16-34, 43-57 strums).
4. The 51 bars of section 5 rest and no bar of an ear-verified section rests; Chelsea Dagger's intro prints chords with empty strokes on bars 0-6, 10 and 11 and power-chord strokes from bar 13.
5. The label appears on the first bar of every riff member whose section header does not say riff (All Fired Up 97-104, Wet Leg 58-65, and any member newly flagged), and nowhere else.
6. Tab prints on Need You Tonight's verse as before; any newly flagged section that passes the gate is recorded, with its tab clip.
7. Pages recorded against 1.6 (no sustain lines and empty rows do not change height).
8. The blind song runs to a sheet with exit 0; its figures recorded, not judged.

Ear clips: every section whose riff flag changed (clicks on its printed strokes, plus a pluck clip for any tab); every resting stretch of more than two bars (the stem alone, to confirm silence or a bell); Chelsea Dagger bars 12 to 20 (unheard; the record's "no guitar" claim rests on bars 0 to 8); AC/DC's six sections re-cut on the 1.7 output. The listening pass is the acceptance test; a flag the ear rejects is recorded, not tuned.

## 9. Assumptions

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | `PITCH_CHANGE_MIN` 0.26 separates riffs from strums | Measured on 68 sections; band 0.24 to 0.29 **rests on one strum below** (All Fired Up 55-61, ear "mostly fits") and two riffs above | A dense strum gains a riff flag, or a one-pitch riff is still missed; the gate still decides what prints |
| A2 | Rule B's root band 0.36 to 0.41 and pitch-change floor 0.55 | Measured on nine sections; **root band 0.05 wide**; depends on chord labels being right | A strum on a wrong chord label gains a flag; a riff on the chord root is missed (All Fired Up 61-90 is caught by Rule A) |
| A3 | The unheard flags Rules A and B add are riffs | **Unverified**: Summer of '69 0-4, The Cars 0-11 and 72-76, Wet Leg 33-42, eight Day Tripper sections | A strum prints "riff heard" over its own strokes; the strokes themselves are unchanged, so the cost is a wrong phrase |
| A4 | `REST_RATIO_MIN` 0.05 | **Pinned by one song**: Need You Tonight's verified tab bars at 0.069 to 0.09 | Quiet real bars rest, losing their strokes; or near-silent bars print invented strokes |
| A5 | `REST_LOW_SHARE_MIN` 0.005 marks a bar as outside a guitar's register | Measured on all bars of ten songs; band 0.001 to 0.04; the lowest verified bar is a decaying tail | A loud high-register bar rests (Day Tripper bar 1 at the looser 0.01); depends on the stem holding content below 330 Hz |
| A6 | Chelsea Dagger bars 13-19 hold a real guitar | Measured (power chords at ratio 0.23 to 0.31); **unheard** by the owner, whose clip covered bars 0-8 | Those bars print strokes the ear would reject; the clip is in the validation pass |
| A7 | Resting bars do not change the vote on the bars that hold | By construction; the vote reads only holding bars | A member with few holding bars prints a thinner-evidence pattern |
| A8 | Removing sustain lines loses nothing the ear wanted | Verified: 4 of 6 held clips contradicted the lines | None |
| A9 | The mixed strokes on a two-part section are the riff's rhythm | Measured (mixed equals the high band's pattern in nearly every section) and heard on AC/DC's intro | A strummer reads the riff's rhythm as a strum; the header phrase says so |
| A10 | No ear-passed pattern changes | By construction (vote, onsets and gate untouched) except where a bar rests; validation lists every changed row | A regression the ear would catch |
| A11 | 1.6 files render under the new page | Loader defaults; unverified until built | Old folders re-run from strums; cheap |
