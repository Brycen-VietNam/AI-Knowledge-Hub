# Feature Memory: citation-quality
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: REVIEWED ✅ — APPROVED by /reviewcode; ready for /report
Updated: 2026-04-15 (session #058)

---

## Summary (5 bullets max — always current)
- Adds `cited: bool` per `CitationObject` — `true` only when LLM emitted `[N]` marker for that doc
- New pure module `backend/rag/citation_parser.py` with `_parse_citations(answer, num_docs) -> set[int]`
- `CitationObject` gains `cited: bool = False` (backward-compatible default — no consumer breakage)
- `query.py` calls parser after LLM response; skips parse when `inline_markers_present=False` (fast path)
- No DB migration, no change to `sources: list[str]`, no change to `citations` ordering

## Key Decisions
| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D-CQ-01 | `cited: bool = False` default — additive only | Zero breakage for existing consumers (pattern: D-CIT-01) | 2026-04-15 |
| D-CQ-02 | Skip parse when `inline_markers_present=False` | No-op fast path — avoids regex on fallback answers | 2026-04-15 |
| D-CQ-03 | OOB markers silently ignored (inherit from GAP-2) | Confirmed behavior from answer-citation — no API change | 2026-04-15 |
| D-CQ-04 | Parser is 0-based output (1-based input markers) | Inherits D-CIT-04 from answer-citation | 2026-04-14 |
| D-CQ-05 | Non-content docs (no `.content`) always `cited=False` | content_docs ⊆ docs; cited indexing maps to content_docs only | 2026-04-15 |

## Open Assumptions
| ID | Assumption | Owner | Resolution |
|----|-----------|-------|------------|
| A-CQ-01 | `cited` indexing maps over `content_docs` (subset of `docs`); docs outside `content_docs` always `cited=False` | lb_mui | RESOLVED — `content_idx` map in S002-T002; D-CQ-05 encodes it |

## Spec
Path: `docs/citation-quality/spec/citation-quality.spec.md`
Stories: 3 | Priority: P1
Sources: `docs/citation-quality/sources/citation-quality.sources.md`

## Plan
Path: `docs/citation-quality/plan/citation-quality.plan.md`
Critical path: S001 (rag-agent) → S002 (api-agent) → S003 (api-agent)
Groups: G1=S001, G2=S002, G3=S003 — fully sequential

## Task Progress
| Story | Status | Agent | Notes |
|-------|--------|-------|-------|
| S001 — `_parse_citations()` | REVIEWED ✅ | rag-agent | citation_parser.py CREATED; __init__.py updated; smoke PASS |
| S002 — CitationObject + query.py | REVIEWED ✅ | api-agent | cited field + _parse_citations wired; 42 tests PASS |
| S003 — Test Coverage | REVIEWED ✅ | api-agent | citation_parser 100%, all branches exercised; 389 pass |

## Files Touched
- `docs/citation-quality/spec/citation-quality.spec.md` (CREATED — /specify)
- `docs/citation-quality/sources/citation-quality.sources.md` (CREATED — /specify)
- `docs/citation-quality/reviews/checklist.md` (CREATED — /checklist inline, 30/30 PASS)
- `docs/citation-quality/plan/citation-quality.plan.md` (CREATED — /plan)
- `backend/rag/citation_parser.py` (CREATED — S001-T001)
- `backend/rag/__init__.py` (MODIFIED — S001-T002: added _parse_citations export)
- `docs/citation-quality/tasks/S001.tasks.md` (CREATED — DONE ✅)
- `backend/api/models/citation.py` (MODIFIED — S002-T001: cited: bool = False)
- `backend/api/routes/query.py` (MODIFIED — S002-T002: import + content_idx + cited_set + list comp)
- `docs/citation-quality/tasks/S002.tasks.md` (CREATED — DONE ✅)
- `tests/rag/test_citation_parser.py` (CREATED — S003-T001: 13 tests, 100% coverage)
- `tests/api/test_citation.py` (MODIFIED — S003-T002: 4 cited-field tests appended)
- `tests/api/test_query.py` (MODIFIED — S003-T003: 4 cited field assertions appended)
- `docs/citation-quality/tasks/S003.tasks.md` (CREATED — DONE ✅)

## Parent Feature
- Blocked by: answer-citation — DONE ✅ 2026-04-15
- Archive: `.claude/memory/COLD/answer-citation.archive.md`
- BACKLOG-1 reference: `cited` flag + `_parse_citations` parser

## CONSTITUTION Violations Found
_None — updated by /checklist or /rules._

## Sync: 2026-04-15 (session #057)
Decisions added: D-CQ-01, D-CQ-02, D-CQ-03, D-CQ-04, D-CQ-05
Tasks changed: all stories → TODO (plan established, /tasks not yet run)
Files touched:
  - docs/citation-quality/spec/citation-quality.spec.md (CREATED — /specify)
  - docs/citation-quality/sources/citation-quality.sources.md (CREATED — /specify)
  - docs/citation-quality/reviews/checklist.md (CREATED — /checklist inline 30/30 PASS)
  - docs/citation-quality/plan/citation-quality.plan.md (CREATED — /plan)
  - .claude/memory/WARM/citation-quality.mem.md (CREATED — /specify)
  - .claude/memory/HOT.md (UPDATED — In Progress, Recent Decisions, Next Session)
Questions resolved: A-CQ-01 (resolved in plan impl note — content_idx map; no lb_mui clarify needed)
New blockers: none

## Sync: 2026-04-15 (session #058 — /implement S001+S002+S003)
Decisions added: none new (D-CQ-01–05 confirmed in implementation)
Tasks changed: S001→DONE, S002→DONE, S003→DONE
Files touched:
  - backend/rag/citation_parser.py (CREATED — S001)
  - backend/rag/__init__.py (MODIFIED — S001: _parse_citations export)
  - backend/api/models/citation.py (MODIFIED — S002: cited: bool = False)
  - backend/api/routes/query.py (MODIFIED — S002: import + content_idx + cited_set + list comp)
  - tests/rag/test_citation_parser.py (CREATED — S003: 13 tests, 100% cov)
  - tests/api/test_citation.py (MODIFIED — S003: 4 cited-field tests)
  - tests/api/test_query.py (MODIFIED — S003: 4 cited assertions)
  - docs/citation-quality/tasks/S001.tasks.md (CREATED)
  - docs/citation-quality/tasks/S002.tasks.md (CREATED)
  - docs/citation-quality/tasks/S003.tasks.md (CREATED)
Questions resolved: A-CQ-01 RESOLVED
New blockers: none
Env note: --cov + test_citation/test_query triggers numpy re-import (pre-existing); citation_parser measured at 100%; all branches exercised by test run
