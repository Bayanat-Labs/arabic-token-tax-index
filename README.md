# Arabic Token-Tax Index

How many more tokens does the same content take in Arabic than in English? This repository holds the harness (`arabic-token-tax`) and the index files for 12 LLM tokenisers: tokens per 1,000 words, the Arabic/English token ratio on parallel text with a 95% confidence interval, characters per token, a diacritics round trip, and the cost of a page at list prices. By **Bayanat Labs**.

**[Leaderboard on Hugging Face](https://huggingface.co/spaces/Bayanat-Labs/arabic-token-tax-index)** · **[Dataset with per-segment counts](https://huggingface.co/datasets/Bayanat-Labs/arabic-token-tax-index)** · [Method](docs/METHOD.md) · Version 0.1.0, run 2026-10-16

On the United Nations 2015 test set (3,990 Arabic–English sentence pairs from 731 UN documents), the median Arabic/English token ratio across the 12 tokenisers measured is **1.42**: the same content takes 1.42 times as many tokens in Arabic as in English. The ratio runs from 0.93 (ALLaM) to 3.35 (Falcon3). A ratio below 1 means Arabic took fewer tokens than English.

## Results: UN 2015 test set

| Tokeniser | Models (same token counts) | Arabic/English ratio (95% CI) | Tokens per 1,000 Arabic words | Tokens per 1,000 English words | Characters per token, Arabic | Vocabulary |
|---|---|---|---|---|---|---|
| ALLaM | ALLaM-7B-Instruct-preview | **0.93** (0.92–0.94) | 1,408 | 1,352 | 3.74 | 64,000 |
| Falcon-H1 | Falcon-H1-34B-Instruct | **1.04** (1.03–1.05) | 1,508 | 1,295 | 3.49 | 261,120 |
| Falcon-H1R | Falcon-H1R-7B | **1.12** (1.11–1.13) | 1,677 | 1,336 | 3.14 | 130,048 |
| Mistral Tekken | Mistral-Small-4-119B-2603, Mistral-Medium-3.5-128B, Mistral-Large-3-675B-Instruct-2512, Ministral-3-8B-Instruct-2512, Mistral-Nemo-Instruct-2407 | **1.24** (1.23–1.25) | 1,808 | 1,300 | 2.91 | 131,072 |
| Qwen3.5 / 3.6 / 3.8 | Qwen3.5-397B-A17B, Qwen3.5-27B, Qwen3.6-27B, Qwen3.6-35B-A3B, Qwen3.8-27B, Qwen3.8-2.4T-A95B, Qwen3.8-Flash-Next | **1.26** (1.25–1.27) | 1,813 | 1,285 | 2.90 | 248,070 |
| OpenAI o200k_base | gpt-5 family (gpt-5*), gpt-4.5, gpt-4.1, gpt-4o, o1, o3, o4-mini, gpt-oss-120b, gpt-oss-20b | **1.36** (1.35–1.37) | 1,884 | 1,232 | 2.79 | 200,019 |
| Fanar-1 | Fanar-1-9B-Instruct | **1.47** (1.46–1.49) | 2,145 | 1,298 | 2.45 | 128,256 |
| Gemma 4 / Fanar-2 | gemma-4-31B-it, gemma-4-26B-A4B-it, gemma-4-E4B-it, Fanar-2-27B-Instruct | **1.48** (1.47–1.49) | 2,105 | 1,267 | 2.50 | 262,144 |
| Qwen3 | Qwen3-235B-A22B, Qwen3-8B, Qwen3-Next-80B-A3B-Instruct | **1.57** (1.56–1.58) | 2,268 | 1,288 | 2.32 | 151,669 |
| DeepSeek V3 / V4 | DeepSeek-V4-Pro-0813, DeepSeek-V4.1-Flash, DeepSeek-V4-Pro, DeepSeek-V4-Flash, DeepSeek-V3.2, DeepSeek-V3.1, DeepSeek-V3 | **1.65** (1.64–1.66) | 2,278 | 1,231 | 2.31 | 129,280 |
| OpenAI cl100k_base | gpt-4, gpt-3.5-turbo | **3.08** (3.05–3.10) | 4,275 | 1,240 | 1.23 | 100,277 |
| Falcon3 | Falcon3-7B-Instruct | **3.35** (3.32–3.39) | 4,788 | 1,274 | 1.10 | 131,072 |

The ratio is total Arabic tokens ÷ total English tokens over the same 3,990 sentence pairs; the 95% interval comes from 10,000 bootstrap resamples of the 731 UN documents. "Same token counts" lists models whose own tokenizer files were checked to give the same count as the measured file on every segment of every slice. Fewer tokens means lower cost and more text per context window; it is not a measure of model quality.

Every one of the 12 tokenisers gives back exactly the same code points after encoding and decoding, both for the synthetic diacritics probe (22 lines, 508 marked letters) and for all 3,990 Arabic UN segments, 987 of which carry at least one diacritic.

## Other text

Arabic/English token ratio by slice. The Tatoeba slices are short, conversational sentences, so compare the Egyptian and Algerian columns with the Tatoeba Standard Arabic column rather than with the UN columns.

| Tokeniser | UN 2015 test set | UN 2015 development set | Tatoeba, Standard Arabic | Tatoeba, Egyptian Arabic | Tatoeba, Algerian Arabic |
|---|---|---|---|---|---|
| ALLaM | 0.93 | 0.95 | 0.89 | 0.87 | 1.24 |
| Falcon-H1 | 1.04 | 1.06 | 1.05 | 1.07 | 1.37 |
| Falcon-H1R | 1.12 | 1.14 | 1.13 | 1.15 | 1.44 |
| Mistral Tekken | 1.24 | 1.25 | 1.16 | 1.20 | 1.52 |
| Qwen3.5 / 3.6 / 3.8 | 1.26 | 1.28 | 1.23 | 1.25 | 1.54 |
| OpenAI o200k_base | 1.36 | 1.38 | 1.30 | 1.32 | 1.64 |
| Fanar-1 | 1.47 | 1.49 | 1.31 | 1.25 | 1.55 |
| Gemma 4 / Fanar-2 | 1.48 | 1.49 | 1.30 | 1.19 | 1.49 |
| Qwen3 | 1.57 | 1.59 | 1.42 | 1.42 | 1.78 |
| DeepSeek V3 / V4 | 1.65 | 1.66 | 1.45 | 1.41 | 1.71 |
| OpenAI cl100k_base | 3.08 | 3.11 | 2.47 | 2.30 | 2.62 |
| Falcon3 | 3.35 | 3.39 | 2.68 | 2.40 | 2.67 |
| *Median* | *1.42* | *1.43* | *1.30* | *1.25* | *1.54* |
| *pairs* | *3,990* | *3,986* | *46,480* | *1,314* | *1,729* |

## Cost per page

A page is the content of 1,000 English words; on the UN test set its Arabic translation has about 892 Arabic words. Page cost = tokens for the page × list price ÷ 1,000,000, at the input price (sending the page to a model) and at the output price (a model writing it). Standard rates in USD with no batch, cache or off-peak discounts, read from the official price pages on 2026-10-16 (UTC). For the DeepSeek and Qwen rows the index assumes that the API serves the published tokenizer of the model named on the price page.

| Model | Tokeniser | Price per 1M tokens, input / output | English page, input | Arabic page, input | English page, output | Arabic page, output | Extra per 1,000 Arabic pages, input / output |
|---|---|---|---|---|---|---|---|
| OpenAI `gpt-5.6-sol` | OpenAI o200k_base | $4.00 / $20.00 | $0.00493 | $0.00672 | $0.02464 | $0.03362 | $1.79 / $8.97 |
| OpenAI `gpt-5.3-codex` | OpenAI o200k_base | $1.75 / $14.00 | $0.00216 | $0.00294 | $0.01725 | $0.02353 | $0.79 / $6.28 |
| DeepSeek `deepseek-v4-pro` | DeepSeek V3 / V4 | $1.32 / $3.96 | $0.00162 | $0.00268 | $0.00487 | $0.00805 | $1.06 / $3.17 |
| DeepSeek `deepseek-flash` | DeepSeek V3 / V4 | $0.30 / $1.20 | $0.00037 | $0.00061 | $0.00148 | $0.00244 | $0.24 / $0.96 |
| Alibaba Cloud `qwen3.5-397b-a17b` | Qwen3.5 / 3.6 / 3.8 | $0.60 / $3.60 | $0.00077 | $0.00097 | $0.00463 | $0.00582 | $0.20 / $1.20 |
| Alibaba Cloud `qwen3.8-27b` | Qwen3.5 / 3.6 / 3.8 | $0.50 / $3.00 | $0.00064 | $0.00081 | $0.00386 | $0.00485 | $0.17 / $1.00 |
| Alibaba Cloud `qwen3.8-2.4t-a95b` | Qwen3.5 / 3.6 / 3.8 | $2.00 / $6.00 | $0.00257 | $0.00324 | $0.00771 | $0.00971 | $0.66 / $1.99 |

Price not shown:

- **OpenAI cl100k_base**: gpt-4 and gpt-3.5-turbo are not listed on the official price page on the retrieval date.
- **Qwen3**: The Qwen3 open-weight models measured here (Qwen3-235B-A22B, Qwen3-8B, Qwen3-Next-80B-A3B-Instruct) are not listed on the official price page on the retrieval date.
- **Mistral Tekken**: The official pricing page gives no per-model API price table in its archived text; its one example names "Mistral Large" without a version.
- **Gemma 4 / Fanar-2**: The official Gemini API price page lists Gemma 4 on the free tier only (paid tier: not available).
- **Falcon3**: No official per-token price page was archived for this release.
- **Falcon-H1**: No official per-token price page was archived for this release.
- **Falcon-H1R**: No official per-token price page was archived for this release.
- **ALLaM**: No official per-token price page was archived for this release.
- **Fanar-1**: No official per-token price page was archived for this release.

## Not measured in this version

- **Claude** (Anthropic; Claude models): Token counts for these models come from the vendor's API with an API key; no keyed API was used for this release.
- **Gemini** (Google; Gemini models): Token counts for these models come from the vendor's API with an API key; no keyed API was used for this release.
- **GPT-6 models** (OpenAI; gpt-6-astra, gpt-6.1-sol, gpt-6-luna): No encoding is listed for these model names in tiktoken 0.14.0.
- **Llama 3.3 and Llama 4** (Meta; Llama-3.3-70B-Instruct, Llama-4-Maverick-17B-128E-Instruct): The tokenizer files are in gated repositories that require accepting the model licence.
- **Gemma 3** (Google; gemma-3-27b-it): The tokenizer files are in a gated repository that requires accepting the model licence.
- **Command A and Command R7B Arabic** (Cohere; c4ai-command-a-03-2025, c4ai-command-r7b-arabic-02-2025): The tokenizer files are in gated repositories that require an access request.
- **Jais** (Inception; jais-family-30b-16k-chat, jais-adapted-70b-chat): The tokenizer files are in gated repositories that require an access request.

## Install

```bash
pip install "git+https://github.com/Bayanat-Labs/arabic-token-tax-index@v0.1.0"
```

Python 3.10 or later. `pip install arabic-token-tax-index` will work once the package is published. Tokenizer files are downloaded from Hugging Face on first use (tokenizer files only, at pinned revisions; no model weights).

Count the tokens of your own text with every tokeniser in the index:

```bash
arabic-token-tax count "تقرير الأمين العام عن أعمال المنظمة"
arabic-token-tax words "تقرير الأمين العام"     # the wordcount-v1 words
```

## Reproduce this release

```bash
git clone https://github.com/Bayanat-Labs/arabic-token-tax-index.git
cd arabic-token-tax-index
git checkout v0.1.0
python -m venv .venv && . .venv/bin/activate
pip install .
arabic-token-tax fetch --data data --tatoeba-ids results/v0.1.0/tatoeba_ids.txt
arabic-token-tax run --config config/tokenisers.yaml --prices config/prices.yaml --data data --out out --run-date 2026-10-16
arabic-token-tax compare out results/v0.1.0
```

`fetch` downloads the UN archive (checked against a pinned SHA-256) and the Tatoeba exports; `--tatoeba-ids` keeps the sentence pairs used in this release. `compare` checks that every token and word count matches. Tatoeba sentences can be edited after release, so a few Tatoeba counts may differ; the UN counts must match exactly.

## Files

| Path | Contents |
|---|---|
| `config/tokenisers.yaml` | the tokenisers: route, pinned revision, models, and the equivalent tokenizer files checked at run time; the list of tokenisers not measured |
| `config/prices.yaml` | list prices with source URL, retrieval time and the SHA-256 of the page as served; tokenisers without a price and why |
| `results/v0.1.0/results.csv` | one row per tokeniser and slice (also `results.json`) |
| `results/v0.1.0/tokenisers.csv` | versions, file hashes, vocabulary sizes, round-trip results and equivalence checks (also `tokenisers.json`) |
| `results/v0.1.0/costs.csv`, `prices.csv`, `prices_not_shown.csv` | cost per page and the prices used |
| `results/v0.1.0/slices.csv` | sources, licences, pairs kept and dropped by reason |
| `results/v0.1.0/not_measured.csv` | tokenisers not measured and why |
| `results/v0.1.0/summary.json` | headline numbers per slice |
| `results/v0.1.0/tatoeba_ids.txt` | Tatoeba sentence id pairs used |
| `docs/METHOD.md` | the full method: cleaning, word count, measures, interval, round trips, cost |

Per-segment token counts (and the cleaned UN text) are in the [dataset](https://huggingface.co/datasets/Bayanat-Labs/arabic-token-tax-index).

## Method in brief

- Each segment is encoded on its own with no special tokens: tiktoken `encode_ordinary`, tokenizers `add_special_tokens=False`, sentencepiece without BOS or EOS.
- Text is cleaned with `clean-v1` (NFC; control and format characters removed except ZWNJ; spaces collapsed); pairs with an untranslated or misaligned side are dropped (3,990 of 4,000 UN test pairs kept).
- Words follow `wordcount-v1`: runs of letters, marks and digits. Arabic clitics are not split, so Arabic has fewer, longer words than English; the parallel ratio does not depend on this choice.
- 95% intervals: 10,000 bootstrap resamples of UN documents (Tatoeba: sentences), seed 20261013, the same resamples for every tokeniser.

## Limitations

- The headline slice is formal UN Modern Standard Arabic. Other registers give other ratios.
- Tatoeba rows rest on short sentences translated by volunteers; the Egyptian and Algerian slices have 1,314 and 1,729 pairs.
- API models may add tokens for message formatting; the counts here are for the text alone.
- Prices change; every price row carries its retrieval time.

## Licence

Code: Apache-2.0 (`LICENSE`). Index files, configuration and documentation: CC BY 4.0 (`LICENSE-data`). Source text keeps its own terms: the UN Parallel Corpus is made available by the United Nations, which must be credited as the source; Tatoeba sentences are CC BY 2.0 FR. See `NOTICE`.

## Cite

```
Bayanat Labs (2026). Arabic Token-Tax Index, version 0.1.0 (run 2026-10-16). https://huggingface.co/datasets/Bayanat-Labs/arabic-token-tax-index. CC BY 4.0.
```

`CITATION.cff` has the same in machine-readable form.

## Contact

Corrections, takedown requests and requests for new tokenisers: hello@bayanatlabs.com.

## بالعربية

*The Arabic text has not yet been reviewed by a native Arabic writer; the English governs.*

<div dir="rtl" lang="ar">

**مؤشر ضريبة الترميز العربية** يقيس كم رمزًا إضافيًا يحتاجه المحتوى نفسه بالعربية مقارنةً بالإنجليزية لدى 12 مُرمِّزًا من مُرمِّزات النماذج اللغوية الكبيرة، على نص عربي-إنجليزي متوازٍ، مع فترات ثقة 95% وتكلفة الصفحة بأسعار القائمة.

على مجموعة اختبار الأمم المتحدة لعام 2015 (3,990 زوجًا من الجمل العربية والإنجليزية من 731 وثيقة)، يبلغ وسيط نسبة الرموز العربية إلى الإنجليزية عبر المُرمِّزات الـ12 المقيسة **1.42**: أي أن المحتوى نفسه يحتاج بالعربية إلى 1.42 ضعف رموزه بالإنجليزية. وتتراوح النسبة بين 0.93 (ALLaM) و3.35 (Falcon3). النسبة الأقل من 1 تعني أن العربية احتاجت رموزًا أقل من الإنجليزية.

أعاد كل واحد من المُرمِّزات الـ12 نقاط الترميز نفسها بالضبط بعد الترميز وفكّه، في عيّنة التشكيل الاصطناعية (22 سطرًا، وعدد الحروف المشكولة فيها 508) وفي المقاطع العربية الـ3,990 من نص الأمم المتحدة، ومنها 987 مقطعًا فيه علامة تشكيل واحدة على الأقل.

النتائج الكاملة في الجداول أعلاه، والمنهجية في `docs/METHOD.md`. الشيفرة بترخيص Apache-2.0، وملفات المؤشر ووثائقه بترخيص CC BY 4.0. للتصحيحات: hello@bayanatlabs.com.

</div>
