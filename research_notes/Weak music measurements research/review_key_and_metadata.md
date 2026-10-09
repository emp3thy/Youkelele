# Review: key estimation and song metadata (written 2026-10-08 against main at 74c11e0)

Read: `code_map_for_reviewers.md`, Area 7 and the five rules of `reports/Weak music measurements research.md`, `key_and_metadata.md`, `src/youkelele/music/key.py`, `titles.py`, `stages/ingest.py`, `stages/harmony.py`, `models/ytdl.py`, `layout.py` (`resolve_run_dir`), `tests/test_key.py`, `tests/test_titles.py`, `tests/test_stage_ingest.py`, the three validations and the 1.4 one. Three spikes were run read-only on `runs\` (section D); their scripts are in the session scratchpad, not the repo.

## A. Diagnosis

### Key: why Badge printed D

`runs\cream-badge\03_harmony\chords.json` and the manifest's harmony notes give the whole trace:

1. **Candidate gate.** `decide_tonic` scores only roots holding at least `TONIC_MIN_SHARE` 0.2 of chord time. Root shares: D 0.339, A 0.208, E 0.173, C 0.134, G 0.108, B 0.036. So the candidates were D and A. **G and E, the published tonics, were never candidates.** No later vote could name them.
2. **Score vote: D by 0.174.** D = 0.339 + `SECTION_END_WEIGHT` 0.15 x 2/7 (Intro and Chorus 2 end on D) = 0.382; A = 0.208. No `FINAL_CHORD_BONUS`: the song's last chord is B minor (bar 69), not a candidate.
3. **Pair vote: A by 0.050** (`tonic_pair_rule` "A by 0.050"): the C major/A minor set holds 0.807 of chord time, the D major set 0.756.
4. **Mix vote: D major** (24-way Krumhansl on the whole mix).
5. Score and pair disagree, the mix sides with the score: `decided_by` "mix", tonic D, mode major (mode margin 0.489). `_losing_chord_rule` then names A as the hedge, so the sheet header reads **"D major (or A major)"** (`07_score\score.json`: key D major, key_hedge A major). Both names are wrong; the hedge is a fifth above the lead, two fifths from G.

Re-scoring the stored stream over all twelve major-key diatonic sets (the same `_set_share` the pair rule uses) gives **G 0.995, C 0.807, D 0.756**: every chord the model emitted (Am, D, Em, C, G/B, Bm; one E major bar at half credit) sits in G major/E minor. The chord transcription is consistent with the published tab; the key logic is what fails. Badge is a *dominant-heavy* song: the tonic chord G holds 11 percent of the time and the dominant D 34 percent, and the bridge cycles D–C–G/B thirteen times.

**Is it the fifth-error class?** By mir_eval's categories, yes: D major against G major scores 0.5 (fifth); against E minor 0.0 (other). But the mechanism is not the profile confusion the literature describes (dominant sharing six of seven pitch classes). It is a root-share tonic rule applied to a song whose most-played chord is the dominant, with the true tonic gated out before any vote. The research's literal remedy, "when the leader is a fifth above the runner-up and the last chord is the runner-up's tonic, prefer the runner-up", would not fire: the runner-up is A, the final chord is Bm, and the stream's root motions favour D (V-to-I motions into D 9, into G 2; IV-to-I into D 14, into G 12, because the D–C–G/B cycle reads as IV-to-I into D as readily as V–IV–I into G). Only the diatonic-set share carries the G signal. The Cars had the same shape (D 0.335, G 0.285, score margin 0.0505) and the ear confirmed D; there the set share says D 1.000 against G 0.876. So the set share separates the two cases where root share could not.

### Metadata: how "Natan Santos" and "RHINO" reached the sheet

1. `cli` names the run folder through `layout.resolve_run_dir`, which calls `models/ytdl.fetch_metadata`. That function keeps only `_METADATA_FIELDS = ("id", "title", "uploader", "artist", "duration")` and `resolve_run_dir` writes those five to `source_meta.json`.
2. `IngestStage.run` downloads with `writeinfojson` and gets yt-dlp's full info dict, then **replaces it with the five-field `source_meta.json`** when the ids match (`info = fetched`), so `channel`, `uploader_id`, `artists`, `track` are discarded even though they were fetched.
3. `raw_artist = info.get("artist") or info.get("uploader")`. yt-dlp's `artist` is the comma-joined twin of `artists`, filled only from YouTube's "Music in this video" credits or an auto-generated description. Spike 3: of the eleven run URLs only Fame (an auto-generated art track) has `artists`/`track`; the ten VEVO, official and fan uploads have `null`. So `raw_artist` was the uploader: "Natan Santos", "RHINO", and for Badge "Gñåf Ütøpìe" (a third instance of the same fault, not yet listed in a validation).
4. `titles._strip_artist_prefix(title, artist)`: the head before " - " ("The Beatles", "The Cars", "Cream") is short enough, but `_long_words(head) & _long_words(artist)` is empty ({"the","beatles"} against {"natan","santos"}; {"the","cars"} against {"rhino"}), so the title is returned whole and the artist stays the uploader. The sheet prints "The Beatles - Day Tripper" by "Natan Santos".

The shared-word rule exists to avoid splitting a head that is not an artist (`test_wider_artist_prefix_rule`: "Of Us - Song" with uploader "Of Them"). On the eleven real titles it never helped: all ten dash titles are artist-dash-title, and on the three where the uploader is not the artist it blocked the right answer.

## B. Suggestions, ranked

### Key

**K1. Diatonic-set veto with a relative-key hedge** (`music/key.py`, `decide_tonic`, `TonicDecision`, `_hedge`; `harmony.py` notes; `evaluate._key_line`). After the three-vote decision, compute `pair_shares(events, _TONICS)` over all twelve tonics. If the best set's share exceeds the decided tonic's set share by at least `SET_VETO_MARGIN`, the tonic becomes that set's major tonic, `_mode_of` picks major or minor at it from the stem chroma as now (G major or E minor for Badge), `decided_by` becomes "set", and the hedge names the *relative* (E minor or G major), because the set cannot separate those two and the published sources disagree on exactly that pair. Band measured on all eleven runs: Badge 0.239; every other song 0.007 or less (Fame 0.007 for B flat, Need You Tonight 0.004, mangetout 0.000, the rest 0). A margin of 0.10 sits inside that gap. Failures addressed: Badge. Research support: a chord-set voter is the one placed to resolve fifth and relative confusions ([Korzeniowski & Widmer 2018](https://ar5iv.labs.arxiv.org/html/1808.05340) category tables; [Lee & Slaney 2007](https://archives.ismir.net/ismir2007/paper/000245.pdf)); the relative hedge is the `MajMin` precedent ([Essentia Key](https://essentia.upf.edu/reference/streaming_Key.html)). Risk to songs right today: none fires (all under 0.007). Generality: a share of chord time, scale-free, no song-specific constant; the veto is one-directional and the three votes keep deciding everything else. Install cost: none. Record `set_tonic` and `set_margin` in `TonicVotes` and print them in `tonic_votes_note` and `evaluate`.

**K2. Category-aware hedge** (`key.py`, `_hedge`, `hedged`; new helper `relation(a, b)` returning fifth, relative, parallel or other via pitch-class arithmetic, cross-checked against `mir_eval.key.weighted_score`). Keep the three rungs but drop a hedge whose other tonic is "other" to the lead and whose margin clears `KEY_HEDGE_MARGIN`; keep it when the pair is fifth, relative or parallel. Failures addressed: none on the current set (every current hedge, Chelsea Dagger D, Need You Tonight C, Badge A, is a fifth), so this is a guard for future songs where the mix names an unrelated tonic. Support: "other" errors are 4 to 7 percent on pop while fifth plus relative plus parallel stay 15 to 20 ([K&W 2018](https://ar5iv.labs.arxiv.org/html/1808.05340)). Risk: none of the three printed hedges changes. Cost: none.

**K3. Whole-song estimation.** Already satisfied: `chroma_mean_for` reads the whole mix, the chord stream is the whole song, the stem chroma averages every loud bar. No change; record it as a met assumption against the 131 s versus 51 s finding ([K&W 2018](https://ar5iv.labs.arxiv.org/html/1808.05340)).

**K4. Models: not now.** madmom 0.16.1 is a 2018 sdist needing Cython and a C compiler on Windows, unconfirmed on Python 3.12+/NumPy 2 ([piwheels](https://www.piwheels.org/project/madmom), [issue #463](https://git.tdem.in/CPJKU/madmom/issues/463), [issue #478](https://git.tdem.in/CPJKU/madmom/issues/478)), which breaks the pip-on-Windows rule; Essentia has no Windows bindings ([installing](https://essentia.upf.edu/installing.html)); S-KEY and KeyMyna promise no weights. The gain would also land in the wrong place: the CNN's edge is on "other" errors, while every error and hedge here is a fifth or relative, where it still errs 5.6 to 7.6 percent. Revisit only for a torch-only checkpoint with a stated licence.

Not recommended: lowering `TONIC_MIN_SHARE` alone. With 0.1, G enters the score at 0.108 + 0.15 x 3/7 = 0.172 against D's 0.382; the root score would still rank D first and the pair rule would then name G, giving a two-against-one "D major (or G major)", a 0.5 result rather than a fix.

### Metadata

**M1. Keep every field and record provenance** (`models/ytdl.py` `_METADATA_FIELDS`; `layout.resolve_run_dir`; `stages/ingest.py`; `schemas.SourceInfo`). Add `artists`, `track`, `album`, `channel`, `channel_id`, `uploader_id`, `release_year` to the fetched set; in ingest merge the fetched details over the download's info dict instead of replacing it. Add `uploader`, `channel`, `credited_artist`, `credited_track`, `artist_source`, `title_source` to `SourceInfo`. Failures addressed: prerequisite for M2 and M3. Risk: none to printed text. Cost: none.

**M2. Evidence order in one function** (`titles.py`, new `resolve_credits(info) -> (title, artist, provenance)`, called from ingest): (1) `track` and `artists` when present (Fame only, on this set); (2) AcoustID when enabled (M3); (3) title parse: split at the first separator when the head has at most four words and no `UPLOAD_TAG_WORDS` word, take the head as artist and the rest as title; (4) when no split, the channel as the default artist, the `get-artist-title` `defaultArtist` idea ([npm](https://npmjs.com/package/get-artist-title)); (5) the raw uploader. Drop the shared-word requirement in `_strip_artist_prefix`; keep the equal-prefix fast path. Treat a channel as the artist's own only when `uploader_id` or `channel` shares a word of three or more letters with the artist or ends in " - Topic" (spike 3: `@PatBenatarVEVO`, `@TheFratellisVEVO`, `@bryanadams` carry the artist; `@rhino`, `@goldsongs7948`, `@GnafUtopie` do not). **Absent versus disagreeing:** a rung that returns nothing is absent and the next rung decides, silently; a rung that returns a value different from the chosen one (casefolded, tags stripped) is a disagreement and is printed. The ordering follows yt-dlp's own embed map, uploader last ([yt-dlp README](https://github.com/yt-dlp/yt-dlp/blob/master/README.md)), and the `multiple_songs` blanking in the extractor ([youtube/_video.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube/_video.py)) is why absence must be distinguished. Failures addressed: The Cars, Day Tripper, Badge. Risk to the eight known songs: none (their heads already equal the uploader after `clean_artist`). Test change: `test_wider_artist_prefix_rule`'s "Of Us - Song" with "Of Them" would now split to artist "Of Us"; replace that case with a tag-word head ("Song - Live at Wembley" stays whole). Cost: none.

**M3. AcoustID as an optional rung** (`models/acoustid.py`; a `pyproject` extra; `install.ps1`). `pyacoustid` 1.3.1 (MIT, Python 3.10+, self-limited to 3 requests per second, 120 s cap) with `fpcalc.exe` from the Chromaprint release on PATH or `FPCALC` ([pyacoustid](https://pypi.org/project/pyacoustid/), [beets chroma](https://docs.beets.io/en/stable/plugins/chroma.html)); a free per-application key under non-commercial terms ([AcoustID](https://acoustid.org/webservice)); MusicBrainz core data CC0, mandatory `Youkulele/<version> (contact)` User-Agent, about one request per second ([rate limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting), [licence](https://musicbrainz.org/doc/About/Data_License)). No pip package bundles `fpcalc`, so `install.ps1` would fetch it as `static-ffmpeg` fetches ffmpeg; the key lives in an environment variable, off by default. Failures addressed: a future upload with neither credits nor a split title; today M2 fixes all three, so this rung changes nothing. A no-match is itself a signal that the upload is not the canonical recording. Ranked below M2: a key, a binary and a network call for no present gain.

**M4. shazamio: do not add.** Reverse-engineered, no service terms, a 12 s signature ([ShazamIO](https://github.com/shazamio/ShazamIO)); its strength (covers, live) is not a failure class seen here.

**M5. What the sheet prints** (`music/score_builder.py`, `render/html.py` header). Title and artist from the chosen rung; a small provenance line only when a lower rung disagrees: "Day Tripper — The Beatles" then "uploaded by Natan Santos". Never the uploader as the artist unless the channel test in M2 passes, in which case the names coincide and nothing extra prints.

## C. Success criteria

**Key.** Score each run's printed lead with `mir_eval.key.weighted_score(reference, estimate)` (installed: 0.8.2; fifth 0.5, relative 0.3, parallel 0.2) and print the category beside it in `evaluate`. Truth per song, with its source:

| Song | Published or ear key | Source | Sheet today | Score |
|---|---|---|---|---|
| Summer of '69 | D major | general knowledge, confirm | D major | 1.0 |
| Chelsea Dagger | G major | [Hooktheory](https://hooktheory.com/theorytab/view/the-fratellis/chelsea-dagger), [Ukutabs](https://ukutabs.com/id/t/the-fratellis/chelsea-dagger/) | G major (or D major) | 1.0 |
| Pour Some Sugar On Me | C# minor (original published key) | [Musicnotes](https://www.musicnotes.com/sheetmusic/def-leppard/pour-some-sugar-on-me/MN0056406) | C# minor | 1.0 |
| mangetout | none found | 1.4 validation accepted C major | C major | n/a |
| Fame | none found | 1.4 validation accepted F major (84 of 100 bars on F) | F major | n/a |
| All Fired Up | unreliable: automated tools say C major and G minor | [SongBPM](https://songbpm.com/@pat-benatar/all-fired-up), [UBC listing](https://www.cs.ubc.ca/~davet/music/track/PATBENTR_GH1/PATBENTR_GH1-04.html) | G major | n/a |
| Need You Tonight | C major by sheet music; F by the owner's ear (1.5 clips) | [Musicnotes](https://www.musicnotes.com/sheetmusic/inxs/need-you-tonight/MN0097720); 1.5 validation | F major (or C major) | 0.5 or 1.0 |
| You Shook Me All Night Long | G major | general knowledge, confirm | G major | 1.0 |
| The Cars, You Might Think | D major | ear, 1.5 clips 11 and 12 | D major | 1.0 |
| Day Tripper | E major | general knowledge, confirm | E major | 1.0 |
| Badge | G major or E minor | published, 1.7 validation | D major (or A major) | 0.5 or 0.0 |

Criteria: (1) Badge's lead scores 1.0 against one of G major and E minor and its hedge names the other; (2) the lead tonic on the other ten runs is unchanged after re-running `--from harmony`; (3) the three printed hedges are unchanged or dropped only by K2's "other" rule (none qualifies today); (4) `SET_VETO_MARGIN` sits inside the measured band and is reported with the per-song set-share gaps in the spec's assumptions; (5) for every future blind song, weighted score at least 0.5 against the published key and, when a hedge prints, the hedge pair is fifth, relative or parallel.

**Metadata.** Exact match after casefold and tag stripping on every blind song so far: "You Might Think" by "The Cars"; "Day Tripper" by "The Beatles"; "Badge" by "Cream"; the eight known songs unchanged (Chelsea Dagger, Pour Some Sugar On Me, mangetout, Summer Of 69, Fame, All Fired Up, Need You Tonight, You Shook Me All Night Long, all with their present artists). A provenance line prints on exactly the three. `KNOWN_TITLES` in `tests/test_titles.py` and the ingest tests pass unchanged except the "Of Us" case.

## D. Spikes on the existing runs

1. **Twelve-set re-score** (run). Question: would a diatonic-set share have named G for Badge, and what does it do elsewhere? Measurement: `_set_share` at all twelve tonics on each `chords.json`. Result: confirmed as a veto (Badge G 0.995 against printed D 0.756; the printed tonic is the best set on nine runs and within 0.007 on Fame); **killed as a replacement**, because Fame's best set is B flat (0.988 against 0.981, F being its dominant) and mangetout ties C with F at 0.995. Root share must stay in the vote; the set share only vetoes.
2. **Cadence counts** (run). Question: does the literal dominant-to-tonic veto fire on Badge? Measurement: final root, section-end roots, V-to-I and IV-to-I counts per tonic. Result: killed (final Bm; section ends G 3, D 2, B 2; V-to-I into D 9, into G 2).
3. **yt-dlp fields on the eleven manifest URLs** (run, no download). Question: do `track`/`artists` fix the blind songs? Result: killed for the present set; only Fame carries them. Confirmed: `channel` equals `uploader` on all eleven, and `uploader_id` handles separate artist channels from label and fan channels.
4. **Mode at G for Badge** (to run). Recompute `harmonic_chroma` from `runs\cream-badge\01_separate` stems, then `mode_at("G", chroma)` and `_profile_fit` at G and D: decides whether K1 leads with G major or E minor and whether the mode margin falls under `MODE_TIE_MARGIN`.
5. **Scorecard** (to run). Extend the re-score script with the truth table above and `mir_eval.key.weighted_score`; keep it as `evaluate --truth` once it is stable.
6. **Title rule on the eleven raw titles** (to run, offline). Apply M2's rule to the raw titles and handles in `source_meta.json` plus yt-dlp's own extractor test titles; count splits and false splits.
7. **AcoustID on the eleven WAVs** (only if M3 proceeds; needs a key and `fpcalc.exe`). Record `score` per match to pick a threshold, since the service does not define one.

## E. Do not do

- Replace the three-vote tonic with the set share, or lower `TONIC_MIN_SHARE` on its own (spike 1; section B).
- Tune `SET_VETO_MARGIN` to Badge; it must sit in the band measured across all runs and be re-measured when a run is added.
- Build madmom or Essentia on Windows, or vendor a deep key model without weights and a licence.
- Add shazamio or the YouTube Data API (key and quota) for a failure class the project has not met.
- Print the uploader as the artist when the channel test fails, or print two artists without saying which source each came from.
- Re-transcribe chords to fix the key; the Badge stream is already consistent with the published tab.
- Hedge with the other mode of the same tonic (the README rule stands); the relative key is a different tonic and is allowed.
