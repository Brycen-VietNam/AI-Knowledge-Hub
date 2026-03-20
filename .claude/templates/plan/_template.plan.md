# Plan Template — Two-Layer Structure
# Usage: /plan copies this to docs/plans/<feature>.plan.md

---

# Plan: {{FEATURE_NAME}}
Created: {{DATE}} | Based on spec: v{{N}} | Checklist: PASS

---

## LAYER 1 — Plan Summary
> Load this section for sprint planning and status reviews.

| Field | Value |
|-------|-------|
| Total stories | N |
| Sessions estimated | N |
| Critical path | S001 → S00N |
| Token budget total | ~Nk tokens |

### Parallel Execution Groups
```
G1 (start immediately, run together):
  S001 — db-agent    — pgvector schema
  S002 — rag-agent   — BM25 indexer setup

G2 (after G1 complete):
  S003 — rag-agent   — hybrid retriever

G3 (after G2, run together):
  S004 — api-agent   — /v1/query route
  S005 — frontend-agent — search UI
```

### Agent Assignments
| Agent | Stories | Can start |
|-------|---------|-----------|
| db-agent | S001 | immediately |
| rag-agent | S002, S003 | S002 immediately, S003 after S001 |
| api-agent | S004 | after S003 |
| auth-agent | — | N/A this feature |
| frontend-agent | S005 | after S004 API contract locked |

### Risk
| Risk | Mitigation |
|------|------------|
| Embedding model latency | Async + 1800ms timeout with BM25 fallback |
| CJK tokenizer missing | Add to requirements.txt in S001 |

---

## LAYER 2 — Story Plans
> Load one story at a time during /tasks phase.

<!-- Repeat per story -->

### S001: {{Story Title}}
**Agent**: {{agent-id}}
**Parallel group**: G1
**Depends on**: none

**Files**
| Action | Path |
|--------|------|
| CREATE | backend/db/migrations/00N_description.sql |
| CREATE | backend/db/models/document_embedding.py |
| MODIFY | backend/db/models/__init__.py |

**Subagent dispatch**: YES / NO
**Est. tokens**: ~Nk
**Test entry**: `pytest tests/db/test_embedding_model.py`

**Story-specific notes**
_Short notes for agent. Key decisions, gotchas._

**Outputs expected**
- [ ] Migration file with HNSW index
- [ ] ORM model with Vector(1536) + user_group_id FK
- [ ] Passing tests

---
<!-- End S001 -->
