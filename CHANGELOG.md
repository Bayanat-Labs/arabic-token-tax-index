# Changelog

## 0.1.1 (2026-10-30)

Corrections to the price table and wording; token counts are unchanged (run of 2026-10-16).

- Prices re-read on 2026-10-30 from the same official pages; all 7 list prices are unchanged. OpenAI's price page moved to https://developers.openai.com/api/docs/pricing and DeepSeek's is served at https://api-docs.deepseek.com/quick_start/pricing/.
- `gpt-5.6-sol`: the row is now marked "promotional price, at least through 21 Nov 2026" (new `price_note` and `promotional_through` fields) instead of being described as a standard rate.
- `deepseek-flash`: the DeepSeek page now names the model version DeepSeek-V4.1-Flash-1017; its published tokenizer.json is byte-identical to that of DeepSeek-V4.1-Flash, a checked equivalent of the measured DeepSeek file.
- OpenAI cl100k_base: the reason for showing no price was wrong. The OpenAI page lists gpt-4-0613 and gpt-3.5-turbo; the index price table has no row for them.
- Model lists: the OpenAI rows follow tiktoken's model-to-encoding table and were not count-checked; tables no longer label them "same token counts".
- `results/v0.1.1/` replaces `results/v0.1.0/`: same counts, with `prices.csv`, `costs.csv` and `prices_not_shown.csv` regenerated from the new `config/prices.yaml`.

## 0.1.0 (2026-10-16)

- First release of the harness (`arabic-token-tax`) and of the index files in `results/v0.1.0/`.
- 12 tokenisers measured on 5 slices: the United Nations Parallel Corpus 2015 test set (headline) and development set, and Tatoeba sentence pairs in Standard, Egyptian and Algerian Arabic.
- 7 list prices from 3 vendors, with cost per page.
- Specifications: `clean-v1`, `wordcount-v1`, `diacritics-probe-v1` (docs/METHOD.md).
