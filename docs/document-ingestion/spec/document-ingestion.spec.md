# Spec: document-ingestion
Created: 2026-04-06 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary

| Field | Value |
|-------|-------|
| Epic | api |
| Priority | P0 |
| Story count | 5 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 → S003 → S004 |
| Parallel-safe stories | S003 ∥ S004 (after S002) |
| Blocking specs | multilingual-rag-pipeline |
| Blocked by | db-schema-embeddings ✅, auth-api-key-oidc ✅, rbac-document-filter ✅, cjk-tokenizer ✅ |
| Agents needed | api-agent, rag-agent, db-agent |

### Problem Statement
Employees and bots need to upload company knowledge into the platform so it can be searched via hybrid RAG.
Currently no ingestion pipeline exists — embeddings table is empty, BM25 index is empty.
Without ingestion, the query endpoint has nothing to retrieve.

### Solution Summary
- POST /v1/documents: accepts JSON `{title, content, lang, user_group_id}`, validates, chunks, embeds, indexes
- Chunking: fixed-size 512 tokens, 50-token overlap, configurable via env vars
- Batch embedding: multilingual-e5-large, min 32 docs per call (C012)
- BM25 index: updated with CJK-aware tokenizer after embedding (C005, C006)
- Document management: GET list (paginated), GET by ID, DELETE (cascades embeddings)

### Out of Scope
- File upload (PDF, DOCX) — plain text JSON only for P0
- Semantic/paragraph-boundary chunking
- Document update (PUT/PATCH) — delete + re-upload pattern
- Full-text content retrieval via API (content stored in DB only for internal use)

---

## LAYER 2 — Story Detail

---

### S001: POST /v1/documents — Upload & validate document

**Role / Want / Value**
- As a: bot (API-key) or admin user (OIDC Bearer)
- I want: to submit a document via POST /v1/documents
- So that: the document enters the ingestion pipeline and becomes searchable

**Acceptance Criteria**
- [ ] AC1: POST /v1/documents accepts JSON body `{title, content, lang, user_group_id?}`
- [ ] AC2: `lang` must be a valid ISO 639-1 code; if missing → 422 with structured error
- [ ] AC3: `content` length > `MAX_DOC_CHARS` (default 100000) → 413 with structured error
- [ ] AC4: `content` empty or whitespace-only → 422 with structured error
- [ ] AC5: Caller must have `write` permission on the target `user_group_id` (RBAC check via existing middleware)
- [ ] AC6: Successful upload returns 202 `{doc_id, status: "processing"}` — ingestion is async

**API Contract**
```
POST /v1/documents
Headers: Authorization: Bearer <oidc_token> | X-API-Key: <key>
Body: {
  "title": "string (required)",
  "content": "string (required, max MAX_DOC_CHARS chars)",
  "lang": "string (required, ISO 639-1, e.g. 'ja', 'en', 'vi', 'ko')",
  "user_group_id": "integer (optional, null = public)"
}
Response 202: {"doc_id": "<uuid>", "status": "processing"}
Response 413: {"error": {"code": "DOC_TOO_LARGE", "message": "...", "request_id": "..."}}
Response 422: {"error": {"code": "INVALID_INPUT", "message": "...", "request_id": "..."}}
Response 403: {"error": {"code": "FORBIDDEN", "message": "...", "request_id": "..."}}
```

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)

**Non-functional**
- Latency: < 500ms for validation + DB insert (embedding is async background task)
- Audit log: not required at upload (required at retrieval per R006)
- CJK support: not applicable at this layer (chunking/tokenization in S002–S004)

**Implementation notes**
- Insert `Document` row immediately on receipt; return doc_id
- Dispatch background task (FastAPI BackgroundTasks or asyncio) for chunking → embedding → BM25 index
- Rate limit: 20 req/min per caller (C013) — enforced by existing middleware (or stub if rate-limiting feature not yet deployed)

---

### S002: Text chunking & language detection

**Role / Want / Value**
- As a: ingestion pipeline (internal)
- I want: document content split into overlapping chunks with detected/confirmed language
- So that: each chunk can be independently embedded and retrieved

**Acceptance Criteria**
- [ ] AC1: Content is split into chunks of `CHUNK_SIZE` tokens (default 512) with `CHUNK_OVERLAP` (default 50), both configurable via env vars
- [ ] AC2: `lang` from request body is accepted as-is if provided; auto-detect (langdetect) only if not supplied
- [ ] AC3: Each chunk records `chunk_index` (0-based), `doc_id`, `lang`
- [ ] AC4: Empty chunks (after strip) are discarded silently

**Non-functional**
- Latency: chunking must complete < 200ms for 100k-char document
- CJK support: chunking is token-count aware (use `len(tokenizer.tokenize(text))` for CJK, whitespace-split token count for latin scripts)

**Implementation notes**
- Chunker lives in `backend/rag/chunker.py` (new file)
- Token counting: for CJK use already-initialized tokenizer from cjk-tokenizer feature; for others use simple whitespace estimate
- Do NOT re-tokenize for BM25 here — chunker only splits, tokenization for BM25 is in S004

---

### S003: Batch embedding generation

**Role / Want / Value**
- As a: ingestion pipeline (internal)
- I want: all chunks for a document embedded in batch via multilingual-e5-large
- So that: vectors are stored in the `embeddings` table ready for pgvector HNSW search

**Acceptance Criteria**
- [ ] AC1: Embeddings generated via `embedder.batch_embed(chunks, batch_size=32)` — no per-chunk loop (C012)
- [ ] AC2: Each `Embedding` row stores: `doc_id`, `chunk_index`, `lang`, `user_group_id` (denormalized from Document), `embedding` (Vector 1024)
- [ ] AC3: `user_group_id` is copied from parent `Document` — never from request at this step
- [ ] AC4: If embedding API call fails → mark document status as `failed`, do not partially insert

**Non-functional**
- Latency: batch of 32 chunks must complete < 1000ms (embedding model local/ollama)
- CJK support: multilingual-e5-large handles ja/ko/zh/vi natively — no special handling

**Implementation notes**
- Embedder lives in `backend/rag/embedder.py` (new file or extend existing stub)
- Use `asyncio.gather` for concurrent batch calls if document has > 32 chunks
- On failure: update `documents.status = 'failed'` and log error — do not raise to caller (already 202'd)

---

### S004: BM25 index update (CJK-aware)

**Role / Want / Value**
- As a: ingestion pipeline (internal)
- I want: each chunk's tokenized text inserted into the BM25 index (PostgreSQL FTS)
- So that: hybrid search can use BM25 scores alongside dense vectors

**Acceptance Criteria**
- [ ] AC1: Chunk text tokenized with correct language tokenizer before FTS update: MeCab (ja), kiwipiepy (ko), jieba (zh), underthesea (vi), whitespace (en/other) — per C005, C006
- [ ] AC2: `documents.content_fts` (TSVECTOR column) updated via `to_tsvector` with tokenized text
- [ ] AC3: If lang is unsupported/unknown → fallback to `simple` PostgreSQL text search config, log warning
- [ ] AC4: BM25 update runs after embedding insert is committed (ordering guarantee)

**Non-functional**
- CJK support: ja / zh / vi / ko (via cjk-tokenizer feature interfaces)
- Audit log: not required

**Implementation notes**
- Call `backend/rag/bm25_indexer.py` (existing from cjk-tokenizer feature)
- Update is a single `UPDATE documents SET content_fts = ... WHERE id = :doc_id`
- On completion: update `documents.status = 'ready'`

---

### S005: Document management — GET list, GET by ID, DELETE

**Role / Want / Value**
- As a: admin or service account
- I want: to list, inspect, and delete indexed documents
- So that: the knowledge base can be audited and incorrect documents removed

**Acceptance Criteria**
- [ ] AC1: GET /v1/documents returns paginated list filtered by caller's accessible `user_group_id` set (RBAC)
- [ ] AC2: GET /v1/documents/{id} returns document metadata (`id`, `title`, `lang`, `user_group_id`, `status`, `created_at`, `chunk_count`)
- [ ] AC3: GET /v1/documents/{id} returns 404 if doc not found or not accessible by caller's groups
- [ ] AC4: DELETE /v1/documents/{id} removes `documents` row; cascades to `embeddings` (FK `ondelete=CASCADE` already set)
- [ ] AC5: DELETE returns 204 on success, 404 if not found or not accessible

**API Contract**
```
GET /v1/documents?page=1&limit=20&user_group_id=<int>
Headers: Authorization: Bearer <token> | X-API-Key: <key>
Response 200: {
  "items": [{"id", "title", "lang", "user_group_id", "status", "created_at", "chunk_count"}],
  "total": <int>, "page": <int>, "limit": <int>
}

GET /v1/documents/{id}
Response 200: {"id", "title", "lang", "user_group_id", "status", "created_at", "chunk_count"}
Response 404: {"error": {"code": "NOT_FOUND", "message": "...", "request_id": "..."}}

DELETE /v1/documents/{id}
Response 204: (no body)
Response 404: {"error": {"code": "NOT_FOUND", "message": "...", "request_id": "..."}}
```

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)

**Non-functional**
- Latency: < 500ms p95
- Audit log: not required (no retrieval of content)
- RBAC: list filtered to caller's groups; single-doc access gated same way

**Implementation notes**
- Add `status` column to `documents` table: `'processing' | 'ready' | 'failed'` — migration 006 required
- Add `chunk_count` as computed from `COUNT(embeddings.doc_id)` — no denormalized column needed
- RBAC filter: `WHERE user_group_id = ANY(:group_ids) OR user_group_id IS NULL`

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1: JSON body shape | Business logic | Backlog #5 `document-ingestion` description + CONSTITUTION tech stack | 2026-03-17 |
| AC2: lang validation | Existing behavior | `Document` model — `CHAR(2)` lang field in `backend/db/models/document.py` | 2026-04-06 |
| AC3: MAX_DOC_CHARS=100000 | Conversation | Clarify session lb_mui 2026-04-06 — reject > limit, env var configurable | 2026-04-06 |
| AC4: empty content reject | Business logic | Fail fast principle — CONSTITUTION P005 | 2026-04-06 |
| AC5: write permission RBAC | Existing behavior | rbac-document-filter feature — CONSTITUTION C001 | 2026-04-06 |
| AC6: 202 async response | Conversation | Clarify session lb_mui 2026-04-06 — embedding is background task | 2026-04-06 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1: CHUNK_SIZE=512, CHUNK_OVERLAP=50 | Conversation | Clarify session lb_mui 2026-04-06 — fixed size, env var configurable | 2026-04-06 |
| AC2: lang from body, fallback auto-detect | Existing behavior | CONSTITUTION C009 — never hardcode lang="en" fallback | 2026-03-18 |
| AC3: chunk_index + doc_id + lang | Existing behavior | `Embedding` model — `chunk_index`, `lang` columns in `backend/db/models/embedding.py` | 2026-04-06 |
| AC4: discard empty chunks | Business logic | CONSTITUTION P005 — fail fast, no silent garbage | 2026-04-06 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1: batch_embed min 32 | Requirement | CONSTITUTION C012 — never per-document loop | 2026-03-18 |
| AC2: Embedding row shape | Existing behavior | `backend/db/models/embedding.py` — doc_id, chunk_index, lang, user_group_id, embedding Vector(1024) | 2026-04-06 |
| AC3: user_group_id from Document | Requirement | CONSTITUTION C002 — no PII in vector metadata; R002 HARD.md | 2026-03-18 |
| AC4: fail → status=failed | Business logic | CONSTITUTION P005 — no silent failures | 2026-04-06 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1: CJK tokenizer per lang | Requirement | CONSTITUTION C005, C006 — MeCab/kiwipiepy/jieba/underthesea mandatory | 2026-03-18 |
| AC2: content_fts TSVECTOR update | Existing behavior | `backend/db/models/document.py` — `content_fts` TSVECTOR column (migration 003) | 2026-04-06 |
| AC3: fallback to simple config | Business logic | CONSTITUTION P005 — fail visibly, log warning | 2026-04-06 |
| AC4: after embedding commit | Business logic | Data consistency — BM25 and vector store must stay in sync | 2026-04-06 |

### S005 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1: RBAC-filtered list | Requirement | CONSTITUTION C001 — RBAC at DB layer | 2026-03-18 |
| AC2: GET metadata fields | Conversation | Clarify session lb_mui 2026-04-06 — id, title, lang, user_group_id, status, created_at, chunk_count | 2026-04-06 |
| AC3: 404 on inaccessible | Business logic | Security — treat inaccessible same as not found (prevent enumeration) | 2026-04-06 |
| AC4: CASCADE delete embeddings | Existing behavior | `backend/db/models/embedding.py` — `ForeignKey("documents.id", ondelete="CASCADE")` | 2026-04-06 |
| AC5: 204 on DELETE | Business logic | REST convention — no body on successful delete | 2026-04-06 |
