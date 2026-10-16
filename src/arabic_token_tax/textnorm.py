"""Text cleaning and the wordcount-v1 word and character counts.

Everything here is standard library only, so the counts can be checked without
any tokeniser installed. The rules are written out in docs/METHOD.md.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata

WORDCOUNT_SPEC = "wordcount-v1"
CLEANING_SPEC = "clean-v1"

ZWNJ = "‌"
# Characters that join two word characters into one word (wordcount-v1).
_JOIN_ANY = {"'", "’", "-"}
# Characters that join two digits into one number (1,000  2.5  ١٬٠٠٠  ٢٫٥).
_JOIN_DIGITS = {",", ".", "٫", "٬"}
_SPACES = re.compile(r" {2,}")

# Unicode blocks counted as Arabic script for the letter-share rule.
ARABIC_RANGES = (
    (0x0600, 0x06FF),  # Arabic
    (0x0750, 0x077F),  # Arabic Supplement
    (0x0870, 0x089F),  # Arabic Extended-B
    (0x08A0, 0x08FF),  # Arabic Extended-A
    (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
)

# Arabic combining marks treated as diacritics (harakat, tanwin, shadda, sukun,
# superscript alef and the hamza/madda marks).
DIACRITICS = frozenset(
    [chr(c) for c in range(0x064B, 0x0660)] + ["ٰ"]
)


def is_arabic(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in ARABIC_RANGES)


def clean(text: str) -> str:
    """clean-v1: NFC; drop control and format characters (keep ZWNJ);
    every white-space character becomes a space; runs of spaces collapse; trim."""
    t = unicodedata.normalize("NFC", text)
    out = []
    for ch in t:
        if ch.isspace():
            out.append(" ")
            continue
        cat = unicodedata.category(ch)
        if cat == "Cc":
            continue
        if cat == "Cf" and ch != ZWNJ:
            continue
        out.append(ch)
    return _SPACES.sub(" ", "".join(out)).strip()


def _is_word_char(ch: str) -> bool:
    cat = unicodedata.category(ch)
    return cat[0] in ("L", "M") or cat == "Nd"


def _is_digit(ch: str) -> bool:
    return unicodedata.category(ch) == "Nd"


def words(text: str) -> list[str]:
    """wordcount-v1 words: maximal runs of letters (L*), marks (M*) and decimal
    digits (Nd). An apostrophe (' or U+2019) or a hyphen between two word
    characters, and a comma, full stop, U+066B or U+066C between two digits,
    stay inside the word. Everything else separates words. Clitics are not split."""
    out: list[str] = []
    cur: list[str] = []
    n = len(text)
    for i, ch in enumerate(text):
        if _is_word_char(ch):
            cur.append(ch)
            continue
        if cur and i + 1 < n:
            nxt = text[i + 1]
            if ch in _JOIN_ANY and _is_word_char(nxt):
                cur.append(ch)
                continue
            if ch in _JOIN_DIGITS and _is_digit(cur[-1]) and _is_digit(nxt):
                cur.append(ch)
                continue
        if cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def word_count(text: str) -> int:
    return len(words(text))


def char_count(text: str) -> int:
    """Characters = Unicode code points that are not white space."""
    return sum(1 for ch in text if not ch.isspace())


def arabic_letter_share(text: str) -> float:
    """Share of letters (L*) that are in the Arabic blocks; 0.0 when there are no letters."""
    letters = [ch for ch in text if unicodedata.category(ch)[0] == "L"]
    if not letters:
        return 0.0
    return sum(1 for ch in letters if is_arabic(ch)) / len(letters)


def has_diacritic(text: str) -> bool:
    return any(ch in DIACRITICS for ch in text)


def strip_diacritics(text: str) -> str:
    return "".join(ch for ch in text if ch not in DIACRITICS)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Pair filter of clean-v1.
MIN_ARABIC_SHARE = 0.5
LENGTH_RATIO_RANGE = (0.4, 2.5)


def pair_drop_reason(text_ar: str, text_en: str) -> str | None:
    """Reason to drop a cleaned pair, or None to keep it."""
    if not text_ar or not text_en:
        return "empty_side"
    if arabic_letter_share(text_ar) < MIN_ARABIC_SHARE:
        return "arabic_side_not_arabic_script"
    ratio = char_count(text_ar) / max(1, char_count(text_en))
    lo, hi = LENGTH_RATIO_RANGE
    if not (lo <= ratio <= hi):
        return "length_ratio_out_of_range"
    return None
