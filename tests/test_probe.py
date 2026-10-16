import unicodedata

from arabic_token_tax import probe


def test_probe_is_deterministic_and_nfc():
    a, b = probe.probe_lines(), probe.probe_lines()
    assert a == b
    assert len(a) == 22
    assert probe.marked_letters() == len(probe.BASE_LETTERS) * len(probe.MARK_PATTERNS) + len(probe.EXTRA)
    for line in a:
        assert unicodedata.normalize("NFC", line) == line


def test_probe_covers_every_mark():
    text = "".join(probe.probe_lines())
    for mark in "ًٌٍَُِّْٰ":
        assert mark in text
