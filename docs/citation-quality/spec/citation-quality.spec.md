# Spec: citation-quality
Created: 2026-04-15 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | answer-citation (extension) |
| Priority | P1 |
| Story count | 3 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 → S003 |
| Parallel-safe stories | none (S002 depends on S001 parser; S003 depends on S002 field) |
| Blocking specs | none |
| Blocked by | answer-citation — DONE ✅ 2026-04-15 |
| Agents needed | rag-agent (S001 parser), api-agent (S002 model + route), api-agent (S003 tests) |

### Problem Statement
Currently `citations` lists ALL retrieved docs regardless of whether the LLM actually referenced them with `[N]` markers. Consumers cannot tell cited docs from mere context, so low-signal citations degrade UX. We need a `cited: bool` flag per `CitationObject` that is `true` only when the LLM emitted a corresponding `[N]` marker in the answer.

### Solution Summary
- Add `_parse_citations(answer: str, num_docs: int) -> set[int]` in a new `backend/rag/citation_parser.py` module — 1-based marker → 0-based index set
- Extend `CitationObject` with `cited: bool` field (default `False` — zero breaking change for existing consumers)
- In `query.py`: after LLM response, call parser on `llm_response.answer`; set `cited=True` for each `CitationObject` whose 0-based index is in the parsed set
- Guard: out-of-range markers (e.g. `[99]` when only 3 docs) are silently ignored — already tested in answer-citation GAP-2
- No change to `sources: list[str]` (D-CIT-03), no change to `citations` ordering, no new DB migration

### Out of Scope
- Confidence scoring fix (sentinel 0.9 in Ollama/Claude) — separate feature `confidence-scoring` (BACKLOG-2)
- Re-ranking cited docs above uncited docs in the response list
- Minimum citation rate enforcement (D-CIT-08 deferred to post-launch metrics)
- Any change to `sources: list[str]` field — additive only (D-CIT-03)
- Frontend rendering logic for the `cited` flag

---

## LAYER 2 — Story Detail

---

### S001: Citation Parser — `_parse_citations()`

**Role / Want / Value**
- As a: rag-agent
- I want: a pure function `_parse_citations(answer: str, num_docs: int) -> set[int]` that extracts 1-based `[N]` markers from the LLM answer and returns a 0-based index set
- So that: the API layer can set `cited=True` on matching `CitationObject` entries without coupling parser logic to the route handler

**Acceptance Criteria**
- [ ] AC1: `_parse_citations("[1] yes and [3] also", 3)` returns `{0, 2}`
- [ ] AC2: `_parse_citations("[99] out of range", 3)` returns `{}` (OOB ignored)
- [ ] AC3: `_parse_citations("no markers here", 5)` returns `{}`
- [ ] AC4: `_parse_citations("[1][1][2]", 3)` returns `{0, 1}` (deduplication — set)
- [ ] AC5: `_parse_citations("", 0)` returns `{}` (empty answer/empty docs — no crash)
- [ ] AC6: marker regex must handle `[N]` with optional whitespace `[ N ]` — strip and parse
- [ ] AC7: function is pure (no I/O, no side effects) and synchronous
- [ ] AC8: module lives at `backend/rag/citation_parser.py`; function exported at `backend/rag/__init__.py` or imported directly

**Non-functional**
- Latency: parser is O(len(answer)) — negligible; no async needed
- Audit log: not required
- CJK support: regex operates on Unicode text — CJK answer bodies do not affect `[N]` ASCII markers

**Implementation notes**
- Use `re.findall(r'\[\s*(\d+)\s*\]', answer)` to extract all marker strings
- Convert each to int, subtract 1 for 0-based, discard if `< 0` or `>= num_docs`
- Return `set[int]`
- No dependency on any other backend module — pure stdlib

---

### S002: Extend `CitationObject` + Wire into `query.py`

**Role / Want / Value**
- As an: API consumer (Web SPA, Teams bot, Slack bot)
- I want: each `CitationObject` in the `/v1/query` response to include a `cited: bool` field
- So that: I can distinguish documents the LLM actually cited (`cited=True`) from documents retrieved but not referenced (`cited=False`), and render them differently

**Acceptance Criteria**
- [ ] AC1: `CitationObject` gains `cited: bool = False` — Pydantic field with explicit default (zero breaking change for existing consumers that omit the field)
- [ ] AC2: `query.py` calls `_parse_citations(llm_response.answer, len(content_docs))` after the LLM call succeeds
- [ ] AC3: `CitationObject` for index `i` (0-based, same order as `content_docs`) has `cited=True` iff `i in cited_set`
- [ ] AC4: `citations` built from all `docs` (not only `content_docs`) — `cited=False` for docs with no content (no regression on D-CIT-03)
- [ ] AC5: when `answer is None` (no-chunk path, D09), `citations=[]` and parser is NOT called
- [ ] AC6: when `llm_response.inline_markers_present is False`, all `cited` flags remain `False` — no parse attempted (fast path, avoids useless regex on fallback answers)
- [ ] AC7: `cited` field appears in OpenAPI schema (automatic via Pydantic — verify with `/docs`)
- [ ] AC8: no change to `sources: list[str]` — doc_id list unchanged (D-CIT-03)
- [ ] AC9: `score` precision retained at 4dp (existing AC11 from answer-citation — no regression)

**API Contract**
```
POST /v1/query
Headers: Authorization: Bearer <token> | X-API-Key: <key>
Body: {"query": "...", "top_k": 10}
Response 200:
{
  "request_id": "uuid",
  "answer": "The answer [1] references doc one.",
  "sources": ["uuid1", "uuid2", "uuid3"],
  "low_confidence": false,
  "citations": [
    {"doc_id": "uuid1", "title": "Doc One", "source_url": null,
     "chunk_index": 0, "score": 0.9512, "lang": "en", "cited": true},
    {"doc_id": "uuid2", "title": "Doc Two", "source_url": null,
     "chunk_index": 1, "score": 0.8341, "lang": "ja", "cited": false},
    {"doc_id": "uuid3", "title": "Doc Three", "source_url": null,
     "chunk_index": 0, "score": 0.7120, "lang": "vi", "cited": false}
  ]
}
```

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)  [x] Both

**Non-functional**
- Latency: parser adds < 1ms — within 1.8s SLA (R007 / P001)
- Audit log: not required (audit already triggered per retrieval — R006)
- CJK support: ja / zh / vi / ko — answer text may be CJK but markers are ASCII `[N]`

**Implementation notes**
- Edit `backend/api/models/citation.py`: add `cited: bool = False`
- Edit `backend/api/routes/query.py`:
  - Import `_parse_citations` from `backend.rag.citation_parser`
  - After successful LLM call: `cited_set = _parse_citations(llm_response.answer, len(content_docs)) if llm_response.inline_markers_present else set()`
  - When building `citations` list: track index `i` relative to `content_docs` list; non-content docs always `cited=False`

> **Assumption**: `citations` list is built over `docs` (all retrieved), but `cited` indexing maps to `content_docs` (subset with content). Docs in `docs` but not `content_docs` always get `cited=False`.
> Confirm or /clarify before /plan.

---

### S003: Test Coverage — `_parse_citations` Unit + Integration

**Role / Want / Value**
- As a: QA / api-agent
- I want: full unit tests for `citation_parser.py` and integration tests for `cited` flag in `/v1/query` response
- So that: the feature ships at ≥ 90% coverage on new code and no regressions on existing answer-citation tests

**Acceptance Criteria**
- [ ] AC1: `tests/rag/test_citation_parser.py` — covers AC1–AC8 from S001 (8 unit test cases minimum)
- [ ] AC2: `tests/api/test_citation.py` — extended with `cited=True` / `cited=False` assertions on existing mock responses
- [ ] AC3: integration test: answer with `[1]` marker → `citations[0].cited == True`, `citations[1].cited == False`
- [ ] AC4: integration test: answer with no markers (`inline_markers_present=False`) → all `cited == False`
- [ ] AC5: integration test: OOB marker `[99]` in 3-doc answer → all `cited == False` (no crash, 200 OK)
- [ ] AC6: integration test: `no_relevant_chunks` path → `citations == []` (no regression)
- [ ] AC7: regression — all existing 80 answer-citation tests still pass (0 failures)
- [ ] AC8: coverage target: `citation_parser.py` ≥ 95%, `citation.py` ≥ 95%, net `query.py` coverage ≥ 90%

**Non-functional**
- No DB integration tests required (parser is pure; CitationObject is in-memory)
- CJK: add one CJK-answer test case (e.g. Japanese answer containing `[1]` marker) to confirm regex works across Unicode text

**Implementation notes**
- Mock `generate_answer` in integration tests to control `llm_response.answer` and `inline_markers_present`
- Reuse existing `mock_content_docs` fixtures from `tests/api/test_citation.py`
- Do NOT change existing test assertions — append new test functions only

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC5 | Existing behavior — BACKLOG-1 in answer-citation archive | `.claude/memory/COLD/answer-citation.archive.md` BACKLOG-1 | 2026-04-15 |
| AC6 | Business logic | lb_mui design note — optional whitespace in `[N]` markers common in LLM output | 2026-04-15 |
| AC7 | Architecture rule | ARCH A001 — pure function, no cross-boundary I/O | 2026-04-15 |
| AC8 | Existing behavior | Directory convention — `backend/rag/` scope for RAG logic | 2026-04-15 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | BACKLOG-1 | `CitedSource.cited: bool` — commit `80f2c59` S002 analysis in answer-citation archive | 2026-04-15 |
| AC2 | Conversation | answer-citation BACKLOG-1: "Parser `_parse_citations(answer, num_docs)` after LLM response" | 2026-04-15 |
| AC3 | Business logic | Marker index 1-based (D-CIT-04); `citations` array 0-based (`[N]` → `citations[N-1]`) | 2026-04-14 |
| AC4 | Decision D-CIT-03 | `citations` mirrors `sources` exactly (no asymmetry) — confirmed lb_mui | 2026-04-14 |
| AC5 | Existing behavior | D09 no-chunk path — `query.py:206–213` | 2026-04-15 |
| AC6 | Existing behavior | `llm_response.inline_markers_present` flag added in answer-citation S003-T001 | 2026-04-15 |
| AC7 | Existing behavior | Pydantic v2 auto-generates OpenAPI schema | 2026-04-15 |
| AC8 | Decision D-CIT-03 | `sources: list[str]` not modified — doc_id list unchanged | 2026-04-14 |
| AC9 | Existing AC (answer-citation S005 AC11) | `score` rounded to 4dp — no regression | 2026-04-15 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC5 | Spec — S001/S002 ACs | This spec, S001 + S002 | 2026-04-15 |
| AC6 | Existing behavior | answer-citation S005 AC9 — `no_relevant_chunks` path regression | 2026-04-15 |
| AC7 | Decision | answer-citation 80-test baseline — must remain 0 failures | 2026-04-15 |
| AC8 | Business logic | Coverage policy established in answer-citation S005 | 2026-04-15 |

---
