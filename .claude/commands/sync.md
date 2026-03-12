# /kh.sync

Compress current session into persistent memory. Discard reasoning, keep decisions.

## Usage
```
/kh.sync [--feature <name>] [--force]
```
Auto-triggered when: conversation > 15 turns, switching features, before subagent dispatch.

---

## What agent does (step by step)

```
1. Scan conversation since last /sync
2. Extract ONLY:
   - Decisions made (D-series)
   - Tasks completed or status changed
   - Blockers discovered or resolved
   - Files created or modified
3. Discard:
   - Reasoning chains and "let me think..." steps
   - Intermediate code iterations
   - Repeated context loading messages
   - Any content already in WARM file
4. Update .claude/memory/HOT.md
5. Update .claude/memory/WARM/<feature>.mem.md if feature is active
6. Report: turns compressed, estimated tokens freed
```

---

## HOT.md Update Format

```markdown
## In Progress — replace current entries
- [x] DONE: S001 — pgvector schema (db-agent)
- [ ] ACTIVE: S003 — hybrid retriever (rag-agent, 60%)
- [ ] NEXT: S004 — multilingual reranker

## Recent Decisions — prepend, drop oldest if > 3
- D004: Use HNSW index (not IVFFlat) — better recall at scale — 2024-01-15
- D003: ...

## Blockers — replace
- B001: Embedding model selection pending → blocks S003, S004
```

---

## WARM/<feature>.mem.md Update Block

Agent appends this block at bottom of WARM file, then merges with existing sections:

```markdown
## Sync: {{DATE}} {{TIME}}
Decisions added: [D-ids]
Tasks changed: T001→DONE, T002→IN_PROGRESS
Files touched: [list]
Questions resolved: [Q-ids]
New blockers: [list or none]
```

---

## Token Report (agent outputs after sync)
```
/kh.sync complete
  Turns compressed: 14
  Decisions captured: 2
  Tasks updated: 3
  HOT.md: updated
  WARM/{{feature}}.mem.md: updated
  Est. tokens freed next session: ~3,200
```

---

## Agent Instructions
- Model: **haiku** (claude-haiku-4-5-20251001)
- Token budget: 2k tokens
- Extract only: decisions (ID + decision + rationale), tasks (T-id + status), blockers
- Do NOT re-summarize full conversation history
- Auto-triggered before subagent dispatch and after 15 turns
