import pytest

from youkelele import vendoring


def test_patch_numpy_aliases_rewrites_only_np_int(tmp_path):
    for rel in vendoring.PATCH_SITES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("np.int(3) np.int64 np.integer\n")
    counts = vendoring.patch_numpy_aliases(tmp_path)
    assert counts == {rel: 1 for rel in vendoring.PATCH_SITES}
    assert (tmp_path / "results_ismir2017.py").read_text() == "int(3) np.int64 np.integer\n"
    assert set(vendoring.patch_numpy_aliases(tmp_path).values()) == {0}


@pytest.mark.slow
def test_patch_counts_on_real_clone():
    if not vendoring.chord_model_ready():
        pytest.skip("chord model not installed")
    root = vendoring.chord_model_dir()
    for rel in vendoring.PATCH_SITES:
        assert "np.int(" not in (root / rel).read_text(), rel
    assert vendoring.PATCH_SITES == {
        "extractors/xhmm_ismir.py": 7, "extractors/xhmm_decoder.py": 7,
        "results_ismir2017.py": 1, "extractors/beat_preprocess.py": 2,
    }
