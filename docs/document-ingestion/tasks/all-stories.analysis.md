# Analysis: document-ingestion — All Stories (S005-db, S001, S002, S003, S004, S005-api)
Created: 2026-04-07 | Depth: shallow | Files scanned: 9

---

## Stories Covered
| Story | Agent | Tasks | Status |
|-------|-------|-------|--------|
| S005-db | db-agent | T001, T002 | TODO |
| S001 | api-agent | T001–T005 | TODO |
| S002 | rag-agent | T001–T003 | TODO |
| S003 | rag-agent | T001–T003 | TODO |
| S004 | rag-agent | T001–T003 | TODO |
| S005-api | api-agent | T001–T003 | TODO |

---

## Code Map (existing relevant code)

### `backend/db/models/document.py` (25 lines)
```python
class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    lang: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    user_group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_groups.id"), nullable=True)
    created_at: Mapped[datetime] = ...
    updated_at: Mapped[datetime] = ...
    content_fts: Mapped[str | None] = ...  # nullable, rag-agent populates post-ingestion
    # ← ADD: status: Mapped[str] = mapped_column(String(20), default="processing")  [S005-db-T002]
    # ← NO content column — D11: raw content NOT stored (DB bloat), chunk text in embeddings.text
```
**Gap**: `content` column is absent from the ORM model. S001-T005 inserts `Document(title, content, lang, ...)` — but no `content` field exists. Check migration 001 to confirm.

### `backend/db/models/embedding.py` (26 lines)
```python
class Embedding(Base):
    __tablename__ = "embeddings"
    id: Mapped[uuid.UUID]
    doc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), ...)
    chunk_index: Mapped[int]
    lang: Mapped[str] = mapped_column(CHAR(2), ...)
    user_group_id: Mapped[Optional[int]] = nullable=True   # denormalized, no FK — R001 ✅
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=True)
    # ← ADD: text: Mapped[str] = mapped_column(Text(), nullable=False)  [S005-db-T002, D11]
    # NOTE: No cascade issue — FK ondelete="CASCADE" present ✅
```

### `backend/api/routes/query.py` — patterns to follow
- Auth dependency pattern: `user: Annotated[AuthenticatedUser, Depends(verify_token)]`
- DB dependency pattern: `db: Annotated[AsyncSession, Depends(get_db)]`
- Error response shape: `{"error": {"code": "...", "message": "...", "request_id": "..."}}` (A005) ✅
- BackgroundTasks pattern: `background_tasks.add_task(fn, arg1, arg2)` ✅
- JSONResponse for 202: `JSONResponse(status_code=202, content={...})` ✅
- asyncio.wait_for timeout pattern at L112 ✅

### `backend/api/routes/__init__.py`
- File is 1 line (empty). Router registration for `documents.py` must be done in the app factory, not here.
- Check `backend/api/app.py` or `backend/main.py` for router include pattern.

### `backend/auth/types.py` — AuthenticatedUser fields
```python
@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: uuid.UUID
    user_group_ids: list[int]          # used for RBAC WHERE in S001/S005-api
    auth_type: Literal["api_key", "oidc"]  # used for write gate in S001-T002
```

### `backend/rag/tokenizers/factory.py` — CJK tokenizer interface
```python
class TokenizerFactory:
    @classmethod
    def get(cls, lang: str) -> BaseTokenizer:   # raises UnsupportedLanguageError if unsupported
        ...
    # Supported: "ja", "ko", "zh", "vi", "en"
    # en → WhitespaceTokenizer (not CJK path — S002-T002 should check lang in ["ja","ko","zh","vi"])
```

### `backend/rag/tokenizers/detection.py` — detect_language signature
```python
def detect_language(text: str) -> str:
    # Returns: "ja" | "ko" | "zh" | "vi" | "en"
    # Raises: LanguageDetectionError (not UnsupportedLanguageError) if text < 8 chars or low confidence
    # S002-T001: _resolve_lang must handle LanguageDetectionError gracefully
```

### `backend/db/migrations/005_nullable_user_group_id.sql`
- Last migration is 005. Migration 006 is next (S005-db-T001) ✅
- Pattern confirmed: forward SQL + rollback as comments at bottom ✅

---

## Patterns to Follow

| Pattern | Source |
|---------|--------|
| Route auth dependency | `query.py:96-100` — `Depends(verify_token)` + `Depends(get_db)` |
| Error shape (A005) | `query.py:125-130` — `{"error": {"code": ..., "message": ..., "request_id": ...}}` |
| BackgroundTasks | `query.py:132` — `background_tasks.add_task(fn, args)` |
| Async HTTP client | `rag/llm.py` (llm-provider) — `httpx.AsyncClient` pattern to follow for embedder |
| Migration convention | `005_nullable_user_group_id.sql` — numbered file, forward + rollback comment |
| ORM field syntax | `embedding.py` — `Mapped[Optional[int]] = mapped_column(...)` |
| SQLAlchemy text() | confirmed pattern from SECURITY.md S001 — `text(...).bindparams(...)` |
| asyncio.gather | S003-T002 — consistent with llm-provider pattern |

---

## Conflicts / Gaps Found

### ✅ RESOLVED — `content` column: Decision D11 — store chunk text in `embeddings.text`, not raw content in `documents`

**Decision D11** (2026-04-07, lb_mui): Do NOT store raw `content` in `documents` table — DB bloat.
Store chunk text (`text TEXT NOT NULL`) in `embeddings` table instead (Option B).

Rationale:
- RAG retrieval only needs chunk text, not the full original document
- `embeddings.text` is what `query.py` reads via `RetrievedDocument.content`
- Raw `content` passed through memory in background task — never persisted to `documents`
- `content_fts` (TSVECTOR) is the BM25 index — not recoverable as text, separate concern

**Migration 006 scope** (S005-db-T001) — updated:
- `ALTER TABLE documents ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'processing'` + CHECK constraint
- `ALTER TABLE embeddings ADD COLUMN text TEXT NOT NULL`

**ORM updates** (S005-db-T002) — updated:
- `Document`: add `status: Mapped[str]` only
- `Embedding`: add `text: Mapped[str] = mapped_column(Text(), nullable=False)`

**S001-T005 update**: `DocumentUpload.content` received in request body, passed to `ingest_pipeline(doc_id, content)` as argument — NOT inserted into `documents`.

### ⚠️ No app factory exists — router registration approach TBD

`backend/api/__init__.py` is empty (1 line). `backend/api/app.py` and `backend/main.py` do not exist.
`query.py` router is not registered anywhere yet — this is a pre-existing gap, not introduced by this feature.

**Action for S001-T001**: Create `backend/api/app.py` as the FastAPI application factory that includes both `query.router` and `documents.router`. Alternatively, confirm with lb_mui whether a standalone `app.py` is the intended pattern before implementing.

### ⚠️ `detect_language` raises `LanguageDetectionError`, not `UnsupportedLanguageError`

S002-T001 `_resolve_lang` must import and catch `LanguageDetectionError` from `backend.rag.tokenizers.exceptions`, not a generic exception. Task description doesn't specify this — easy miss.

### ⚠️ `TokenizerFactory.get("en")` returns `WhitespaceTokenizer` — not an error

S002-T002 chunker CJK branch check: use `lang in {"ja", "ko", "zh", "vi"}` not `TokenizerFactory.get(lang)` as the branch condition (avoids calling factory for latin text unnecessarily). Task spec says "CJK langs (ja/ko/zh/vi) → TokenizerFactory" — correct, just ensure latin path uses `text.split()` directly.

### ⚠️ S004-T002 `to_tsvector('simple', ...)` — must match retriever's tsquery config

Migration 003 added `content_fts`. Check retriever uses `to_tsquery('simple', ...)` — confirmed in task as pattern requirement. `simple` config is language-agnostic, correct for multilingual CJK tokens.

### ✅ No existing `bm25_indexer.py` or `chunker.py` or `embedder.py` — clean creates

Confirmed: none of these files exist yet. All are clean creates.

### ✅ No existing `backend/api/routes/documents.py` — clean create

`query.py` and `__init__.py` only. Clean create for `documents.py`.

### ✅ `ondelete="CASCADE"` confirmed in `embedding.py`

S005-api-T003 DELETE: no explicit cascade logic needed, FK handles it ✅

### ✅ Migration 006 is the correct next number

Last migration is 005. File will be `006_add_document_status_and_chunk_text.sql` (covers both `documents.status` + `embeddings.text` — D11) ✅

---

## RBAC Analysis

| Story | RBAC Location | Method | Rule |
|-------|--------------|--------|------|
| S001-T004 | Route handler — `body.user_group_id not in current_user.user_group_ids` | Python check at write time | R001 ✅ (write path — no retrieval) |
| S005-api-T001 | SQL WHERE clause — `user_group_id = ANY(:group_ids) OR user_group_id IS NULL` | pgvector/PG query | R001 ✅ |
| S005-api-T002 | SQL WHERE clause — same as T001 | Single query | R001 ✅ (+ enumeration protection via 404) |
| S005-api-T003 | SQL WHERE clause — DELETE with same RBAC filter | No fetch-then-delete | R001 ✅ P004 ✅ |

---

## Implementation Order (respecting cross-story dependencies)

```
G0: S005-db-T001  (migration 006) — prerequisite for all
G1: S005-db-T002  (Document model — add status)
    S001-T001     (router scaffold + DocumentUpload schema)
G2: S001-T002     (auth_type write gate)
G3: S001-T003 ∥ S001-T004    (input validation ∥ RBAC check)
    S002-T001     (Chunk dataclass + lang detection wrapper)
    S003-T001     (OllamaEmbedder + EmbedderError)
    S004-T001     (bm25_indexer scaffold + tokenize_for_fts)
G4: S001-T005     (DB insert + BackgroundTasks dispatch)
    S002-T002     (sliding window chunker)
    S003-T002     (batch_embed + asyncio.gather)
    S004-T002     (update_fts query)
    S005-api-T001 ∥ S005-api-T002  (GET list ∥ GET by ID)
G5: S002-T003     (empty chunk discard + pipeline wire-up)
    S003-T003     (embedding DB insert + failure path)
    S004-T003     (status=ready + pipeline wire-up)
    S005-api-T003 (DELETE)
```

---

## Recommended Pre-Implementation Actions

1. **Migration 006 scope confirmed (D11)**: `documents.status` + `embeddings.text` in one migration. File: `006_add_document_status_and_chunk_text.sql`.
2. **Check app factory**: `backend/api/app.py` and `backend/main.py` absent — create `app.py` in S001-T001, include `query.router` + `documents.router`.
3. **Check `backend/rag/llm/ollama.py`** for `httpx.AsyncClient` pattern — S003 `OllamaEmbedder` should follow exactly.

---

## Token Budget
Analysis saved: `docs/document-ingestion/tasks/all-stories.analysis.md`
Estimated total implementation: ~16 tasks, ~450 lines code + ~350 lines tests
