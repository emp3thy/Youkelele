# Lessons from the first three real-song runs

Date: 2026-10-03. Inputs: three completed runs from `main` (`runs\sexhetcxqy4`, `runs\9f06qzcvuhg`, `runs\0uib9y4ofps`), their logs (`chelsea_run2.log`, `batch2.log`, plus the earlier `real_run_sEXHeTcxQy4*.log` and `batch.log`), ground truth from `research_notes\gap_analysis\verification_web_pages.md` (sections 3, 4, 5 and 10) and the spike reports beside this file. Measurement scripts are in the session scratchpad under `lessons\` (`analyse.py`, `capo_key.py`, `diatonic.py`, `offset.py`, `stems.py`, `chel.py`, `bounds.py`, `slotfreq.py`, `fit8.py`, `backbeat.py`, `capo_rules*.py`, `raster.py`). No source file was changed.

## Summary

| Song | Tempo found / true | Key found / true | Sections right? | Chords right? | Strum fit | Slots | Pages | Verdict |
|---|---|---|---|---|---|---|---|---|
| Chelsea Dagger (The Fratellis) | 157.9 with `--beat-octave none` (auto gave 76.9) / about 155 to 158, not verified (the run's own mean beat interval gives 154.7) | D major / unverified: D major or G major, low confidence (audio key scores 0.766 vs 0.762) | Not verifiable. The first "chorus" starts 11 bars before the vocals enter. No section under 4 bars | Plausible G D C Bm Em A Am B, but 6 bars of the instrumental intro are N.C. | 0.40 (stage uncertain) | 16 (should be 8) | 15 | Chord names usable; strum staff unusable |
| Summer of '69 | 136.4 / 139 | D major / D major | 6 of 12 hand-list boundaries within 1 bar, 7 of 12 within 2. Choruses 3 of 3; bridge and intro both labelled "verse 2" | Yes: D A Bm G, plus F Bb C in the bridge, the published set exactly; 72 of 75 changes on bar starts | 0.91 | 8 | 10 | Best of the three. Chords and capo match the published chart; patterns half right |
| Pour Some Sugar On Me | 85.7 / 85 | C# major / C# minor (mode wrong) | 4 of 11 within 1 bar (after a 25.2 s alignment). Choruses 3 of 3; pre-chorus absorbed; no bridge | Mostly: E A B and F# B right; the C#m power-chord riff comes out as C# major; D (bridge) never detected | 0.60 (stage uncertain) | 16 (plausible) | 12 | Chords mostly right; capo 2 instead of 4; strum staff unusable |

## Per-song findings

### Chelsea Dagger (`sexhetcxqy4`, 229.4 s, music video upload)

**Grid.** The auto rule halved 157.9 to 76.9 (72 bars, median bar 3.10 s) on the first attempt, as the spec says it would for a real 141 to 190 bpm song. That attempt then crashed in harmony on the relative-path bug fixed in PR #2. The rerun with `--beat-octave none` gave 157.9 bpm, 566 beats, 142 bars: 141 bars of 4 beats plus a final 2-beat bar stretched from 219.36 to 229.41 s (10 s). Beats end at 219.74 s while the audio runs to 229.4 s. At 157.9 bpm the duration predicts 150.9 bars. The difference is the 10 s tail plus a tempo bias: the median beat interval is 0.38 s (157.9) but the mean is 0.388 s (154.7). No interval was more than 1.3 times the median, so no beats were dropped.

**Sections.** k 3, largest cluster share 0.58, chorus margin 1.29 dB, so the labels are flagged low confidence. There are 8 sections and none is shorter than 4 bars. From the vocal stem, the vocals are silent for bars 0 to 19 (about 30 s), present for bars 20 to 92, silent again for bars 93 to 108, and present from bar 109. The labeller calls bars 0 to 8 "verse" (an instrumental intro) and starts the first "chorus" at bar 9, eleven bars before any vocal. It splits the 16-bar vocal-free break into chorus (6), bridge (6) and the start of the final chorus. With no reference I cannot score the boundaries. The labels are visibly off at the start.

**Harmony.** 69 events. By time: G 34.2%, D 28.5%, N 10.3%, Em 8.1%, Bm 6.8%, C 4.7%, A 4.1%, Am 2.7%, B 0.7%. No sevenths, inversions or sus labels appear (every label equals its triad), so the easy tier changed nothing. 57 of 68 changes fall on beat 0 and 10 on beat 2. The intro is lost: N from 0.6 to 14.4 s (bars 0 to 8), although the stems show drums from the start, guitar at 0.44 of the mix RMS from 5 to 10 s and bass at 0.38 from 10 to 14 s. Key: D major with confidence 0.006. The audio Krumhansl scores are D major 0.766 and G major 0.762, a tie. The detected chords include C and Am, which fit G major (94.7% of chord time diatonic) slightly better than D major (91.0%). I have no published chart for this song. The key is D or G major, possibly D Mixolydian, with low confidence.

**Strums.** Guitar stem (ratio 0.39), 16 slots, grid fit 0.40, stage uncertain. 16 slots at 158 bpm means sixteenths of 95 ms (10.5 strokes a second), which is not plausible for a strummed part. The 16-slot choice came from 28% of onsets sitting nearer an odd sixteenth, just over the 25% rule. In the per-slot strike rates the strikes concentrate on the quarter positions (slots 0, 4, 8, 12), with beats 2 and 4 strongest (slot 4 at 78 to 100% of bars), which fits snare bleed into the guitar stem. Re-quantising the same onsets at 8 slots gives grid fit 0.55 instead of 0.40 and section confidence 0.45 to 0.71 instead of 0.22 to 0.52. Patterns at 16 slots: every section is 75 to 100% rests (the intro `----------------`, most choruses `----D-------D---`). 6 of 8 sections are flagged uncertain, and the two that are not (confidence 0.52 and 0.51) are 88% and 75% rests. No section inherited a pattern.

**Arrange.** Capo 0, no substitutions. G 0232, D 2220, A 2100, C 0003, Bm 4222, Em 0432, Am 2000, B 4322 (barre, 1 event). Reasonable shapes for the detected chords.

**Render.** 15 pages for 142 bars. Page 1 holds only the header and chord legend. Page 2 is nine bars of sixteen rests each (the N.C. intro). The middle page (8) is ten bars of a chorus that differ only by chord name, each showing two sixteenth strokes among fourteen rests. A ukulele player would first complain that 15 pages of mostly rests tell them nothing about how to strum, and that the sheet asks for sixteenths at 158 bpm.

### Summer of '69 (`9f06qzcvuhg`, 207.2 s, the same upload as the spikes)

**Grid.** 136.4 bpm against 139 (Hooktheory, Tunebat). Not halved, which is correct. 121 bars, including a 1-beat pickup bar at 0.02 to 0.44 s and a 1-beat final bar; the duration at 139 bpm predicts 120. The median beat interval is 0.44 s, which gives 136.4. The mean interval gives 138.6, within 0.4 of the published tempo. k 4, largest share 0.50, chorus margin 0.70 dB, labels flagged low confidence. 11 sections, none under 4 bars.

Boundaries against the owner's hand list for this upload: 6 of 12 within 1 bar and 7 of 12 within 2, with precision 6 of 10. This is the same as spike round 3 (6 and 8 of 12). Labels against Hooktheory's Verse / Pre-Chorus / Chorus / Bridge: the three pre-chorus-plus-chorus blocks (31.6, 69.8, 142.5 s) are all "chorus", which is right. The bridge (99.2 to 118.3 s, the F Bb C block) is labelled "verse 2", and so is the 4-bar guitar-only intro. The two landed in one cluster, which therefore counts as recurring, and the labeller names recurring non-chorus clusters "verse 2". The bridge label is lost. There is no pre-chorus label because pre-chorus and chorus fall in one cluster.

**Harmony.** 76 events, key D major (correct; confidence 0.056; audio scores D major 0.844 against A major 0.797). Chord set D A Bm G F Bb C, exactly the Ultimate Guitar and UkuTabs set. The sequence is right: verse D-A every two bars, chorus Bm A D G, bridge F Bb C Bb F Bb C. N covers 4.7%: 0.9 s at the start and 8.8 s of fade at the end, so the intro is not lost. 72 of 75 changes fall on bar starts. No sevenths or inversions appear.

**Strums.** Guitar stem (ratio 0.39), 8 slots (correct at 136 bpm), grid fit 0.91, stage not uncertain. Ultimate Guitar publishes a muted all-down eighth chug for the intro and verse. The run gives intro `D-xx-xxx` (confidence 0.65) and verse `xxxU-xxx` (0.64): six of eight slots muted, close to the chug. The `U` is the direction rule (odd slot means up), not something heard. Choruses come out as `D-DU--D-` (0.61), `D-------` (0.39, uncertain) and `D-------` (0.53, not uncertain). The record strums through its choruses, but the detector finds only 1.8 to 3.9 strikes per bar there (6.1 in the verse), and the majority vote then keeps only beat 1. In the last chorus slot 0 is struck in 83% of bars and every other slot in 25% or fewer. 4 of 11 sections are uncertain and 4 of 11 patterns are 75% or more rests. The outro has confidence 0.15. No section inherited a pattern.

**Arrange.** Capo 0, D 2220, A 2100, Bm 4222, G 0232, F 2010, Bb 3211, C 0003, as published and as the arrange spike predicted. No substitutions. The margin is thin: capo 0 scores 1.73 against 1.82 for capo 2.

**Render.** 10 pages for 121 bars. Page 1 has the header, legend and the 4-bar "verse 2" intro (the 1-beat pickup is drawn as a full 4/4 bar with strokes), then two thirds blank. Page 2 is the verse, one bar per system because the dead-slap X glyphs are wide: ten identical bars apart from D/A. The middle page (6) is the bridge, labelled "verse 2", eleven bars of `D--U----` with an uncertain badge, and the page is half empty. A ukulele player would complain first about length: ten pages for a song that UkuTabs fits on one screen.

### Pour Some Sugar On Me (`0uib9y4ofps`, 295.5 s, the music video upload)

**Upload.** This run used the music video (`0UIB9Y4OFPs`, 295.5 s). The spikes used the album audio (`Rqs4cMyMLnY`, 267.3 s). Chroma cross-correlation at seven points shows the video is the album audio offset by +25.2 s (similarity 0.97 to 0.98). The first 25 s are video pre-roll. The hand list was shifted by 25.2 s for scoring.

**Grid.** 85.7 bpm against 85 (mean interval 84.9). Not halved, which is correct. 103 bars: 102 of 4 beats plus a final 2-beat bar stretched to 7.1 s. k 3, largest share 0.49, chorus margin 0.77 dB, labels flagged low confidence. 7 sections, none under 4 bars. Boundaries: 4 of 11 within 1 bar (and within 2), with precision 4 of 6. That is slightly better than spike round 3 (3 of 11) on the album audio. The riff at 31.3 s, verse 2 at 110.4 s and solo at 189.5 s land exactly. The chorus at 79.3 s is 1 bar early because it swallows the pre-chorus. Chorus 2 at 155.6 s is 2 bars late, and the outro at 237.5 s is 3 bars late. Labels against Hooktheory's Verse / Pre-Chorus / Chorus / Bridge: intro, verse and chorus are named, and all three choruses are right. There is no pre-chorus and no bridge.

**Harmony.** 83 events. Key C# major with confidence 0.0096. The truth is C# minor (Tunebat, Ultimate Guitar tonality field) or E major for the chorus (Hooktheory). The audio scores are C# major 0.550 and C# minor 0.544, a tie decided the wrong way. By time: C# major 29.4%, N 28.8%, B 18.2%, E 12.7%, A 8.8%, F# 1.9%, C#m 0.2%. The verse riff is a no-third power chord (Hooktheory draws I(no3)), and the model reads it as C#:maj, which pulls the key to major. Chorus E A B and pre-chorus F# B match the Ultimate Guitar chart. D (the Hooktheory bridge, VII to I) is never detected. Much of the 28.8% N is musically right:

- 8 s of video pre-roll.
- The a cappella intro.
- Both verses, which Ultimate Guitar marks "N.C.": the vocal and drum stems dominate there and the guitar stem is at 0.02.
- The drum-and-voice breakdown.

About 26 s around the solo (184.6 to 212 s, guitar stem 0.25 to 0.34) is doubtful. Only 47 of 82 changes fall on bar starts (25 on beat 2). The chorus moves E-A on beats 1 and 3 and B on the next bar, which is how Ultimate Guitar writes it, so this is not an error. 22 events last 2 beats or less. No sevenths or inversions appear.

**Strums.** Guitar stem (ratio 0.29), 16 slots (44% of onsets nearer odd sixteenths; plausible at 85 bpm), grid fit 0.60, stage uncertain, all 7 sections uncertain. Patterns: verses `-------U--------` (confidence 0.15), `---------------U` (0.08); choruses `D---D---D---D--U` (0.42), `------------D---` (0.12). 4 of 7 patterns are 88% or more rests, although the bars average 3.4 to 7.7 detected strikes. As in round 1, this guitar stem does not support pattern inference.

**Arrange.** Capo 2 with transpose -2. Shapes: B 4322 (barre, for C#), E 1402 (for F#), A, D, G, Bm. The spike expected capo 4 (Am C G F). Even with C# read as major, capo 4 gives all-open shapes: A for C#, C for E, G for B, F for A, D for F#, at a mean shape cost of 1.13 against 1.73 for capo 2. The capo penalty (0.3 per fret plus 0.3 per fret above 3) adds 1.5 at capo 4 against 0.6 at capo 2, and that decides it. With C# corrected to minor, the current rule still picks capo 2 (2.33 against 2.56). The header reads "Key C# major, Capo fret 2", and the legend shows B E A D G Bm with no note that these are shapes relative to the capo.

**Render.** 12 pages for 103 bars. Page 1 is header and legend only. Page 2 is the intro: N.C. bars draw rests while the token line under them still reads `U D U D D D`. On the middle page (7), bar 52's token line overlaps bar 53's staff, and the page is three-quarters empty because the next section starts a new page. A ukulele player would complain first about the verse: a page of `-------U--------` over C# barre shapes, which neither sounds nor looks like the song.

### Timing (seconds, from manifest finish times)

| Song (audio) | ingest | separate | grid | harmony | strums | arrange | score | render | total |
|---|---|---|---|---|---|---|---|---|---|
| Chelsea (229 s) | not logged | 116.5 | 13.4 | 12.6 | 2.8 | 0.1 | 0.0 | 1.3 | 147 after ingest |
| S69 (207 s) | about 4 | 93.3 | 6.5 | 9.5 | 1.7 | 0.2 | 0.0 | 1.5 | 117 |
| PSSOM (295 s) | about 9 (one 403 retry) | 135.4 | 8.9 | 12.0 | 2.0 | 0.2 | 0.1 | 1.6 | 169 |

Separation runs at 0.45 to 0.51 times real time, twice as fast as the 248 s for 240 s the spec measured, and is 76 to 84% of the run. Everything after harmony takes under 5 s, so iterating on strums, arrange, score and render with `--from 4` is cheap.

## Ranked lessons and proposed changes

Ranked by benefit to the person reading the sheet, divided by effort. Sizes are rough implementation hours, including tests.

1. **Render a chord grid, not a bar-per-strum slash staff, and drop the staff where the pattern is uncertain or mostly rests.** Stage: score and render.
   - Evidence: 10 to 15 pages for 103 to 142 bars. Page 1 is header-only on 2 of 3 songs, each section forces a page break, and the X-glyph verse runs one bar per system.
   - Within a section every bar repeats the section pattern, so bars differ only by chord name. Unique bar signatures are 31 of 142, 34 of 121 and 27 of 103.
   - 16 of 26 section patterns are 75% or more rests. Chelsea page 2 is nine bars of rests.
   - Proposal:
     - Draw each section as its pattern box once, followed by a chord grid (four or eight bars per line, `%` or "x4" for repeats).
     - Keep the slash staff only for confident patterns, or behind a flag.
     - Stop forcing a page break per section.
     - Print N.C. bars without tokens.
     - Fix the token-line overlap seen on PSSOM page 7.
     - Draw the 1-beat pickup bar as a pickup.
     - Expected: 1 to 3 pages per song.
   - Size: 8 to 12 h.
2. **Cap slots per bar by tempo.** Stage: strums.
   - Evidence: Chelsea at 157.9 bpm got 16 slots (95 ms sixteenths) on a 28% odd-sixteenth share. The same onsets at 8 slots give grid fit 0.55 instead of 0.40 and section confidence 0.45 to 0.71 instead of 0.22 to 0.52 (1 to 2 uncertain sections out of 8, against 6).
   - The cap changes neither other song: S69 at 136 bpm already picks 8, and PSSOM at 86 bpm keeps a plausible 16.
   - Proposal: allow 16 only when a sixteenth lasts at least about 105 ms (bpm at or below about 140), and raise the odd-sixteenth threshold above 25%.
   - Size: 1 h.
3. **Add a drum backbeat test to the auto tempo-octave rule rather than narrowing the band.** Stage: grid, which would then require `separate/stems/drums.wav`. Separate already runs before grid.
   - Evidence: narrowing the band cannot work. Chelsea (157.9, correct) sits between I'm Yours (150, doubled) and Over the Rainbow (166.7, doubled).
   - Measured the drum stem's 1.5 to 6 kHz spectral-flux strength on beats 2 and 4 over beats 1 and 3 of the detected grid:

     | Song | Grid bpm | Octave | Backbeat ratio |
     |---|---|---|---|
     | Chelsea Dagger | 157.9 | correct | 2.12 |
     | Summer of '69 | 136.4 | correct | 2.39 |
     | Pour Some Sugar | 85.7 | correct | 2.27 |
     | Riptide | 103 | correct | 0.86 |
     | I'm Yours | 150 | doubled | 0.57 (snare peak on beat 3) |
     | Over the Rainbow | 166.7 | doubled | 0.19, no drums (stem RMS 0.001) |

   - Proposed rule: halve only if bpm > 140, the half lies in 60 to 95, and either the backbeat ratio is below 1 or the drum stem is silent. It is right on all 6 songs.
   - Size: 3 to 4 h.
4. **Re-weight the capo score.** Stage: arrange.
   - Evidence: PSSOM got capo 2 (a B barre for its most-used chord, 29% of the time) over all-open capo 4, because the penalty of 0.3 per fret plus 0.3 per fret above 3 outweighs a 0.6 lower mean shape cost. S69's correct capo 0 wins by only 0.09.
   - Tested on the three run chord streams plus the spike's S69 list, its PSSOM list and C-G-Am-F. Only two of seven variants got all six right (Chelsea 0, S69 0, PSSOM 4, spike S69 0, spike PSSOM 4, C-G-Am-F 0):
     - Mean shape cost over unique labels plus 0.2 per capo fret: S69 margin 0.33, PSSOM margin 0.47.
     - Square-root-count-weighted mean with the current penalty: PSSOM margin 0.01, too fragile.
   - The current rule, a time-weighted mean, and mean plus 0.15 per fret each fail at least one.
   - Proposal: unique-label mean plus 0.2 per capo fret. Also show "shapes relative to capo" and the sounding key in the header.
   - Size: 1 to 2 h.
5. **Stop the slot-wise majority vote from erasing strikes.** Stage: strums.
   - Evidence: 16 of 26 patterns are 75% or more rests, while their bars average 1.8 to 7.7 detected strikes. S69's final chorus becomes `D-------` (slot 0 struck in 83% of bars, the rest in 25% or fewer), even though the record strums throughout.
   - The confidence score does not catch this. Chelsea sections at 0.51 and 0.52 and the S69 chorus at 0.53 are "certain" with 75 to 88% rests, because Jaccard ignores slots where both vectors rest.
   - Proposal, to be measured on the five spike songs before adopting:
     - Lower the strike threshold to about 35 to 40%.
     - Report the strike density alongside the pattern.
     - Mark as uncertain any pattern whose strike count is under half the section's mean strikes per bar.
   - Size: 4 to 6 h.
6. **Recalibrate or drop the 1.5 dB chorus-margin flag, and name once-only harmonic blocks by chord novelty.** Stage: grid.
   - Evidence: the margin was under 1.5 dB on all three songs (1.29, 0.70, 0.77), so every label got confidence 0.3. Yet 6 of 6 verifiable choruses were right.
   - The 60% split rule never bound (largest shares 0.58, 0.50, 0.49). It neither helped nor hurt, so I would leave it alone.
   - No section was under 4 bars on any song. The "merge sub-4-bar sections" candidate has no support here, so I would not do it.
   - The real labelling miss is S69's bridge. Its F Bb C chords occur nowhere else, but it clustered with the guitar-only intro and became "verse 2".
   - Proposal: a segment whose chord set is mostly absent from the rest of the song is a bridge, whatever its cluster.
   - Size: 2 to 4 h, mostly measurement.
7. **Represent power chords and use them in key estimation.** Stage: harmony.
   - Evidence: PSSOM's key came out C# major against true C# minor. The audio scores are 0.550 against 0.544, and the chord model labels the no-third riff C#:maj.
   - Key-from-chords alone does not fix it. Strict diatonic chord-time picks F# major for PSSOM. Root-only matching picks E/C#m for PSSOM but G major for S69.
   - With the C# chord relabelled as a power chord (C#5), strict diatonic chord-time would give about 97% for E/C#m against 70% for F# major (worked by hand, not run).
   - Proposal: flag a major triad as a power chord when its chroma third is weak against its fifth. Let the key's diatonic quality decide what the easy tier prints (C#m here, matching the published chart). Then estimate the key from chord time.
   - Size: 4 to 6 h.
8. **Recover intro chords the model leaves blank.** Stage: harmony.
   - Evidence: Chelsea's first 14.4 s (9 bars) are N.C., though guitar and bass are present from about 5 s. That is about 6 bars lost.
   - S69's intro is fine. PSSOM's long N stretches are mostly genuine N.C.: the pre-roll, the a cappella intro, the N.C. verses and the breakdown.
   - Only one song shows the problem, so keep the fix narrow: where harmony says N but the bass plus guitar/other stems are above about 0.2 of the mix, take the first confident chord after the gap, or print "riff" rather than N.C.
   - Size: 2 to 3 h.
9. **Header tempo from the mean beat interval.** Stage: grid.
   - Evidence: the median of 20 ms-quantised intervals gave 136.4 for S69 (true 139) and 85.7 for PSSOM (true 85). The mean interval gives 138.6 and 84.9.
   - Size: 0.5 h.
10. **Ingest: version and title hygiene.** Stage: ingest.
    - Evidence: the PSSOM music video adds 25.2 s of pre-roll to the album audio, which became an "intro" section with N.C. and chords.
    - Titles come through as "Bryan Adams - Summer Of 69 (Official Music Video)" and artist "DEF LEPPARD".
    - Proposal: strip "(Official ... Video)" and a leading "Artist - " from the title. Print a hint in the log when the title says "Video", recommending the album or "Provided to YouTube" upload.
    - Size: 1 to 2 h.

## Operational findings

- `python -m youkelele.cli run ...` exits 0 in about 1 s and does nothing, because `cli.py` has no `if __name__ == "__main__"` guard and the package has no `__main__.py`. The first worktree batch (`batch.log`) "finished" both songs in 1 s this way. `youkelele.exe` works.
- The yt-dlp `HTTP Error 403: Forbidden` on PSSOM was retried by `models/ytdl.py` (3 attempts) and the run succeeded. In `batch2.log` it appears after `[07] render` only because `batch2.py` writes stdout and then stderr. Ordering in that log is not chronological.
- `[opus @ ...] Error parsing Opus packet header.` comes from ffmpeg during conversion on all three songs. It is harmless: S69's converted WAV is 207.25 s, the same as the spike's ffprobe.
- The first Chelsea attempt failed in harmony with the chord model unable to open a relative path. PR #2 fixed this (resolving run-folder paths before subprocesses).
- The last bar of every song is stretched to the end of the file (Chelsea 10 s, PSSOM 7.1 s, S69 0.7 s), and S69 starts with a 1-beat pickup bar. Both are drawn as full 4/4 bars.
- The stage prints "N bpm detected, octave X" and the median bar length. This did make the wrong halving on Chelsea obvious (3.10 s bars), as the spec intended.
- Separation dominates runtime (93 to 135 s). Stages 4 to 7 together take under 5 s, so the fixes above can be iterated on the existing run folders with `--from strums` without re-separating.
