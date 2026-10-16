import os
import re

import yaml

from arabic_token_tax.tokenisers import default_config_path, default_prices_path, load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def test_packaged_config_matches_repository_config():
    assert _read(default_config_path()) == _read(os.path.join(ROOT, "config", "tokenisers.yaml"))
    assert _read(default_prices_path()) == _read(os.path.join(ROOT, "config", "prices.yaml"))


def test_every_hf_entry_is_pinned():
    cfg = load_config(os.path.join(ROOT, "config", "tokenisers.yaml"))
    for e in cfg["tokenisers"]:
        for spec in [e] + e.get("equivalents", []):
            assert spec["route"] in ("tiktoken", "hf", "sentencepiece")
            if spec["route"] != "tiktoken":
                assert re.fullmatch(r"[0-9a-f]{40}", spec["revision"]), spec
    for n in cfg["not_measured"]:
        assert n["reason"] and n["checked_on"]


def test_prices_point_at_measured_tokenisers():
    cfg = load_config(os.path.join(ROOT, "config", "tokenisers.yaml"))
    ids = {e["id"] for e in cfg["tokenisers"]}
    with open(os.path.join(ROOT, "config", "prices.yaml"), encoding="utf-8") as f:
        prices = yaml.safe_load(f)
    for p in prices["prices"]:
        assert p["tokeniser_id"] in ids
        assert p["input_usd_per_mtok"] > 0 and p["output_usd_per_mtok"] > 0
        assert p["source_url"].startswith("https://") and re.fullmatch(r"[0-9a-f]{64}", p["page_sha256"])
    shown = {p["tokeniser_id"] for p in prices["prices"]}
    not_shown = {p["tokeniser_id"] for p in prices["prices_not_shown"]}
    assert shown | not_shown == ids and not (shown & not_shown)
