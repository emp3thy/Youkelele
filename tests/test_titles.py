from __future__ import annotations

import pytest

from youkelele.titles import (
    UPLOAD_TAG_WORDS,
    channel_is_artist,
    clean_artist,
    clean_artist_from,
    clean_title,
    resolve_credits,
    split_title,
)


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
    # no shared word is needed any more (spec 8.4): a short head splits
    assert clean_title("Of Us - Song", "Of Them") == "Song"
    assert clean_artist_from("Of Us - Song", "Of Them") == "Of Us"
    # an upload-tag word in the head, or in the tail outside brackets, keeps the title whole
    assert clean_title("Song - Live at Wembley", "Someone") == "Song - Live at Wembley"
    assert clean_artist_from("Song - Live at Wembley", "Someone") == "Someone"
    assert clean_title("Live - Song", "Someone") == "Live - Song"
    assert clean_artist_from("Live - Song", "Someone") == "Someone"
    # more than four words before the separator: not an artist
    long = "One Two Three Four Benatar - Song"
    assert clean_title(long, "Benatar") == long
    # no artist field: the head still splits (spec 8.4)
    assert clean_title("Pat Benatar - Song", None) == "Song"
    assert clean_artist_from("Pat Benatar - Song", None) == "Pat Benatar"
    assert clean_artist_from("Song", "DEF LEPPARD") == "Def Leppard"


def test_split_title_takes_a_short_head_without_tag_words():
    assert split_title("The Beatles - Day Tripper (Official Video)") == ("The Beatles", "Day Tripper (Official Video)")


def test_split_title_keeps_a_tag_word_in_the_tail_whole_but_ignores_brackets():
    assert split_title("Song - Live at Wembley") is None and split_title("Live - Song") is None
    assert split_title("The Cars - You Might Think [Official Video]") == ("The Cars", "You Might Think [Official Video]")
    assert split_title("Band - Song - Live") is None


def test_channel_is_artist_cases():
    assert channel_is_artist("@PatBenatarVEVO", None, "Pat Benatar") and channel_is_artist("@bryanadams", None, "Bryan Adams")
    assert channel_is_artist("@acdc", None, "AC/DC") and channel_is_artist(None, "Oasis - Topic", "Oasis")
    assert not channel_is_artist("@rhino", "RHINO", "The Cars") and not channel_is_artist("@goldsongs7948", "Natan Santos", "The Beatles")


def test_resolve_credits_rungs_and_provenance():
    beatles = resolve_credits({"title": "The Beatles - Day Tripper", "uploader": "Natan Santos", "uploader_id": "@goldsongs7948"})
    assert (beatles.title, beatles.artist, beatles.artist_source, beatles.provenance) == ("Day Tripper", "The Beatles", "title", "Natan Santos")
    benatar = resolve_credits({"title": "Pat Benatar - All Fired Up (Official Music Video)", "uploader": "Benatar Giraldo", "uploader_id": "@PatBenatarVEVO"})
    assert (benatar.artist, benatar.provenance) == ("Pat Benatar", None)
    credited = resolve_credits({"title": "Fame (2016 Remaster)", "uploader": "David Bowie", "track": "Fame", "artists": ["David Bowie"]})
    assert (credited.title, credited.artist, credited.title_source) == ("Fame", "David Bowie", "credited")
    plain = resolve_credits({"title": "Song", "uploader": "Someone", "uploader_id": "@someone"})
    assert (plain.artist, plain.artist_source, plain.provenance) == ("Someone", "uploader", None)
