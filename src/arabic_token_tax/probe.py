"""Diacritics round-trip probe (synthetic).

The probe is generated, not written: every base letter below is combined with
every mark pattern below, in Unicode NFC order, and the syllables are grouped
into lines. It is not natural text and is used only to check whether a
tokeniser's decode(encode(text)) gives back exactly the same code points.
"""
from __future__ import annotations

import unicodedata

PROBE_SPEC = "diacritics-probe-v1"

BASE_LETTERS = (
    "ابتثجحخدذرزسشص"
    "ضطظعغفقكلمنهوي"
    "ءأإآؤئةى"
)

FATHA, DAMMA, KASRA = "َ", "ُ", "ِ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
SHADDA, SUKUN = "ّ", "ْ"
SUPERSCRIPT_ALEF = "ٰ"

MARK_PATTERNS = (
    FATHA, DAMMA, KASRA, SUKUN, FATHATAN, DAMMATAN, KASRATAN,
    SHADDA + FATHA, SHADDA + DAMMA, SHADDA + KASRA,
    SHADDA + FATHATAN, SHADDA + DAMMATAN, SHADDA + KASRATAN,
    SUPERSCRIPT_ALEF,
)

# Extra sequences: tatweel and lam-alef carrying marks.
EXTRA = (
    "ـ" + FATHA, "ـ" + SHADDA + DAMMA, "ل" + FATHA + "ا",
    "ل" + KASRA + "ا" + FATHATAN,
)

SYLLABLES_PER_WORD = 3
WORDS_PER_LINE = 8


def syllables() -> list[str]:
    out = [unicodedata.normalize("NFC", b + m) for b in BASE_LETTERS for m in MARK_PATTERNS]
    out += [unicodedata.normalize("NFC", s) for s in EXTRA]
    return out


def probe_lines() -> list[str]:
    syl = syllables()
    words = ["".join(syl[i:i + SYLLABLES_PER_WORD]) for i in range(0, len(syl), SYLLABLES_PER_WORD)]
    return [" ".join(words[i:i + WORDS_PER_LINE]) for i in range(0, len(words), WORDS_PER_LINE)]


def marked_letters() -> int:
    return len(syllables())
