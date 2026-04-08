# COLD Archive: document-ingestion
Archived: 2026-04-08 | Status: DONE ✅ | Approved by: lb_mui

---

## Spec Summary
POST /v1/documents ingestion pipeline — upload JSON text, chunk, batch embed, BM25 index.
5 stories, 22 ACs, all PASS.

## Key Decisions
- D01: Content format = plain text JSON only (no file upload). PDF/DOCX out of scope for P0.
- D02: Chunk strategy = fixed-size 512 tokens, 50-token overlap. Env vars: CHUNK_SIZE, CHUNK_OVERLAP.
- D03: Access control = RBAC write permission (not admin-only, not open). Bots need group assignment.
- D04: Max content = MAX_DOC_CHARS=100000 chars. Reject (413), never truncate.
- D05: Upload response = 202 async. Embedding is background task. Document status: processing → ready | failed.
- D06: Document management = GET list (paginated), GET by ID, DELETE. No PUT/PATCH.
- D07: Migration 006 needed — add `status` column to `documents` table.
- D08: bm25_indexer.py — CREATE NEW in this feature. Owns write path to content_fts; retriever owns read path.
- D09: Write permission = auth_type=="api_key" → write allowed; OIDC Bearer → read-only. OIDC write deferred to role-management feature post-MVP.
- D10: Embedder backend = Ollama /api/embeddings endpoint. Env var: EMBEDDING_MODEL (default: mxbai-embed-large).
- D11: Raw `content` NOT stored in `documents` table (DB bloat). Chunk text stored in `embeddings.text TEXT NOT NULL`. Migration 006 adds both `documents.status` + `embeddings.text`.
- D12: /reviewcode W1+W2+W3 fixed before approval. A003 compliant (LanguageDetectionError propagates).

## Files Touched
| File | Action | Story |
|------|--------|-------|
| `backend/api/routes/documents.py` | CREATED | S001, S005 |
| `backend/rag/chunker.py` | CREATED | S002 |
| `backend/rag/embedder.py` | CREATED | S003 |
| `backend/rag/bm25_indexer.py` | CREATED | S004 |
| `backend/db/models/document.py` | MODIFIED — added `status` column | S005-db |
| `backend/db/models/embedding.py` | MODIFIED — added `text TEXT NOT NULL` column | S005-db |
| `backend/db/migrations/006_add_document_status_and_chunk_text.sql` | CREATED | S005-db |

## Results
- AC Coverage: 22/22 (100%)
- Tests: 61 new, 230 total pass, 9 pre-existing fails (unrelated)
- /reviewcode: APPROVED — 3 warnings fixed (W1 double verify_token, W2 httpx timeout=10.0, W3 A003 lang fallback)

## Deferred
- PDF/DOCX upload — post-P0
- OIDC write access — role-management feature
- Document PUT/PATCH — delete + re-upload pattern

## Rule Update Candidates
- PERF P006 (proposed): All httpx.AsyncClient must set timeout=10.0
- ARCH A007 (proposed): FastAPI auth — signature-level Depends(verify_token) only, no duplication in dependencies=[]

## Unblocks
- query-endpoint
- multilingual-rag-pipeline

## Report
`docs/document-ingestion/reports/document-ingestion.report.md`
