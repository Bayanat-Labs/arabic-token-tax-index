"""Load tokenisers from config/tokenisers.yaml and count tokens.

Three routes:
  tiktoken       an encoding shipped with the tiktoken package (encode_ordinary)
  hf             a tokenizer.json file from a Hugging Face model repository at a
                 pinned revision, run with the `tokenizers` library
                 (add_special_tokens=False)
  sentencepiece  a tokenizer.model file from a Hugging Face model repository at a
                 pinned revision, run with the `sentencepiece` library (no BOS/EOS)

Only tokenizer files are downloaded, never model weights. No model code is run.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Callable, Sequence


@dataclass
class Tokeniser:
    source: str                     # human-readable source: encoding name or repo@revision
    route: str
    vocab_size: int
    file_sha256: str | None
    library: str                    # library name and version used to run it
    _encode: Callable[[Sequence[str]], list[list[int]]] = field(repr=False)
    _decode: Callable[[list[int]], str] = field(repr=False)

    def encode(self, texts: Sequence[str]) -> list[list[int]]:
        return self._encode(list(texts))

    def count(self, texts: Sequence[str]) -> list[int]:
        return [len(ids) for ids in self.encode(texts)]

    def roundtrip(self, text: str) -> bool:
        ids = self.encode([text])[0]
        try:
            return self._decode(ids) == text
        except Exception:  # undecodable byte sequences count as a failed round trip
            return False


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _hf_file(repo_id: str, filename: str, revision: str) -> str:
    from huggingface_hub import hf_hub_download

    return hf_hub_download(repo_id=repo_id, filename=filename, revision=revision)


def load(spec: dict) -> Tokeniser:
    """Load one tokeniser from a config entry (or an `equivalents` entry)."""
    route = spec["route"]
    if route == "tiktoken":
        import tiktoken

        enc = tiktoken.get_encoding(spec["encoding"])

        def _decode(ids: list[int]) -> str:
            return enc.decode_bytes(ids).decode("utf-8", errors="strict")

        return Tokeniser(
            source=spec["encoding"], route=route, vocab_size=enc.n_vocab, file_sha256=None,
            library=f"tiktoken {tiktoken.__version__}",
            _encode=lambda texts: enc.encode_ordinary_batch(texts), _decode=_decode,
        )
    if route == "hf":
        import tokenizers

        path = _hf_file(spec["repo_id"], spec.get("file", "tokenizer.json"), spec["revision"])
        tok = tokenizers.Tokenizer.from_file(path)

        def _encode(texts: list[str]) -> list[list[int]]:
            return [e.ids for e in tok.encode_batch(texts, add_special_tokens=False)]

        return Tokeniser(
            source=f"{spec['repo_id']}@{spec['revision']}", route=route,
            vocab_size=tok.get_vocab_size(with_added_tokens=True), file_sha256=_sha256_file(path),
            library=f"tokenizers {tokenizers.__version__}",
            _encode=_encode, _decode=lambda ids: tok.decode(ids, skip_special_tokens=False),
        )
    if route == "sentencepiece":
        import sentencepiece as spm

        path = _hf_file(spec["repo_id"], spec.get("file", "tokenizer.model"), spec["revision"])
        sp = spm.SentencePieceProcessor(model_file=path)
        return Tokeniser(
            source=f"{spec['repo_id']}@{spec['revision']}", route=route,
            vocab_size=sp.get_piece_size(), file_sha256=_sha256_file(path),
            library=f"sentencepiece {spm.__version__}",
            _encode=lambda texts: sp.encode(texts), _decode=lambda ids: sp.decode(ids),
        )
    raise ValueError(f"unknown route: {route!r}")


def load_config(path: str) -> dict:
    import yaml

    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    ids = [t["id"] for t in cfg.get("tokenisers", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate tokeniser ids in config")
    return cfg


def default_config_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "config", "tokenisers.yaml")


def default_prices_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "config", "prices.yaml")
