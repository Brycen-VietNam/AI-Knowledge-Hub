# Sources Traceability: document-ingestion
Created: 2026-04-06 | Feature spec: `docs/document-ingestion/spec/document-ingestion.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source.
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: POST /v1/documents — Upload & validate document

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: JSON body `{title, content, lang, user_group_id?}` | Business logic | Backlog #5 + CONSTITUTION tech stack | API-first design, all consumers send JSON | 2026-03-17 |
| AC2: lang ISO 639-1 required, 422 if missing | Existing behavior | `backend/db/models/document.py` CHAR(2) lang | DB model enforces 2-char lang code | 2026-04-06 |
| AC3: MAX_DOC_CHARS=100000 → 413 | Conversation | Clarify session lb_mui 2026-04-06 | Reject > limit (env var), no truncation (P005) | 2026-04-06 |
| AC4: empty content → 422 | Business logic | CONSTITUTION P005 — fail fast, fail visibly | No silent failures | 2026-04-06 |
| AC5: write permission RBAC check | Existing behavior | rbac-document-filter — CONSTITUTION C001 | RBAC already implemented, apply to write path | 2026-04-06 |
| AC6: 202 `{doc_id, status: "processing"}` | Conversation | Clarify session lb_mui 2026-04-06 | Embedding is async background task | 2026-04-06 |

### Story S002: Text chunking & language detection

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: CHUNK_SIZE=512, CHUNK_OVERLAP=50 env vars | Conversation | Clarify session lb_mui 2026-04-06 | Fixed-size, configurable via env vars | 2026-04-06 |
| AC2: lang from body; auto-detect fallback | Requirement | CONSTITUTION C009 | Never hardcode lang="en" as fallback | 2026-03-18 |
| AC3: chunk records doc_id, chunk_index, lang | Existing behavior | `backend/db/models/embedding.py` | chunk_index and lang columns already defined | 2026-04-06 |
| AC4: discard empty chunks silently | Business logic | CONSTITUTION P005 | No garbage data in index | 2026-04-06 |

### Story S003: Batch embedding generation

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: batch_embed min 32, no per-chunk loop | Requirement | CONSTITUTION C012 | Mandatory batch minimum to avoid API throttling | 2026-03-18 |
| AC2: Embedding row — doc_id, chunk_index, lang, user_group_id, Vector(1024) | Existing behavior | `backend/db/models/embedding.py` | All columns already defined in DB model | 2026-04-06 |
| AC3: user_group_id copied from Document, not request | Requirement | CONSTITUTION C002, HARD.md R002 | Zero PII in vector metadata; only doc_id, lang, user_group_id, created_at | 2026-03-18 |
| AC4: embedding failure → status=failed, no partial insert | Business logic | CONSTITUTION P005 | Partial state causes phantom search results | 2026-04-06 |

### Story S004: BM25 index update (CJK-aware)

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: MeCab/kiwipiepy/jieba/underthesea per lang | Requirement | CONSTITUTION C005, C006 | CJK tokenizers mandatory; whitespace split forbidden for CJK | 2026-03-18 |
| AC2: content_fts TSVECTOR updated | Existing behavior | `backend/db/models/document.py` migration 003 | content_fts column exists, nullable until rag-agent populates | 2026-04-06 |
| AC3: unknown lang → fallback simple config, log warning | Business logic | CONSTITUTION P005 | Fail visibly — warning in log, don't crash pipeline | 2026-04-06 |
| AC4: BM25 update after embedding commit | Business logic | Data consistency requirement | BM25 and pgvector must be in sync for hybrid search | 2026-04-06 |

### Story S005: Document management — GET list, GET by ID, DELETE

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: GET list paginated, RBAC-filtered | Requirement | CONSTITUTION C001 | RBAC at DB layer — filter by caller's group_ids | 2026-03-18 |
| AC2: GET by ID returns status + chunk_count | Conversation | Clarify session lb_mui 2026-04-06 | Fields: id, title, lang, user_group_id, status, created_at, chunk_count | 2026-04-06 |
| AC3: 404 for inaccessible doc (not 403) | Business logic | Security — prevent enumeration attacks | Treat inaccessible same as not found | 2026-04-06 |
| AC4: DELETE cascades to embeddings | Existing behavior | `backend/db/models/embedding.py` ForeignKey ondelete=CASCADE | Cascade already defined in schema | 2026-04-06 |
| AC5: DELETE 204 no body | Business logic | REST convention | Standard HTTP DELETE success response | 2026-04-06 |

---

## Summary

**Total ACs:** 22
**Fully traced:** 22/22 ✓
**Pending sources:** 0
