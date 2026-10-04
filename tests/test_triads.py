import pytest

from youkelele.music.triads import to_triad


@pytest.mark.parametrize(
    "label,triad",
    [
        ("C#:min7", "C#:min"), ("G:7", "G:maj"), ("F:maj7", "F:maj"), ("A:hdim7", "A:dim"),
        ("D:sus4(b7)", "D:sus4"), ("E:dim7", "E:dim"), ("C:maj/5", "C:maj"), ("C:min9", "C:min"),
        ("C:maj6", "C:maj"), ("C:minmaj7", "C:min"), ("C:13", "C:maj"), ("N", "N"), ("X", "X"),
        ("E:aug7", "E:maj"),
    ],
)
def test_to_triad(label, triad):
    assert to_triad(label) == triad


def test_to_triad_keeps_power_label():
    assert to_triad("C#:5") == "C#:5"
