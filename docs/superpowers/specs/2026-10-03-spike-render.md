# Spike: arrangement heuristics, alphaTex edge cases, printed sheet prototype

Date: 2026-10-03. De-risks plan Tasks 11, 12 and 13 of `2026-10-03-ukulele-tab-chain.md` before coding starts. Everything below was run, not reasoned: alphaTab 1.8.4 (npm tarball, `dist/alphaTab.min.js`) in headless Chromium 153 via Playwright for Python 1.63.0, from `file://` with `core.useWorkers: false`; chords-db `lib/ukulele.json` (552 chords); PDF pages rasterised with PyMuPDF 1.28 for inspection.

Scratch files (scratchpad `spike_render/`, not committed): `spike1_arrange.py`, `spike1_variants.py`, `spike1_final.py` (+ `.txt` outputs); `render_tex.py` (tex -> html -> png harness), `dump_lyrics.py` (reads the alphaTab model to see which beat got which lyric), `tex/*.tex` cases a to n with `.png` renders; `sheet_proto.html`, `pdf_proto.py`, `pdf_variants.py`, `sheet_proto_*.pdf` and page PNGs.

## Confidence changes

| Task | Before | After | Why |
|---|---|---|---|
| 11 Arrange | 80% | 88% | The two real songs exposed two heuristic bugs (capo penalty not normalised; voicing Viterbi inconsistent). Both fixed and re-run with the exact weights below; shape choices now match the published UkuTabs/e-chords charts. Still untested on a real detected chord stream with noise. |
| 12 Score / alphaTex | 85% | 92% | Every edge case renders; the one wrong assumption (the `\lyrics` line) is replaced by a verified per-beat form; absolute-fret rule for `firstfret` and the barre syntax are confirmed; the chord-change slot rule is defined and rendered. |
| 13 Render | 80% | 90% | Prototype printed to a 6-page A4 PDF with clean section breaks, legible diagrams and arrows; the reflow question is answered (fix the width). Open: real-world sheets with very long sections, and a one-bar-per-line cost for 16-slot bars. |

---

## Spike 1: arrangement heuristics against real songs (Task 11)

### Question
Do `shape_cost`, `score_capo`/`choose_capo`, `select_voicings` and `simplify_for_tier` as specified in Task 11 give a beginner the shapes a ukulele player would expect for Summer of '69 (D major) and Pour Some Sugar On Me (C#m)?

### What was run
`spike1_arrange.py` implements the Task 11 functions exactly (HARTE_TO_SUFFIX, ROOT_TO_DB_KEY, ShapeDB over `ukulele.json`, `shape_cost` = 1.5 barre + 0.4 per fretted string + 0.6*(base_fret-1) + 0.5*span, `score_capo` = sum of min shape_cost per label transposed down by capo + 2.0*capo + 5.0 per label without a shape, `choose_capo` over 0..5, Viterbi `select_voicings` with 0.3*movement, `simplify_for_tier`). Chord lists from the research notes (verification_web_pages.md sections 3, 4, 5, 10; tablature_theory_and_strumming.md):

- Summer of '69, D major, UkuTabs/UG "no capo": verse D A (x12 events), pre-chorus/chorus Bm A D G (x4), bridge F Bb C Bb F Bb C C. 48 events.
- Pour Some Sugar On Me, C#m/E: verse C#m (x8), pre-chorus F# C#m B (x2) then E B A E A B, chorus E A B (x6), C#m. 40 events.

### Results

Capo score tables, plan weights as written (sum over all events):

| Song | capo 0 | 1 | 2 | 3 | 4 | 5 | chosen | wanted |
|---|---|---|---|---|---|---|---|---|
| Summer of '69 (D) | 64.3 | 129.2 | **57.8** | 110.2 | 107.4 | 70.4 | 2 | 0 |
| PSSOM (C#m) | 115.6 | 102.4 | 94.6 | 152.2 | **45.8** | 135.0 | 4 | 4 (see below) |

Summer of '69 is wrong: with 48 events the flat `2.0*capo` is noise against the summed costs, and because the verse is D-A over and over, capo 2 (C-G) beats D-A by 0.14 per event. The plan's own test `test_choose_capo_zero_for_c_g_am_f` would pass while real songs fail. Normalising by the number of events fixes it:

| Rule | S69 (D) | PSSOM (C#m) | Eb Bb Cm Ab | C G Am F | Bb F Gm Eb | E A B |
|---|---|---|---|---|---|---|
| plan: sum + 2.0*capo | capo 2 (wrong) | 4 | 3 | 0 | 3 | 2 |
| plan weights on unique labels | 0 | 4 (13.0 vs 13.9 capo 1, fragile) | 3 | 0 | 1 | 0 |
| mean per event + 0.35*capo | 0 | 4 | 3 | 0 | 1 | 2 |
| **mean + 0.3*capo + 0.3 per fret above 3** | **0** (1.79 vs 2.09) | **4** (2.44 vs 2.81 capo 1, 2.89 capo 0) | **3** (1.85) | **0** (0.95) | 1 (2.00 vs 2.27 capo 3) | 2 (2.00) |
| mean + 0.5*capo | 0 | 0 (2.89 vs 2.94) | 3 | 0 | 1 | 2 |

Full FINAL table (mean cost + 0.3*capo + 0.3 per fret above 3, plus the finger term below):

| Song | c0 | c1 | c2 | c3 | c4 | c5 | chosen |
|---|---|---|---|---|---|---|---|
| S69 (D) | **1.79** | 3.99 | 2.13 | 3.96 | 4.33 | 3.81 | 0 |
| PSSOM (C#m) | 3.05 | 2.89 | 2.87 | 4.73 | **2.44** | 5.46 | 4 |
| Eb Bb Cm Ab | 2.75 | 2.38 | 4.53 | **1.85** | 4.83 | 4.55 | 3 |
| C G Am F | **0.95** | 3.62 | 3.05 | 2.62 | 4.62 | 3.48 | 0 |
| Bb F Gm Eb | 2.45 | **2.02** | 3.73 | 2.27 | 5.30 | 3.98 | 1 |
| E A B | 2.70 | 3.57 | **2.00** | 4.77 | 2.63 | 5.53 | 2 |

Shapes chosen (G C E A, absolute frets), final rules:

- Summer of '69, capo 0: D 2220, A 2100, Bm 4222 (barre 2), G 0232, F 2010, Bb 3211 (barre 1), C 0003. Identical to the UkuTabs and ukulelearn charts (Bm "a barre chord at fret 2"). A beginner gets the published sheet; the two barres are unavoidable in D.
- Pour Some Sugar On Me, capo 4: Am 2000, D 2220, G 0232, C 0003, F 2010. This is exactly the e-chords/ukulele-tabs uke chord set (Am D F C G) and the UG acoustic chart with the commenter's "capo 4 to match the original". Without a capo the song is C#m 1444, F# 3121, B 4322 (barre), E 1402 or 4442, A 2100: three hard shapes for a beginner. So the scorer's capo 4 is what a player wants. Capo 4 is unusual on a ukulele, hence the extra 0.3 per fret above 3; it still wins here by a clear 0.37 over capo 1 because the saving is large (mean cost 2.89 -> 1.24). The sheet should say "Capo 4 (or play the shapes without a capo in Am, a major third lower)" so the player can choose.
- `select_voicings` on C G Am F G7 C: 0003, 0232, 2000, 2010, 0212, 0003 (correct).

Two voicing problems with the plan's Viterbi (0.3*movement, per-event states):

1. PSSOM at capo 4 chose F = 2013 instead of 2010, because 0003 -> 2013 -> 0003 moves 3+3 frets versus 6+6 for 2010 and 0.3*6 outweighs the 0.9 cost difference. 2013 is a legal F but no beginner chart uses it.
2. PSSOM at capo 0 switched E between 1402 and 4442 within one song (two "E" diagrams would appear in the legend).

Variants run (`spike1_variants.py`): movement weight 0.1 fixes 1 but not 2; counting movement only on strings fretted in both shapes fixes 1 but not 2; **one shape per label for the whole song** (coordinate descent over the distinct labels, cost = shape_cost*count + w_move*movement over adjacent pairs) fixes 2, and with w_move 0.1 fixes both. Final voicings: S69 as listed above; PSSOM capo 4 Am 2000, D 2220, G 0232, C 0003, F 2010; PSSOM capo 0 C#m 1444, F# 3121, B 4322 barre, E 1402, A 2100.

`shape_cost` ranking (final, with finger term): C 0.4, Am 0.4, D 1.2, F 1.3, A 1.3, G 1.7, Em 2.2, Gm 2.2, Eb 2.2, E 2.7, C#m 3.5, F# 3.5, Bb 4.1, Bm 4.1, B 4.1. The plan's weights put E 4442 at 2.6, below Em; the four-finger cram is harder than that, hence the term `+0.4 * max(0, distinct fingers - 3)` (uses chords-db `fingers`).

`simplify_for_tier` (plan rules, unchanged, all sensible):

| Label | easy | full |
|---|---|---|
| A:min/b3 | A:min "Am" (easy tier: reduced to triad) | A:min/b3 "Am" (bass dropped by harte_to_db) |
| D:sus4(b7) | D:sus4 "Dsus4" | D:sus4(b7) "D7sus4" |
| E:aug7 | E:aug "Eaug" | E:aug "Eaug" (no shape in chords-db for aug7) |
| G:7 | G:maj "G" | G:7 "G7" |
| B:hdim7 | B:dim "Bdim" | B:hdim7 "Bm7b5" |
| C#:maj/3 | C#:maj "Db" | "Db" |

Note the display name for C# comes out as "Db" because ROOT_TO_DB_KEY maps to the chords-db key before display. For a song in C#m the player expects "C#m" not "Dbm": `display_name` should take the original root spelling (sharps when the key has sharps) and only use the Db key for the lookup. Also `to_triad` needs an entry for `aug7 -> aug` (mir_eval raises on `aug7`; the plan already says keep the label when it raises, but then the triad fallback must still find `aug`).

Harte "submission" vocabulary (24 qualities + inversions) -> chords-db suffix, all verified present for every root (`shapes(C)` count in brackets): maj->major(4), min->minor(4), aug->aug(4), dim->dim(4), maj7->maj7(4), 7->7(4), min7->m7(4), hdim7->m7b5(4), dim7->dim7(4), maj9->maj9(4), 9->9(4), min9->m9(4), 11->11(**1**), 13->13(4), sus4->sus4(4), sus2->sus2(4), sus4(b7)->7sus4(4); the inversions maj/3, maj/5, maj/2, maj/b7, min/b3, min/5, min/2, min/b7 drop the bass and map to major/minor. **Every submission quality has a chords-db entry**; the only quality with no entry is `aug7` (not in the submission list but in the "full" list; chords-db has `aug7` as a suffix name but HARTE_TO_SUFFIX lacks it, so add `"aug7": "aug7"`, which makes the "no shape for aug7" test case need a different quality, e.g. `7(#9)` or `min11`). chords-db suffixes with no Harte mapping (fine to ignore): 13b5b9, 13b9, 69, 7#9, 7b5, 7b9, 7b9#5, 9#11, 9b5, add9, alt, aug7, aug9, b13#9, b13b9, m11, m69, m9b5, madd9, maj11, maj13, maj7#5, maj7b5, mmaj11, mmaj7b5, mmaj9.

### Recommended plan changes (Task 11)

1. `score_capo(labels, capo, db)` = **mean** over events of min `shape_cost` (5.0 for a label with no shape) `+ 0.3 * capo + 0.3 * max(0, capo - 3)`. Keep `max_capo = 5`. Tests: S69 list -> capo 0; PSSOM list -> capo 4; Eb Bb Cm Ab -> 3; C G Am F -> 0.
2. `shape_cost` += `0.4 * max(0, len({f for f in fingers if f > 0}) - 3)`.
3. Replace the per-event Viterbi with `select_voicings` that assigns **one shape per distinct label** for the whole song: start each label at its cheapest shape, then iterate (at most 5 passes) choosing for each label the shape minimising `shape_cost * count + 0.1 * sum(movement to the neighbouring labels' current shapes)`; movement = sum of absolute fret differences on strings fretted or open in both shapes (muted ignored). Test: PSSOM-capo-4 list gives F = 2010; a list containing E twice gives one E shape.
4. `display_name` keeps the caller's root spelling (`C#m`), lookup uses `ROOT_TO_DB_KEY`.
5. Add `"aug7": "aug7"` to HARTE_TO_SUFFIX and `aug7 -> aug` to the triad table; pick `E:min11` for the "unknown quality" test.
6. Arrangement header text: when capo > 0 also state the no-capo alternative key ("shapes shown are in Am; play with capo 4 to match the recording").

---

## Spike 2: alphaTex edge cases (Task 12)

### Question
Does the Task 12 alphaTex form survive mid-bar chord changes, one-slot chords, 16 slots, rests under lyric tokens, section markers, capo, high-position and barre diagrams and 3/4?

### What was run
`render_tex.py` wraps a `.tex` file in the verified no-workers `file://` page (classic `<script src="alphaTab.min.js">`, `core: {tex: true, useWorkers: false}`, `player: {playerMode: 0}`, optional `notation` settings from a `.settings.json` sidecar), waits for `renderFinished` + `document.fonts.ready`, screenshots. `dump_lyrics.py` reads `api.score` to list, per beat, rest/dead-slap state, chord name and the lyric actually attached. Cases `tex/a_*.tex` to `n_*.tex`, all rendered with zero diagnostics after the fixes below.

### Results

| Case | Result |
|---|---|
| a: chord change at slot 3 of 8 with `{ch "G"}` on that beat | Renders; "G" sits above beat 4, the earlier "C" above beat 1. |
| b: `:16`, 16 slots | Renders with 16th beams; one bar per line at 900px width. |
| c: one-slot chord (`G` on slot 3, `C` back on slot 5, `F` on slot 7) | Renders; three names above the right beats. |
| d: `\lyrics "D - D U - U D U"` over a bar with rests | **Wrong.** alphaTab's `Track.applyLyrics` skips `isRest`/`isEmpty` beats when spreading chunks, so tokens shift left ("-" lands under a played beat) and the last tokens fall off the bar. Also every `\lyrics` directive creates a new lyric *line* starting at bar 1, so "one `\lyrics` per bar" stacks N rows under bar 1. The rendering check's "rests consume a token" statement is false. |
| j1: single `\lyrics` with tokens only for non-rest beats | Aligns (dead-slap `(){ds}` beats do take a token), but depends on this skipping behaviour and on one line for the whole song. Not recommended. |
| **j2: per-beat `{lyrics "D"}` property, including `r{lyrics "-"}` and `(){ds lyrics "x"}`** | **Correct.** Dump: `n[D]{C} r[-] n[D] n[U] r[-] n[U] n[D] n[U]` and `n[D]{G} n[U] X[x] n[U] ...`; render shows one token centred under every slot, rests and chunks included. Used in the Spike 3 prototype for 64 bars with no errors. |
| j3: per-beat `{txt "D"}` | Also aligns (text above the beat) but collides with the chord names and tempo above the staff. Use `lyrics`. |
| e1: `\section "Verse 1"` + `\tempo 100` + `{ch "C"}` on bar 1 | Marker text overprints the tempo glyph and **hides the chord name "C"** (the marker is drawn in the chord-name row). Not merely cosmetic. |
| e2: without `\tempo` | Marker still hides the chord name. |
| e3: `\section "A" "Verse 1"` | Renders "[A] Verse 1", same collision. |
| e4: `notation.elements.effectTempo: false` | Tempo gone, chord name still hidden under the marker. |
| n: `\section` on a bar whose first beat has no `{ch}` | No collision (marker sits where the chord name would be). |
| **m: `notation.elements.effectMarker: false` and `effectTempo: false`** | Markers and tempo hidden, chord names visible, no overlap. |
| f: `\capo 2` | Renders "Capo. fret 2" under bar 1 (overlaps the first lyric token slightly); diagrams unchanged (shapes are relative to the capo, as wanted). Hide with `notation.elements.effectCapo: false` if the HTML header carries the capo. |
| g: `{firstfret 3}` | **Frets must be absolute.** `\chord ("C" 3 3 4 5) {firstfret 3}` draws dots in rows 1-3 with "3" beside the first row and the relative numbers "3 2 1 1" above; `\chord ("C" 1 1 2 3) {firstfret 3}` draws "-1" labels and no dots. Barre likewise absolute: `{firstfret 3 barre 3}` correct, `{firstfret 3 barre 1}` draws a bar above the grid. |
| h: barre syntax | `{barre 1}` and `{barre (1)}` render identically (bar across the strings whose fret equals 1); `{barre 2}` on Bm 4222 spans C E A. Muted string `x` in `\chord ("Fm" x 1 0 1)` draws "x" over the A string. Option names in 1.8.4: `firstfret`, `barre`, `showdiagram`, `showfingering` (the docs' `showfingers` is not accepted), `showname`. |
| i: `\ts 3 4` with six `:8` slots | Renders 3/4 with six eighths per bar. |
| k: two chord changes one slot apart (`G` slot 3, `Am` slot 4), change on the last slot, `:16` bar with a change at slot 6 | All render. |

Exact per-bar form that worked (8 slots, island strum on C with a change to G at slot 3):

```
\ts 4 4
:8 (3.1 0.2 0.3 0.4){bd ch "C" lyrics "D"} r{lyrics "-"} (3.1 0.2 0.3 0.4){bd lyrics "D"} (2.1 3.2 2.3 0.4){bu ch "G" lyrics "U"} r{lyrics "-"} (2.1 3.2 2.3 0.4){bu lyrics "U"} (2.1 3.2 2.3 0.4){bd lyrics "D"} (2.1 3.2 2.3 0.4){bu lyrics "U"} |
```

Chunk slot: `(){ds lyrics "x"}`. Chord definitions (after `\tuning (A4 E4 C4 G4)`), frets listed A E C G, absolute:

```
\chord ("Bb" 1 1 2 3) {barre 1}
\chord ("C/5" 3 3 4 5) {firstfret 3 barre 3}
\chord ("Fm" x 1 0 1)
```

Chord-change slot rule (defined here, rendered in case k): `start_slot = round((event.start - bar.start) / bar_len * slots_per_bar)` clamped to `[0, slots_per_bar - 1]`; an event whose rounded start equals the previous chord's start in the same bar replaces it (the earlier one lasted under half a slot); every chord therefore lasts at least one slot; an event whose rounded start lands on `slots_per_bar` belongs to the next bar at slot 0. Events that round away entirely are recorded nowhere in the score but remain in `chords.json`.

### Recommended plan changes (Task 12)

1. `alphatex.py`: drop the per-bar `\lyrics "..."` line. Emit the direction token as a beat property on **every** beat: `{bd ch "C" lyrics "D"}`, `{bu lyrics "U"}`, `r{lyrics "-"}`, `(){ds lyrics "x"}`. Update the "must reproduce the two-bar example" test to this form (the rendering report's B1 example is superseded).
2. Diagram frets: emit `fret + base_fret - 1` for fretted strings when `base_fret > 1`; barre values likewise `barre + base_fret - 1`; muted strings as `x` in `\chord` (they are omitted from the note group as planned).
3. Keep `\section "<label>"` in the alphaTex (it is correct data), but the render page sets `notation.elements.effectMarker: false` so it never hides a chord name; the HTML heading shows the section. Likewise `effectTempo: false` (tempo in the header), and `effectCapo: false` if `\capo` is emitted.
4. Add the slot rule above to `score_builder.py` with tests: change at 3/8 of the bar -> slot 3; two events rounding to the same slot -> later wins; an event of 0.3 slot at the bar end -> next bar slot 0.
5. Tests to add: `test_alphatex_firstfret_uses_absolute_frets`, `test_alphatex_every_beat_has_lyrics_token`.

---

## Spike 3: printed sheet prototype (Task 13)

### Question
Does a page built as Task 13 describes (header, inline-SVG diagram legend, SVG strum boxes, one slash staff per section, print CSS) print to A4 with clean breaks and legible diagrams, and does alphaTab reflow under print media?

### What was run
`sheet_proto.html`: header block (title, artist, key, capo, tempo, tuning, tier, meter, "uncertain" badge, "Strum detected from full mix" note); legend of eight hand-rolled 80x100 SVG diagrams (open C 0003 with finger 3, G 0232 with fingers 1 3 2, Am, F, Bb 3211 barre at 1, D 2220, C at base fret 3 with "3" label and barre, muted x210); strum boxes (28px per slot, labels `1 & 2 & 3 & 4 &`, `1 e & a ...`, `1 & 2 & 3 &`, down arrow, up arrow, crossed arrow for x, nothing for -); eight 8-bar sections (one 16-slot) plus a standalone 3/4 box; one whole-song alphaTex (64 bars, per-beat `lyrics` tokens, `{showdiagram false}` on every chord, `\tuning ... {hide}`) rendered by one `AlphaTabApi` per section using `display.startBar` / `display.barCount`; `window.__rendered` set when all sections have fired `postRenderFinished` and fonts are ready. `pdf_proto.py`: `chromium.launch(args=["--allow-file-access-from-files"])`, `wait_for_function("window.__rendered === true")`, `document.fonts.ready`, `page.pdf(format="A4", print_background=True, prefer_css_page_size=True)`; pages rasterised with PyMuPDF (`pip install pymupdf` into pwvenv; `pdftoppm` is not installed). `pdf_variants.py`: fluid width without print emulation, `stretchForce 0.7`, `scale 0.75`, `scale 0.6`, smaller effect font.

### Results

- **Pages:** 6 A4 pages (118 KB) for header + legend + 8 sections + 3/4 sample. Page 1: header, legend, Intro; page 2: Verse 1, Pre-chorus; page 3: Chorus (16-slot) alone; page 4: Verse 2, Bridge; page 5: Solo, Outro; page 6: the 3/4 box.
- **Breaks:** every section starts and ends on one page; no staff is cut mid-system. `break-inside: avoid-page` on the `.section` div works although it contains alphaTab's SVG partials (alphaTab renders the page layout into an `.at-surface` div with statically placed SVGs, not an absolutely positioned canvas, so Chromium can treat the block as unbreakable). `.section-head { break-after: avoid }` kept every heading and strum box with its staff. Cost: when the next section does not fit, the rest of the page is left blank (page 1 has ~25% white space, page 3 ~20%).
- **Legibility at print size:** diagrams at 80x100 CSS px (about 21 x 26 mm) are clear: dots, finger numbers in white on black (7.5 px font still readable), barre bar, "3" base-fret label, "x" and "o" markers, string letters. Direction tokens under the staff (alphaTab lyrics font, italic serif at scale 0.85) are about 7 pt and readable; chord names and bar numbers fine. Strum-box arrows and beat labels clear; the crossed arrow reads as "chunk".
- **Header:** stays with the legend and the first section; the badge and the mix note print.
- **16-slot bars:** at scale 0.85 one 16-slot bar with sixteen lyric tokens is about 480 px wide, so each bar takes its own system and an 8-bar 16-slot section is 727 px tall (nearly a full page, hence page 3). `stretchForce 0.7` and a smaller `display.resources.effectFont` changed nothing (the per-beat minimum width is set by the lyric glyphs); `scale 0.75` gave 650 px (still one bar per line); `scale 0.6` gave three bars per line but the tokens are too small to read in print. Recommendation: accept one bar per line for 16-slot sections, or render 16-slot sections at `scale 0.75` and mark the pattern box as the primary display.
- **Reflow under print media:** with a fluid container (body 1000 px) and `page.pdf()` called without `emulate_media("print")`, alphaTab did **not** re-layout: Chromium shrank the 1000 px page to the A4 width (3 pages, everything about 70% size). If `emulate_media("print")` is called first and 1.5 s allowed, alphaTab's resize observer does re-render to the print width, but that is a race. The robust fix is a fixed-width sheet: `.sheet { width: 182mm }` on screen (A4 210 mm minus 2 x 14 mm margins) and `html, body { width: 182mm }` under `@media print`; measured alphaTab width was 687.86 px in both media, and the PDF matched the screen layout exactly.
- **"rendered by alphaTab" footer:** drawn by the page layout under every section (eight times on a sheet). It is a hard-coded text glyph in the layout (`"rendered by alphaTab"` in `alphaTab.min.js`), no setting switches it off; MPL-2.0 allows removing it, or simply crop it with CSS (`.at-section { margin-bottom: -18px; overflow: hidden }`) or hide via a `transform`/clip of the last text node. Decide in Task 13; the simplest licence-clean option is the CSS crop.
- Each section's first system shows the time signature only for bar 1 of the song; later sections start without it (alphaTab shows the signature where it changes). Acceptable for a chord sheet.
- `postRenderFinished` fires twice per section (initial render, then re-render after the font loads); the flag must be set on the first full completion and the PDF waits for `document.fonts.ready` anyway; the output was correct.

alphaTab settings that worked (per section):

```js
new alphaTab.AlphaTabApi(div, {
  core: { tex: true, useWorkers: false, enableLazyLoading: false },
  display: { scale: 0.85, startBar: sec.start, barCount: sec.count, layoutMode: "page" },
  notation: { elements: { effectTempo: false, trackNames: false, scoreTitle: false, chordDiagrams: false, effectMarker: false } },
  player: { playerMode: 0 }
});
```

CSS that worked:

```css
.sheet { width: 182mm; margin: 0 auto; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 10px; break-inside: avoid; }
.section { break-inside: avoid-page; page-break-inside: avoid; margin-bottom: 5mm; }
.section-head { break-after: avoid; page-break-after: avoid; }
@media print {
  @page { size: A4; margin: 14mm; }
  html, body { width: 182mm; }
  .sheet { width: auto; margin: 0; padding: 0; }
  .no-print { display: none !important; }
}
```

SVG approach (both generators are about 40 lines of string building, no library): diagram = title text, x/o markers row, nut rect or base-fret text, 5 fret lines and 4 string lines (14 px string spacing, 15 px fret spacing), barre `rect` spanning the strings whose relative fret equals the barre, dots `circle r=5` with white finger digits, string letters below. Strum box = bordered rect, a column per slot with beat label (bold for beat numbers, grey for subdivisions), vertical shaft + chevron for D/U, two crossing lines over a down arrow for x, faint separators at beat boundaries.

### Recommended plan changes (Task 13)

1. Render stage: one alphaTex for the song (Task 12 output), **one `AlphaTabApi` per section** with `display.startBar`/`barCount` taken from the section's bar range (the plan's `data-bars` attribute), settings as above. `window.__rendered` = all sections rendered and `document.fonts.ready`.
2. Template CSS: fixed 182 mm sheet width on screen and print (as above); keep `break-inside: avoid-page` for sections (confirmed) and add a fallback for sections taller than a page (more than ~16 systems): `break-inside: auto` via a `.section.long` class so they are not pushed to a fresh page only to be split anyway.
3. Hide alphaTab's own title, track name, tempo, markers and diagrams (`notation.elements`), and `\chord ... {showdiagram false}` in the tex, so the HTML header and legend are the single source.
4. Decide on the "rendered by alphaTab" footer (CSS crop recommended).
5. Diagram and strum-box tests as planned; add `test_html_sets_fixed_sheet_width` and `test_pdf_page_count_matches_sections` (slow).
6. 16-slot sections: `scale 0.75` for sections with 16 slots per bar, or document the one-bar-per-line behaviour.

## Environment notes for the implementer

- `pwvenv` (Python 3.13) has Playwright 1.63.0 and launches Chromium 153 (`chromium-1243`) without `playwright install`; `pymupdf` 1.28.2 was installed there for page rasterisation. `venv_ytdlp` was not modified.
- Do not `html.escape` alphaTex inside `<script type="text/plain">`: script content is not entity-decoded, so `&quot;` reaches the parser verbatim and `\tuning (...) { label "gCEA" }` fails with "no overload matched arguments". Only `</script` needs escaping.
- Git Bash heredocs mangled `\\t` in Python source (`\\ts` became a tab); generate alphaTex with Python files, not shell heredocs.
