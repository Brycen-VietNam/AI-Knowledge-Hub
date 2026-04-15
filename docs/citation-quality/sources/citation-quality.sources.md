# Sources Traceability: citation-quality
Created: 2026-04-15 | Feature spec: `docs/citation-quality/spec/citation-quality.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Citation Parser — `_parse_citations()`

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `[1]…[3]` → `{0,2}` | Existing behavior | `answer-citation.archive.md` BACKLOG-1 — `_parse_citations(answer, num_docs) -> set[int]` | Requirement surfaced from commit `80f2c59` S002 analysis; 1-based markers, 0-based output | 2026-04-15 |
| AC2: OOB `[99]` → `{}` | Existing behavior | answer-citation GAP-2 — `test_oob_marker_in_answer` in `tests/rag/test_generator.py` | OOB markers silently ignored; API returns 200 | 2026-04-15 |
| AC3: no markers → `{}` | Business logic | Graceful fallback (D-CIT-08) — monitor `inline_markers_present` post-launch | Models may omit markers; parser must not crash | 2026-04-15 |
| AC4: deduplication | Business logic | Set semantics — `[1][1]` should not double-count | Prevents inflated `cited` counts | 2026-04-15 |
| AC5: empty inputs → `{}` | Business logic | Defensive contract — `num_docs=0` occurs on no-chunk path | Prevents IndexError | 2026-04-15 |
| AC6: whitespace in `[\s*N\s*]` | Business logic | lb_mui design note — LLM output frequently emits `[ 1 ]` with spaces | Regex must tolerate optional whitespace | 2026-04-15 |
| AC7: pure + synchronous | Architecture rule | ARCH A001 — agent scope isolation; no I/O in rag-layer pure functions | Parser must be testable without DB/network | 2026-04-15 |
| AC8: module path | Existing behavior | `backend/rag/` scope convention (rag-agent boundary per ARCH A001) | Consistent with `retriever.py`, `generator.py` | 2026-04-15 |

### Story S002: Extend `CitationObject` + Wire into `query.py`

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `cited: bool = False` | Existing behavior (BACKLOG-1) | `answer-citation.archive.md` BACKLOG-1 — `CitedSource.cited: bool` | Default `False` preserves backward compat for consumers not yet reading the field | 2026-04-15 |
| AC2: call parser in `query.py` | Conversation | BACKLOG-1: "Parser `_parse_citations(answer, num_docs)` after LLM response" | Wire-up point is after `generate_answer()` returns | 2026-04-15 |
| AC3: index alignment | Decision D-CIT-04 | `answer-citation.archive.md` — "marker index 1-based; citations array 0-based (`[N]` → `citations[N-1]`)" | Same conversion as original marker design | 2026-04-14 |
| AC4: all docs in `citations` | Decision D-CIT-03 | "No score filter on citations — mirrors sources exactly. Consumers decide what to display" | Non-content docs get `cited=False` — no asymmetry | 2026-04-14 |
| AC5: no-chunk path | Existing behavior | `query.py:206–213` D09 path — `citations=[]` when `NoRelevantChunksError` | Parser must not be called on empty answer | 2026-04-15 |
| AC6: `inline_markers_present` fast path | Existing behavior | `LLMResponse.inline_markers_present` — added S003-T001; `backend/rag/llm/base.py:16` | Skip parse when model used graceful fallback (no markers in answer) | 2026-04-15 |
| AC7: OpenAPI schema | Existing behavior | Pydantic v2 auto-generates schema — verified via `/docs` | No manual schema update needed | 2026-04-15 |
| AC8: `sources` unchanged | Decision D-CIT-03 | D-CIT-03 — additive only, `sources: list[str]` unmodified | Zero breakage for consumers reading `sources` | 2026-04-14 |
| AC9: score 4dp | Existing behavior (answer-citation S005 AC11) | `query.py:234` — `round(d.score, 4)` | No regression on score precision | 2026-04-15 |

### Story S003: Test Coverage

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: unit tests `test_citation_parser.py` | Spec — S001 ACs | This spec S001 AC1–AC8 | Each AC maps to one pytest function | 2026-04-15 |
| AC2: extend `test_citation.py` | Existing behavior | `tests/api/test_citation.py` — 7 existing tests (S005-T001) | Append-only: no existing assertion changes | 2026-04-15 |
| AC3: cited=True integration | Business logic | Core feature requirement — LLM marker → `cited` flag | Golden path test | 2026-04-15 |
| AC4: all cited=False (no markers) | Existing behavior | `inline_markers_present=False` path — answer-citation S003 graceful fallback | Ensures fast path works | 2026-04-15 |
| AC5: OOB marker no crash | Existing behavior | answer-citation GAP-2 (`test_oob_marker_in_answer`) | Regression from existing test | 2026-04-15 |
| AC6: no-chunk regression | Existing behavior | answer-citation S005 AC9 — `citations==[]` on `no_relevant_chunks` | Must not regress | 2026-04-15 |
| AC7: 80-test baseline | Conversation | answer-citation approval — 80/80 pass; lb_mui 2026-04-15 | Approved test count must not drop | 2026-04-15 |
| AC8: coverage targets | Business logic | Coverage policy from answer-citation S005 (≥90% net) | Consistent quality bar | 2026-04-15 |

---

## Summary

**Total ACs:** 25 (S001: 8 + S002: 9 + S003: 8)
**Fully traced:** 25/25 ✓
**Pending sources:** 0

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |

---
