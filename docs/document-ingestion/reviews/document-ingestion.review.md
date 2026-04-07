## Code Review: document-ingestion — Full Feature
Level: security | Date: 2026-04-07 | Reviewer: Claude (opus)

Stories covered: S001 · S002 · S003 · S004 · S005-db · S005-api

---

### S001 — POST /v1/documents (Upload & validate)

#### Task Review Criteria
- [x] T001: `DocumentUpload` fields: `title`, `content`, `lang`, `user_group_id` — all present (L41–45)
- [x] T001: `title` max_length=500 (L42, `Field(..., max_length=500)`)
- [x] T001: Route `@router.post("/v1/documents", dependencies=[Depends(verify_token)])` (L126)
- [x] T001: R003 + R004 satisfied
- [x] T001: Router registered in `app.py` (L6–7 of `app.py`)
- [x] T002: auth_type check is FIRST logic in handler (L136)
- [x] T002: Error shape A005 compliant (L138–140)
- [x] T002: OIDC → 403; API-key → not 403 — tests present
- [x] T003: `MAX_DOC_CHARS = int(os.getenv("MAX_DOC_CHARS", "100000"))` (L31)
- [x] T003: 413 for oversized, 422 for empty/invalid lang (L143–157)
- [x] T003: Error codes `DOC_TOO_LARGE`, `INVALID_INPUT` with `request_id`
- [x] T003: All 4 validation tests present
- [x] T004: `body.user_group_id not in user.user_group_ids` → 403 (L160–164)
- [x] T004: `user_group_id=None` skips group check
- [x] T004: All 3 RBAC tests present
- [x] T005: Response code 202 (L179)
- [x] T005: Response body `{"doc_id": "<uuid>", "status": "processing"}` (L180–182)
- [x] T005: `content` NOT in `Document(...)` constructor — only `title, lang, user_group_id, status` (L167–172)
- [x] T005: `BackgroundTasks.add_task(ingest_pipeline, doc.id, body.content)` (L177)
- [x] T005: DB insert via ORM — no string interpolation (L167–175)
- [x] T005: All success-path tests present, including `ingest_pipeline` called-once assert

---

### S002 — Text chunker (chunker.py)

#### Task Review Criteria
- [x] T001: `Chunk` dataclass: `doc_id: uuid.UUID`, `chunk_index: int`, `text: str`, `lang: str` (L20–25)
- [x] T001: `_resolve_lang` calls `detect_language()` only when `provided_lang` falsy (L33–34)
- [x] T001: Imports `detect_language` + `LanguageDetectionError` correctly
- [x] T002: Sliding window with `CHUNK_SIZE`, `CHUNK_OVERLAP` from env (L15–16)
- [x] T002: CJK langs use `TokenizerFactory.get(lang)` (L44–45), latin uses `text.split()` (L46)
- [x] T002: CJK text joined with `""`, latin with `" "` (L68–70)
- [x] T003: Empty/whitespace-only chunks discarded via `if text.strip()` (L73)

---

### S003 — Batch embedding (embedder.py)

#### Task Review Criteria
- [x] T001: `OLLAMA_BASE_URL = os.getenv(...)` default `http://localhost:11434` (L16)
- [x] T001: `EMBEDDING_MODEL = os.getenv(...)` default `mxbai-embed-large` (L17)
- [x] T001: Uses `httpx.AsyncClient` (L34)
- [x] T001: `EmbedderError` raised on non-200 (L39–40)
- [x] T002: `batch_size` defaults to 32 (L43)
- [x] T002: `asyncio.gather` for concurrent calls within batch (L48)
- [x] T002: Output preserves order (`results.extend(batch_vectors)`)
- [x] T003: `insert_embeddings` uses `db.add_all` — single bulk insert, no N+1 (L76–79)
- [x] T003: R002: `user_group_id` taken from `doc`, never from chunk/request (L71)
- [x] T003: D11: `text=chunk.text` stored in `Embedding.text` (L70)

---

### S004 — BM25 indexer (bm25_indexer.py)

#### Task Review Criteria
- [x] T001: CJK langs → `TokenizerFactory.get(lang)` (L31–33)
- [x] T001: `UnsupportedLanguageError` caught → warning logged + fallback to raw text (L34–36)
- [x] T001: Latin/other → `text.split()` (L37)
- [x] T002: Single `UPDATE` — not per-chunk (L52–57)
- [x] T002: `text().bindparams(tokens=..., doc_id=...)` — no f-string interpolation (L52–57)
- [x] T003: `status = 'ready'` set in same UPDATE as `content_fts` (L53–55)
- [x] T003: `await db.commit()` after UPDATE (L58)

---

### S005-db — Migration 006

#### Task Review Criteria
- [x] `documents.status VARCHAR(20) NOT NULL DEFAULT 'processing'` with CHECK constraint
- [x] `embeddings.text TEXT NOT NULL` with `DEFAULT ''` then `DROP DEFAULT`
- [x] Rollback section present and correct
- [x] Migration number 006 — in sequence

---

### S005-api — GET list, GET by ID, DELETE

#### Task Review Criteria
- [x] T001: RBAC at SQL WHERE `user_group_id = ANY(:group_ids) OR user_group_id IS NULL` (L210–211)
- [x] T001: `limit > 100` → 422 (L198–202)
- [x] T001: `ORDER BY created_at DESC` (L212)
- [x] T001: `chunk_count` via subquery — no N+1 (L208)
- [x] T001: `Depends(verify_token)` on route (L189)
- [x] T002: Single query with RBAC in WHERE, returns 404 for both not-found and unauthorized (L252–258)
- [x] T002: `chunk_count` via same subquery pattern (L253–255)
- [x] T003: RBAC in WHERE clause of DELETE via `RETURNING id` pattern (L291–296)
- [x] T003: 204 on success (L307), 404 if not deleted (L300–303)
- [x] T003: `await db.commit()` only on successful delete (L306)

---

### Full Level Checks

- [x] Error handling: `EmbedderError` caught in `ingest_pipeline`, doc set to `failed` (documents.py L96–100)
- [x] Logging: `_logger.error("ingest_pipeline: ...", doc_id, exc)` — contextual (documents.py L97)
- [x] No magic numbers: `MAX_DOC_CHARS`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `OLLAMA_BASE_URL`, `EMBEDDING_MODEL` all env-configurable
- [x] Docstrings on all new public functions: `ingest_pipeline`, `chunk_document`, `_resolve_lang`, `batch_embed`, `insert_embeddings`, `tokenize_for_fts`, `update_fts`
- [x] No dead commented-out code

---

### Security Level Checks

- [x] R001: RBAC WHERE clause present on all read/delete paths (`ANY(:group_ids)` — documents.py L210, L257, L294)
- [x] R002: Embedding metadata = `{doc_id, lang, user_group_id, chunk_index, text}` only — no PII (embedder.py L66–76)
- [x] R003: `verify_token()` on all 4 routes (L126, L189, L243, L282)
- [x] R004: All routes `/v1/documents[/{id}]` — prefix correct
- [x] S001: All SQL via `text().bindparams()` — zero f-string interpolation (documents.py L207–214, L252–258, L291–297; bm25_indexer.py L52–57)
- [x] S005: All config via `os.getenv()` — no hardcoded URLs or secrets
- [x] R006: Spec explicitly excludes audit log from upload/management endpoints — required at retrieval only (spec L80). N/A for this feature.

---

### Issues Found

#### ⚠️ WARNING-1 — Double `verify_token` dependency (minor inefficiency)
All 4 routes declare `verify_token` **twice**: once in `dependencies=[Depends(verify_token)]` and once as `user: Annotated[AuthenticatedUser, Depends(verify_token)]` in the function signature (e.g., L126–130).

FastAPI deduplicates `Depends` by identity so this is **not a security gap**, but it triggers two dependency resolution calls per request (two token verifications).

**Fix**: Remove the `dependencies=[Depends(verify_token)]` kwarg; the signature-level `Depends(verify_token)` is sufficient and returns the user object.

```python
# Before (L126–131):
@router.post("/v1/documents", dependencies=[Depends(verify_token)])
async def upload_document(
    ...
    user: Annotated[AuthenticatedUser, Depends(verify_token)],

# After:
@router.post("/v1/documents")
async def upload_document(
    ...
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
```

Applies to all 4 routes (L126, L189, L243, L282).

#### ⚠️ WARNING-2 — httpx.AsyncClient has no timeout (embedder.py L34)
`httpx.AsyncClient()` is created without a timeout. If Ollama is unresponsive, `batch_embed` will hang indefinitely, violating P001 (p95 < 2000ms / timeout 1800ms).

**Fix**:
```python
async with httpx.AsyncClient(timeout=10.0) as client:
```
10 s is a reasonable per-chunk timeout; the ingest pipeline is already async/background so it won't block the 202 response, but hung tasks waste resources.

#### ⚠️ WARNING-3 — `_resolve_lang` fallback hardcodes `"en"` (chunker.py L38)
When `LanguageDetectionError` is raised, the function falls back to `"en"`. ARCH rule A003 states: _"Never hardcode `lang="en"` as fallback."_

This is a soft violation (detection failure path only; the non-error path correctly uses the provided/detected lang), but it contradicts A003.

**Fix**: raise a `ChunkerError` or pass `None` and let the caller decide, or at minimum document this as a conscious exception to A003 with a comment.

---

### Suggested test (for WARNING-2)
```python
@pytest.mark.asyncio
async def test_embed_one_timeout():
    """Ollama timeout must raise EmbedderError, not hang."""
    embedder = OllamaEmbedder()
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )
        with pytest.raises(EmbedderError):
            await embedder._embed_one("test")
```

---

### Verdict

**[ ] APPROVED &nbsp; [x] CHANGES REQUIRED &nbsp; [ ] REJECTED**

Blockers: **0** — no hard blockers.
Warnings: **3** — all should be fixed before merge but do not block.

- WARNING-1: double `verify_token` — low risk, easy fix, all 4 routes
- WARNING-2: missing httpx timeout — medium risk for production stability
- WARNING-3: hardcoded `"en"` fallback — contradicts A003, low impact

Recommendation: fix W1 + W2 in a follow-up commit; W3 document or fix before multilingual-rag-pipeline story where detection correctness becomes critical.
