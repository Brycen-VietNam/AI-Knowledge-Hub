# Plan: citation-quality
Created: 2026-04-15 | Author: /plan | Checklist: PASS (30/30)
Spec: `docs/citation-quality/spec/citation-quality.spec.md`

---

## LAYER 1 — Plan Summary

```
Stories:         3
Sessions est.:   1 (all sequential, no DB migration — fast cycle)
Critical path:   S001 → S002 → S003
Parallel groups:
  G1 (sequential): S001 (rag-agent) — new pure module
  G2 (after G1):   S002 (api-agent) — model + route wiring
  G3 (after G2):   S003 (api-agent) — tests
Token budget total: ~4k
```

### Why fully sequential?
- S002 imports `_parse_citations` from S001 — cannot start until S001 module exists
- S003 tests `cited` field from S002 and `_parse_citations` from S001 — cannot write meaningful tests until both are done
- No story is parallel-safe; story count (3) is small enough that sequencing adds no meaningful delay

### Risk flags
| Risk | Mitigation |
|------|------------|
| A-CQ-01: `cited` indexing over `content_docs` vs `docs` | Implementation note covers both; confirm at /tasks S002 |
| `query.py` already complex — patch must be surgical | Impl note: only 3 changes — import, `cited_set` call, `cited=` in list comp |
| 80 existing tests — must not regress | S003 AC7 explicit regression gate |

---

## LAYER 2 — Per-Story Plan

---

### S001: Citation Parser — `_parse_citations()`
**Agent:** rag-agent | **Group:** G1 | **Depends:** none
**Story type:** sequential (G1 — first)

**Files:**
```
CREATE: backend/rag/citation_parser.py
  — _parse_citations(answer: str, num_docs: int) -> set[int]
  — re.findall(r'\[\s*(\d+)\s*\]', answer) → int list → OOB filter → set
  — stdlib only (re module); no imports from other backend modules
VERIFY: backend/rag/__init__.py
  — check if _parse_citations needs to be exported; add import if missing
```

**Task outline:**
- T001: Create `backend/rag/citation_parser.py` with `_parse_citations()` — pure, sync, stdlib only
- T002: Verify/update `backend/rag/__init__.py` export (if needed)

**Est. tokens:** ~1k
**Test gate:** `pytest tests/rag/test_citation_parser.py` (created in S003 — run after S003)
**Subagent dispatch:** YES — self-contained; no DB, no auth, no imports from other modules

---

### S002: Extend `CitationObject` + Wire into `query.py`
**Agent:** api-agent | **Group:** G2 | **Depends:** S001
**Story type:** sequential (after G1)

**Files:**
```
MODIFY: backend/api/models/citation.py
  — Add: cited: bool = False  (line after lang field)
  — Pydantic v2 field; default False = backward compatible

MODIFY: backend/api/routes/query.py
  — Add import: from backend.rag.citation_parser import _parse_citations
  — After generate_answer() succeeds (~line 201), add:
      cited_set = (
          _parse_citations(llm_response.answer, len(content_docs))
          if llm_response.inline_markers_present
          else set()
      )
  — Modify citations list comprehension (~line 226):
      Track doc position relative to content_docs; for doc d in docs:
        i = content_docs_index_map.get(id(d))  # or enumerate content_docs
        cited=(i in cited_set) if i is not None else False
```

**Index alignment detail (resolve A-CQ-01):**
`content_docs = [d for d in docs if d.content]` (existing line ~194).
`cited_set` indices are 0-based positions in `content_docs`.
When building `citations` over `docs`, a doc has `cited=True` only if it appears in `content_docs` AND its `content_docs` index is in `cited_set`.
Docs not in `content_docs` (no `.content`) always `cited=False`.

**Implementation pattern for citations list comp:**
```python
# Build content_docs index lookup: doc object id → position in content_docs
content_idx = {id(d): i for i, d in enumerate(content_docs)}
cited_set = (
    _parse_citations(llm_response.answer, len(content_docs))
    if llm_response.inline_markers_present
    else set()
)
citations = [
    CitationObject(
        doc_id=str(d.doc_id),
        title=d.title or "",
        source_url=d.source_url,
        chunk_index=d.chunk_index,
        score=round(d.score, 4),
        lang=d.lang or "",
        cited=(content_idx.get(id(d), -1) in cited_set),
    )
    for d in docs
]
```

**Task outline:**
- T001: Edit `citation.py` — add `cited: bool = False`
- T002: Edit `query.py` — import + `cited_set` + `content_idx` + update citations list comp
- T003: Manual smoke-check — confirm OpenAPI `/docs` shows `cited` field in CitationObject schema

**Est. tokens:** ~1.5k
**Test gate:** `pytest tests/api/test_citation.py tests/api/test_query.py` (run after S003 extends them)
**Subagent dispatch:** YES — touches 2 files, both in api-agent scope

---

### S003: Test Coverage — `_parse_citations` Unit + Integration
**Agent:** api-agent | **Group:** G3 | **Depends:** S001 + S002
**Story type:** sequential (after G2)

**Files:**
```
CREATE: tests/rag/test_citation_parser.py
  — 8 unit tests (AC1–AC8 from S001):
      test_basic_markers, test_oob_ignored, test_no_markers,
      test_deduplication, test_empty_inputs, test_whitespace_markers,
      test_pure_sync, test_module_importable
  — 1 CJK test: Japanese answer body + ASCII [1] marker

MODIFY: tests/api/test_citation.py
  — Append (do NOT modify existing 7 tests):
      test_cited_true_when_marker_present
      test_cited_false_when_no_markers  (inline_markers_present=False)
      test_cited_false_oob_marker  ([99] in 3-doc response)
      test_no_chunk_path_citations_empty  (regression AC6)

MODIFY: tests/api/test_query.py (if needed)
  — Add cited field assertions to existing integration mocks
  — Append only — no changes to existing assertions
```

**Task outline:**
- T001: Create `tests/rag/test_citation_parser.py` — 8 unit + 1 CJK test
- T002: Extend `tests/api/test_citation.py` — 4 new integration tests
- T003: Extend `tests/api/test_query.py` — cited field assertions (if integration mocks exist)
- T004: Run full test suite — confirm 80 prior tests pass + new tests pass; check coverage

**Coverage gates:**
```
citation_parser.py : ≥ 95%
citation.py        : ≥ 95%
query.py (net)     : ≥ 90%
```

**Est. tokens:** ~1.5k
**Test gate:** `pytest tests/ -x --tb=short` — 0 failures required
**Subagent dispatch:** YES — test-only story; no production file changes

---

## Execution Order

```
[Session start]
  G1: rag-agent → S001 (T001 create citation_parser.py, T002 verify __init__)
  G2: api-agent → S002 (T001 edit citation.py, T002 edit query.py, T003 smoke)
  G3: api-agent → S003 (T001 create test_citation_parser.py,
                         T002 extend test_citation.py,
                         T003 extend test_query.py,
                         T004 run full suite + coverage)
[Session end → /reviewcode citation-quality]
```

---

## File Change Summary

| File | Action | Story | Agent |
|------|--------|-------|-------|
| `backend/rag/citation_parser.py` | CREATE | S001 | rag-agent |
| `backend/rag/__init__.py` | VERIFY / MODIFY | S001 | rag-agent |
| `backend/api/models/citation.py` | MODIFY | S002 | api-agent |
| `backend/api/routes/query.py` | MODIFY | S002 | api-agent |
| `tests/rag/test_citation_parser.py` | CREATE | S003 | api-agent |
| `tests/api/test_citation.py` | MODIFY (append) | S003 | api-agent |
| `tests/api/test_query.py` | MODIFY (append) | S003 | api-agent |

**No DB migrations. No new endpoints. No frontend changes.**

---
