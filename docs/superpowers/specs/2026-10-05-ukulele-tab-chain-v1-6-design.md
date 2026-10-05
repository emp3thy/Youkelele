# Ukulele tab chain, version 1.6: every bar carries its strokes, and a riff prints as tab when it can be trusted

Date: 2026-10-05. Branch `worktree-v1-6`. Supersedes section 5 of the 1.5 spec (the page) and amends sections 3 (the plan) and 4 (strums) there. Everything not named here stays as 1.5 built it. Research for this version: `docs/superpowers/research/2026-10-05-v1-6/` (the 1.5 listening pass, the pattern-vote spike, the riff-pitch spike, the lyrics spike).

## 1. Goal and scope

The owner stated the two things the sheet is for: to see, for every bar, which chord goes with which strokes, as one thing; and to see how a riff is played, not just that one was heard. Reading the 1.5 sheet, the owner could not tell that a box was a bar, read the example strip as the section's opening bars, and lost the order of a verse to row folding. The 1.5 listening pass then found three things the data could not: a merged section printing one pattern over bars that play something else, the slot-wise pattern vote flattening syncopation into even strokes, and the riff marker flagging dense strumming as a riff.

Version 1.6 therefore:

- **Prints the sheet bar by bar.** One box per bar in song order, the chord above the stroke it starts on, the strokes inside the bar, held strokes drawn as held, the count once per line. No example strip, no row folding.
- **Chooses rhythm honestly.** A section's pattern is the majority vote unless a real bar represents the section clearly better, in which case that bar prints; a two-bar pattern is allowed when the bars pair; every stroke records whether it rings; a member of a merged section prints its own pattern when it differs from the section's; an uncertain pattern prints greyed instead of not at all.
- **Prints riff tab behind a gate.** A section heard as a riff gets its notes named at the trusted onsets, reduced to a one- or two-bar riff, mapped onto the ukulele, and printed as tab with the stroke row under it, but only when the riff repeats steadily enough to pass a gate set so that the one verified riff passes and the one verified wrong figure fails. Otherwise the section says "riff heard, not transcribed".
- **Tightens the riff test** with the pitch-change measure, which removes the two ear-confirmed false positives.

Out of scope, deferred to 1.7 with its spike recorded: lyrics under the bars. Out of scope for good reasons stated in section 5.6: separating two guitars in one stem.

Package version 0.7.0. Schema version 2 for `strums.json` and `score.json`; 1.3 to 1.5 files load with defaults.

**Generality (owner's rule, 2026-10-04).** The validation songs are where patterns and strategies are learnt, never what the program is built for. No code path, constant or test may depend on which song is being processed. Every rule below is stated so that it applies to any input, and every constant is set inside a band measured across every section available, with the sections that set the band named in section 9 so the owner can see where fitting these songs is closest to learning from them. In this version the thinnest bands are: the hybrid vote delta (A1), the member threshold (A4), the riff gate (A9 to A11), and the pitch-change band (A8). Unit tests use synthetic inputs or the measured numbers as examples of a rule, never as the rule. The blind song exists to catch a rule that only fits the known ones.

## 2. What listening and the spikes established on 2026-10-05

Fifteen ear clips from the 1.5 validation were judged by the owner, and three throwaway spikes ran on the kept run folders (research folder above). The design rests on these facts.

| Fact | Source | Consequence here |
|---|---|---|
| All Fired Up's merged Verse 2 prints `D-D-D-DU` over 55 bars; 61-90 and, with variation, 55-61 play it; 90-97 is sparse sustained strums; 97-104 is a riff with improvisation; 104-110 opens with improvisation. Verse 1's merge is right. | clips 1 to 7 | Members keep their own pattern when it differs (4.3). The merge rule itself stands. |
| 1.4's own patterns for All Fired Up 55-61 and Summer of '69 53-58 were wrong (both are syncopated eighths); All Fired Up Chorus 3 `D---DUD-` is right though flipped to uncertain. | clips 8 to 10 | The chance test stands; a four-bar section that flipped was the test lacking bars, and prints greyed, not blank (4.5). |
| The Cars: D major is home; Verse 1 is a strum though marked riff; Verse 3 is a riff; Chorus 3's `-UDUDUD-` is "the signature strum". | clips 11 to 15 | Second false positive of the riff marker on dense strumming (5.1). |
| The owner hears All Fired Up's Verse 2 figure as a riff ("d D D DUD"). | clip 7 | A pattern of single-note strokes is a riff in the owner's ear; the riff test must not depend on the strum pattern looking strum-like. |
| The slot-wise majority is an actual played bar in only 30 of 68 sections, inflates strike count (denser than the median bar in 47 of 68), and erases pushes (bars average 0.59 anticipations; the majority keeps 0.25). | pattern-vote spike | The hybrid vote (4.1). |
| A pure medoid is no better overall (better on 30, worse on 34) and breaks three ear-right patterns at delta 0; at delta 0.03 to 0.05 it fixes Summer of '69 53-58 and regresses nothing. The Cars 52-60 needs a mute tie-break. | pattern-vote spike | Constants in 4.1 and A1, A2. |
| On distorted stems a stroke rings until the next hit; what separates playing styles is the decay in the first slot after the peak. Per stroke it is too noisy to flag (9.6% of 2,114 strokes fall between 6 and 10 dB), but song medians separate: 1.8 to 2.7 dB per slot on six songs, 8.3 and 8.7 on the two played muted. | pattern-vote spike and assumption pass | The ring flag, decided per section (4.4). |
| Monophonic pitch tracking at the onsets names Need You Tonight's verse riff correctly (owner: "the tones are right") but its rhythm came out wrong when taken from the tracker's own segmentation; the strums stage's onsets on that section were "perfect" in two passes. | riff-pitch spike and ear check | Rhythm from the trusted onsets, pitch from the tracker (5.2). |
| The spike's medium-confidence Fame figure is "absolutely miles off"; it had passed the spike's provisional gate. | ear check | The gate sits above Fame's scores and is named as resting on one verified riff (5.4, A9). |
| Without a gate, strum sections produce a confident one-note "riff" (the power chord's root); the pitch-change share separates riffs (0.65 to 0.85) from strums (0.05 to 0.17). | riff-pitch spike | The riff test (5.1) and gate (5.4). |
| Four of six ear-confirmed riff sections yield no steady line (Fame intro, Need You Tonight intro, The Cars Verse 3, All Fired Up 97-104). | riff-pitch spike | "Riff heard, not transcribed" is the common case and must read well (3.3). |
| Lyrics from the vocals stem are feasible: words placed in the right bar 95% or more of the time, half a minute a song, wording rough on some songs. | lyrics spike | Deferred to 1.7; the lyric row is not drawn in 1.6. |

## 3. The page

### 3.1 Bars

The sheet is a sequence of bar boxes in song order, grouped under section headers. A line holds four bars. A line holds eight when every bar on it would hold at most one chord and the section's grid is eighths; the choice is per line, by that rule, never per song. Nothing is folded: a section of 55 bars prints 55 boxes. A repeat mark is allowed only when a whole line's bars are identical in chords, strokes and ring flags to the line before, and then the line prints once with "play twice" (or "three times") in words at its right edge; a bare multiplier never prints.

Inside a bar, top to bottom:

1. **Chord row.** The chord name sits over the slot it starts on. A bar with two chords shows both, each over its slot. The filled (italic) and passing conventions of 1.4 stay. A bar whose chord continues from the previous bar still prints its name: every bar is readable alone.
2. **Stroke row.** One cell per slot, eight or sixteen as the section's grid dictates. A down stroke is a down arrow, an up stroke an up arrow, a muted strike the arrow crossed, an empty slot nothing. A stroke whose ring flag is set and which is followed by one or more empty slots before the next stroke or the bar end is drawn with a sustain line through those slots, so a held strum reads as held. A stroke whose ring flag is clear draws no line.
3. **Count row**, once per line under the first bar only: `1 & 2 & 3 & 4 &` on an eighth grid, `1 e & a ...` on sixteenths.

A riff bar (3.4) adds a tab block between the chord row and the stroke row.

### 3.2 Section header

The section's display name (as 1.5 names them), then one state phrase in the smaller face, from this list and no other: nothing when the pattern is certain; "pattern uncertain" when the strokes are a greyed best guess (4.5); "riff" when tab prints; "riff heard, not transcribed" when the section is a riff that failed the gate; "no strummed instrument detected" as before. When the tab was shifted by an octave, the header adds "written an octave up" or "down".

### 3.3 Grey and the not-transcribed riff

An uncertain pattern prints in a mid grey (the same grey for arrows and sustain lines) with the chord row in full black, so the chords are never in doubt and the strokes read as a suggestion. A riff section that did not pass the gate prints exactly like a strummed section (its strokes are the riff's rhythm, which is still useful to a strummer) with the header phrase above; nothing else distinguishes it, by design: the owner asked that the sheet never pretend.

### 3.4 Riff bars

For a riff section that passed the gate, every bar carries a tab block: four lines labelled at the left of the first bar on the line A, E, C, G from top to bottom (the legend states "re-entrant tuning, G is the high string"), one column per slot of the section's grid, and a fret number on the string's line at each slot where a note starts. A note that rings over following slots gets the same sustain line as a held stroke, drawn on its string. The stroke row under the tab carries the riff's rhythm with the same arrows, in full black, so a strummer can play along and a picker can read direction. Chord names stay above for a second player. The tab block is drawn by the package (inline SVG, as the chord diagrams are), not by alphaTab, so the HTML and the PDF share one rendering path; the alphaTex export gains the riff notes for anyone who later wants playback.

### 3.5 Legend and header

Unchanged from 1.5: title and artist, key with its hedge, capo and sounding key, the no-capo line, chord diagrams in order of first appearance, the power-chord line on the easy sheet, the two-guitar limitation line when it applies. One line is added to the legend when any riff prints: "Tab: A E C G top to bottom; numbers are frets."

### 3.6 Measured effect and costs

Page counts are not promised. They are measured in validation (section 8) for the eight songs against 1.5's 2, 3, 2, 2, 2, 2, 2 and 3 pages. The assumption pass estimated the new sheet from bar counts and the 1.5 page geometry (a paginator calibrated to reproduce all eight 1.5 counts; a bar box taken as 1.6 times a 1.5 chord cell plus a gap, a riff line as 1.5 times a bar line): with four bars to every line, Summer of '69 and All Fired Up gain two pages; with the eight-bar line rule of 3.1, five songs gain one page and none gains two. The eight-bar rule is therefore part of the design, not a lever held in reserve. The expectation written before the run: at most one page more than 1.5 on any song. The songs at risk are the three on a sixteenth grid (Pour Some Sugar On Me, Fame, Need You Tonight), where the eight-bar rule does nothing and the headroom before another page is 69 to 106 mm; if the built bar box is taller than estimated, the whole-line repeat mark of 3.1 is the only remaining lever (A14).

## 4. Rhythm

### 4.1 Choosing a section's pattern: the hybrid vote

For a section (or member, 4.3) with bars `B`, the stage computes two candidates from the per-bar slot vectors: the **majority** vector `M` (as 1.5) and the **medoid** `D`, the real bar with the highest mean Jaccard agreement to the other bars of the section (ties to the earliest bar). It scores them like for like: `score(D)` is `D`'s mean agreement with the other bars; `score(M)` is the mean, over bars, of each bar's agreement with the majority recomputed without that bar (leave-one-out). The printed pattern is `D` when `score(D) - score(M) >= HYBRID_DELTA` **and** `D` has at least `MEDOID_MIN_STROKES` down or up strokes (muted strikes do not count), else `M`.

`HYBRID_DELTA = 0.04`, inside the measured band 0.03 to 0.05: at 0.00 the medoid regresses three ear-right sections, at 0.08 it no longer catches the syncopated verse (pattern-vote spike). `MEDOID_MIN_STROKES = 2`: the assumption pass found that 4 of the 14 sections that would switch at delta 0.04 have an all-rest medoid, and one more an all-mute medoid (a sparse section whose most typical bar is silence or chucks), which is no pattern to print; with the floor, 10 of 68 sections switch. Validation lists the ten. A mute tie-break (prefer the candidate with fewer mute slots when the scores tie) was considered and dropped: across the 68 sections it would never change a printed pattern, and the one case that motivated it (The Cars 52-60) is not a planned section and its planned section already votes without mutes (A2).

Confidence is the mean agreement of the section's bars with the printed candidate. The chance test of 1.5 is unchanged: its statistic is the bars' agreement with their own vote, so it does not depend on which candidate prints, and the assumption pass confirmed that no section's certain or uncertain state changes under the hybrid rule (a medoid-based statistic was also tried and changed no state either). Direction stays a rendering rule (down on eighth positions, up elsewhere), as 1.5.

### 4.2 Two-bar patterns

Before choosing, the stage measures the section's period: `lag2 - lag1`, the mean agreement of each bar with the bar two later minus with the next bar. When `lag2 - lag1 >= PERIOD2_MARGIN` **and** each bar of the best consecutive pair has at least `PERIOD2_MIN_STRIKES` strikes, the section's unit is two bars: the candidates of 4.1 are built over bar pairs (the medoid is a real pair; the majority is voted per position over pairs), and the pattern prints as two distinct bars alternating. Otherwise the unit is one bar.

`PERIOD2_MARGIN = 0.10` (median 0.034, 90th percentile 0.204; seven sections clear it). `PERIOD2_MIN_STRIKES = 2` excludes the sparse-busy alternations in intros and outros: of the seven, one pair is `--------|-------U` and is dropped by the floor, the other six have 2 to 11 strikes in each bar and survive. Across margins 0.08, 0.10 and 0.15 the floor removes exactly that one case and the count of two-bar sections runs 8, 6, 4 (A3).

### 4.3 Members of a merged section

The section plan of 1.5 stands unchanged (the fragment rule, the sandwich rule as written, intro/instrumental/outro/bridge never merging). What changes is what a merged section prints. Each member computes its own pattern by 4.1 and 4.2, its own confidence and its own chance test. The section's pattern is its longest member's, as 1.5. A member prints the **section's** pattern when the Jaccard agreement between the member's own pattern and the section's is at least `MEMBER_AGREE`; otherwise it prints its own, with its own certainty. The section header is unchanged by this; the state phrase reflects the longest member.

`MEMBER_AGREE = 0.35`. The assumption pass measured every member of every merged section on the eight songs (nine members in three merged sections): Wet Leg's 58-65 agrees 0.69 with its section's pattern; All Fired Up's 28-33 agrees 0.75; Verse 2's 55-61 agrees 0.43, 90-97 0.31, 97-104 0.50 and 104-110 0.375. Against the ear: 55-61 must print the section's pattern (the ear accepted it "with variations" and rejected the member's own `D-Dx-U-U`), 90-97 must not (sparse sustained strums), and 104-110 is better served by the section's (four of its six bars play the figure). The threshold therefore sits between 0.31 and 0.375, and 0.35 is its middle; it rests on one merged section (A4). With it: 55-61, 61-90 and 104-110 print the section's pattern; 90-97 prints its own, greyed; 97-104 is a riff by the 5.1 test on its own onsets and prints "riff heard, not transcribed" strokes.

### 4.4 The ring flag

For every detected stroke the stage measures the decay of the source-stem RMS in the first slot after the stroke's peak, in dB, and stores it. Whether strokes **ring** is decided per section: a section rings when the median decay of its measurable strokes (those with at least 1.5 slots to the next stroke) is below `RING_SECTION_DB`; otherwise its strokes are **short**. Every stroke carries its section's flag. The flag is used only by the renderer (3.1); it plays no part in the vote or the chance test.

`RING_SECTION_DB = 5`. The assumption pass measured 2,114 strokes across the eight songs: per-stroke decay is not bimodal enough to flag strokes one by one (9.6% sit between 6 and 10 dB, and a per-stroke cut at 8 dB would have drawn sustain lines on half of a muted-funk song's bars), but song medians separate cleanly: 1.8 to 2.7 dB per slot on six songs, 8.3 and 8.7 on the two played muted (Fame, Need You Tonight). The threshold sits in that gap; per-section medians are checked in validation (A5). The measurement is made on the source the stage already uses (guitar stem, or other, or mix as 1.5 chooses); on the full mix every section is marked ringing, since drums make the decay meaningless, and the legend then omits sustain lines.

### 4.5 Uncertain patterns print greyed

A section or member whose pattern fails the chance test (or whose stem is too quiet to judge) prints its best candidate greyed, with "pattern uncertain" in the header. The 1.5 behaviour of inheriting a neighbour's pattern for short sections is removed: a short section computes its own candidate and prints it greyed when the test cannot pass for lack of bars. The `inherited_from` field stays in the schema, always null from this version, so 1.5 files still load.

### 4.6 Expected effect

On the eight songs: 10 sections change pattern by 4.1 (listed in validation, with the ear-verified ones held fixed); Summer of '69 53-58 prints `DU-U-UDU`; All Fired Up Verse 2 prints the section's pattern on 55-61, 61-90 and 104-110, its own greyed pattern on 90-97, and riff-not-transcribed strokes on 97-104; Need You Tonight's and Fame's bars draw no sustain lines while the six ringing songs' held strokes do; no section prints blank strokes.

## 5. Riffs

### 5.1 The riff test

A section (or member) is a riff when all three hold, computed on the detector's own onsets before the recall gate as 1.5 fixed it:

1. `riff_entropy <= 0.82` and `single_share >= 0.45` (1.5's two features, unchanged, with the knife-edge case named in A8);
2. `pitch_change_share >= PITCH_CHANGE_MIN`, where the share is the fraction of consecutive onset pairs whose named pitches (5.2) differ.

`PITCH_CHANGE_MIN = 0.4`, in the gap between the two strum controls (0.05 and 0.17) and the six ear-confirmed riffs (0.65 to 0.85). Expected effect on the eight songs: All Fired Up 33-49 and The Cars 11-19 lose their riff flag; every ear-confirmed riff keeps it; All Fired Up 97-104 gains it as a member. The band rests on two strum sections (A8).

### 5.2 Naming the notes

For a riff section, the new riff stage reads the stage's source stem at 22 050 Hz mono and runs monophonic pitch tracking (librosa `pyin`, `fmin` E2 82.4 Hz, `fmax` E6 1318.5 Hz, frame 2048, hop 256). At each detected onset it names one note: the rounded median MIDI of the voiced frames from 20 ms after the onset to 10 ms before the next onset (or the bar end), provided at least half those frames are voiced; otherwise the onset is unnamed. The onsets, their slots and their ring flags come from `strums.json`; the riff stage adds pitch and nothing else. This is the split the ear check demanded: rhythm from the onsets the owner has passed twice, pitch from the tracker.

### 5.3 Reducing the bars to a riff

Per bar, the named notes form a slot vector of MIDI values. The riff is chosen exactly as a strum pattern is (4.1, 4.2): the unit is one or two bars by the period rule; the candidates are the majority (per slot, the most common pitch among bars that have a note there, if present in at least half of them) and the medoid (the real bar or pair that agrees best with the others); agreement between two bars is the Jaccard of their (slot, pitch) pairs, a pitch matching only exactly; the hybrid delta and tie-break apply unchanged. The chosen bar's **support** is the mean, over its notes, of the share of bars that have that pitch in that slot.

### 5.4 The gate

Tab prints when all hold for the chosen riff:

- `agreement >= RIFF_AGREE_MIN`: the chosen bar's mean agreement with the section's other bars;
- `support >= RIFF_SUPPORT_MIN`;
- `named_share >= RIFF_NAMED_MIN`: the share of the section's onsets that received a pitch;
- the section passed the riff test (5.1).

`RIFF_AGREE_MIN = 0.70`: the verified riff (Need You Tonight verse) scores 0.72 to 0.76 by the two trackers tried; the verified wrong figure (Fame instrumental) 0.52 to 0.62; the four unsteady riffs 0.08 to 0.41. `RIFF_SUPPORT_MIN = 0.75` (verified 0.80; Fame 0.79, so support alone does not reject it, which is why agreement leads). `RIFF_NAMED_MIN = 0.6` (verified 0.91; Fame 0.76; the unsteady riffs 0.52 to 0.85; this one is a sanity floor, not a discriminator). Every one of these rests on one verified riff, one verified failure and two strum controls (A9 to A11). A riff that fails prints as 3.3 says.

### 5.5 Onto the ukulele

The chosen riff's notes are mapped to strings and frets in three steps, each a rule of the instrument profile, not of any song:

1. Choose the whole-octave shift (−2 to +2) that puts the most notes inside the profile's comfortable range, MIDI 60 to 81 for re-entrant G C E A (open C to the twelfth fret of A); ties to the smaller shift.
2. Move any note still outside the range by whole octaves until it is inside.
3. For each note choose the string and fret with the lowest fret among the strings that can reach it; the re-entrant G string (MIDI 67) counts as a high string. Fret numbers above 12 are allowed but the validation notes them.

The shift is recorded and printed in the header (3.2). The verified riff needs no shift and sits on the C string, frets 0 to 3.

### 5.6 Stated limitation

The two-guitar limitation of 1.5 stands and gains a sentence in the README: "When two guitars share one stem, their notes interleave; the riff stage then finds no steady line and prints the riff as heard, not transcribed." Fame is the example in the validation record, not in the code.

## 6. Key, sections, certainty: unchanged

The three tonic votes and the hedge, the power-chord gates and line, the section plan's rules and constants, the chance test and its densities, the sixteenth floor, the recall gate and the onset detector are all as 1.5 left them. Chords, beats, bars and onsets must be byte-identical to 1.5 on every re-run song; that is the regression line for this version.

## 7. Data formats, stages, compatibility, tooling

**strums.json, schema 2.** Keeps every 1.5 field (`plan`, `patterns` with their chance-test and riff fields, `bar_onsets`). Adds `bars`: one record per bar with `index`, `member` (index into the plan), `strokes` (list of `slot`, `kind` D/U/x, `rings` bool, `decay_db` float), `pattern` (the slot vector the bar prints), `unit` (1 or 2), `confidence`, `p_value`, `uncertain`, `riff` (the 5.1 result for the member). Adds to each `patterns` entry: `candidate` ("majority" or "medoid"), `score_majority`, `score_medoid`, `unit`, `pitch_change_share`. A 1.5 file without `bars` loads with the bars rebuilt from `bar_onsets` and `patterns` (ring flags true, `decay_db` null), so old runs render under the new page.

**riff.json (new stage `05_riff`, between strums and arrange; stage numbers shift by one from arrange on).** Per riff section or member: `onsets` (slot, midi or null), `unit`, `riff` (slot, midi, string, fret, rings), `agreement`, `support`, `named_share`, `candidate`, `octave_shift`, `printable` bool and `reason` when false. Written only when the song has at least one riff section; the score builder treats a missing file as "no riffs".

**score.json, schema 2.** Each bar carries `strokes` (slot, kind, rings), `tab` (list of slot, string, fret, rings) or null, and `grey` bool; each section carries `state` (one of the 3.2 phrases) and `octave_shift`. The per-section `pattern` field stays for evaluate and the alphaTex export. The consistency check that requires the plan to still describe `grid.json` extends to `riff.json`'s sections matching the plan.

**Stages.** `strums.py` gains the hybrid vote, the period rule, the member patterns and the ring measurement, each in `music/` modules (`music/vote.py`, `music/ring.py`) so the stage stays a loop. `stages/riff.py` and `music/pitch.py`, `music/tab.py` are new. `stages/score.py` and `music/score_builder.py` emit per-bar strokes and tab. The renderer's template is rewritten around the bar box; `render/tab.py` draws the tab block as SVG; the strip, example-bar and row-folding code is deleted. `evaluate` prints per-bar patterns, ring flags, the riff test figures and the gate figures; `compare_runs` pairs bars by index and reports pattern changes per section.

**Compatibility.** Old `strums.json` and `score.json` load (above). The manifest records the new stage; `--from arrange` on a 1.5 folder runs the riff stage first since it is upstream of arrange. The non-coder path is unchanged: no new dependency (librosa already provides `pyin`).

**Tooling.** The research scripts stay in `%TEMP%` as throwaway; the implementer mirrors their calls from the research notes, which name every librosa argument.

## 8. Validation

Seven known songs re-run from the strums stage in place (the stems and grids of 1.5 unchanged) plus The Cars from strums, and one new blind song chosen for a prominent single-line riff (unknown until validation, A15). Baselines copied aside first as 1.5 did.

Expectations written before the run:

1. `grid.json`, the chord events and `bar_onsets` byte-identical to 1.5 on all eight songs.
2. The 10 sections the spike says change pattern under the hybrid vote with the strike floor are exactly the sections that change; the five ear-right patterns (All Fired Up 33-49, 61-90, 128-132; The Cars 11-19, 68-72; Need You Tonight 13-24) print as before; Summer of '69 53-58 prints `DU-U-UDU`; The Cars 52-60 prints `DUDUDUDU`.
3. All Fired Up's Verse 2 prints the section pattern on 55-61, 61-90 and 104-110, its own greyed pattern on 90-97, and "riff heard, not transcribed" strokes on 97-104; the header is one "Verse 2". Wet Leg's merged Verse 4 and All Fired Up's Verse 1 print one pattern throughout.
4. Need You Tonight's and Fame's sections are short (no sustain lines); every section of the other six songs rings and shows sustain lines on held strokes; the per-section medians are recorded and none lies within 1 dB of the threshold; Pour Some Sugar On Me prints greyed strokes in every section instead of none.
5. Riff flags: All Fired Up 33-49 and The Cars 11-19 lose theirs; every 1.5 flag that the ear confirmed stays; nothing new is flagged outside All Fired Up 97-104.
6. Tab prints on Need You Tonight's verses and choruses (whichever pass the gate; the verse must), on the C string without an octave shift; Fame, Need You Tonight's intro, The Cars Verse 3 and All Fired Up 97-104 print "riff heard, not transcribed".
7. Pages at most one more than 1.5 on every song.
8. The blind song runs to a sheet with exit 0; its riff flags, gate figures and tab, if any, are recorded, not judged.

Ear clips are prepared for: every section whose pattern changed (the new pattern's clicks), the three member patterns of All Fired Up's Verse 2, five held-stroke bars and five short-stroke bars, every bar of tab that printed (synthesised plucks at the song's tempo, as the ear check did), and the blind song's riff sections. The listening pass that follows is the acceptance test for this version's rhythm and riff claims.

## 9. Assumptions

Each with its status now and what it costs if wrong. "Measured" means on the eight kept runs today; "verified" means by the owner's ear.

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | `HYBRID_DELTA` 0.04 with a two-strike floor fixes the flattened patterns without regressing ear-right ones | Measured on 68 sections and 10 ear ranges; band 0.03 to 0.05; the floor removes four all-rest medoids; **rests on one syncopated section** (Summer of '69 53-58) for the lower edge | A wrong delta either leaves syncopation flattened or breaks right patterns; validation lists every changed section and the listening pass judges them |
| A2 | A mute tie-break is needed | **Refuted and dropped**: over 68 sections it would fire on two and change neither (the majority already had fewer mutes); the motivating range is not a planned section and its planned section votes without mutes | None; the rule is gone |
| A3 | A two-bar unit needs at least two strikes in each bar of the pair | **Measured on all 68 sections**: the floor removes exactly one near-empty case at every margin tried (0.08, 0.10, 0.15 give 8, 6, 4 two-bar sections); the same floor applies to a medoid switch (4.1) | A real two-bar figure with a one-strike bar prints as one bar; cheap |
| A4 | `MEMBER_AGREE` 0.35 separates members that share the section's playing from those that do not | **Measured on all nine members of the three merged sections**; the ear-decided band is 0.31 to 0.375, **set by one merged section** (All Fired Up Verse 2), and the three members above it on other songs agree 0.69 to 0.75 | A member prints the wrong pattern; cost bounded to merged sections, which the plan marks; the margin is 0.04 either side |
| A5 | A section rings when its median stroke decay is under 5 dB per slot | **Measured on 2,114 strokes of all eight songs**: per-stroke flags are not separable (9.6% in the 6 to 10 band), song medians are (1.8 to 2.7 against 8.3 and 8.7); per-section medians are checked in validation; **no sustained-vs-dense distinction within a song** (both ring; the empty slots after a stroke carry that) | Sustain lines drawn on a muted section or missing on a ringing one; a drawing error, not a pattern error |
| A6 | The chance test behaves the same on a medoid candidate as on a majority | **Measured on the 14 switch sections**: the stage's statistic does not read the candidate, so no state changes; a medoid-based statistic was also tried and changed no state | None beyond A1; validation still counts flips against 1.5 |
| A7 | Short sections print their own greyed candidate better than an inherited neighbour's | Design choice from the owner's A-or-B answer; unverified by ear | A reader tries a worse guess than before; the grey says so |
| A8 | `PITCH_CHANGE_MIN` 0.4 separates riffs from strums | Measured: riffs 0.65 to 0.85, **strums 0.05 and 0.17 from two sections only**; the 1.5 knife-edge non-riff (Summer of '69 95-111 at 0.8204 against the 0.82 entropy ceiling) is still protected by the entropy test | A dense strum keeps a riff flag, or a riff loses one; the gate then decides whether anything wrong prints |
| A9 | `RIFF_AGREE_MIN` 0.70 passes real steady riffs and fails blends | **One verified pass (0.72 to 0.76), one verified fail (0.52 to 0.62)**; four unsteady riffs well below | A wrong tab prints, which the owner has said is the worst outcome; or a good riff is withheld, which costs only the tab |
| A10 | `RIFF_SUPPORT_MIN` 0.75 | Measured; does not separate the verified fail on its own (0.79) | None on its own; it backs A9 |
| A11 | `RIFF_NAMED_MIN` 0.6 | A floor; the verified riff 0.91 | A thin riff (few voiced onsets) is withheld |
| A12 | Pitch at the trusted onsets reproduces the verified notes | **Verified for pitch** on Need You Tonight's verse by the spike's method; the stage's exact window (20 ms in, 10 ms before the next onset) is the spike's | Wrong notes print; the ear clips of every printed tab catch it before release |
| A13 | The octave-and-fret mapping gives playable tab | Rule of the instrument; verified only on the one riff (C string frets 0 to 3) | Awkward fingerings; no wrong notes |
| A14 | Pages stay within one of 1.5 | **Estimated** from bar counts with a paginator calibrated on the eight 1.5 sheets: holds only with the eight-bar line rule (five songs +1, none +2); the bar-box height is assumed 1.6 cells and the three sixteenth-grid songs have 69 to 106 mm of headroom | A second page more on a sixteenth-grid song; the whole-line repeat mark is the remaining lever; acceptable per the owner, who ranked honesty above length |
| A15 | A blind song with a steady single-line riff exists among the owner's choices | Unknown by design | The blind song tests only the strum side |
| A16 | Chords, beats, bars and onsets are untouched by this version | By construction; verified by byte comparison in validation | A regression in the part of the chain the ear has already passed |
| A17 | 1.5 files render under the new page via the rebuilt `bars` | Unverified until the loader is written | Old run folders need a re-run from strums; cheap |
