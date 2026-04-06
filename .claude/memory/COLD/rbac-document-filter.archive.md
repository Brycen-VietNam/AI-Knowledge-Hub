# Feature Archive: rbac-document-filter
> Archived by /report --finalize. Approved by: lb_mui. Date: 2026-04-06.
> Load only when explicitly referenced: /context rbac-document-filter --from-cold

Status: DONE ✅
Completed: 2026-04-06
Stories: 5 (S001–S005) | AC: 41/41 | Tests: all PASS | Review blockers: 0

---

## Summary
RBAC enforcement at SQL WHERE level for hybrid retrieval pipeline.
- `user_group_id` nullable on `documents` + `embeddings` — `NULL = public`
- Filter: `WHERE (user_group_id = ANY(:group_ids) OR user_group_id IS NULL)`
- Dense path: filters on `embeddings.user_group_id` (no JOIN — D02)
- BM25 path: filters on `documents.user_group_id`
- 0-group users → public-only results, 200 (not 403) — D04
- `/v1/query` endpoint wired: auth token groups → retriever → audit log

## Key Decisions
| ID  | Decision | Date |
|-----|----------|------|
| D01 | `user_group_id IS NULL` = public (not `is_public` column) | 2026-04-02 |
| D02 | Dense: filter on `embeddings.user_group_id` (no JOIN). BM25: filter on `documents.user_group_id` | 2026-04-03 |
| D03 | document-ingestion MUST write user_group_id to both tables atomically | 2026-04-02 |
| D04 | 0-group users → empty results, not 403 | 2026-04-02 |

## Files Touched
| File | Action |
|------|--------|
| `backend/db/migrations/005_nullable_user_group_id.sql` | CREATE |
| `backend/db/models/document.py` | MODIFY — Mapped[Optional[int]] |
| `backend/db/models/embedding.py` | MODIFY — Mapped[Optional[int]] |
| `backend/rag/__init__.py` | CREATE |
| `backend/rag/retriever.py` | CREATE — retrieve(), _dense_search(), _bm25_search(), _merge(), QueryTimeoutError |
| `backend/api/__init__.py` | CREATE |
| `backend/api/routes/__init__.py` | CREATE |
| `backend/api/routes/query.py` | CREATE — POST /v1/query |
| `tests/rag/__init__.py` | CREATE |
| `tests/rag/conftest.py` | CREATE — real PG fixtures |
| `tests/rag/test_retriever_rbac.py` | CREATE — RBAC matrix + concurrency + performance |
| `tests/db/test_models.py` | MODIFY — +4 nullable tests |
| `tests/api/__init__.py` | CREATE |
| `tests/api/conftest.py` | CREATE |
| `tests/api/test_query_rbac.py` | CREATE — 401/OIDC/API-key/0-group/504 |
| `pytest.ini` | MODIFY — integration + performance markers |

## Deferred Issues (non-blocking)
- W-01: Timeout test indirection — fix at embedder-integration
- W-02: large_seeded_session teardown — fix before CI setup
- W-03: p95 index off-by-one — fix at performance story
- W-05: Shared AsyncSession in concurrency test — fix at performance story
- W-S5-01: Unused imports in query.py — next cleanup
- W-S5-02: embed() outside timeout wrapper — fix at embedder-integration (SLA risk)
- W-S5-03: Return type annotation mismatch query.py — next cleanup

## Unblocks
- document-ingestion (D03 contract: must write user_group_id atomically)
- multilingual-rag-pipeline (retrieve() interface stable)
- query-endpoint (POST /v1/query scaffold + RBAC wired)

## Report
`docs/rbac-document-filter/reports/rbac-document-filter.report.md`
