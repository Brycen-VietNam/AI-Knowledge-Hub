# Spec Template — Two-Layer Structure
# Usage: /specify copies this to docs/specs/<feature>.spec.md

---

# Spec: {{FEATURE_NAME}}
Created: {{DATE}} | Author: {{AUTHOR}} | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | {{EPIC}} |
| Priority | P0 / P1 / P2 |
| Story count | N |
| Token budget est. | ~Nk |
| Critical path | S001 → S00N |
| Parallel-safe stories | [list] |
| Blocking specs | [list] |
| Blocked by | [list] |
| Agents needed | db-agent, rag-agent, ... |

### Problem Statement (3 lines max)
_What problem does this solve, for whom, and why now._

### Solution Summary (5 bullets max)
- _
- _
- _

### Out of Scope
- _

---

## LAYER 2 — Story Detail (load per story for /tasks, /analyze, /implement)

<!-- Repeat for each story -->

### S001: {{Story Title}}

**Role / Want / Value**
- As a: _[role]_
- I want: _[capability]_
- So that: _[value]_

**Acceptance Criteria**
- [ ] AC1: _
- [ ] AC2: _

**API Contract** _(if applicable)_
```
METHOD /v1/<path>
Headers: Authorization: Bearer <token> | X-API-Key: <key>
Body: {}
Response 200: {}
Response 4xx: {"error": {"code": "...", "message": "..."}}
```

**RAG Behavior** _(if applicable)_
- Retrieval: hybrid | dense-only | bm25-only
- RBAC: filter on user_group_id
- Languages: ja / en / vi / ko
- Fallback: _

**Auth Requirement**
- [ ] OIDC Bearer (human)  [ ] API-Key (bot)  [ ] Both

**Non-functional**
- Latency: < 2s p95
- Audit log: required / not required
- CJK support: ja / zh / vi / ko / not applicable

**Implementation notes**
_Short notes for agent. Not design doc._

---
<!-- End S001 -->

---

## LAYER 3 — Sources Traceability (load for audit / design rationale)

### S001 Sources
| AC | Source | Reference | Date |
|-----|--------|-----------|------|
| AC1 | _[type: requirement doc / email / ticket / conversation]_ | _[doc name, email date, ticket ID]_ | _[YYYY-MM-DD]_ |
| AC2 | | | |

---
