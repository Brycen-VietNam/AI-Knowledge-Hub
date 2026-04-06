# Clarify: cjk-tokenizer
Generated: 2026-04-06 | Spec: DRAFT | WARM: `.claude/memory/WARM/cjk-tokenizer.mem.md`

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|---|---|---|---|
| Q1 | langdetect confidence threshold: 0.85 đủ chưa cho short Asian queries (< 10 chars)? | **Minimum text length approach**: nếu `len(text) < 8 chars` → raise `LanguageDetectionError` ngay, không dùng confidence. Với text ≥ 8 chars dùng confidence ≥ 0.85. | lb_mui 2026-04-06 ✅ | — |
| Q2 | MeCab installation trên deployment environment: Docker image có sẵn MeCab + ipadic chưa? | **Chưa có** — cần thêm `apt-get install mecab libmecab-dev mecab-ipadic-utf8` vào Dockerfile. S001 phải include Dockerfile change. | lb_mui 2026-04-06 ✅ | — |

---

## SHOULD — Assume nếu không trả lời trước sprint start

| # | Question | Default assumption |
|---|---|---|
| Q3 | Japanese: surface forms hay base forms (dictionary form) cho BM25? "走っている" → `["走っ", "て", "いる"]` (surface) hay `["走る", "いる"]` (base)? | **Default: surface forms** — consistent với MeCab default output; base form needs extra MeCab config |
| Q4 | Chinese: simplified only, hay cần hỗ trợ traditional Chinese (zh-TW)? jieba supports both nhưng default dict là simplified. | **Default: simplified only** — traditional maps to `zh` same tokenizer; no separate handling |
| Q5 | underthesea `word_tokenize` hay `tokenize`? underthesea có 2 APIs với output khác nhau. | **Default: `word_tokenize`** — output là list of word strings, consistent với other tokenizers |
| Q6 | Korean: kiwipiepy returns `(form, tag, start, end)` tuples — filter by POS tag (noun/verb only) hay return all morphemes? | **Default: return all morphemes** (form only, drop tag/pos) — filtering is stopword concern, deferred to multilingual-rag-pipeline |
| Q7 | `detect_language()` scope: dùng cho cả query-time detection lẫn document-ingestion-time detection, hay chỉ query-time? | **Default: reusable cho cả hai** — same function, callers decide when to call |

---

## NICE — Won't block

| # | Question |
|---|---|
| Q8 | MeCab dictionary: ipadic (default) hay unidic? unidic có base form tốt hơn nhưng cần install riêng. |
| Q9 | jieba: normal mode hay search mode (`jieba.cut_for_search`)? Search mode cuts thêm fine-grained cho BM25. |
| Q10 | Có cần support `zh-TW` (Traditional Chinese) như một lang code riêng trong Factory, hay map về `zh`? |

---

## Auto-answered từ existing files

| # | Question | Source | Answer |
|---|---|---|---|
| A1 | Tokenizer library choices (MeCab/kiwipiepy/jieba/underthesea) | CONSTITUTION.md C005, C006 | Fixed — không thay đổi được |
| A2 | No Java runtime | CONSTITUTION.md C005 | "No Java runtime dependency allowed" — kiwipiepy replaces KoNLPy |
| A3 | Output format `list[str]` vs pre-joined string | /specify session D02, lb_mui 2026-04-06 | `list[str]` — caller formats for tsquery |
| A4 | Factory.get(lang) pattern vs single function | /specify session D01, lb_mui 2026-04-06 | Factory pattern — Option A decided |
| A5 | Detection failure → raise vs fallback | /specify session D03, lb_mui 2026-04-06 | Raise `LanguageDetectionError` — Option A decided |
| A6 | Input truncation at 512 chars | SECURITY.md S003 | "limit to 512 tokens before embedding" |
| A7 | Test coverage ≥ 80% | CONSTITUTION.md testing policy | Standard threshold for all new code |
| A8 | Thread safety requirement | FastAPI process model + ARCH.md A001 | Threading.Lock or equivalent required for singleton |
| A9 | Empty string → empty list (tokenizers) | /specify session AC8 | Agreed: no exception on empty input at tokenizer level |
| A10 | Whitespace tokenizer forbidden for CJK | HARD.md R005 | "WRONG: whitespace split on Japanese text" — hard rule |

---

## Summary
**BLOCKERs:** 2 → **RESOLVED ✅**
**SHOULD assumptions:** 5 (Q3–Q7) — safe defaults, proceed if unanswered
**NICE:** 3 (Q8–Q10) — non-blocking
**Auto-answered:** 10
**Gate status: PASS — ready for /checklist**
