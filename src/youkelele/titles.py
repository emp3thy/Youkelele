"""Tidy the song title and artist taken from video metadata at ingest."""

from __future__ import annotations

import re

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


def _long_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[^\W\d_]+", text.casefold()) if len(w) >= _MIN_SHARED_LETTERS}


def _strip_artist_prefix(title: str, artist: str) -> tuple[str, str]:
    """The title without a leading artist, and the artist that prefix names.

    The prefix equal to the artist field wins; otherwise a short leading `X - ` sharing a
    word of three or more letters with the artist field is taken as the artist."""
    folded = title.casefold()
    for sep in _SEPARATORS:
        prefix = (artist + sep).casefold()
        if folded.startswith(prefix):
            return title[len(prefix):], artist
    found = [(title.find(sep), sep) for sep in _SEPARATORS if title.find(sep) > 0]
    if found:
        index, sep = min(found)
        head = title[:index].strip()
        if len(head.split()) <= _MAX_PREFIX_WORDS and _long_words(head) & _long_words(artist):
            return title[index + len(sep):], _title_case_if_shouting(head)
    return title, artist


def clean_artist_from(title: str, artist: str | None) -> str | None:
    """The artist for a video: a leading artist prefix of the title, else the artist field."""
    cleaned_artist = clean_artist(artist)
    if not cleaned_artist:
        return cleaned_artist
    return _strip_artist_prefix(title, cleaned_artist)[1]


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


def clean_title(title: str, artist: str | None) -> str:
    """Drop a leading artist, upload-tag brackets and surrounding quotes."""
    text = title
    cleaned_artist = clean_artist(artist)
    if cleaned_artist:
        text = _strip_artist_prefix(text, cleaned_artist)[0]
    text = _GROUP_RE.sub(lambda m: "" if _TAG_RE.search(m.group()) else m.group(), text)
    text = re.sub(r"\s{2,}", " ", text)
    text = _strip_quotes(text)
    text = _title_case_if_shouting(text)
    return text or title.strip()
