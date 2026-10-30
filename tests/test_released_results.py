"""The released results are internally consistent: every derived number can be
recomputed from the counts in the same files."""
import csv
import json
import os
import statistics

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "v0.1.1")


def _csv(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_result_rows_recompute():
    for r in _csv("results.csv"):
        a, e = int(r["ar_tokens"]), int(r["en_tokens"])
        aw, ew = int(r["ar_words"]), int(r["en_words"])
        assert float(r["token_tax_ratio"]) == round(a / e, 4)
        assert float(r["tokens_per_1000_ar_words"]) == round(1000 * a / aw, 1)
        assert float(r["tokens_per_1000_en_words"]) == round(1000 * e / ew, 1)
        assert float(r["ar_tokens_per_page"]) == round(1000 * a / ew, 1)
        assert float(r["ratio_ci95_low"]) <= float(r["token_tax_ratio"]) <= float(r["ratio_ci95_high"])


def test_headline_matches_results():
    with open(os.path.join(RES, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    for slice_id, h in summary["headline"].items():
        ratios = [float(r["token_tax_ratio"]) for r in _csv("results.csv") if r["slice"] == slice_id]
        assert h["n_tokenisers"] == len(ratios)
        assert h["median_ratio"] == round(statistics.median(ratios), 2)


def test_costs_recompute_from_prices_and_results():
    res = {r["tokeniser_id"]: r for r in _csv("results.csv") if r["slice"] == "unpc_test2015"}
    for c in _csv("costs.csv"):
        r = res[c["tokeniser_id"]]
        pin = float(c["input_usd_per_mtok"])
        assert float(c["ar_page_input_usd"]) == pytest.approx(float(r["ar_tokens_per_page"]) * pin / 1e6, abs=1e-6)
        assert float(c["en_page_input_usd"]) == pytest.approx(float(r["en_tokens_per_page"]) * pin / 1e6, abs=1e-6)


def test_equivalents_all_verified():
    with open(os.path.join(RES, "tokenisers.json"), encoding="utf-8") as f:
        toks = json.load(f)
    for t in toks:
        for q in t["equivalents"]:
            assert q["identical_counts"], (t["tokeniser_id"], q["source"])
