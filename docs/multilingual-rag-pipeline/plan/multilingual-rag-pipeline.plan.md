# Plan: multilingual-rag-pipeline
Generated: 2026-04-08 | Spec: v1 DRAFT | Status: READY FOR /tasks

---

## Plan Summary
**multilingual-rag-pipeline** | 4 Stories | 1 Session Est. | Critical Path: S002→S003→S004→S005
- **Stories**: S002 (Query Tokenization), S003 (Query Embedding), S004 (Unified search() Service), S005 (Integration Test)
- **Parallel groups**: G1 (S002 ∥ S003), G2 (S004→S005 sequential after G1)
- **Agent**: rag-agent (S002–S005), db-agent (read-only)
- **Token budget**: ~3.5k total

---

## Layer 1 — Plan Overview

| Dimension | Value |
|-----------|-------|
| Total stories | 4 (S002, S003, S004, S005) |
| Critical path | S002 → S003 → (both complete) → S004 → S005 |
| Parallel-safe group G1 | S002 ∥ S003 (tokenization + embedding independent) |
| Sequential G2 | S004 (unified search service after G1 complete) |
| Sequential G2 | S005 (integration test after S004 complete) |
| Blockers | None — all dependencies DONE ✅ |
| Agents needed | rag-agent (primary), db-agent (read-only) |
| Sessions est. | 1 |

**Parallelization Strategy**:
- Run S002 and S003 concurrently (Group G1) — both are independent utility functions with no data flow between them
- After both G1 stories complete → run S004 (orchestration layer depends on both tokenize_query + embed_query)
- After S004 complete → run S005 (integration validation)

---

## Layer 2 — Per-Story Plan

### S002: Query Tokenization for BM25
| Field | Value |
|-------|-------|
| **Agent** | rag-agent |
| **Parallel group** | G1 |
| **Depends on** | None |
| **Files to create** | `backend/rag/query_processor.py` (new file) |
| **Functions to add** | `tokenize_query(text: str, lang: str) -> str` |
| **ACs to verify** | 5 |
| **Est. tokens** | ~1.2k |
| **Test strategy** | Unit tests: ja, vi, en, unsupported lang (4 cases) |

**Scope**: Single function + unit tests
- Implement `tokenize_query()` using `TokenizerFactory.get(lang).tokenize()`
- All languages (including "en") delegate to factory — no special-casing
- Return space-separated token string (symmetric with `bm25_indexer.tokenize_for_fts()`)
- Propagate `UnsupportedLanguageError` — no swallowing
- Unit test: 4 cases covering ja, vi, en, unknown lang

**AC Checklist**:
- [ ] AC1: `tokenize_query(text: str, lang: str) -> str` returns space-separated token string
- [ ] AC2: All langs (including "en") delegate to `TokenizerFactory.get(lang).tokenize()`
- [ ] AC3: `UnsupportedLanguageError` propagates to caller
- [ ] AC4: Function lives in `backend/rag/query_processor.py`
- [ ] AC5: Unit-tested: ja, vi, en, and unknown lang each exercised

---

### S003: Query Embedding
| Field | Value |
|-------|-------|
| **Agent** | rag-agent |
| **Parallel group** | G1 |
| **Depends on** | None |
| **Files to modify** | `backend/rag/query_processor.py` (add function) |
| **Functions to add** | `embed_query(text: str) -> list[float]` |
| **ACs to verify** | 5 |
| **Est. tokens** | ~0.8k |
| **Test strategy** | Unit tests: mocked OllamaEmbedder._embed_one() |

**Scope**: Single function + unit tests
- Implement `embed_query()` using `OllamaEmbedder._embed_one()`
- No new embedding client — reuse existing `OllamaEmbedder` from `backend/rag/embedder.py`
- Instantiate at module level (singleton) or accept as dependency
- Propagate `EmbedderError` — no silent fallback
- Unit test: mocked embedder returning fixed vector

**AC Checklist**:
- [ ] AC1: `embed_query(text: str) -> list[float]` returns a vector via `OllamaEmbedder._embed_one()`
- [ ] AC2: Uses `OllamaEmbedder` from `backend/rag/embedder.py` — no new embedding client created
- [ ] AC3: `EmbedderError` propagates to caller — no silent fallback
- [ ] AC4: Function lives in `backend/rag/query_processor.py` (same file as S002)
- [ ] AC5: Unit-tested with a mocked `OllamaEmbedder._embed_one` returning a fixed vector

---

### S004: Unified search() Service Function
| Field | Value |
|-------|-------|
| **Agent** | rag-agent |
| **Parallel group** | G2 (after G1 complete) |
| **Depends on** | S002 + S003 (both tokenize_query and embed_query must exist) |
| **Files to create** | `backend/rag/search.py` (new file) |
| **Functions to add** | `search(query, user_group_ids, session, top_k, lang) async -> list[RetrievedDocument]` |
| **ACs to verify** | 9 |
| **Est. tokens** | ~1.2k |
| **Test strategy** | Unit tests (mocked DB) + integration test (Docker real DB) |

**Scope**: Orchestration function + unit + integration tests
- Implement `search()` as async entry point orchestrating: (detect_language if lang=None) → tokenize_query → embed_query → retrieve
- Support `lang` override — if provided, skip detection and use directly
- Pass `user_group_ids` through to `retrieve()` unchanged (RBAC at DB layer)
- Propagate all errors: `LanguageDetectionError`, `EmbedderError`, `QueryTimeoutError`
- Unit tests: lang=None path (auto-detect), lang="ja" path (override), error propagation
- Integration test: called against real DB session, returns ranked results

**API Contract** (internal — no HTTP boundary):
```python
async def search(
    query: str,
    user_group_ids: list[int],
    session: AsyncSession,
    top_k: int = 10,
    lang: str | None = None,
) -> list[RetrievedDocument]
```

**AC Checklist**:
- [ ] AC1: Signature matches spec — importable from `backend/rag/search.py`
- [ ] AC2: If `lang` is None, calls `detect_language(query)` — if provided, skips detection
- [ ] AC3: Internally calls (detect →) `tokenize_query()` → `embed_query()` → `retrieve()` in that order
- [ ] AC4: `LanguageDetectionError` propagates to caller when `lang=None` and detection fails
- [ ] AC5: `QueryTimeoutError` from `retrieve()` propagates to caller unchanged
- [ ] AC6: `EmbedderError` propagates to caller unchanged
- [ ] AC7: RBAC filter (`user_group_ids`) is passed through to `retrieve()` unchanged
- [ ] AC8: Unit-tested: lang=None path, lang="ja" path, error propagation covered
- [ ] AC9: Integration test: `search()` called against real DB session returns ranked results

---

### S005: RAG Pipeline Smoke Test & Integration Validation
| Field | Value |
|-------|-------|
| **Agent** | rag-agent |
| **Parallel group** | G2 (after S004 complete) |
| **Depends on** | S004 (search function must exist) |
| **Files to create** | `tests/rag/test_integration_search.py` (new file) |
| **Functions to test** | `search()` — full pipeline validation |
| **ACs to verify** | 7 |
| **Est. tokens** | ~0.6k |
| **Test strategy** | Docker-based integration test (real PostgreSQL + pgvector) |

**Scope**: Integration test suite + coverage validation
- Reuse Docker test infra from `cjk-tokenizer` and `document-ingestion` test suites
- Seed ≥1 document per language (ja, en, vi, ko) into test DB
- Verify `search()` returns ≥1 result for each language
- Verify RBAC: query with `user_group_ids=[]` returns only public documents
- Verify `LanguageDetectionError` raised for gibberish/empty query (lang=None path)
- Verify explicit `lang="ja"` override skips auto-detect and returns correct results
- Verify ≥80% unit test coverage for `query_processor.py` and `search.py`
- All tests pass in Docker (pytest with real DB, no mocks for integration suite)

**AC Checklist**:
- [ ] AC1: Integration test seeds ≥1 document per supported language (ja, en, vi, ko) into test DB
- [ ] AC2: `search()` called with a matching query returns ≥1 result for each language
- [ ] AC3: Test verifies RBAC: query with `user_group_ids=[]` returns only public documents
- [ ] AC4: Test verifies `LanguageDetectionError` is raised for a gibberish/empty query (lang=None path)
- [ ] AC5: Test verifies explicit `lang="ja"` override skips auto-detect and returns correct results
- [ ] AC6: All tests pass in Docker (pytest with real DB, no mocks for integration suite)
- [ ] AC7: Unit test coverage for `query_processor.py`, `search.py` ≥ 80%

---

## Subagent Assignment & Dispatch

| Story | Agent | Dispatch | Scope |
|-------|-------|----------|-------|
| S002 | rag-agent | Parallel (G1) | Tokenizer + unit tests (1.2k tokens) |
| S003 | rag-agent | Parallel (G1) | Embedder + unit tests (0.8k tokens) |
| S004 | rag-agent | Sequential (G2) | Search service + unit + integration (1.2k tokens) |
| S005 | rag-agent | Sequential (G2) | Integration validation suite (0.6k tokens) |

**Cross-boundary dependencies**: None. All 4 stories are within `backend/rag/` — rag-agent scope (ARCH.md A001, A002 compliant).

---

## Architecture & Rules Compliance

| Rule | Status | Evidence |
|------|--------|----------|
| **A001** (Agent scope) | ✅ PASS | rag-agent owns all stories; db-agent read-only |
| **A002** (Dependency direction) | ✅ PASS | rag → db only (retrieve() call); no api ← rag |
| **A003** (Language detection) | ✅ PASS | Auto-detect at S004 entry; lang override supported |
| **A004** (Hybrid weights) | ✅ PASS | Retrieved via existing retrieve() — weights already parameterized |
| **R001** (RBAC before retrieval) | ✅ PASS | user_group_ids passed to retrieve() at DB layer |
| **R005** (CJK tokenization) | ✅ PASS | TokenizerFactory.get(lang) delegates to MeCab/kiwipiepy/jieba/underthesea |
| **R007** (Latency SLA) | ✅ PASS | search() budget ≤1500ms (p95 /v1/query < 2000ms) |
| **P002** (Batch embeddings) | ✅ PASS | embed_query() is single-text (acceptable); batch calls elsewhere |

---

## Next Steps
1. ✅ Spec: DRAFT (v1)
2. ✅ Checklist: PASS (all 30 items)
3. ✅ Plan: READY (this file)
4. → Run `/tasks multilingual-rag-pipeline` to break stories into atomic tasks
5. → Dispatch rag-agent for parallel group G1 (S002 ∥ S003)
6. → Sequence S004 (search service) after G1 complete
7. → Finalize with S005 (integration validation)
8. → Run `/report multilingual-rag-pipeline` after all stories DONE

---

## Token Budget Summary
| Story | Est. tokens | Phase |
|-------|-------------|-------|
| S002 | ~1.2k | /tasks + /analyze + /implement |
| S003 | ~0.8k | /tasks + /analyze + /implement |
| S004 | ~1.2k | /tasks + /analyze + /implement |
| S005 | ~0.6k | /tasks + /analyze + /implement |
| **Total** | **~3.8k** | Feature completion |

Per CLAUDE.md budgets: /plan (4k) ✅, /tasks (3k per story), /analyze (5k), /implement (6k), /reviewcode (3k).
