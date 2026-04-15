## Code Review: citation-quality — S001 + S002 + S003
Level: security | Date: 2026-04-15 | Reviewer: Claude (opus)
Branch: feature/citation-quality | Stories: S001, S002, S003

---

### Task Review Criteria

#### S001 — Citation Parser `_parse_citations()`
- [x] `_parse_citations("See [1] and [2].", 3)` → `{0, 1}` ✅ (citation_parser.py L35–38)
- [x] `_parse_citations("See [99].", 3)` → `set()` (D-CQ-03 OOB ignored) ✅
- [x] `_parse_citations("", 3)` → `set()` (empty answer guard) ✅
- [x] `_parse_citations("See [1].", 0)` → `set()` (num_docs=0 guard) ✅
- [x] `_parse_citations("[ 1 ]", 3)` → `{0}` (whitespace inside brackets OK) ✅ — regex `\[\s*(\d+)\s*\]`
- [x] stdlib only — only `import re` ✅
- [x] sync function — not async ✅
- [x] Importable via `from backend.rag.citation_parser import _parse_citations` ✅
- [x] Importable via `from backend.rag import _parse_citations` ✅ (`__init__.py` updated)

#### S002 — Extend CitationObject + Wire into query.py
- [x] `cited: bool = False` added to `CitationObject` (backward-compatible, D-CQ-01) ✅
- [x] `_parse_citations` imported in `query.py` ✅ (L38)
- [x] `content_idx = {id(d): i for i, d in enumerate(content_docs)}` built before list comp ✅ (L229)
- [x] `cited_set` computed conditionally on `inline_markers_present` (D-CQ-02 fast path) ✅ (L231–235)
- [x] `cited=(content_idx.get(id(d), -1) in cited_set)` in list comp ✅ (L244)
- [x] Non-content docs (`content=None`) always `cited=False` via `content_idx.get(id(d), -1)` sentinel (D-CQ-05) ✅
- [x] 42 prior tests PASS — no regression ✅

#### S003 — Test Coverage
- [x] `tests/rag/test_citation_parser.py` — 13 tests: basic, OOB, dedup, empty/zero, whitespace, sync, import×2, CJK ✅
- [x] `tests/api/test_citation.py` — 4 cited-field tests appended ✅ (D-CQ-01/02/03 + regression)
- [x] `tests/api/test_query.py` — 4 cited-field assertions ✅ (D-CQ-01/02/04/05)
- [x] Full suite: 389 pass, 22 skip, 0 new failures ✅
- [x] `citation_parser.py` coverage: **100%** ✅ (13 pass, clean measurement)

---

### Full Checks
- [x] Error handling: `_parse_citations` is pure — no external calls, no exception paths needed ✅
- [x] `query.py`: all external calls (`search`, `generate_answer`) wrapped in `try/except` with `asyncio.wait_for` ✅
- [x] `request_id` present in all error log entries (L152, L177, L221) ✅
- [x] No magic numbers: `_RETRIEVAL_TIMEOUT`, `_LLM_TIMEOUT`, `_LOW_CONFIDENCE_THRESHOLD` extracted to module-level constants ✅
- [x] Docstring on `_parse_citations()` — complete with Args/Returns/behavior docs ✅
- [x] No commented-out dead code ✅

---

### Security Checks

**R001 — RBAC WHERE clause (RAG tasks)**
- [x] `_parse_citations` is pure stdlib — no DB access, R001 not applicable to S001 ✅
- [x] `query.py` passes `user_group_ids` to `search()` (L165) — RBAC enforced at retriever layer (pre-existing, not regressed) ✅

**R002 — No PII in vector metadata**
- [x] `citation_parser.py` operates on string only — no metadata written ✅
- [x] `CitationObject` fields: `doc_id`, `title`, `source_url`, `chunk_index`, `score`, `lang`, `cited` — no user PII ✅

**R003 — verify_token on all new routes**
- [x] No new routes added in this feature ✅
- [x] Existing `/v1/query` retains `Depends(verify_token)` (L122) ✅

**R006 — audit_log.write() before return**
- [x] `background_tasks.add_task(_write_audit, ...)` at L181 — fires before any return path ✅
- [x] Citation-quality changes do not introduce any new return paths before the audit task ✅

**S001 — SQL injection**
- [x] `citation_parser.py` — no SQL, N/A ✅
- [x] `citation.py` — Pydantic model, no SQL ✅
- [x] `query.py` S002 additions — no SQL; DB access only in `_write_audit` via SQLAlchemy ORM ✅

**S003 — Input sanitization**
- [x] Query sanitization (`strip_control_chars`) pre-existing at `QueryRequest.strip_control_chars` (L66–70) ✅
- [x] `_parse_citations` input is `llm_response.answer` (internal, post-LLM) — not raw user input ✅

**S005 — No hardcoded secrets or URLs**
- [x] Zero hardcoded secrets in all 5 touched files ✅

---

### Issues Found

#### ⚠️ WARNING — Minor, non-blocking
1. **`content_idx` uses `id(d)` (Python object identity)** — This is correct within a single request lifecycle since `docs` and `content_docs` are built from the same list in the same frame. However, if `docs` were ever replaced (e.g., by a new list copy), identity would break silently. The current code is safe but brittle. Consider documenting the invariant in a comment.
   - File: [backend/api/routes/query.py:229](backend/api/routes/query.py#L229)
   - Impact: Low — only a future maintenance concern, not a current bug.

2. **`__all__` in `backend/rag/__init__.py` exports `_parse_citations` with leading underscore** — convention signals "private" but it's in `__all__`. Minor inconsistency; may confuse consumers. The task decision records this is intentional (module-private convention from within the package), but a brief comment would clarify.
   - File: [backend/rag/__init__.py:4](backend/rag/__init__.py#L4)
   - Impact: Negligible — documentation/style only.

#### No blockers found.

---

### Suggested test (optional — post-approval)
```python
def test_content_idx_identity_stable():
    """Guard: content_docs elements are same objects as in docs (no list copy)."""
    docs = [make_doc(content="text")]
    content_docs = [d for d in docs if d.content]
    content_idx = {id(d): i for i, d in enumerate(content_docs)}
    assert id(docs[0]) in content_idx  # identity preserved, not copied
```

---

### Rules Violated
- None.

---

### Verdict
[x] APPROVED  [ ] CHANGES REQUIRED  [ ] BLOCKED

All 3 stories (S001, S002, S003) pass security review at full level.
No blockers. 2 minor style warnings noted — recommend addressing in a follow-up or inline comments.
Feature ready for `/report citation-quality`.
