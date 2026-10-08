"""Tidy the song title and artist taken from video metadata, and resolve them by evidence."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

UPLOAD_TAG_WORDS = (
    "official",
    "video",
    "audio",
    "lyric",
    "lyrics",
    "visualiser",
    "visualizer",
    "hd",
    "hq",
    "4k",
    "remaster",
    "remastered",
    "live",
)

_TAG_RE = re.compile(r"\b(?:" + "|".join(UPLOAD_TAG_WORDS) + r")\b", re.IGNORECASE)
_GROUP_RE = re.compile(r"\([^()]*\)|\[[^\[\]]*\]")
_DOUBLE_QUOTES = "\"“”"
_SINGLE_QUOTE_PAIRS = (("'", "'"), ("‘", "’"))
_WORD_RE = re.compile(r"\S+")


def _title_case_if_shouting(text: str) -> str:
    """Title-case two or more words given entirely in capitals. One word in capitals stays
    as written (INXS, ABBA, AC/DC), and so does anything with a lower-case letter."""
    if any(ch.islower() for ch in text) or len(_WORD_RE.findall(text)) < 2:
        return text
    return _WORD_RE.sub(lambda m: m.group()[:1].upper() + m.group()[1:].lower(), text)


def clean_artist(artist: str | None) -> str | None:
    """Title-case an artist of two or more words given entirely in capitals; otherwise
    leave it alone."""
    if artist is None:
        return None
    return _title_case_if_shouting(artist)


_SEPARATORS = (" - ", " – ", ": ")
_MAX_PREFIX_WORDS = 4
_MIN_SHARED_LETTERS = 3
_TOPIC_SUFFIX = " - Topic"
# Words of an artist's name too common to identify a channel: "the" sits inside "southern"
# (spec 8.3).
_STOPWORDS = frozenset({"the", "and", "of"})


def _long_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[^\W\d_]+", text.casefold()) if len(w) >= _MIN_SHARED_LETTERS}


def split_title(raw: str) -> tuple[str, str] | None:
    """`(artist, title)` when the raw title reads as "Artist - Title" (spec 8.2, rung 2).

    The title splits at the earliest of " - ", " – " and ": " when the head has at most
    four words and no upload-tag word appears in the head, or in the tail once its bracket
    groups are removed. The tail condition keeps "Song - Live at Wembley" whole, at the
    accepted cost of keeping "Band - Song - Live" whole too. The tail comes back as written,
    brackets and all; cleaning it is the caller's job."""
    found = [(raw.find(sep), sep) for sep in _SEPARATORS if raw.find(sep) > 0]
    if not found:
        return None
    index, sep = min(found)
    head, tail = raw[:index].strip(), raw[index + len(sep):].strip()
    if not head or not tail or len(head.split()) > _MAX_PREFIX_WORDS:
        return None
    if _TAG_RE.search(head) or _TAG_RE.search(_GROUP_RE.sub("", tail)):
        return None
    return head, tail


def _letters(text: str) -> str:
    return "".join(ch for ch in text.casefold() if ch.isalpha())


def channel_is_artist(uploader_id: str | None, channel: str | None, artist: str) -> bool:
    """Whether the channel that uploaded the video is the artist's own (spec 8.3).

    True when the handle (`uploader_id`) or the channel name, casefolded with its
    non-letters removed, contains a word of three or more letters from the artist's name
    other than a stopword ("the", "and", "of"), or the whole name run together ("AC/DC" as
    "acdc", which no three-letter word can pass), or when either ends in " - Topic",
    YouTube's auto-generated artist channel."""
    handles = [h for h in (uploader_id, channel) if h]
    if any(h.endswith(_TOPIC_SUFFIX) for h in handles):
        return True
    words = _long_words(artist) - _STOPWORDS
    whole = _letters(artist)
    for handle in map(_letters, handles):
        if any(word in handle for word in words):
            return True
        if len(whole) >= _MIN_SHARED_LETTERS and whole in handle:
            return True
    return False


def _strip_artist_prefix(title: str, artist: str | None) -> tuple[str, str | None]:
    """The title without a leading artist, and the artist that prefix names.

    The prefix equal to the artist field wins; otherwise a title that `split_title` splits
    gives its head as the artist, whatever the artist field says (spec 8.2: no shared word
    is needed)."""
    if artist:
        folded = title.casefold()
        for sep in _SEPARATORS:
            prefix = (artist + sep).casefold()
            if folded.startswith(prefix):
                return title[len(prefix):], artist
    split = split_title(title)
    if split is not None:
        head, tail = split
        return tail, _title_case_if_shouting(head)
    return title, artist


def clean_artist_from(title: str, artist: str | None) -> str | None:
    """The artist for a video: a leading artist prefix of the title, else the artist field."""
    return _strip_artist_prefix(title, clean_artist(artist))[1]


def _strip_quotes(text: str) -> str:
    text = text.strip()
    while True:
        before = text
        text = text.strip(_DOUBLE_QUOTES).strip()
        for opening, closing in _SINGLE_QUOTE_PAIRS:
            if len(text) > 1 and text[0] == opening and text[-1] == closing:
                text = text[1:-1].strip()
        if text == before:
            return text


def _tidy(text: str) -> str:
    """Upload-tag brackets and surrounding quotes dropped, shouting title-cased."""
    text = _GROUP_RE.sub(lambda m: "" if _TAG_RE.search(m.group()) else m.group(), text)
    text = re.sub(r"\s{2,}", " ", text)
    text = _strip_quotes(text)
    return _title_case_if_shouting(text)


def clean_title(title: str, artist: str | None) -> str:
    """Drop a leading artist, upload-tag brackets and surrounding quotes."""
    text = _strip_artist_prefix(title, clean_artist(artist))[0]
    return _tidy(text) or title.strip()


@dataclass(frozen=True)
class Credits:
    """The title and artist a sheet prints, and the evidence each came from (spec 8.2).

    `title_source` and `artist_source` name the deciding rung: "credited", "title",
    "channel", "uploader", or "file" for a local file. `uploader` is the uploader when a
    lower rung disagreed with the chosen artist; `provenance` is that uploader when the
    channel is also not the artist's own (spec 8.3), the name printed after "uploaded by"."""

    title: str
    artist: str | None
    title_source: str
    artist_source: str
    uploader: str | None
    provenance: str | None


def _text(value: object) -> str | None:
    """A non-empty string field, stripped, or None."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def credited_names(info: Mapping[str, object]) -> tuple[str | None, str | None]:
    """The track and the artists the platform credits, `artists` joined with ", " as
    yt-dlp's own `artist` field is; either may be None (spec 8.2, rung 1)."""
    artists = info.get("artists")
    if isinstance(artists, str):
        joined = _text(artists)
    elif isinstance(artists, (list, tuple)):
        joined = _text(", ".join(name.strip() for name in artists if _text(name)))
    else:
        joined = None
    return _text(info.get("track")), joined


def _comparable(name: str) -> str:
    """A name casefolded with upload-tag words removed, for telling disagreement apart."""
    return " ".join(_TAG_RE.sub(" ", name.casefold()).split())


def _channel_vouches(info: Mapping[str, object], uploader: str | None) -> bool:
    """Rung 3 of spec 8.2: the uploader is the artist when the channel passes spec 8.3.

    Either handle may pass (`uploader_id` or `channel`); with no uploader there is no
    name for the rung to give, so it is absent."""
    if uploader is None:
        return False
    return channel_is_artist(_text(info.get("uploader_id")), _text(info.get("channel")), uploader)


def resolve_credits(info: Mapping[str, object]) -> Credits:
    """The title and artist of a video by the evidence order of spec 8.2.

    1. Credited: `track` and `artists`, when both are present, give the title and artist.
    2. Title split: a raw title `split_title` splits gives its head as the artist and its
       tail as the title.
    3. Channel: when nothing split and the channel passes spec 8.3, the uploader, as the
       artist's own channel.
    4. Uploader: otherwise the uploader.

    A rung with nothing to say is absent and the next decides silently; yt-dlp blanks the
    credited fields of a video holding several songs, so a missing field is not evidence
    against anything. A rung that returns a different name is a disagreement: when the
    artist did not come from the uploader and the uploader (casefolded, tags stripped)
    differs from it, the uploader is recorded, and it becomes the provenance unless the
    channel is the artist's own (spec 8.3; "Benatar Giraldo" on @PatBenatarVEVO prints
    nothing). The chosen title and artist are tidied as `clean_title` and `clean_artist`
    tidy them."""
    raw_title = _text(info.get("title")) or ""
    uploader = _text(info.get("uploader"))
    track, credited_artist = credited_names(info)
    split = split_title(raw_title)
    if track and credited_artist:
        title, artist = _tidy(track) or track, credited_artist
        title_source = artist_source = "credited"
    elif split is not None:
        artist, tail = split
        title = _tidy(tail) or tail
        title_source = artist_source = "title"
    else:
        # the equal-prefix fast path still drops an uploader that leads the title
        title = clean_title(raw_title, uploader)
        artist, title_source = uploader, "title"
        artist_source = "channel" if _channel_vouches(info, uploader) else "uploader"
    artist = clean_artist(artist)
    disagreed = (
        artist_source in ("credited", "title")
        and uploader is not None
        and artist is not None
        and _comparable(uploader) != _comparable(artist)
    )
    recorded = uploader if disagreed else None
    own_channel = artist is not None and channel_is_artist(
        _text(info.get("uploader_id")), _text(info.get("channel")), artist
    )
    provenance = recorded if recorded is not None and not own_channel else None
    return Credits(title, artist, title_source, artist_source, recorded, provenance)
