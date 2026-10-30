# Method (index version 0.1.0)

This page defines every number in the Arabic Token-Tax Index. The code that implements it is in `src/arabic_token_tax/`; the tests in `tests/` check the arithmetic.

## 1. Text

| Slice | Text | Pairs before cleaning | Unit for the confidence interval |
|---|---|---|---|
| `unpc_test2015` (headline) | United Nations Parallel Corpus v1.0, official 2015 test set, Arabic and English sides | 4,000 | UN document (the first field of `UNv1.0.testset.ids`) |
| `unpc_dev2015` | the same corpus, official 2015 development set | 4,000 | UN document |
| `tatoeba_ara` | Tatoeba sentences tagged Standard Arabic (`ara`) with an English translation | one pair per Arabic sentence | sentence |
| `tatoeba_arz` | Tatoeba sentences tagged Egyptian Arabic (`arz`) | one pair per Arabic sentence | sentence |
| `tatoeba_arq` | Tatoeba sentences tagged Algerian Arabic (`arq`) | one pair per Arabic sentence | sentence |

The UN archive `UNv1.0.testsets.tar.gz` is downloaded from the United Nations and checked against a pinned SHA-256 (`src/arabic_token_tax/sources.py`). The UN sets were drawn by their publishers from documents released in 2015 (development set: first quarter; test set: second quarter), keeping only translation tuples whose English sentence is unique.

For Tatoeba, each Arabic sentence is paired with the linked English sentence that has the lowest id. Tatoeba exports change weekly; `results/v0.1.0/tatoeba_ids.txt` lists the `arabic_id english_id` pairs used in this version, and `arabic-token-tax fetch --tatoeba-ids` restricts a new download to them.

Tatoeba sentences are short and conversational, and the UN sentences are long and formal. Compare the Egyptian and Algerian rows with the Tatoeba Standard Arabic row, not with the UN rows.

## 2. Cleaning (`clean-v1`)

Both sides of every pair:

1. Unicode NFC.
2. Control characters (category Cc) and format characters (category Cf) are removed, except ZERO WIDTH NON-JOINER (U+200C).
3. Every white-space character becomes a space; runs of spaces become one space; leading and trailing spaces are removed.

A pair is dropped when:

- either side is empty;
- fewer than half of the letters on the Arabic side are in the Arabic Unicode blocks (U+0600–06FF, U+0750–077F, U+0870–089F, U+08A0–08FF, U+FB50–FDFF, U+FE70–FEFF), for example an untranslated English line;
- the Arabic side has fewer than 0.4 or more than 2.5 times as many characters as the English side (a likely misalignment);
- it repeats an earlier pair exactly.

`slices.csv` gives, per slice, the number of pairs before cleaning, the number dropped for each reason and the number changed by cleaning.

## 3. Words and characters (`wordcount-v1`)

- A **word** is a maximal run of characters whose Unicode general category is a letter (L\*), a mark (M\*) or a decimal digit (Nd). An apostrophe (U+0027 or U+2019) or a hyphen between two such characters, and a comma, full stop, ARABIC DECIMAL SEPARATOR (U+066B) or ARABIC THOUSANDS SEPARATOR (U+066C) between two digits, stay inside the word. Everything else separates words.
- The same rule is used for Arabic and English. Arabic clitics are not split: «وقال» is one word. Arabic therefore has fewer, longer words than English for the same content, which is why the ratio on parallel text (section 5) is the headline and the per-word figures are secondary.
- A **character** is a Unicode code point that is not white space.

## 4. Token counts

Each segment is encoded on its own, with no special tokens added:

| Route | Library | Call |
|---|---|---|
| `tiktoken` | tiktoken | `encoding.encode_ordinary(text)` |
| `hf` | tokenizers | `Tokenizer.from_file(tokenizer.json).encode(text, add_special_tokens=False)` |
| `sentencepiece` | sentencepiece | `SentencePieceProcessor(model_file=tokenizer.model).encode(text)` (no BOS or EOS) |

Only tokenizer files are downloaded (at the revision pinned in `config/tokenisers.yaml`), never model weights, and no model code is run.

When several models publish tokenizer files, one is measured and the others are listed as `equivalents`. At run time every equivalent is loaded and must give the same token count as the measured file on every segment of every slice and on every probe line; `tokenisers.json` records the result (`identical_counts`, `differing_texts`).

Model lists (`models`, with `models_basis`): for the two OpenAI encodings, the model names that tiktoken 0.14.0 maps to the encoding in its model-to-encoding table; these names are not separate tokenizer files and were not count-checked (the gpt-oss tokenizer files, listed as equivalents, were). For the other tokenisers, the model whose repository publishes the measured file, plus the models of the checked equivalents.

## 5. Measures

For a tokeniser on a slice, with sums over all segments:

| Field | Definition |
|---|---|
| `token_tax_ratio` | Σ Arabic tokens ÷ Σ English tokens. The same content in Arabic takes this many times as many tokens as in English. |
| `ratio_ci95_low`, `ratio_ci95_high` | Percentile 95% interval from 10,000 bootstrap resamples of the slice's units (UN documents, or Tatoeba sentences), drawn with replacement, seed 20261013. All tokenisers see the same resamples. |
| `tokens_per_1000_ar_words` | 1,000 × Σ Arabic tokens ÷ Σ Arabic words |
| `tokens_per_1000_en_words` | 1,000 × Σ English tokens ÷ Σ English words |
| `chars_per_token_ar`, `chars_per_token_en` | Σ characters ÷ Σ tokens, per side |
| `en_tokens_per_page` | tokens for one page: the content of 1,000 English words = 1,000 × Σ English tokens ÷ Σ English words |
| `ar_tokens_per_page` | tokens for the Arabic translation of the same page = 1,000 × Σ Arabic tokens ÷ Σ English words |

The headline is the median `token_tax_ratio` across the measured tokenisers on `unpc_test2015`, with the lowest and highest named. A ratio below 1 means Arabic took fewer tokens than English for the same content.

## 6. Round trips

- **Diacritics probe** (`diacritics-probe-v1`, synthetic): every one of 36 base letters with each of 14 mark patterns (fatha, damma, kasra, sukun, the three tanwin, shadda with each of the six vowel and tanwin marks, superscript alef), plus tatweel and lam-alef carrying marks, in NFC order, grouped into lines. `arabic-token-tax probe` prints it. A tokeniser passes when `decode(encode(line))` returns exactly the same code points for every line.
- **UN Arabic text**: the same exact check on every Arabic segment of `unpc_test2015`, reported separately for the segments that contain at least one diacritic.

Decoding uses the library's plain decode without clean-up of spaces (tiktoken: bytes decoded as strict UTF-8).

## 7. Cost

Prices are list prices in USD per million tokens, read from each vendor's official price page and listed with the page URL, the retrieval time (UTC) and the SHA-256 of the page as served (`config/prices.yaml`). No batch, cache, off-peak or regional discounts. When the page marks a price as promotional, the row carries a `price_note` and `promotional_through` (in version 0.1.1: `gpt-5.6-sol`, promotional price, at least through 21 Nov 2026). A price is shown only when the page names a model whose tokenizer is measured here, either through tiktoken's model table or because the page names an open-weight model whose tokenizer file is published. For those API models the index assumes the API uses the published tokenizer of the model version named on the page; `mapping_basis` in each row says how the model was matched to a measured tokenizer.

For each priced model: page cost = tokens per page × price ÷ 1,000,000, for the English page and for its Arabic translation, at the input price and at the output price. `extra_*_usd_per_1000_pages` is the difference for 1,000 pages. Cost is computed from the rounded tokens-per-page values in `results.csv`, so it can be recomputed from the released files.

## 8. What the index does not say

- Fewer tokens is lower cost and more text per context window. It is not a measure of model quality.
- The UN text is formal Modern Standard Arabic. Other registers give other ratios; the Tatoeba rows show one example.
- Per-word figures depend on the word definition; the parallel ratio does not.
- Prices change. Every cost row carries its retrieval time.
