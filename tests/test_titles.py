from __future__ import annotations

import pytest

from youkelele.titles import UPLOAD_TAG_WORDS, clean_artist, clean_artist_from, clean_title


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


def test_one_word_in_capitals_stays_as_written():
    # a one-word name in capitals is usually how the act spells itself
    for name in ("INXS", "ABBA", "KISS", "AC/DC"):
        assert clean_artist(name) == name
        assert clean_artist_from(f"{name} - Song", name) == name
    assert clean_artist("PAT BENATAR") == "Pat Benatar"
    assert clean_artist("deadmau5") == "deadmau5" and clean_artist("McFly") == "McFly"
    # the same rule for the title
    assert clean_title("FAME", None) == "FAME"
    assert clean_title("INXS - NEED YOU TONIGHT", "INXS") == "Need You Tonight"
    assert clean_title("SHOUTY TITLE", None) == "Shouty Title"


def test_tag_words_are_the_agreed_set():
    assert "official" in UPLOAD_TAG_WORDS and "remastered" in UPLOAD_TAG_WORDS


KNOWN_TITLES = [
    ("The Fratellis - Chelsea Dagger", "The Fratellis", "Chelsea Dagger", "The Fratellis"),
    (
        'DEF LEPPARD - "Pour Some Sugar On Me" (Official Music Video)',
        "DEF LEPPARD",
        "Pour Some Sugar On Me",
        "Def Leppard",
    ),
    ("Wet Leg - mangetout (Official Video)", "Wet Leg", "mangetout", "Wet Leg"),
    ("Bryan Adams - Summer Of '69 (Official Music Video)", "Bryan Adams", "Summer Of '69", "Bryan Adams"),
    ("Fame (2016 Remaster)", "David Bowie", "Fame", "David Bowie"),
]


def test_wider_artist_prefix_rule():
    raw = "Pat Benatar - All Fired Up (Official Music Video)"
    assert clean_title(raw, "Benatar Giraldo") == "All Fired Up"
    assert clean_artist_from(raw, "Benatar Giraldo") == "Pat Benatar"
    for raw, uploader, title, artist in KNOWN_TITLES:
        assert (clean_title(raw, uploader), clean_artist_from(raw, uploader)) == (title, artist)
    # en dash and colon separate too; the match ignores case
    assert clean_title("pat benatar – Song", "BENATAR Fan") == "Song"
    assert clean_artist_from("PAT BENATAR: Song", "benatar fan") == "Pat Benatar"
    # no shared word of three or more letters: the prefix stays
    assert clean_title("Of Us - Song", "Of Them") == "Of Us - Song"
    assert clean_artist_from("Of Us - Song", "Of Them") == "Of Them"
    # more than four words before the separator: not an artist
    long = "One Two Three Four Benatar - Song"
    assert clean_title(long, "Benatar") == long
    # no artist field: nothing to compare against
    assert clean_title("Pat Benatar - Song", None) == "Pat Benatar - Song"
    assert clean_artist_from("Pat Benatar - Song", None) is None
    assert clean_artist_from("Song", "DEF LEPPARD") == "Def Leppard"
