# Research strand: ukulele arrangement, chord simplification and what the tools do

Date: 2026-10-03. Scope: turning recognised chords into a playable GCEA ukulele chart (simplification of sevenths, slash chords and power chords; capo and transposition; voicing choice; key and key changes), what Chordify, Moises, Ultimate Guitar, Songsterr, Riffstation and Chord ai present, how separation model and stem choice affect chord and strum quality, and quick wins for sheet readability and correctness.

Ground rules for reading this document:

- **[verified]** means I read the source (web page, paper text, the project's own code, run artifacts or spec) and the statement is in it. **[inferred]** means my own reasoning from verified facts. **[secondary]** means a number quoted by a third party (for example a hosting site's model card), not the original.
- Version 1.2 items (four-bar sections, mean tempo, title cleaning, filling N bars by chroma template match within the song's chord set, passing chords without diagrams, phrase alignment, repeated row blocks, narrow pickup cell) are taken as built. Nothing below proposes them again; several items build on them.
- Code paths are under `C:\Users\gethi\sources\Youkelele\src\youkelele\` and were read, not edited.

## 0. What the code does today (baseline for everything below) [verified]

| Concern | Where | Behaviour |
|---|---|---|
| Chord model | `models/chords.py` runs the vendored Chord-CNN-LSTM with the `submission` dictionary | Vocabulary (read from `~/.youkelele/models/chord_cnn_lstm/data/submission_chord_list.txt`): `maj min dim aug`, inversions `maj/3 maj/5 min/b3 min/5 maj/2 min/2 maj/b7 min/b7`, `sus2 sus4 sus4(b7)`, `maj7 7 min7 dim7 hdim7`, `maj9 9 min9 11 13`, `N`. **No power chord (`:5`) class.** |
| Beat snapping | `music/snap.py` | Per-beat majority label, runs merged into events. No minimum duration, no bar-level smoothing. |
| Triad reduction | `music/triads.py` | `mir_eval` bitmap of the quality (bass dropped) matched to maj, min, dim, aug, sus4, sus2 templates; unknown qualities fall to the largest overlap. |
| Tier | `music/arrange.py::simplify_for_tier` | `easy` reduces every label to its triad; `full` keeps the quality if chords-db has a shape, else reduces, else blanks. Only two tiers. |
| Slash chords | `music/shapes.py::_split_label` | The bass is dropped before any lookup or display, in both tiers, so a slash chord never reaches the sheet. |
| Spelling | `shapes.py::display_name_for`, `arrange.py::transpose_label` | Display keeps the model's own root spelling; any transposed root is spelt with sharps (`_SHARPS`). No key-based spelling. |
| Capo | `arrange.py::score_capo`, `choose_capo` | Capo 0 to 5; score = mean over **distinct** labels of the cheapest shape cost after transposition, plus 0.2 per fret; ties to the lower capo. |
| Shape cost | `shapes.py::shape_cost` | 1.5 if chords-db lists a barre, 0.4 per fretted string, 0.6 per fret of `baseFret` above 1, 0.5 per fret of span when two or more strings are fretted, 0.4 per finger above three. |
| Voicing | `arrange.py::select_voicings` | One shape per distinct label for the whole song; coordinate descent on shape cost times count plus 0.1 times finger movement between adjacent events. |
| No-capo alternative | `stages/arrange.py` writes `Arrangement.no_capo_alternative` | Computed when capo > 0 but **nothing in `render/` reads it** (grep of `render/` finds no reference). |
| Key | `music/key.py` | Krumhansl-Kessler correlation on the mean CQT chroma of the **whole mix**, one global key, confidence = relative margin to the runner-up. No local key, no chord-based key. |
| Grid cell | `render/grid.py::cell_for` | Chord names in slot order joined by ` / `; three or more names flagged `crowded`. |
| Shape data | `data/chords-db/ukulele.json` | 552 chords, 481 with four positions; 178 chords list a barre as their first position. Suffixes include `add9`, `m7b5`, `7sus4`, but **no `5`**. |

Shapes that chords-db offers for the chords the runs met [verified, from the probe script]: E `1402` (first position, no barre), `4442` (second, no barre flag); B `4322` barre; Bm `4222` barre; Bb `3211` barre; Db/C# `1114` barre. Major and minor chords with **no** open, barre-free position inside four frets: B, Bm, Bb, Bbm, Db. Everything else has an open shape.

Run facts used below [verified from `runs/*/03_harmony/chords.json`, `05_arrange/arrangement.json`, `06_score/score.json`]:

| Run | Key found | Capo | Shapes | Events, of which under 1.2 s |
|---|---|---|---|---|
| Chelsea Dagger `sexhetcxqy4` | D major, confidence 0.006 (G major 0.762 vs D 0.766) | 0 (margin over capo 2 only 0.11, per the v1.1 validation) | G D A C Bm(barre) Em Am B(barre) | 68, 13 short |
| Summer of '69 `9f06qzcvuhg` | D major 0.056 | 0 (margin 0.33) | D A Bm(barre) G F Bb(barre) C | 76, 0 short |
| Pour Some Sugar On Me `0uib9y4ofps` | C# major 0.010 (truth C# minor) | 4 | A D G C F Am, all open | 82, 6 short |
| Wet Leg "mangetout" `lbc6ccztp5e` | C major 0.136 | 0 | C F Dm C#(barre) | 67, 3 short |

No run produced a seventh, sus or inversion label (every `label` equals its `triad`), so the `easy` tier has never changed anything on a real song.

## 1. Failure modes

### 1.1 Power chords read as major triads, which then drags the key to the wrong mode

- **Observed [verified]:** Pour Some Sugar On Me's verse riff is a no-third power chord; the model labels it `C#:maj` (30% of the song), the key comes out C# major against the published C# minor, and the sheet prints the riff as a major chord (`A` shape at capo 4) where every ukulele chart uses the minor (`Am`). The lessons document works through this and the v1.2 spec explicitly leaves "key mode from power chords" out of scope.
- **Why it happens [verified]:** the `submission` vocabulary has no `:5` class, so a root-plus-fifth sound must land on `maj` or `min`. McFee and Bello report the same thing for their 170-class model: of the chords that map to the out-of-gamut class `X`, 2091 are single-note chords and 2365 are power chords, "neither of which map unambiguously onto the simplified vocabulary", and "the model appears to resolve these toward the more commonly used min and maj qualities" (ISMIR 2017, section 5.2, [archives.ismir.net/ismir2017/paper/000077.pdf](https://archives.ismir.net/ismir2017/paper/000077.pdf)). Deng and Kwok quantify the imbalance behind it: "the maj and min triads make up almost 70% of the whole sample population, the maj7, min7 and 7 chords constitute more than 20%, and the portion of other chords are less than 10%" ([arXiv 1709.07153](https://arxiv.org/abs/1709.07153)).
- **Consequence for the key [verified]:** `estimate_key` is a Krumhansl correlation on the whole-mix chroma; the lessons measured a tie (0.550 vs 0.544) decided the wrong way, and a chord-set diatonic fit with C# relabelled as a power chord would favour E/C#m by a wide margin (97% against 70%, worked by hand in the lessons).

### 1.2 Global key is a coin toss on two of four songs, and the sheet does not say so

- **Observed [verified]:** Chelsea Dagger D major 0.766 against G major 0.762; Pour Some Sugar On Me 0.550 against 0.544. The header prints one key with no hedge. The confidence field (0.006, 0.010) exists in `chords.json` but is not rendered.
- **Why [verified]:** whole-song chroma of the mix includes vocals and drums; Krumhansl profiles were derived from probe-tone experiments and are known to be beaten by other profiles on popular music. On the MTG popular-music evaluation, "the best result for popular music (55% accuracy) is obtained using a tonic triad profile" ([ISMIR 2006 paper 91](https://archives.ismir.net/ismir2006/paper/000091.pdf), via [Essentia docs](https://essentia.upf.edu/reference/std_Key.html)). Essentia ships fourteen profile types and defaults to `bgate`, described as beating Krumhansl-Kessler across a broad tonal repertoire ([Essentia Key reference](https://essentia.upf.edu/reference/std_Key.html)).
- **Inference [inferred]:** the project already has a far better key witness than the chroma: the chord stream itself. Four of four runs produced a clean diatonic chord set. Key-from-chords with a tonic-triad weighting (count the I, IV, V and vi, ii, iii occurrences, weight by time, prefer the mode whose tonic triad is most frequent and opens or closes the song) would have given D or G for Chelsea with an explicit tie, and C# minor/E for PSSOM once the power chord is relabelled.

### 1.3 Key changes are never detected

- **Observed [verified]:** `estimate_key` returns one key. None of the four validation songs modulates, so nothing has yet gone wrong, but a gear-change chorus would print the whole song in the first key.
- **How common [verified]:** Mauch's analysis of the UK charts found gear changes fell "from a staggering 15% in and around 1960 to consistently lower than 4% in the first decade of the current century" ([ArtsJournal summary of Mauch](https://www.artsjournal.com/lies/2013/02/gear-change/)); NPR's 2022 piece puts US number-one hits with any key change at roughly a quarter per decade from the 1960s to the 1990s and one in the 2010s ([NPR](https://www.npr.org/transcripts/1139232684)). So for the catalogue a ukulele player actually wants (1960s to 1990s rock and pop), a local-key pass matters more than the modern-chart figure suggests.
- **Inference [inferred]:** the symptom on this chain would not be a wrong key label so much as a wrong **capo decision**, because `choose_capo` scores the union of chords across both keys and may pick a compromise capo that makes neither half open.

### 1.4 Capo decision is thin and the player is given no alternative

- **Observed [verified]:** Chelsea Dagger chose capo 0 over capo 2 by 0.11; Summer of '69 by 0.33. The v1.1 spec deliberately scores distinct labels, not time. `no_capo_alternative` is computed and written but never rendered.
- **Why it matters [verified]:** ukulele players use a capo far less than guitarists; the Live Ukulele capo lesson frames the capo as an occasional tool "not to be used as a substitute for learning chords" ([liveukulele.com capos](https://liveukulele.com/lessons/theory/transposing/capos/)). Moises makes the capo a **user** control ("Under 'Capo on fret', input the fret number where your capo is placed", [moises.ai capo mode](https://moises.ai/features/guitar-capo-mode/)); Ultimate Guitar prints the transcriber's capo with the shapes relative to it (the Humphrey and Bello table marks such transcriptions with an asterisk and transposes them for comparison, [ISMIR 2015 paper 294](http://ismir2015.uma.es/articles/294_Paper.pdf)).
- **Inference [inferred]:** a sheet that silently commits to capo 4 is right for a player who owns a capo and wrong for one who does not; the data to print both already exists.

### 1.5 Beat-level flicker produces two-chord cells that are not harmonic rhythm

- **Observed [verified]:** 13 of Chelsea Dagger's 68 events last under 1.2 s (under two beats at 158 bpm); the v1.1 validation notes Chelsea's "G / D" cells and PSSOM bars with three names. Some half-bar changes are real (PSSOM chorus E-A on beats 1 and 3, as Ultimate Guitar writes it), so a blanket minimum would be wrong.
- **Why [verified]:** `snap_to_beats` takes a per-beat majority and merges runs; it has no notion of bar, phrase or harmonic rhythm. The literature is consistent that frame-wise or beat-wise maxima "are often fragmented" and that decoding (HMM, CRF) or structural priors are what make the sequence coherent (Müller's chord recognition chapter, [audiolabs-erlangen](https://www.audiolabs-erlangen.com/fau/professor/mueller/teaching/2022w_mpa/MPA_material/data/2021_Mueller_MPA_ChordRecognition.pdf)). Papadopoulos and Peeters showed that modelling chord dependence on metric position improves chord estimation and downbeat estimation together ([HAL hal-00525172](https://hal.archives-ouvertes.fr/hal-00525172)). The ISMIR 2021 coherence paper reports that, for every model they tested, the segmentation score's limiting term was **over**-segmentation, not under-segmentation ([archives.ismir.net/ismir2021/paper/000055.pdf](https://archives.ismir.net/ismir2021/paper/000055.pdf)).

### 1.6 Sevenths, sus and slash chords: the simplification exists but has never been exercised, and the full tier is not "full"

- **Observed [verified]:** on four songs the model emitted triads only. When it does emit `A:sus4(b7)` or `D:maj/5`, `easy` reduces it; `full` keeps `7`, `sus4` and so on if chords-db has the suffix, but **both** tiers drop the bass before display, so a `full` sheet can never show `D/F#`.
- **Is that wrong for ukulele? [verified]:** mostly not. Live Ukulele's slash chord guide says "it gets tricky to do slash chords right if you play with a high G string" and writes its examples for low G; the practical rule it and UkuTabs give is to play the chord before the slash unless the bass is not a chord tone ([liveukulele slash chords](https://liveukulele.com/chords/ukulele-slash-chords/); [ukulelehunt](https://ukulelehunt.com/?p=598)). In re-entrant tuning a strummed chord "has no clear bass note at the bottom" ([cursa.app on high G](https://cursa.app/en/article/high-g-or-low-g-why-the-ukuleles-fourth-string-breaks-the-rules)).
- **Where it is wrong [inferred]:** when the model says `C:maj/2` or `C:maj/b7` (inversions of sus2 or seventh colour) the triad reduction gives `C`, which is fine; but `E:7` in a blues or `G:7` before `C` is a colour a `full` sheet should keep because the ukulele `G7 0212` is **easier** than `G 0232`. The tiers conflate "harder to play" with "more notes in the name".
- **Research framing [verified]:** Jiang et al. observe that "most quality errors are from mapping complex chord qualities to simpler ones" ([ISMIR 2019 paper 78](http://archives.ismir.net/ismir2019/paper/000078.pdf)); Koops et al. measured inter-annotator agreement of 0.73 for major/minor and 0.60 for sevenths on 50 Billboard songs, and the Humphrey and Bello "With or Without You" table shows six Ultimate Guitar transcriptions that are "equivalent at the major-minor level" while differing in sevenths and sus, with no effect on their user ratings (Koops 2019, [UvA PDF](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf); Humphrey and Bello 2015). The practical reading: the major/minor layer is the trustworthy one; seventh and sus layers are optional colour and should be presented as such.

### 1.7 Root spelling ignores the key

- **Observed [verified]:** `transpose_label` spells with sharps; display keeps whatever the model wrote (the model wrote `Bb:maj` for Summer of '69 but `C#:maj` for Wet Leg's passing chord and PSSOM). A capo-shifted result that lands on pitch class 3 prints `D#`, never `Eb`. Nothing was wrong on the four runs because the transpositions happened to land on naturals.
- **Why it matters [verified]:** UkuTabs and Live Ukulele chord charts spell by key (Bb, Eb, Ab in flat keys), chords-db keys are `C Db D Eb E F Gb G Ab A Bb B`, and the diagram legend will otherwise show `A#` beside a `Bb` on the same page when one comes from the model and one from transposition.

### 1.8 Voicing choice is sound for beginners but the cost function has two blind spots

- **Observed [verified]:** `shape_cost` charges 1.5 only when chords-db lists a `barres` entry. chords-db lists E `4442` with no barre and fingers `[2,3,4,1]`, so the cost is 2.6 plus 0.4 for a fourth finger = 3.0, against 2.7 for `1402`; `1402` wins, which agrees with every ukulele teaching source ("the easiest way to play the ukulele E chord is the no-barre shape 1 4 0 2", [ukutabs E chord guide](https://ukutabs.com/ukulele-guides/ukulele-e-chord/); [liveukulele E](https://liveukulele.com/chords/major/e/)). Good, but by a margin of 0.3 that a small change to the weights would flip.
- **Blind spot one [inferred]:** the cost treats a three-finger `4442`-type cluster as nearly as easy as `2220`; players rate E, Bb, Bm and B as the hard ones because of **finger crowding and the fret-4 stretch**, not finger count. A span term exists but is linear in frets, not in position.
- **Blind spot two [verified]:** `select_voicings` optimises movement between **adjacent events**, but the sheet shows one diagram per chord for the whole song, so the movement term only matters through its effect on which single shape is chosen. That is the right design for a beginner chart (Chordify and Ultimate Guitar also show one diagram per chord name) and should not be changed; the point is that the movement weight 0.1 is doing less than its name suggests.

### 1.9 Stem choice: the mix is right for chords, and the guitar stem is weak for everything else

- **Verified numbers:** On MUSDB18-HQ, `htdemucs_ft` scores 9.19 dB vocals, 10.11 drums, 10.38 bass, 6.34 other; `htdemucs_6s` scores 8.66, 9.54, 9.11, 5.74 [secondary, StemSplit/Hugging Face model cards: [htdemucs-ft](https://huggingface.co/StemSplitio/htdemucs-ft-pytorch), [aireiter](https://aireiter.com/blog/demucs-stem-separation-models-flags-cost)]. The Demucs README says of 6s: "the piano source is not working great at the moment" and "Quick testing seems to show okay quality for guitar, but a lot of bleeding and artifacts for the piano source"; `htdemucs_ft` "will take 4 times more time but might be a bit better" ([facebookresearch/demucs README](https://github.com/facebookresearch/demucs)). On MoisesDB (88 tracks) the 6-stem HT-Demucs scores guitar **3.07 dB**, piano 1.60 dB and other **0.28 dB** mean SDR, against 11.93 bass and 11.02 drums ([MoisesDB paper, Table 3](https://ar5iv.labs.arxiv.org/html/2307.15913)). The MVSEP guitar leaderboard tops out at 9.01 dB (BS Roformer SW, UVR 5.6) and does not list `htdemucs_6s` at all ([mvsep guitar leaderboard](https://mvsep.com/quality_checker/leaderboard/guitar)); the project's own research notes established that the SW checkpoint has no licence and is not redistributable.
- **Chord recognition on stems [verified]:** the APSIPA 2025 study re-mixed HTDemucs stems with pitched sources doubled and fed BTC: +0.20 WCSR points on triads over 485 songs, statistically significant but tiny, and boosting bass or vocals alone **hurt** (project research note citing [APSIPA 2025 P307](https://webdev.apsipa.org/proceedings/2025/papers/APSIPA2025_P307.pdf)). The Wisconsin project that trained the Jiang model on Demucs bass-plus-other found it "performed worse than the model that was trained using the original dataset" on every metric ([ko28.github.io/chord-transcription](https://ko28.github.io/chord-transcription/)). The design's decision to recognise chords on the mix is therefore correct and well supported.
- **Where stems do help [inferred from the above and the project's own measurements]:** key estimation, the v1.2 fill-by-template, and the power-chord third test all want a chroma **without vocals and drums**, which is exactly what bass+guitar+piano+other summed gives, and the 0.28 dB "other" SDR warns that the 6s `other` stem alone is not a dependable harmonic witness: summing the four harmonic stems (as v1.2 does) recovers most of what 6s smeared between them, because the errors between guitar, piano and other largely cancel in the sum [inferred].

## 2. What others do

### 2.1 Chordify [verified]

- Pipeline (ISMIR 2015 late-breaking demo by Chordify's José Pedro Magalhães): Sonic Annotator extracts downbeats and tonal features; HarmTrace, "a model of Western tonal harmony", selects the chord where the audio is ambiguous: "At beat positions where the audio matches a particular chord well, this chord is used in final transcription. However, in case there is uncertainty ... the HarmTrace harmony model will select the correct chords based on the rules of tonal harmony" ([LBD42 PDF](https://www.ismir2015.uma.es/LBD/LBD42.pdf); de Haas, Magalhães, Wiering, ISMIR 2012, "Improving audio chord transcription by exploiting harmonic and metric knowledge", pp. 295 to 300). HarmTrace is on Hackage ([HarmTrace](https://hackage.haskell.org/package/HarmTrace)).
- Presentation: a beat grid of diagrams synchronised to the YouTube player; instruments guitar, piano, ukulele, mandolin; chord editing by users, with plans to merge edits ([LBD42](https://www.ismir2015.uma.es/LBD/LBD42.pdf); [Hooktheory review](https://www.hooktheory.com/blog/chordify-alternatives/)).
- Toolkit (Premium): transpose, capo, and "Simplifying replaces complicated chords with simple major and minor chords" ([support.chordify.net Toolkit article 11755805765661](https://support.chordify.net/hc/en-us/articles/11755805765661-How-to-use-the-Toolkit), wording from the search snippet; the page itself returned 403). Hooktheory's review: "it doesn't always get them right", corrected by community edits.
- What it gets right that this project does not: harmony-model tie-breaking at uncertain beats; one visible unit per beat so a player sees harmonic rhythm; user correction loop; simplification as a **toggle** on the same data rather than a run option.

### 2.2 Moises [verified]

- Chord view has three levels, "easy, medium, or advanced" (help centre article 6569274648220, from the search snippet; the page returned 403). Capo Mode: the user sets the fret and "Moises will automatically adjust the displayed chord shapes to match the capo position without changing the song's key" ([moises.ai capo mode](https://moises.ai/features/guitar-capo-mode/)).
- What it gets right: three tiers, not two; capo as a user decision with the shapes recomputed instantly.

### 2.3 Ultimate Guitar [verified]

- Pro features: "simplify difficult chords", transpose, "choose the most comfortable chord variation" per chord; tapping a chord shows a diagram with alternatives ([UG help 6741560](https://help.ultimate-guitar.com/en/articles/6741560-what-do-i-get-if-i-subscribe-to-pro); [UG help 6741306](https://help.ultimate-guitar.com/en/articles/6741306-tabs)). Official tabs are a paid tier; user tabs are wiki-edited ([Hooktheory review](https://www.hooktheory.com/blog/chordify-alternatives/)).
- Humphrey and Bello's analysis of six UG transcriptions of one verse: all agree at the major/minor level, two write power chords (`D:5`), three are given relative to a capo, and ratings do not track harmonic detail ([ISMIR 2015 paper 294](http://ismir2015.uma.es/articles/294_Paper.pdf), Table 3). The printed convention is "Capo n" in the header and shapes written relative to it, which the v1.1 header already follows.

### 2.4 Songsterr and Riffstation [verified]

- Songsterr is tab-first, with fingerpicking tablature as its strength and chord charts secondary; the free tier is throttled ([Hooktheory review](https://www.hooktheory.com/blog/chordify-alternatives/)).
- Riffstation (Fender) detected chords and synced diagrams with the audio, with loop, slow-down and pitch controls; its chord detection "frequently faltered, requiring corrections"; web and iOS ended in 2018 and the desktop app in 2019 ([AlternativeTo](https://alternativeto.net/software/riffstation/about)). Nothing to copy except the lesson that a chord viewer without an edit path is judged by its worst bar.

### 2.5 Chord ai [verified from store listings]

- Tiers of chord type: basic (maj, min, aug, dim), sevenths and sus in the standard tier, extended qualities in Pro; displays chords "organized into bars and beats"; ukulele diagrams; offline ([Chord ai listing](https://www.bluestacks.com/campaign/com.chordai/en)). The "95%+ accuracy" claim is marketing, not a measurement.

### 2.6 TheoryTab (Hooktheory) [verified]

- Shows chords in relative (Roman numeral, colour-coded) notation and transposes with mode changes for free ([Hooktheory review](https://www.hooktheory.com/blog/chordify-alternatives/)). Relevant because a relative view makes a key change and a capo trivially explainable: "same shapes, capo up one".

### 2.7 Printed chart conventions [verified]

- iReal Pro: four bars per line is the standard; "Spacing is not decoration. It is how you write the rhythm"; `%` repeats a bar ([irealpro.com chart layout](https://www.irealpro.com/learn/chart-layout)).
- ChordPro: `{soc}`/`{eoc}` for choruses, `{chorus}` to recall one, `{comment: Repeat 2x}` for repeats, `{define}` for custom shapes ([chordpro.org cheat sheet](https://chordpro.org/beta/chordpro-cheat_sheet/); [chordpro46](https://chordpro.org/chordpro46.html)).
- Open-source capo calculators rank positions "by how many of your chords become open shapes ... a lower fret wins when two positions tie" ([capo-calc, MIT](https://github.com/nobodywasishere/capo-calc); [CAPOOT](https://github.com/gumballoon/capoot)). The project's `score_capo` is a cost-weighted version of the same idea.

### 2.8 Teaching sources on simplification for ukulele [verified via the project's own research notes and the pages they cite]

- Live Ukulele's "make songs easier" rules: remove extensions (G9 to G7), undo substitutions (maj7 to major, m6/m7/m9 to minor), play major instead of a seventh "since major chords are contained within 7th chords", ignore `add` notes, ignore slash basses (Em/B becomes Em), use power chords for either mode ([liveukulele how to make songs easier](https://liveukulele.com/songs/how-to-make-songs-easier/)); UkuTabs' five tips are the same ([ukutabs simplify](https://ukutabs.com/ukulele-guides/simplify-difficult-ukulele-chords-5-quick-tips/)).
- Hard-chord work-arounds: E as `4447`, `1402` or transpose up a half step; three-string triads instead of four; transpose with capo or chart ([liveukulele hard chords](https://liveukulele.com/chords/hard-chords/)).
- Easy keys: C, G, F (and D, A) have open shapes; flat keys (Eb, Ab, Bb) are "awkward on the uke" and good candidates for transposition ([songscription blog](https://www.songscription.ai/blog/ukulele-chords-for-any-song), secondary; UkuTabs keys pages [ukutabs.com/ukulele-keys](https://ukutabs.com/ukulele-keys/)). The chords-db probe confirms the mechanics: B, Bm, Bb, Bbm and Db have no open shape.

## 3. Research summary

### 3.1 Chord vocabulary: what is state of the art and what is good enough

- Best large-vocabulary models on the 1217-song corpus: McFee and Bello's structured CR2+S+A scores root 0.861, thirds 0.836, triads 0.812, sevenths 0.729, tetrads 0.671, maj-min 0.855, MIREX 0.852 ([ISMIR 2017 paper 77](https://archives.ismir.net/ismir2017/paper/000077.pdf), Table 2). Jiang et al. (the vendored model) decompose root, bass, triad and extensions and beat the Chordino, DNN, KHMM and CGRU baselines on every small-vocabulary metric; errors run from complex to simple, 11 and 13 are rarely detected, and "the accuracy for a specific component class has a positive correlation with the number of its appearances in the dataset" ([ISMIR 2019 paper 78](http://archives.ismir.net/ismir2019/paper/000078.pdf)). ChordFormer (2025) attacks the same imbalance with a reweighted loss ([arXiv 2502.11840](https://arxiv.org/abs/2502.11840v1)). BTC (Park et al. 2019, MIT) uses the same 170-class vocabulary ([arXiv 1907.02698](https://arxiv.org/pdf/1907.02698); [jayg996/BTC-ISMIR19](https://github.com/jayg996/BTC-ISMIR19)).
- Ceiling: human annotators agree at 0.73 (major/minor) and 0.60 (sevenths) on average; the best MIREX 2017 system already exceeds that by about ten points, so sevenths beyond roughly 0.6 to 0.7 are measuring annotator taste, not audio (Koops et al. 2019, [UvA PDF](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)). Humphrey and Bello's fourth insight: "the subjective nature of chord perception may render objective ground truth and evaluation untenable" ([ISMIR 2015 paper 294](http://ismir2015.uma.es/articles/294_Paper.pdf)).
- Inversions: for implicit-bass models the WCSR on `maj/3` and `maj/5` is stuck near 20% and on minor inversions near 0 to 6% (Deng and Kwok 2016, Table 2, [ISMIR 2016 paper 58](https://archives.ismir.net/ismir2016/paper/000058.pdf)); only one MIREX submission after the new standard supported inversions at all ([arXiv 1709.07153](https://arxiv.org/abs/1709.07153)). Explicit bass estimation (Camacho 2022) brings MajMin+Bass to 90.38% but with hand-set boundaries and no ablation (project research note).
- **Good enough for a ukulele sheet [inferred]:** major/minor plus N, snapped to beats and smoothed to the bar, with sevenths and sus offered as an optional colour layer. That is where the models are accurate (0.85), where annotators agree (0.73), and where the instrument's re-entrant tuning makes bass and inversion information unplayable anyway.

### 3.2 Key

- Profile choice matters more than algorithm: Essentia's `tonictriad`, `edma`, `bgate`, `shaath` and `temperley` profiles exist precisely because Krumhansl's probe-tone profiles underperform on popular and electronic repertoire ([Essentia Key reference](https://essentia.upf.edu/reference/std_Key.html)); Essentia itself is AGPL with CC BY-NC-ND models ([Essentia licensing](https://essentia.upf.edu/licensing_information.html)), so copy the profile idea, not the library. madmom's CNN key model is CC BY-NC-SA ([madmom key docs](https://madmom.readthedocs.io/en/v0.16.1/modules/features/key.html)).
- Chord-based key: Temperley's Bayesian model and the 24-state HMM over chord transitions are the classical approaches ([Temperley](https://music.informatics.indiana.edu/courses/I546/pdf/temperley.pdf); [ISMIR 2006 paper 91](https://archives.ismir.net/ismir2006/paper/000091.pdf)). Mauch and Dixon's DBN and Pauwels' joint key-chord work show key-aware chord relabelling can hurt when borrowed chords occur, so the project's research notes already recommend low weight for key priors on chords; the opposite direction, **key from chords**, is safe.
- Local key: Korzeniowski and Widmer argue that local key needs "the harmonic coherence of the whole piece" ([arXiv 1808.05340](https://arxiv.org/abs/1808.05340)); a regularised Krumhansl segmentation that "balances the number of sections and avoids superfluous modulations" is the simplest published formulation ([Izmir, "A Regularization Algorithm for Local Key Detection"](https://gcris.ieu.edu.tr/entities/publication/8a11f682-70a6-4c4f-861e-8ac868942ca0)); Papadopoulos and Peeters tie local key to harmonic and metric structure ([ip-paris record](https://researchportal.ip-paris.fr/en/publications/local-key-estimation-from-an-audio-signal-relying-on-harmonic-and/)). No pop/rock local-key dataset with modulation marks exists (project research note), so any detector here will be judged on the validation songs by hand.

### 3.3 Harmonic rhythm and smoothing

- Beat-synchronous features plus HMM/Viterbi decoding is the standard remedy for fragmentation (Müller; Cho and Bello 2014 on the relative importance of components, [DOI 10.1109/taslp.2013.2295926](https://doi.org/10.1109/taslp.2013.2295926)). Papadopoulos and Peeters 2011 modelled chord change probability by metric position and improved both chords and downbeats ([HAL hal-00525172](https://hal.archives-ouvertes.fr/hal-00525172)). Over-segmentation dominates the segmentation error for every model in the 2021 coherence study ([ISMIR 2021 paper 55](https://archives.ismir.net/ismir2021/paper/000055.pdf)).
- Practitioner heuristics: a minimum duration around 0.5 s to count a chord as real ([Amadeus ChordZart docs](https://amadeus-chordzart.readthedocs.io/en/stable/pipeline/chord_detection.html)); the project already has beat and downbeat positions, so a **metric** minimum (one beat, with a bar-position prior) is better founded than a seconds one.

### 3.4 Voicing and fingering

- The DadaGP chord-diagram study found guitarists favour minimal movement, open voicings and barre avoidance ([arXiv 2407.14260](https://arxiv.org/pdf/2407.14260)), matching `select_voicings`' intent. No published quantitative ukulele difficulty model was found (project research note Q2 gap, unchanged by this search); `ukechords` has an undocumented heuristic ([nickurak/ukechords](https://github.com/nickurak/ukechords)). The Fretting-Transformer handles capo and tuning as tokens for MIDI-to-tab, which is overkill for chord charts ([arXiv 2506.14223](https://arxiv.org/pdf/2506.14223)).

### 3.5 Separation

- Stems do not improve chord recognition on the mix (APSIPA 2025: +0.20 points; Ko: worse). `htdemucs_ft` improves the four stems by about 0.5 to 1.3 dB over `htdemucs_6s` at four times the time ([Demucs README](https://github.com/facebookresearch/demucs); model cards). The six-stem guitar and piano stems are poor in absolute terms (3.07 dB and 1.60 dB on MoisesDB) and the 6s `other` stem is near zero SDR because guitar and piano were removed from it ([MoisesDB Table 3](https://ar5iv.labs.arxiv.org/html/2307.15913)). Better guitar models exist (9 dB) but are unlicensed or hosted only on MVSEP ([mvsep leaderboard](https://mvsep.com/quality_checker/leaderboard/guitar)); `audio-separator` (MIT) can list models with SDR via `--list_models` and run them on CPU ([python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator)).

## 4. Easy wins

Each item names the code it touches, the evidence, and what to measure. None repeats a v1.2 item.

### 4.1 Detect power chords by third strength and let the key decide the printed quality

- **Touches:** `stages/harmony.py` (after `snap_to_beats`), `music/triads.py`, `schemas.ChordEvent` (new `power: bool = False`), `music/arrange.py::simplify_for_tier`.
- **Rule:** for each `maj` or `min` event, take the mean CQT chroma of the summed harmonic stems over the event (the v1.2 fill code already computes bar chroma from the same stems), compute `third = max(chroma[root+3], chroma[root+4])` and `fifth = chroma[root+7]`; if `third / fifth` is below a measured threshold (start around 0.35, calibrate on PSSOM's verse against Summer of '69's open chords), mark the event `power` and set `triad` to the diatonic quality of that root in the estimated key (I, IV, V major; ii, iii, vi minor; vii dim or, for a sheet, the major a tone below). Print the chord name with a small `5` superscript in the cell when `tier == full`; print the diatonic triad name in `easy`.
- **Evidence:** PSSOM `C#:maj` 30% of the song; the model has no `:5` class; McFee and Bello's power-chord mapping statement; Live Ukulele's "a power chord can be used for either" (so printing the diatonic triad is what charts do).
- **Measure:** PSSOM verse relabelled to C#m (Am shape at capo 4); no `power` events on Summer of '69, Wet Leg or the Chelsea verses.

### 4.2 Estimate the key from chord time (tonic-triad weighting) with the chroma as tie-breaker, and print a hedge when the margin is small

- **Touches:** `music/key.py` (new `key_from_chords(events, power_flags)`), `stages/harmony.py`, `render/html.py` header.
- **Rule:** for each of 24 keys, score = time-weighted share of events whose triad is diatonic, plus a bonus for the tonic triad being the most frequent chord or the first or last non-N chord (the "tonic triad" insight from the MTG evaluation). Power-chord events count for either mode. Combine with the Krumhansl score on **harmonic-stem** chroma (not mix) only to break ties. Store both top candidates and the margin in `Key`; when the margin is under a measured threshold, the header prints `Key: D major (or G major)`.
- **Evidence:** Chelsea 0.766 vs 0.762 with C and Am in the chord set favouring G (94.7% diatonic vs 91.0%); PSSOM tie decided wrong; the lessons' hand calculation that chord-time with the power chord relabelled gives about 97% for E/C#m.
- **Measure:** Summer of '69 stays D; Wet Leg stays C; PSSOM becomes C# minor (or E major, both acceptable, both print the same shapes); Chelsea prints the hedge.

### 4.3 Merge sub-beat and off-position chord fragments by harmonic rhythm

- **Touches:** `music/snap.py` (new pass after run merging), `schemas.ChordEvent` (optional `merged_from: int = 0`).
- **Rule:** inside a bar, an event shorter than one beat is absorbed into the longer neighbour within the same bar. An event of one beat is kept only if it starts on beat 1 or beat 3 (in 4/4) **or** the same two-chord pattern recurs in a neighbouring bar of the same section; otherwise it is absorbed. Never merge across a bar line. `confidence` of the result is the time-weighted mean.
- **Evidence:** 13 sub-1.2 s events in Chelsea Dagger, 6 in PSSOM, 0 in Summer of '69 (whose chart is right); Papadopoulos and Peeters on metric position; the 2021 coherence paper on over-segmentation being the limiting error. PSSOM's legitimate E-A on beats 1 and 3 survives because it sits on beat 3 and recurs.
- **Measure:** Chelsea cell count with two names falls; Summer of '69 unchanged (72 of 75 changes already on bar starts); PSSOM chorus keeps `C / F` cells.

### 4.4 Render the no-capo alternative that arrange already computes

- **Touches:** `music/score_builder.py` (copy `no_capo_alternative` shapes into a `Score.alternative_diagrams` list), `render/templates/sheet.html.j2` (one line under the legend: `Without a capo: C# 1114, E 4442, B 4322 ...` in fret notation, matching the v1.2 passing-chord line).
- **Evidence:** the field exists in `arrangement.json` on PSSOM and is dropped; ukulele players use capos less than guitarists (Live Ukulele); Moises and UG treat capo as the player's decision.
- **Also:** print the capo margin in the manifest notes (`ctx.note("capo_margin", ...)`) so a thin decision (Chelsea 0.11) is visible without rerunning.

### 4.5 Spell roots by key

- **Touches:** `music/arrange.py::transpose_label` (take a `prefer_flats: bool`), `music/shapes.py::display_name_for` (respell from the key), `render/html.py::_shape_key`.
- **Rule:** flats for F, Bb, Eb, Ab, Db, Gb major and D, G, C, F, Bb minor; sharps otherwise; a chromatic passing chord keeps the direction of motion (ascending sharp, descending flat) when both neighbours are known, else the key spelling. Apply to the shape key shown with a capo.
- **Evidence:** `transpose_label` always uses `_SHARPS`; chords-db keys are flat-spelt; UkuTabs and UG spell by key.
- **Measure:** no sheet mixes `A#` and `Bb`; Wet Leg's passing chord between C and Dm prints `C#`.

### 4.6 Add a `medium` tier and make the tiers about playability, not name length

- **Touches:** `options.tier` (add `medium`), `music/arrange.py::simplify_for_tier`.
- **Rule:** `easy` = triads only (as now). `medium` = triads plus dominant sevenths and `sus4`/`sus2` **when the seventh or sus shape costs no more than the triad shape** (G7 `0212` vs G `0232`; C7 `0001` vs C `0003`; A7 `0100` vs A `2100`), otherwise the triad. `full` = as now. Record the reason in `substitutions`.
- **Evidence:** Moises has three levels, Chord ai three, Chordify one toggle; Live Ukulele says to play major for a seventh because the triad is contained in it, which cuts both ways when the seventh is the easier shape; chords-db C7 first position is `0001`.
- **Measure:** no change on the four runs today (no sevenths were emitted), so test on the synthetic clip and on a blues upload.

### 4.7 Slash chords: keep the current drop, but say so, and keep the one case that matters

- **Touches:** `music/shapes.py::_split_label` (return the bass too), `music/arrange.py::simplify_for_tier` (record `"bass dropped (not a chord tone)"` only when the bass is outside the triad), `score.json` (no change).
- **Rule:** always drop the bass for the shape (re-entrant tuning has no bass to play); in `full` tier print the slash in the cell only when the bass is **not** a chord tone of the triad (`C/B`, `G/F#`), since that is the only case where a player would hear a difference, following the Live Ukulele rule.
- **Evidence:** Live Ukulele and UkuTabs rules; Deng and Kwok's 20% inversion WCSR says the model's `/3` and `/5` are not trustworthy enough to print anyway.

### 4.8 Use harmonic-stem chroma, not the mix, wherever chroma is read

- **Touches:** `music/key.py::chroma_mean_for` (and the v1.2 fill and the 4.1 third test share one helper).
- **Rule:** `chroma = chroma_cqt(bass + guitar + piano + other)`; never the mix, never the 6s `other` stem alone.
- **Evidence:** MoisesDB 6s `other` 0.28 dB SDR; the lessons' stems table shows vocals dominating PSSOM's verses; Krumhansl on the mix produced two coin-toss keys.
- **Measure:** Chelsea and PSSOM key margins move away from zero; Summer of '69 and Wet Leg unchanged.

### 4.9 Sheet hygiene that costs almost nothing

- Print the key confidence hedge (4.2) and the capo margin.
- Print `Capo 4` as its own bold line near the title, UG style, not only in the facts row; it is the first thing a player needs to set.
- Legend: order diagrams by first appearance (as now) but put the capo-relative key's I, IV, V first when the song is diatonic; this is how UkuTabs chord-sheet legends read [inferred from the pages; not a documented rule].
- `crowded` cells (three names): shorten to the two longest chords when the third is a sub-beat fragment (4.3 removes most of these anyway).
- Write `score.json` `chord_diagrams` with fret strings (`0232`) as well as shapes, so the passing-chord and no-capo lines and the legend share one formatter.

## 5. Deeper options

### 5.1 Local key with a key-lift rule

- Beat-synchronous harmonic-stem chroma per **section** (the grid already has sections of four bars or more); correlate each section against 24 tonic-triad-weighted profiles; Viterbi over sections with a high self-transition so only sustained changes register; detect the specific "last chorus up one or two semitones" shape as a special case because it is more than half of all pop key changes (52% of key changes in US number ones 1958 to 1990 are a semitone or tone near the end, per [Tedium's summary](https://tedium.co/2022/11/09/the-death-of-the-key-change)). Arrange then scores the capo per key segment and, when the lift is one or two frets, prints "Chorus 3: same shapes, capo +1" rather than a second legend. [inferred design; literature in 3.2]
- Validation needs a modulating song added to the set (none of the five has one).

### 5.2 A bar-level chord decoder with a harmonic-rhythm prior

- Replace the per-beat majority in `snap.py` with a small Viterbi over beats whose states are the model's beat labels, with transition cost depending on metric position (cheap at bar start, dearer at beat 3, dearest elsewhere) and on the section's observed change rate (Summer of '69's verse changes every two bars; the prior should learn that from the first pass). This is Papadopoulos and Peeters' idea in the project's own terms and subsumes 4.3. [inferred]

### 5.3 Difficulty-calibrated shape cost

- Replace `shape_cost` weights with an ordinal tier read from the shape itself: `open` (base fret 1, no barre, at most three fingers, span at most two frets), `stretch` (span three or four frets, or four fingers), `barre`, `high` (base fret above 3). Score capo and voicings on the tier first, cost second. Keeps E `1402` ahead of `4442` by category rather than by 0.3, and makes B/Bm/Bb/Bbm/Db (the five chords with no open shape) the explicit targets a capo search is trying to remove. [inferred; no published ukulele difficulty model exists]

### 5.4 Chord model options if the vocabulary ever has to change

- BTC (MIT, 170 classes, PyTorch) is the obvious drop-in beside Chord-CNN-LSTM; it will not fix power chords either (its vocabulary has no `:5`). The structured-training line (McFee and Bello, ChordFormer) is what would, by predicting pitch classes rather than labels, but no CPU-ready release with weights under a permissive licence was found in this search. Training on synthetic audio is an emerging route ([arXiv 2508.05878](https://arxiv.org/html/2508.05878v1)). Given the 0.73 annotator ceiling at major/minor and the project's four clean runs, changing the model is the lowest-value deep option; the third test in 4.1 is the cheap fix.

### 5.5 Separation configuration

- Option A: keep `htdemucs_6s` as the only separator (MIT, one pass). Option B: run `htdemucs_ft` (4 stems, about four times the time) and derive an accompaniment stem `mix - vocals - drums` for strum onsets, fill chroma and the third test, keeping 6s only when a guitar stem is specifically wanted. Option B roughly doubles separation time on a run that is already 76 to 84% separation; its benefit is a 6.34 dB `other` against the 6s sum of weak stems. Measure before adopting: strum grid fit and section confidence on the five spike songs with each accompaniment source. [inferred; numbers in 1.9]
- A better guitar stem (RoFormer SW at 9 dB) stays behind the existing `--separator roformer-sw` flag because of its licence status.

### 5.6 A correction loop

- Chordify's LBD and UG's wiki model both show that an edit path is what makes an automatic chart trusted. The chain already supports hand-editing `chords.json` and rerunning from arrange; the deeper version is a `youkelele edit <slug>` command that prints the bar grid with event ids and accepts `bar 12: C#m`, writes the file and reruns from arrange, so a user never opens JSON. [inferred]

## 6. Sources

Project (read-only):
- `docs/superpowers/specs/2026-10-03-real-run-lessons.md`, `2026-10-03-v1-1-validation.md`, `2026-10-03-ukulele-tab-chain-design.md`, `...-v1-1-design.md`, `...-v1-2-design.md`, `2026-10-03-spike-models.md`.
- `src/youkelele/music/{arrange,shapes,triads,key,snap,score_builder}.py`, `stages/{arrange,harmony}.py`, `models/chords.py`, `render/{grid,html}.py`, `data/chords-db/ukulele.json`.
- `runs/{sexhetcxqy4,9f06qzcvuhg,0uib9y4ofps,lbc6ccztp5e}/0{3,5,6}_*`.
- `~/.youkelele/models/chord_cnn_lstm/data/submission_chord_list.txt`.
- `C:\Users\gethi\sources\research_notes\...\verification_papers_and_libraries.md`, `bass_anchor_and_local_key.md`, `tablature_theory_and_strumming.md`, `techniques_and_ukulele_arrangement.md`.

Papers and documentation:
- Jiang, Chen, Li, Xia, "Large-vocabulary chord transcription via chord structure decomposition", ISMIR 2019: http://archives.ismir.net/ismir2019/paper/000078.pdf ; repository https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition
- McFee, Bello, "Structured training for large-vocabulary chord recognition", ISMIR 2017: https://archives.ismir.net/ismir2017/paper/000077.pdf
- Humphrey, Bello, "Four timely insights on automatic chord estimation", ISMIR 2015: http://ismir2015.uma.es/articles/294_Paper.pdf
- Deng, Kwok, "Large vocabulary automatic chord estimation using deep neural nets", 2017: https://arxiv.org/abs/1709.07153 ; ISMIR 2016 hybrid paper: https://archives.ismir.net/ismir2016/paper/000058.pdf
- Koops et al., "Annotator subjectivity in harmony annotations of popular music", JNMR 2019: https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf
- Park et al., "A bi-directional transformer for musical chord recognition", ISMIR 2019: https://arxiv.org/pdf/1907.02698 ; https://github.com/jayg996/BTC-ISMIR19
- ChordFormer, 2025: https://arxiv.org/abs/2502.11840v1
- Micchi et al., "A deep learning method for enforcing coherence in automatic chord recognition", ISMIR 2021: https://archives.ismir.net/ismir2021/paper/000055.pdf
- Papadopoulos, Peeters, "Joint estimation of chords and downbeats from an audio signal", IEEE TASLP 2011: https://hal.archives-ouvertes.fr/hal-00525172 ; local key: https://researchportal.ip-paris.fr/en/publications/local-key-estimation-from-an-audio-signal-relying-on-harmonic-and/
- Cho, Bello, "On the relative importance of individual components of chord recognition systems", 2014: https://doi.org/10.1109/taslp.2013.2295926
- Müller, chord recognition lecture notes: https://www.audiolabs-erlangen.com/fau/professor/mueller/teaching/2022w_mpa/MPA_material/data/2021_Mueller_MPA_ChordRecognition.pdf
- Mitoma, Furuya, "Accuracy improvement of automatic chord recognition with source separation preprocessing", APSIPA 2025: https://webdev.apsipa.org/proceedings/2025/papers/APSIPA2025_P307.pdf
- Ko, "Automatic chord recognition by music source separation": https://ko28.github.io/chord-transcription/
- Magalhães, "Chordify: three years after the launch", ISMIR 2015 LBD: https://www.ismir2015.uma.es/LBD/LBD42.pdf ; HarmTrace: https://hackage.haskell.org/package/HarmTrace
- de Haas, Magalhães, Wiering, "Improving audio chord transcription by exploiting harmonic and metric knowledge", ISMIR 2012 (pp. 295 to 300): https://www.cs.ox.ac.uk/publications/publication6253-abstract.html
- Temperley, Bayesian key finding: https://music.informatics.indiana.edu/courses/I546/pdf/temperley.pdf ; HMM key from chords, ISMIR 2006: https://archives.ismir.net/ismir2006/paper/000091.pdf
- Essentia Key algorithm and profiles: https://essentia.upf.edu/reference/std_Key.html ; licensing: https://essentia.upf.edu/licensing_information.html
- madmom key module (CC BY-NC-SA models): https://madmom.readthedocs.io/en/v0.16.1/modules/features/key.html
- Korzeniowski, Widmer, local key coherence: https://arxiv.org/abs/1808.05340
- Regularisation algorithm for local key detection: https://gcris.ieu.edu.tr/entities/publication/8a11f682-70a6-4c4f-861e-8ac868942ca0
- Mauch gear-change statistics: https://www.artsjournal.com/lies/2013/02/gear-change/ ; NPR 2022: https://www.npr.org/transcripts/1139232684 ; Tedium 2022: https://tedium.co/2022/11/09/the-death-of-the-key-change
- MoisesDB paper (HT-Demucs six-stem SDR): https://ar5iv.labs.arxiv.org/html/2307.15913
- Demucs README: https://github.com/facebookresearch/demucs ; model cards with MUSDB18-HQ SDR: https://huggingface.co/StemSplitio/htdemucs-ft-pytorch , https://aireiter.com/blog/demucs-stem-separation-models-flags-cost
- MVSEP guitar leaderboard: https://mvsep.com/quality_checker/leaderboard/guitar
- python-audio-separator: https://github.com/nomadkaraoke/python-audio-separator ; ZFTurbo pretrained models: https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md
- Guitar chord diagram suggestion (DadaGP): https://arxiv.org/pdf/2407.14260 ; Fretting-Transformer: https://arxiv.org/pdf/2506.14223
- Synthetic-audio chord training: https://arxiv.org/html/2508.05878v1
- Amadeus ChordZart minimum duration: https://amadeus-chordzart.readthedocs.io/en/stable/pipeline/chord_detection.html

Products:
- Moises Guitar Capo Mode: https://moises.ai/features/guitar-capo-mode/ ; chord detection help (403 at fetch, snippet only): https://help.moises.ai/hc/articles/6569274648220-How-do-I-use-Chord-Detection
- Chordify Toolkit (403 at fetch, snippet only): https://support.chordify.net/hc/en-us/articles/11755805765661-How-to-use-the-Toolkit ; Hooktheory review of Chordify, Songsterr, TheoryTab, UG: https://www.hooktheory.com/blog/chordify-alternatives/
- Ultimate Guitar Pro features: https://help.ultimate-guitar.com/en/articles/6741560-what-do-i-get-if-i-subscribe-to-pro ; tabs help: https://help.ultimate-guitar.com/en/articles/6741306-tabs
- Riffstation history: https://alternativeto.net/software/riffstation/about
- Chord ai listing: https://www.bluestacks.com/campaign/com.chordai/en
- iReal Pro chart layout: https://www.irealpro.com/learn/chart-layout ; ChordPro cheat sheet: https://chordpro.org/beta/chordpro-cheat_sheet/
- capo-calc (MIT): https://github.com/nobodywasishere/capo-calc ; CAPOOT: https://github.com/gumballoon/capoot

Ukulele practice:
- Live Ukulele: slash chords https://liveukulele.com/chords/ukulele-slash-chords/ ; E chord https://liveukulele.com/chords/major/e/ ; capos https://liveukulele.com/lessons/theory/transposing/capos/ ; hard chords https://liveukulele.com/chords/hard-chords/ ; simplifying https://liveukulele.com/songs/how-to-make-songs-easier/
- UkuTabs: E chord https://ukutabs.com/ukulele-guides/ukulele-e-chord/ ; simplify tips https://ukutabs.com/ukulele-guides/simplify-difficult-ukulele-chords-5-quick-tips/ ; keys https://ukutabs.com/ukulele-keys/ ; transposing guide (403 at fetch) https://ukutabs.com/ukulele-guides/transpose-ukulele-chords/
- Ukulele Hunt slash chords: https://ukulelehunt.com/?p=598 ; re-entrant tuning explainer: https://cursa.app/en/article/high-g-or-low-g-why-the-ukuleles-fourth-string-breaks-the-rules
- Songscription on easy keys (secondary): https://www.songscription.ai/blog/ukulele-chords-for-any-song
