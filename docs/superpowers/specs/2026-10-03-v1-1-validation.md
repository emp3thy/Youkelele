# Version 1.1 validation on four real songs

Date: 2026-10-03. Branch `worktree-v1-1` at `3ee4d46` plus this commit. Checks every expectation in section 6 of `2026-10-03-ukulele-tab-chain-v1-1-design.md` and compares against `2026-10-03-real-run-lessons.md`.

Runs, all with `--runs-dir C:\Users\gethi\sources\Youkelele\runs`:

- Chelsea Dagger (`sexhetcxqy4`): `--from grid --beat-octave auto`.
- Summer of '69 (`9f06qzcvuhg`): `--from grid --beat-octave auto` (passed explicitly so a saved option could not leak in).
- Pour Some Sugar On Me (`0uib9y4ofps`): `--from grid --beat-octave auto`.
- Wet Leg "mangetout" (`lbc6ccztp5e`): a full run from the URL with default settings.

All four exited 0. The version 1 `sheet.pdf`, `score.json` and stage outputs were copied aside before the re-runs and compared bar by bar. Ground truth for the three known songs is `research_notes\gap_analysis\verification_web_pages.md` (sections 3, 4, 5, 10) and the lessons document. There is no reference for "mangetout". I cannot listen to audio, so every "by ear" judgement in the spec is replaced by measurements: an independent librosa tempo and key estimate, and per-bar stem levels from the separated stems. What those cannot settle is marked unverified.

## Summary

| Song | Tempo found / true | Octave, backbeat ratio | Key found / true | Capo and shapes / published | Slots | Grid fit | Sections | Pages v1 / v1.1 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Chelsea Dagger | 157.9 (mean interval 154.7) / about 155 to 158, unverified | none, 2.06 | D major (confidence 0.006) / unverified, D or G major | 0; G D A C Bm Em Am B / no published chart | 8 (v1: 16) | 0.55 (v1: 0.40) | 8 | 15 / 3 | Usable chord chart. Intro lost to N.C.; three of seven strum boxes are mostly rests |
| Summer of '69 | 136.4 (mean 138.6) / 139 | none, 2.14 | D major / D major | 0; D A Bm G F Bb C / exactly the Ultimate Guitar and UkuTabs set, no capo | 8 | 0.91 | 11 | 10 / 3 | Playable. Right chords and capo; bridge still labelled "verse 2"; one chorus box is a single down stroke |
| Pour Some Sugar On Me | 85.7 (mean 84.9) / 85 | none, 2.14 | C# major / C# minor | 4; A D G C F Am / capo 4 with A C G F (spike's expectation; no ukulele chart exists) | 16 | 0.59 | 7 | 12 / 2 | Chord chart mostly right and now all-open. No strum guidance at all (every section uncertain); the solo is mostly N.C. |
| Wet Leg "mangetout" | 130.4 (mean 128.0; librosa 129.2) / unverified | none, 1.94 | C major (audio key score C major 0.644 against F major 0.566) / unverified | 0; C F Dm C# / no reference | 8 | 0.73 | 25 (17 under 4 bars) | none / 4 | Chords simple and plausible, but the sheet is fragmented into two-bar sections and misses the page target |

## Expectations from spec section 6

| Song | Expectation | Met? | Evidence |
|---|---|---|---|
| Chelsea Dagger | Automatic rule keeps 158 bpm without an override | Yes | 157.9 bpm, `octave_decision` none, run with `--beat-octave auto` |
| | Backbeat ratio about 2.1 | Yes | 2.06 |
| | Eight slots | Yes | 8 slots per bar |
| | Grid fit about 0.55 | Yes | 0.546; section confidences 0.45 to 0.71 apart from the N.C. intro (0.22), as the lessons predicted. The stage is still flagged uncertain because 0.55 is under the 0.6 stage threshold |
| | At most three pages | Yes | 3 pages |
| Summer of '69 | Chord sequence unchanged | Yes | 0 of 121 printed bars differ from version 1 |
| | Capo 0 unchanged | Yes | Capo 0 scores 2.01 against 2.34 for capo 2, the 0.33 margin the spec measured |
| | At most three pages | Yes | 3 pages, but page 3 holds only the 10-bar outro |
| | Pickup bar drawn as a pickup | Yes, partly | Bar 0 (0.02 to 0.44 s, one beat) is flagged `pickup` and printed "pickup N.C." on a row of its own. It is a one-bar-wide cell in a smaller font on a row of its own, not the narrow leading cell spec 3.1 item 4 describes |
| | Final bar not stretched | Yes | Bar 120 ends at 207.02 s, one median beat after the last beat (version 1: 207.25 s). On the other two songs the stretch was larger and is also gone: Chelsea's last bar ends at 220.12 s instead of 229.41 s, Pour Some Sugar On Me's at 289.76 s instead of 295.50 s |
| Pour Some Sugar On Me | Capo 4 | Yes | Capo 4 scores 1.85 against 2.32 for capo 1, margin 0.47 as measured in the spec (version 1: capo 2) |
| | A, C, G, F shapes | Yes | A (for C#), C (E), G (B), F (A), plus D (F#) and Am (one 0.5 s C#m event). All open, no barre |
| | Header shows shapes relative to capo and sounding key | Yes | "Shapes are relative to the capo" and "Sounding key: C# major". The Key field above repeated "C# major" (fixed in this wave: with a capo the Key fact now shows the shape key, "A major (shapes)"), and the mode is wrong (see below) |
| | At most three pages | Yes | 2 pages |
| Wet Leg "mangetout" | The chain completes | Yes | Exit 0. Separation 105 s, grid 7 s, harmony 10 s, everything after under 3 s |
| | Octave decision recorded | Yes | none at 130.4 bpm, backbeat ratio 1.94. At 130 bpm the halving rule cannot fire, so the backbeat test was not exercised. Three estimates agree within 2.4 bpm, so the octave is very likely right |
| | Key, capo, slots, grid fit recorded | Yes | C major, capo 0, 8 slots, grid fit 0.73 |
| | Judged by ear against the record | No | I cannot listen. Measurements stand in for it: see the per-song section |
| | At most three pages | No | 4 pages. 25 sections, 17 of them 2 or 3 bars long, each with its own heading |
| | A reader can follow the chord grid without the audio | Partly | The chords are three open shapes and easy to read. The middle of the song prints as ten headings of two bars each, which reads as a puzzle rather than "Dm F C C, five times" |

End-to-end test: the synthetic clip prints in at most two pages (`count_pages(pdf_bytes) <= 2` added to `tests/test_end_to_end.py`, passing).

## Per song

### Chelsea Dagger

**Pages.** Page 1: header, the strum-uncertain note, eight chord diagrams, the N.C. intro (two rows, the first `×2`) and the first chorus as alternating rows of four G and four D. Page 2: the first verse (G A A C, Bm Em D G, ending in long Em and Bm runs), a 10-bar chorus and the second verse. Page 3: a 6-bar chorus, the 6-bar "bridge" (D D G G G G) and the 37-bar final chorus.

**Quality.** The sheet is readable and a player could strum along from it: the chords are open shapes, the chorus is visibly a two-chord G and D song, and the verses show a real progression. What is right: the tempo octave without an override, eight slots, the chord vocabulary and its timing (version 1.1 prints the same chord in every bar as version 1). What is wrong:

- The grid prints G G G G / D D D D rows one after another, seven rows for the 29-bar first chorus (one already collapsed `×2`) and ten for the 37-bar final chorus, because only identical consecutive rows collapse. A two-row repeat would print as one `×3` block.
- The strum boxes are weak. The first chorus (bars 9 to 37) shows down strokes on beats 2 and 4 only (`--D---D-`), which is the snare bleed pattern the lessons described, and the bridge and last chorus are also 75% rests, all printed as certain (confidence 0.45 to 0.47).
- The labels are visibly off at the start, as in version 1: the first "chorus" begins at bar 9 (14.4 s), eleven bars before the vocals. The sections are unchanged from version 1.
- The capo choice is thin: capo 0 scores 1.93 against 2.04 for capo 2.

**Completeness.** All 142 bars are present. The first 9 bars (0.6 to 14.4 s) print as N.C. although the stems show guitar from about 5 s and bass from about 10 s, so about six bars of intro are missing. No section is lost to the row collapse (the only `×2` collapses are N.C. intro rows and the first G row). The 9.3 s tail after the last beat is no longer drawn as a bar; it is the final chord ringing out. Header fields: title, artist, key, capo, tempo, tuning, tier, meter and the strum note are all present. The title repeats the artist ("The Fratellis - Chelsea Dagger").

### Summer of '69

**Pages.** Page 1: header, seven diagrams, the intro labelled "verse 2" with its strum box and the pickup cell, the first verse (`D A A D ×3`), the first chorus (`Bm A D G ×2`, then Bm A D D) and the start of verse 2. Page 2: the end of verse 2, the uncertain second chorus (no box), the short verse, the bridge labelled "verse 2" (F Bb C Bb F Bb C), the third verse and the third chorus with a one-arrow box, and the start of the last verse. Page 3: only the 10-bar outro (A A A/D D D, then five N.C. bars of fade).

**Quality.** This is the best of the four and a ukulele player could play the song from it. The chord set and sequence match the published charts exactly: verse alternating D and A every two bars, chorus Bm A D G, bridge F Bb C. The verse box (`xxxU-xxx`, mostly muted strokes) is close to Ultimate Guitar's muted eighth chug. What is wrong:

- The bridge (bars 58 to 68, 99.2 to 118.3 s) is still labelled "verse 2", and so is the intro, as in version 1.
- The first verse row reads D A A D because the section boundary sits one bar into the two-bar harmonic rhythm (bars 1 to 4 are all D). Later verses read A A D D. A player has to notice that the phrase is the same.
- The third chorus box (bars 83 to 94) is a single down stroke on beat 1 (`D-------`, confidence 0.53, printed as certain), although the record strums through the chorus. The strum boxes vary from verse to verse (`D-DU--D-`, `DU-U-UD-`, `D--UDUD-`) where the record has one pattern, which says the per-section detection is noise around the same groove.
- Page 3 carries one 10-bar section; the sheet would fit in two pages if the outro's five fade-out N.C. bars collapsed or the rows packed tighter.

**Completeness.** All 121 bars are present, including the pickup and the 1-beat last bar. No N.C. where a chord is clearly playing: the only N.C. is the first 0.9 s and the 8.6 s fade at the end. Choruses 3 of 3 present. Header fields present; the title keeps "(Official Music Video)".

### Pour Some Sugar On Me

**Pages.** Page 1: the long title, header with capo 4, the two capo lines and the strum note, six open diagrams, the intro (N.C., then six bars of A, then three N.C.), the first verse (A ×4, N.C. ×4, A A A A `×2`, D/G), the first chorus and the start of the second verse. Page 2: the end of the second verse, the second chorus (ending Am, N.C.), the third "verse" (mostly N.C. with five bars of C) and the final chorus (`G C/F G C/F ×3`). The lower half of page 2 is empty.

**Quality.** The chord chart is right in most places and is now playable on open shapes: the chorus E A B prints as C/F then G, the pre-chorus F# B as D/G, the C# riff as A. A player who knows the song could follow it. What is wrong:

- No section has a strum box. All seven patterns are uncertain (confidence 0.08 to 0.42, grid fit 0.59), so the sheet is a chord chart only. That is honest, but it gives no rhythm guidance on a song with a very recognisable groove.
- The key is still C# major; the truth is C# minor (the verse riff is a no-third power chord the model reads as major). The header printed "Key C# major" and "Sounding key: C# major" one above the other, which repeated itself and said nothing about the shape key a capo-4 player reads in (A); fixed in this wave, the Key fact now reads "A major (shapes)".
- The third "verse" (bars 67 to 83, 189.5 to 237.5 s) is the solo and the breakdown in the record. It prints 11 of 17 bars as N.C., although the lessons measured the guitar stem at 0.25 to 0.34 of the mix around the solo.
- The D of the bridge (Hooktheory VII to I) is never detected, as in version 1.
- Bars with three chords (`C / F / G`, bar 58) are legible but tight.

**Completeness.** All 103 bars present; the 5.7 s after the last beat is no longer a bar. The intro section (0.1 to 31.3 s) is the music video's opening, 25.2 s of which precedes the album audio; its six bars of A belong to the video, not the album track. The many N.C. bars in the verses are mostly right (the published chart marks the verses N.C.). The pre-chorus is not its own section: it is absorbed at the end of each verse (one D/G bar) and the start of each chorus. Header fields present; the title is "DEF LEPPARD - "Pour Some Sugar On Me" (Official Music Video)" and the artist is in capitals.

### Wet Leg "mangetout" (blind test)

**What I measured.** The song is 213.3 s. Beat This! gives 130.4 bpm (median interval), the mean interval gives 128.0 and librosa's beat tracker gives 129.2, so the tempo is about 128 to 130 bpm and the octave is almost certainly right. A Krumhansl key estimate on the harmonic part of the mix gives C major 0.644 against F major 0.566 and C minor 0.480, a clear margin, and the chord time (C 50.7%, F 32.0%, Dm 12.4%, N 3.8%, C# 1.1%) is a I, IV, ii song in C. The bass stem dominates the mix (0.6 to 0.8 of the mix RMS in most bars); the guitar stem is weak (0.1 to 0.3, source ratio 0.20) and almost absent in bars 18 to 25 (34 to 49 s). Vocals enter at bar 2 (4.0 s), alternate bar by bar in bars 10 to 17 and 42 to 49 (call and response), and the passage at bars 66 to 87 (124 to 165 s) alternates every two bars between full band and a quieter texture where the bass drops to 0.16 to 0.23 of the mix and the mix level falls by 4 to 5 dB. The last four bars (204.6 to 211.1 s) hold only the "other" stem, at a level as loud as the song: non-song audio at the end of the video, which the sheet rightly prints as N.C.

**Pages.** Page 1: header, four diagrams (C, F, Dm and a C# barre), the 5-bar opening labelled "verse 3" with a box, then six headed sections of two or three bars each (F C C, F F, C C, F F, C C, F F). Page 2: a 15-bar verse (no box), a 9-bar chorus with a `DUDUDxDU` box, a 16-bar verse with straight eighths (`C C F F ×2`, Dm F C C, Dm F C C/C#), a 7-bar "verse 3" and a 3-bar verse. Page 3: ten headings alternating "verse 2" (Dm F) and "verse" (C C), then a 12-bar "verse 2" (`Dm F C C ×3`). Page 4: an 8-bar chorus with straight eighths and the 5-bar outro (C#, then four N.C.) marked "No strummed instrument detected".

**Quality.** The chords themselves are easy and plausible: three open shapes, changes on bar lines, the I, IV, ii vocabulary consistent with the key estimate. Six sections print a strum box, and they are dense (0 to 25% rests), mostly straight eighths, the opposite of the sparse-pattern problem on the other songs. What is wrong:

- The sheet is fragmented. The section stage cut 17 sections of 2 or 3 bars, so the reader meets 25 headings in 113 bars. The fragments follow real texture changes (the vocal call and response, the two-bar stop-start passage), but they are not song sections, and they push the sheet to four pages.
- Sixteen of the seventeen short sections have pattern confidence 0.61 to 1.00 and are uncertain only because they are under four bars, so they print no box. Four of them print "inherited from" a section with a different label ("verse" inherited from "verse 3"), which a reader cannot act on.
- C# appears four times (bars 57, 63, 107, 108), each about half a bar, and gets a barre diagram. At bar 63 it sits between C and Dm, which fits a chromatic walk-up; elsewhere it may be a slide or an error. Unverified either way; a beginner would be better served without the diagram.
- Labels are arbitrary: the opening is "verse 3", and the last 20 bars of the middle passage are "verse 2" while the same chords earlier are "verse".

**Completeness.** All 113 bars present; no section is lost to collapse. No N.C. where a chord is clearly sounding: the only N.C. bars are the non-song audio at the end. Bars 18 to 25 have chords (from the bass) but no strummed guitar, and the sheet does not say so; its section pattern is flagged uncertain. Header fields present; the title keeps "(Official Video)". What I cannot verify: the true tempo and key, the chord names (beyond their consistency with each other and with the chroma), whether C# is real, the section names, and whether the strum patterns match the record.

## What to improve next

Ranked by benefit to the person reading the sheet, divided by effort. Sizes are rough hours including tests.

1. **Merge sections shorter than four bars before labelling, or print a run of short sections as one block.** Stage: grid (`boundaries_from_clusters` uses `min_bars=2`) or render. Evidence: Wet Leg has 17 of 25 sections under four bars and misses the page target (4 pages) only because of them; the three other songs have none, so the change cannot hurt them. Refutes the lessons' "merge sub-4-bar sections has no support here". Size: 2 to 4 h.
2. **Run the strike-threshold spike (spec section 7, lesson 5).** Stage: strums. Evidence: four printed boxes of 75% or more rests marked certain (Chelsea first chorus `--D---D-`, bridge and last chorus; Summer of '69 third chorus `D-------`), and Pour Some Sugar On Me has no box at all because every pattern is uncertain. Wet Leg's patterns are dense (0 to 38% rests), so the rule must leave a dense song alone: add it to the spike's song set. Confirms lesson 5. Size: 4 to 6 h for the spike, then 2 to 4 h to build.
3. **Collapse repeating multi-row blocks and align rows to the phrase.** Stage: render (row grouping only; `score.json` unchanged). Evidence: Chelsea prints alternating G and D rows (7 rows in the first chorus, 10 in the last) that would be two `×N` blocks; Summer of '69's first verse reads D A A D because the boundary is one bar into the two-bar rhythm. Would bring Chelsea and Summer of '69 to two pages. Size: 2 to 3 h.
4. **Title hygiene and the capo header line.** Stage: ingest (title) and render (header). Evidence: 4 of 4 titles repeat the artist, 3 of 4 carry "(Official ... Video)", and Def Leppard's artist is in capitals; the title is now the largest thing on the page. The capo part is fixed in this wave: with capo 4 the Key line now gives the shape key (A major (shapes)) beside "Sounding key: C# major". Confirms lesson 10. Size: 1 to 2 h.
5. **Fill N.C. where the stems show a band playing.** Stage: harmony. Evidence: Chelsea's intro, 9 bars N.C. with guitar and bass playing; Pour Some Sugar On Me's solo, 11 of 17 bars N.C. In the grid an N.C. row is now far more visible than it was on the staff. Confirms lesson 8 and extends it to a second song. Size: 2 to 3 h.
6. **Power chords and key mode.** Stage: harmony. Evidence: Pour Some Sugar On Me still reads C# major (truth C# minor). Confirms lesson 7. Size: 4 to 6 h.
7. **Header tempo from the mean beat interval.** Stage: grid. Evidence: Summer of '69 mean 138.6 against 139 (median 136.4); Pour Some Sugar On Me 84.9 against 85 (median 85.7); Wet Leg mean 128.0 is closer to librosa's 129.2 than the median 130.4. Confirms lesson 9. Size: 0.5 h.
8. **Name a block of novel chords a bridge; drop or recalibrate the chorus-margin flag.** Stage: grid. Evidence: Summer of '69's F Bb C bridge is still "verse 2"; the chorus margin is under 1.5 dB on all four songs (1.43, 0.70, 0.93, 0.75 dB) so every label carries confidence 0.3, yet all verifiable choruses are right. Confirms lesson 6 on this point. Size: 2 to 4 h.
9. **Do not give a passing chord a diagram.** Stage: arrange or score. Evidence: Wet Leg's C# (1.1% of the time, a barre shape) and Chelsea's B (0.7%, one event, a barre shape) each add a hard diagram for half a bar. Print such chords small in the cell without a diagram, or below a duration threshold fold them into the neighbour. Size: 1 to 2 h.
10. **Draw the pickup as the narrow leading cell the spec describes.** Stage: render. Evidence: Summer of '69 prints it as a one-bar-wide cell on its own row. Size: 0.5 to 1 h.

Also confirmed: lesson 2 (eight slots at 158 bpm gives grid fit 0.55 and section confidence 0.45 to 0.71, with 1 of 8 sections uncertain instead of 6), lesson 3 (the backbeat ratio is 2.06 to 2.14 on the three songs whose octave is right; the shipped calculation, mean flux per position class, gives slightly different values from the lessons' 2.12, 2.39 and 2.27 but the same decisions), lesson 4 (capo 4 for Pour Some Sugar On Me with the predicted 0.47 margin; new: Chelsea's capo 0 wins by only 0.11). The stretched last bar from the operational findings is fixed on all three re-runs.
