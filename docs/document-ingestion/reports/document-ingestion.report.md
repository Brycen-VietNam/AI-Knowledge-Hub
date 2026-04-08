# Report: document-ingestion
Generated: 2026-04-08 | Reviewer: Claude (haiku) | Status: COMPLETE — pending sign-off

---

## Executive Summary

| Field | Value |
|-------|-------|
| Feature | document-ingestion |
| Status | COMPLETE — all 22 ACs PASS, /reviewcode APPROVED |
| Duration | 2026-04-06 → 2026-04-07 (2 days) |
| Stories | 5 (S001, S002, S003, S004, S005 [split: db + api]) |
| ACs | 22/22 PASS (100%) |
| Tests | 61 new tests, 230 pass, 9 pre-existing fails (unrelated) |
| Code review | APPROVED after 3 warnings fixed (W1, W2, W3) |
| Unblocks | query-endpoint, multilingual-rag-pipeline |

---

## Changes Summary

### Code (new files)
| File | Story | Description |
|------|-------|-------------|
| `backend/api/routes/documents.py` | S001, S005 | POST, GET list, GET by ID, DELETE — 307 lines |
| `backend/rag/chunker.py` | S002 | Fixed-size chunker with CJK token counting — 80 lines |
| `backend/rag/embedder.py` | S003 | Ollama batch embedding client, asyncio.gather — 79 lines |
| `backend/rag/bm25_indexer.py` | S004 | CJK-aware FTS indexer, content_fts write path — 58 lines |

### Code (modified files)
| File | Story | Change |
|------|-------|--------|
| `backend/db/models/document.py` | S005-db | Added `status` column |
| `backend/db/models/embedding.py` | S005-db | Added `text TEXT NOT NULL` column |
| `backend/api/routes/__init__.py` | S001 | Registered documents router |

### Database
| Migration | Change |
|-----------|--------|
| `006_add_document_status_and_chunk_text.sql` | `documents.status VARCHAR(20) DEFAULT 'processing'` + `embeddings.text TEXT NOT NULL`; rollback section included |

### Config / Env Vars added
| Variable | Default | Used by |
|----------|---------|---------|
| `MAX_DOC_CHARS` | `100000` | S001 upload validation |
| `CHUNK_SIZE` | `512` | S002 chunker |
| `CHUNK_OVERLAP` | `50` | S002 chunker |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | S003 embedder |
| `EMBEDDING_MODEL` | `mxbai-embed-large` | S003 embedder |

### Tests added
| File | Story | Count |
|------|-------|-------|
| `tests/api/test_documents_upload.py` | S001 | ~20 |
| `tests/api/test_documents_management.py` | S005-api | ~20 |
| `tests/db/test_document_model.py` | S005-db | ~13 |
| `tests/rag/test_chunker.py` | S002 | ~12 |
| `tests/rag/test_embedder.py` | S003 | ~15 |
| `tests/rag/test_bm25_indexer.py` | S004 | ~12 |

---

## Test Results

| Suite | Pass | Fail | Skip | Coverage |
|-------|------|------|------|----------|
| All tests (post-implement) | 230 | 9 | 0 | ~94% |
| 9 pre-existing failures | — | 9 | — | Unrelated to this feature |
| New tests (this feature) | 61 | 0 | 0 | — |

**Pre-existing failures (9):** Unrelated to document-ingestion — inherited from prior features, not introduced by this work.

---

## Code Review Results

Review date: 2026-04-07 | Reviewer: Claude (opus) | Level: security + functionality

| Category | Result |
|----------|--------|
| Functionality | PASS — all task criteria met across S001–S005 |
| Security (R001–R006, S001–S005) | PASS — RBAC WHERE clause, no SQL injection, all routes auth-gated |
| Performance (P001–P005) | PASS — batch embed, no N+1, async pipeline |
| Architecture (A001–A006) | PASS — agent scope, error shape, env config |
| Hard rules (HARD.md) | PASS — R001 RBAC, R002 no PII, R003 verify_token, R004 /v1/ prefix, R005 CJK tokenizer |

**Warnings fixed (pre-approval):**

| ID | Issue | Fix | Status |
|----|-------|-----|--------|
| W1 | Double `verify_token` on all 4 routes (inefficiency, not security gap) | Removed `dependencies=[Depends(verify_token)]` — signature-level Depends sufficient | FIXED |
| W2 | `httpx.AsyncClient` no timeout — Ollama hang risk | Added `timeout=10.0` to AsyncClient | FIXED |
| W3 | `_resolve_lang` fallback to `"en"` — violates A003 | `LanguageDetectionError` now propagates to caller; no silent `"en"` fallback | FIXED |

Final verdict: **APPROVED** (0 blockers, 0 open warnings)

---

## Acceptance Criteria Status

### S001 — POST /v1/documents
| AC | Description | Status |
|----|-------------|--------|
| AC1 | Accepts JSON `{title, content, lang, user_group_id?}` | PASS |
| AC2 | Invalid/missing `lang` → 422 structured error | PASS |
| AC3 | `content` > MAX_DOC_CHARS → 413 structured error | PASS |
| AC4 | Empty/whitespace content → 422 structured error | PASS |
| AC5 | RBAC write check on `user_group_id` | PASS |
| AC6 | Returns 202 `{doc_id, status: "processing"}` — async | PASS |

### S002 — Text chunking
| AC | Description | Status |
|----|-------------|--------|
| AC1 | CHUNK_SIZE / CHUNK_OVERLAP env-configurable | PASS |
| AC2 | `lang` from request body; auto-detect if absent | PASS |
| AC3 | Each chunk records `chunk_index`, `doc_id`, `lang` | PASS |
| AC4 | Empty chunks discarded silently | PASS |

### S003 — Batch embedding
| AC | Description | Status |
|----|-------------|--------|
| AC1 | `batch_embed(chunks, batch_size=32)` — no per-chunk loop | PASS |
| AC2 | Embedding row: `doc_id`, `chunk_index`, `lang`, `user_group_id`, `embedding` Vector(1024) | PASS |
| AC3 | `user_group_id` copied from parent Document | PASS |
| AC4 | Embedding API failure → `status=failed`, no partial insert | PASS |

### S004 — BM25 index update
| AC | Description | Status |
|----|-------------|--------|
| AC1 | CJK tokenizer per lang (MeCab/kiwipiepy/jieba/underthesea) | PASS |
| AC2 | `content_fts` TSVECTOR updated via `to_tsvector` | PASS |
| AC3 | Unknown lang → fallback `simple` config + log warning | PASS |
| AC4 | BM25 update runs after embedding commit | PASS |

### S005 — Document management
| AC | Description | Status |
|----|-------------|--------|
| AC1 | GET list: paginated, RBAC-filtered | PASS |
| AC2 | GET by ID: returns metadata fields + chunk_count | PASS |
| AC3 | GET by ID: 404 for inaccessible (prevents enumeration) | PASS |
| AC4 | DELETE cascades to embeddings (FK ondelete=CASCADE) | PASS |
| AC5 | DELETE: 204 on success, 404 if not found/accessible | PASS |

**Total: 22/22 PASS (100%)**

---

## Key Decisions (captured during feature)

| ID | Decision |
|----|----------|
| D01 | Content format = plain text JSON only. PDF/DOCX deferred. |
| D02 | Fixed-size 512-token chunks, 50-token overlap. Env-configurable. |
| D03 | RBAC write permission required. Bots need group assignment. |
| D04 | MAX_DOC_CHARS=100000. Reject (413), never truncate. |
| D05 | Upload → 202 async. Embedding is background task. |
| D06 | GET list + GET by ID + DELETE. No PUT/PATCH (delete+reupload pattern). |
| D07 | Migration 006 adds `status` column to `documents`. |
| D08 | `bm25_indexer.py` is NEW in this feature — owns content_fts write path. |
| D09 | Write permission = `api_key` only. OIDC Bearer → read-only (post-MVP: role-management). |
| D10 | Embedder backend = Ollama `/api/embeddings`. Model: `mxbai-embed-large`. |
| D11 | Raw `content` NOT stored in `documents` table (DB bloat). Chunk text in `embeddings.text`. |
| D12 | /reviewcode W1+W2+W3 fixed before approval. A003 compliant (LanguageDetectionError propagates). |

---

## Blockers & Deferred Items

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| No blockers | — | — | All 3 /reviewcode warnings fixed before finalization |
| PDF/DOCX upload | Deferred (out of scope P0) | TBD | Spec explicitly excludes file upload |
| OIDC write access | Deferred to role-management feature | TBD | D09 — OIDC Bearer read-only at MVP |
| Document update (PUT/PATCH) | Deferred | TBD | Delete + re-upload pattern documented in spec |

---

## Rollback Plan

| Step | Action | Risk |
|------|--------|------|
| 1 | Revert `backend/api/routes/documents.py` (remove POST/GET/DELETE routes) | Low |
| 2 | Revert router registration in `backend/api/routes/__init__.py` | Low |
| 3 | Remove `backend/rag/chunker.py`, `embedder.py`, `bm25_indexer.py` | Low |
| 4 | Run rollback SQL in migration 006: `ALTER TABLE documents DROP COLUMN status; ALTER TABLE embeddings DROP COLUMN text;` | **Medium** — data loss if rows already ingested |
| 5 | Revert `backend/db/models/document.py` and `embedding.py` | Low |

**Data loss risk:** Migration rollback drops `documents.status` and `embeddings.text`. Any documents already ingested after migration 006 will lose status tracking and chunk text. Rollback is safe only if no documents have been ingested in production.

**Downtime:** None expected — migration 006 adds columns only (non-breaking). Rollback requires brief DB maintenance.

---

## Knowledge & Lessons Learned

### What went well
- D11 (no raw content in documents table) caught early in /analyze — avoided a DB design mistake that would have required a later migration.
- W3 (A003 `lang="en"` hardcode) caught in /reviewcode — multilingual-rag-pipeline would have broken on detection failures without this fix.
- Parallel-safe S003/S004 file creation matched plan exactly — no merge conflicts.

### What to improve
- W2 (httpx timeout) should be a checklist item for any external HTTP client — add to HARD.md or PERF.md as P006.
- W1 (double verify_token) pattern — consider adding a project-level FastAPI pattern rule: "signature-level Depends only, never duplicate in `dependencies=[]`."

### Rule update candidates
- **PERF P006 (proposed):** All `httpx.AsyncClient` calls must set `timeout=`. Default: `timeout=10.0` for embedding/LLM calls.
- **ARCH A007 (proposed):** FastAPI route auth — use signature-level `Depends(verify_token)` only. Do not duplicate in `dependencies=[]`.

---

## Sign-Off

| Role | Approver | Status |
|------|----------|--------|
| Tech Lead | lb_mui | _pending_ |
| Product Owner | lb_mui | _pending_ |
| QA Lead | lb_mui | _pending_ |

After all approvals, run:
```
/report document-ingestion --finalize
```
→ Archives `WARM/document-ingestion.mem.md` → `COLD/document-ingestion.archive.md`
→ Adds row to `COLD/README.md`
→ Updates `HOT.md` — removes from In Progress
→ Feature marked DONE
