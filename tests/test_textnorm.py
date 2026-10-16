from arabic_token_tax import textnorm as t


def test_clean_nfc_controls_and_spaces():
    # shadda before fatha is reordered by NFC; ZWSP and RLM are removed; ZWNJ is kept
    raw = "  شَّر​ق‏ ‌\tx y  "
    assert t.clean(raw) == "شَّرق ‌ x y"


def test_words_english():
    assert t.words("The UN’s 1,000-page report (A/70/1) said: well-known.") == [
        "The", "UN’s", "1,000-page", "report", "A", "70", "1", "said", "well-known"]


def test_words_arabic_clitics_not_split_and_digits_joined():
    text = "وقال الأمين: ١٬٠٠٠ و٢٫٥"
    assert t.words(text) == ["وقال", "الأمين",
                             "١٬٠٠٠", "و٢٫٥"]


def test_words_marks_and_tatweel_stay_inside():
    assert t.word_count("كَتَبَ عــرب") == 2


def test_char_count_ignores_white_space():
    assert t.char_count("a b\tc\n") == 3


def test_arabic_share_and_pair_filter():
    assert t.arabic_letter_share("Original: English") == 0.0
    assert t.pair_drop_reason("Original: English", "Original: English") == "arabic_side_not_arabic_script"
    assert t.pair_drop_reason("", "x") == "empty_side"
    assert t.pair_drop_reason("ب" * 10, "x" * 100) == "length_ratio_out_of_range"
    assert t.pair_drop_reason("بيت", "house") is None


def test_diacritics_helpers():
    assert t.has_diacritic("كَ") and not t.has_diacritic("ك")
    assert t.strip_diacritics("كَتّ") == "كت"
