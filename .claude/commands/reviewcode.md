# /reviewcode

## ⚡ PRE-FLIGHT — Model Check (BLOCKING)

This command runs on **claude-opus-4-6**. Do not proceed on sonnet.

If running directly:
1. `/model claude-opus-4-6`
2. Run `/reviewcode <task-id>`
3. `/model claude-sonnet-4-6` — restore after review

If running from orchestrator (/implement post-flight):
→ Dispatch via Agent tool with `model: "opus"` parameter.
→ Do NOT call /reviewcode inline — spawn as subagent.

---

Review implemented code. Post-hook of /implement. Cannot APPROVE if ❌ exists.

## Usage
```
/reviewcode <task-id|file> [--level quick|full|security]
```

Level selection (auto if not specified):
- touches backend/auth/ or backend/rag/ → always `security`
- touches backend/api/ → `full`
- touches frontend/ or backend/bots/ → `quick`
- --level flag overrides auto

---

## Execution Flow

```
1. /rules --task <id> --phase post   — run rule check (auto)
2. Load: task file review_criteria only (not full task file)
3. Load: diff of changed files (not full files, develop is main)
4. Run checks at selected level
5. Output review report
6. Set verdict: APPROVED | CHANGES_REQUIRED | BLOCKED
7. Save: docs/reviews/<task-id>.review.md
8. If APPROVED: update task file status → REVIEWED
```

---

## Quick Level Checks
- [ ] All review_criteria from task file satisfied
- [ ] Test command passes
- [ ] No files outside TOUCH list were modified

## Full Level Checks (all Quick +)
- [ ] Error handling: all external calls have try/except
- [ ] Logging: request_id in all log entries
- [ ] No magic numbers (extract to constants/config)
- [ ] Docstring on new public functions
- [ ] No commented-out dead code

## Security Level Checks (all Full +)
- [ ] R001: RBAC WHERE clause present (RAG tasks)
- [ ] R002: No PII in vector metadata (DB/RAG tasks)
- [ ] R003: verify_token() on all new routes (API tasks)
- [ ] S001: Zero string interpolation in SQL
- [ ] S002: JWT fully validated (auth tasks)
- [ ] S003: Input length/sanitization in place
- [ ] S005: No hardcoded secrets or URLs
- [ ] R006: audit_log.write() called before return

---

## Output Format

```markdown
## Code Review: T002 — RBAC retriever filter
Level: security | Date: 2024-01-15 | Reviewer: Claude

### Task Review Criteria
- [x] user_group_ids param added to retrieve()
- [x] WHERE clause uses parameterized query
- [x] CJK language branch implemented (ja, zh)
- [ ] ❌ vi (Vietnamese) not handled — underthesea import missing

### Full Checks
- [x] try/except on pgvector query
- [x] request_id in log entries
- [x] HNSW config extracted to settings.py
- [x] Docstring on HybridRetriever.retrieve()

### Security Checks
- [x] R001: WHERE user_group_id = ANY(:group_ids) at L67
- [x] R002: embedding metadata = {doc_id, lang, user_group_id} only
- [x] S001: text().bindparams() throughout
- [x] R006: audit_log.write() at L89

### Issues Found

#### ❌ BLOCKER — Must fix before merge
- Task criterion not met: Vietnamese (vi) not handled
  File: backend/rag/retriever.py L45
  Fix: `elif lang == "vi": tokens = underthesea.word_tokenize(query)`

#### ⚠️ WARNING — Should fix
- L112: bare `except:` catches everything including KeyboardInterrupt
  Fix: `except (pgvector.PgVectorError, asyncpg.PostgresError) as e:`

### Suggested test
```python
def test_vietnamese_tokenization():
    result = retriever.retrieve("kiến trúc hệ thống", lang="vi", ...)
    assert result  # should not empty-tokenize Vietnamese
```

---
### Verdict
[ ] APPROVED  [x] CHANGES REQUIRED  [ ] REJECTED

Blockers: 1 — resolve then re-run /reviewcode T002
```

---

## Post-review memory update (agent auto-runs)
If APPROVED:
```
Update WARM/<feature>.mem.md:
  Task T002 status → REVIEWED
  Add decision if any new decisions made during review
```
If CHANGES_REQUIRED:
```
Create follow-up task T002-fix in docs/tasks/<feature>/
  with specific fix items from ❌ blockers section
```

---

## Agent Instructions
- Model: **opus** (claude-opus-4-6)
- Token budget: 3k tokens
- POST-FLIGHT auto-runs `/rules --phase post` (blocks APPROVED if security violations remain)
- Deep reasoning required: prioritize security > performance > style
- Output level (quick/full/security) auto-selected by task type
