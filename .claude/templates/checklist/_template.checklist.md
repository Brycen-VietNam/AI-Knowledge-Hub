# Pre-Plan Checklist: {{FEATURE_NAME}}
Created: {{DATE}} | Spec: `docs/specs/{{FEATURE_NAME}}.spec.md` | Status: {{STATUS}}

---

## Overview
Gate-keeping checklist before `/plan` is allowed.
Must reach **STATUS: PASS** to proceed to planning phase.

**Status:**
- [ ] **AC Coverage** — All acceptance criteria clear & testable?
- [ ] **Scope Impact** — All affected systems identified?
- [ ] **Quality Criteria** — Performance, security, CJK support defined?

---

## Section 1: Acceptance Criteria Coverage

### Completeness
- [ ] All ACs have clear "as a / want / so that" statements
- [ ] All ACs are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- [ ] All ACs have acceptance/rejection criteria defined
- [ ] No vague ACs like "improve", "support", "handle"

### Testability
- [ ] Each AC is independently testable (no "and" between test cases)
- [ ] Test success criteria are unambiguous
- [ ] No assumptions hidden in AC description
- [ ] Edge cases mentioned (empty input, concurrent access, timeouts, etc.)

### Story Dependencies
- [ ] Story order/dependencies clearly marked (S001 → S002 → ...)
- [ ] Blocking stories identified (if any)
- [ ] Parallel-safe stories identified
- [ ] Critical path clear

**Verdict:**
- [ ] PASS — All ACs clear + testable
- [ ] FAIL — Ambiguities remain (list below)

_If FAIL: resolve before proceeding._

---

## Section 2: Scope Impact

### Systems & Files
- [ ] API endpoints impacted? (if yes, list)
- [ ] Database schema changes? (if yes, migration needed?)
- [ ] Authentication/Authorization? (if yes, RBAC rules defined?)
- [ ] Frontend components? (if yes, UI mockups attached?)
- [ ] Third-party integrations? (if yes, API keys / webhooks configured?)
- [ ] Configuration files? (if yes, list)

### Non-functional Impact
- [ ] Latency SLA affected? (p95 target defined?)
- [ ] Storage impact? (backup, indexing needed?)
- [ ] Audit logging required? (user_id, doc_id, timestamp logged?)
- [ ] Cache invalidation strategy? (if yes, describe)
- [ ] Rollback plan feasible? (if yes, outline)

### Cross-team Impact
- [ ] Other teams affected? (notification sent?)
- [ ] Breaking changes? (versioning strategy defined?)
- [ ] Deployment order (if multiple features)? (described?)

**Verdict:**
- [ ] PASS — All scope boundaries clear
- [ ] PARTIAL — Some questions remain (list below)
- [ ] FAIL — Unclear scope (halt planning)

_If PARTIAL/FAIL: clarify before proceeding._

---

## Section 3: Quality Criteria

### Functional Quality
- [ ] RBAC applied at DB level (not Python) — per R001?
- [ ] No PII in vector metadata — per R002?
- [ ] Auth on every endpoint — per R003?
- [ ] API version prefix (/v1/*) — per R004?

### Multilingual Support (if applicable)
- [ ] CJK-aware tokenization defined (ja/zh/vi)? — per R005?
- [ ] Language-specific test cases included?
- [ ] Fallback language defined (if lang unsupported)?

### Performance
- [ ] p95 latency target < 2s (for /v1/query)? — per R007?
- [ ] Query timeout defined (ms)?
- [ ] Batch size / pagination limits defined?
- [ ] Index strategy (database indexes, vector indexes)?

### Security & Compliance
- [ ] Audit log on document access? — per R006?
- [ ] Input validation (XSS, injection prevention)?
- [ ] Rate limiting configured (if user-facing)?
- [ ] Encryption at rest / in transit (if handling secrets)?
- [ ] GDPR/compliance requirements checked (data retention)?

### Testing & Documentation
- [ ] Unit test scope defined (% coverage target)?
- [ ] Integration test scenarios listed?
- [ ] Black-box test cases (happy path + edge cases)?
- [ ] Documentation strategy (API docs, change log)?
- [ ] Prompt caching strategy documented? (stable prefix + dynamic suffix + cache_control if API path)

Prompt caching applicability:
- Required when feature includes LLM prompts or subagent orchestration.
- If feature has no LLM path, mark this item as N/A with a short reason.

**Verdict:**
- [ ] PASS — All quality criteria met
- [ ] WARN — Some quality criteria flagged (acceptable risk?)
- [ ] FAIL — Critical quality gaps (must resolve)

_If FAIL: address before proceeding._

---

## Final Gate: Overall Status

| Section | Result | Issues |
|---------|--------|--------|
| AC Coverage | ✓ / ✗ | _[list if ✗]_ |
| Scope Impact | ✓ / ⚠️ / ✗ | _[list if not ✓]_ |
| Quality Criteria | ✓ / ⚠️ / ✗ | _[list if not ✓]_ |

---

### **OVERALL CHECKLIST STATUS:**

- [ ] **PASS** — All sections green. Ready for `/plan`.
- [ ] **WARN** — Some flags, but acceptable. Team approved. Ready for `/plan`.
- [ ] **FAIL** — Blockers remain. Cannot proceed to `/plan`.

**Approved by:** _[name]_
**Date:** _[YYYY-MM-DD]_
**Comments:** _[any additional notes]_

---

## How to Use

1. Spec is complete → run `/checklist {{FEATURE_NAME}}`
2. `/checklist` fills out this form (agent auto-generates answers based on spec)
3. Team reviews checklist (human approves or requests changes)
4. Once PASS → `/plan {{FEATURE_NAME}}` becomes available
5. Archive checklist: move to `docs/reviews/{{FEATURE_NAME}}.checklist.md` after `/plan` completes

---
