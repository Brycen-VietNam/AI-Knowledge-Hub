# Plan: document-ingestion
Generated: 2026-04-07 | Spec: v1 DRAFT | Checklist: PASS (WARN-approved)

---

## Layer 1 — Plan Summary

| Field | Value |
|-------|-------|
| Stories | 5 (S001–S005) |
| Sessions est. | 3 |
| Critical path | S005-db → S001 → S002 → S003 ∥ S004 |
| Token budget total | ~18k |
| Agents | db-agent, api-agent, rag-agent |

### Parallel Groups

```
G0 (no deps):     S005-db  — db-agent         [migration 006 + model update]
G1 (after G0):    S001     — api-agent         [POST /v1/documents route]
G2 (after G1):    S002     — rag-agent         [chunker.py]
G3 (after G2):    S003     — rag-agent  ┐      [embedder.py]
                  S004     — rag-agent  ┘      [bm25_indexer.py]  ← parallel-safe (different files)
G4 (after G3):    S005-api — api-agent         [GET/DELETE routes]
```

> Note: S005 is split into two sub-tasks:
> - **S005-db** (G0): migration + model — must run first, unblocks S001
> - **S005-api** (G4): GET/DELETE routes — runs last (needs status column + chunk_count query)

---

## Layer 2 — Per-Story Plan

---

### S005-db: Migration 006 + Document model update
Agent: **db-agent** | Group: G0 | Depends: none
Sequential: YES — must complete before any other story

**Files:**
| Action | Path |
|--------|------|
| CREATE | `backend/db/migrations/006_add_document_status.sql` |
| MODIFY | `backend/db/models/document.py` — add `status` column |

**Migration spec:**
```sql
-- 006_add_document_status.sql
ALTER TABLE documents
  ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'processing'
  CHECK (status IN ('processing', 'ready', 'failed'));

-- Rollback:
-- ALTER TABLE documents DROP COLUMN status;
```

**Model update:**
```python
# backend/db/models/document.py
status: Mapped[str] = mapped_column(String(20), default="processing")
```

**Test:** `pytest tests/db/test_document_model.py -v`
**Est. tokens:** ~1.5k
**Subagent dispatch:** YES (self-contained, no runtime deps)

---

### S001: POST /v1/documents — Upload & validate
Agent: **api-agent** | Group: G1 | Depends: S005-db (status column exists)
Sequential: YES (G1)

**Files:**
| Action | Path |
|--------|------|
| CREATE | `backend/api/routes/documents.py` |
| MODIFY | `backend/api/routes/__init__.py` — register router |

**Key logic:**
```python
@router.post("/v1/documents", dependencies=[Depends(verify_token)])
async def upload_document(body: DocumentUpload, current_user: AuthenticatedUser, bg: BackgroundTasks):
    # 1. auth_type gate: only api_key can write (D09 / WARN-3)
    if current_user.auth_type != "api_key":
        raise HTTPException(403, ...)
    # 2. validate: content length, lang ISO 639-1, empty check
    # 3. RBAC: verify current_user has write access to user_group_id
    # 4. INSERT Document(status="processing") → get doc_id
    # 5. bg.add_task(ingest_pipeline, doc_id)
    # 6. return 202 {doc_id, status: "processing"}
```

**Hard rules checked:**
- R003: `Depends(verify_token)` on route ✓
- R004: `/v1/documents` prefix ✓
- A005: structured error shape ✓
- D09: auth_type=="api_key" gate ✓
- C013: rate limit 20 req/min (existing middleware) ✓

**Test:** `pytest tests/api/test_documents_upload.py -v`
**Est. tokens:** ~3k
**Subagent dispatch:** YES

---

### S002: Text chunking & language detection
Agent: **rag-agent** | Group: G2 | Depends: S001 (ingest_pipeline callable defined)
Sequential: YES (G2)

**Files:**
| Action | Path |
|--------|------|
| CREATE | `backend/rag/chunker.py` |

**Key logic:**
```python
# backend/rag/chunker.py
def chunk_document(content: str, lang: str | None, doc_id: uuid) -> list[Chunk]:
    # 1. lang = detect_language(content) if not provided (C009)
    # 2. token_count = len(TokenizerFactory.get(lang).tokenize(text)) for CJK
    #                  len(text.split()) for latin
    # 3. sliding window: CHUNK_SIZE=512, CHUNK_OVERLAP=50 (env vars)
    # 4. discard empty chunks after strip
    # 5. return list[Chunk(doc_id, chunk_index, text, lang)]
```

**Env vars:** `CHUNK_SIZE` (default 512), `CHUNK_OVERLAP` (default 50)

**Hard rules checked:**
- R005: CJK token counting via TokenizerFactory ✓
- C009: auto-detect lang if not provided ✓
- P005: discard empty, no silent failures ✓

**Test:** `pytest tests/rag/test_chunker.py -v`
**Est. tokens:** ~2.5k
**Subagent dispatch:** YES

---

### S003: Batch embedding generation
Agent: **rag-agent** | Group: G3 | Depends: S002
Parallel-safe with: S004 (different files, S004 waits for S003 DB commit)

**Files:**
| Action | Path |
|--------|------|
| CREATE | `backend/rag/embedder.py` |

**Key logic:**
```python
# backend/rag/embedder.py
async def batch_embed(chunks: list[Chunk], batch_size: int = 32) -> list[Embedding]:
    # 1. split chunks into batches of batch_size (C012)
    # 2. for each batch: POST OLLAMA_BASE_URL/api/embeddings
    #    body: {"model": EMBEDDING_MODEL, "prompt": chunk.text}
    # 3. asyncio.gather for concurrent batch calls (> 32 chunks)
    # 4. on any failure: raise EmbedderError (caller sets status=failed)
    # 5. return list[Embedding(doc_id, chunk_index, lang, user_group_id, vector)]
```

**Env vars:** `OLLAMA_BASE_URL` (default `http://localhost:11434`), `EMBEDDING_MODEL` (default `mxbai-embed-large`)

**Hard rules checked:**
- C012: batch_size=32 minimum, no per-chunk loop ✓
- R002: user_group_id copied from Document, no PII in metadata ✓
- P002 (PERF): batch calls, not per-doc loop ✓

**On failure path:** caller (`ingest_pipeline`) catches `EmbedderError` → sets `document.status = "failed"`, logs, returns without partial insert.

**Test:** `pytest tests/rag/test_embedder.py -v`
**Est. tokens:** ~3k
**Subagent dispatch:** YES

---

### S004: BM25 index update (CJK-aware)
Agent: **rag-agent** | Group: G3 | Depends: S002 + S003 DB commit
Parallel-safe with: S003 (different files; S004 must wait for embeddings committed before updating status)

> Note: S003 and S004 share the same `ingest_pipeline` orchestration function. They are parallel at the *file-creation* level but S004 executes after S003 commits in the runtime pipeline.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `backend/rag/bm25_indexer.py` |

**Key logic:**
```python
# backend/rag/bm25_indexer.py
async def index_document(doc_id: uuid, chunks: list[Chunk], db: AsyncSession):
    # 1. for each chunk: tokens = TokenizerFactory.get(lang).tokenize(text)
    #    fallback: simple config + log warning if UnsupportedLanguageError (AC3)
    # 2. joined_tokens = " ".join(tokens)
    # 3. UPDATE documents SET content_fts = to_tsvector('simple', :tokens)
    #    WHERE id = :doc_id
    # 4. after commit: UPDATE documents SET status = 'ready' WHERE id = :doc_id
```

**Hard rules checked:**
- R005 / C005 / C006: TokenizerFactory per lang ✓
- S004 AC4: runs after embedding insert committed ✓
- S004 AC3: catch UnsupportedLanguageError → fallback + log warning ✓

**Test:** `pytest tests/rag/test_bm25_indexer.py -v`
**Est. tokens:** ~2.5k
**Subagent dispatch:** YES (parallel with S003 file creation)

---

### S005-api: GET list, GET by ID, DELETE routes
Agent: **api-agent** | Group: G4 | Depends: S003 + S004 (status="ready" pipeline complete)
Sequential: YES (G4 — last)

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `backend/api/routes/documents.py` — add GET + DELETE handlers |

**Key logic:**
```python
# GET /v1/documents (paginated, RBAC-filtered)
SELECT id, title, lang, user_group_id, status, created_at,
       (SELECT COUNT(*) FROM embeddings WHERE doc_id = d.id) AS chunk_count
FROM documents d
WHERE (user_group_id = ANY(:group_ids) OR user_group_id IS NULL)
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset

# GET /v1/documents/{id} — 404 if not found OR not in caller's groups (AC3, prevent enumeration)

# DELETE /v1/documents/{id} — 204; CASCADE handles embeddings
```

**Hard rules checked:**
- R001: RBAC WHERE clause at DB level ✓
- R003: `Depends(verify_token)` ✓
- R004: `/v1/documents` prefix ✓
- S005 AC3: 404 for inaccessible (not 403) — prevents enumeration ✓
- P004 (PERF): IN clause for chunk_count subquery, not N+1 ✓

**Test:** `pytest tests/api/test_documents_management.py -v`
**Est. tokens:** ~3k
**Subagent dispatch:** YES

---

## Execution Schedule

| Session | Group | Stories | Agent(s) | Notes |
|---------|-------|---------|----------|-------|
| 1 | G0 | S005-db | db-agent | Migration first — unblocks all |
| 2 | G1 | S001 | api-agent | Route + background task dispatch |
| 2 | G2 | S002 | rag-agent | Chunker (after S001 interface defined) |
| 3 | G3 | S003 ∥ S004 | rag-agent | Embedder + BM25 indexer (parallel file creation) |
| 3 | G4 | S005-api | api-agent | GET/DELETE routes (after pipeline complete) |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Ollama not running in test env | Medium | S003 blocked | Mock `httpx.AsyncClient` in tests; integration test with real Ollama tagged `@pytest.mark.integration` |
| TokenizerFactory missing lang raises UnsupportedLanguageError in S004 | Low | BM25 index empty for unknown langs | AC3: catch + fallback to `simple` config + log warning |
| Background task failure not visible to caller | Medium | Doc stuck in `processing` | Status visible via GET /v1/documents/{id}; no webhook (Q6 default) |
| OIDC user bypasses write gate if auth_type check missed | Medium | Data integrity | WARN-3 mitigation: inline check in route handler, covered by test |
