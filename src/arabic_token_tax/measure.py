"""Measures: tokens per 1,000 words, the Arabic/English token ratio with a
document-level bootstrap interval, characters per token, round trips and cost."""
from __future__ import annotations

import statistics
from typing import Iterable

import numpy as np

BOOTSTRAP_SEED = 20261013
BOOTSTRAP_RESAMPLES = 10_000
PAGE_EN_WORDS = 1000  # a page is the content of 1,000 English words (wordcount-v1)


def group_sums(groups: list[str], values: np.ndarray) -> tuple[list[str], np.ndarray]:
    """Sum per-segment values (n_segments x k) by group, keeping first-seen group order."""
    order: dict[str, int] = {}
    idx = np.empty(len(groups), dtype=np.int64)
    for i, g in enumerate(groups):
        idx[i] = order.setdefault(g, len(order))
    out = np.zeros((len(order), values.shape[1]), dtype=np.float64)
    np.add.at(out, idx, values)
    return list(order), out


def bootstrap_ratio_ci(ar_g: np.ndarray, en_g: np.ndarray, resamples: int = BOOTSTRAP_RESAMPLES,
                       seed: int = BOOTSTRAP_SEED, chunk: int = 250) -> tuple[np.ndarray, np.ndarray]:
    """Percentile 95% interval of sum(ar)/sum(en) under resampling of groups with
    replacement. ar_g and en_g are (n_groups x n_tokenisers); every tokeniser sees
    the same resamples, so intervals are paired. Returns (low, high) arrays."""
    n = ar_g.shape[0]
    rng = np.random.default_rng(seed)
    ratios = []
    done = 0
    while done < resamples:
        c = min(chunk, resamples - done)
        idx = rng.integers(0, n, size=(c, n))
        w = np.stack([np.bincount(row, minlength=n) for row in idx]).astype(np.float64)
        ratios.append((w @ ar_g) / (w @ en_g))
        done += c
    r = np.concatenate(ratios, axis=0)
    lo, hi = np.percentile(r, [2.5, 97.5], axis=0)
    return lo, hi


def slice_rows(slice_id: str, segments: list[dict], counts: dict[str, tuple[list[int], list[int]]],
               resamples: int = BOOTSTRAP_RESAMPLES, seed: int = BOOTSTRAP_SEED) -> list[dict]:
    """One result row per tokeniser for one slice. counts maps tokeniser id to
    (arabic counts, english counts), one entry per segment."""
    tids = list(counts)
    ar = np.array([counts[t][0] for t in tids], dtype=np.float64).T
    en = np.array([counts[t][1] for t in tids], dtype=np.float64).T
    groups = [s["doc_id"] for s in segments]
    _, ar_g = group_sums(groups, ar)
    _, en_g = group_sums(groups, en)
    lo, hi = bootstrap_ratio_ci(ar_g, en_g, resamples=resamples, seed=seed)
    ar_words = sum(s["ar_words"] for s in segments)
    en_words = sum(s["en_words"] for s in segments)
    ar_chars = sum(s["ar_chars"] for s in segments)
    en_chars = sum(s["en_chars"] for s in segments)
    rows = []
    for j, t in enumerate(tids):
        a, e = int(ar[:, j].sum()), int(en[:, j].sum())
        rows.append({
            "tokeniser_id": t, "slice": slice_id,
            "n_segments": len(segments), "n_groups": int(ar_g.shape[0]),
            "ar_words": ar_words, "en_words": en_words, "ar_chars": ar_chars, "en_chars": en_chars,
            "ar_tokens": a, "en_tokens": e,
            "tokens_per_1000_ar_words": round(1000 * a / ar_words, 1),
            "tokens_per_1000_en_words": round(1000 * e / en_words, 1),
            "token_tax_ratio": round(a / e, 4),
            "ratio_ci95_low": round(float(lo[j]), 4), "ratio_ci95_high": round(float(hi[j]), 4),
            "chars_per_token_ar": round(ar_chars / a, 3), "chars_per_token_en": round(en_chars / e, 3),
            "ar_tokens_per_page": round(PAGE_EN_WORDS * a / en_words, 1),
            "en_tokens_per_page": round(PAGE_EN_WORDS * e / en_words, 1),
        })
    return rows


def headline(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    ratios = [r["token_tax_ratio"] for r in rows]
    lo = min(rows, key=lambda r: r["token_tax_ratio"])
    hi = max(rows, key=lambda r: r["token_tax_ratio"])
    return {
        "n_tokenisers": len(rows),
        "median_ratio": round(statistics.median(ratios), 2),
        "min_ratio": round(lo["token_tax_ratio"], 2), "min_tokeniser": lo["tokeniser_id"],
        "max_ratio": round(hi["token_tax_ratio"], 2), "max_tokeniser": hi["tokeniser_id"],
    }


def cost_rows(prices: list[dict], results: dict[str, dict]) -> list[dict]:
    """Cost of one page (the content of 1,000 English words) in English and in its
    Arabic translation, at input and at output list prices. results maps
    tokeniser id to its headline-slice result row."""
    out = []
    for p in prices:
        r = results.get(p["tokeniser_id"])
        if r is None:
            continue
        en_t, ar_t = r["en_tokens_per_page"], r["ar_tokens_per_page"]
        pin, pout = float(p["input_usd_per_mtok"]), float(p["output_usd_per_mtok"])
        out.append({
            "vendor": p["vendor"], "model_id": p["model_id"], "tokeniser_id": p["tokeniser_id"],
            "input_usd_per_mtok": pin, "output_usd_per_mtok": pout,
            "en_tokens_per_page": en_t, "ar_tokens_per_page": ar_t,
            "en_page_input_usd": round(en_t * pin / 1e6, 6), "ar_page_input_usd": round(ar_t * pin / 1e6, 6),
            "en_page_output_usd": round(en_t * pout / 1e6, 6), "ar_page_output_usd": round(ar_t * pout / 1e6, 6),
            "extra_input_usd_per_1000_pages": round((ar_t - en_t) * pin / 1e3, 4),
            "extra_output_usd_per_1000_pages": round((ar_t - en_t) * pout / 1e3, 4),
            "price_retrieved_at": p["retrieved_at"], "price_source_url": p["source_url"],
        })
    return out
