# Clarify: multilingual-rag-pipeline
Generated: 2026-04-08 | Spec: v1 DRAFT

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | S001 spec says create `backend/rag/lang_detect.py` with `detect_language()`. But this function **already exists** at `backend/rag/tokenizers/detection.py` (from cjk-tokenizer feature). Should S001 be **dropped** (reuse existing) or **replaced** with a thin re-export wrapper at `backend/rag/lang_detect.py`? | ❓ | lb_mui | |
| Q2 | `detection.py` L49: unsupported high-confidence lang falls back to `"en"` silently (`return "en"`). The spec says AC2 maps unsupported → "en" too — but A003/C009 says never hardcode "en". **Is the current `"en"` fallback for truly-foreign langs (e.g. French, German) acceptable, or should it also raise `LanguageDetectionError`?** | ❓ | lb_mui | |
| Q3 | Should `search()` accept an explicit `lang: str \| None = None` override parameter so the query-endpoint can pass a user-declared language (bypassing auto-detect)? | ❓ | lb_mui | |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q4 | Should `search()` fall back to dense-only retrieval when `LanguageDetectionError` is raised (e.g. short query), or hard-fail? | **Hard-fail** — propagate `LanguageDetectionError` to caller (consistent with P005 + document-ingestion precedent D12) |
| Q5 | `OllamaEmbedder` singleton: instantiate at module level in `query_processor.py` or inject as dependency? | **Module-level singleton** — consistent with how `OllamaEmbedder` is used in `embedder.py` (no DI framework in use) |
| Q6 | What is the `top_k` default for `search()`? | **10** — matches `retrieve()` default in `retriever.py` L120 |
| Q7 | Integration test: should `zh` (Chinese) also be included in S005 AC1 alongside ja/en/vi/ko? The spec says "≥1 per supported language (ja, en, vi, ko)" but omits zh, which is supported by the tokenizer. | **Include zh** — CONSTITUTION P003 says all supported languages treated equally; zh is in `_SUPPORTED` set |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q8 | Should `search.py` expose `__all__` with just `["search"]` to enforce the public interface explicitly? |
| Q9 | Should `RetrievedDocument.content` field be guaranteed non-None when returned from `search()` (i.e. assert or filter nulls)? Currently optional per dataclass. |

---

## Auto-answered from existing files

| Q | Source | Answer |
|---|--------|--------|
| A1 — Library: langdetect vs fasttext | `backend/rag/tokenizers/detection.py` L6 | **`langdetect`** confirmed — already used in cjk-tokenizer feature (`DetectorFactory.seed=0` for CI determinism) |
| A2 — `LanguageDetectionError` class | `backend/rag/tokenizers/exceptions.py` L9 | Already defined — import from `backend.rag.tokenizers.exceptions`, do NOT redefine |
| A3 — `TokenizerFactory.get()` interface | `backend/rag/tokenizers/factory.py` L16 | Accepts: "ja", "ko", "zh", "vi", "en". Raises `UnsupportedLanguageError` for anything else |
| A4 — Hybrid weights | `backend/rag/retriever.py` L14–15 | `RAG_DENSE_WEIGHT=0.7`, `RAG_BM25_WEIGHT=0.3` — env-configurable (C007 ✅) |
| A5 — `retrieve()` signature | `backend/rag/retriever.py` L119–128 | `retrieve(query_embedding, user_group_ids, top_k=10, *, session, bm25_query=None)` — `bm25_query` is optional (BM25-only skipped if None) |
| A6 — RBAC null = public | `backend/rag/retriever.py` L5 (Decision D01) | `user_group_id IS NULL` = public document — no change needed |
| A7 — `WhitespaceTokenizer` for "en" | `backend/rag/tokenizers/factory.py` L38–39 | "en" is handled by `WhitespaceTokenizer` via factory — `tokenize_query()` for non-CJK can just call `TokenizerFactory.get(lang)` uniformly |

---

## Spec Corrections Required (action before /plan)

These are factual errors in the spec discovered during clarification — **must fix before /plan**:

| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| SC1 | S001 entirely | `detect_language()` already exists at `backend/rag/tokenizers/detection.py`. Creating a new `lang_detect.py` would duplicate it. | **Pending Q1 answer.** Either drop S001 (reuse) or make it a thin import wrapper. |
| SC2 | S001 AC2 | "Maps unsupported codes → 'en' (default for all others)" — but current behavior is `return "en"` for unknown langs, which is arguably a silent A003 violation. | **Pending Q2 answer.** |
| SC3 | S002 AC3 | "Non-CJK langs use whitespace split" — actually `TokenizerFactory` already handles "en" via `WhitespaceTokenizer`. No need for special-case in `tokenize_query()`. | Update AC3: "Non-CJK langs delegate to `TokenizerFactory.get(lang)` — factory returns `WhitespaceTokenizer` for 'en'" |
| SC4 | S004 Solution Summary | Lists "Add `/v1/search` health-probe endpoint" but this is never mentioned in any story and conflicts with HARD R003 (no endpoints without auth). | **Remove** — not in any story AC, out of scope. |
