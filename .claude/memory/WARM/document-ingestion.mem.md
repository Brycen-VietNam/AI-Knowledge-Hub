# WARM Memory: document-ingestion
Created: 2026-04-06 | Status: REVIEW_APPROVED | Phase: /reviewcode DONE 2026-04-07 → next: /report

---

## Spec Summary
POST /v1/documents ingestion pipeline — upload JSON text, chunk, batch embed, BM25 index.
5 stories, 22 ACs, all traced.

## Key Decisions
- D01: Content format = plain text JSON only (no file upload). PDF/DOCX out of scope for P0.
- D02: Chunk strategy = fixed-size 512 tokens, 50-token overlap. Env vars: CHUNK_SIZE, CHUNK_OVERLAP.
- D03: Access control = RBAC write permission (not admin-only, not open). Bots need group assignment.
- D04: Max content = MAX_DOC_CHARS=100000 chars. Reject (413), never truncate.
- D05: Upload response = 202 async. Embedding is background task. Document status: processing → ready | failed.
- D06: Document management = GET list (paginated), GET by ID, DELETE. No PUT/PATCH.
- D07: Migration 006 needed — add `status` column to `documents` table.
- D08: bm25_indexer.py — CREATE NEW in this feature (not a cjk-tokenizer leftover). Owns write path to content_fts; retriever owns read path.
- D09: Write permission = auth_type=="api_key" → write allowed; OIDC Bearer → read-only. No schema change needed. OIDC write access deferred to role-management feature post-MVP.
- D10: Embedder backend = Ollama /api/embeddings endpoint. Env var: EMBEDDING_MODEL (default: mxbai-embed-large or nomic-embed-text). Consistent with llm-provider adapter pattern. No sentence-transformers dependency.
- D11: Raw `content` NOT stored in `documents` table (DB bloat). Chunk text stored in `embeddings.text TEXT NOT NULL` instead. `content` passed through memory in background task: `ingest_pipeline(doc_id, content)`. Migration 006 adds both `documents.status` + `embeddings.text`.

## Files to Touch
| File | Action | Story |
|------|--------|-------|
| `backend/api/routes/documents.py` | CREATE | S001, S005 |
| `backend/rag/chunker.py` | CREATE | S002 |
| `backend/rag/embedder.py` | CREATE — Ollama /api/embeddings client (D10) | S003 |
| `backend/rag/bm25_indexer.py` | CREATE — new file, owns content_fts write path (D08) | S004 |
| `backend/db/models/document.py` | EXTEND — add status column | S001, S005 |
| `backend/db/migrations/006_add_document_status_and_chunk_text.sql` | CREATE — status + embeddings.text (D11) | S005-db |

## Open Questions
- None. Q1–Q3 (blockers) resolved 2026-04-06. Q4–Q8 (SHOULD) have defaults in clarify file.

## Assumptions (confirmed)
- A1: JSON plain text only ✅
- A2: Fixed chunk size, configurable env vars ✅
- A3: RBAC write permission check ✅
- A4: Reject > MAX_DOC_CHARS ✅
- A5: GET list + GET by ID + DELETE ✅

## Sync Log
- 2026-04-07 /sync #026: /reviewcode warnings fixed (W1+W2+W3), review APPROVED, D12 captured, phase → /report
- 2026-04-07 /sync #025: /analyze DONE, D11 captured (embeddings.text), 4 gaps documented, tasks S005-db/S001/S003 updated
- 2026-04-07 /sync #023: /plan DONE, plan file saved, execution groups G0–G4 defined, no new decisions
- 2026-04-07 /sync #022: /checklist PASS, WARN-1/2/3 approved by lb_mui, checklist.md saved
- 2026-04-06 /sync #021: /clarify complete, D08–D10 captured (Q1–Q3 resolved), clarify file written
- 2026-04-06 /sync #020: /specify complete, D01–D07 captured, 22 ACs traced, 3 output files written

## Phase Checklist
- [x] /specify — DONE 2026-04-06
- [x] /clarify — DONE 2026-04-06 (3 blockers resolved: D08, D09, D10)
- [x] /checklist — PASS 2026-04-07 (WARN-1/2/3 approved by lb_mui)
- [x] /plan — DONE 2026-04-07 → `docs/document-ingestion/plan/document-ingestion.plan.md`
- [x] /tasks — DONE 2026-04-07 → 5 task files, 16 tasks total
- [x] /analyze — DONE 2026-04-07 → `docs/document-ingestion/tasks/all-stories.analysis.md`
- [x] /implement — DONE 2026-04-07 → 61 new tests, 230 pass, 9 pre-existing fails
- [x] /reviewcode — APPROVED 2026-04-07 (3 warnings fixed: W1 double verify_token, W2 httpx timeout=10.0, W3 A003 compliant)
- [ ] /report
