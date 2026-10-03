# Assumption checks: rendering chain (alphaTab, chords-db, strum vocabulary, chord diagrams)

Date: 2026-10-03. Checked against the design spec `2026-10-03-ukulele-tab-chain-design.md`, sections 6.6 to 6.8 and 11. All URLs accessed 2026-10-03. Where a claim was tested empirically, it was tested with alphaTab 1.8.4 from the npm tarball in headless Chromium 153 (Playwright for Python 1.63) and in the Playwright MCP browser; the test pages and screenshots are described in the notes.

## Summary table

| # | Assumption in spec | Status | Evidence | Spec change |
|---|---|---|---|---|
| B1a | alphaTex can show a slash staff, and it can be the only staff (no standard notation, no tab) | CONFIRMED | `\staff {slash}` is a documented staff property ("Enable the display of slash notation"; default when none given is `score tabs`). Rendered test showed slash staff only. [structural metadata](https://www.alphatab.net/docs/alphatex/structural-metadata); source `docs/alphatex/_structural-metadata.mdx` in CoderLine/alphaTabWebsite; 1.4.0 release notes "feat: Add Slash Notation (#1511)", "feat: add beat slash reading and rendering (#1646)". Current stable: **1.8.4** (npm, 2026-07-05). | None |
| B1b | Brush strokes `{bd}` `{bu}` on a beat render as strum arrows on the slash staff | CHANGED | `bd`/`bu` are documented beat properties and parse without error, but the slash renderer never draws them: `SlashBeatContainerGlyph` uses a bare `BeatGlyphBase` for pre-notes, whereas `ScoreBeatPreNotesGlyph` adds `ScoreBrushGlyph` (only score and tab staves draw brushes). Rendered test: no arrows on the slash staff. | Keep `{bd}`/`{bu}` for semantics/MIDI but show direction with a beat text `{txt "D"}` above the slash, or a `\lyrics "D - D U - U D U"` line below the staff (both verified rendering on a slash-only staff). The per-section pattern box in the HTML remains the primary direction display. |
| B1c | Muted slots as dead notes, rests as `r`, on a slash staff | CHANGED (muted) / CONFIRMED (rests) | `r` rests draw as rests on the slash staff (verified). Dead notes `(x.1 x.2 x.3 x.4)` parse but draw as ordinary slashes, indistinguishable from played beats. The dead-slap beat `(){ds}` ("Marks the beat to be a dead-slap beat ... simply use () to indicate the empty beat") draws a large X on the slash staff (verified). | Emit `(){ds}` for `x` slots, not dead notes. |
| B1d | `\chord` definitions produce diagrams at the top; `{ch "C"}` puts chord names above beats | CONFIRMED (with ordering caveat) | `\chord (name strings)` + beat `{ch "C"}`; diagrams appear in the header list when `ch` is used; `\chordDiagramsInScore` additionally draws them inline (big, duplicated; do not use). Verified. **String order:** chord strings and `\tuning` are listed from alphaTex string 1 to string N; the diagram draws the LAST listed string on the LEFT (`ChordDiagramGlyph.ts`: `strings[length - i - 1]` at x = i). | Write `\tuning (A4 E4 C4 G4)` and `\chord ("C" 3 0 0 0)` (A first, G last) so the diagram reads G C E A left to right; notes then use string 1 = A (`(3.1 0.2 0.3 0.4){ch "C"}`). Add `\hideDynamics` to suppress the default `f`. |
| B1e | Section/rehearsal markers via `\section` | CONFIRMED | `\section "Verse"` or `\section (marker "text")`, e.g. `\section "S" "Solo"`. [bar metadata](https://www.alphatab.net/docs/alphatex/bar-metadata). Verified rendering. Cosmetic: marker, tempo and first chord name stack over bar 1. | None |
| B1f | 4-string tuning as pitches; re-entrant ordering accepted | CONFIRMED | `\tuning (strings)` takes "pitched notes"; nothing checks monotonicity; `(A4 E4 C4 G4)` and `(G4 C4 E4 A4)` both rendered. Order semantics as in B1d. For a slash-only staff the pitches only affect MIDI. | Use high-to-low-by-position order (A4 E4 C4 G4). |
| B1g | Tempo and title/artist metadata | CONFIRMED | `\title "..."`, `\artist "..."` (score metadata, optional template/alignment), `\tempo bpm` or `\tempo (bpm "label")`, `\ts 4 4`. Verified. | None |
| B2a | alphaTab npm package and licence | CONFIRMED | `@coderline/alphatab` 1.8.4, licence **MPL-2.0**, published 2026-07-05, unpacked 13.7 MB. Bravura font is SIL OFL 1.1 (`dist/font/Bravura-OFL.txt`). Soundfont `dist/soundfont/sonivox.sf2/.sf3` (Apache 2.0) is only needed for playback. | Ship `dist/alphaTab.min.js` (1.12 MB) + `dist/font/Bravura.woff2` (313 KB; optionally `Bravura.woff` 550 KB) + `Bravura-OFL.txt` + alphaTab LICENSE. No soundfont. |
| B2b | Renders from a `file://` page in headless Chromium | CHANGED | With default `core.useWorkers: true`, alphaTab creates a Blob worker that calls `importScripts('file:///.../alphaTab.js')`, which Chromium refuses: "Failed to execute 'importScripts' on 'WorkerGlobalScope'" and nothing renders (verified, Playwright Python headless Chromium 153). With `core: { useWorkers: false }` the same page renders fully from `file://` (fonts load via `document.fonts`, `renderFinished` fires, `page.pdf()` produced an 84 KB A4 PDF). `core.fontDirectory` auto-detects `<script folder>/font/` from `document.currentScript.src` for a classic `<script>` include, also under `file://` (`Environment._detectScriptFile`). | Template must set `core.useWorkers: false` (and `player.playerMode: 0`). Use a classic `<script src="alphaTab.min.js">`, not an ES module import, so font auto-detection works offline. |
| B2c | Node.js server-side render path (SVG) exists | CONFIRMED | Official guide "Node.js" sets `settings.core.engine = 'svg'`, uses `new alphaTab.rendering.ScoreRenderer(settings)` and collects SVG chunks from `partialRenderFinished`; `@coderline/alphaskia` (since 1.3.0) renders PNG via `engine = 'skia'`. No PDF output; SVG relies on CSS `@font-face` for Bravura. [Node.js guide](https://alphatab.net/docs/guides/nodejs). Caveat: issue #2888 (open, 2026-09-24) shows a Node repro crashing on `slashed` beats on a **tab** staff with rhythm stems; not our slash-staff case. | Optional. Browser + Playwright PDF stays simplest; Node SVG is a fallback if Chromium is unwanted. |
| B3 | chords-db has a ukulele set, MIT, usable from Python | CONFIRMED | MIT (LICENSE, (c) 2016 David Rubert). `lib/ukulele.json`: `main {strings 4, fretsOnChord 4}`, `tunings.standard ["G4","C4","E4","A4"]`, 12 keys, **46 suffixes**, **552 chords, 2114 positions**. Position fields: `frets` (G,C,E,A order, -1 = muted), `fingers`, `baseFret`, `barres`, `midi`, optional `capo`. npm `@tombatossals/chords-db` 0.5.1 (2022-06-13) ships `lib/ukulele.json`; repo is at 0.6.0 unpublished. Not on PyPI. | Vendor `lib/ukulele.json` (215 KB) with LICENSE into the package data; load with `json`. |
| B4 | A bundled vocabulary of around thirty common ukulele patterns can be seeded from public sources | CONFIRMED | UkuTabs guide (18 patterns, D/U/x/- notation), Ukulele Tricks (5 patterns, as staff images), Ukulele Go (32-pattern arrow chart, free PDF). 31 distinct 4/4 eight-slot patterns extracted below. Patterns are rhythmic facts; not copyrightable, but copy neither prose nor images. | Vocabulary data file: 8-slot strings over `D U x -`; attribute sources in the file header. |
| B5 | A small MIT/BSD library exists for ukulele chord diagrams as SVG, or hand-rolled SVG | CONFIRMED (hand-rolled is right for Python) | JS: `svguitar` 2.6.2 MIT (configurable strings, barres, muted `x`, Node headless via svgdom); `@chordbook/charts` 0.0.2 MIT (guitar + ukulele, 3 stars). Python: `uchord` (Python-Ninja-Hebi, MIT, 3 stars, last push 2023-03-28, no barres/muted, not on PyPI); `uke` 0.1.0.dev1 on PyPI (MIT) but its GitHub repo is gone. | Hand-roll the SVG in Python from chords-db shape data (frets, baseFret, barres, fingers); it is ~60 lines and avoids a JS dependency in the Python render stage. |

## Notes per item

### B1. alphaTex capabilities (alphaTab 1.8.4)

Docs consulted: [alphaTex introduction](https://www.alphatab.net/docs/alphatex/introduction), [document structure](https://www.alphatab.net/docs/alphatex/document-structure), [score metadata](https://www.alphatab.net/docs/alphatex/score-metadata), [structural metadata](https://www.alphatab.net/docs/alphatex/structural-metadata), [staff metadata](https://www.alphatab.net/docs/alphatex/staff-metadata), [bar metadata](https://www.alphatab.net/docs/alphatex/bar-metadata), [beat properties](https://www.alphatab.net/docs/alphatex/beat-properties). Several pages are client-rendered; the markdown sources at `github.com/CoderLine/alphaTabWebsite/docs/alphatex/*.mdx` were used where fetches returned the landing page. There is no public "alphaTex playground" URL (`/alphatex/` is a 404; `/docs/playground` has no alphaTex input), so rendering was verified with a local page.

Exact syntax used and confirmed:

- Staff: `\staff {slash}`; properties `score lineCount`, `tabs`, `slash`, `numbered`; "If no properties describing the visible notation are provided, the default is `score tabs`."
- Tuning: `\tuning (A4 E4 C4 G4) { label "gCEA" }` (also `{hide}`); `\capo fret`.
- Chord diagram: `\chord ("C" 3 0 0 0)`; options `{firstfret n}`, `{barre (f1 f2)}`, `{showname false}`, `{showdiagram false}`, `{showfingers false}`; usage `{ch "C"}` on the beat. "To avoid inconsistencies with tunings, chords should be defined after the tuning is set."
- Beat: duration prefix `:8`, chord `(3.1 0.2 0.3 0.4)`, rest `r`, dead-slap `(){ds}`, brush `{bd}` `{bu}` (optional duration in MIDI ticks), text `{txt "D"}`, lyrics `{lyrics "D"}` or staff-level `\lyrics "D - D U - U D U"` (syllables are spread one per beat, rests included; `+` joins words).
- Bar: `\ts 4 4`, `\tempo 100`, `\section "Verse"`, `\ks Dmajor`, repeats `\ro` / `\rc n`.
- Score: `\title "..."`, `\artist "..."`, `\hideDynamics`, `\chordDiagramsInScore` (avoid).

String ordering (important, from source `rendering/glyphs/ChordDiagramGlyph.ts` and `importer/AlphaTexImporter.ts`): alphaTex string 1 is the first entry of `\tuning` (default guitar tuning array is `[64, 59, 55, 50, 45, 40]`, i.e. E4 first). The chord diagram draws `strings[length - 1 - i]` at the i-th column from the left, so the last listed string is the leftmost. Test 1 with `\tuning (G4 C4 E4 A4)` and `\chord ("C" 0 0 0 3)` drew `3 o o o` (wrong way round); test 2 with `\tuning (A4 E4 C4 G4)` and `\chord ("C" 3 0 0 0)` drew `o o o 3` and `G7` as `o 2 1 2`, which is the conventional gCEA diagram.

Rendering observations (both from a local HTTP page in the Playwright MCP browser and from `file://` in headless Chromium):

- Slash-only staff renders with slashes, beams, rests and bar numbers; no standard notation or tab appears.
- No brush arrows appear for `{bd}`/`{bu}`. Source: `rendering/SlashBeatContainerGlyph.ts` sets `this.preNotes = new BeatGlyphBase()`; brush glyphs are added only in `ScoreBeatPreNotesGlyph` (`ScoreBrushGlyph`) and `TabBeatPreNotesGlyph` (`TabBrushGlyph`).
- `(x.1 x.2 x.3 x.4)` dead notes render as plain slashes. `(){ds}` renders a large X spanning the staff.
- `{txt "D"}` renders above the beat; `\lyrics` renders below; both fine on the slash staff.
- The default `f` dynamic appears under bar 1 unless `\hideDynamics` is set.
- Section marker, tempo and the first chord name overlap above bar 1 (cosmetic; a `\section` on a bar with no chord name, or CSS scale, avoids it).
- Related open bug: [#2888](https://github.com/CoderLine/alphaTab/issues/2888) "Tablature rendering crashes on slash-notation beats with rhythm stems enabled in 1.8.4" concerns `beat.slashed` on a **tab** staff; a slash-only staff did not hit it.

Minimal working alphaTex (two bars: island strum on C, then a chunked pattern on G7; verified rendering without errors in 1.8.4):

```
\title "Strum Test"
\artist "Youkelele"
\tempo 100
\hideDynamics
.
\track "Ukulele"
\staff {slash}
\tuning (A4 E4 C4 G4) { label "gCEA" }
\chord ("C" 3 0 0 0)
\chord ("G7" 2 1 2 0)
\ts 4 4
\section "Verse"
\lyrics "D - D U - U D U D U D x D U D U"
:8 (3.1 0.2 0.3 0.4){bd ch "C"} r (3.1 0.2 0.3 0.4){bd} (3.1 0.2 0.3 0.4){bu} r (3.1 0.2 0.3 0.4){bu} (3.1 0.2 0.3 0.4){bd} (3.1 0.2 0.3 0.4){bu} |
(2.1 1.2 2.3 0.4){bd ch "G7"} (2.1 1.2 2.3 0.4){bu} (2.1 1.2 2.3 0.4){bd} (){ds} (2.1 1.2 2.3 0.4){bd} (2.1 1.2 2.3 0.4){bu} (2.1 1.2 2.3 0.4){bd} (2.1 1.2 2.3 0.4){bu}
```

Mapping from `strums.json` slots: `D` -> chord beat `{bd}`, `U` -> chord beat `{bu}`, `x` -> `(){ds}`, `-` -> `r`; duration `:8` for 8 slots per bar, `:16` for 16. The `\lyrics` line carries one token per slot (rests consume a token) and is the on-staff direction display; the `{bd}`/`{bu}` properties are kept for MIDI and for any future score/tab staff.

### B2. Vendoring alphaTab offline

- Package: `@coderline/alphatab` 1.8.4 (latest; `alpha` tag 1.9.0-alpha.1891), licence MPL-2.0 ([npm registry JSON](https://registry.npmjs.org/@coderline/alphatab)). Exports: `.`, `./vite`, `./webpack`, `./font/*`, `./soundfont/*`.
- Files in `dist/`: `alphaTab.js` / `alphaTab.min.js` (UMD, 1.12 MB min), `alphaTab.mjs` / `alphaTab.core.min.mjs` (ESM), `alphaTab.worker.min.mjs`, `alphaTab.worklet.min.mjs`, `font/Bravura.{woff2,woff,otf,eot,svg}` + `Bravura-OFL.txt` (SIL OFL 1.1), `soundfont/sonivox.{sf2,sf3}` (Apache 2.0). Ship: `alphaTab.min.js`, `font/Bravura.woff2` (and `.woff`), `Bravura-OFL.txt`, alphaTab `LICENSE`. The soundfont is not needed with `player.playerMode: 0` (Disabled).
- `core.fontDirectory` default `"${AlphaTabScriptFolder}/font/"`, derived from `document.currentScript.src` for a classic script, or `import.meta.url` for a module unless it is a `file://` URL ("avoid using file:// urls in case of bundlers like webpack", `Environment.ts`); overridable with global `ALPHATAB_FONT` or the setting. Under `file://` with a classic `<script>` it resolved to `file:///.../dist/font/` and `document.fonts.check('12px alphaTab')` returned true. [core.fontDirectory](https://www.alphatab.net/docs/reference/settings/core/fontdirectory)
- `core.useWorkers` default true ("Whether the rendering should be done in a worker if possible"). Under `file://` the Blob worker fails with `Failed to execute 'importScripts' on 'WorkerGlobalScope': The script at 'file:///.../alphaTab.js' failed to load` and no render event ever fires. With `useWorkers: false` rendering completed in about 10 ms for two bars and `page.pdf(format="A4")` produced the PDF. [core.useWorkers](https://www.alphatab.net/docs/reference/settings/core/useworkers)
- Node path: [Node.js guide](https://alphatab.net/docs/guides/nodejs): `import * as alphaTab from "@coderline/alphatab"`, `settings.core.engine = "svg"`, `new alphaTab.rendering.ScoreRenderer(settings)`, `renderer.width = ...`, collect `partialRenderFinished` SVG chunks; PNG via `@coderline/alphaskia` (`engine = "skia"`, since 1.3.0). No PDF; SVG text needs an `@font-face` for Bravura at display time.

### B3. chords-db

- Repo [tombatossals/chords-db](https://github.com/tombatossals/chords-db), MIT ([LICENSE](https://raw.githubusercontent.com/tombatossals/chords-db/master/LICENSE)). Raw data: [lib/ukulele.json](https://raw.githubusercontent.com/tombatossals/chords-db/master/lib/ukulele.json).
- Shape: top-level `main`, `tunings`, `keys`, `suffixes`, `chords` (keyed by root, e.g. `"C"`, `"Db"`), each chord `{key, suffix, positions: [{frets, fingers, baseFret, barres, midi, capo?}]}`. Example C major position 1: `frets [0,0,0,3]`, `fingers [0,0,0,3]`, `baseFret 1`, `barres []`, `midi [67,60,64,72]`, which confirms `frets` are in G, C, E, A order (midi 67 = G4). Muted strings are `-1`. `baseFret` is the fret of the first diagram row; frets are relative to it when `baseFret > 1`.
- Counts: 12 keys (C Db D Eb E F Gb G Ab A Bb B), 46 suffixes (major, minor, dim, dim7, sus2, sus4, 7sus4, alt, aug, 6, 69, 7, 7b5, aug7, 9, 9b5, aug9, 7b9, 7b9#5, 7#9, 11, 9#11, 13, 13b9, 13b5b9, b13b9, b13#9, maj7, maj7b5, maj7#5, maj9, maj11, maj13, m6, m7, m7b5, m9, m69, m9b5, m11, mmaj7, mmaj7b5, mmaj9, mmaj11, add9, madd9), 552 chords, 2114 positions.
- Distribution: npm `@tombatossals/chords-db` 0.5.1 (2022-06-13) includes `lib/ukulele.json`; repo package.json says 0.6.0 (unpublished). PyPI `chords-db`: 404. Vendor the JSON.

### B4. Strum pattern vocabulary seed

Sources (all public, no licence stated except as noted):

1. UkuTabs, "Ukulele strumming patterns for beginners", https://ukutabs.com/ukulele-guides/ukulele-strumming-patterns-beginners/ (18 patterns in `d u x –` notation with audio; the author states "I do not publish the exact strumming for an individual copyrighted song, but the general patterns and notation below work across thousands of them"). Notation key on the page: `–` = "pause or missed strum", `x` = chunk, capital = accent.
2. Ukulele Tricks (Brett McQueen), "5 Effective Strumming Patterns for Beginners", https://ukuleletricks.com/5-effective-strumming-patterns-for-beginners/ (five patterns as slash-staff images; "Copyright 2026 Ukulele Tricks - a McQueen Machine, LLC website").
3. Ukulele Go (Dave), "32 Ukulele Strumming Patterns", https://ukulelego.com/stuff/32-ukulele-strumming-patterns/ (arrow chart PNG and free PDF; eighth-note grid). Also "The Most Important Strumming Pattern You'll Ever Learn", https://ukulelego.com/?p=183 (D-DU-UDU).

Live Ukulele's strumming material is behind membership ("Strumming on the Grid", "Generating All 256 Grid Strums"); Ukulele Underground is behind a bot challenge; Ukulele Hunt's pattern post could not be located. Both are therefore not cited.

Licence/attribution: a strumming pattern is a short rhythmic idea, which is a fact or method, not an original literary or artistic work, so the patterns themselves carry no copyright. What is protected is each site's prose, audio and images, and arguably the particular selection and arrangement of a long list. The vocabulary file should encode the patterns in our own format with a header crediting the three pages as sources, and must not reproduce their text, images or audio. Ukulele Go's chart is offered as a free download; UkuTabs has no licence notice; Ukulele Tricks reserves copyright on its page.

Candidate 4/4 vocabulary, 8 slots per bar (1 & 2 & 3 & 4 &), tokens `D U x -`. Ukulele Go rows were transcribed from the chart image and should be re-checked against the PDF before bundling.

| # | Pattern (8 slots) | Name / note | Source |
|---|---|---|---|
| 1 | `D-D-D-D-` | All downs | UkuTabs 1, Ukulele Tricks 1, Ukulele Go 1 |
| 2 | `DUDUDUDU` | Down-up eighths | UkuTabs 2, Ukulele Tricks 2, Ukulele Go 3 |
| 3 | `D-DU-UD-` | "Everywhere 4/4" | UkuTabs 3, Ukulele Go 6 |
| 4 | `D-DU-UDU` | Island / calypso strum | UkuTabs 4, Ukulele Tricks 5, Ukulele Go (?p=183) |
| 5 | `D-D-DUDU` | Driving 4/4 | UkuTabs 5, Ukulele Go 8 |
| 6 | `D-DUDUDU` | Busy upbeat 4/4 | UkuTabs 6, Ukulele Go 9 |
| 7 | `D-DUD-DU` | Half-bar pattern repeated | UkuTabs 7, Ukulele Tricks 3, Ukulele Go 4 |
| 8 | `DUxUDUxU` | Half-bar chunk / "funky chunky" | UkuTabs 8 and 11 |
| 9 | `-D-D-D-D` | Reggae offbeat | UkuTabs 12 |
| 10 | `--DU--D-` | Syncopated reggae | UkuTabs 13 |
| 11 | `D-------` | Whole-bar ballad | UkuTabs 18 |
| 12 | `DUD-DUD-` | Up on the "and" of 1 and 3 | Ukulele Tricks 4, Ukulele Go 5 |
| 13 | `D-D-D-DU` | | Ukulele Go 2 |
| 14 | `DU-UDU-U` | | Ukulele Go 7 |
| 15 | `DU-U-U-U` | | Ukulele Go 10 |
| 16 | `DU-U--DU` | | Ukulele Go 11 |
| 17 | `-UDUDU-U` | | Ukulele Go 12 |
| 18 | `D-DUD-D-` | | Ukulele Go 13 |
| 19 | `-U-U-U-U` | Offbeat ups (swing/reggae feel) | Ukulele Go 14 |
| 20 | `-U-U-UDU` | | Ukulele Go 15 |
| 21 | `-UDU-UDU` | | Ukulele Go 16 |
| 22 | `D---D---` | Half notes | Ukulele Go 17 |
| 23 | `--D---D-` | Backbeat downs | Ukulele Go 18 |
| 24 | `DUD-D-D-` | | Ukulele Go 19 |
| 25 | `DU-UD-DU` | | Ukulele Go 20 |
| 26 | `D----UDU` | | Ukulele Go 21 |
| 27 | `D--UD-D-` | | Ukulele Go 22 |
| 28 | `DUDUD-D-` | | Ukulele Go 23 |
| 29 | `-UD-D-D-` | | Ukulele Go 24 |
| 30 | `DUDUD--U` | | Ukulele Go 25 |
| 31 | `DU--DU--` | | Ukulele Go 26 |
| 32 | `-UDUDUDU` | | Ukulele Go 27 |
| 33 | `-UD-D-DU` | | Ukulele Go 28 |
| 34 | `DUDU-UDU` | | Ukulele Go 29 |
| 35 | `D-D--UDU` | | Ukulele Go 30 |
| 36 | `DUDUDUD-` | | Ukulele Go 31 |
| 37 | `-UDU-UD-` | | Ukulele Go 32 |

Two-bar (16-slot) seed: `D-DU-UDU-UDU-UD-` (UkuTabs 9, "two-bar relaxed", island strum stretched over two bars). Non-4/4 patterns noted for a later `--meter` option: 3/4 `D-DUD-` and `D-DUDU` (UkuTabs 14, 15); 6/8 `D--D-U` and `D-UD-U` (UkuTabs 16, 17). UkuTabs 10 (`DUDUDUDU` with accented upbeats) collapses onto #2 because the vocabulary has no accent token. The spec's "around thirty" is met by rows 1 to 31; rows 32 to 37 are optional extras.

### B5. Chord diagram drawing

- `svguitar` (omnibrain/svguitar): MIT, npm 2.6.2 (2026-09-17), 823 stars; configurable string and fret counts, barres, muted `x`, finger labels, tuning labels, title; Node headless via `svgdom` with a bundled OpenSans font for text metrics ("handdrawn" style unsupported headless). https://github.com/omnibrain/svguitar
- `@chordbook/charts`: MIT, npm 0.0.2 (2024-12-28), fork of vexchords, "Renders SVG chord diagrams for Guitar / Ukulele in your browser"; 3 stars, last push 2025-03-01. https://github.com/chordbook/charts
- `uchord` (Python-Ninja-Hebi/python-ukulele-chord-to-svg): MIT, 3 stars, last push 2023-03-28; `write_chord(filename, name, '0003', fingers='', subtexts='', starting_fret=-1)`; no barres, no muted strings; not on PyPI. https://github.com/Python-Ninja-Hebi/python-ukulele-chord-to-svg
- `uke` on PyPI: 0.1.0.dev1 (2023-04-16), MIT, "Creating Ukulele Chord and Strumming Patterns Diagrams in SVG with Python"; its homepage https://github.com/llxlr/uke returns 404, so it is unmaintained and unverifiable.
- Conclusion: no maintained Python option; the JS options would force a Node step into the Python render stage. Hand-rolled SVG from chords-db data (4 strings, 4 or 5 frets, `baseFret` label when > 1, barre rectangle from `barres`, `x`/`o` markers from `-1`/`0`, finger numbers from `fingers`) is the right call, with a unit test per shape class (open, barre, high position, muted string).

## Test artefacts

Scratchpad only (not committed): `uke_test.html` / `uke_test2.html` (alphaTab 1.8.4 UMD build from the npm tarball, `core.tex`, `useWorkers` switchable by query string), `file_test.py` (Playwright for Python, headless Chromium, `file://` URL, waits for `renderFinished`, writes PNG and A4 PDF). Screenshots `shot1.png` and `shot2.png` under `.playwright-mcp/` in the repo root (git-ignored or to be removed).
