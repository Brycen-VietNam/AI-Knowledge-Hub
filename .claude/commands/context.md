# /kh.context

Load ONLY the context needed. Never load full project.

## Usage
```
/kh.context <feature-or-task-id> [--minimal | --full]
--minimal: HOT.md + WARM/<feature> summary section only
--full: HOT.md + full WARM/<feature> + task file
default: HOT.md + WARM/<feature> (full) + task file if task-id given
```

---

## Loading Algorithm

```
INPUT: feature name OR task-id (e.g. "multilingual-search" or "T002")

IF task-id:
  1. Read docs/tasks/<feature>/<task>.tasks.md → get feature name + files to touch
  2. Load HOT.md
  3. Load WARM/<feature>.mem.md
  4. Load ONLY the lines referenced in task from src/ files
     (e.g. task says "modify retriever.py L40-L90" → load ONLY those lines)
  5. Load relevant rules: read task type → map to rules files
     - DB task → rules/HARD.md R001,R002 + rules/ARCH.md A006
     - API task → rules/HARD.md R003,R004 + rules/SECURITY.md
     - RAG task → rules/HARD.md R001,R005,R007
     - Auth task → rules/SECURITY.md (all)

IF feature name:
  1. Load HOT.md
  2. Load WARM/<feature>.mem.md
  3. Do NOT load src/ files (wait for task assignment)
```

---

## Output Format

```markdown
## Context Loaded
Feature: multilingual-search | Task: T002
Mode: default

### Files in context
- .claude/memory/HOT.md ✅
- .claude/memory/WARM/multilingual-search.mem.md ✅
- src/rag/retriever.py (L1-12 imports, L40-90 HybridRetriever class) ✅
- [skipped] src/rag/bm25_indexer.py — not in task scope

### Rules active for this task
- HARD: R001 (RBAC before retrieval), R005 (CJK tokenization), R007 (latency)
- ARCH: A004 (hybrid weights parameterized)
- [skipped] SECURITY.md — not auth task

### Budget
Loaded: ~3,800 tokens | Budget: 6,000 tokens | Remaining: 2,200 tokens ✅

### Status from HOT.md
Sprint: RAG pipeline foundation
Blockers: B001 — embedding model TBD (affects this task)
```

---

## Anti-patterns (agent must avoid)
- ❌ Loading entire backend/ directory to "understand codebase"
- ❌ Loading all WARM files at session start
- ❌ Re-loading files already in context from this session
- ❌ Loading COLD archives unless user explicitly asks

---

## Agent Instructions
- Model: **haiku** (claude-haiku-4-5-20251001)
- Token budget: 2k tokens
- Load minimal + tiered: HOT.md always, then targeted WARM file
- Prevent context bloat: only load what task requires
- Auto-called at session start and feature switches
