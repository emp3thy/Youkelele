from youkelele.cli import main

def test_version_flag_prints_version(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out
