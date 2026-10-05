from youkelele.music.tab import RANGE_HI, RANGE_LO, octave_shift, string_fret, to_tab, tuning_midis

NYT = [60, 60, 62, None, None, None, 62, None, 60, None, 62, 63, None, 62, None, 60]


def test_tab_maps_the_verified_riff_onto_the_c_string_without_a_shift():
    tab, shift = to_tab(NYT, True, tuning_midis(("G4", "C4", "E4", "A4")))
    assert shift == 0 and [(n.string, n.fret) for n in tab] == [(1, 0), (1, 0), (1, 2), (1, 2), (1, 0), (1, 2), (1, 3), (1, 2), (1, 0)]


def test_octave_shift_lifts_a_guitar_register_riff_and_moves_outliers():
    assert octave_shift([56, 56, 63, 63, 60, 62]) == 1  # G#3 to D#4 sits an octave low
    tab, shift = to_tab([44, 56, 63], True, tuning_midis(("G4", "C4", "E4", "A4")))
    assert shift == 1 and all(RANGE_LO <= n.midi <= RANGE_HI for n in tab) and all(n.fret >= 0 for n in tab)


def test_string_fret_prefers_the_lowest_fret_and_treats_g_as_high():
    t = tuning_midis(("G4", "C4", "E4", "A4"))
    assert string_fret(67, t) == (0, 0) and string_fret(69, t) == (3, 0) and string_fret(65, t) == (2, 1)


def test_tuning_midis():
    assert tuning_midis(("G4", "C4", "E4", "A4")) == [67, 60, 64, 69]
    assert tuning_midis(["F#3", "Bb2"]) == [54, 46]
