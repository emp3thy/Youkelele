# Version 1.2 validation on five real songs

Date: 2026-10-04. Branch `worktree-v1-2` at `26dadfd` plus this commit. Checks every expectation in section 6 of `2026-10-03-ukulele-tab-chain-v1-2-design.md` and compares against `2026-10-03-v1-1-validation.md` and `2026-10-03-v1-2-fill-measurements.md`.

## Runs

All five ran through the whole chain from their URLs with default settings: `uv run youkelele run "<url>" --runs-dir C:\Users\gethi\sources\Youkelele\runs`. The four existing folders kept their saved options (`--beat-octave auto`, tier easy, 4/4, Demucs, cnn-lstm); "Fame" started from scratch with the same defaults. The version 1.1 `sheet.pdf`, `sheet.html`, `score.json` and stage JSON were copied aside first and compared bar by bar.

| Song | Slug | Exit | Separate | Grid | Harmony | Strums | Arrange, score, render | Ingest done to render done |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Chelsea Dagger | `sexhetcxqy4` | 0 | 109.7 s | 7.5 s | 12.6 s | 1.7 s | 0.9 s | 132 s |
| Summer of '69 | `9f06qzcvuhg` | 0 | 98.0 s | 6.5 s | 11.8 s | 1.6 s | 0.9 s | 119 s |
| Pour Some Sugar On Me | `0uib9y4ofps` | 0 | 153.9 s | 9.6 s | 15.1 s | 2.1 s | 0.9 s | 182 s |
| Wet Leg "mangetout" | `lbc6ccztp5e` | 0 | 116.1 s | 7.7 s | 11.8 s | 1.5 s | 0.8 s | 138 s |
| David Bowie "Fame" | `ypgq0qdgvza` | 0 | 142.6 s | 8.6 s | 13.9 s | 1.9 s | 0.8 s | 168 s |

Stage times are the differences between the `finished_at` stamps in each `manifest.json`. Every ingest printed an ffmpeg "Error parsing Opus packet header" line, as in earlier runs; the audio hashes of the four re-runs match version 1.1 exactly, so it is harmless.

The stems of Summer of '69, Pour Some Sugar On Me and Wet Leg are byte-identical to version 1.1 (same hashes for every stem the manifest records). Chelsea Dagger's audio is identical but its drums, guitar and other stems hash differently. The spec assumed that seeded separation makes the stems match the previous runs; they match to within 16-bit rounding (multithreaded CPU floating-point differences can flip an occasional sample), and Chelsea Dagger's three differing stems are consistent with that. The difference is tiny and changed nothing on the sheet: the backbeat ratio moved in the seventh decimal place (2.0588849 to 2.0588853), and the beats, bars, sections, key, recognised chord events and strum patterns match version 1.1 exactly. The only differences are the new header tempo and the three filled bars. On all four re-runs the beats and bars are identical to version 1.1 and every non-N chord event is unchanged; only Wet Leg's sections differ, by design.

I cannot listen to audio. Every "by ear" judgement is replaced by measurements: an independent librosa tempo, a Krumhansl key estimate on the harmonic stems, and per-bar RMS of each separated stem. What those cannot settle is marked unverified. Every page of every sheet was rasterised and looked at. A script expanded each printed grid (collapsed rows and `×N` blocks) back to bars and compared it with `score.json`: all five match bar for bar, so the collapsing hides nothing.

## Summary

| Song | Clean title | Tempo header / published | Sections (shortest) | Filled bars | Passing chords | Shifted sections | Pages v1.1 / v1.2 | Verdict |
|---|---|---|---|---|---|---|---|---|
| Chelsea Dagger | Chelsea Dagger | 155 (mean 154.7, median 157.9; librosa 154.3) / about 158 | 8 (6) | 3, 4 (C), 8 (G) | B (0.7%) | none | 3 / 3 | Better: intro partly filled, both long choruses collapse to blocks (7 to 5 rows and 10 to 6). Still three pages and the same mostly-rest strum boxes |
| Summer of '69 | Summer Of 69 | 139 (mean 138.6) / about 139 | 11 (4; 5 after the shift) | 118 (A), 119 (Bm) | none | verse at bar 5, +1 | 3 / 3 | Playable as before; tempo right; pickup is now a narrow cell. First verse reads A A D D, not the D then A the spec expected; page 3 still holds only the outro |
| Pour Some Sugar On Me | Pour Some Sugar On Me | 85 (mean 84.9) / about 85 | 7 (11) | 8 (A); 44, 45 (C); 68, 70, 74 (F); 71 (C) | Am (C#m, 0.2%) | none | 2 / 2 | Solo now 7 of 17 bars N.C. (was 11); two probable false fills in the second verse; still no strum box and the wrong key mode |
| Wet Leg "mangetout" | mangetout | 128 (mean 128.0; librosa 129.2) / unverified | 9 (5) | none | C# (1.1%) | chorus at bar 6, +1 | 4 / 3 | Much better: 25 headings become 9 and the middle passage prints as one `×8` row. Page 3 holds a single N.C. cell |
| David Bowie "Fame" | Fame | 95 (mean 94.8, median 93.8; librosa 95.7) / unverified | 8 (5) | none | Am (Cm, 1.5%) | none | none / 2 | Completes cleanly in two pages. A one-shape vamp sheet (D alone under capo 3 in 83 of 101 bars), plausible from the stems; the header names a minor key over major chords |

## Expectations from spec section 6

| Song | Expectation | Met? | Evidence |
|---|---|---|---|
| Wet Leg "mangetout" | No section under four bars | Yes | 9 sections (version 1.1: 25, 17 of them under four bars). Shortest 5 bars in the grid and on the sheet |
| | At most three pages | Yes | 3 pages (version 1.1: 4). Page 3 holds one N.C. cell, the last bar of the outro |
| Chelsea Dagger | Intro bars filled with chords from the song's set | Yes, partly | Bars 3 and 4 fill as C and bar 8 as G, exactly as the fill measurements predicted; both are in the song's set. The other six intro bars stay N.C. and the stems agree: guitar at most 0.004 RMS and bass at most 0.002 in bars 0 to 2 and 5 to 7, drums only. The version 1.1 report's "about six bars of intro missing" overstated it |
| | Alternating G and D rows collapsed as a block | Yes | First chorus: `G G G G ×2`, then `D D D D / G G G G` once with `×2`, then D D D D and G: 5 rows (version 1.1: 7). Final chorus: `G C/D G C/D / G C/D Am D ×2` and `G G G G / D D D D ×2`: 6 rows (version 1.1: 10) |
| | At most three pages, ideally two | Yes for three, no for two | 3 pages; page 3 is about half full (the 6-bar bridge and the final chorus). The intro gained a row because the fills break its `N.C. ×2` collapse |
| Summer of '69 | First verse rows start on D A | No | Phrase alignment moved the first verse one bar later, to bar 5 (`shifted: 1`), so it reads `A A D D ×3`, then A A: the rows are now in phase with the two-bar chord rhythm, but the section starts a phrase late. This now matches the four later verse sections, which all start A A D D, but it does not start on D. The vocal stem enters in bar 3 (0.077 RMS, then 0.11 to 0.15 from bar 4), so the sung phrase starts on the D bars 3 and 4; starting the rows on D would need the boundary one bar earlier, and the rule only moves later |
| | Tempo header 138 or 139 | Yes | "139 bpm" (mean interval 138.6; the median gave 136.4) |
| | At most three pages | Yes | 3 pages; page 3 holds only the 10-bar outro, as in version 1.1 |
| Pour Some Sugar On Me | Solo bars filled where the band plays | Yes, partly | In the solo section (bars 67 to 83) bars 68, 70 and 74 fill as F (A sounding) and 71 as C (E). N.C. falls from 11 of 17 bars to 7. Bars 69 and 73 stay N.C. although the guitar stem is at solo level (0.022 to 0.023 RMS): their chroma is the lead line and matches no triad (r 0.23 and 0.19). Bars 77 to 80 are the drum-and-voice breakdown (guitar 0.005 or less) and rightly stay N.C.; bar 67 (energy 0.162) is just under the threshold |
| | Still capo 4 | Yes | Capo fret 4; shapes A D G C F, passing Am; header "Key A major (shapes)" and "Sounding key: C# major" |
| | At most three pages | Yes | 2 pages, the lower third of page 2 empty |
| David Bowie "Fame" | The chain completes | Yes | Exit 0; separation 142.6 s, everything after it under 15 s per stage |
| | Title cleaned to "Fame" | Yes | `raw_title` "Fame (2016 Remaster)", `title` "Fame", artist "David Bowie" |
| | No section under four bars | Yes | 8 sections, shortest 5 bars (the intro: a one-beat pickup plus four bars; and the first "verse 2") |
| | At most three pages | Yes | 2 pages |
| | Tempo, key, capo, filled bars and passing chords recorded and judged from audio features | Yes | Tempo 94.8 bpm (median 93.8, librosa 95.7, backbeat ratio 2.63, octave none); key F minor (confidence 0.09); capo 3; no filled bars (the only all-N bar is the last one, bar 100, at energy 0.033 of the chorded median); passing Cm, printed as Am under the capo. Judgements and what cannot be verified are in the per-song section |
| All | Titles without artist prefix or upload tags | Yes | Chelsea Dagger; Summer Of 69; Pour Some Sugar On Me (artist Def Leppard, no longer in capitals); mangetout; Fame. "Summer Of 69" keeps the upload's capitals and missing apostrophe, which the rules leave alone |
| | Passing chords without diagrams | Yes | B (Chelsea), Am for C#m (Pour Some Sugar On Me), C# (Wet Leg) and Am for Cm (Fame) are absent from each legend and listed as `Passing: B 4322`, `Passing: Am 2000`, `Passing: C# 1114`, `Passing: Am 2000`. Each still names its cells |
| | No filled chords in bars without harmonic energy | Yes | All 12 filled bars have an energy ratio of at least 0.235 of the chorded median and a playing guitar, bass or other stem. Two are probably wrong anyway (Pour Some Sugar On Me 44 and 45, see below) |

Section 4 of the spec, checked on the sheets: filled chords print in italics on all three songs that have them, with the note "Italic chords were inferred where the recording had no clear chord" under the header (absent on Wet Leg and Fame, which have no fills); the pickup prints as a narrow leading cell labelled "pickup" on the first row of its section (Summer of '69, "N.C."; Fame, "Dm"); repeated blocks print once with a bracket and `×N`.

## Per song

### Chelsea Dagger

**Pages.** Italics in these descriptions mark inferred chords, as on the sheet. Page 1: title, artist, the facts line (Key D major, Capo none, Tempo 155 bpm), the italics note and the strum-uncertain note, seven diagrams (C G D A Bm Em Am), "Passing: B 4322", the intro labelled "verse" (N.C. N.C. N.C. *C* / *C* N.C. N.C. N.C. / *G*, no box), the first chorus with its `--D---D-` box (5 rows as above) and the start of the first verse (G A A C, Bm Em D G). Page 2: the rest of the first verse (ending in long Em and Bm runs), a 10-bar chorus, the second verse (with B in one cell) and a 6-bar chorus. Page 3: the 6-bar bridge (D D G G G G) and the 37-bar final chorus in 6 rows; the lower half of the page is empty.

**Quality.** The best change is the chorus: the two-chord G and D song now looks like one, a block of four G and four D printed once with `×2`. The passing B no longer takes a barre diagram. The intro shows the guitar's C entry in italics, and the italics note says why. What is still wrong:

- The strum boxes are unchanged from version 1.1 (identical patterns): the first chorus `--D---D-`, the bridge `--D---D-` and the final chorus `--D-D---` are 75% rests and printed as certain.
- Three pages, not two. The two verses (23 and 22 bars) have no repeats to collapse, and each of the eight sections spends a heading and a box.
- The tempo header dropped from 158 to 155 with the mean-interval rule. The beat tracker's intervals are quantised to 0.02 s, so the median sits on 0.38 s (157.9) while the beats span the song at an average of 0.388 s; an independent librosa tracker gives 154.3 (half-tempo 77.1, doubled). Both trackers say the recording averages about 155, against a published figure of about 158. Unverified by ear.
- Labels as in version 1.1: the intro is "verse" and the first "chorus" begins at bar 9.

**Completeness.** All 142 bars present. The intro's remaining six N.C. bars are drums only in the stems, so N.C. is the honest reading. Header fields complete; the title no longer repeats the artist.

### Summer of '69

**Pages.** Page 1: title, artist, Key D major, Capo none, Tempo 139 bpm, the italics note, seven diagrams (D A Bm G F Bb C), the intro labelled "verse 2" with its box and the narrow "pickup N.C." cell leading the row (then N.C./D, D, D, D), the first verse (`A A D D ×3`, A A) with the `xxxU-xxx` box, the first chorus (`Bm A D G ×2`, Bm A D D) and a short verse (`A A D D ×2`, A A). Page 2: the second chorus (uncertain, no box), a 5-bar verse, the bridge labelled "verse 2" (A F Bb C / Bb F Bb C / C D D, uncertain), the third verse (`A A D D ×3`, A A), the third chorus with a single down-stroke box, and the last verse (`A A D D ×4`, uncertain). Page 3: only the outro (A A A/D D / D N.C. N.C. *A* / *Bm* N.C.).

**Quality.** Still the most playable sheet: the chord set and order match the published charts, the header tempo is now right, and the pickup no longer takes a row. What is wrong:

- The first verse reads A A D D. Version 1.1 read D A A D; the shift fixed the split pair but in the direction that moves the row start away from the vocal entry (see the expectations table).
- The outro gained two italic chords, A and Bm, in bars 118 and 119. The stems show the band playing into the fade there (bass 0.10 to 0.11 RMS, energy ratio 0.89 to 1.01), so the fill rule is behaving as designed, but they sit between two loud unpitched N.C. bars and a silent one, and their chroma peaks on D sharp and E, so whether A and Bm are what is played is unverified.
- Unchanged from version 1.1: the bridge is "verse 2", the intro is "verse 2", and the third chorus box is one down stroke (`D-------`, confidence 0.53) printed as certain.
- The F of the bridge is not a passing chord by a margin of 0.02 s (its longest event is 1.76 s against a 1.74 s median bar). That is the right outcome, since F is a structural bridge chord, but it is fragile.

**Completeness.** All 121 bars present, including the pickup. Choruses 3 of 3. Page 3 exists only for the outro's three rows.

### Pour Some Sugar On Me

**Pages.** Page 1: the clean title, "Def Leppard", Key A major (shapes), Capo fret 4, Tempo 85 bpm, four notes (italics, shapes relative to the capo, sounding key C# major, strum detection uncertain), five open diagrams (A D G C F), "Passing: Am 2000", the intro (N.C. / N.C. A / six bars of A / *A* / N.C. N.C.), the first verse (A ×4, N.C. ×4, `A A A A ×2`, D/G), the first chorus and the first row of the second verse. Page 2: the rest of the second verse (N.C. *C* *C* N.C., `A A A A ×2`), the second chorus (ending Am, N.C.), the solo section (N.C. *F* N.C. *F* / *C* C N.C. *F* / C C N.C. N.C. / N.C. N.C. C C / D/G) and the final chorus (G C/F C/G C/F, then `G C/F G C/F ×3`, then G C/F G). The lower third of page 2 is empty.

**Quality.** The fills do most of what was asked in the solo: the guitar's A and E (F and C shapes) now appear in four bars that were N.C., in italics. What is wrong:

- Bars 44 and 45 fill as C (E sounding) in the middle of the second verse. These are probably false: the version 1.1 run lessons describe the verses as marked N.C. in the published chart, the first verse has N.C. at the same place, and the guitar stem there is 0.008 to 0.009 RMS, a third of its level in chorded bars. They pass only because this song's chorded median is low. A reader now sees the two verses differ.
- Bar 8 fills as A in the intro, which is the music video's opening before the album audio (22.8 to 25.6 s; the stems there are mostly the other stem at 0.013 and drums). It continues the six A bars before it, so it is harmless.
- Still no strum box: all seven patterns are uncertain (unchanged from version 1.1).
- Key mode still C# major against the true C# minor (power-chord riff read as major).

**Completeness.** All 103 bars present. Of the solo section's remaining 7 N.C. bars, four are the drum-and-voice breakdown and correct; bars 69 and 73 (lead line over the band) and 67 (faint guitar) are the misses.

### Wet Leg "mangetout"

**Pages.** Page 1: "mangetout", "Wet Leg", Key C major, Capo none, Tempo 128 bpm, no notes, three diagrams (C F Dm), "Passing: C# 1114", the opening labelled "verse 2" (C C C C / F F) with a box, the chorus (`C C F F ×3`) with straight eighths, the uncertain verse (F/C C F F / C C F F / Dm F C C / Dm F C) and the first row of the second chorus. Page 2: the rest of that chorus, the verse (`C C F F ×2`, Dm F C C, Dm F C C/C#), "verse 2" (C C C C / C C/C# Dm), the bridge (`F C C Dm ×8`, then F C C), the last chorus (Dm F C C / C C F F/C#) and the outro marked "No strummed instrument detected" (C# N.C. N.C. N.C.). Page 3: one N.C. cell.

**Quality.** The sheet now reads like a song: nine headings instead of 25, and the 35-bar middle passage that printed as ten two-bar headings is one row repeated eight times. The chorus shift (bar 5 to 6) makes it `C C F F ×3`. C# no longer has a barre diagram. What is wrong:

- The last row of the outro, a single N.C. bar of non-song audio, spills onto page 3. The four N.C. bars at the end are the drone on the other stem after the song.
- The two-bar stop-start texture of the middle passage (bass dropping to 0.16 to 0.23 of the mix every other two bars, measured in version 1.1) is no longer visible; one strum box (`DUDUxxDU`, confidence 0.73) covers both textures. Unverified whether that box fits either.
- Labels are still arbitrary: the opening is "verse 2" and the middle passage is "bridge".

**Completeness.** All 113 bars present, no fills (the only all-N bars are the drone at the end, rejected at r 0.22 to 0.30). Header fields complete. What I cannot verify: true tempo and key, the chord names, whether C# is real, the section names, the strum patterns.

### David Bowie "Fame" (blind test)

**What I measured.** The audio is 261.4 s; the first beat is at 3.38 s (the audio before it is near silent, RMS 0.0019 against 0.136 for the song) and the last at 256.46 s. Beat This! gives 93.8 bpm by median interval and 94.8 by mean; librosa's tracker gives 95.7. The backbeat ratio is 2.63, the highest of the five songs, so the octave is almost certainly right and the tempo is about 94 to 96 bpm. The tonic is clearly F: it is the strongest chroma bin of both the harmonic stems (1.00) and the bass stem (1.00). The mode is not settled by the audio: Krumhansl gives F minor 0.530 against F major 0.525 on the harmonic stems and 0.557 against 0.507 on the full mix (vocals included), and the harmonic chroma holds A (the major third) and A flat (the minor third) equally, both 0.42. The next strongest bins are E (0.73) and E flat (0.64). The chord recogniser labels 85.8% of the chord time F:7 and 10.1% Bb:7, with short F:min, F:min7 and C:min7 events; the easy tier reduces them to triads. That is consistent with a vamp on F with a flattened seventh, but whether the guitar plays a full chord or a single-note riff cannot be told from these features. Vocals are near silent in the first 10 bars (the opening "intro" and "verse 2", 0.000 to 0.002 RMS) and in the second "verse 2" (bars 53 to 60, 0.000), so those are instrumental passages; the bridge has the loudest vocal (0.095).

**Pages.** Page 1: "Fame", "David Bowie", Key D minor (shapes), Capo fret 3, Tempo 95 bpm, the capo notes "Shapes are relative to the capo" and "Sounding key: F minor", three diagrams (Dm G D), "Passing: Am 2000", the intro with a narrow "pickup Dm" cell then Dm, Dm/Am, G, G (uncertain, no box), "verse 2" (five bars of D) with a 16-slot box, the chorus (`D D D D ×2`, D) and the start of the 34-bar verse (D D D D / D D G G / `D D D D ×4`). Page 2: the rest of that verse (G G D D / D D D D / D D/Dm), the second "verse 2" (Dm/Am Am/G G G/D / D D D D), the chorus (`D D D D ×2`, D D), the bridge (D D D D / D D/G G G/D / D D D) and the last verse (`D D D D ×4`, D D N.C.), which ends near the foot of the page.

**Quality.** Under capo 3 every shape is open (D, G, Dm and the passing Am), where the no-capo set would need a Bb barre; a beginner can play it. The sheet is mostly one shape, which matches what the recogniser and the chroma say about the song. Seven sections print a dense 16-slot box (38 to 50% rests, confidence 0.62 to 0.76). What is wrong:

- The header says "Key D minor (shapes)" and "Sounding key: F minor" above a grid where 83 of 101 bars are D alone, the major shape. The key estimator chose minor by a margin of 0.005 on the stems; the chord events say F major (or F7). A reader is told one thing by the header and another by the grid.
- The pickup holds Dm (F minor sounding) and the intro opens Dm, Dm/Am, then G G; from bar 5 on, 83 of the 96 bars are D alone. The short F:min event at the start may be the riff's minor-third colour rather than a minor chord. Unverified.
- Labels: "verse 2" names two instrumental passages; "chorus" and "verse" alternate on the same chord. Unverified either way.

**Completeness.** All 101 bars present, from the pickup at 3.38 s to 257.1 s; nothing after the last beat is lost (the tail is silent). No fills: the only all-N bar is the last one (bar 100), at 0.033 of the chorded energy; bar 99 holds F7 until its last beat, so it prints D. Header fields complete and clean. What I cannot verify: the true tempo and mode, every chord name, whether the guitar plays chords at all, the section names, and the strum patterns.

## What to improve next

Ranked by benefit to the person reading the sheet.

1. **Run the strike-threshold spike (version 1.1 spec section 7).** Stage: strums. Evidence: unchanged since version 1.1 and now the largest visible fault. Chelsea prints three certain boxes with 75% rests (first chorus, bridge, final chorus); Summer of '69's third chorus is one down stroke printed as certain; Pour Some Sugar On Me has no box at all. Wet Leg (0 to 50% rests at 8 slots) and Fame (38 to 50% at 16 slots) are the dense songs any new rule must leave alone.
2. **Compact the sheet so a short song fits two pages.** Stage: render. Evidence: three of five sheets print a third page that is at most half full: Wet Leg's holds one N.C. cell, Summer of '69's holds the 10-bar outro, Chelsea's is about half full. Row collapsing has done what it can (Chelsea 38 to 33 rows, Wet Leg 36 to 21); the remaining height is section headings and strum boxes, about two rows' worth per section (Summer of '69 has 11 sections and 22 rows and needs three pages; Pour Some Sugar On Me has 7 sections, no boxes and 24 rows and fits two). Two fixes, each helping different songs. Dropping the trailing N.C. bars after the last chord (Wet Leg bars 109 to 112, non-song audio) removes Wet Leg's page 3 on its own. It would not help Summer of '69, whose outro would still need three rows without bar 120, or Chelsea. Those two need less height per section, for example the strum box beside the first rows rather than above them.
3. **Take the key mode from the chords when the key estimate is a near tie.** Stage: harmony or score. Evidence: Fame's header names F minor and a D minor shape key over a grid that is D major alone in 83 of 101 bars, with a Krumhansl margin of 0.005; Pour Some Sugar On Me still reads C# major where the truth is C# minor (confidence 0.010). The two errors go in opposite directions, so the rule needs measurement on both, not a bias towards one mode.
4. **Let phrase alignment move a section start earlier when the vocal enters earlier.** Stage: score. Evidence: Summer of '69's first verse moved from bar 4 to bar 5 and reads A A D D, while the vocal stem enters in bar 3, so the expected D then A start needed a move the other way. The second shift (Wet Leg's chorus to bar 6, giving `C C F F ×3`) looks right but cannot be checked. One failing song; measure before changing the rule.
5. **Tighten filling where the guitar is faint, and catch lead-line bars.** Stage: harmony. Evidence: Pour Some Sugar On Me bars 44 and 45 fill in a verse the published chart marks N.C. (guitar a third of its chorded level) while solo bars 69 and 73, with the guitar at full solo level, stay N.C. because a lead line matches no triad. A per-stem test (the guitar or bass against its own chorded median) and carrying the surrounding chord through a loud, unmatched bar inside a filled run are both candidates; the fill measurements show the margins are narrow (bar 68 fills at 0.235).
6. **Name a block of novel chords a bridge; stop naming intros after verses.** Stage: grid. Evidence: Summer of '69's F Bb C bridge is still "verse 2"; the openings of Chelsea Dagger ("verse", bars 0 to 8), Summer of '69 and Wet Leg ("verse 2") are named after verses; Fame's two instrumental passages are "verse 2". Unchanged from version 1.1 item 8.

Not ranked as faults: Chelsea Dagger's header tempo of 155 sits under the published 158, but two independent trackers measure the recording at about 155 (see its section). The passing rule decides Summer of '69's F and Fame's F:min7 by 0.02 to 0.04 s against the median bar; both outcomes are right today.
