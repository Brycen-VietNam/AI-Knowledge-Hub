# AGENTS.md — Subagent Orchestration Protocol
# Claude Code reads this automatically for multi-agent tasks.

---

## Agent Registry

| Agent ID        | Owns                                      | Entry dirs              | Model          | Can parallel with         |
|-----------------|-------------------------------------------|-------------------------|----------------|---------------------------|
| db-agent        | PostgreSQL schema, migrations, pgvector   | backend/db/             | sonnet         | rag-agent, api-agent      |
| rag-agent       | Retriever, embeddings, BM25, reranker     | backend/rag/            | sonnet         | db-agent, frontend-agent  |
| api-agent       | FastAPI routes, middleware, serializers   | backend/api/            | sonnet         | db-agent, frontend-agent  |
| auth-agent      | OIDC, API-key, RBAC, JWT claims           | backend/auth/           | sonnet         | NONE (always sequential)  |
| frontend-agent  | React/Vite SPA, components                | frontend/               | haiku          | api-agent, rag-agent      |
| bot-agent       | Teams/Slack adapters                      | backend/bots/           | haiku          | api-agent                 |
| review-agent    | Code review, security audit               | any (read-only)         | opus           | NONE                      |

## Parallelization Rules
```
PARALLEL OK:
  db-agent + rag-agent          (schema + retriever, no shared files)
  api-agent + frontend-agent    (endpoint + UI, API contract must be locked first)
  bot-agent + api-agent         (adapter + endpoint)
  rag-agent + frontend-agent    (no shared files)

SEQUENTIAL REQUIRED:
  auth-agent → everything else  (auth changes are foundational)
  db migration → db models      (migration first, then ORM)
  /specify → /plan → /tasks     (SDD phases are sequential)
  any two agents touching same file
```

---

## Compact Handoff Template

> Orchestrator MUST use this format when dispatching. No prose. No full file contents.

```markdown
## DISPATCH: <agent-id> | Task: <T-id>
CONTEXT: <2 sentences max about feature>
CONSTRAINT: <2-3 HARD rules relevant to this task, from rules/HARD.md>
TASK: <exact task title and definition, 3-5 lines>
TOUCH: [src/path/file.py, src/path/other.py]
NO_TOUCH: [src/auth/, src/api/routes/]
TEST_CMD: pytest tests/<path>/<test_file.py>::<test_name> -v
MEMORY: .claude/memory/WARM/<feature>.mem.md
RETURN: diff + test_result + memory_update_block
```

## Return Format (subagent must use)
```markdown
## RESULT: <agent-id> | Task: <T-id>
STATUS: DONE | BLOCKED | PARTIAL
TEST: PASS ✅ | FAIL ❌ — <error summary if fail>
FILES_CHANGED: [list]
DECISIONS: [any new decisions made, for memory update]
BLOCKERS: [list, empty if none]
MEMORY_UPDATE:
  status: <new status>
  decisions: [list]
  files_touched: [list]
```

---

## Memory Sync on Dispatch

Before dispatching ANY subagent:
1. Run `/sync` to flush session → HOT.md + WARM/<feature>.mem.md
2. Include `MEMORY:` line in handoff pointing to WARM file
3. Subagent reads WARM file, NOT full conversation

After subagent returns:
1. Orchestrator reads RESULT block only (not full subagent output)
2. Updates HOT.md status
3. Merges MEMORY_UPDATE into WARM/<feature>.mem.md
4. Does NOT re-read all changed files (trusts test result)

---

## Token Budget for Orchestration
- Dispatch package: max 500 tokens
- Subagent context: max 6k tokens (per CLAUDE.md budget)
- Result package: max 300 tokens
- Cross-agent communication: via files only, never via conversation relay

---

## Model Assignment Rationale

| Tier    | Model          | Model ID                        | Use when                                      |
|---------|----------------|---------------------------------|-----------------------------------------------|
| Opus    | claude-opus-4-6    | `claude-opus-4-6`           | Deep reasoning, security audit, code review   |
| Sonnet  | claude-sonnet-4-6  | `claude-sonnet-4-6`         | Logic-heavy coding, spec writing, planning    |
| Haiku   | claude-haiku-4-5   | `claude-haiku-4-5-20251001` | File reads, templated output, simple adapters |
