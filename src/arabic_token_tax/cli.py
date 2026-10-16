"""Command line: arabic-token-tax {fetch,run,count,words,probe,compare}."""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import sys

from . import __version__, measure, probe, sources, textnorm
from .tokenisers import default_config_path, default_prices_path, load, load_config

RESULT_COLUMNS = [
    "row_id", "tokeniser_id", "label", "vendor", "slice", "variety", "n_segments", "n_groups",
    "ar_words", "en_words", "ar_chars", "en_chars", "ar_tokens", "en_tokens",
    "tokens_per_1000_ar_words", "tokens_per_1000_en_words", "token_tax_ratio",
    "ratio_ci95_low", "ratio_ci95_high", "chars_per_token_ar", "chars_per_token_en",
    "ar_tokens_per_page", "en_tokens_per_page", "tokeniser_version", "run_date", "harness_version",
]


def _write_csv(path: str, rows: list[dict], columns: list[str] | None = None) -> None:
    columns = columns or (list(rows[0]) if rows else [])
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                        for k, v in r.items()})


def _write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _version_string(tok, spec: dict) -> str:
    if spec["route"] == "tiktoken":
        return f"{spec['encoding']} ({tok.library})"
    return f"{spec['repo_id']}@{spec['revision']}/{spec.get('file', 'tokenizer.json' if spec['route'] == 'hf' else 'tokenizer.model')}"


def cmd_fetch(a: argparse.Namespace) -> int:
    slices = a.slices.split(",") if a.slices else list(sources.SLICES)
    rep = sources.fetch(a.data, slices, tatoeba_ids=a.tatoeba_ids, offline=a.offline)
    print(json.dumps(rep["slices"], indent=1))
    return 0


def cmd_run(a: argparse.Namespace) -> int:
    cfg = load_config(a.config)
    entries = cfg["tokenisers"]
    if a.only:
        keep = set(a.only.split(","))
        entries = [e for e in entries if e["id"] in keep]
    seg_dir = os.path.join(a.data, "segments")
    slice_ids = [s for s in sources.SLICES if os.path.exists(os.path.join(seg_dir, f"{s}.jsonl"))]
    if a.slices:
        slice_ids = [s for s in slice_ids if s in a.slices.split(",")]
    if not slice_ids:
        print(f"no segment files in {seg_dir}; run `arabic-token-tax fetch` first", file=sys.stderr)
        return 2
    segs = {s: sources.read_segments(os.path.join(seg_dir, f"{s}.jsonl")) for s in slice_ids}
    lines = probe.probe_lines()
    run_date = a.run_date or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    os.makedirs(a.out, exist_ok=True)

    counts: dict[str, dict[str, tuple[list[int], list[int]]]] = {s: {} for s in slice_ids}
    tok_rows: list[dict] = []
    for e in entries:
        print(f"[{e['id']}] loading {e.get('encoding') or e.get('repo_id')}", file=sys.stderr)
        tok = load(e)
        sig = []
        for s in slice_ids:
            ar = tok.count([x["text_ar"] for x in segs[s]])
            en = tok.count([x["text_en"] for x in segs[s]])
            counts[s][e["id"]] = (ar, en)
            sig.append((ar, en))
        probe_counts = tok.count(lines)
        probe_fail = sum(0 if tok.roundtrip(x) else 1 for x in lines)
        head = sources.HEADLINE_SLICE if sources.HEADLINE_SLICE in segs else slice_ids[0]
        ar_texts = [x["text_ar"] for x in segs[head]]
        rt_ok = sum(1 for x in ar_texts if tok.roundtrip(x))
        diac = [x["text_ar"] for x in segs[head] if x.get("ar_has_diacritics")]
        rt_diac_ok = sum(1 for x in diac if tok.roundtrip(x))
        equivalents = []
        for q in e.get("equivalents", []):
            print(f"[{e['id']}]   equivalent {q.get('encoding') or q.get('repo_id')}", file=sys.stderr)
            qt = load(q)
            mism = 0
            for i, s in enumerate(slice_ids):
                qa = qt.count([x["text_ar"] for x in segs[s]])
                qe = qt.count([x["text_en"] for x in segs[s]])
                mism += sum(1 for u, v in zip(qa, sig[i][0]) if u != v)
                mism += sum(1 for u, v in zip(qe, sig[i][1]) if u != v)
            mism += sum(1 for u, v in zip(qt.count(lines), probe_counts) if u != v)
            equivalents.append({"source": _version_string(qt, q), "models": q.get("models", []),
                                "identical_counts": mism == 0, "differing_texts": mism})
        tok_rows.append({
            "tokeniser_id": e["id"], "label": e["label"], "vendor": e["vendor"], "route": e["route"],
            "tokeniser_version": _version_string(tok, e), "file_sha256": tok.file_sha256,
            "library": tok.library, "vocab_size": tok.vocab_size, "licence": e.get("licence"),
            "models": e.get("models", []), "models_basis": e.get("models_basis"),
            "equivalents": equivalents,
            "diacritics_probe_lines": len(lines), "diacritics_probe_failures": probe_fail,
            "diacritics_roundtrip": probe_fail == 0,
            "roundtrip_slice": head, "roundtrip_ar_segments": len(ar_texts), "roundtrip_ar_exact": rt_ok,
            "roundtrip_ar_diacritised_segments": len(diac), "roundtrip_ar_diacritised_exact": rt_diac_ok,
        })

    meta = {e["id"]: e for e in entries}
    tinfo = {t["tokeniser_id"]: t for t in tok_rows}
    results: list[dict] = []
    for s in slice_ids:
        for r in measure.slice_rows(s, segs[s], counts[s], resamples=a.resamples):
            t = r["tokeniser_id"]
            r.update(row_id=f"{t}:{s}:{run_date}", label=meta[t]["label"], vendor=meta[t]["vendor"],
                     variety=sources.SLICES[s]["variety"], tokeniser_version=tinfo[t]["tokeniser_version"],
                     run_date=run_date, harness_version=__version__)
            results.append(r)

    _write_csv(os.path.join(a.out, "results.csv"), results, RESULT_COLUMNS)
    _write_json(os.path.join(a.out, "results.json"), [{k: r[k] for k in RESULT_COLUMNS} for r in results])
    _write_csv(os.path.join(a.out, "tokenisers.csv"), tok_rows)
    _write_json(os.path.join(a.out, "tokenisers.json"), tok_rows)
    _write_csv(os.path.join(a.out, "not_measured.csv"), cfg.get("not_measured", []),
               ["name", "vendor", "models", "reason", "checked_on"])

    seg_out = os.path.join(a.out, "segment_counts")
    os.makedirs(seg_out, exist_ok=True)
    for s in slice_ids:
        released = sources.SLICES[s]["text_released"]
        rows = []
        for i, x in enumerate(segs[s]):
            row = {k: x[k] for k in ("segment_id", "doc_id", "source_ref", "sha256_ar", "sha256_en",
                                       "ar_words", "en_words", "ar_chars", "en_chars", "ar_has_diacritics")}
            if released:
                row["text_ar"], row["text_en"] = x["text_ar"], x["text_en"]
            for t in counts[s]:
                row[f"{t}__ar"], row[f"{t}__en"] = counts[s][t][0][i], counts[s][t][1][i]
            rows.append(row)
        _write_csv(os.path.join(seg_out, f"{s}.csv"), rows)
        if s.startswith("tatoeba_"):
            with open(os.path.join(seg_out, f"{s}.ids.txt"), "w", encoding="utf-8") as f:
                for ar_id, en_id in sources.tatoeba_id_pairs(segs[s]):
                    f.write(f"{ar_id} {en_id}\n")

    slices_meta = []
    fetch_report = {}
    fr = os.path.join(a.data, "fetch_report.json")
    if os.path.exists(fr):
        with open(fr, encoding="utf-8") as f:
            fetch_report = json.load(f).get("slices", {})
    for s in slice_ids:
        m = sources.SLICES[s]
        rep = fetch_report.get(s, {})
        slices_meta.append({"slice": s, **m, "n_segments": len(segs[s]),
                            "n_groups": len({x["doc_id"] for x in segs[s]}),
                            "raw_pairs": rep.get("raw"), "dropped": rep.get("dropped"),
                            "changed_by_cleaning": rep.get("changed_by_cleaning"),
                            "ar_segments_with_diacritics": sum(1 for x in segs[s] if x.get("ar_has_diacritics"))})
    _write_csv(os.path.join(a.out, "slices.csv"), slices_meta)

    costs: list[dict] = []
    prices: list[dict] = []
    if a.prices and os.path.exists(a.prices):
        import yaml

        with open(a.prices, encoding="utf-8") as f:
            pdoc = yaml.safe_load(f)
        prices = pdoc.get("prices", [])
        head = sources.HEADLINE_SLICE
        by_tok = {r["tokeniser_id"]: r for r in results if r["slice"] == head}
        costs = measure.cost_rows(prices, by_tok)
        _write_csv(os.path.join(a.out, "prices.csv"), prices)
        _write_csv(os.path.join(a.out, "costs.csv"), costs)
        _write_csv(os.path.join(a.out, "prices_not_shown.csv"), pdoc.get("prices_not_shown", []),
                   ["tokeniser_id", "reason"])

    summary = {
        "harness_version": __version__, "run_date": run_date, "wordcount_spec": textnorm.WORDCOUNT_SPEC,
        "cleaning_spec": textnorm.CLEANING_SPEC, "probe_spec": probe.PROBE_SPEC,
        "bootstrap": {"resamples": a.resamples, "seed": measure.BOOTSTRAP_SEED, "unit": "UN document or Tatoeba sentence"},
        "page_en_words": measure.PAGE_EN_WORDS,
        "headline_slice": sources.HEADLINE_SLICE,
        "headline": {s: measure.headline(r for r in results if r["slice"] == s) for s in slice_ids},
        "n_tokenisers_measured": len(tok_rows), "n_not_measured": len(cfg.get("not_measured", [])),
        "n_prices": len(prices),
        "diacritics_probe": {"lines": len(lines), "marked_letters": probe.marked_letters()},
    }
    _write_json(os.path.join(a.out, "summary.json"), summary)
    print(json.dumps(summary["headline"], indent=1))
    return 0


def cmd_count(a: argparse.Namespace) -> int:
    cfg = load_config(a.config)
    text = a.text if a.text is not None else sys.stdin.read()
    text = textnorm.clean(text)
    ids = a.tokeniser.split(",") if a.tokeniser else [e["id"] for e in cfg["tokenisers"]]
    print(f"words (wordcount-v1): {textnorm.word_count(text)}")
    for e in cfg["tokenisers"]:
        if e["id"] in ids:
            print(f"{e['id']}\t{load(e).count([text])[0]}")
    return 0


def cmd_words(a: argparse.Namespace) -> int:
    text = textnorm.clean(a.text if a.text is not None else sys.stdin.read())
    for w in textnorm.words(text):
        print(w)
    return 0


def cmd_probe(a: argparse.Namespace) -> int:
    for line in probe.probe_lines():
        print(line)
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    def read(p: str) -> dict:
        with open(os.path.join(p, "results.csv"), encoding="utf-8") as f:
            return {(r["tokeniser_id"], r["slice"]): r for r in csv.DictReader(f)}

    x, y = read(a.new), read(a.reference)
    diff = 0
    for k in sorted(x):
        if k not in y:
            print(f"not in the reference: {k}")
            diff += 1
            continue
        for col in ("n_segments", "ar_words", "en_words", "ar_tokens", "en_tokens"):
            if x[k][col] != y[k][col]:
                print(f"{k} {col}: {x[k][col]} != {y[k][col]}")
                diff += 1
    print(f"{len(x)} rows: identical counts" if diff == 0 else f"{diff} differences")
    return 0 if diff == 0 else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="arabic-token-tax", description="Arabic token-tax index harness")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download and clean the parallel text")
    f.add_argument("--data", default="data")
    f.add_argument("--slices", help="comma-separated slice ids (default: all)")
    f.add_argument("--tatoeba-ids", help="file of 'arabic_id english_id' pairs to keep")
    f.add_argument("--offline", action="store_true", help="use files already in DATA/raw")
    f.set_defaults(fn=cmd_fetch)

    r = sub.add_parser("run", help="count tokens and write the index files")
    r.add_argument("--config", default=default_config_path())
    r.add_argument("--prices", default=default_prices_path(), help="price file ('' for none)")
    r.add_argument("--data", default="data")
    r.add_argument("--out", default="out")
    r.add_argument("--only", help="comma-separated tokeniser ids")
    r.add_argument("--slices", help="comma-separated slice ids")
    r.add_argument("--resamples", type=int, default=measure.BOOTSTRAP_RESAMPLES)
    r.add_argument("--run-date", help="date written into the rows (default: today, UTC)")
    r.set_defaults(fn=cmd_run)

    c = sub.add_parser("count", help="count tokens in a text with each tokeniser")
    c.add_argument("text", nargs="?")
    c.add_argument("--config", default=default_config_path())
    c.add_argument("--tokeniser", help="comma-separated tokeniser ids")
    c.set_defaults(fn=cmd_count)

    w = sub.add_parser("words", help="print the wordcount-v1 words of a text")
    w.add_argument("text", nargs="?")
    w.set_defaults(fn=cmd_words)

    pr = sub.add_parser("probe", help="print the diacritics probe")
    pr.set_defaults(fn=cmd_probe)

    cp = sub.add_parser("compare", help="check that every row of a new run matches a reference run")
    cp.add_argument("new", help="result directory of the new run")
    cp.add_argument("reference", help="result directory to compare with, e.g. results/v0.1.0")
    cp.set_defaults(fn=cmd_compare)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
