# Spec: multilingual-rag-pipeline
Created: 2026-04-08 | Author: Claude Code | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | rag |
| Priority | P0 |
| Story count | 4 |
| Token budget est. | ~4k |
| Critical path | S002 → S003 → S004 → S005 |
| Parallel-safe stories | S002 ∥ S003 (query tokenization + query embedding are independent) |
| Blocking specs | — |
| Blocked by | document-ingestion ✅, cjk-tokenizer ✅, llm-provider ✅, rbac-document-filter ✅ |
| Agents needed | rag-agent, db-agent (read-only) |

### Problem Statement
The retriever (`backend/rag/retriever.py`) and BM25 indexer exist but operate on raw query text with no language detection or language-aware tokenization at query time. The multilingual-rag-pipeline must wire language detection → CJK-aware query tokenization → hybrid retrieval into a single cohesive `search()` service that the query-endpoint can call.

### Solution Summary
- Reuse `detect_language()` from `backend.rag.tokenizers.detection` (cjk-tokenizer feature) — no new file
- Tokenize query using `TokenizerFactory` (all langs including "en" via WhitespaceTokenizer) before BM25 search
- Embed query using `OllamaEmbedder` and pass to existing `retrieve()` hybrid search
- Expose a single `search(query, user_group_ids, session)` function as the rag-agent's public interface

> **Decision D1**: S001 dropped — `detect_language()` already exists at `backend/rag/tokenizers/detection.py` (cjk-tokenizer). `search.py` imports directly from there.
> **Decision D2**: `search()` returns `list[RetrievedDocument]` — the same dataclass from `retriever.py`. The query-endpoint maps this to its response schema.

### Out of Scope
- Answer generation (handled by `query-endpoint` via `generator.py`)
- Conflict detection between retrieved chunks (separate `conflict-detection` feature)
- Re-ranking beyond current weighted hybrid merge
- Query expansion / synonym handling
- Caching of query embeddings

---

## LAYER 2 — Story Detail

---

### S002: Query Tokenization for BM25

**Role / Want / Value**
- As a: rag-agent
- I want: to tokenize a query string using the correct language-aware tokenizer
- So that: BM25 query passed to `_bm25_search()` matches the tokenized FTS index built by `bm25_indexer.tokenize_for_fts()`

**Acceptance Criteria**
- [ ] AC1: `tokenize_query(text: str, lang: str) -> str` returns space-separated token string (same format as `tokenize_for_fts()`)
- [ ] AC2: All langs (including "en") delegate to `TokenizerFactory.get(lang).tokenize()` — factory returns `WhitespaceTokenizer` for "en", CJK-aware tokenizer for ja/ko/zh/vi (R005 compliant)
- [ ] AC3: `UnsupportedLanguageError` from factory is NOT swallowed — propagates to caller
- [ ] AC4: Function lives in `backend/rag/query_processor.py`
- [ ] AC5: Unit-tested: ja, vi, en, and unknown lang each exercised

**Auth Requirement**
- [ ] Not applicable (internal module)

**Non-functional**
- Latency: < 50ms per call (tokenizer in-process)
- Audit log: not required
- CJK support: ja / ko / zh / vi

**Implementation notes**
- Use `TokenizerFactory.get(lang).tokenize()` for ALL langs — no special-casing needed (factory handles "en" → WhitespaceTokenizer)
- `tokenize_query()` is symmetric with `tokenize_for_fts()` — same logic, different caller context

---

### S003: Query Embedding

**Role / Want / Value**
- As a: rag-agent
- I want: to embed an incoming query string into a dense vector
- So that: the vector can be passed to `_dense_search()` in the retriever

**Acceptance Criteria**
- [ ] AC1: `embed_query(text: str) -> list[float]` returns a vector via `OllamaEmbedder._embed_one()`
- [ ] AC2: Uses `OllamaEmbedder` from `backend/rag/embedder.py` — no new embedding client created
- [ ] AC3: `EmbedderError` propagates to caller — no silent fallback
- [ ] AC4: Function lives in `backend/rag/query_processor.py` (same file as S002)
- [ ] AC5: Unit-tested with a mocked `OllamaEmbedder._embed_one` returning a fixed vector

**Auth Requirement**
- [ ] Not applicable (internal module)

**Non-functional**
- Latency: < 500ms p95 (network call to Ollama)
- Audit log: not required
- CJK support: not applicable (embedder handles all langs via multilingual-e5-large)

**Implementation notes**
- Instantiate `OllamaEmbedder()` at module level or accept as dependency — prefer module-level singleton for simplicity
- CONSTITUTION C012: no per-document loop (not applicable here — single query embed is fine)

---

### S004: Unified `search()` Service Function

**Role / Want / Value**
- As a: api-agent (query-endpoint)
- I want: a single `search(query, user_group_ids, session)` async function
- So that: the query-endpoint never touches lang detection, tokenization, or retriever internals directly (A001, A002)

**Acceptance Criteria**
- [ ] AC1: `search(query: str, user_group_ids: list[int], session, top_k: int = 10, lang: str | None = None) -> list[RetrievedDocument]` is importable from `backend/rag/search.py`
- [ ] AC2: If `lang` is None, calls `detect_language(query)` — if `lang` is provided, skips detection and uses it directly
- [ ] AC3: Internally calls (detect →) `tokenize_query()` → `embed_query()` → `retrieve()` in that order
- [ ] AC4: `LanguageDetectionError` propagates to caller when `lang=None` and detection fails (no silent swallow)
- [ ] AC5: `QueryTimeoutError` from `retrieve()` propagates to caller unchanged
- [ ] AC6: `EmbedderError` propagates to caller unchanged
- [ ] AC7: RBAC filter (`user_group_ids`) is passed through to `retrieve()` unchanged — never modified by `search()`
- [ ] AC8: Unit-tested: lang=None path (auto-detect), lang="ja" path (override), and error propagation each covered
- [ ] AC9: Integration test: `search()` called against a real DB session returns ranked results (Docker-based)

**API Contract** _(internal function — no HTTP boundary)_
```
search(
    query: str,                    # raw user query, any language
    user_group_ids: list[int],     # from auth token — enforced by caller
    session: AsyncSession,         # injected
    top_k: int = 10,
    lang: str | None = None,       # override auto-detect; None = auto
) -> list[RetrievedDocument]       # ranked by hybrid score
```

**RAG Behavior**
- Retrieval: hybrid (dense + BM25)
- RBAC: user_group_ids passed to retrieve() unchanged — enforced at DB layer (C001)
- Languages: ja / en / vi / ko / zh (any detected or caller-specified lang)
- Fallback: `LanguageDetectionError` → propagate when lang=None and detection fails

**Auth Requirement**
- [ ] Not applicable (internal service — auth enforced at API boundary by query-endpoint)

**Non-functional**
- Latency: contributes to overall /v1/query p95 < 2000ms (R007 / P001). search() budget ≤ 1500ms.
- Audit log: not required (query-endpoint writes audit log — R006)
- CJK support: ja / zh / vi / ko

**Implementation notes**
- New file: `backend/rag/search.py`
- Do NOT import from `backend/api/` — A002 dependency direction
- `retrieve()` already has `asyncio.wait_for(1.8s)` — search() does not add a second timeout wrapper
- When `lang` is provided by caller, validate it is in `_SUPPORTED` set — raise `UnsupportedLanguageError` if not

---

### S005: RAG Pipeline Smoke Test & Integration Validation

**Role / Want / Value**
- As a: developer / CI
- I want: a deterministic integration test that runs the full search() pipeline against a real PostgreSQL+pgvector instance
- So that: regressions in lang detection → tokenization → retrieval are caught before merge

**Acceptance Criteria**
- [ ] AC1: Integration test seeds ≥1 document per supported language (ja, en, vi, ko) into test DB
- [ ] AC2: `search()` called with a matching query returns ≥1 result for each language
- [ ] AC3: Test verifies RBAC: query with `user_group_ids=[]` returns only public documents
- [ ] AC4: Test verifies `LanguageDetectionError` is raised for a gibberish/empty query (lang=None path)
- [ ] AC5: Test verifies explicit `lang="ja"` override skips auto-detect and returns correct results
- [ ] AC6: All tests pass in Docker (pytest with real DB, no mocks for integration suite)
- [ ] AC7: Unit test coverage for `query_processor.py`, `search.py` ≥ 80%

**Auth Requirement**
- [ ] Not applicable (test-only)

**Non-functional**
- Latency: integration test must complete < 60s per language
- Audit log: not required in test environment
- CJK support: ja / ko / zh / vi all exercised

**Implementation notes**
- Reuse Docker test infra from `document-ingestion` and `cjk-tokenizer` test suites
- Seed via `insert_embeddings()` + `update_fts()` from existing modules — no new test fixtures needed beyond data

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Business logic | CONSTITUTION.md C009 | "Query language must be auto-detected — never hardcode lang='en' as fallback" | 2026-03-18 |
| AC2 | Existing behavior | `backend/rag/bm25_indexer.py` L19 | `_CJK_LANGS = {"ja", "ko", "zh", "vi"}` — same language set | 2026-04-08 |
| AC3 | Existing behavior | document-ingestion archive D12 | LanguageDetectionError propagates (A003 compliant) — set precedent in ingestion | 2026-04-08 |
| AC4 | Business logic | CONSTITUTION.md P003 | "Multilingual by design. Japanese, English, Vietnamese, Korean treated equally." | 2026-03-18 |
| AC5 | Business logic | CLAUDE.md directory map | `backend/rag/` — rag-agent scope | 2026-04-08 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Existing behavior | `backend/rag/bm25_indexer.py` `tokenize_for_fts()` | Symmetric function already written for ingestion path | 2026-04-08 |
| AC2 | Business logic | CONSTITUTION.md C005/C006 | CJK tokenizer requirement: MeCab(ja), kiwipiepy(ko), jieba(zh), underthesea(vi) | 2026-03-18 |
| AC3 | Business logic | CONSTITUTION.md C005 | "Whitespace split is forbidden" for CJK | 2026-03-18 |
| AC4 | Business logic | HARD.md R005 | CJK-aware tokenization required — error must not be swallowed | 2026-04-08 |
| AC5 | Business logic | CLAUDE.md directory map | `backend/rag/` scope | 2026-04-08 |
| AC6 | Business logic | CONSTITUTION.md Testing convention | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |

### S003 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Existing behavior | `backend/rag/embedder.py` `OllamaEmbedder._embed_one()` | Single-text embed already implemented | 2026-04-08 |
| AC2 | Business logic | ARCH.md A001 | "Each agent owns its directory. Cross-boundary calls via interfaces only." — reuse existing embedder | 2026-04-08 |
| AC3 | Business logic | CONSTITUTION.md P005 | "Fail fast, fail visibly. Structured errors, no silent failures." | 2026-03-18 |
| AC4 | Business logic | CLAUDE.md directory map | query_processor.py grouped with tokenize_query in same file | 2026-04-08 |
| AC5 | Business logic | CONSTITUTION.md Testing convention | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |

### S004 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Business logic | ARCH.md A001/A002 | api-agent must not import rag internals — needs single public interface | 2026-04-08 |
| AC2 | Business logic | backlog.md #6 | "Hybrid search: dense embeddings + BM25, auto lang detect" | 2026-03-17 |
| AC3–AC5 | Business logic | CONSTITUTION.md P005 | Errors must propagate — no silent failures | 2026-03-18 |
| AC6 | Business logic | HARD.md R001 + CONSTITUTION.md C001 | RBAC at DB layer — pipeline must not modify group IDs | 2026-03-18 |
| AC7 | Business logic | CONSTITUTION.md Testing | Unit + integration tests required for critical journeys | 2026-03-18 |
| AC8 | Existing behavior | cjk-tokenizer + document-ingestion test suites | Docker-based integration test pattern already established | 2026-04-08 |

### S005 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2 | Business logic | CONSTITUTION.md P003 | "Japanese, English, Vietnamese, Korean treated equally." | 2026-03-18 |
| AC3 | Business logic | HARD.md R001 / CONSTITUTION.md C001 | RBAC filter must be verified at retrieval level | 2026-03-18 |
| AC4 | Business logic | CONSTITUTION.md C009 | No fallback for undetected language | 2026-03-18 |
| AC5 | Existing behavior | cjk-tokenizer + document-ingestion Docker test suites | Docker infra already in place | 2026-04-08 |
| AC6 | Business logic | CONSTITUTION.md Testing | ≥ 80% coverage for new code | 2026-03-18 |
