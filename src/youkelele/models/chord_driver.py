"""Decode chords with the chain's own beats and downbeats (run as a script, not imported).

Mirrors the vendored model's `chord_recognition.py`, adding the beat file so the decoder
puts chord changes on the bar lines. Run with cwd = the model directory, as `chords.py` does:

    python chord_driver.py <audio.wav> <out.lab> <chord dictionary> <beats.lab>

`beats.lab` is a headerless tab file; the model reads only column 0 (time in seconds) and
column 2 (1-based position in the bar). The decoder keeps its default penalties.
"""

import sys

sys.path.insert(0, ".")  # the model's own modules, found relative to its directory

import numpy as np  # noqa: E402
from chord_recognition import MODEL_NAMES  # noqa: E402
from chordnet_ismir_naive import ChordNet  # noqa: E402
from extractors.cqt import CQTV2  # noqa: E402
from extractors.xhmm_ismir import XHMMDecoder  # noqa: E402
from io_new.beatlab_io import BeatLabIO  # noqa: E402
from io_new.chordlab_io import ChordLabIO  # noqa: E402
from mir import DataEntry, io  # noqa: E402
from mir.nn.train import NetworkInterface  # noqa: E402
from settings import DEFAULT_HOP_LENGTH, DEFAULT_SR  # noqa: E402


def decode(audio_path: str, lab_path: str, chord_dict_name: str, beats_path: str) -> None:
    hmm = XHMMDecoder(template_file="data/%s_chord_list.txt" % chord_dict_name)
    entry = DataEntry()
    entry.prop.set("sr", DEFAULT_SR)
    entry.prop.set("hop_length", DEFAULT_HOP_LENGTH)
    entry.append_file(audio_path, io.MusicIO, "music")
    entry.append_extractor(CQTV2, "cqt")
    entry.append_file(beats_path, BeatLabIO, "beat")
    probs = []
    for model_name in MODEL_NAMES:
        net = NetworkInterface(ChordNet(None), model_name, load_checkpoint=False)
        print("Inference: %s on %s" % (model_name, audio_path))
        probs.append(net.inference(entry.cqt))
    probs = [np.mean([p[i] for p in probs], axis=0) for i in range(len(probs[0]))]
    chordlab = hmm.decode_to_chordlab(entry, probs, False, use_beats=True, use_downbeats=True)
    entry.append_data(chordlab, ChordLabIO, "chord")
    entry.save("chord", lab_path)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: chord_driver.py <audio.wav> <out.lab> <chord dictionary> <beats.lab>")
    decode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
