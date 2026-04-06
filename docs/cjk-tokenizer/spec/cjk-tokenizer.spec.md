# Spec: cjk-tokenizer
Created: 2026-04-06 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary

| Field | Value |
|-------|-------|
| Epic | rag-pipeline |
| Priority | P0 |
| Story count | 4 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 → S003 → S004 |
| Parallel-safe stories | S003 ∥ S004 (after S002) |
| Blocking specs | None |
| Blocked by | db-schema-embeddings ✅, auth-api-key-oidc ✅ |
| Agents needed | rag-agent |

### Problem Statement
BM25 search in `_bm25_search()` currently uses PostgreSQL `simple` dictionary — whitespace tokenization — which is a hard violation of C005/R005 for Japanese, Korean, Chinese, and Vietnamese text.
The RAG pipeline needs a language-aware tokenizer layer before BM25 indexing and query construction.

### Solution Summary
- `TokenizerFactory.get(lang)` returns a language-specific tokenizer instance (lazy-loaded)
- Per-language backends: MeCab (ja), kiwipiepy (ko), jieba (zh), underthesea (vi), whitespace (en/fallback-explicit)
- All tokenizers output `list[str]` — callers format for tsquery/BM25 index themselves
- Language auto-detection via `langdetect` at tokenization entry; raises `LanguageDetectionError` on failure
- Zero Java runtime dependency; all libraries are OSS Python packages

### Out of Scope
- BM25 indexer itself (`bm25_indexer.py`) — that is `document-ingestion` scope
- Dense embedding — separate pipeline (`multilingual-rag-pipeline`)
- Query-time tsquery formatting — caller responsibility
- Stopword filtering — deferred to `multilingual-rag-pipeline`

---

## LAYER 2 — Story Detail

### S001: Per-language tokenizer backends

**Role / Want / Value**
- As a: rag-agent developer
- I want: individual tokenizer classes for ja/ko/zh/vi/en
- So that: each language uses the correct OSS library with no cross-language coupling

**Acceptance Criteria**
- [ ] AC1: `JapaneseTokenizer.tokenize(text: str) -> list[str]` uses MeCab (ipadic); returns surface forms
- [ ] AC2: `KoreanTokenizer.tokenize(text: str) -> list[str]` uses kiwipiepy (MIT); returns morpheme forms
- [ ] AC3: `ChineseTokenizer.tokenize(text: str) -> list[str]` uses jieba; returns cut tokens
- [ ] AC4: `VietnameseTokenizer.tokenize(text: str) -> list[str]` uses underthesea `word_tokenize`
- [ ] AC5: `WhitespaceTokenizer.tokenize(text: str) -> list[str]` splits on whitespace; used for `en` and explicitly-selected fallback only
- [ ] AC6: No Java runtime dependency — kiwipiepy replaces KoNLPy (backlog 2026-03-18 decision)
- [ ] AC7: All tokenizer classes implement `BaseTokenizer` abstract interface with single `tokenize()` method
- [ ] AC8: Empty string input returns empty list (no exception)

**Auth Requirement**
- N/A — internal library, no HTTP endpoint

**Non-functional**
- No latency SLA at this story level (covered in S004)
- CJK support: ja, ko, zh, vi
- Audit log: not required

**Implementation notes**
- Location: `backend/rag/tokenizers/` — new subdirectory
- `BaseTokenizer` ABC in `backend/rag/tokenizers/base.py`
- One file per language: `japanese.py`, `korean.py`, `chinese.py`, `vietnamese.py`, `whitespace.py`

---

### S002: TokenizerFactory with lazy loading

**Role / Want / Value**
- As a: rag-agent caller (`_bm25_search`, `bm25_indexer`)
- I want: `TokenizerFactory.get(lang: str) -> BaseTokenizer`
- So that: I get the right tokenizer without knowing implementation details, and heavy libraries load only when first used

**Acceptance Criteria**
- [ ] AC1: `TokenizerFactory.get("ja")` returns `JapaneseTokenizer` instance (singleton per process)
- [ ] AC2: `TokenizerFactory.get("ko")` returns `KoreanTokenizer` instance
- [ ] AC3: `TokenizerFactory.get("zh")` returns `ChineseTokenizer` instance
- [ ] AC4: `TokenizerFactory.get("vi")` returns `VietnameseTokenizer` instance
- [ ] AC5: `TokenizerFactory.get("en")` returns `WhitespaceTokenizer` instance
- [ ] AC6: `TokenizerFactory.get("unknown_lang")` raises `UnsupportedLanguageError`
- [ ] AC7: Tokenizer instances are lazy-loaded — library import happens on first `get()` call, not at module import
- [ ] AC8: Factory is thread-safe (singleton guard with lock or module-level dict)

**Non-functional**
- First-call latency acceptable (library init); subsequent calls near-zero
- CJK support: ja, ko, zh, vi
- Audit log: not required

**Implementation notes**
- Location: `backend/rag/tokenizers/factory.py`
- `UnsupportedLanguageError` defined in `backend/rag/tokenizers/exceptions.py`
- Use `_registry: dict[str, BaseTokenizer]` with `threading.Lock` for thread safety

---

### S003: Language auto-detection at tokenization entry

**Role / Want / Value**
- As a: BM25 query builder
- I want: `detect_language(text: str) -> str` that returns ISO 639-1 code
- So that: tokenizer is selected automatically without hardcoding `lang="en"` (C009)

**Acceptance Criteria**
- [ ] AC1: `detect_language(text)` uses `langdetect` library; returns ISO 639-1 code (e.g. `"ja"`, `"vi"`)
- [ ] AC2: Returns one of the supported codes: `"ja"`, `"ko"`, `"zh"`, `"vi"`, `"en"` — maps unsupported detected langs to `"en"` only when detection confidence ≥ 0.85
- [ ] AC3: If `len(text) < 8` → raises `LanguageDetectionError` immediately (no detection attempted). If `langdetect` raises `LangDetectException` or confidence < 0.85 → raises `LanguageDetectionError` with message including input text length
- [ ] AC4: `LanguageDetectionError` is a distinct exception class in `backend/rag/tokenizers/exceptions.py`
- [ ] AC5: Input text longer than 512 chars is truncated to 512 before detection (aligns with S003 input sanitization)
- [ ] AC6: Empty string input raises `LanguageDetectionError` (not silent empty result)

> **Decision** (lb_mui 2026-04-06): text < 8 chars → raise immediately; text ≥ 8 chars → confidence ≥ 0.85 required.

**Non-functional**
- Detection call < 50ms p95 for inputs ≤ 512 chars
- Audit log: not required

**Implementation notes**
- Location: `backend/rag/tokenizers/detection.py`
- `LanguageDetectionError` in `backend/rag/tokenizers/exceptions.py`

---

### S004: Tokenizer tests — unit + performance

**Role / Want / Value**
- As a: developer
- I want: full test coverage for all tokenizer paths
- So that: CJK tokenization regressions are caught before merge (CONSTITUTION testing policy)

**Acceptance Criteria**
- [ ] AC1: Unit tests for each tokenizer backend with ≥2 golden examples per language (ja/ko/zh/vi/en)
- [ ] AC2: `TokenizerFactory` unit tests cover all 5 supported langs + `UnsupportedLanguageError` case
- [ ] AC3: `detect_language()` tests cover: high-confidence detection, low-confidence → error, `LangDetectException` → error, empty string → error
- [ ] AC4: Whitespace tokenizer must NOT be used for ja/ko/zh/vi inputs — regression test asserts this
- [ ] AC5: Test coverage ≥ 80% for all files in `backend/rag/tokenizers/`
- [ ] AC6: Performance test: `tokenize()` for a 200-char Japanese/Korean/Chinese/Vietnamese text < 200ms each

**Non-functional**
- Tests run in CI without network access (all libs installed locally)
- Audit log: not required

**Implementation notes**
- Location: `tests/rag/test_tokenizers.py`
- Golden examples should include: mixed CJK+ASCII, short query (3 chars), long sentence (150+ chars)
- Use `pytest.mark.performance` for AC6 timing test

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: MeCab for Japanese | Constitution | CONSTITUTION.md C005 | "MeCab (ja) ... no Java runtime" | 2026-03-18 |
| AC2: kiwipiepy for Korean | Constitution + Backlog | CONSTITUTION.md C005 + backlog.md license decision | kiwipiepy (MIT) replaces KoNLPy to avoid Java | 2026-03-18 |
| AC3: jieba for Chinese | Constitution | CONSTITUTION.md C005 | "jieba (zh)" | 2026-03-18 |
| AC4: underthesea for Vietnamese | Constitution | CONSTITUTION.md C006 | "underthesea tokenizer before BM25 indexing" | 2026-03-18 |
| AC5: WhitespaceTokenizer for en | Business logic | HARD.md R005 + conversation 2026-04-06 | Whitespace only for en; forbidden for CJK | 2026-04-06 |
| AC6: No Java runtime | Constitution | CONSTITUTION.md C005 | "No Java runtime dependency allowed" | 2026-03-18 |
| AC7: BaseTokenizer ABC | Conversation | lb_mui decision 2026-04-06 | Option A — Factory.get(lang) pattern agreed | 2026-04-06 |
| AC8: Empty string → empty list | Business logic | Fail-safe convention | Silent empty is safer than exception for empty input | 2026-04-06 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1–AC5: Factory lang mapping | Conversation | lb_mui decision 2026-04-06 | Option A — TokenizerFactory.get(lang) | 2026-04-06 |
| AC6: UnsupportedLanguageError | Business logic | CONSTITUTION P005 — fail fast | Unknown lang must not silently fall back | 2026-04-06 |
| AC7: Lazy loading | Business logic | PERF.md — avoid startup cost for unused libs | MeCab/kiwipiepy init is expensive | 2026-04-06 |
| AC8: Thread safety | Business logic | FastAPI async workers share process | Singleton dict without lock = race condition risk | 2026-04-06 |

### S003 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: langdetect library | Existing behavior | retriever.py uses langdetect pattern | Consistent with existing detection approach | 2026-04-06 |
| AC2–AC3: Confidence threshold 0.85 | Conversation | lb_mui decision 2026-04-06 | Option A — raise LanguageDetectionError on failure | 2026-04-06 |
| AC4: LanguageDetectionError | Constitution | CONSTITUTION P005 — fail fast, fail visibly | Distinct exception for observability | 2026-04-06 |
| AC5: 512 char truncation | Security rule | SECURITY.md S003 | "limit to 512 tokens before embedding" | 2026-03-18 |
| AC6: Empty string → error | Conversation | lb_mui decision 2026-04-06 | Option A — raise error, not silent | 2026-04-06 |

### S004 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1–AC3: Golden test examples | Constitution | CONSTITUTION.md testing policy | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |
| AC4: Whitespace not for CJK | Hard rule | HARD.md R005 | "whitespace split on Japanese text" is WRONG | 2026-03-18 |
| AC5: ≥80% coverage | Constitution | CONSTITUTION.md testing policy | Standard coverage threshold | 2026-03-18 |
| AC6: Performance test <200ms | Business logic | PERF.md P001 — latency SLA concern | Tokenizer must not dominate query budget | 2026-04-06 |
