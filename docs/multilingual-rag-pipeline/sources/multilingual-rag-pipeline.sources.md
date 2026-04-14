# Sources Traceability: multilingual-rag-pipeline
Created: 2026-04-08 | Feature spec: `docs/multilingual-rag-pipeline/spec/multilingual-rag-pipeline.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Language Detection for Incoming Queries

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `detect_language()` returns BCP-47 code | Business logic | CONSTITUTION.md C009 | "Query language must be auto-detected — never hardcode lang='en' as fallback" | 2026-03-18 |
| AC2: Maps to ja/ko/zh/vi/en | Existing behavior | `backend/rag/bm25_indexer.py` L19 | `_CJK_LANGS = {"ja","ko","zh","vi"}` — same language set used in ingestion | 2026-04-08 |
| AC3: Raises LanguageDetectionError | Existing behavior | document-ingestion archive D12 | LanguageDetectionError propagates (A003 compliant) — precedent set | 2026-04-08 |
| AC4: Unit-tested ≥1 per lang | Business logic | CONSTITUTION.md P003 | "Multilingual by design. Japanese, English, Vietnamese, Korean treated equally." | 2026-03-18 |
| AC5: Lives in `lang_detect.py` | Business logic | CLAUDE.md directory map | `backend/rag/` — rag-agent scope | 2026-04-08 |

### Story S002: Query Tokenization for BM25

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `tokenize_query()` returns space-sep tokens | Existing behavior | `backend/rag/bm25_indexer.py` `tokenize_for_fts()` | Symmetric function already in ingestion path | 2026-04-08 |
| AC2: CJK uses TokenizerFactory | Business logic | CONSTITUTION.md C005/C006 | MeCab(ja), kiwipiepy(ko), jieba(zh), underthesea(vi) — no Java | 2026-03-18 |
| AC3: Non-CJK uses whitespace split | Business logic | CONSTITUTION.md C005 | "Whitespace split is forbidden" for CJK only | 2026-03-18 |
| AC4: UnsupportedLanguageError propagates | Business logic | HARD.md R005 | CJK-aware tokenization required — error must not be swallowed | 2026-04-08 |
| AC5: Lives in `query_processor.py` | Business logic | CLAUDE.md directory map | `backend/rag/` scope | 2026-04-08 |
| AC6: Unit-tested all langs | Business logic | CONSTITUTION.md Testing | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |

### Story S003: Query Embedding

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `embed_query()` via OllamaEmbedder | Existing behavior | `backend/rag/embedder.py` `_embed_one()` | Single-text embed already implemented | 2026-04-08 |
| AC2: Reuses OllamaEmbedder — no new client | Business logic | ARCH.md A001 | "Each agent owns its directory. Cross-boundary calls via interfaces only." | 2026-04-08 |
| AC3: EmbedderError propagates | Business logic | CONSTITUTION.md P005 | "Fail fast, fail visibly. Structured errors, no silent failures." | 2026-03-18 |
| AC4: Lives in `query_processor.py` | Business logic | CLAUDE.md directory map | Same file as tokenize_query for co-located query prep logic | 2026-04-08 |
| AC5: Unit-tested with mock embedder | Business logic | CONSTITUTION.md Testing | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |

### Story S004: Unified `search()` Service Function

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `search()` importable from `search.py` | Business logic | ARCH.md A001/A002 | api-agent must not import rag internals — single public interface required | 2026-04-08 |
| AC2: detect → tokenize → embed → retrieve | Business logic | backlog.md #6 | "Hybrid search: dense embeddings + BM25, auto lang detect" | 2026-03-17 |
| AC3: LanguageDetectionError propagates | Business logic | CONSTITUTION.md P005 | No silent failures | 2026-03-18 |
| AC4: QueryTimeoutError propagates | Existing behavior | `backend/rag/retriever.py` L145 | `QueryTimeoutError` already defined and raised at 1800ms | 2026-04-08 |
| AC5: EmbedderError propagates | Business logic | CONSTITUTION.md P005 | No silent failures | 2026-03-18 |
| AC6: user_group_ids passed unchanged | Business logic | HARD.md R001 / CONSTITUTION.md C001 | RBAC at DB layer — pipeline must not modify group IDs | 2026-03-18 |
| AC7: Unit-tested with mocks | Business logic | CONSTITUTION.md Testing | Unit tests required | 2026-03-18 |
| AC8: Integration test against real DB | Existing behavior | cjk-tokenizer + document-ingestion test suites | Docker-based integration test pattern established | 2026-04-08 |

### Story S005: RAG Pipeline Smoke Test & Integration Validation

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Seeds ≥1 doc per language | Business logic | CONSTITUTION.md P003 | "Japanese, English, Vietnamese, Korean treated equally." | 2026-03-18 |
| AC2: search() returns ≥1 result per lang | Business logic | CONSTITUTION.md P003 | Parity across all supported languages | 2026-03-18 |
| AC3: RBAC test — public-only when group_ids=[] | Business logic | HARD.md R001 / CONSTITUTION.md C001 | RBAC filter must be verifiable at retrieval level | 2026-03-18 |
| AC4: LanguageDetectionError for empty query | Business logic | CONSTITUTION.md C009 | No fallback for undetected language | 2026-03-18 |
| AC5: Passes in Docker | Existing behavior | cjk-tokenizer + document-ingestion Docker infra | Infra already in place | 2026-04-08 |
| AC6: ≥ 80% unit coverage | Business logic | CONSTITUTION.md Testing | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |

---

## Summary

**Total ACs:** 24
**Fully traced:** 24/24 ✓
**Pending sources:** 0

---

## Source Type Reference

| Type | Examples |
|------|---------|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |
