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
    if any(ch.islower() for ch in text):
        return text
    return _WORD_RE.sub(lambda m: m.group()[:1].upper() + m.group()[1:].lower(), text)


def clean_artist(artist: str | None) -> str | None:
    """Title-case an artist given entirely in capitals; otherwise leave it alone."""
    if artist is None:
        return None
    return _title_case_if_shouting(artist)


def _strip_artist_prefix(title: str, artist: str) -> str:
    folded = title.casefold()
    for sep in (" - ", " – ", ": "):
        prefix = (artist + sep).casefold()
        if folded.startswith(prefix):
            return title[len(prefix):]
    return title


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
        text = _strip_artist_prefix(text, cleaned_artist)
    text = _GROUP_RE.sub(lambda m: "" if _TAG_RE.search(m.group()) else m.group(), text)
    text = re.sub(r"\s{2,}", " ", text)
    text = _strip_quotes(text)
    text = _title_case_if_shouting(text)
    return text or title.strip()
