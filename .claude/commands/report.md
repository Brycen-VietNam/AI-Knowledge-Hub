# /report

Generate final report after feature implementation complete.
Summarizes changes, test results, blockers, rollback plan, lessons learned.

## Usage
```
/report <feature-name> [--dry-run] [--include-archive]
```

## Execution Flow
```
1. Load: docs/specs/<feature>.spec.md (Layer 1, for AC reference)
2. Load: docs/plans/<feature>.plan.md (for what was planned)
3. Load: docs/tasks/<feature>/*.tasks.md (all task files, check all DONE)
4. Load: .claude/memory/WARM/<feature>.mem.md (get decisions, blockers)
5. Run: git diff develop..HEAD --stat (code changes summary)
6. Load: test results from /implement + /reviewcode logs
7. Compile: changes, test results, AC coverage, blockers, rollback plan
8. Save: docs/reports/<feature>.report.md
9. Ask: approval from tech lead + product owner
10. If approved: move WARM file → COLD/<feature>.archive.md
11. Add one row to COLD/README.md Archive Index (feature, completed date, stories, tests, unblocks, report path)
12. Update: HOT.md — remove from "In Progress"
```

## Output Format

### Final Report File
**Path:** `docs/reports/<feature>.report.md`

**Sections:**
- Executive Summary (status, duration, key metrics)
- Changes Summary (code, database, config, docs)
- Test Results (unit / integration / black-box)
- Code Review Results (functionality, security, performance, style, tests)
- Acceptance Criteria Status (all ACs verified PASS)
- Blockers & Open Issues (what was deferred + why)
- Rollback Plan (procedure, downtime, data loss risk)
- Knowledge & Lessons Learned (what went well, improvements, rule updates)
- Sign-Off (tech lead, product owner, QA lead approval)

### Example Output
```markdown
## /report complete

Report: docs/reports/multilingual-search.report.md
Status: ✓ COMPLETE
AC Coverage: 12/12 (100%)
Test Pass Rate: 34/34 (100%)

### Sign-Off Status
- [ ] Tech Lead approval: _pending_
- [ ] Product Owner approval: _pending_
- [ ] QA Lead approval: _pending_

After all approvals, run:
  /report multilingual-search --finalize
→ Archives WARM/<feature> → COLD/<feature>.archive.md
→ Updates HOT.md
→ Feature marked DONE
```

## Requirements for DONE Status

Before `/report --finalize` is allowed:

### Code
- [ ] All changes committed to feature branch
- [ ] Code review completed (APPROVED)
- [ ] No review blockers remain

### Tests
- [ ] Unit tests: 100% pass rate
- [ ] Integration tests: 100% pass rate (or N/A if none)
- [ ] Black-box tests: 100% pass rate (or N/A if manual)
- [ ] No test failures in final run

### Acceptance Criteria
- [ ] All AC verified PASS (traced in AC coverage table)
- [ ] None marked PARTIAL without sign-off
- [ ] Zero AC marked FAIL

### Documentation
- [ ] Architecture changes documented (if any)
- [ ] API docs updated (if endpoints changed)
- [ ] CHANGELOG entry added
- [ ] Rollback procedure written + tested in staging

### Blockers
- [ ] All CRITICAL blockers resolved
- [ ] Any DEFERRED blockers have: owner, due date, jira ticket
- [ ] Product owner approved deferral list

### Sign-Off
- [ ] Tech Lead reviewed report: ✓ APPROVED
- [ ] Product Owner reviewed report: ✓ APPROVED
- [ ] QA Lead reviewed report: ✓ APPROVED

---

## Dry-Run Mode (--dry-run)

Show what report would contain WITHOUT saving:
```
/report multilingual-search --dry-run

→ Shows: summary, changes count, test results, blockers
→ Does NOT save to disk
→ Does NOT move to archive
```

---

## Finalization (--finalize)

After all approvals, archive feature:
```
/report multilingual-search --finalize

→ Moves: WARM/<feature>.mem.md → COLD/<feature>.archive.md
→ Adds row to COLD/README.md Archive Index
→ Updates: HOT.md — removes from "In Progress"
→ Creates: CHANGELOG entry with deployment notes
→ Output: "Feature marked DONE. Archive: COLD/<feature>.archive.md"
```

---

## Agent Instructions
- Model: **haiku** (claude-haiku-4-5-20251001)
- Token budget: 4k tokens
- Do NOT auto-approve. Report all blockers + open issues.
- Dry run (--dry-run) useful for review before human approval.
- Finalize only AFTER all 3 stakeholder approvals collected.
- If any AC marked FAIL or PARTIAL: halt and report.
- If test pass rate < 100%: warn but allow (with sign-off).

---

## Related Commands
- `/implement <task>` — generate test results + code changes
- `/reviewcode <task>` — generate code review
- `/checklist <feature>` — pre-plan validation (used for AC reference in report)

---
