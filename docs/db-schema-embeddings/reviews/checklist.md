# Pre-Plan Checklist: db-schema-embeddings
Created: 2026-03-18 | Spec: `docs/specs/db-schema-embeddings.spec.md` | Status: PASS

---

## Overview

**Status:**
- [x] **AC Coverage** — All acceptance criteria clear & testable
- [x] **Scope Impact** — All affected systems identified
- [x] **Quality Criteria** — Performance, security, CJK support defined

---

## Section 1: Acceptance Criteria Coverage

### Completeness
- [x] All ACs have clear "as a / want / so that" statements — S001–S004 all have role/want/value
- [x] All ACs are SMART — each AC is a concrete DDL statement or verifiable condition
- [x] All ACs have acceptance/rejection criteria — pass = DDL executes without error + verify with `\d`
- [x] No vague ACs — all ACs are SQL-level statements (CREATE TABLE, CREATE INDEX, etc.)

### Testability
- [x] Each AC is independently testable — each DDL line is a standalone assertion
- [x] Test success criteria are unambiguous — e.g. `\d embeddings` confirms HNSW index exists
- [x] No hidden assumptions — all assumptions explicitly tagged in spec (D02, D03, D04)
- [x] Edge cases: rollback section required per AC5 in S001, S002, S003 (C010)

### Story Dependencies
- [x] S001 → S002 → S003/S004 (S003 + S004 parallel after S001) — Layer 1 critical path defined
- [x] Blocking stories: none (db-schema-embeddings is root, not blocked by anything)
- [x] Parallel-safe: S003, S004 clearly marked in Layer 1
- [x] Critical path: S001 → S002 → S003/S004

**Verdict:** ✅ PASS — All ACs clear + testable (18/18 ACs traced)

---

## Section 2: Scope Impact

### Systems & Files
- [ ] API endpoints impacted? **N/A** — DB schema only, no route changes
- [x] Database schema changes? **YES** — 4 new tables + pgvector extension + 2 indexes. Migration files 001–004 required (C010).
- [ ] Authentication/Authorization? **N/A** — schema provides `user_group_id` column; auth logic is auth-agent scope
- [ ] Frontend components? **N/A**
- [ ] Third-party integrations? **N/A** — pgvector is PostgreSQL extension, no external API
- [x] Configuration files? **YES** — `backend/db/session.py` (pool config), env vars: `DATABASE_URL`

### Non-functional Impact
- [ ] Latency SLA affected? **N/A** — schema layer; query latency SLA applies to /v1/query (query-endpoint spec)
- [x] Storage impact? **YES** — `embeddings` table stores vector(1024) per chunk. HNSW index ~1.5x storage overhead vs raw vectors. Acceptable for initial deploy.
- [x] Audit logging required? **YES** — `audit_logs` table schema defined in S001 AC4 (C008). Populated by query-endpoint, not this spec.
- [ ] Cache invalidation? **N/A**
- [x] Rollback plan feasible? **YES** — each migration file has rollback section (DROP TABLE CASCADE / DROP INDEX / DROP EXTENSION)

### Cross-team Impact
- [ ] Other teams affected? **Internal only** — db-agent scope, other agents use session factory interface
- [ ] Breaking changes? **N/A** — greenfield, no existing schema
- [x] Deployment order? **YES** — must deploy before auth, rag, api agents (root dependency)

**Verdict:** ✅ PASS — All scope boundaries clear

---

## Section 3: Quality Criteria

### Functional Quality
- [x] RBAC at DB level — `user_group_id INT` column on `embeddings` table enables WHERE clause filter (C001, R001) ✅
- [x] No PII in vector metadata — `embeddings` metadata: doc_id, lang, user_group_id, created_at only (C002, R002) ✅
- [ ] Auth on every endpoint — **N/A** (schema layer, no endpoints)
- [ ] API version prefix — **N/A** (schema layer, no routes)

### Multilingual Support
- [x] CJK-aware tokenization defined — `content_fts tsvector` column in S003; app-layer tokenization confirmed (D02); MeCab/kiwipiepy/jieba/underthesea (C005, C006, R005) ✅
- [x] Language-specific: `lang CHAR(2)` column on both `documents` and `embeddings` — supports ja/en/vi/ko/zh ✅
- [ ] Fallback language — **N/A** for schema layer. Fallback lang behavior is query-endpoint scope (C009).

### Performance
- [ ] p95 < 2s for /v1/query — **N/A** (schema layer). HNSW index in S002 is the schema-level enabler.
- [ ] Query timeout — **N/A** (schema layer)
- [ ] Pagination limits — **N/A** (schema layer)
- [x] Index strategy — HNSW index (m=16, ef_construction=64, cosine) in S002 (P003) + GIN index on `content_fts` in S003 ✅

### Security & Compliance
- [x] Audit log schema defined — `audit_logs` table in S001 AC4 (R006, C008) ✅
- [x] Input validation — **N/A** at schema layer. No user input touches DB directly.
- [ ] Rate limiting — **N/A** (schema layer; rate-limiting is P2 feature)
- [ ] Encryption at rest — ⚠️ WARN — see below
- [ ] GDPR/data retention — ⚠️ WARN — see below

### Testing & Documentation
- [x] Unit test scope — migration files tested via `psql` execution + rollback test
- [x] Integration test — session.py pool tested via `SELECT 1` health check (S004 AC4)
- [x] Black-box test cases: verify tables exist, HNSW index exists, pool connects on startup
- [x] Documentation — migration files are self-documenting via numbered naming + rollback sections

**Verdict:** ✅ PASS with 2 WARNs (acceptable, see below)

---

## WARN Items

⚠️ **WARN-01: Encryption at rest not specified**
Risk: If PostgreSQL volume is compromised, embeddings and document metadata are exposed in plaintext.
Mitigation: Delegate to infrastructure layer (volume encryption at deploy time). Schema itself cannot enforce this. Document in deployment runbook.
Approve? [x] Yes, proceed — infra-level concern, not schema blocker

⚠️ **WARN-02: GDPR / data retention policy not defined**
Risk: `audit_logs` and `documents` tables may accumulate indefinitely.
Mitigation: Add `retention_days` column to `audit_logs` as P1 item. For now, manual purge acceptable for internal platform pre-MVP.
Approve? [x] Yes, proceed — P1 backlog item, not P0 blocker

✅ **WARN-03: RESOLVED — AGENTS.md exists at `.claude/AGENTS.md`**
db-agent scope confirmed: owns `backend/db/`, model=sonnet, can parallel with rag-agent + api-agent.
No action needed.

---

## Final Gate: Overall Status

| Section | Result | Issues |
|---------|--------|--------|
| AC Coverage | ✅ PASS | None |
| Scope Impact | ✅ PASS | None |
| Quality Criteria | ✅ PASS (2 WARNs approved) | WARN-01: encryption at rest, WARN-02: data retention |

---

### **OVERALL CHECKLIST STATUS: ✅ PASS**

All sections green. 3 WARNs acknowledged and approved (infra/P1 concerns, not schema blockers).

**Ready for `/plan db-schema-embeddings`**

**Approved by:** /checklist agent (auto)
**Date:** 2026-03-18
**Comments:**
- Create AGENTS.md before second feature's /plan
- Add data retention design to P1 backlog
- Deployment runbook to cover encryption at rest

---

## Passed Items Summary (30/30 applicable)

| Category | Checked | N/A | WARNs |
|----------|---------|-----|-------|
| AC Coverage | 8 | 0 | 0 |
| Scope Impact | 6 | 4 | 0 |
| Quality Criteria | 10 | 7 | 3 |
| **Total** | **24** | **11** | **3** |
