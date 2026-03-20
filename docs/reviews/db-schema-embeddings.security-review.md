# Code Review: db-schema-embeddings — Security Level
Level: security | Date: 2026-03-19 | Reviewer: Claude | Verdict: APPROVED ✅

---

## Scope
All implemented files in `backend/db/` and `backend/db/migrations/`.
This is a DB-layer-only feature — no routes, no auth, no RAG logic.

---

## Security Checks

### S001 — SQL Injection
- [x] **No Python SQL string interpolation** — zero f-strings in any query
- [x] All SQL lives in `.sql` migration files — no dynamic SQL construction
- [x] ORM columns defined declaratively — no raw query strings in models
- [x] `session.py` contains no queries

**Result: PASS ✅**

### S005 — No Hardcoded Secrets
- [x] `session.py:9` — `DATABASE_URL = os.getenv("DATABASE_URL")` ✅
- [x] No passwords in any `.py` file (grep confirmed: 0 matches)
- [x] No passwords in any `.sql` file (grep confirmed: 0 matches)

⚠️ `docker-compose.yml` contains `POSTGRES_PASSWORD: kh_dev_password`
→ **Acceptable for dev-only compose file.** Clearly labeled `kh_dev_password`.
→ `.gitignore` should exclude `.env` (confirmed) but `docker-compose.yml` is tracked.
→ **Recommendation**: use `docker-compose.override.yml` for production credentials, keep compose dev-only.

⚠️ `.env.example` contains `kh_dev_password`
→ **Acceptable** — `.env.example` is intentionally a template with placeholder values.

**Result: PASS ✅ (warnings non-blocking for dev environment)**

### R001 — RBAC WHERE Clause
- [x] `embeddings.user_group_id` denormalized (no FK join needed) — correct by design (R001, C002)
- [x] Comment in migration 001 L38: `"-- denormalized for RBAC filter (R001, C002)"`
- [x] Comment in embedding.py L22: `"# denormalized, no FK (R001)"`
- [x] Schema is RBAC-ready — WHERE clause enforcement is rag-agent responsibility (out of scope)

**Result: PASS ✅ (db layer responsibility fulfilled)**

### R002 — No PII in Vector Metadata
- [x] `embeddings` columns: `id, doc_id, chunk_index, lang, user_group_id, created_at, embedding`
- [x] No name, email, content snippet, or user-identifiable fields in embeddings table
- [x] `user_id` only exists in `audit_logs` (correct — for compliance logging, not vector metadata)

**Result: PASS ✅**

### R006 — Audit Log on Document Access
- [x] `audit_logs` table exists with: `user_id, doc_id, query_hash, accessed_at`
- [x] Schema is ready — write enforcement is api-agent/rag-agent responsibility (out of scope)

**Result: PASS ✅ (db layer responsibility fulfilled)**

### R003, R004 — Auth / Route Prefix
- [x] N/A — no routes in db layer

### R007 — Latency SLA
- [x] HNSW index in place (P003) — migration 002
- [x] GIN index for FTS (migration 003)
- [x] Connection pool pre-ping enabled — no stale connection latency spikes

**Result: PASS ✅**

---

## Full Level Checks

### backend/db/session.py
- [x] No magic numbers — pool params documented with D04/C011 refs
- [x] Module-level engine (not per-request)
- [x] No dead code

### ORM Models
- [x] All nullable columns explicitly documented (why nullable, who populates)
- [x] No silent defaults that could mask missing data
- [x] `audit_logs.user_id` TEXT placeholder — FK deferred to auth-agent, documented

---

## Issues Found

### ⚠️ WARNING — Non-blocking

**1. `session.py:9` — no guard on `DATABASE_URL=None`**
```python
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, ...)  # raises if None
```
Currently: fails at import time with `ArgumentError: Could not parse rfc1738 URL from string 'None'` — fast-fail, clear error.
Recommended fix (future task):
```python
DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL, "DATABASE_URL environment variable is required"
```

**2. `docker-compose.yml` — credentials via env vars** ✅ FIXED
`docker-compose.yml` now uses `${POSTGRES_USER}` / `${POSTGRES_PASSWORD}` from `.env`.
`.env` is gitignored. `.env.example` has placeholder values only.

**3. `audit_logs` — no index on `doc_id` or `accessed_at`**
High-volume audit log queries (e.g. `WHERE doc_id = ?` for compliance reports) will do seq scan.
Not a security issue — performance concern for future. Deferred to api-agent when audit query patterns are known.

---

## Verdict

**APPROVED ✅**

Zero security blockers. DB layer fulfills all security obligations within its scope:
- RBAC-ready schema (R001 ✅)
- No PII in vector metadata (R002 ✅)
- Audit log table ready (R006 ✅)
- No SQL injection surface (S001 ✅)
- No hardcoded secrets in code (S005 ✅)

Remaining security enforcement (JWT validation, RBAC WHERE clause, audit log writes) is api-agent / rag-agent / auth-agent responsibility — correctly deferred.
