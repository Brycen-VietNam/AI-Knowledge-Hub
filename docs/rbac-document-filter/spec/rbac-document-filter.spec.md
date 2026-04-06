# Spec: rbac-document-filter
Created: 2026-04-02 | Author: Claude Code | Status: DRAFT
Epic: auth | Priority: P0

---

## LAYER 1 — Summary

| Field | Value |
|-------|-------|
| Epic | auth |
| Priority | P0 |
| Story count | 5 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S003 ∥ S004 (after S002) |
| Blocking specs | document-ingestion, multilingual-rag-pipeline, query-endpoint |
| Blocked by | auth-api-key-oidc ✅ DONE, db-schema-embeddings ✅ DONE |
| Agents needed | db-agent, rag-agent, api-agent |

### Problem Statement
Authenticated users can currently retrieve any document regardless of group membership. RBAC must be enforced at the SQL WHERE clause level — before results are ranked or returned — to prevent cross-group data leakage. Some documents are public (`user_group_id IS NULL`) and visible to all authenticated users.

### Solution Summary
- Migration 004: relax `documents.user_group_id NOT NULL` → nullable (`NULL = public`)
- Also relax `embeddings.user_group_id NOT NULL` → nullable (denormalized mirror)
- Retriever filters on `embeddings.user_group_id` directly (no JOIN) for speed
- Filter: `WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)`
- User with 0 groups sees only NULL-group (public) documents — no 403

### Decisions (confirmed)
| ID | Decision | Date |
|----|----------|------|
| D01 | `user_group_id IS NULL` = public document (not `is_public` column) | 2026-04-02 |
| D02 | Filter on `embeddings.user_group_id` directly — no JOIN to documents (denormalized for speed) | 2026-04-02 |
| D03 | document-ingestion MUST write `user_group_id` to both `documents` and `embeddings` atomically | 2026-04-02 |
| D04 | 0-group users → empty results (not 403) | 2026-04-02 |

### Out of Scope
- Group membership management (auth-api-key-oidc scope)
- Document ownership transfer between groups
- Fine-grained per-document ACLs beyond group + public
- PostgreSQL RLS (deferred — app-level filter sufficient for P0)
- Enforcing D03 atomic write (document-ingestion feature scope)

---

## LAYER 2 — Story Detail

---

### S001: Migration 004 — relax NOT NULL on user_group_id (documents + embeddings)

**Role / Want / Value**
- As a: database architect
- I want: `user_group_id` to be nullable on both `documents` and `embeddings` tables
- So that: `NULL` can represent public documents without adding a separate column

**Acceptance Criteria**
- [ ] AC1: Migration file `backend/db/migrations/005_nullable_user_group_id.sql` created
- [ ] AC2: `ALTER TABLE documents ALTER COLUMN user_group_id DROP NOT NULL`
- [ ] AC3: `ALTER TABLE embeddings ALTER COLUMN user_group_id DROP NOT NULL`
- [ ] AC4: Existing FK constraint on `documents.user_group_id → user_groups.id` preserved
- [ ] AC5: Partial index `idx_documents_public` on `documents(id) WHERE user_group_id IS NULL` created
- [ ] AC6: Partial index `idx_embeddings_public` on `embeddings(doc_id) WHERE user_group_id IS NULL` created
- [ ] AC7: Rollback section at bottom restores `NOT NULL` constraints (idempotent)
- [ ] AC8: Migration verified on live PostgreSQL 17: `\d documents` and `\d embeddings` show nullable columns

**Database Schema**
```sql
-- 005_nullable_user_group_id.sql

-- FORWARD
ALTER TABLE documents ALTER COLUMN user_group_id DROP NOT NULL;
ALTER TABLE embeddings ALTER COLUMN user_group_id DROP NOT NULL;

CREATE INDEX idx_documents_public ON documents(id) WHERE user_group_id IS NULL;
CREATE INDEX idx_embeddings_public ON embeddings(doc_id) WHERE user_group_id IS NULL;

-- ROLLBACK:
-- DROP INDEX IF EXISTS idx_embeddings_public;
-- DROP INDEX IF EXISTS idx_documents_public;
-- UPDATE embeddings SET user_group_id = 1 WHERE user_group_id IS NULL; -- set safe default before constraint
-- UPDATE documents SET user_group_id = 1 WHERE user_group_id IS NULL;
-- ALTER TABLE embeddings ALTER COLUMN user_group_id SET NOT NULL;
-- ALTER TABLE documents ALTER COLUMN user_group_id SET NOT NULL;
```

**Auth Requirement**
- N/A (DDL migration)

**Non-functional**
- Latency: N/A
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
- Rollback requires a valid default group ID (e.g., 1) — document this assumption in migration comment.
- `ALTER COLUMN DROP NOT NULL` does not touch existing data — safe on live DB.
- Partial indexes optimize the `IS NULL` branch of the RBAC filter.

---

### S002: Retriever RBAC filter — dense + BM25 via embeddings.user_group_id

**Role / Want / Value**
- As a: RAG pipeline developer
- I want: retrievers to filter on `embeddings.user_group_id` at SQL WHERE level — no JOIN
- So that: RBAC is enforced without additional JOIN cost, meeting the 1800ms SLA

**Acceptance Criteria**
- [ ] AC1: `backend/rag/retriever.py` exposes `retrieve(query_embedding, user_group_ids, top_k)` async method
- [ ] AC2: Dense SQL: `WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)`
- [ ] AC3: BM25 SQL: `WHERE (d.user_group_id = ANY(:group_ids) OR d.user_group_id IS NULL)` on `documents` table (BM25 query starts from `documents.content_fts`)
- [ ] AC4: Filter applied BEFORE `ORDER BY` and `LIMIT` — never post-retrieval Python
- [ ] AC5: Hybrid merge operates only on pre-filtered result sets from both paths
- [ ] AC6: `user_group_ids=[]` → filter becomes `WHERE e.user_group_id IS NULL` only (public-only)
- [ ] AC7: Empty result returns `[]` — no error raised
- [ ] AC8: All SQL via `text()` with named params — zero string interpolation (SECURITY.md S001)
- [ ] AC9: `asyncio.wait_for(..., timeout=1.8)` wraps full retrieval call

**Python Interface**
```python
# backend/rag/retriever.py
async def retrieve(
    query_embedding: list[float],
    user_group_ids: list[int],   # [] = public-only mode
    top_k: int = 10,
) -> list[RetrievedDocument]:
    ...
```

**SQL Pattern (dense path — no JOIN)**
```sql
SELECT e.doc_id, e.chunk_index, e.embedding <-> :query_vec AS distance
FROM embeddings e
WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)
ORDER BY distance
LIMIT :top_k
```

**RAG Behavior**
- Retrieval: hybrid (dense + BM25)
- RBAC: `WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)`
- Languages: all (filter is language-agnostic)
- Fallback: `[]` if no matching documents

**Auth Requirement**
- [X] OIDC Bearer (human)  [X] API-Key (bot)  [X] Both

**Non-functional**
- Latency: < 1800ms p95
- Audit log: logged in S005
- CJK support: ja / zh / vi / ko (BM25 tokenization handled by cjk-tokenizer feature)

**Implementation notes**
- No JOIN needed — `embeddings.user_group_id` is the denormalized RBAC field (D02).
- PostgreSQL: `ANY(:group_ids)` with empty array evaluates to FALSE — `OR IS NULL` handles public correctly.
- `asyncio.wait_for` timeout 1.8s; raise `QueryTimeoutError` on exceed.
- Hybrid weight: `RAG_BM25_WEIGHT=0.3`, `RAG_DENSE_WEIGHT=0.7` from env (ARCH.md A004).

---

### S003: Retriever test suite — RBAC access matrix

**Role / Want / Value**
- As a: QA engineer
- I want: full test coverage of RBAC filtering including NULL-group (public) edge cases
- So that: no access regression is introduced by future changes

**Acceptance Criteria**
- [ ] AC1: User (1 group) → doc in same group → retrieved ✅
- [ ] AC2: User (1 group) → doc in different group → NOT retrieved ✅
- [ ] AC3: User (2 groups) → docs from either group → all retrieved ✅
- [ ] AC4: User (2 groups) → doc in third group → NOT retrieved ✅
- [ ] AC5: User (0 groups) → private doc (group assigned) → NOT retrieved ✅
- [ ] AC6: User (0 groups) → public doc (`user_group_id IS NULL`) → retrieved ✅
- [ ] AC7: User (1 group) → public doc (NULL group) → retrieved ✅
- [ ] AC8: Hybrid: dense-filtered ∩ BM25-filtered results both respect RBAC ✅
- [ ] AC9: Concurrent queries (n=10) with different `user_group_ids` → no cross-contamination ✅
- [ ] AC10: Latency p95 < 1800ms with 10k embeddings, user has access to 1k

**Test file**
```
tests/rag/test_retriever_rbac.py
├── TestGroupFilter
│   ├── test_own_group_retrieved
│   ├── test_other_group_denied
│   ├── test_multi_group_retrieved
│   ├── test_multi_group_other_denied
├── TestPublicAccess
│   ├── test_no_groups_private_denied
│   ├── test_no_groups_public_retrieved
│   ├── test_with_group_public_doc_retrieved
├── TestHybridRBAC
│   ├── test_hybrid_respects_filter
├── TestConcurrency
│   ├── test_concurrent_no_cross_contamination
├── TestPerformance
│   ├── test_latency_p95_under_1800ms
```

**Non-functional**
- Latency: measured in `test_latency_p95_under_1800ms` (`@pytest.mark.performance`)
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
- Fixtures: 3 user_groups + embeddings: 5 per group (user_group_id set) + 3 public (user_group_id NULL)
- Use `pytest-asyncio`, `asyncio.gather` for concurrency test
- Parameterize: `@pytest.mark.parametrize("group_ids, expected_doc_count", [...])`

---

### S004: ORM model update — nullable user_group_id

**Role / Want / Value**
- As a: backend developer
- I want: Document and Embedding ORM models updated to reflect nullable user_group_id
- So that: application layer correctly handles NULL as public

**Acceptance Criteria**
- [ ] AC1: `backend/db/models/document.py` — `user_group_id: Mapped[Optional[int]]` (was `int`)
- [ ] AC2: `backend/db/models/embedding.py` — `user_group_id: Mapped[Optional[int]]` (was `int`)
- [ ] AC3: `tests/db/test_models.py` — new test verifies both columns accept NULL value
- [ ] AC4: `tests/db/test_models.py` — existing NOT NULL tests removed/updated to match new nullable behavior
- [ ] AC5: Migration 004 verified on live PostgreSQL 17: columns show nullable in `\d documents` / `\d embeddings`
- [ ] AC6: Rollback verified: NULL rows updated to default group, NOT NULL restored cleanly

**Non-functional**
- Latency: N/A
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
- `Optional[int]` in SQLAlchemy 2.x Mapped syntax = nullable column.
- Existing relationship `document.user_group` (many-to-one) remains — nullable FK is valid.
- AC4: test_models.py currently has tests asserting `user_group_id NOT NULL` — invert these.

---

### S005: Wire RBAC filter into /v1/query endpoint

**Role / Want / Value**
- As a: API developer
- I want: `/v1/query` to pass user's group IDs from auth token to retriever automatically
- So that: RBAC is transparent to callers

**Acceptance Criteria**
- [ ] AC1: Route uses `Depends(verify_token)` → `AuthenticatedUser` (auth-api-key-oidc)
- [ ] AC2: `retriever.retrieve(user_group_ids=authenticated_user.groups)` called
- [ ] AC3: OIDC user: JWT `groups` claim names → lookup `user_groups.id` (cache TTL=60s)
- [ ] AC4: API-key user: `api_keys.user_group_ids INTEGER[]` column → passed directly
- [ ] AC5: User with 0 groups → `user_group_ids=[]` → public-only results → 200 with `[]` if none
- [ ] AC6: Audit log: `user_id`, `query_hash`, `retrieved_doc_ids`, `timestamp`, `public_only` flag
- [ ] AC7: Response includes `request_id` (ARCH.md A005)
- [ ] AC8: Latency p95 < 2000ms end-to-end (retrieval 1800ms + async audit write)

**API Contract**
```http
POST /v1/query
Authorization: Bearer <jwt> | X-API-Key: <key>
Content-Type: application/json

{ "query": "string", "top_k": 5 }

--- 200 OK ---
{
  "request_id": "req-uuid",
  "results": [
    { "doc_id": "uuid", "content": "...", "score": 0.92, "is_public": true }
  ]
}

--- 200 OK (0 results) ---
{ "request_id": "req-uuid", "results": [] }

--- 401 Unauthorized ---
{ "error": { "code": "ERR_UNAUTHENTICATED", "message": "...", "request_id": "req-uuid" } }
```

**RAG Behavior**
- Retrieval: hybrid
- RBAC: `user_group_ids` from `AuthenticatedUser.groups`
- Languages: auto-detect (multilingual-rag-pipeline scope)
- Fallback: `[]` — no 403 for 0-group users

**Auth Requirement**
- [X] OIDC Bearer (human)  [X] API-Key (bot)  [X] Both

**Non-functional**
- Latency: < 2000ms p95 (HARD.md R007, PERF.md P001)
- Audit log: required (HARD.md R006) — async background task
- CJK support: ja / zh / vi / ko

**Implementation notes**
- Audit write: `background_tasks.add_task(audit_log.write(...))` — non-blocking.
- `request_id = str(uuid4())` at route entry; propagate to response + audit.
- OIDC group name → ID mapping: `SELECT id FROM user_groups WHERE name = ANY(:names)` — cache 60s.
- `is_public` field in response: `True` if retrieved chunk has `user_group_id IS NULL`.

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC7 | ARCH.md A006 (Migration Strategy — numbered files + rollback) | .claude/rules/ARCH.md | 2026-04-02 |
| AC2 | Stakeholder decision — `NULL = public`, relax NOT NULL on documents | Conversation 2026-04-02 | 2026-04-02 |
| AC3 | Stakeholder decision — embeddings.user_group_id mirrors documents (D03) | Conversation 2026-04-02 | 2026-04-02 |
| AC4 | db-schema-embeddings migration 001 — FK `documents.user_group_id → user_groups.id` | backend/db/migrations/001_create_core_schema.sql | 2026-03-18 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC5 | HARD.md R001 (RBAC Before Retrieval — WHERE clause) | .claude/rules/HARD.md | 2026-04-02 |
| AC2–AC3 | Stakeholder decision D02 — filter on embeddings.user_group_id, no JOIN | Conversation 2026-04-02 | 2026-04-02 |
| AC6–AC7 | Stakeholder decision D04 — 0 groups → empty results | Conversation 2026-04-02 | 2026-04-02 |
| AC8 | SECURITY.md S001 (SQL injection — named params only) | .claude/rules/SECURITY.md | 2026-04-02 |
| AC9 | PERF.md P001 (timeout 1800ms) | .claude/rules/PERF.md | 2026-04-02 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC7 | HARD.md R001 (RBAC Before Retrieval) | .claude/rules/HARD.md | 2026-04-02 |
| AC6–AC7 | Stakeholder decision D01 — NULL = public | Conversation 2026-04-02 | 2026-04-02 |
| AC10 | PERF.md P001 (< 1800ms p95) | .claude/rules/PERF.md | 2026-04-02 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC2 | Stakeholder decisions D01/D03 — nullable user_group_id on both models | Conversation 2026-04-02 | 2026-04-02 |
| AC3–AC6 | db-schema-embeddings — ORM pattern, TDD inversion lesson (L02) | docs/db-schema-embeddings/reports/db-schema-embeddings.report.md | 2026-03-19 |

### S005 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC2 | auth-api-key-oidc (DONE) — AuthenticatedUser.groups interface | .claude/memory/COLD/auth-api-key-oidc.archive.md | 2026-03-24 |
| AC3–AC4 | Stakeholder decision Q2 — OIDC JWT claim + api_keys DB | Conversation 2026-04-02 | 2026-04-02 |
| AC5 | Stakeholder decision D04 — 0 groups → empty, not 403 | Conversation 2026-04-02 | 2026-04-02 |
| AC6 | HARD.md R006 (Audit Log on Document Access) | .claude/rules/HARD.md | 2026-04-02 |
| AC7 | ARCH.md A005 (Error Response Shape with request_id) | .claude/rules/ARCH.md | 2026-04-02 |
| AC8 | HARD.md R007 + PERF.md P001 (< 2000ms p95) | .claude/rules/HARD.md | 2026-04-02 |

---
