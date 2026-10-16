"""Needs internet access: downloads two tokenizer files and counts the first UN
test segment. Run with ARABIC_TOKEN_TAX_NETWORK=1."""
import os

import pytest

from arabic_token_tax import textnorm
from arabic_token_tax.tokenisers import load, load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pytestmark = [pytest.mark.network,
              pytest.mark.skipif(os.environ.get("ARABIC_TOKEN_TAX_NETWORK") != "1", reason="network tests are opt-in")]

AR = "الجلسة 7439 المعقودة في 11 أيار/مايو ٢٠١٥."


def test_round_trip_and_counts_are_stable():
    cfg = load_config(os.path.join(ROOT, "config", "tokenisers.yaml"))
    entries = {e["id"]: e for e in cfg["tokenisers"]}
    for tid in ("o200k_base", "qwen3.5"):
        tok = load(entries[tid])
        text = textnorm.clean(AR)
        assert tok.roundtrip(text)
        assert tok.count([text]) == tok.count([text])
        assert tok.count([text])[0] > 0
