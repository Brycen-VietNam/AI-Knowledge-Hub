# /kh.rules

Check work against rules. Auto-hooked into /implement (pre) and /reviewcode (post).

## Usage
```
/kh.rules [--task <id>] [--file <path>] [--phase pre|post] [--all]
--phase pre:  run before implement — catch design violations
--phase post: run after implement — catch code violations
--all:        run all rule files regardless of task type
```

## Auto-hook behavior
- /implement calls: /rules --task <id> --phase pre  (blocks if ❌)
- /reviewcode calls: /rules --task <id> --phase post (blocks APPROVED if ❌)
- Agent MUST NOT proceed with implement if pre-check has ❌ BLOCKER

---

## Rule Files to Load per Task Type

```
Task touches src/rag/     → HARD.md (R001,R005,R007) + ARCH.md (A001,A004)
Task touches src/api/     → HARD.md (R003,R004,R006) + SECURITY.md (S001,S004)
Task touches src/auth/    → HARD.md (R003) + SECURITY.md (all)
Task touches src/db/      → HARD.md (R002) + ARCH.md (A006) + SECURITY.md (S001)
Task touches frontend/    → SECURITY.md (S003) + ARCH.md (A005)
Task touches src/bots/    → HARD.md (R003,R004) + ARCH.md (A005)
--all flag                → all rule files
```

---

## Check Protocol per Rule

For each applicable rule, agent must:
1. Read the CHECK line from rule definition
2. Run check against task scope (not full codebase)
3. Output: ✅ PASS | ⚠️ PENDING (in task scope, not done yet) | ❌ VIOLATION

---

## Output Format

```markdown
## Rule Check: T002 — RBAC retriever filter
Phase: pre-implement | Scope: src/rag/retriever.py

### HARD Rules
| Rule | Description | Status | Location |
|------|-------------|--------|----------|
| R001 | RBAC before retrieval | ⚠️ PENDING | retriever.py — task adds this |
| R005 | CJK tokenizer | ❌ VIOLATION | L45: whitespace split on all langs |
| R007 | Latency < 2s | ⚠️ NOT TESTABLE | needs load test in T008 |

### ARCH Rules
| Rule | Description | Status | Location |
|------|-------------|--------|----------|
| A004 | Hybrid weights env vars | ✅ PASS | config.py L12-13 |

### Security Rules
| Rule | Description | Status |
|------|-------------|--------|
| S001 | SQL injection | ✅ PASS | parameterized throughout |

---
### Summary
✅ Pass: 2  |  ⚠️ Pending/Not-testable: 2  |  ❌ Violations: 1

### BLOCKERS (must fix before proceeding)
❌ R005 — L45 in retriever.py uses whitespace split.
   Fix: detect language → route to MeCab (ja), underthesea (vi), or default tokenizer
   Reference: .claude/rules/HARD.md#R005
```

---

## Violation Escalation

| Severity | When | Agent action |
|----------|------|--------------|
| ❌ HARD (HARD.md) | pre-implement | STOP — do not write any code |
| ❌ ARCH (ARCH.md) | pre-implement | STOP — flag for tech lead |
| ⚠️ SECURITY | post-implement | Block APPROVED status, list fixes |
| ✅ / ⚠️ PENDING | any | Continue — note in review |

---

## Agent Instructions
- Model: **haiku** (claude-haiku-4-5-20251001)
- Token budget: 2k tokens
- Auto-hooked into `/kh.implement` (--phase pre) and `/kh.reviewcode` (--phase post)
- Load rule files for task type only (db-agent tasks → HARD + ARCH + SECURITY, etc.)
- Return structured violation table + verdict
