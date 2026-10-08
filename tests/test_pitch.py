import librosa
import numpy as np

from youkelele.music.pitch import PITCH_CHANGE_MIN, name_notes, pitch_change_share, track_pitch


def _tone_sequence(sr, midis, seconds_each):
    parts = [
        np.sin(2 * np.pi * librosa.midi_to_hz(m) * np.arange(int(sr * seconds_each)) / sr)
        for m in midis
    ]
    return np.concatenate(parts).astype(np.float32)


def test_name_notes_recovers_a_c_d_eflat_sequence():
    sr = 22050
    y = _tone_sequence(sr, [60, 62, 63, 62], 0.5)
    track = track_pitch(y, sr)
    onsets = [0.0, 0.5, 1.0, 1.5]
    assert name_notes(track, onsets, [0.5, 1.0, 1.5, 2.0]) == [60, 62, 63, 62]


def test_unvoiced_window_names_none():
    sr = 22050
    y = np.concatenate(
        [_tone_sequence(sr, [60], 0.5), np.zeros(int(sr * 0.5), dtype=np.float32)]
    )
    track = track_pitch(y, sr)
    assert name_notes(track, [0.0, 0.5], [0.5, 1.0]) == [60, None]


def test_pitch_change_share_counts_named_pairs_only():
    assert pitch_change_share([60, 60, 62, None, 62, 63]) == 2 / 3
    assert pitch_change_share([60]) is None and pitch_change_share([None, None]) is None
    assert pitch_change_share([43] * 8) == 0.0


def test_pitch_change_floor_is_0_26():
    assert PITCH_CHANGE_MIN == 0.26
