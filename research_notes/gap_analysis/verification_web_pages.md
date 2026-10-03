# Verification of previously blocked web pages (browser session)

Method: every page below was opened in a real Chromium browser (Playwright) on 2026-10-03, because plain HTTP fetches in the earlier research rounds returned 403, CAPTCHA, geo-blocks or empty client-rendered shells. Help centres on Zendesk (Chordify, Moises) were read in full via their public `/api/v2/help_center/en-us/articles.json` endpoint from inside the browser session; everything else was read from the rendered DOM. Quotes are verbatim. "Report impact" says whether the page confirms, changes or adds to what the two reports currently say.

Scope reminder: only web pages on sites that blocked automated fetching are covered here. Academic papers, PyPI/GitHub facts and library internals are left to the other verification agent.

---

## 1. Chordify (help centre, premium page, song pages)

### Previously unverified
Whether users can edit chords; whether strumming patterns are shown; what Chordify says about accuracy, capo, "simplify", slash chords, Song Lessons strums, BPM/tempo; whether user corrections are shared.

### What the pages say
- The public FAQ page at https://chordify.net/pages/faq/ renders only the broken shortcode text `[ultimate-faqs]`; the working help centre is https://support.chordify.net/hc/en-us (Zendesk, 77 articles, all updated 2026-10-01).
- **Strumming (the "near-impossible" claim, verbatim):** "Unfortunately, we're not able to accurately detect strumming patterns on Chordify - this is near-impossible to detect accurately with algorithms, so it is unlikely this would be added in the future. With our Loops feature though, you can repeat sections of songs, and this is a useful way of practising any tricky patterns until you get the hang of them!" — [Does Chordify show the strumming patterns?](https://support.chordify.net/hc/en-us/articles/360019489618-Does-Chordify-show-the-strumming-patterns)
- **Song Lessons (iOS only) do include strumming patterns, but as curated lesson content, not detection:** "Note: Song Lessons are currently only available on the iOS app" ... "We divided the process into learning the chords, learning the transitions and learning the strumming pattern of this section." ... "You'll also see if you need a capo to play the song, what tuning the song is in and the tempo/BPM of the song." ... "100% is the accurate tempo for the song, 50% is half time and 200% is double time." — [What are Song Lessons?](https://support.chordify.net/hc/en-us/articles/33951891429917-What-are-Song-Lessons)
- **Editing chords (website only):** "Please note that editing is *only* available on our website!" Features: toggle meter "between a 3/4 or 4/4 time signature"; delete, move (Ctrl/Cmd + arrows), add/replace by typing the chord name ("For a flat sign, just type ' b', for a sharp , use the hashtag"); copy/paste ranges; rests via "~" or "n"; **bar-line correction**: "Sometimes the automatic beat-tracker does not put the bar lines in the right place ... You can however, 'shift' the chord sequence to correctly align with the bar lines"; downloads (MIDI/PDF) use the edited version; "Switching between edited and automatically recognized chords ... go to the Edits section below the video player ... and click the Chordify version". — [How to edit chords](https://support.chordify.net/hc/en-us/articles/360002148717-How-to-edit-chords)
- **Sharing of user edits:** "You can share your chord edits via Facebook, X, Whatsapp, or Email" and "If someone shares an edit with you, or you open a public edit of a song, you can copy it to your own library". Song pages carry an "Edits — Check out how other users improved the chords of this song" block listing "Chordify" (original) and user edits (e.g. "Anonymous" on the PSSOM page). Embedding supports "only the default versions", not edits. — same article; [PSSOM song page](https://chordify.net/chords/def-leppard-songs/pour-some-sugar-on-me-chords)
- **Capo / transpose (Premium):** "A capo is a clamp you put on the strings of your guitar or ukulele that helps you to play easier chord shapes, without changing the key of the song ... Just move the digital capo up and down the digital fretboard. You will notice that the chord diagrams change when you move the digital capo." Transpose moves "one semitone up or down with every click"; a Chrome "Chordify Transpose Extension" also pitch-shifts the YouTube audio. — [How to use Premium features](https://support.chordify.net/hc/en-us/articles/360002164538-How-to-use-Premium-features)
- **Tempo/BPM:** "The original tempo is displayed as 100%, with the BPM displayed below ... For YouTube songs on the website, you can adjust the tempo in smaller steps of 5%, from 50% to 200% speed." MIDI downloads come in two forms, one "fixed tempo version which is great for creating sheet music", and "the downloaded MIDI file name will contain the right tempo". — same article; [Why doesn't the MIDI file sound like the song?](https://support.chordify.net/hc/en-us/articles/360001415518-Why-doesn-t-the-MIDI-file-sound-like-the-song)
- **Simplify / slash chords:** the entire help centre contains no article or sentence about a "simplify" mode or slash/inversion chords (full-text search of all 77 article bodies for "simplif", "slash", "inversion" returned nothing relevant). Song pages render power chords (C♯⁵, E⁵, B⁵) and sevenths (C♯⁷) as first-class chord labels, and spell the Summer of '69 bridge as F, A♯, C (sharps, not B♭) — [S69 song page](https://chordify.net/chords/bryan-adams-songs/summer-of-69-chords).
- **Accuracy wording:** Premium page: "We combine artificial intelligence (AI) with music researchers (humans) to calculate original chords from audio signals." and the help centre: "At Chordify we're currently mainly focused on extracting chord data from songs—our algorithm is not at a point where it can reliably transcribe individual melody lines". "We don't offer tablature, but you can view fretboard chord diagrams for guitar or ukulele". — [Premium](https://chordify.net/premium); [melodies](https://support.chordify.net/hc/en-us/articles/360019357917-Does-Chordify-provide-melodies-as-well-as-chords); [sheet music/tablature](https://support.chordify.net/hc/en-us/articles/360020910138-Does-Chordify-provide-sheet-music-tablature)
- **Instruments / tiers / price:** guitar, piano, ukulele, mandolin; Toolkit (tuner, metronome, chord trainer, live chord detection) is "guitar only"; Basic £2/mo, Premium £3/mo, Premium Plus £4/mo billed yearly (GBP, 2026-10-03). — [Which instruments](https://support.chordify.net/hc/en-us/articles/360002272998-Which-instruments-can-I-use-with-Chordify); [Toolkit instruments](https://support.chordify.net/hc/en-us/articles/31904455208093-What-instruments-can-I-use-with-the-Toolkit-features); [Premium](https://chordify.net/premium)
- **Copyright stance:** "chord progressions are not considered innovative or sufficiently unique enough to be copyrighted on their own ... copyright owners ... can request the retraction of individual songs by emailing retract@chordify.net". Lyrics are "provided by LyricsFind" plus an AI "Generate Lyrics" feature (Premium Plus). — [copyright](https://support.chordify.net/hc/en-us/articles/360001420738-Does-this-not-infringe-copyright); [Lyrics on Chordify](https://support.chordify.net/hc/en-us/articles/38862626089885-Lyrics-on-Chordify)
- **Song-page data for the two targets:** Summer of '69 (version indexed is "Live in America"): key D, 143 BPM, chords A D Bm G (+E, F, A♯, C). Pour Some Sugar on Me (version indexed is the Coyote Ugly soundtrack cut): key shown as **B**, 86 BPM, chord vocabulary C♯⁵ C♯⁷ C♯ F♯ B E A E⁵ B⁵, FAQ answer "Def Leppard plays Pour Some Sugar on Me in B major". — [S69](https://chordify.net/chords/bryan-adams-songs/summer-of-69-chords); [PSSOM](https://chordify.net/chords/def-leppard-songs/pour-some-sugar-on-me-chords)

### Report impact
**Confirms** the "near-impossible" strumming quote and the no-tab/no-melody position; **adds** concrete edit-tool semantics (meter toggle, bar-line shift, rest token, edited-vs-original toggle, public user edits) that the correction-workflow section can cite; **adds** two data points that matter for the pipeline: Chordify labels PSSOM's key as "B" (a dominant-of-E mislabel) and spells flats as sharps, both good regression-test cases. Simplify/slash-chord behaviour remains **undocumented** by Chordify.

---

## 2. Moises (help centre and Chord Finder page)

### Previously unverified
Chord Finder easy/medium/advanced levels, ukulele profile, chord editing, lead/backing vocal and lead/rhythm guitar separation, pricing of those features.

### What the pages say
- **Levels and views:** "On the web or desktop app, you can also set the chord view to easy, medium, or advanced." and "On the mobile app, you can change your view to simplified, add a capo, or change the notation; click on Song Settings > Chords and select your preferred options." Free accounts: "limited to the song's first minute". — [How do I use Chord Detection?](https://help.moises.ai/hc/en-us/articles/6569274648220-How-do-I-use-Chord-Detection) (updated 2026-10-03)
- **Marketing page:** "Switch between Easy, Medium, and Advanced voicings, see capo-adjusted shapes with Capo Mode, or edit any chord yourself." FAQ: "How accurate is AI chord detection? Most users find our chord detection is quite accurate, but it does occasionally make mistakes. That's why you also have the option to manually edit chords so they appear correctly moving forward." New: chord-chart export "as a web link, or as an iReal Pro or MusicXML file", "chords aligned over the lyrics, organized by song section, with key, tempo, and time signature up top". — [Chord Finder](https://moises.ai/features/chord-finder/)
- **Chord editing inside Moises Studio:** "In the chord area, click AI Detect. The system detects chords, root key, time signature, and tempo from your track. Double-click any chord to edit or fix changes if something's off." Metronome subdivision "2×" gives half-beat snap for chord changes. — [Moises AI Studio](https://help.moises.ai/hc/en-us/articles/21745204066076-Moises-AI-Studio-Your-All-in-One-AI-Music-Creation-Platform)
- **Ukulele:** the word "ukulele" does not occur anywhere in the 116 help-centre articles; the Chord Finder page only says "Built for guitar and beyond" and "Chord diagrams show real fingerings". No ukulele chord-diagram profile is documented.
- **Separation tiers:** Free: "2 stems: Vocals and Instrumental" or "4 stems: Vocals, Drums, Bass and Other", "limited to 5 uploads per month, with files up to 5 minutes long". Premium: "Voice: Vocals, Lead Vocals, Background Vocals; Strings & Fretted: Bass, Guitars, Acoustic Guitars, Electric Guitars, Lead Guitars, Rhythm Guitars, Strings; Keyboards: Piano, Grand Piano, Keys; Winds; Drums". Constraint: "You can select up to 5 instruments per upload, and the extended options within a group can't be combined — for Guitars, for example, you can pick Guitars, or Acoustic and Electric, or Lead and Rhythm, but not all three." Pro adds Female/Male Vocals, Brass/Reeds/Woodwind, drum parts, Hi-Fi models, 48 kHz/24-bit WAV. — [Free plan](https://help.moises.ai/hc/en-us/articles/29530482524316-Which-instruments-can-be-separated-on-the-Free-plan); [Premium plan](https://help.moises.ai/hc/en-us/articles/29530520103324-Which-instruments-can-be-separated-on-the-Premium-plan); [Pro plan](https://help.moises.ai/hc/en-us/articles/360010972019-Which-instruments-can-be-separated-on-the-Pro-plan); [Pro reasons](https://help.moises.ai/hc/en-us/articles/10523828567196-Reasons-to-Subscribe-to-the-Moises-Pro-Plan)
- **BPM behaviour (relevant to the tempo-grid section):** "The Smart Metronome click actually floats by following the song rhythm patterns ... Once the algorithm sets a static BPM number based on that, you may come across this type of issue. Also, remember that not every song sticks to the same BPM throughout its whole playing time, and the algorithm can not detect such nuances in this unit (yet)." — [The BPM is wrong; what should I do?](https://help.moises.ai/hc/en-us/articles/16697903875484-The-BPM-is-wrong-what-should-I-do)
- **Fair use:** "we will generally consider that your usage is abnormal or unreasonable if you regularly (i) process 14 tracks per day or more, or four hundred twenty (420) tracks per month"; "Normal, reasonable personal use does not include bulk processing or commercial uses". — [Acceptable Use and Fair Usage Policy](https://help.moises.ai/hc/en-us/articles/5968943445404-Acceptable-Use-and-Fair-Usage-Policy) (Last Updated August 26, 2025)
- **Pricing:** moises.ai/pricing redirects to the home page; the only price link goes to https://studio.moises.ai/billing/pricing/ which requires login, so no price figures were captured.

### Report impact
**Confirms** manual chord editing and easy/medium/advanced levels; **adds** the Lead/Rhythm and Lead/Background stem options (Premium tier) and the "can't combine sub-options" rule that constrains a Moises-based separation stage; **adds** Moises' own admission that its exported BPM is a single static value. Ukulele-specific support and prices remain **unverified** (not documented / behind login).

---

## 3. Ultimate Guitar (song pages and Terms of Service)

### Previously unverified
Ukulele chord pages for the two songs (chords, capo, strumming), and ToS wording on reproduction, scraping and "Official"/AI chords.

### What the pages say
- **Summer of '69 — Ukulele Chords v1** (id 1326626; 75 votes, rating 4.81; "Tuning: G C E A", "Capo: No capo"; 20,282 views; last edit May 6 2019): chords D, A, Bm, G, F, Bb, C. The page has a **STRUMMING** widget: "INTRO / VERSE 138 bpm", 16 eighth-note slots over two bars; the underlying JSON is `{"part":"Intro / Verse","denuminator":8,"bpm":138,"measures":[3,2,2,3,2,2,2,2,2,2,2,2,2,2,1,2]}`. Rendered (screenshot), every slot is a **down-stroke arrow**; slots coded 2 carry an "x" mark above the arrow, slots coded 3 carry an accent ">" (beat 1 and the "&" of 2), the slot coded 1 (beat 8) is a plain down. So UG's published uke pattern for the verse is a muted straight-eighth down-strum "chug" with accents, not a D/U pattern. Two further user versions exist (ids 1378082, 1771713) plus an "Official" UG version (id 1960235). — [UG S69 ukulele](https://tabs.ultimate-guitar.com/tab/bryan-adams/summer-of-69-ukulele-1326626)
- **Pour Some Sugar On Me:** UG has **no ukulele version** (type filter 800 returns only unrelated songs). The guitar Chords v2 (id 1506911; 246 votes, 4.81; difficulty "novice"; tuning E A D G B E; tonality field "C#m"; no capo; no strumming widget) gives: Riff (C#m); Verse N.C. → C#m; Pre-chorus "F# C#m B | F# C#m B | E B A | E A B"; Chorus "E A B" ×3 then "C#m N.C."; verse 2 also uses C# (major) and D appears later. — [UG PSSOM chords v2](https://tabs.ultimate-guitar.com/tab/def-leppard/pour-some-sugar-on-me-chords-1506911); search listing [type=300](https://www.ultimate-guitar.com/search.php?search_type=title&value=pour%20some%20sugar%20on%20me&type=300)
- **Terms of Service** (Last updated August 24, 2026): §6.2 "You agree that you will not duplicate or otherwise reproduce the Content, or any portion thereof, onto any physical medium, memory or device now known or hereinafter devised; except, however, that you may print out text-based Tablature and/or Lyrics for your personal, non-commercial use, as permitted by our license agreements with Content Providers. With respect to certain songs, Content Providers will not permit this functionality." §6.3 "Content received through the Service may be accessed for your personal, non-commercial use only." §6.4 "You may not copy, reproduce, transfer or access (except as expressly authorized by this Agreement), re-license, reverse engineer ...". §7 grants registered users "Tablature Rights ... solely on or through the Service". The ToS text contains **no** clause mentioning scraping, crawling, bots, automated access, "Official" tabs, or AI/machine-generated chords (searched for "automat", "bot", "harvest", "scrap", "crawl", "data min", "Official", "artificial", "machine"). — [UG ToS](https://www.ultimate-guitar.com/about/tos.htm)

### Report impact
**Confirms** the personal-print-only licence quoted in the gap analysis. **Changes** the strumming assumption for Summer of '69: UG's uke chart shows an all-down, palm-muted eighth pattern with accents rather than the "D-DU-DU-DU" quoted from secondary sources. **Adds** that no UG ukulele chart exists for PSSOM and that the UG ToS has no explicit anti-scraping or AI-content clause (the restriction is the general reproduction ban).

---

## 4. UkuTabs and ukulele-tabs.com

### Previously unverified
Pages for both songs (chords, capo, strum) and the sites' simplification/strumming notation conventions.

### What the pages say
- **UkuTabs — Summer Of '69** (rated NOVICE, 4.3/5 from 6): instrument switch "ukulele / baritone / guitar / mandolin / LEFTY"; toggles "simplify" and "hide easy chords"; key transposer (−/0/+, ♭); tuning options "Standard 'C' tuning (g C E A)" and "Low-G tuning (G C E A)". **SUGGESTED STRUM: "driving 4/4"** shown as a grid "1 d & – 2 d & – 3 d & u 4 d & u" with "HEAR IT", and the line "Prefer something simpler: down-up eighths d u d u d u d u". Prose: "The strumming pattern that fits is the driving 4/4: d – d – d u d u. The groove sits around 140 bpm, a brisk pace. The original recording is in D major. Chord-wise this is an easy one: everything sits at the novice level." Chords: "A, Bb, Bm, C, D, F and G" (bridge F Bb C). Includes a 4-line high-g riff tab (A string 9-10-9, g string 9 / 4-6-7-6-4-6). Footer: "This arrangement is its contributor's own interpretation, shared for private study, education and non-commercial use." — [UkuTabs S69](https://ukutabs.com/b/bryan-adams/summer-of-69/)
- **UkuTabs — PSSOM:** not present. The guessed URL returns 404 and site search for "pour some sugar on me" returns "No artists matching" and no Def Leppard song. — [search](https://ukutabs.com/?s=pour+some+sugar+on+me)
- **ukulele-tabs.com — PSSOM** (uke tab 85624 by Jesperap, 14 Jun 2023): the body is replaced by "Error / Sorry, this content has been blocked in your country." (UK access), so chords/strum could not be read. — [ukulele-tabs PSSOM](https://www.ukulele-tabs.com/uke-songs/def-leppard/pour-some-sugar-on-me-uke-tab-85624.html)
- **ukulele-tabs.com strumming notation convention:** "Patterns are listed using both traditional and alternative rhythm notations", written as beat groups separated by hyphens with lowercase d/u for down/up, x for a muted (chunk) stroke and uppercase D for an accented down, e.g. "#3 : d-du-d-du", "#11 : xu-xu-xu-xu", "#12 : du-xu-du-xu", "#20 : d-D-u-du". — [Strumming patterns](https://www.ukulele-tabs.com/strumming-patterns.html)

### Report impact
**Confirms** the S69 chord set and D-major/~140 BPM priors; **changes** the cited S69 uke strum to UkuTabs' "d – d – d u d u" (with a simpler "d u d u d u d u" alternative) and documents UkuTabs' "simplify / hide easy chords" toggles as a real simplification UI; **adds** the d/u/x/D hyphen-grouped notation convention. PSSOM uke charts remain **unreachable** (absent on UkuTabs, geo-blocked on ukulele-tabs.com).

---

## 5. Hooktheory TheoryTab and terms

### Previously unverified
Whether the key/BPM/section/melody-range figures quoted in the notes are what the pages actually show; the anti-scraping/API wording.

### What the pages say
- **Pour Some Sugar on Me** (last modified Jan 19, 2026): header shows "KEY E maj / BPM 85"; section tabs Verse, Pre-Chorus, Chorus, Bridge; "About the Key: C♯ Minor"; progressions table: Pre-Chorus "I V(sus4) IV", Chorus "I IV V", Bridge "VII I"; melody aggregate "E2 – B4, Melody range across 31 semitones, 0.41 beats/note, Across 97.0 beats of melody"; Chorus stats "Key E Major, Tempo 85 BPM, Meter 4/4, Melody Range B3 – G#4, Most Used Chord I(no3)". The chord lane is drawn as I(no3)/IV(no3)/V(no3) power chords. — [TheoryTab PSSOM](https://www.hooktheory.com/theorytab/view/def-leppard/pour-some-sugar-on-me)
- **Summer of 69** (last modified Jul 17, 2026): "KEY D maj / BPM 139"; melody "A3 – A4, Melody range across 12 semitones, 1.17 beats/note, Across 152.0 beats"; Pre-Chorus and Chorus stats "Key D Major, Tempo 139 BPM, Meter 4/4, Melody Range B3 – A4, Most Used Chord V". — [TheoryTab S69](https://www.hooktheory.com/theorytab/view/bryan-adams/summer-of-69)
- **Terms** (Last updated October, 2025): "Anti-Scraping Policy – Public Display and Use. Except as expressly authorized by Hooktheory (e.g., via a written data license or API terms), no third party may copy, scrape, bulk-download, text-and-data mine, or redistribute the website including the TheoryTab database or any substantial portion of it (including using it to train, fine-tune, or evaluate models). You may not circumvent or bypass rate limits, access controls, or other technical measures. Hooktheory reserves its rights under text-and-data-mining laws and expresses this reservation in machine-readable form; violations may result in access suspension and injunctive relief." — [Hooktheory Terms](https://www.hooktheory.com/terms)

### Report impact
**Confirms** every Hooktheory figure already in the notes (85 BPM / E major–C♯ minor; 139 BPM / D major; melody ranges) and the verbatim anti-scraping clause. Note the PSSOM "E2–B4" aggregate is the whole-song figure; the sung chorus range is B3–G#4.

---

## 6. Songsterr (API, ukulele availability, editor help)

### Previously unverified
Whether any API exists; ukulele tabs for the two songs; tab-editor help.

### What the pages say
- **Undocumented but live JSON endpoints** (same-origin, no key): `GET /api/songs?pattern=<query>&size=N` returns `[{songId, artistId, artist, title, hasChords, hasPlayer, tracks:[{instrumentId, instrument, name, tuning:[MIDI numbers], difficulty, hash}]}]`; `GET /api/meta/<songId>` returns the same plus `aiGenerated`, `revisionId`, `createdAt`, `author`, `restriction`. The legacy documented URLs `/a/wa/api` (HTML 404) and `/a/ra/songs.json` (`{"code":"ERR_NOT_FOUND"}`) are dead; an `inst=ukulele` query parameter is rejected with `"inst":"Should be one of the allowed options"`. Observed on 2026-10-03 from https://www.songsterr.com/ ; not covered by any published terms, so treat as unofficial.
- **Ukulele availability:** no track for either song is a ukulele. Summer Of '69 (songId 24235, revision 8354384, `aiGenerated:false`) has 10 tracks, all guitar [64,59,55,50,45,40], bass [43,38,33,26], organ, pad, drums, "vocals" tracks. Pour Some Sugar On Me (songId 5973, `aiGenerated:false`) tracks: "Steve Clark | Gibson Les Paul Custom | Lead Guitar", "Steve Clark | Solo", "Phil Collen | Fender Stratocaster | Rhythm Guitar" all in **E standard** [64,59,55,50,45,40], "Rick Savage | Hamer Blitz | Bass (5-String)" [43,38,33,28,23], drums, lead and backing vocal tracks. User-made variants titled "Pour Some Sugar On Me (D Standard)" (id 3266231) and "Pour Some Sugar On Me Eb" (id 7142836) also exist, i.e. the community disagrees about the recording's pitch. Help page: "Unfortunately, we don't have many ukulele tabs and don't get many requests from ukulele players." — [search](https://www.songsterr.com/?pattern=summer%20of%2069); [help](https://www.songsterr.com/help)
- **Editor:** "Press E to activate the Tab Editor. To correct a note, simply click on it ... Change a note by typing digits from 0 to 9, or delete it using the backspace key. Any corrections made will be saved automatically when you are signed in". Revision history: "Open the tab's revision history from the revision date under the song title." — [help](https://www.songsterr.com/help)
- **Songsterr AI page:** "Transcribe tabs instantly with AI — Paste a YouTube link and let AI create accurate guitar, bass, and drum tabs in minutes" (YouTube link or audio upload; "Your tab remains private until you choose to share it"). No mention of ukulele or strumming. — [Generate Tabs with AI](https://www.songsterr.com/new)
- Licensing: "Error: 'Sorry this content has been removed' — This means that at the moment we don't have licenses with the publisher of this artist." "All tabs on Songsterr are contributed by users — we don't do transcriptions". — [help](https://www.songsterr.com/help)

### Report impact
**Changes** "Songsterr's documented API endpoints return 404" to "the documented endpoints are dead but an undocumented `/api/songs` + `/api/meta` JSON API is live (unofficial, no terms)". **Confirms** the edit-by-typing-digits workflow with revisions. **Adds** that neither song has a ukulele track, and that Songsterr's main PSSOM tab is in E standard while user forks claim D standard / E♭ — directly relevant to the unresolved "tuning of the Hysteria master" gap.

---

## 7. alphaTab documentation (alphatab.net, v1.8.4)

### Previously unverified
alphaTex lyrics syntax, sync points / external media (IExternalMediaHandler, PlayerMode), chord-diagram syntax, brush/strum arrows, re-entrant tuning syntax.

### What the pages say
- The URL tried earlier, https://www.alphatab.net/docs/alphatex/lyrics, is a genuine **404**; the content lives in the staff-metadata, bar-metadata and beat-properties reference pages.
- **Lyrics:** `\lyrics lyrics` or `\lyrics (startBar lyrics)`. "The lyrics system of alphaTab is borrowed from Guitar Pro. For every track multiple 'lines' of lyrics can be defined which can either start at the beginning or at a later bar. The syllables of the provided lyrics are spread automatically across the beats of the track. Syllables are separated with spaces. If multiple words/syllables should stay on the same beat the space can be replaced with a +. Comments which should not be displayed can be put [into brackets]." Example titled "Combine Syllables (and empty beats)": `\lyrics "Do+Do  Mi+Mi"` over `C4 C4 E4 E4` (a double space leaves a beat empty). Alternative per-beat property: `C4 {lyrics "Do"}` and multi-line `G4 {lyrics 0 "So" lyrics 1 "G"}`. — [Staff metadata](https://www.alphatab.net/docs/alphatex/staff-metadata); [Beat properties](https://www.alphatab.net/docs/alphatex/beat-properties)
- **Sync points:** `\sync (barIndex occurence millisecondOffset ratioPosition)` — "Adds a new sync point for synchronizing the music sheet with an external media source like a backing track or video player ... The barIndex, occurence, ratioPosition parameters define the absolute position within the music sheet. The millisecondOffset defines the absolute position within the external media." Example tail: `\sync 0 0 0 \sync 0 0 1500 0.666 \sync 1 0 4075 0.666 \sync 2 0 6475 0.333 \sync 3 0 10223 1`. — [Bar metadata](https://www.alphatab.net/docs/alphatex/bar-metadata)
- **External media:** `PlayerMode` enum: Disabled 0, EnabledAutomatic 1, EnabledSynthesizer 2, EnabledBackingTrack 3, **EnabledExternalMedia 4** "an external audio/video source is used as time axis". Guide (since 1.6.0): "the alphaTab.synth.IExternalMediaHandler interface has to be implemented ... alphaTab has to be informed about the time updates on the external media ... 50ms updates have shown to work well on even fast songs"; the handler exposes `backingTrackDuration`, `playbackRate`, `masterVolume`, `seekTo(time)`, `play()`, `pause()`, and the page calls `(api.player.output as IExternalMediaSynthOutput).updatePosition(ms)`. "alphaTab cannot mix the synthesized audio and a backing track together". The guide explicitly declines to ship a YouTube integration but gives a worked example using the YouTube IFrame Player API. — [Audio & Video Sync](https://www.alphatab.net/docs/guides/audio-video-sync); [PlayerMode](https://www.alphatab.net/docs/reference/types/playermode); [player.playerMode](https://www.alphatab.net/docs/reference/settings/player/playermode)
- **Chord diagrams:** `\chord (name strings)` — "For every string of the staff tuning, the fret to be played or x for strings not played"; "To avoid inconsistencies with tunings, chords should be defined after the tuning is set"; use with beat property `{ch "C"}`; options `{firstfret 6}`, `{barre 6}` / `{barre (1 3)}`, `{showname false}`, `{showdiagram false}`, `{showfingers false}`; `\chordDiagramsInScore` shows diagrams inline. — [Staff metadata](https://www.alphatab.net/docs/alphatex/staff-metadata)
- **Brush (strum) arrows:** beat properties `bd` / `bu` "Adds a brush stroke effect to the beat" with optional `duration` "in MIDI ticks", e.g. `(0.1 0.2 0.3 2.4 2.5 0.6){bd}` and `{bu 60}`; arpeggio `ad`/`au`. Also `{pm}` palm mute, `x` dead note (`x.3` or `3.3{x}`), `{ac}`/`{hac}` accents, `{lr}` let ring, `{barre 4 half}`. — [Beat properties](https://www.alphatab.net/docs/alphatex/beat-properties); [Note properties](https://www.alphatab.net/docs/alphatex/note-properties)
- **Tuning:** `\tuning (strings)` "The tuning values as pitched notes", e.g. `\tuning (A1 D2 A2 D3 G3 B3 E4)`, with `{hide}` and `{label "..."}`; modes `piano|none|voice`. Nothing in the docs restricts the list to monotonic pitches, so re-entrant `\tuning (G4 C4 E4 A4)` is syntactically expressible, but **no example or statement confirms re-entrant handling** (fret calculation for a high-g 4th string). `\capo fret` exists. — [Staff metadata](https://www.alphatab.net/docs/alphatex/staff-metadata)

### Report impact
**Confirms** the pipeline's assumption that alphaTex can carry lyrics, chord diagrams and sync points, and gives the exact tokens. **Adds** that strum direction is expressible via `{bd}`/`{bu}` brush effects and muting via `{pm}`/`x`, and the external-media handler contract (50 ms updates). Re-entrant-tuning behaviour is still **unverified** from docs (needs an empirical render test).

---

## 8. Lyrics providers' terms (Genius, Musixmatch, LRCLIB)

### Previously unverified
Genius API terms verbatim; Musixmatch developer pricing; LRCLIB licence/usage policy and rate limits.

### What the pages say
- **Genius ToS** (Last Updated January 13, 2026): "Except as expressly authorized by Genius in writing, you agree not to modify, copy, frame, scrape, rent, lease, loan, sell, distribute or create derivative works based on the Service or the Genius Content, in whole or in part, including for any purposes related to AI machine learning/use on AI platforms ... you shall not engage in or use any data mining, robots, scraping or similar data gathering or extraction methods"; "Commercial Use: ... you agree not to use, display, distribute, license, perform, publish, reproduce, duplicate, copy, create derivative works from, modify, sell, resell, exploit (including, without limitation, for A.I. machine learning purposes), transfer or transmit for any commercial purposes/machine learning purposes, any portion of the Service". — [Genius Terms](https://genius.com/static/terms)
- **Genius API docs** (docs.genius.com sits behind a Cloudflare challenge that cleared after ~6 s in a real browser): "Commercial use of the Genius API is not allowed without a license. Please reach out to api-sales@genius.com to discuss commercial usage." The documented resources are Annotations, Referents, Songs, Artists, Web Pages, Search, Account; there is no lyrics-text endpoint listed. — [Genius API](https://docs.genius.com/)
- **Musixmatch:** the old developer plans page now redirects to the Pro API pricing page; there is **no free tier**. Basic $49/mo: "5k total calls / day, 500 lyrics calls / day ... INCLUDES Music metadata, Static lyrics; NOT INCLUDED Time-synced lyrics, Lyrics caching". Grow $199/mo adds "Time-synced lyrics" (2k lyrics calls/day). Scale $499/mo (10k lyrics calls/day). Enterprise "starting from $2,000/mo" is the only tier with "Lyrics caching (licensed only)". — [Musixmatch Pro API pricing](https://www.musixmatch.com/pro/api/pricing)
- **LRCLIB:** "This API has a generous rate limiting in place and is openly accessible to all users and applications. No API key is required"; clients "are required" to send a `User-Agent` "with your application's name, version, and a link" (or `X-User-Agent` / `Lrclib-Client`); on 429 "Your client must honor" `Retry-After`, "Ignoring it ... may result in a temporary ban"; "send requests sequentially ... add a short delay between requests (200–500 ms)". `/api/get` needs `track_name` + `artist_name`, matches only when "the duration matches the record ... or at least with a difference of ±2 seconds"; `/api/search` returns max 20 results, no pagination; records carry `plainLyrics`, `syncedLyrics` (LRC) and a new `lyricsfile` YAML with optional word-level timings (`hasWordSync`). Publishing requires a proof-of-work `X-Publish-Token` from `/api/request-challenge` ("refer to the source code of LRCGET"). CORS is open. **No data-licence statement** appears on the docs page or the dumps page; the dumps page lists one file, `lrclib-db-dump-20260923T042405Z.sqlite3.gz`, 44.3 GiB. — [LRCLIB API docs](https://lrclib.net/docs); [DB dumps](https://lrclib.net/db-dumps)

### Report impact
**Confirms** that Genius forbids scraping and non-licensed commercial API use; **changes** the Musixmatch picture (no free developer tier any more; synced lyrics start at $199/mo); **confirms** LRCLIB is key-less with soft rate limits and **adds** the exact client requirements and the ±2 s duration-matching rule; LRCLIB's data licence remains **unstated** on its own pages.

---

## 9. Production articles (Sound on Sound / Mix) for the two songs

### Previously unverified
First-hand mixing facts (guitar panning, tuning, tempo) for PSSOM and S69.

### What the pages say
- Sound on Sound's site search returns "Found 27649 results" for every query including quoted phrases ("def leppard", "summer of 69"), i.e. the search is non-functional for phrase matching; no Classic Tracks page for either song was surfaced. — [SOS search](https://www.soundonsound.com/search?search_api_fulltext=pour+some+sugar+on+me)
- Mix Online's search for "pour some sugar" returns only two unrelated 1999/2007 articles; no Classic Tracks feature on the song exists on the current site. — [Mix search](https://www.mixonline.com/?s=%22pour+some+sugar%22)

### Report impact
**Still unreachable / probably non-existent.** The "hard-panned doubled guitars" claim stays unsourced. The only new tuning evidence is indirect: Songsterr's main PSSOM transcription is in E standard while user forks claim D standard and E♭ (see §6).

---

## 10. Tunebat / SongBPM / BPMDatabase (85 vs 176 BPM, C♯m vs E)

### Previously unverified
Tunebat values (page was 403); resolution of the tempo-octave and key disagreements.

### What the pages say
- **Tunebat, PSSOM search results** (Cloudflare challenge cleared after ~8 s; a second search then returned HTTP 429, so Tunebat rate-limits browsers too): studio "Pour Some Sugar On Me" — **C♯ minor, 85 BPM, Camelot 12A** (popularity 70); "Remastered 2017" — C♯ minor, 85 BPM, 12A; "Extended Version" — C♯ minor, **170 BPM**, 12A (two entries); live versions 87–88 BPM in A♭ major, C♯ major, B minor, E♭ major; a 2005 Live 8 take B major 90 BPM. — [Tunebat search](https://tunebat.com/Search?q=pour%20some%20sugar%20on%20me%20def%20leppard)
- **Tunebat, Summer Of '69** (Reckless 30th Anniversary): "D Major, Key; 10B, Camelot; 139 BPM; 3:36; Popularity 88; Energy 83; Danceability 51"; MTV Unplugged version listed as A major 141 BPM. — [Tunebat S69](https://tunebat.com/Info/Summer-Of-69-Bryan-Adams/0GONea6G2XdnHWjNZd6zt3)
- Earlier-fetched values for cross-reference (not re-fetched here): SongBPM 176 BPM "half-time at 88"; BPMDatabase 85 BPM; Hooktheory 85 BPM / E major with verse in C♯ minor (§5).

### Report impact
**Resolves** the tempo question as a pure octave ambiguity: the same Spotify-derived feature set gives 85 for the album cut and 170 for the extended mix, and SongBPM's 176 is the doubled count; all human-curated sources (Hooktheory, BPMDatabase, UG's chord page tonality, Tunebat album entry) sit at 85–88. **Resolves** the key question as relative-mode labelling: Tunebat/UG say C♯ minor (verse riff), Hooktheory says E major (chorus) with C♯-minor verse; Chordify's "B major" is the outlier/mislabel. Live versions are genuinely transposed (A♭/E♭/B), so version matching matters.

---

## 11. Live Ukulele, Ukulele Tricks, Ukulele Underground, Ukulele Hunt (notation, chunking, arranging)

### Previously unverified
Sourced descriptions of D/U/x notation, chunk/mute strums, melody arranging heuristics (earlier fetches 403/404).

### What the pages say (Live Ukulele; the others were not reached in this session)
- **Strum notation:** patterns are written against a "1 + 2 + 3 + 4 +" count with D/U letters and dashes for skipped strokes, e.g. "D - D U - U D -", and with parenthesised "invisible strums" to show the hand keeps moving: "D(U)D U(D)U D(U)". "This is key: Keep your hand moving the entire way through the strum pattern!" "Downstrums are usually played on the beat counts (1…2…3…4…)". The page also lists "D U D U D U D U", "D   D U   U D" (DDUUD), and a reggae "U U U U". — [How To Properly Strum Your Ukulele](https://liveukulele.com/lessons/strums/)
- **Chunk/mute:** "the chop has many names, such as: chop, chunk, chuck, mute, chick, chock"; "Instead of strumming and sounding a chord, you quickly attack and then mute the strings in a single motion as your hand moves downward ... The finger should sound the strings before the palm mutes them a split second after. Don't strum, then mute." — [Chunk Strum](https://liveukulele.com/lessons/strums/chunk-strum/); separate [Palm mute](https://liveukulele.com/lessons/techniques/palm-mute/) lesson.
- **Converting guitar tab / range handling:** "Since the ukulele is tuned the same as a guitar capoed on the 5th fret, any number on the tab higher than 5 can be used straight on ukulele. Just subtract 5"; notes below that "can't be converted in this way"; "The guitar's range is an octave and a bit lower than the ukulele ... You can combat these low notes one of two ways: Hop them up an octave. Transpose. Retune/Use a baritone."; "Since everything you play on a high-g string is an octave above a low-G string, you usually have to move the notes onto the E or A-string to play them at the correct pitch." "you always can play a high-g part on a low-G uke. The notes are there. It doesn't necessarily work going the other way." — [Converting Guitar Tabs for Ukulele](https://liveukulele.com/tabs/converting/)
- **Solo/chord-melody arranging rule:** "What you should be going for with a solo arrangement is to play the melody as the highest note at any given point while adding complementary harmonies in clever places." "If you play with a high-g string on your ukulele, be sure to account for the higher octave notes." — [Creating Solo Ukulele Arrangements](https://liveukulele.com/lessons/solo-fingerpicking-arrangements/)
- **Tab-timing caveat:** "Since tab by itself can't show timing ... Sometimes people who want to express the timing for a song will put special notation on top of the text ukulele tab to show note duration." — [How to Read Ukulele TABs](https://liveukulele.com/tabs/how-to-read-tab/)
- Ukulele Hunt's 2009 notation post, Ukulele Tricks and Ukulele Underground were not visited (time budget); the ukulele-tabs.com convention in §4 covers the d/u/x/D grammar.

### Report impact
**Adds** citable, practitioner descriptions for: dash = skipped stroke, parenthesis = ghost stroke, "x"/chunk = attack-then-mute on a downstroke, melody-on-top rule for arrangements, the subtract-5 guitar-to-uke rule and octave-hop/transpose/baritone fallbacks for out-of-range notes. These directly support the techniques/arrangement and vocal-melody sections.

---

## 12. Reddit threads (r/ukulele, r/Guitar, r/musictheory)

### Previously unverified
Community consensus on auto-tab tools, Chordify accuracy and strumming detection (Reddit blocked the crawler).

### What the threads say (read via the site's JSON endpoints in-browser, 2026-10-03)
- **Chordify accuracy:** "Having just tested Chordify on a couple of songs, it seems only capable of recognising major and minor triads. No 7ths, no diminished chords... It seems pretty reliable on very simple songs, but on complex ones - the very ones you're going to need most help - it fails miserably ... it inserts the closest major or m[inor]" (top comment, +5); "I've checked 3-4 songs and NONE of them were right." — [How reliable is Chordify.net?](https://www.reddit.com/r/musictheory/comments/87ankc/how_reliable_is_chordifynet/) (2018). A 2026 r/ukulele thread says Chordify's YouTube playback is now frequently "video unavailable" ("part of the YouTube ad block arms race"), with users migrating to Moises (upload-based) and Chord ai; a commenter's browser extension claims "accuracy is roughly Chordify-tier (not perfect but workable)". — [Chordify alternative?](https://www.reddit.com/r/ukulele/comments/1r5icoj/chordify_alternative/) (2026-02-15, 16 comments)
- **AI tabs (Songsterr):** "Not reliable at all, you're better off learning it by ear" (+6); "the songster tabs would be played in the wrong position of the neck and would miss notes or entirely change parts of songs ... it does get some of the notes right so it sort of give you a quick starting point" (+3); "you'd be better off using one of those things that splits songs out into stem tracks. Then you can solo guitar parts" (+3). — [How reliable are the songsterr ai tabs?](https://www.reddit.com/r/Guitar/comments/1p417k3/how_reliable_are_the_songsterr_ai_tabs/) (2025-11). A 189-point thread complains that "good pre-existing transcriptions [are] getting replaced by nonsense" by contributors using AI. — [Unusably bad A.I. Generated tabs](https://www.reddit.com/r/Guitar/comments/1n9130d/unusably_bad_ai_generated_tabs_getting_more_common/) (2025-09, 99 comments)
- **Strumming:** no thread found where any app is credited with detecting a strum pattern from a recording; advice is to practise by ear ("I try to guess what the pattern is to whatever I'm listening to and 'strum' with one hand on my leg"), with Kala and 8Strummer named as pattern-practice apps. — [Strumming practice app?](https://www.reddit.com/r/ukulele/comments/b3465k/strumming_practice_app/) (2019, 20 pts)

### Report impact
**Adds** the community consensus the existing_implementations note lacked: automatic chords are "a starting point" that fails on extended chords and dense arrangements; AI tabs get string/position choices wrong even when pitches are right (matching the TART 81%-notes/54%-tab finding); nobody expects strum detection from software. Also **adds** a 2026 operational risk: Chordify's YouTube-embed workflow is breaking, pushing users to upload-based tools.

---

## 13. Yousician / Songsterr AI / Klangio product claims

### What the pages say
- **Yousician:** positions itself as a listening/feedback tutor, not a transcriber: "Our award-winning technology listens to you play and gives instant feedback on your accuracy and timing"; ukulele page: "Learn ukulele chords, strumming patterns, plucking, melodies, fingerpicking ..." and "You always know when you're hitting the right notes and strumming the chords on time"; content is "lesson plans created by real ukulele players and music teachers"; supports "soprano or concert" ukulele. No claim of audio-to-tab generation. — [Yousician ukulele](https://yousician.com/ukulele)
- **Songsterr AI:** "Paste a YouTube link and let AI create accurate guitar, bass, and drum tabs in minutes" (guitar/bass/drums only). — [Songsterr AI](https://www.songsterr.com/new)
- **Klangio Guitar2Tabs:** "Strumming or Picking? Your Style, Your Choice – Supports both strumming patterns and picked melodies"; "Multi-Instrument Audio Support – Even if other instruments are present, Guitar2Tabs isolates and transcribes the guitar or bass part"; "Polyphonic & Chord-Aware"; exports "PDF ... MIDI (quantized/unquantized), MusicXML and GuitarPro"; built-in "Edit Mode"; "Free Demo: Transcribe 20 Seconds of Guitar or Bass Audio ... no signup required". No ukulele product; /pricing returned 404. — [Guitar2Tabs](https://klang.io/guitar2tabs/)

### Report impact
**Adds** current vendor claims: Klangio is the only one that markets "strumming patterns" as an input style (a transcription mode, not a detected D/U chart); Songsterr AI is guitar/bass/drums; Yousician does no transcription. None offers ukulele audio-to-tab.

---

## 14. MuseScore handbook (ukulele, tablature, chord diagrams, MIDI import)

### What was reached
- musescore.org/en/handbook/4/tablature now redirects to the new handbook host; the "Customising a tablature stave" page documents `Edit String Data…` (change tuning per string, "Add a string", "Delete a string", "Mark unfretted string 'open'", "Change number of instrument frets") and notes "If the tuning is changed on a tab staff that already contains some notes, fret marks will be adjusted automatically (if possible)". The sidebar lists sibling pages: Fretboard diagrams, Guitar techniques, Creating a tablature stave, Entering and editing tablature notation, Applying capos, Alternate string tunings, Guitar bends, Fretboard diagram legend, Chord symbols, Working with MIDI. — [Customising a tablature stave](https://handbook.musescore.org/en_gb/idiomatic-notation/guitar/customizing-a-tablature-staff)
- Guessed URLs for chord diagrams and MIDI import returned 404; the fretboard-diagram, ukulele-instrument and MIDI-import quantisation pages were **not read** in this session (time budget).

### Report impact
**Partially confirms** that MuseScore 4 can model arbitrary string counts/tunings and fret counts for a tab stave (so a 4-string re-entrant uke stave is configurable); chord-diagram and MIDI-import-quantisation specifics remain **unverified**.

---

## 15. Other items from the Step 1 list

- **Chordify terms (chordify.net/terms was 403 earlier):** the help centre hosts "Terms and Conditions" at https://support.chordify.net/hc/en-us/articles/360002257178-Terms-and-Conditions (readable now; not analysed in detail here). The publisher-licensing question is answered only indirectly by the "chord progressions are not ... copyrighted" FAQ and the retract@chordify.net takedown route (§1).
- **Chord ai help page (HTTP 500 earlier):** not retried.
- **Shazam / ACRCloud terms, Fordham IPLJ article, SponsorBlock categories:** not attempted (out of the prioritised list).

---

## Summary table

| # | Target | Status | One-line result |
|---|--------|--------|-----------------|
| 1 | Chordify | CONFIRMED (+adds) | "near-impossible" strumming quote verified; website-only chord editor with meter toggle, bar-line shift, public edits; no simplify/slash docs; PSSOM key mislabelled "B" |
| 2 | Moises | CONFIRMED (+adds) | easy/medium/advanced + capo + simplified view; manual chord edit; Lead/Rhythm and Lead/Background stems on Premium with "pick one pair" rule; no ukulele mention; prices behind login |
| 3 | Ultimate Guitar | CHANGED | S69 uke chart strum is muted all-down eighths with accents, not D-DU; no PSSOM uke chart; ToS = personal print only, no scraping/AI clause |
| 4 | UkuTabs / ukulele-tabs | CHANGED / PARTIAL | UkuTabs S69: "d – d – d u d u", simplify toggle, 7 chords; no PSSOM on UkuTabs; ukulele-tabs PSSOM geo-blocked; d/u/x/D notation documented |
| 5 | Hooktheory | CONFIRMED | 85 BPM E/C♯m and 139 BPM D; anti-scraping clause verbatim |
| 6 | Songsterr | CHANGED | undocumented live JSON API (/api/songs, /api/meta); no uke tracks; main PSSOM tab in E standard, forks in D/E♭; editor help confirmed |
| 7 | alphaTab | CONFIRMED (+adds) | exact \lyrics, \sync, \chord, {bd}/{bu}, \tuning syntax; IExternalMediaHandler/PlayerMode 4; re-entrant tuning not documented |
| 8 | Genius / Musixmatch / LRCLIB | CHANGED | Genius bans scraping and ML use; Musixmatch has no free tier (synced lyrics from $199/mo); LRCLIB key-less with User-Agent + Retry-After rules, no licence stated |
| 9 | SOS / Mix production articles | STILL UNREACHABLE | neither site surfaces a Classic Tracks article for either song |
| 10 | Tunebat / BPM databases | CONFIRMED (resolved) | PSSOM 85 BPM C♯m (170 for extended mix = octave); S69 139 BPM D major |
| 11 | Live Ukulele etc. | CONFIRMED (+adds) | dash/ghost-stroke notation, chunk = attack-then-mute, melody-on-top rule, subtract-5 and octave-hop conversion rules |
| 12 | Reddit | ADDED | consensus: auto chords are a starting point, fail on 7ths; AI tabs wrong positions; nobody expects strum detection; Chordify YouTube embed breaking in 2026 |
| 13 | Yousician / Songsterr AI / Klangio | ADDED | only Klangio markets "strumming" input; Songsterr AI = guitar/bass/drums; Yousician = feedback tutor |
| 14 | MuseScore handbook | PARTIAL | tab stave tuning/strings/frets configurable; chord diagram + MIDI quantisation pages not read |
| 15 | Other | NOTED | Chordify T&C now reachable via help centre; Chord ai not retried |
