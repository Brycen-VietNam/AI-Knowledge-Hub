# Plan: rbac-document-filter
Created: 2026-04-03 | Based on spec: v2 DRAFT | Checklist: WARN-APPROVED ✅

---

## LAYER 1 — Plan Summary

| Field | Value |
|-------|-------|
| Total stories | 5 |
| Sessions estimated | 2 |
| Critical path | S001 → S002 → (S003 ∥ S004) → S005 |
| Token budget total | ~18k tokens |

### Parallel Execution Groups
```
G1 (start immediately):
  S001 — db-agent    — Migration 005: DROP NOT NULL + partial indexes

G2 (after G1):
  S002 — rag-agent   — Retriever RBAC filter (dense + BM25)

G3 (after G2, run together):
  S003 — rag-agent   — Test suite: RBAC access matrix
  S004 — db-agent    — ORM model update: nullable user_group_id

G4 (after G3):
  S005 — api-agent   — Wire RBAC into /v1/query endpoint
```

### Agent Assignments
| Agent | Stories | Can start |
|-------|---------|-----------|
| db-agent | S001, S004 | S001 immediately; S004 after S002 |
| rag-agent | S002, S003 | S002 after S001; S003 after S002 |
| api-agent | S005 | after S003 + S004 both done |

### Risk
| Risk | Mitigation |
|------|------------|
| S001 ALTER COLUMN on live DB with existing rows | `DROP NOT NULL` does not touch data — safe, no default needed |
| Rollback assumes group_id=1 exists | Migration comment documents: use `(SELECT MIN(id) FROM user_groups)` as safe fallback |
| OIDC group name → ID cache stale | TTL=60s; cache miss falls back to live DB lookup |
| `api_keys.user_group_ids` empty array edge case | Empty `ANY([])` → FALSE in PostgreSQL; `OR IS NULL` covers public docs correctly |
| S004/S003 parallel file conflict | S003 touches `tests/rag/`, S004 touches `backend/db/models/` + `tests/db/` — no file overlap |

---

## LAYER 2 — Story Plans

---

### S001: Migration 005 — DROP NOT NULL on user_group_id
**Agent**: db-agent
**Parallel group**: G1 (start immediately)
**Depends on**: none

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/db/migrations/005_nullable_user_group_id.sql` |

**Subagent dispatch**: YES (self-contained DDL, no code dependencies)
**Est. tokens**: ~2k
**Test entry**: `psql -c "\d documents" && psql -c "\d embeddings"` (verify nullable)

**Story-specific notes**
- `ALTER COLUMN DROP NOT NULL` is safe on a live DB with existing rows — no data migration needed.
- Two partial indexes: `idx_documents_public ON documents(id) WHERE user_group_id IS NULL` and `idx_embeddings_public ON embeddings(doc_id) WHERE user_group_id IS NULL`.
- Rollback: update NULLs to `(SELECT MIN(id) FROM user_groups)` BEFORE restoring NOT NULL constraint.
- FK `documents.user_group_id → user_groups.id` is preserved — DROP NOT NULL does not drop FK.
- Do NOT add `SET NOT NULL DEFAULT` — that would require a table rewrite.

**Outputs expected**
- [ ] `005_nullable_user_group_id.sql` with FORWARD + ROLLBACK sections
- [ ] Both tables show `nullable=YES` after migration

---

### S002: Retriever RBAC filter — dense + BM25
**Agent**: rag-agent
**Parallel group**: G2 (after S001)
**Depends on**: S001 (nullable columns must exist before retriever is coded to filter them)

**Files**
| Action | Path |
|--------|------|
| MODIFY | `backend/rag/retriever.py` |

**Subagent dispatch**: YES (isolated rag-agent scope)
**Est. tokens**: ~4k
**Test entry**: `pytest tests/rag/test_retriever_rbac.py` (written in S003)

**Story-specific notes**
- Signature: `async def retrieve(query_embedding: list[float], user_group_ids: list[int], top_k: int = 10) -> list[RetrievedDocument]`
- Dense SQL: `WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)` — no JOIN, pure embeddings table.
- BM25 SQL: `WHERE (d.user_group_id = ANY(:group_ids) OR d.user_group_id IS NULL)` — documents table (BM25 uses `content_fts`).
- Empty `user_group_ids=[]` → `ANY([])` = FALSE → only `IS NULL` branch returns results (public-only mode). No special-casing needed.
- Wrap full call: `asyncio.wait_for(retrieve_inner(...), timeout=1.8)` → raise `QueryTimeoutError`.
- All SQL via `text()` with `.bindparams()` — zero f-string interpolation (SECURITY.md S001).
- Hybrid weights from env: `RAG_BM25_WEIGHT`, `RAG_DENSE_WEIGHT` (ARCH.md A004).

**Outputs expected**
- [ ] `retrieve()` method with correct SQL WHERE filter on both paths
- [ ] `asyncio.wait_for` timeout wrapper
- [ ] No string interpolation in SQL

---

### S003: Retriever test suite — RBAC access matrix
**Agent**: rag-agent
**Parallel group**: G3 (after S002, parallel with S004)
**Depends on**: S002 (tests exercise the retriever implementation)

**Files**
| Action | Path |
|--------|------|
| CREATE | `tests/rag/test_retriever_rbac.py` |

**Subagent dispatch**: YES (test-only, isolated)
**Est. tokens**: ~4k
**Test entry**: `pytest tests/rag/test_retriever_rbac.py -v`

**Story-specific notes**
- Fixtures: 3 user_groups + embeddings seeded as: 5 per group (user_group_id set) + 3 public (user_group_id NULL).
- Test classes: `TestGroupFilter`, `TestPublicAccess`, `TestHybridRBAC`, `TestConcurrency`, `TestPerformance`.
- Concurrency test: `asyncio.gather(*[retrieve(...) for _ in range(10)])` with different group_ids → verify no cross-contamination.
- Performance test: `@pytest.mark.performance` — 10k embeddings, user has access to 1k, assert p95 < 1800ms.
- Use `pytest-asyncio` with `asyncio_mode = "auto"`.
- No mocking of SQL — tests must hit real PostgreSQL (WARN from checklist: integration, not mock).

**Outputs expected**
- [ ] 10 test methods covering full AC matrix (AC1–AC10)
- [ ] Parameterized group filter test
- [ ] Performance test with `@pytest.mark.performance`

---

### S004: ORM model update — nullable user_group_id
**Agent**: db-agent
**Parallel group**: G3 (after S002, parallel with S003)
**Depends on**: S002 (models must match the retriever's nullable assumption; S001 migration must be applied)

**Files**
| Action | Path |
|--------|------|
| MODIFY | `backend/db/models/document.py` |
| MODIFY | `backend/db/models/embedding.py` |
| MODIFY | `tests/db/test_models.py` |

**Subagent dispatch**: YES (db-agent scope, no rag/api files)
**Est. tokens**: ~2k
**Test entry**: `pytest tests/db/test_models.py -v`

**Story-specific notes**
- `document.py` line ~20: change `Mapped[int]` → `Mapped[Optional[int]]`; add `nullable=True` to `mapped_column`.
- `embedding.py` line ~22: same — `Mapped[Optional[int]]`; keep `# denormalized, no FK (R001)` comment.
- `test_models.py`: existing NOT NULL tests must be inverted — NULL value must now be accepted.
- FK on `document.user_group_id` is preserved; only nullability changes.
- `from typing import Optional` import check in both model files.

**Outputs expected**
- [ ] Both models: `Mapped[Optional[int]]` with `nullable=True`
- [ ] Updated tests accepting NULL

---

### S005: Wire RBAC into /v1/query endpoint
**Agent**: api-agent
**Parallel group**: G4 (after S003 + S004)
**Depends on**: S003 (retriever tested), S004 (models correct)

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/api/__init__.py` |
| CREATE | `backend/api/routes/__init__.py` |
| CREATE | `backend/api/routes/query.py` |
| CREATE | `tests/api/test_query_rbac.py` |

**Subagent dispatch**: YES (api-agent scope, after G3 complete)
**Est. tokens**: ~6k
**Test entry**: `pytest tests/api/test_query_rbac.py -v`

**Story-specific notes**
- Route: `POST /v1/query` with `dependencies=[Depends(verify_token)]` (HARD.md R003, R004).
- Extract groups from `AuthenticatedUser`:
  - OIDC: `groups` = `list[str]` → `SELECT id FROM user_groups WHERE name = ANY(:names)` with TTL=60s cache.
  - API-key: `api_keys.user_group_ids` = `list[int]` → pass directly.
- Audit log: `background_tasks.add_task(audit_log.write(user_id, doc_ids, query_hash, timestamp, public_only))` — non-blocking.
- `request_id = str(uuid4())` at entry; propagate to response + audit.
- Response: `{"request_id": ..., "results": [...]}` — `is_public: True` if chunk `user_group_id IS NULL`.
- 0-group users: `user_group_ids=[]` → empty results → `200 {"results": []}` (not 403).
- Auth pattern: `verify_token` from `backend/auth/dependencies.py` (auth-api-key-oidc DONE ✅).
- End-to-end latency budget: 1800ms retrieval + async audit = fits within 2000ms SLA (HARD.md R007).

**Outputs expected**
- [ ] `backend/api/routes/query.py` with POST /v1/query
- [ ] OIDC group name→ID lookup with cache
- [ ] Async audit log background task
- [ ] Tests: OIDC path + API-key path + 0-group + 401 unauthenticated

---

## Dependency Graph

```
S001 (db-agent)
  └─► S002 (rag-agent)
        ├─► S003 (rag-agent) ─┐
        └─► S004 (db-agent)  ─┴─► S005 (api-agent)
```

## Implementation Order

| Step | Stories | Gate |
|------|---------|------|
| 1 | S001 | Migration applied to dev DB |
| 2 | S002 | Retriever code review passes |
| 3 | S003 + S004 | All tests green (parallel) |
| 4 | S005 | Full integration test green |
