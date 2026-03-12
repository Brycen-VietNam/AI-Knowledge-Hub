# /kh.analyze

Analyze codebase context for a task. Run before /implement on any non-trivial task.

## Usage
```
/kh.analyze <task-id> [--depth shallow|deep]
shallow: signatures + imports only (default)
deep:    include function bodies for touched files
```

## Execution Flow
```
1. Load: docs/tasks/<feature>/<story>.tasks.md — target task only
2. Load: WARM/<feature>.mem.md — decisions + prior context
3. Load: ONLY files in task TOUCH list
   shallow → imports + class/function signatures (L1-N per function)
   deep    → full function bodies for TOUCH files only
4. Map: what calls what, what imports what
5. Find: existing patterns to follow
6. Detect: conflicts, missing pieces, rule violations in current code
7. Save: docs/tasks/<feature>/<task-id>.analysis.md
```

## Output Format
```markdown
## Analysis: T002 — RBAC WHERE clause
Depth: shallow | Files scanned: 2

### Code Map (relevant only)
src/rag/retriever.py
  class HybridRetriever:
    __init__(self, db, embedder, bm25)     ← add user_group_ids here
    retrieve(self, query, lang, top_k)     ← add WHERE clause here, L67
    _dense_search(self, vec, top_k)        ← pgvector query at L45
    _bm25_search(self, tokens, top_k)

### Patterns to Follow
- Auth param passing: see src/api/routes/query.py L23 — user pulled from JWT
- pgvector query style: text().bindparams() — see src/db/repo/doc_repo.py L34
- Logging: structured JSON via src/utils/logger.py — import get_logger

### Conflicts / Gaps Found
⚠️  retriever.py L45: hardcoded lang="en" in BM25 path — VIOLATES R005
⚠️  No CJK imports present — MeCab, underthesea not in requirements.txt
❌  SECURITY: _dense_search() uses f-string in SQL at L67 — VIOLATES S001

### RBAC Gap
Current: filter applied in Python AFTER pgvector returns results
Required: WHERE user_group_id = ANY(:group_ids) inside pgvector query
Fix location: src/rag/retriever.py L67 _dense_search()

### Recommended Approach for T002
1. Add `user_group_ids: list[str]` to retrieve() signature
2. Pass to _dense_search() and _bm25_search()
3. In _dense_search(): add `.where(Embedding.user_group_id.in_(user_group_ids))`
4. Add lang branch: if lang in ["ja","zh"]: use MeCab; elif lang=="vi": use underthesea

### Token budget
Estimated implementation: ~2.5k tokens
Analysis saved: docs/tasks/multilingual-search/T002.analysis.md
```

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 5k tokens
- Load only TOUCH files — not full backend/ directory
- Flag security issues as ❌ immediately (do not bury in analysis)
- Save analysis — /implement will load this instead of re-analyzing
