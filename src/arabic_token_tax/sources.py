"""Fetch the parallel text and write cleaned segment files.

  unpc_test2015, unpc_dev2015   United Nations Parallel Corpus v1.0, official 2015
                                test and development sets (Arabic-English side)
  tatoeba_ara, tatoeba_arz,     Tatoeba sentences in Standard Arabic, Egyptian Arabic
  tatoeba_arq                   and Algerian Arabic with their English translations

Segment files are JSON Lines, one cleaned pair per line, in DATA_DIR/segments/.
"""
from __future__ import annotations

import bz2
import csv
import hashlib
import json
import os
import tarfile
import urllib.request

from . import textnorm

USER_AGENT = "arabic-token-tax-index (+https://github.com/Bayanat-Labs/arabic-token-tax-index)"

UN_URL = "https://www.un.org/dgacm/sites/www.un.org.dgacm/files/files/UNCORPUS/UNv1.0.testsets.tar.gz"
UN_SHA256 = "0b4040d723eab132fadc7809a329a4787b338a424ef23bfe3e029d41b7e0153d"
UN_MEMBERS = {
    "unpc_test2015": "testsets/testset/UNv1.0.testset",
    "unpc_dev2015": "testsets/devset/UNv1.0.devset",
}

TATOEBA_BASE = "https://downloads.tatoeba.org/exports/per_language/"
TATOEBA_VARIETIES = ("ara", "arz", "arq")

SLICES = {
    "unpc_test2015": {
        "variety": "msa", "variety_name": "Modern Standard Arabic (UN documents)",
        "source": "United Nations Parallel Corpus v1.0, 2015 test set", "url": UN_URL,
        "licence": "United Nations Parallel Corpus terms: credit the United Nations as the source",
        "text_released": True, "group": "UN document",
    },
    "unpc_dev2015": {
        "variety": "msa", "variety_name": "Modern Standard Arabic (UN documents)",
        "source": "United Nations Parallel Corpus v1.0, 2015 development set", "url": UN_URL,
        "licence": "United Nations Parallel Corpus terms: credit the United Nations as the source",
        "text_released": True, "group": "UN document",
    },
    "tatoeba_ara": {
        "variety": "ara", "variety_name": "Standard Arabic (short everyday sentences)",
        "source": "Tatoeba (ara-eng)", "url": TATOEBA_BASE + "ara/",
        "licence": "CC BY 2.0 FR (Tatoeba)", "text_released": False, "group": "sentence",
    },
    "tatoeba_arz": {
        "variety": "arz", "variety_name": "Egyptian Arabic (short everyday sentences)",
        "source": "Tatoeba (arz-eng)", "url": TATOEBA_BASE + "arz/",
        "licence": "CC BY 2.0 FR (Tatoeba)", "text_released": False, "group": "sentence",
    },
    "tatoeba_arq": {
        "variety": "arq", "variety_name": "Algerian Arabic (short everyday sentences)",
        "source": "Tatoeba (arq-eng)", "url": TATOEBA_BASE + "arq/",
        "licence": "CC BY 2.0 FR (Tatoeba)", "text_released": False, "group": "sentence",
    },
}
HEADLINE_SLICE = "unpc_test2015"


def _download(url: str, dest: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(dest + ".part", dest)
    return dest


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare(raw: list[dict]) -> tuple[list[dict], dict]:
    """Clean raw pairs with clean-v1, drop by the pair filter, de-duplicate exact pairs.

    raw items need: segment_id, doc_id, source_ref, text_ar, text_en.
    Returns (segments, report)."""
    kept: list[dict] = []
    seen: set[str] = set()
    dropped: dict[str, int] = {}
    changed = 0
    for r in raw:
        ar, en = textnorm.clean(r["text_ar"]), textnorm.clean(r["text_en"])
        if ar != r["text_ar"] or en != r["text_en"]:
            changed += 1
        reason = textnorm.pair_drop_reason(ar, en)
        key = textnorm.sha256_text(ar + "\n" + en)
        if reason is None and key in seen:
            reason = "duplicate_pair"
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        seen.add(key)
        kept.append({
            "segment_id": r["segment_id"], "doc_id": r["doc_id"], "source_ref": r["source_ref"],
            "text_ar": ar, "text_en": en,
            "sha256_ar": textnorm.sha256_text(ar), "sha256_en": textnorm.sha256_text(en),
            "ar_words": textnorm.word_count(ar), "en_words": textnorm.word_count(en),
            "ar_chars": textnorm.char_count(ar), "en_chars": textnorm.char_count(en),
            "ar_has_diacritics": textnorm.has_diacritic(ar),
        })
    report = {"raw": len(raw), "kept": len(kept), "changed_by_cleaning": changed,
              "dropped": dict(sorted(dropped.items()))}
    return kept, report


def un_raw_pairs(archive: str) -> dict[str, list[dict]]:
    """Read the Arabic, English and id files of both UN sets from the archive
    without extracting it to disk."""
    out: dict[str, list[dict]] = {}
    with tarfile.open(archive, "r:gz") as tf:
        for slice_id, stem in UN_MEMBERS.items():
            def lines(ext: str) -> list[str]:
                f = tf.extractfile(stem + ext)
                if f is None:
                    raise ValueError(f"missing member {stem + ext}")
                return f.read().decode("utf-8").split("\n")[:-1]

            ar, en, ids = lines(".ar"), lines(".en"), lines(".ids")
            if not (len(ar) == len(en) == len(ids)):
                raise ValueError(f"{slice_id}: line counts differ ({len(ar)}, {len(en)}, {len(ids)})")
            out[slice_id] = [
                {"segment_id": f"{slice_id}:{i + 1:04d}", "doc_id": ids[i].split(" ")[0],
                 "source_ref": ids[i], "text_ar": ar[i], "text_en": en[i]}
                for i in range(len(ar))
            ]
    return out


def _read_tsv_bz2(path: str) -> list[list[str]]:
    with bz2.open(path, "rt", encoding="utf-8", newline="") as f:
        return [row for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)]


def tatoeba_raw_pairs(raw_dir: str, variety: str, keep_ids: set[tuple[str, str]] | None = None) -> list[dict]:
    """One pair per Arabic sentence: the linked English sentence with the lowest id.
    keep_ids restricts the pairs to (arabic_id, english_id) pairs listed in a release."""
    ar = {r[0]: r[2] for r in _read_tsv_bz2(os.path.join(raw_dir, f"{variety}_sentences.tsv.bz2")) if len(r) >= 3}
    links: dict[str, list[str]] = {}
    for r in _read_tsv_bz2(os.path.join(raw_dir, f"{variety}-eng_links.tsv.bz2")):
        if len(r) >= 2 and r[0] in ar:
            links.setdefault(r[0], []).append(r[1])
    eng = _english(raw_dir)
    out = []
    for ar_id in sorted(links, key=int):
        cands = sorted((e for e in links[ar_id] if e in eng), key=int)
        if not cands:
            continue
        en_id = cands[0]
        if keep_ids is not None and (ar_id, en_id) not in keep_ids:
            continue
        out.append({"segment_id": f"tatoeba_{variety}:{ar_id}", "doc_id": ar_id,
                    "source_ref": f"https://tatoeba.org/en/sentences/show/{ar_id} -> {en_id}",
                    "text_ar": ar[ar_id], "text_en": eng[en_id]})
    return out


_ENG_CACHE: dict[str, dict[str, str]] = {}


def _english(raw_dir: str) -> dict[str, str]:
    if raw_dir not in _ENG_CACHE:
        _ENG_CACHE[raw_dir] = {r[0]: r[2] for r in _read_tsv_bz2(os.path.join(raw_dir, "eng_sentences.tsv.bz2")) if len(r) >= 3}
    return _ENG_CACHE[raw_dir]


def write_segments(path: str, segments: list[dict], slice_id: str) -> None:
    meta = SLICES[slice_id]
    with open(path, "w", encoding="utf-8") as f:
        for s in segments:
            f.write(json.dumps({"slice": slice_id, "variety": meta["variety"], **s}, ensure_ascii=False) + "\n")


def read_segments(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def fetch(data_dir: str, slices: list[str], tatoeba_ids: str | None = None, offline: bool = False) -> dict:
    """Download (unless offline) and prepare the requested slices. Returns a report."""
    raw_dir = os.path.join(data_dir, "raw")
    seg_dir = os.path.join(data_dir, "segments")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(seg_dir, exist_ok=True)
    report: dict = {"slices": {}, "downloads": {}}

    if any(s.startswith("unpc_") for s in slices):
        archive = os.path.join(raw_dir, "UNv1.0.testsets.tar.gz")
        if not os.path.exists(archive):
            if offline:
                raise FileNotFoundError(archive)
            _download(UN_URL, archive)
        digest = _sha256_file(archive)
        if digest != UN_SHA256:
            raise ValueError(f"UN archive SHA-256 {digest} does not match the pinned {UN_SHA256}")
        report["downloads"]["UNv1.0.testsets.tar.gz"] = {"url": UN_URL, "sha256": digest}
        raw = un_raw_pairs(archive)
        for s in slices:
            if s in raw:
                segs, rep = prepare(raw[s])
                write_segments(os.path.join(seg_dir, f"{s}.jsonl"), segs, s)
                report["slices"][s] = rep

    keep = None
    if tatoeba_ids:
        keep = set()
        with open(tatoeba_ids, encoding="utf-8") as f:
            for line in f:
                p = line.split()
                if len(p) >= 2:
                    keep.add((p[0], p[1]))
    for v in TATOEBA_VARIETIES:
        s = f"tatoeba_{v}"
        if s not in slices:
            continue
        names = [f"{v}_sentences.tsv.bz2", f"{v}-eng_links.tsv.bz2", "eng_sentences.tsv.bz2"]
        for name in names:
            dest = os.path.join(raw_dir, name)
            sub = "eng" if name.startswith("eng_") else v
            if not os.path.exists(dest):
                if offline:
                    raise FileNotFoundError(dest)
                _download(TATOEBA_BASE + f"{sub}/{name}", dest)
            report["downloads"][name] = {"url": TATOEBA_BASE + f"{sub}/{name}", "sha256": _sha256_file(dest)}
        segs, rep = prepare(tatoeba_raw_pairs(raw_dir, v, keep))
        write_segments(os.path.join(seg_dir, f"{s}.jsonl"), segs, s)
        report["slices"][s] = rep
    with open(os.path.join(data_dir, "fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    return report


def tatoeba_id_pairs(segments: list[dict]) -> list[tuple[str, str]]:
    out = []
    for s in segments:
        ref = s["source_ref"]
        ar_id = s["doc_id"]
        en_id = ref.rsplit("-> ", 1)[-1]
        out.append((ar_id, en_id))
    return out
