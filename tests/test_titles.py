from __future__ import annotations

import pytest

from youkelele.titles import UPLOAD_TAG_WORDS, clean_artist, clean_title


@pytest.mark.parametrize(
    "raw,artist,expected",
    [
        ("The Fratellis - Chelsea Dagger", "The Fratellis", "Chelsea Dagger"),
        (
            'DEF LEPPARD - "Pour Some Sugar On Me" (Official Music Video)',
            "DEF LEPPARD",
            "Pour Some Sugar On Me",
        ),
        ("Wet Leg - mangetout (Official Video)", "Wet Leg", "mangetout"),
        ("Bryan Adams - Summer Of '69 (Official Music Video)", "Bryan Adams", "Summer Of '69"),
        ("Some Band – Song Name [HD]", "Some Band", "Song Name"),
        ("Some Band: Song Name", "some band", "Song Name"),
        ("Song Name (Live at Wembley)", "Other Artist", "Song Name"),
        ("Song Name (Acoustic Version)", None, "Song Name (Acoustic Version)"),
        ("SHOUTY TITLE", None, "Shouty Title"),
        ("Fame (2016 Remaster)", "David Bowie", "Fame"),
        ("Song (Official Video) Extra [4K]", None, "Song Extra"),
        ("“Curly Quoted”", None, "Curly Quoted"),
        ("Rockin'", None, "Rockin'"),
        ("Alive Again (Delivered)", None, "Alive Again (Delivered)"),
    ],
)
def test_clean_title(raw, artist, expected):
    assert clean_title(raw, artist) == expected


def test_clean_title_never_empty():
    assert clean_title("(Official Video)", None) == "(Official Video)"


def test_clean_artist_title_cases_capitals():
    assert clean_artist("DEF LEPPARD") == "Def Leppard"
    assert clean_artist(None) is None
    assert clean_artist("Wet Leg") == "Wet Leg"


def test_tag_words_are_the_agreed_set():
    assert "official" in UPLOAD_TAG_WORDS and "remastered" in UPLOAD_TAG_WORDS
