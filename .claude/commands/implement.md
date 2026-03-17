# /implement

Implement a specific task. Has pre/post hooks. Never exceeds task scope.

## Usage
```
/implement <task-id> [--dry-run] [--subagent <agent-id>]
```

---

## Execution Flow (agent follows exactly)

```
PRE-FLIGHT (auto, blocking):
  1. /context <task-id>              — load minimal context
  2. /rules --task <id> --phase pre  — check HARD + ARCH rules
     → If ❌ BLOCKER: STOP. Report violation. Do not write code.
  3. Read task file: docs/tasks/<feature>/<task>.tasks.md
     → Confirm: status=TODO or IN_PROGRESS (not DONE)
     → Load: review_criteria, test_cmd, touch_files

IMPLEMENT:
  4. For each file in TOUCH list:
     a. Show: "Modifying <file> — <reason>"
     b. Make MINIMAL change (task scope only)
     c. Show unified diff (not full file)
  5. Run: test_cmd from task file
     → PASS ✅: continue
     → FAIL ❌: show error, fix within scope, re-run once
     → FAIL again: STOP, report, do not guess further

POST-FLIGHT (auto):
  6. /rules --task <id> --phase post  — verify no new violations
  7. Update task status: IN_PROGRESS → DONE in task file
  8. /sync if conversation > 15 turns since last sync
```

---

## Scope Enforcement
```
Agent MUST only touch files listed in task TOUCH list.
If a fix requires touching unlisted file → STOP and report.
"I need to modify backend/auth/middleware.py but it's not in task T002 scope.
 Should I create task T002b or expand T002 scope? (requires plan update)"
```

---

## Subagent Dispatch (--subagent flag)

Agent generates compact handoff (per AGENTS.md template) then outputs:

```markdown
## Ready to dispatch: rag-agent

DISPATCH: rag-agent | Task: T002
CONTEXT: Multilingual hybrid search feature. Adding RBAC filter to pgvector retrieval.
CONSTRAINT: R001 (RBAC at WHERE clause), R005 (CJK tokenizer per language), R007 (p95 < 2s)
TASK: Add user_group_ids filter to HybridRetriever.retrieve() method.
  - Accept user_group_ids: list[str] parameter
  - Pass to pgvector query as: WHERE user_group_id = ANY(:group_ids)
  - Add CJK branch: if lang in ["ja","zh"] use MeCab tokenizer for BM25 query
TOUCH: [backend/rag/retriever.py, tests/rag/test_retriever.py]
NO_TOUCH: [backend/auth/, backend/api/, backend/db/migrations/]
TEST_CMD: pytest tests/rag/test_retriever.py::test_rbac_filter -v
MEMORY: .claude/memory/WARM/multilingual-search.mem.md
RETURN: diff + test_result + memory_update_block
```

---

## Dry Run Mode (--dry-run)
Show implementation plan without writing files:
```markdown
## Dry Run: T002

Would modify:
  backend/rag/retriever.py
    - L23: add user_group_ids param to __init__
    - L67: add WHERE clause to pgvector query
    - L89: add language branch for CJK tokenizer

Would create:
  tests/rag/test_retriever.py::test_rbac_filter (new test)

Test command: pytest tests/rag/test_retriever.py::test_rbac_filter -v

Rules that would be satisfied: R001, R005
Rules still pending: R007 (load test, separate task)

Proceed? (yes / adjust scope first)
```

---

## Memory comment in code
Add at top of any complex function implemented:
```python
# Spec: docs/specs/multilingual-search.spec.md#S002
# Task: T002 — RBAC filter at retrieval
# Decision: D001 — HNSW index, D002 — BM25 weight 0.3
```

---

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 6k tokens
- PRE-FLIGHT auto-runs `/rules --phase pre` (blocks on HARD violations)
- POST-FLIGHT auto-runs `/sync` if conversation > 15 turns
- Never exceed TOUCH scope without creating follow-up task
