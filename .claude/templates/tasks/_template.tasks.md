# Tasks Template — Atomic & Reviewable
# Usage: /tasks copies this to docs/tasks/<feature>/<story>.tasks.md

---

# Tasks: {{FEATURE}} / {{STORY_ID}} — {{STORY_TITLE}}
Created: {{DATE}} | Agent: {{AGENT_ID}} | Status: TODO

---

## LAYER 1 — Story Task Summary

| Field | Value |
|-------|-------|
| Story | {{STORY_ID}}: {{STORY_TITLE}} |
| Total tasks | N |
| Parallel groups | G1: [T001,T002], G2: [T003] |
| Critical path | T001 → T003 → T004 |
| Agent | {{AGENT_ID}} |
| Est. session | 1 |

### Task Status Board
| Task | Title | Status | Parallel | Blocks |
|------|-------|--------|----------|--------|
| T001 | | TODO | — | T003 |
| T002 | | TODO | T001 | — |
| T003 | | TODO | — | T004 |

---

## LAYER 2 — Task Detail

<!-- Max 50 lines of code per task. If larger, split. -->

### T001: {{Task Title}}

**Status**: TODO | IN_PROGRESS | DONE | BLOCKED

**File(s)**
- `src/<path>/<file>.py` — action: create | modify | delete

**Change description** (3-5 lines)
_What exactly changes. No full implementation._

**Review criteria** (agent checks these in /reviewcode)
- [ ] _
- [ ] _
- [ ] Rule satisfied: R00X

**Test command**
```bash
pytest tests/<path>/<test>.py::<test_name> -v
```

**Rollback** _(DB/migration tasks only)_
```sql
-- rollback
```

**Parallel**: safe | after:T00X
**Size estimate**: ~N lines changed

---
<!-- End T001 -->

<!-- Repeat for each task -->
