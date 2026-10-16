import numpy as np
import pytest

from arabic_token_tax import measure


def test_group_sums_keeps_first_seen_order():
    names, sums = measure.group_sums(["b", "a", "b"], np.array([[1.0], [2.0], [3.0]]))
    assert names == ["b", "a"]
    assert sums[:, 0].tolist() == [4.0, 2.0]


def test_bootstrap_is_deterministic_and_brackets_the_ratio():
    rng = np.random.default_rng(1)
    en = rng.integers(10, 50, size=(200, 2)).astype(float)
    ar = en * np.array([1.5, 2.0]) + rng.normal(0, 2, size=(200, 2))
    lo1, hi1 = measure.bootstrap_ratio_ci(ar, en, resamples=500)
    lo2, hi2 = measure.bootstrap_ratio_ci(ar, en, resamples=500)
    assert np.array_equal(lo1, lo2) and np.array_equal(hi1, hi2)
    point = ar.sum(axis=0) / en.sum(axis=0)
    assert np.all(lo1 <= point) and np.all(point <= hi1)


def _segments():
    return [
        {"doc_id": "d1", "ar_words": 8, "en_words": 10, "ar_chars": 40, "en_chars": 50},
        {"doc_id": "d1", "ar_words": 8, "en_words": 10, "ar_chars": 40, "en_chars": 50},
        {"doc_id": "d2", "ar_words": 4, "en_words": 5, "ar_chars": 20, "en_chars": 25},
    ]


def test_slice_rows_arithmetic():
    rows = measure.slice_rows("s", _segments(), {"t": ([30, 30, 15], [20, 20, 10])}, resamples=200)
    r = rows[0]
    assert (r["ar_tokens"], r["en_tokens"], r["n_groups"]) == (75, 50, 2)
    assert r["token_tax_ratio"] == 1.5
    assert r["tokens_per_1000_ar_words"] == 3750.0
    assert r["tokens_per_1000_en_words"] == 2000.0
    assert r["ar_tokens_per_page"] == 3000.0 and r["en_tokens_per_page"] == 2000.0
    assert r["chars_per_token_ar"] == round(100 / 75, 3)


def test_headline_median_min_max():
    rows = [{"tokeniser_id": k, "token_tax_ratio": v} for k, v in [("a", 1.0), ("b", 2.0), ("c", 4.0), ("d", 3.0)]]
    h = measure.headline(rows)
    assert h == {"n_tokenisers": 4, "median_ratio": 2.5, "min_ratio": 1.0, "min_tokeniser": "a",
                 "max_ratio": 4.0, "max_tokeniser": "c"}


def test_cost_rows():
    prices = [{"vendor": "V", "model_id": "m", "tokeniser_id": "t", "input_usd_per_mtok": 2.0,
               "output_usd_per_mtok": 10.0, "retrieved_at": "x", "source_url": "u"}]
    res = {"t": {"en_tokens_per_page": 1000.0, "ar_tokens_per_page": 1500.0}}
    c = measure.cost_rows(prices, res)[0]
    assert c["en_page_input_usd"] == pytest.approx(0.002)
    assert c["ar_page_input_usd"] == pytest.approx(0.003)
    assert c["ar_page_output_usd"] == pytest.approx(0.015)
    assert c["extra_input_usd_per_1000_pages"] == pytest.approx(1.0)
