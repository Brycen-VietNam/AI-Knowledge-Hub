# Final Report: {{FEATURE_NAME}}
Created: {{DATE}} | Feature spec: `docs/specs/{{FEATURE_NAME}}.spec.md`

---

## Executive Summary

**Status:** ✓ COMPLETE / ⚠️ PARTIAL / ❌ BLOCKED
**Duration:** _[start date → end date]_
**Stories completed:** N / N
**Test pass rate:** N / N (N%)

### What Changed
_2-3 sentence summary of what was delivered._

### Key Metrics
| Metric | Value |
|--------|-------|
| Lines of code added | N |
| Files modified | N |
| Test coverage added | N% |
| AC coverage | N / N (N%) |
| Bugs found + fixed | N |
| Performance impact | _[% latency change, if any]_ |

---

## Changes Summary

### Code Changes
```bash
# Run: git diff <base-branch>..HEAD --stat
# Shows file-by-file diff stat
```

### Database Changes
- [ ] Schema migrations? (if yes, list migrations)
- [ ] Data migration? (if yes, describe)
- [ ] Indexes added? (if yes, list)
- [ ] Rollback procedure documented?

### Configuration Changes
- [ ] Environment variables? (if yes, list + values for prod/staging)
- [ ] Feature flags? (if yes, default on/off?)
- [ ] API version increments? (if yes, /v2 routes?)

### Documentation Changes
- [ ] API docs updated? (OpenAPI spec, examples?)
- [ ] Architecture docs updated? (ARCH.md?)
- [ ] Setup/deployment docs updated?
- [ ] CHANGELOG entry added?

---

## Test Results

### Unit Tests
```bash
# Run: pytest tests/ -v --tb=short
# Paste output or summary
```
**Status:** ✓ PASS / ❌ FAIL
**Coverage:** _[report link or % from pytest-cov]_

### Integration Tests
```bash
# Run: pytest tests/integration/ -v
```
**Status:** ✓ PASS / ❌ FAIL
**Tests:** _[count + duration]_

### Black-box Tests
**Executed by:** _[name]_
**Date:** _[YYYY-MM-DD]_
**Results:**
- [ ] Happy path tests: ✓ PASS / ❌ FAIL
- [ ] Edge case tests: ✓ PASS / ❌ FAIL
- [ ] Permission tests (RBAC): ✓ PASS / ❌ FAIL
- [ ] Performance tests (p95 < 2s?): ✓ PASS / ⚠️ WARN / ❌ FAIL

**Issues found:** N
- [ ] Issue 1: _[description]_ → Fixed / Deferred
- [ ] Issue 2: _[description]_ → Fixed / Deferred

### Code Review Results
**Reviewed by:** _[name(s)]_
**Date:** _[YYYY-MM-DD]_

| Category | Status | Notes |
|----------|--------|-------|
| Functionality | ✓ | _[any issues found?]_ |
| Security | ✓ | _[any violations?]_ |
| Performance | ✓ | _[any bottlenecks?]_ |
| Code style | ✓ | _[any violations?]_ |
| Test quality | ✓ | _[any gaps?]_ |

**Approval:** ✓ APPROVED / ❌ BLOCKED
**Comments:** _[if blocked, list items]_

---

## Acceptance Criteria Status

| Story | AC | Status | Evidence |
|-------|-----|--------|----------|
| S001 | AC1 | ✓ PASS | _[test case / screenshot / ticket]_ |
| S001 | AC2 | ✓ PASS | |
| S002 | AC1 | ✓ PASS | |

**Overall AC coverage:** N / N (N%) ✓ COMPLETE

---

## Blockers & Open Issues

### Resolved During Implementation
- [ ] Issue 1: _[description]_ → Resolution: _[what was done]_
- [ ] Issue 2: → Resolution:

### Remaining (Deferred)
- [ ] Issue 1: _[description]_ → Deferred reason: _[why]_ → Owner: _[name]_ → Due: _[date]_
- [ ] Issue 2: → Deferred reason: → Owner: → Due:

**None remaining:** _[check if all clear]_ ✓

---

## Rollback Plan

### If Rollback Needed

**Trigger:** _[describe conditions that would trigger rollback, e.g., "p95 latency > 5s in prod", "data loss", etc.]_

**Procedure:**
1. Stop service: `systemctl stop knowledge-hub-api`
2. Revert database: `psql < rollback/{{FEATURE_NAME}}_migration_undo.sql`
3. Revert code: `git revert <commit-hash>`
4. Restart service: `systemctl start knowledge-hub-api`
5. Verify: `curl https://api.example.com/v1/health`

**Estimated downtime:** _[minutes]_
**Data loss:** None / _[describe if any]_

### Rollback Validation
- [ ] Rollback tested in staging? (date: _[YYYY-MM-DD]_)
- [ ] Stakeholders notified of rollback procedure?
- [ ] Monitoring alerts set up for rollback triggers?

---

## Knowledge & Lessons Learned

### What Went Well
- _[pattern, tool, decision that worked]_
- _[another positive outcome]_

### What Could Improve
- _[blocker, rework, complexity that surprised]_
- _[suggestion for next time]_

### Updates to Project Knowledge
**Files updated in next phases:**
- [ ] `.claude/memory/COLD/{{FEATURE_NAME}}.archive.md` — archived (feature DONE)
- [ ] `.claude/rules/` — any new rules discovered? (if yes, update HARD.md / ARCH.md)
- [ ] `docs/architecture/` — any architecture patterns to document?
- [ ] `docs/standards/` — any coding standards to formalize?

---

## Sign-Off

**Feature Status:** ✓ COMPLETE / ⚠️ PARTIAL / ❌ BLOCKED

**Approved by:**
- [ ] Tech Lead: _[name]_ — _[date]_
- [ ] Product Owner: _[name]_ — _[date]_
- [ ] QA Lead: _[name]_ — _[date]_

**Deployment readiness:** ✓ READY / ❌ NOT READY
**Target deployment:** _[date/sprint]_

---

## Appendix

### A. Git Log
```
git log <base-branch>..HEAD --oneline
```

### B. Related Tickets
- Jira: _[list issue keys]_
- GitHub: _[list issue URLs]_

### C. Architecture Diagrams
_[Link to diagrams or description of system changes]_

### D. Performance Benchmarks
_[If applicable: before/after latency, throughput, memory usage]_

---
