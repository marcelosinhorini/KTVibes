import json
import time
from unittest.mock import patch

import numpy as np
import soundfile as sf
import pytest

from ktvibes import lyrics, worker


def test_non_korean_does_not_load_pronunciation_dependencies():
    lines = [{"text": "Olá mundo", "units": [["Olá", 0, 1]]}]
    with patch.object(lyrics, "_g2p", None), patch("builtins.__import__", side_effect=AssertionError("unexpected import")):
        assert lyrics.add_korean_romanization(lines) is lines


def test_windows_korean_uses_installed_mecab_without_installer(monkeypatch):
    import sys
    import types
    import nltk

    class FakeG2p:
        def __init__(self):
            self.check_mecab()
            self.mecab = self.get_mecab()

        def __call__(self, text):
            return "눈무리"

    mecab = object()
    monkeypatch.setitem(sys.modules, "g2pk2", types.SimpleNamespace(G2p=FakeG2p))
    monkeypatch.setitem(sys.modules, "mecab", types.SimpleNamespace(MeCab=lambda: mecab))
    monkeypatch.setattr(nltk.data, "find", lambda _: True)
    monkeypatch.setattr(lyrics, "_g2p", None)
    units = [[c, 0, 1] for c in "눈물이"]
    lyrics.add_korean_romanization([{"text": "눈물이", "units": units}])
    assert [u[3] for u in units] == ["nun", "mu", "ri"]
    assert lyrics._g2p.mecab is mecab


def test_missing_corpus_does_not_import_g2pk_or_install(monkeypatch):
    import nltk
    import sys

    def missing(_):
        raise LookupError("corpus missing")

    monkeypatch.setattr(nltk.data, "find", missing)
    monkeypatch.setattr(lyrics, "_g2p", None)
    monkeypatch.delitem(sys.modules, "g2pk2", raising=False)
    with pytest.raises(RuntimeError, match="nltk.downloader cmudict"):
        lyrics.add_korean_romanization([{"text": "눈", "units": [["눈", 0, 1]]}])
    assert "g2pk2" not in sys.modules


def test_guide_failure_preserves_timing_and_retries_next_run(tmp_path, monkeypatch, caplog):
    sf.write(tmp_path / "vocals.wav", np.zeros(8000, dtype="float32"), 8000)
    monkeypatch.setattr(worker.align, "align", lambda *args: None)
    calls = []

    def broken(lines):
        calls.append(1)
        lines[0]["text"] = "partial mutation"
        raise FileNotFoundError("missing dependency")

    def other(lines):
        lines[0]["other_guide"] = True
        return lines

    monkeypatch.setattr(lyrics, "add_korean_romanization", broken)
    monkeypatch.setattr(worker.guides, "add_hangul", other)
    raw = "[00:00.10]hello"
    def prepare():
        return worker.timed_lyrics(tmp_path, raw, tmp_path / "vocals.wav", lyrics.parse_lrc(raw))

    result = prepare()
    assert result[0]["text"] == "hello"
    assert result[0]["units"] and result[0]["other_guide"]
    assert json.loads((tmp_path / "timed.json").read_text(encoding="utf-8"))["failed_guides"] == ["broken"]
    assert "missing dependency" in caplog.text
    assert prepare() == result
    assert len(calls) == 1
    monkeypatch.setattr(worker, "STARTED", time.time() + 60)
    prepare()
    assert len(calls) == 2
