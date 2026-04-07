# Tasks: document-ingestion / S005-api — GET list, GET by ID, DELETE routes
Created: 2026-04-07 | Agent: api-agent | Status: TODO

---

## LAYER 1 — Story Task Summary

| Field | Value |
|-------|-------|
| Story | S005-api: Document management — GET list, GET by ID, DELETE |
| Total tasks | 3 |
| Parallel groups | G1: [T001,T002 safe], G2: [T003 after:T001,T002] |
| Critical path | T001 → T003 |
| Agent | api-agent |
| Est. session | 1 |

### Task Status Board
| Task | Title | Status | Parallel | Blocks |
|------|-------|--------|----------|--------|
| T001 | GET /v1/documents — paginated RBAC-filtered list + test | DONE | safe | T003 |
| T002 | GET /v1/documents/{id} — metadata + 404 + test | DONE | safe | T003 |
| T003 | DELETE /v1/documents/{id} — 204 + 404 + test | DONE | after:T001,T002 | — |

---

## LAYER 2 — Task Detail

### T001: GET /v1/documents — paginated, RBAC-filtered list

**Status**: TODO

**File(s)**
- `backend/api/routes/documents.py` — action: modify (add GET list handler)
- `tests/api/test_documents_management.py` — action: create

**Change description**
Add `GET /v1/documents?page=1&limit=20&user_group_id=<int>` handler.
Query: `SELECT ... FROM documents WHERE (user_group_id = ANY(:group_ids) OR user_group_id IS NULL) ORDER BY created_at DESC LIMIT :limit OFFSET :offset`.
`chunk_count` via subquery: `SELECT COUNT(*) FROM embeddings WHERE doc_id = d.id`.
Response: `{"items": [...], "total": int, "page": int, "limit": int}`.

**Review criteria**
- [ ] RBAC filter at SQL WHERE clause — not Python post-filter (R001)
- [ ] Filter: `user_group_id = ANY(:group_ids) OR user_group_id IS NULL`
- [ ] `limit` max 100; if > 100 → 422 (Q8 default)
- [ ] `chunk_count` uses subquery (not N+1 per document — P004)
- [ ] `ORDER BY created_at DESC` (Q7 default)
- [ ] `Depends(verify_token)` on route (R003)
- [ ] Test: caller in group A → only group A + public docs returned
- [ ] Test: limit=101 → 422
- [ ] Test: empty result → `{"items": [], "total": 0, ...}`
- [ ] Rule satisfied: R001, R003, R004, P004

**Test command**
```bash
pytest tests/api/test_documents_management.py::test_list_documents -v
```

**Parallel**: safe
**Size estimate**: ~35 lines handler + ~35 lines tests

---
<!-- End T001 -->

### T002: GET /v1/documents/{id} — metadata + 404 (prevent enumeration)

**Status**: TODO

**File(s)**
- `backend/api/routes/documents.py` — action: modify (add GET by ID handler)
- `tests/api/test_documents_management.py` — action: modify (add GET by ID tests)

**Change description**
Add `GET /v1/documents/{id}` handler.
Query: `SELECT ... FROM documents WHERE id = :id AND (user_group_id = ANY(:group_ids) OR user_group_id IS NULL)`.
If not found OR not in caller's groups → 404 NOT_FOUND (not 403 — prevents enumeration, AC3).
`chunk_count` via same subquery pattern as list endpoint.

**Review criteria**
- [ ] Single query with RBAC in WHERE clause (R001)
- [ ] Returns 404 for both not-found AND unauthorized (AC3 — no enumeration)
- [ ] Error: `{"error": {"code": "NOT_FOUND", "message": "...", "request_id": "..."}}` (A005)
- [ ] Response fields: `id, title, lang, user_group_id, status, created_at, chunk_count`
- [ ] Test: valid accessible doc → 200 with all fields
- [ ] Test: doc exists but wrong group → 404 (not 403)
- [ ] Test: doc does not exist → 404
- [ ] Rule satisfied: R001, R003, A005

**Test command**
```bash
pytest tests/api/test_documents_management.py::test_get_document_by_id -v
```

**Parallel**: safe
**Size estimate**: ~20 lines handler + ~30 lines tests

---
<!-- End T002 -->

### T003: DELETE /v1/documents/{id} — 204 + 404

**Status**: TODO

**File(s)**
- `backend/api/routes/documents.py` — action: modify (add DELETE handler)
- `tests/api/test_documents_management.py` — action: modify (add DELETE tests)

**Change description**
Add `DELETE /v1/documents/{id}` handler.
Same RBAC WHERE check as GET by ID — 404 if not found or inaccessible.
`DELETE FROM documents WHERE id = :id AND (user_group_id = ANY(:group_ids) OR user_group_id IS NULL)`.
Cascade to `embeddings` is handled by FK `ondelete=CASCADE` (already in schema).
Returns `Response(status_code=204)` (no body).

**Review criteria**
- [ ] DELETE uses RBAC WHERE clause — not fetch-then-delete (R001, P004)
- [ ] Returns `Response(status_code=204)` with no body (AC5)
- [ ] 404 if doc not found OR not in caller's groups (AC5 + enumeration prevention)
- [ ] No explicit cascade logic needed — FK handles it (verified from embedding.py)
- [ ] Test: successful delete → 204, doc no longer in GET list
- [ ] Test: cascade verified — embeddings also deleted (query count = 0)
- [ ] Test: delete inaccessible doc → 404
- [ ] Test: delete non-existent doc → 404
- [ ] Rule satisfied: R001, R003, R004, P004

**Test command**
```bash
pytest tests/api/test_documents_management.py::test_delete_document -v
```

**Parallel**: after:T001,T002
**Size estimate**: ~20 lines handler + ~30 lines tests

---
<!-- End T003 -->
