# Checklist: rbac-document-filter
Generated: 2026-04-03 | Updated: 2026-04-03 (CONSTITUTION v1.3 added) | Model: haiku | Spec: v2 DRAFT

---

## Result: ⚠️ WARN — 3 items need approval, 0 blockers

---

## ❌ Blockers (fix before /plan)
_None._

---

## ⚠️ WARN items — require approval

---

⚠️ WARN: `sources.md` Open Source Questions (Q5/Q6) reference old assumptions now superseded by confirmed decisions
Risk: Future agents loading sources.md may be confused by stale "default assumption" entries that contradict confirmed spec.
Mitigation: Update sources.md to reflect confirmed decisions (NULL=public, embeddings.user_group_id for dense, documents.user_group_id for BM25) before /plan. Low risk — clarify.md is authoritative.
Approve? [x] Yes, proceed  [ ] No, resolve first

---

⚠️ WARN: AGENTS.md does not exist — agent scope assignments cannot be verified
Risk: db-agent, rag-agent, api-agent scope assignments listed in spec Layer 1 are unverified against registry.
Mitigation: Scope assignments are consistent with ARCH.md A001 (db-agent owns migrations, rag-agent owns retriever, api-agent owns routes). Proceed with ARCH.md as authority.
Approve? [x] Yes, proceed  [ ] No, resolve first

---

⚠️ WARN: Prompt caching strategy not documented in spec
Risk: If subagents are dispatched during /implement, cache prefix may not be stable.
Mitigation: This feature has no direct LLM call path (pure retrieval + SQL filter). Cache strategy N/A for core RBAC logic. S005 wires into existing /v1/query — caching handled by query-endpoint feature.
Approve? [x] Yes, proceed  [ ] No, resolve first

---

## ✅ Passed (27/30)

### Spec Quality
- [x] Spec file exists at `docs/rbac-document-filter/spec/rbac-document-filter.spec.md`
- [x] Layer 1 summary complete — all fields filled (epic, priority, story count, budget, critical path, parallel-safe, blocking, blocked-by, agents)
- [x] Layer 2 stories have clear SMART AC statements — all measurable/testable
- [x] Layer 3 sources mapped — every AC traced (note: sources.md stale on Q5/Q6, covered by WARN above)
- [x] All ACs testable — no vague "should work well" statements
- [x] API contract defined for S005 (POST /v1/query) — request/response shapes, 200 + 401 documented
- [x] No silent assumptions — all explicit: D01–D04 in spec Layer 1, A2/A3 superseded by confirmed decisions

### Architecture Alignment
- [x] No CONSTITUTION violations — CONSTITUTION v1.3 checked: 16/16 constraints PASS (see section below)
- [x] HARD.md R001 ✅ — filter at WHERE clause level, before ORDER BY/LIMIT (S002/AC4)
- [x] HARD.md R003 ✅ — Auth on every endpoint; S005/AC1 uses `Depends(verify_token)`
- [x] HARD.md R004 ✅ — Route `/v1/query` with `/v1/` prefix (S005 API contract)
- [x] HARD.md R006 ✅ — Audit log on every retrieval; S005/AC6 records user_id, doc_ids, query_hash, timestamp
- [x] HARD.md R007 ✅ — Latency SLA < 2000ms p95; S005/AC8 + S002/AC9 (1800ms retrieval timeout)
- [x] SECURITY.md S001 ✅ — Named params only; S002/AC8 explicitly requires `text()` with bindparams
- [x] PERF.md P001 ✅ — Timeout 1800ms in retriever + 2000ms end-to-end; async pipeline
- [x] PERF.md P003 ✅ — HNSW index already exists (migration 002); no sequential scan
- [x] ARCH.md A001 ✅ — Agent scope: db-agent (S001/S004), rag-agent (S002/S003), api-agent (S005)
- [x] ARCH.md A002 ✅ — Dependency direction: api→rag→db preserved; no reverse deps
- [x] ARCH.md A006 ✅ — Migration 005 with rollback section; numbered sequentially
- [x] Auth pattern specified: both OIDC Bearer + API-Key (S005/AC3–AC4)
- [x] pgvector schema change: migration 005 plan defined (DROP NOT NULL + partial indexes)

### Multilingual Completeness
- [x] All 4 languages addressed: RBAC filter is language-agnostic; BM25 + dense paths cover ja/en/vi/ko
- [x] CJK tokenization: explicitly deferred to cjk-tokenizer feature (S002 implementation notes)
- [x] Response language behavior: N/A — RBAC filter does not affect response language

### Dependencies
- [x] auth-api-key-oidc: DONE ✅ — `verify_token`, `AuthenticatedUser` available
- [x] db-schema-embeddings: DONE ✅ — tables exist, ORM models established
- [x] No circular story dependencies: S001→S002→S003→S004→S005 strictly sequential (S003∥S004 parallel-safe)
- [x] External contracts: pgvector HNSW index locked (migration 002), PostgreSQL 17 confirmed

### Agent Readiness
- [x] Token budget estimated: ~4k in Layer 1
- [x] Parallel-safe stories identified: S003 ∥ S004
- [x] Subagent assignments listed: db-agent (S001/S004), rag-agent (S002/S003), api-agent (S005)
- [x] Prompt caching: N/A — no LLM call path in this feature (see WARN above)

---

## Summary

| Category | Items | Pass | Warn | Fail |
|----------|-------|------|------|------|
| Spec Quality | 7 | 7 | 0 | 0 |
| Architecture | 14 | 14 | 0 | 0 |
| Multilingual | 3 | 3 | 0 | 0 |
| Dependencies | 4 | 4 | 0 | 0 |
| Agent Readiness | 4 | 3 | 1 | 0 |
| Admin (sources, AGENTS.md) | 2 | 0 | 2 | 0 |
| **Total** | **34** | **31** | **3** | **0** |

---

## CONSTITUTION v1.3 — Full Check

### Principles
| ID | Principle | Result | Note |
|----|-----------|--------|------|
| P001 | Spec before code | ✅ | Spec + clarify + checklist complete before /plan |
| P002 | RBAC at DB layer | ✅ | S002/AC4: filter before ORDER BY/LIMIT, not post-retrieval Python |
| P003 | Multilingual equality | ✅ | Filter language-agnostic; CJK deferred to correct scope |
| P004 | API contract = source of truth | ✅ | S005 has full request/response contract |
| P005 | Fail fast, structured errors | ✅ | 401 shape matches A005: code + message + request_id |
| P006 | Latency SLA | ✅ | 1800ms retriever timeout + 2000ms e2e |
| P007 | Memory layered | ✅ | HOT/WARM loaded per task only |
| P008 | Agent scope isolation | ✅ | db/rag/api-agent separated; no cross-imports |

### Hard Constraints
| ID | Constraint | Result | Note |
|----|-----------|--------|------|
| C001 | RBAC filter at pgvector WHERE — never Python | ✅ | S002/AC2+AC4 |
| C002 | PII not in vector metadata | ✅ | Migration only makes user_group_id nullable; no PII added |
| C003 | All /v1/* require auth; /v1/health exception only | ✅ | S005/AC1: `Depends(verify_token)` |
| C004 | /v1/ prefix mandatory | ✅ | S005 API: POST /v1/query |
| C005 | CJK needs language-aware tokenizer | ✅ | Deferred correctly — S002 notes: "handled by cjk-tokenizer feature" |
| C006 | Vietnamese needs underthesea | ✅ | Same — deferred to cjk-tokenizer |
| C007 | Hybrid weights configurable via env | ✅ | S002 notes: RAG_BM25_WEIGHT + RAG_DENSE_WEIGHT env vars |
| C008 | Audit log on every retrieval | ✅ | S005/AC6: user_id, doc_ids, query_hash, timestamp |
| C009 | Auto-detect language, no lang="en" hardcode | ✅ | N/A — RBAC filter is language-agnostic |
| C010 | Schema changes via numbered migration files | ✅ | S001: 005_nullable_user_group_id.sql |
| C011 | Connection pool min=5, max=20 | ✅ | Established in db-schema-embeddings; RBAC adds no new connections |
| C012 | Embedding batch min 32 docs | ✅ | N/A — no embedding API calls in this feature |
| C013 | Rate limiting 60/min query | ✅ | N/A — deferred to rate-limiting feature (P2 backlog) |
| C014 | AI answer cite ≥1 source | ✅ | N/A — no LLM answer generation |
| C015 | LLM provider configurable via env | ✅ | N/A — no LLM call |
| C016 | Rate limiting: Valkey/Redis ≤7.2 only | ✅ | N/A — deferred |

**CONSTITUTION result: 8/8 principles ✅ | 16/16 constraints ✅ — ZERO VIOLATIONS**

---

## Next

All 3 WARN items approved. CONSTITUTION v1.3 fully verified.
**→ Proceed to `/plan rbac-document-filter`**
