# /tasks

Break plan stories into atomic, reviewable tasks. Max 50 lines per task.

## Usage
```
/tasks <feature-name> [--story <S-id>] [--agent <agent-id>]
```

## Examples
```
/tasks multilingual-search --story S001
/tasks multilingual-search --agent db-agent   ← all stories for that agent
/tasks multilingual-search                    ← all stories (sequential output)
```

## Execution Flow
```
1. Load: docs/plans/<feature>.plan.md — Layer 2 (specific story)
2. Load: WARM/<feature>.mem.md (context + decisions)
3. Load: relevant rules files for agent scope (from CLAUDE.md budget table)
4. Break story into atomic tasks (max 50 lines each)
5. Assign parallel/sequential tags per task
6. Copy template: .claude/templates/tasks/_template.tasks.md
7. Save: docs/tasks/<feature>/<story-id>.tasks.md
8. Update: WARM/<feature>.mem.md — add task list + status board
```

## Task Size Rules
```
Max 50 lines of code changed per task → split if larger
One logical change per task (not "implement feature X")
DB tasks: always include rollback SQL
Every task: has explicit review_criteria + test_cmd
```

## Granularity Examples
```
TOO BIG ❌:  "Implement RBAC in retriever"
RIGHT    ✅:  T001: Add user_group_ids param to HybridRetriever.__init__
             T002: Add WHERE clause to pgvector query in retrieve()
             T003: Add language branch for CJK tokenizer
             T004: Write pytest for RBAC filter isolation
```

## Parallel tagging
```
T001 parallel: safe      ← no dependency
T002 parallel: after:T001
T003 parallel: safe      ← independent of T001/T002
T004 parallel: after:T002,T003  ← needs both done
```

## Output
```
/tasks complete
  Story: S001 | Feature: multilingual-search
  Tasks created: 4
  File: docs/tasks/multilingual-search/S001.tasks.md
  Parallel groups: G1[T001,T003], G2[T002], G3[T004]
  Est. total tokens to implement: ~6k
  Next: /analyze T001
```

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 3k tokens
- Load plan Layer 2 for the specific story only
- Each task must map to exactly one file change (prefer) or closely related set
- Output Layer 1 task summary table first, then Layer 2 on request
