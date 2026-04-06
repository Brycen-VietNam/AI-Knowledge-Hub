# /plan

Generate 2-layer implementation plan from a passed checklist.
Requires: /checklist PASS before running.

## Usage
```
/plan <feature-name> [--parallel]
```

## Execution Flow
```
1. Verify: docs/<feature>/reviews/checklist.md status = PASS
   → If not: "Run /checklist first. Checklist status: <status>"
2. Load: docs/<feature>/spec/<feature>.spec.md
3. Load: .claude/memory/HOT.md (check active sprint capacity)
4. Load: .claude/rules/ARCH.md (agent scope rules)
5. Generate Layer 1 plan summary
6. Generate Layer 2 story plans (one per spec story)
7. Identify parallel groups
8. Assign agents per AGENTS.md registry
9. Save: docs/<feature-name>/plan/<feature-name>.plan.md
10. Update: WARM/<feature>.mem.md — add plan path + critical path
```

## Parallelization Rules (from AGENTS.md)
```
Tag each story:
  parallel-safe  — can run concurrently with tagged peers
  sequential     — must complete before next story
  after:S00X     — depends on specific story

Group parallel-safe stories → subagent dispatch batches
Never parallelize: auth stories + anything else
Never parallelize: two stories touching same file
```

## Output: docs/<feature>/plan/<feature>.plan.md

### Layer 1 — Plan Summary
```markdown
## Plan: multilingual-search
Stories: 5 | Sessions est.: 2 | Critical path: S001→S003→S005
Parallel groups:
  G1 (run together): S001 (db-agent), S002 (rag-agent)
  G2 (after G1): S003 (rag-agent)
  G3 (after G2): S004 (api-agent), S005 (frontend-agent)
Token budget total: ~18k
```

### Layer 2 — Per-Story Plan
```markdown
### S001: pgvector schema for embeddings
Agent: db-agent | Parallel: G1 | Depends: none
Files:
  CREATE: backend/db/migrations/002_embeddings.sql
  CREATE: backend/db/models/document_embedding.py
  MODIFY: backend/db/models/__init__.py
Est. tokens: ~2k
Test: pytest tests/db/test_embedding_model.py
Subagent dispatch: YES (self-contained)
```

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 4k tokens
- Load spec Layer 1 only for planning (not full story details)
- Output Layer 1 first → wait for team review → then Layer 2
- Flag if any story has no clear agent owner
