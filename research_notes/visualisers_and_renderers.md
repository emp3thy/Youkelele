# Visualisers and renderers for ukulele tab, chord diagrams, strumming patterns and audio-synced playback (as of 2026-10-01)

Research date: 2026-10-01. Version/date facts below were pulled live from the GitHub REST API, the npm registry and the PyPI JSON API on that date unless a different source is cited. Where two sources disagreed, both are listed.

## Key Question 1: Web renderers (alphaTab, VexFlow/VexTab, OSMD, Soundslice, abcjs, Verovio, ChordSheetJS/ChordPro, chord-diagram libs, strum-pattern renderers, Tone.js)

### Takeaway
alphaTab is the only open-source web renderer that combines tab + standard notation + in-score chord diagrams + a playback cursor + a documented external-audio/YouTube sync API (sync points, `IExternalMediaHandler`), and it accepts arbitrary 4-string tunings via alphaTex `\tuning (G4 C4 E4 A4)`. VexFlow/OSMD/Verovio/abcjs can draw tab but none ships audio sync; chord diagrams and strum arrows need separate small libraries (svguitar, @chordbook/charts, strumvg) or hand-rolled SVG.

### Comparison table (facts; each row's sources are in the findings list below)

| Library | Lang | License | Latest release (date) | Input formats | Tab staff | Std notation | Chord diagrams | Strum arrows | Playback cursor | External audio sync | MIDI synth | PDF export | Embedding |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alphaTab | TS/JS (also .NET, Kotlin) | MPL-2.0 | 1.8.4 (2026-07-05) | Guitar Pro 3-8, alphaTex, MusicXML | Yes | Yes | Yes (in-score, since 1.8.0) | Not confirmed (gap) | Yes, smooth scrolling | Yes: sync points, GP8 backing tracks, YouTube via custom handler | Yes (alphaSynth, SF2/SF3) | No native PDF (print/SVG) | Plain JS/npm; webpack plugin; no official React wrapper found |
| VexFlow 5 | TS | MIT | 5.0.0 (2025-03-05) | Programmatic API / EasyScore | Yes (TabStave) | Yes | No (separate vexchords) | No | No | No | No | No | npm |
| VexTab | JS | custom ("LicenseRef-LICENSE") | 4.0.5 (npm 2026-01-18); no GitHub releases | VexTab text | Yes | Yes | No | No | No | No | No | No | npm |
| OpenSheetMusicDisplay | TS | BSD-3-Clause | 2.1.3 (2026-09-19) | MusicXML/MXL | Yes (from MusicXML, bends/gliss) | Yes | No | No | Cursor API (manual timing) | No (official audio player = sponsors-only early access) | Via 3rd-party osmd-audio-player (2021) | No | npm, headless Node |
| Verovio | C++ with JS/Python toolkits | LGPL-3.0 | 6.3.0 (2026-08-19) | MEI, MusicXML, Humdrum, ABC | Partial (lute-focused; "preliminary" MusicXML tab import) | Yes | No | No | No (timemap export) | No | MIDI export | No (SVG) | npm, PyPI `verovio` |
| abcjs | JS | MIT | 6.7.1 (2026-09-21) | ABC | Yes (guitar/violin/mandolin/fiveString + custom tuning) | Yes | No | No | Yes (built-in synth cursor) | No external sync documented | Yes (built-in) | No | npm |
| ChordSheetJS | TS | GPL-2.0-only | 18.0.0 (2026-09-24) | ChordPro, chords-over-words, Ultimate Guitar | No | No | `{define}`/`{chord}` for guitar and ukulele | No | No | No | No | PDF (beta, jsPDF) | npm |
| ChordPro (reference impl.) | Perl | see repo | R6.101.0 (2026-04-21) | ChordPro | No | No | Yes, native PDF, any string count | No | No | No | No | Yes | CLI |
| svguitar | TS | MIT | 2.6.2 (2026-09-17) | JSON config | - | - | Yes (configurable string count) | No | - | - | - | SVG | npm, UMD, Node headless |
| @chordbook/charts (vexchords fork) | JS | MIT | 0.0.2 (2024-12-28) | JSON | - | - | Yes, guitar + ukulele | No | - | - | - | SVG | npm |
| vexchords | JS | MIT | 1.2.0 (2019-03-31) | JSON | - | - | Yes | No | - | - | - | SVG | npm (dormant) |
| @tombatossals/react-chords (+chords-db) | JS/React | MIT | 0.2.10 (2019-10-23) | chords-db JSON | - | - | Yes, guitar + ukulele | No | - | - | - | SVG | React |
| strumvg | TS | no license file | 3.0.1 (2026-09-17) | pattern string D/U/M/m/A/a | - | - | - | Yes | - | - | - | SVG | CLI |
| html-midi-player | TS | BSD-2-Clause | 1.6.0 (2025-07-06) | MIDI | No | "staff" visualizer | No | No | Yes | No | Yes (Magenta.js) | No | Web components |
| Tone.js | TS | MIT | 15.1.22 (2025-04-27) | - | - | - | - | - | - | Transport/scheduling | Yes | - | npm |
| Soundslice (commercial) | hosted | proprietary | n/a | Guitar Pro, MusicXML, editor | Yes | Yes | Yes | Yes (brush arrows) | Yes | Yes (YouTube free; MP3/video on paid) | Yes | Yes | iframe embed; full embed + API only on Licensing plan |

### Cited Findings

alphaTab
- License: the repo LICENSE file states "alphaTab is licensed under MPL-2.0. Copyright 2025, Daniel Kuschny and Contributors" — [GitHub LICENSE](https://github.com/CoderLine/alphaTab/blob/develop/LICENSE); npm metadata also reports MPL-2.0 — [npm @coderline/alphatab](https://www.npmjs.com/package/@coderline/alphatab)
- Release cadence (GitHub API, 2026-10-01): v1.8.4 2026-07-05, v1.8.3 2026-05-24, v1.8.2 2026-04-10, v1.8.1 2026-02-01, v1.8.0 2026-01-12, v1.7.1 2025-12-02, v1.6.3 2025-08-30, v1.6.0 2025-06-15, v1.5.0 2025-05-04, v1.4.0 2025-03-02, v1.3.0 2024-05-15; repo last pushed 2026-10-01, 1,856 stars, not archived — [GitHub releases](https://github.com/CoderLine/alphaTab/releases)
- Inputs: "alphaTab can load music notation from various sources like Guitar Pro 3-7, AlphaTex and MusicXML"; built-in synth alphaSynth plays via MIDI + SoundFont2/3 — [GitHub README](https://github.com/coderline/alphaTab)
- v1.6 added Guitar Pro 8 backing tracks "embedded into Guitar Pro 8 files including the synchronization details", plus a generic sync-point mechanism; developers either let alphaTab control media or "implement a custom handler which receives calls from alphaTab"; the Media Sync Editor "offers synchronization with YouTube videos if you decide to integrate with the YouTube iFrame API" — [alphaTab v1.6 release notes](https://www.alphatab.net/docs/releases/release1_6/)
- Release-notes summary (dates from GitHub API): 1.8.0 added in-score chord diagrams, smooth cursor scrolling, hide-empty-staves, multi-system slurs, bass-clef detection for GP3-5; 1.7.1 added an alphaTex exporter, beat-level lyrics, a new alphaTex parser, and a monorepo; 1.6.0 added GP8 audio tracks, external media backing tracks, audio export API, sync points for alphaTex — [GitHub releases](https://github.com/CoderLine/alphaTab/releases). One search summary attributes "sync points for alphaTex" to 1.7.1 rather than 1.6.0 — [alphaTab release 1.6 page via search](https://www.alphatab.net/docs/releases/release1_6/); treat the exact minor version as uncertain.
- External audio API: implement `IExternalMediaHandler` with `backingTrackDuration` (ms), `playbackRate`, `masterVolume`, `seekTo(time)`, `play()`, `pause()`; alphaTab calls `updatePosition()` and the docs say "50ms updates have shown to work well on even fast songs"; enable via `settings.player.playerMode = alphaTab.PlayerMode.EnabledExternalMedia`; built-in support for OGG Vorbis and MP3 and GP8 embedded audio; custom integration works with HTML5 audio/video and YouTube iframe API. Limitations: "alphaTab can only play either the external audio file or the synthesized audio" (no mixing), no pitch/tempo transformation of the backing track, and YouTube's `seekTo()` starts playback when not paused (needs a workaround) — [alphaTab Audio & Video Sync guide](https://alphatab.net/docs/guides/audio-video-sync)
- Media Sync Editor (in the Playground) auto-creates sync points at audio start/end and at every tempo change, lets you add masterbar-level sync points by double-click, supports a YouTube player mode but "YouTube doesn't allow access to the raw media. That's why the waveform will be empty", and exports either a Guitar Pro 8 file with embedded sync data or "custom source code" — [alphaTab Media Sync Editor guide](https://alphatab.net/docs/guides/media-sync-editor)
- alphaTex sync points "are specified as a flat list at the end of the song contents" — [alphaTex Sync Points doc (search snippet)](https://alphatab.net/docs/alphatex/sync-points/)
- alphaTex tuning: `\tuning (strings)` defines string count and pitches, e.g. `\tuning (G4 C4 E4 A4) { label "Ukulele Tuning" }` — [alphaTex Staff metadata (search snippet)](https://alphatab.net/docs/alphatex/staff-metadata); Tuning model stores "the values for each string of the instrument" as a list of MIDI numbers, with `getPresetsFor(stringCount)` and `getDefaultTuningFor()`; the reference page does not list ukulele presets or discuss re-entrant tunings — [alphaTab.model.Tuning](https://alphatab.net/docs/reference/types/model/tuning)
- Audio export API has an option to apply the loaded song's sync points during generation — [AudioExportOptions](https://alphatab.net/docs/reference/types/synth/audioexportoptions)
- Framework embedding: official docs describe a WebPack plugin and say "If you are using a framework like Angular, React or Vue.js you might read in their documentation on how the WebPack settings can be customized"; no official `@coderline/alphatab-react` package surfaced — [Installation (WebPack)](https://alphatab.net/docs/getting-started/installation-webpack/)

VexFlow / VexTab / vexchords
- VexFlow npm: 5.0.0 published 2025-03-05, MIT, "A JavaScript library for rendering music notation and guitar tablature"; GitHub releases: 5.0.0 (2025-03-05), 5.0.0-beta.1 (2025-02-25), 5.0.0-beta.0 (2024-09-12); repo pushed 2026-09-16 — [npm vexflow](https://www.npmjs.com/package/vexflow); [GitHub releases](https://github.com/vexflow/vexflow/releases)
- VexTab npm 4.0.5 (2026-01-18), license field "LicenseRef-LICENSE" (custom file); GitHub repo has zero releases, last push 2026-04-15; VexFlow documentation now points to EasyScore instead of VexTab — [npm vextab](https://www.npmjs.com/package/vextab); [VexFlow docs](https://vexflow.github.io/vexflow-docs/)
- vexchords: MIT, npm 1.2.0 last published 2019-03-31, repo last push 2024-12-31 — [GitHub 0xfe/vexchords](https://github.com/0xfe/vexchords)
- @chordbook/charts is "a fork of the vexchords library", MIT, renders guitar and ukulele SVG chord diagrams with open/muted strings, barres, position markers and tuning labels; v0.0.2 2024-12-28; 3 stars; repo pushed 2025-03-01 — [GitHub chordbook/charts](https://github.com/chordbook/charts)

OpenSheetMusicDisplay
- BSD-3-Clause; npm 2.1.3 on 2026-09-19 (2.1.2 2026-08-06, 2.1.1 2026-07-29); repo pushed 2026-10-01; 1,976 stars; "renders sheet music in MusicXML format in browsers and headless with NodeJS. Based on VexFlow" — [npm opensheetmusicdisplay](https://www.npmjs.com/package/opensheetmusicdisplay); [GitHub](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay)
- "OpenSheetMusicDisplay can display tablature (guitar tabs) from MusicXML, including effects like bends and glissandi" and can combine with treble clef — [OSMD blog, sheet music display libraries](https://opensheetmusicdisplay.org/blog/sheet-music-display-libraries-browsers/)
- Tab-specific changelog: 1.8.5 (2024-01-09) added `TabKeySignatureSpacingAdded`/`TabTimeSignatureSpacingAdded` for tab-only scores; 1.8.7 (2024-02-23) fixed tab tuplet alignment and `TabBeamsRendered=false` edge case; 1.8.9 (2024-07-15) tab rendering fixes — [OSMD CHANGELOG](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay/blob/develop/CHANGELOG.md)
- Fretboard/chord diagrams: issue #1010 asks "Is it possible to draw fretboard diagram with guitar tabs?" (open feature request, not supported) — [OSMD issue #1010](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay/issues/1010)
- Cursor: `Cursor.next()`, `show()`, `nextMeasure()`/`previousMeasure()`; the `MusicPartManagerIterator` exposes timestamps so note timing can be extracted; official wiki "Extracting note timing for playing"; issue #480 "Using Timestamps to move the Cursor" — [OSMD Cursor classdoc](https://opensheetmusicdisplay.github.io/classdoc/classes/Cursor.html); [OSMD wiki tutorial](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay/wiki/Tutorial---Extracting-note-timing-for-playing); [issue #480](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay/issues/480)
- OSMD itself "does not support playback"; the official OSMD audio player is early access for GitHub sponsors; community `osmd-audio-player` (MIT) last published 0.7.0 on 2021-12-30 — [OSMD blog, audio player upgraded](https://opensheetmusicdisplay.org/blog/blog-audio-player-upgraded/); [npm osmd-audio-player](https://www.npmjs.com/package/osmd-audio-player); [jimutt/osmd-audio-player](https://github.com/jimutt/osmd-audio-player)

Verovio
- LGPL-3.0; npm `verovio` 6.3.0 and PyPI `verovio` 6.3.0 both 2026-08-19; repo pushed 2026-10-01 — [GitHub rism-digital/verovio](https://github.com/rism-digital/verovio); [npm verovio](https://www.npmjs.com/package/verovio); [PyPI verovio](https://pypi.org/project/verovio/)
- Tablature changelog: 3.4.0 (2021-05-01) "Preliminary support for tablature (experimental work)"; 3.7.0 (2021-11-22) preliminary tab MIDI output; 3.9.0 (2022-02-22) "Preliminary support for tablature MusicXML import"; 3.10.0 (2022-05-25) stems/beams for guitar tab; 4.5.0 (2024-12-22) tablature customization; 5.2.0 (2025-04-23) "additional tablature features introduced in MEI 5.1"; 6.1.0 (2026-03-12) "Support (initial) for notationtype@tab.staff-like" — [Verovio CHANGELOG](https://github.com/rism-digital/verovio/blob/develop/CHANGELOG.md)
- Known gap: "Arpeggios and articulations missing when rendering MusicXML with a TAB staff" (issue #4449) and "Tablature articulation" (issue #4452) — [issue #4449](https://github.com/rism-digital/verovio/issues/4449); [issue #4452](https://github.com/rism-digital/verovio/issues/4452)
- MEI tablature work is driven by lute projects (E-LAUTE, TabMEI group); MEI "support for tablatures is currently weak" — [Oxford blog, customising MEI for lute tablature](https://tm.web.ox.ac.uk/blog/customising-mei-lute-tablature); [E-LAUTE paper](https://www.tandfonline.com/doi/full/10.1080/09298215.2024.2445593)

abcjs
- MIT; npm 6.7.1 2026-09-21 (6.7.0 2026-08-07); repo pushed 2026-09-21; 2,353 stars — [npm abcjs](https://www.npmjs.com/package/abcjs); [GitHub paulrosen/abcjs](https://github.com/paulrosen/abcjs)
- Tablature option supports `instrument: "violin" | "mandolin" | "fiddle" | "guitar" | "fiveString"`, a `tuning` array of open-string notes (lowest to highest), `capo`, `label` with `%T` for tuning, `highestNote`, `hideTabSymbol`; out-of-range notes render as "?"; ukulele is not explicitly listed — [abcjs tablature docs](https://docs.abcjs.net/visual/tablature)
- Michael Eskin's abctools (built on abcjs) claims it "can display standard notation and tablature for standard EADGBE-tuned Guitar, and for GCEA tuned Ukulele" — [abctools user guide](https://michaeleskin.com/abctools/userguide.html); [GitHub seisiuneer/abctools](https://github.com/seisiuneer/abctools)

ChordSheetJS / ChordPro
- GPL-2.0-only; npm 18.0.0 2026-09-24, with v17.0.0 2026-09-18 and v16.2.2 2026-08-25 (two major bumps in one week); repo pushed 2026-09-30 — [npm chordsheetjs](https://www.npmjs.com/package/chordsheetjs); [GitHub releases](https://github.com/martijnversluis/ChordSheetJS/releases)
- Parses ChordPro, chords-over-words and Ultimate Guitar; formats to text, HTML (table/div), ChordPro, PDF (beta, jsPDF), "measured HTML" (beta); recognises `{define}`/`{chord}` directives for guitar and ukulele; transposition, capo, chord-style conversion — [GitHub ChordSheetJS README](https://github.com/martijnversluis/ChordSheetJS)
- ChordPro reference implementation (Perl): "Originally developed for guitar players... ChordPro now lifts this limitation and allows an arbitrary number of strings" for mandolin, banjo, ukulele; produces PDF with chord diagrams natively; GitHub release R6.101.0 2026-04-21, repo pushed 2026-09-25 — [ChordPro reference implementation](https://www.chordpro.org/chordpro/chordpro-reference-implementation/); [GitHub ChordPro/chordpro](https://github.com/ChordPro/chordpro)

Chord diagram libraries
- svguitar: MIT; GitHub release v2.6.2 2026-09-17 (v2.6.0 2026-08-30); configurable number of strings (default 6) and frets (default 4), barres, finger labels/colors/shapes, titles, tuning labels, vertical/horizontal orientation, "normal" and "handdrawn" styles; Node headless via svgdom (handdrawn unsupported headless); powers chordpic.com; no explicit ukulele docs or framework wrappers — [GitHub omnibrain/svguitar](https://github.com/omnibrain/svguitar); [npm svguitar](https://www.npmjs.com/package/svguitar)
- @tombatossals/react-chords: MIT, "React library for easily generate guitar/ukulele SVG chords"; npm 0.2.10 last published 2019-10-23; companion `@tombatossals/chords-db` 0.5.1 2019-11-02; repo pushed 2025-10-15 — [GitHub tombatossals/react-chords](https://github.com/tombatossals/react-chords)
- spilth/chord_diagrams "Generate SVGs for Guitar and Ukulele Chord Diagrams" (not evaluated further) — [GitHub spilth/chord_diagrams](https://github.com/spilth/chord_diagrams)

Strumming-pattern renderers
- strumvg: "A command-line tool for generating SVG of a guitar strumming pattern from a formatted string"; D/d down, u/U up, M muted down, m muted up, A/a arpeggio; releases 3.0.1 2026-09-17, repo pushed 2026-09-30, 0 stars, no license detected by GitHub — [GitHub edonv/strumvg](https://github.com/edonv/strumvg)
- strum-trainer: single `index.html` ukulele/guitar tool; pattern of D, U, X (chuck), - (rest) plus chord progression, "giant arrows and chord diagrams" at a chosen BPM; 0 stars, no license — [GitHub Cloakmancer/strum-trainer](https://github.com/Cloakmancer/strum-trainer)
- CaGListRo/strumming-pattern-generator: Python generator + metronome with up/down arrow images — [GitHub](https://github.com/CaGListRo/strumming-pattern-generator)
- ChordSet PR #1: notation D/B down, U/C up, X muted, - rest, "x2" repeat; viewer shows arrows with count (1 e 2 e), highlighted step, BPM stepper — [GitHub felipednegredo/ChordSet PR #1](https://github.com/felipednegredo/ChordSet/pull/1)
- Soundslice added "Brush up"/"Brush down" buttons in the Tablature section of its editor on 2018-06-08 — [Soundslice blog](https://www.soundslice.com/blog/83/brush-strumming-arrows-in-our-notation-editor/)
- FaChords has an interactive strumming trainer with down/up/chuck symbols and a pendulum (hosted, not a library) — [FaChords](https://www.fachords.com/guitar-strumming-patterns/)

Playback/visualisation helpers
- html-midi-player: BSD-2-Clause, 1.6.0 2025-07-06 (previous 1.5.0 2022-07-09); `<midi-player>` and `<midi-visualizer type="piano-roll|waterfall|staff">` web components built on Magenta.js; SVG-based, stylable — [GitHub cifkao/html-midi-player](https://github.com/cifkao/html-midi-player); [midi-visualizer doc](https://github.com/cifkao/html-midi-player/blob/master/doc/midi-visualizer.md)
- Tone.js: MIT, npm 15.1.22 2025-04-27 — [npm tone](https://www.npmjs.com/package/tone)

Soundslice (commercial)
- Plans page: Free $0; Plus $5/month; Teacher $20/month (100 students, $0.20 per extra); Licensing $100/month (200 unique users, $0.50 per extra). Embedding limited to 1 slice on Free/Plus/Teacher; "Unlimited" embedding and API access only on Licensing. Sync: Free = YouTube only; Plus and above = uploaded MP3s/videos, Mux/Vimeo/Wistia, multitrack stems, auto-sync — [Soundslice plans](https://www.soundslice.com/plans/). (A search snippet said "The Plus plan ... is $20 per month"; the plans page itself shows $5 — [Soundslice licensing FAQ](https://www.soundslice.com/licensing/faq/) is where the conflicting snippet came from.)
- Data API manages slices and "syncpoints providing the mapping between notation and an audio/video recording"; official Python client `soundsliceapi` — [Soundslice data API](https://www.soundslice.com/help/data-api/); [GitHub soundslice/soundsliceapi](https://github.com/soundslice/soundsliceapi)
- Embedding: full player and a "miniplayer" for short notation synced with audio/video — [Embedding the Soundslice player](https://www.soundslice.com/help/en/embedding/); [Miniplayer](https://www.soundslice.com/help/en/embedding/miniplayer/47/overview/)

### Inferences
- For a 4-string ukulele with re-entrant tuning, alphaTab's tuning model is just an ordered list of MIDI pitches per string, so `\tuning (G4 C4 E4 A4)` should synthesize the high G correctly (pitch = string MIDI + fret); nothing in the docs suggests tunings must be monotonic, but this is not explicitly documented (see Gaps).
- alphaTab is also the only web option with chord diagrams drawn inside the score (1.8.0), so a Python pipeline that emits alphaTex can get tab + notation + diagrams from one renderer; strum arrows would still need a custom SVG layer.
- VexTab and vexchords are effectively dormant (no GitHub releases; last npm publish 2019 for vexchords); prefer VexFlow 5 directly or @chordbook/charts / svguitar for diagrams.
- Verovio's tablature work is lute/MEI-driven; MusicXML tab import is still labelled "preliminary" and has open issues, so it is a poor fit for ukulele tab.
- OSMD can draw ukulele tab from MusicXML if MuseScore/music21 emits it, but all cursor timing must be driven by your own code; it has no sync-point concept.
- ChordSheetJS's weekly major-version churn (v16 to v18 in September 2026) means pin versions.

### Gaps
- Exact alphaTex `\sync` syntax: the docs page returns only the site landing content to automated fetches; the only confirmed detail is that sync points are a flat list at the end of the song.
- Whether alphaTab renders strum-direction (brush up/down) arrows from alphaTex beat effects, and whether its chord-diagram directive supports 4-string diagrams, was not verified from docs.
- No official statement found on alphaTab handling of re-entrant (non-monotonic) tunings for automatic string assignment when importing MIDI/MusicXML without string info.
- No maintained npm library dedicated to strumming-pattern arrows was found; all candidates are 0-star personal tools.
- svguitar's README does not mention ukulele explicitly (string count is configurable, so it should work, but unverified).
- VexTab's custom license terms were not read.

## Key Question 2: Python/desktop tooling (music21, LilyPond, MuseScore 4, Guitar Pro 8, TuxGuitar, matplotlib/plotly fretboards, PyPI packages, Streamlit/Gradio/Jupyter)

### Takeaway
MuseScore Studio 4.7.x gives a headless CLI (`-o`) that exports PDF/PNG/SVG/MIDI/MusicXML/MP3 from a MusicXML or MSCZ file and supports 4-string fretboard diagrams, making it the most practical static-render backend; LilyPond 2.26 has built-in `ukulele-tuning` and `predefined-ukulele-fretboards.ly` but its automatic string assignment assumes descending string pitch (re-entrant caveat); the pure-Python diagram packages (`fretboard`, `fretboardgtr`) are old or copyleft, and no Streamlit/Gradio notation components exist on PyPI.

### Cited Findings

MuseScore Studio 4
- Latest GitHub release v4.7.5 on 2026-09-08 (v4.7.4 2026-07-07) — [GitHub musescore/MuseScore releases](https://github.com/musescore/MuseScore/releases)
- CLI: `-o`/`--export-to` converts without the GUI ("converter mode"); output formats PDF, PNG, SVG, MIDI, MusicXML, MP3, FLAC, OGG, WAV, mscz/mscx; PNG is one file per page at 300 DPI by default (`-r`); `-T` trims SVG (single-page only); `-S` style file; `-P` append parts to PDF; `-j file.json` batch jobs with `in`/`out`/`plugin`; `--score-parts`; `-f` ignores corruption/version warnings — [MuseScore handbook, command line usage](https://handbook.musescore.org/appendix/command-line-usage)
- Fretboard diagrams: Ctrl+K chord symbol then "Add fretboard diagram"; "MuseScore Studio can automatically create guitar fretboard diagrams for most common chords symbols"; linked diagrams update when the chord symbol changes (can be disabled in Preferences); diagrams allowed "for any stringed instrument"; Properties > Settings > "Strings" sets the number of strings — [MuseScore handbook, fretboard diagrams](https://handbook.musescore.org/idiomatic-notation/guitar/fretboard-diagrams); [handbook, chord symbols](https://handbook.musescore.org/text/chord-symbols)
- Ukulele caveats from forums: ukulele diagrams come from a community "Ukulele Chords.mpal" palette loaded into a custom workspace; palette ukulele diagrams do not auto-show chord names — [musescore.org, How do you insert ukulele fretboard diagrams](https://musescore.org/en/node/283424); [musescore.org, Ukulele chord diagrams](https://musescore.org/en/node/355019)
- Regression reported for 4.5+: adding a chord symbol to a note with a custom fretboard diagram "discards the custom diagram and replaces it with the default chord" — [MuseScore issue #27284](https://github.com/musescore/MuseScore/issues/27284)

music21
- BSD-3-Clause; PyPI 10.5.0 2026-06-17; repo pushed 2026-10-01 — [PyPI music21](https://pypi.org/project/music21/); [GitHub cuthbertLab/music21](https://github.com/cuthbertLab/music21)
- `show()` needs `musescoreDirectPNGPath` pointed at MuseScore 4 (`C:\Program Files\MuseScore 4\bin\MuseScore4.exe` on Windows, `/Applications/MuseScore 4.app/Contents/MacOS/mscore` on macOS), set via `environment.set(...)` or `environment.UserSettings()`, or `configure.run()` — [music21 issue #1612](https://github.com/cuthbertLab/music21/issues/1612); [music21list thread](https://groups.google.com/g/music21list/c/vlMrBo9F2Cc)
- `showscore` (PyPI 0.1.4, 2024-07-24, MIT) renders music21 scores in Jupyter without MuseScore — [PyPI showscore](https://pypi.org/project/showscore/)
- `music21.tablature` provides FretNote/FretBoard objects with `GuitarFretBoard`, `UkeFretBoard`, `BassGuitarFretBoard`, `MandolinFretBoard` and `ChordWithFretBoard` (ChordSymbol + FretBoard) — [music21.tablature module docs](https://www.music21.org/music21docs/moduleReference/moduleTablature.html)

LilyPond
- GitHub releases: v2.26.0 2026-04-21, v2.24.4 2024-12-15 (one search summary said 2.24.4 was released 2024-07-21; GitHub tag date is 2024-12-15); 2.27.0 dev 2026-04-25 — [GitHub lilypond releases](https://github.com/lilypond/lilypond/releases); [LilyPond news](https://lilypond.org/news.html)
- `TabStaff` with `stringTunings`; predefined `guitar-tuning`, `ukulele-tuning`, `mandolin-tuning`, `bass-tuning`, `banjo-open-g-tuning`; `FretBoards` context with lookup table; `\fret-diagram`, `\fret-diagram-terse`, `\fret-diagram-verbose`; `predefined-ukulele-fretboards.ly`; use `"treble_8"` clef or `\transposition c` for correct MIDI — [LilyPond 2.24 Notation Reference 2.4.1](https://lilypond.org/doc/v2.24/Documentation/notation/common-notation-for-fretted-strings)
- Re-entrant caveat: LilyPond's automatic fret/string assignment "assumes strings are in falling pitch and walks through all strings to find the lowest possible fret, which doesn't work ... with non-monotonous strings like re-entrant ukuleles"; the algorithm would need to find "the next highest string instead of always getting the next string" (2015 lilypond-user thread) — [lilypond-user, Errors when using TabStaff with stringTunings](https://lists.gnu.org/archive/html/lilypond-user/2015-08/msg00586.html); [Uke tab questions thread](https://www.mail-archive.com/lilypond-user@gnu.org/msg145510.html)

TuxGuitar
- GitHub releases: 2.1.0 2026-07-22, 2.0.1 2025-12-27, plus rolling "tuxguitar-next" builds (latest 2026-09-14); repo pushed 2026-09-29; 1,535 stars; GitHub shows no license metadata — [GitHub helge17/tuxguitar releases](https://github.com/helge17/tuxguitar/releases)
- 2.0.0 (released 2025-11-02 per search summary) introduced a new file format not readable by older versions, free-edition mode, line breaks, configurable frets per track — [TuxGuitar CHANGES](https://github.com/helge17/tuxguitar/blob/master/CHANGES); [Release 2.0.0](https://github.com/helge17/tuxguitar/releases/tag/2.0.0)
- Imports GP3/GP4/GP5/GPX; exports MIDI, PDF, MusicXML; no command-line/headless mode documented; packages are unsigned — [GitHub releases page summary](https://github.com/helge17/tuxguitar/releases)
- Conflict: one automated summary of the releases page dated 2.0.0/2.0.1 to 2023 and 2.1.0 to 2024; the GitHub API dates (2025-12-27, 2026-07-22) are authoritative.

Guitar Pro 8 (commercial)
- GP 8.1 imports .gp/.gpx, PowerTab, MIDI, ASCII, TablEdit, MusicXML and exports GPX, GP5, MIDI, ASCII, PDF, PNG, MusicXML and audio (MP3/WAV/FLAC/AIFF/Ogg); supports fretted instruments from 3 to 10 strings including ukulele — [Guitar Pro 8.1 blog](https://www.guitar-pro.com/blog/p/38236-new-free-updade-guitar-pro-8-1-is-available); [Guitar Pro 8 user guide PDF](https://static.guitar-pro.com/gp8/manual/Guitar-Pro-8-user-guide.pdf)
- Dorico forum reports MusicXML-from-GP8 quirks — [Steinberg forum](https://forums.steinberg.net/t/import-musicxml-from-gp8-quirks/900076)
- PyPI `pyguitarpro` 0.11 (2026-05-03) reads/writes GP3-GP5 from Python — [PyPI pyguitarpro](https://pypi.org/project/pyguitarpro/)

Python diagram/fretboard packages (PyPI JSON API, 2026-10-01)
- `fretboard` 1.0.0, MIT, last PyPI upload 2016-11-18; repo dmpayton/python-fretboard last push 2023-02-22, 94 stars; API `fretboard.UkuleleChord(positions='x232', fingers='-132').save('svg/ukulele-G.svg')` — [PyPI fretboard](https://pypi.org/project/fretboard/); [GitHub dmpayton/python-fretboard](https://github.com/dmpayton/python-fretboard)
- `fretboardgtr` 0.2.7, 2024-01-23, AGPL-3.0; draws fretboards (scales) and chord diagrams in SVG — [PyPI fretboardgtr](https://pypi.org/project/fretboardgtr/)
- `pychord` 1.4.0, 2026-04-29; chord theory only (no diagrams) — [PyPI pychord](https://pypi.org/project/pychord/); [GitHub yuma-m/pychord](https://github.com/yuma-m/pychord)
- `uke-chords-print` (GitHub only, not on PyPI) uses pychord to generate printable PDF ukulele diagrams, 108 chords with up to 3 voicings, baritone/low-G tunings; CLI `python3 -m uke_chords_print C Am G7 F -t "Beginner Chords"` — [GitHub baijum/uke-chords-print](https://github.com/baijum/uke-chords-print)
- `uchord` (GitHub only) writes ukulele chord SVGs: `uchord.write_chord('c.svg','C','0003')` — [GitHub Python-Ninja-Hebi/python-ukulele-chord-to-svg](https://github.com/Python-Ninja-Hebi/python-ukulele-chord-to-svg)
- `mpl-chord-diagram` is a matplotlib "chord diagram" in the data-viz sense (flow arcs), not guitar chords — [PyPI mpl-chord-diagram](https://pypi.org/project/mpl-chord-diagram/)

Web-framework embedding from Python
- Streamlit 1.64.0 (2026-09-15); `st.components.v1.html` renders an HTML string in an iframe (params `height` default 150, `scrolling`, `width`), returns nothing, and is deprecated as of 1.56.0 in favour of `st.html`; docs warn never to pass untrusted HTML — [Streamlit docs st.components.v1.html](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html); [PyPI streamlit](https://pypi.org/project/streamlit/)
- Gradio 6.29.0 (2026-09-29) — [PyPI gradio](https://pypi.org/project/gradio/)
- No `streamlit-abcjs`, `streamlit-vexflow` or `streamlit-alphatab` packages exist on PyPI (404 on 2026-10-01); search for Streamlit notation components found none — [PyPI](https://pypi.org/)

### Inferences
- Pipeline-friendly static path: Python (music21 or hand-built MusicXML with `<technical><string>/<fret>`) -> `MuseScore4 -o out.pdf/png/svg/mid` in converter mode; MuseScore's 4-string fretboard diagrams and ukulele instrument cover the diagram need, but chord-name labelling of ukulele diagrams from palettes is manual per forum reports.
- LilyPond is viable for publication-quality ukulele tab if you set string numbers explicitly per note (`\4`, `\3`), sidestepping the re-entrant auto-assignment problem.
- Any Python chord-diagram package should be treated as "generate once, cache SVG": `fretboard` has had no release since 2016 and `fretboardgtr` is AGPL.
- For Streamlit/Gradio, the realistic route is `st.html`/`gr.HTML` with a self-contained HTML page that loads alphaTab from a CDN; there is no return channel without writing a bidirectional component.

### Gaps
- TuxGuitar licence not confirmed from a primary source (GitHub reports none; commonly cited as LGPL).
- No source found documenting whether MuseScore's CLI export preserves fretboard diagrams in MusicXML (the handbook page is silent).
- Plotly/matplotlib fretboard or piano-roll packages beyond `fretboardgtr` were not surveyed.
- Guitar Pro 8's ukulele re-entrant playback behaviour (high-G synthesis) was not verified.

## Key Question 3: Audio-synced "scrolling tab" open-source equivalents to Songsterr / Ultimate Guitar Tab Pro / Chordify / Moises

### Takeaway
Every open-source Songsterr-style player found (It's MyTabs, Songstarr, tabrender) is a thin app around alphaTab's sync-point/external-media API; It's MyTabs (MIT, self-hostable via Docker) already does MP3/OGG/YouTube sync with cursor modes. For Chordify-style chord timelines there is no established open-source project, only hosted free tools.

### Cited Findings
- It's MyTabs: "Open source, web based, self hostable guitar/bass tab (tablature) viewer and player, similar to Songsterr"; MIT; rendering engine alphaTab; backend Deno 2.4.4+; Docker on port 47777 or Windows executable; syncs with .mp3/.ogg or YouTube; MIDI synth with mute/solo; cursor modes "No cursor (auto-scroll), bar highlighting, or follow-cursor"; formats .gp/.gpx/.gp3/.gp4/.gp5/.musicxml/.capx; repo pushed 2026-10-01 — [GitHub ticket-wisp/its-mytabs](https://github.com/ticket-wisp/its-mytabs)
- Songstarr: "open-source, local-first tab player in the spirit of Songsterr"; accepts Guitar Pro 3-8, MusicXML (.xml/.musicxml/.mxl), alphaTex and plain-text ASCII tabs; uses alphaTab — [GitHub mauritsE/Songstarr](https://github.com/mauritsE/Songstarr) (GitHub API returned no metadata on 2026-10-01; status unverified)
- tabrender: "self-hosted Songsterr alternative for Guitar Pro tabs as a synced player with realistic audio" (mentioned in a 2025-12-05 blog guide; repo not evaluated) — [BrightCoding guide](https://www.blog.brightcoding.dev/2025/12/05/the-ultimate-guide-to-self-hosting-your-own-guitar-tab-player-break-free-from-subscriptions-forever-%F0%9F%8E%B8/)
- alphaTab's own external-media feature "can integrate with YouTube Videos and audio recordings" and ships a Media Sync Editor — [alphaTab Audio & Video Sync](https://alphatab.net/docs/guides/audio-video-sync); [Media Sync Editor](https://alphatab.net/docs/guides/media-sync-editor)
- Chordify-like hosted tools: StrumTube "turns any YouTube video into chords ... support for both guitar and ukulele"; ChordU extracts chords from a YouTube URL with a synced player; BeatKey detects chords in-browser; Guitariz claims to be open-source with chord recognition — [AlternativeTo, open source Chordify alternatives](https://alternativeto.net/software/chordify/?license=opensource); [Guitariz](https://guitariz.studio/chordify-alternative); [BeatKey](https://chords.beatkey.app/chordify-alternative)
- YouTube IFrame API: `player.getCurrentTime()` returns elapsed seconds; `onPlayerStateChange` fires on play/pause/end; polling via `setInterval` is the standard way to detect seeks — [YouTube IFrame Player API reference](https://developers.google.com/youtube/iframe_api_reference); [Tutorialzine example](https://tutorialzine.com/2015/08/how-to-control-youtubes-video-player-with-javascript)

### Inferences
- Because all three open-source players are alphaTab wrappers, forking It's MyTabs (or copying its YouTube `IExternalMediaHandler` implementation) is the fastest route to a Songsterr-style ukulele player; the ukulele-specific work is only in producing the input file with a 4-string tuning.
- A Chordify-style chord timeline (chord blocks on a time axis) is simple enough to hand-build (chords + onsets JSON, one `requestAnimationFrame` loop reading `getCurrentTime()`); none of the found projects is worth depending on.

### Gaps
- Guitariz's open-source claim and its licence were not verified against a repository.
- Songstarr and tabrender repositories could not be inspected (metadata unavailable / not fetched).
- No open-source project rendering strum-direction arrows synced to audio was found.

## Key Question 4: Debug visualisers (librosa.display, pretty_midi, piano-roll JS, Sonic Visualiser + Chordino/pYIN, html-midi-player)

### Takeaway
librosa 1.0.0 (`specshow` with `y_axis='chroma'`) plus `pretty_midi.get_piano_roll()` cover static Python debugging; Sonic Visualiser 5.2.1 with the NNLS-Chroma/Chordino and pYIN Vamp plugins gives an interactive reference for chord and pitch tracks; html-midi-player 1.6.0 gives a browser piano-roll synced to MIDI playback.

### Cited Findings
- librosa: ISC; PyPI/GitHub 1.0.0 2026-08-11 (0.11.0 2025-03-11); `librosa.display.specshow` plots spectrograms, CQT and chromagrams (`y_axis='chroma'`) — [PyPI librosa](https://pypi.org/project/librosa/); [librosa display docs](https://librosa.org/doc/0.11.0/display.html); [specshow example](http://librosa.org/doc/0.11.0/auto_examples/plot_display.html)
- pretty_midi: MIT; PyPI 0.2.11.post0 2026-07-28 (GitHub 0.2.11 2025-10-08); `Instrument.get_piano_roll()` / `PrettyMIDI.get_piano_roll()` return pitch x time matrices commonly plotted with `specshow` — [PyPI pretty_midi](https://pypi.org/project/pretty_midi/); [pretty_midi tutorial](https://notebook.community/craffel/pretty-midi/Tutorial); [issue #170 plotting piano roll](https://github.com/craffel/pretty-midi/issues/170)
- Sonic Visualiser: GitHub releases sv_v5.2.1 2025-03-21, sv_v5.2 2025-03-07, sv_v5.0.1 2024-10-01 — [GitHub sonic-visualiser releases](https://github.com/sonic-visualiser/sonic-visualiser/releases)
- NNLS Chroma / Chordino: "Chordino provides a simple chord transcription based on NNLS Chroma"; Vamp plugins run in Sonic Visualiser, Sonic Annotator and Audacity; a gist shows batch Chordino via Sonic Annotator — [isophonics NNLS Chroma](https://isophonics.net/nnls-chroma); [gist: run chordino on a batch](https://gist.github.com/xavriley/b72645b2ccb9398308c7dc713a78d4fb)
- pYIN is a Vamp plugin for pitch and note tracking available in Sonic Visualiser — [arXiv 2111.03895, digital audio processing tools](https://arxiv.org/pdf/2111.03895)
- html-midi-player: `<midi-visualizer type="piano-roll">` (also "waterfall", "staff"), SVG-based, configured via `config` attribute; 1.6.0 2025-07-06, BSD-2 — [html-midi-player README](https://github.com/cifkao/html-midi-player/blob/master/README.md)
- Magenta.js `PianoRollSVGVisualizer` demo and a looping/tempo-changing player built on it — [magenta-js visualizer demo](https://github.com/magenta/magenta-js/blob/master/music/demos/visualizer.html); [swampthang/magenta-midi-player](https://github.com/swampthang/magenta-midi-player)

### Inferences
- For a ukulele pipeline the useful debug stack is: chromagram (librosa) vs. estimated chords (Chordino export) on one time axis, and piano-roll (pretty_midi) vs. pYIN f0 for melody/tab notes; all are matplotlib-renderable in Jupyter without extra tooling.

### Gaps
- Sonic Visualiser's own version page was not fetched; dates come from GitHub tags.
- No standalone "pianoroll" npm library beyond html-midi-player/Magenta was evaluated.

## Key Question 5: Least-friction path for a Python developer to a web page showing chords + tab + strum pattern scrolling in sync with a YouTube video

### Takeaway
Generate alphaTex from Python (tab with `\tuning (G4 C4 E4 A4)`, chord definitions, lyrics, and a sync-point list), serve one static HTML page that loads `@coderline/alphatab` from npm/CDN in `PlayerMode.EnabledExternalMedia`, implement `IExternalMediaHandler` over the YouTube IFrame API (poll `getCurrentTime()` every ~50 ms and call `updatePosition`), and overlay strum arrows and chord timeline as your own SVG/HTML driven by the same clock; wrap in `st.html` only if a Streamlit shell is wanted.

### Cited Findings
- alphaTab supports "alphaTex" text input, YouTube via a custom external media handler, `updatePosition()` at ~50 ms, and `PlayerMode.EnabledExternalMedia` — [alphaTab Audio & Video Sync](https://alphatab.net/docs/guides/audio-video-sync); [alphaTex introduction](https://alphatab.net/docs/alphatex/introduction)
- alphaTex `\tuning (G4 C4 E4 A4)` and 1.8.0 in-score chord diagrams — [alphaTex staff metadata](https://alphatab.net/docs/alphatex/staff-metadata); [GitHub releases](https://github.com/CoderLine/alphaTab/releases)
- alphaTab limitation: cannot mix synth with external audio, cannot pitch-shift the backing track; YouTube `seekTo()` autoplay quirk — [alphaTab Audio & Video Sync](https://alphatab.net/docs/guides/audio-video-sync)
- Media Sync Editor exports sync data as a GP8 file or "custom source code"; YouTube mode has no waveform — [Media Sync Editor](https://alphatab.net/docs/guides/media-sync-editor)
- YouTube IFrame API `getCurrentTime()` / `onPlayerStateChange` — [YouTube IFrame Player API](https://developers.google.com/youtube/iframe_api_reference)
- Worked reference implementation of exactly this (alphaTab + YouTube + cursor modes), MIT — [GitHub ticket-wisp/its-mytabs](https://github.com/ticket-wisp/its-mytabs)
- Streamlit `st.components.v1.html` is an iframe with no return value and is deprecated in favour of `st.html` since 1.56.0 — [Streamlit docs](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html)
- Strum arrows: no maintained library; strumvg CLI makes SVG from "D U M m A a" strings — [GitHub edonv/strumvg](https://github.com/edonv/strumvg)
- Alternative static path: MuseScore 4 CLI exports PNG/SVG/PDF/MIDI/MusicXML headlessly from a MusicXML with 4-string fretboard diagrams — [MuseScore command line usage](https://handbook.musescore.org/appendix/command-line-usage)
- Commercial shortcut: Soundslice syncs notation with YouTube on the free plan but allows only one embedded slice outside the $100/month Licensing plan — [Soundslice plans](https://www.soundslice.com/plans/)

### Inferences
- Friction ranking (lowest first): (1) alphaTab + alphaTex + YouTube handler in a single static HTML page served by FastAPI/Flask or opened from disk; (2) OSMD from MusicXML with a hand-written cursor scheduler (more code, no chord diagrams); (3) MuseScore CLI PNG strips scrolled by JS (no beat-level cursor without extra timing data); (4) Soundslice (fastest UX, but embed limits and no custom strum/chord overlays).
- Since Python already knows beat onsets from the audio analysis, emit sync points per bar (bar index -> ms) so alphaTab's cursor follows real tempo drift; strum-pattern arrows can reuse the same per-beat timestamps.
- Jupyter prototyping works with `IPython.display.HTML` for the same page, but the YouTube iframe must be allowed by the notebook's CSP; this was not tested.

### Gaps
- Exact alphaTex sync-point syntax and the chord-diagram directive syntax could not be fetched (site returned landing-page content to automated fetches); read https://alphatab.net/docs/alphatex/sync-points and https://alphatab.net/docs/alphatex/metadata in a browser.
- Whether alphaTab draws strum-direction arrows natively (brush up/down beat effects) remains unverified.
- No benchmark found comparing cursor-sync latency of alphaTab vs. OSMD vs. abcjs.
