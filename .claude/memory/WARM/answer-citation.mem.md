# Feature Memory: answer-citation
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: PLAN COMPLETE
Updated: 2026-04-14 (session #047)

---

## Summary (5 bullets max — always current)
- Enriches `/v1/query` response with `citations: list[CitationObject]` alongside existing `sources: list[str]` (Option C — additive, no breaking change)
- Requires DB migration 007: `ALTER TABLE documents ADD COLUMN source_url TEXT NULL`
- `_dense_search()` needs INNER JOIN to `documents`; `_bm25_search()` already queries `documents` — both must SELECT `title, lang, source_url`
- LLM prompt changed from raw `{context}` to numbered `[N] title\nchunk` index with explicit `[N]` marker instruction; graceful fallback if model omits markers
- `generate_answer()` and `LLMProvider.complete()` signatures extended with `doc_titles: list[str]`

## Key Decisions
| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D-CIT-01 | Option C (additive) — add `citations` alongside `sources` | Zero client breakage; opt-in for new consumers | 2026-04-14 |
| D-CIT-02 | `source_url` column requires migration 007 — does not exist in schema | NULL nullable — zero downtime migration | 2026-04-14 |
| D-CIT-03 | No score filter on `citations` — mirrors `sources` exactly | Consumers decide what to display; no asymmetry | 2026-04-14 |
| D-CIT-04 | Marker index is 1-based; `citations` array is 0-indexed (`[N]` → `citations[N-1]`) | Natural language convention | 2026-04-14 |
| D-CIT-05 | API layer builds CitationObject from RetrievedDocument, NOT from LLM output | Trust retrieval pipeline data, not model-generated structured data | 2026-04-14 |
| D-CIT-06 | `source_url NULL` acceptable at launch — plain-text title rendered for existing docs | Option A: populate incrementally via PATCH; no retroactive backfill | 2026-04-14 |
| D-CIT-07 | Q2 (consumer strict parsing) N/A — consumers not yet implemented. S004 AC9 mandates permissive JSON parsing in rendering contract | Constraint enforced at contract level, not at API level | 2026-04-14 |
| D-CIT-08 | Graceful fallback sufficient for v1 — no minimum marker rate. Monitor `inline_markers_present` post-launch | Hard gate deferred until 1 sprint of metrics available | 2026-04-14 |

## Spec
Path: `docs/answer-citation/spec/answer-citation.spec.md`
Stories: 5 | Priority: P1
Sources: `docs/answer-citation/sources/answer-citation.sources.md`

## Plan
Path: `docs/answer-citation/plan/answer-citation.plan.md`
Critical path: S001 → S002 → S003 → S005 (S004 ‖ S003)

## Task Progress
| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| — | S001 | pending /tasks | db-agent | G1 — start immediately |
| — | S002 | pending /tasks | api-agent | G2 — after S001 |
| — | S003 | pending /tasks | rag-agent | G3 — after S002 (parallel S004) |
| — | S004 | pending /tasks | api-agent | G3 — after S002 (parallel S003) |
| — | S005 | pending /tasks | api-agent | G4 — after S003 |

## Files Touched
- `docs/answer-citation/reviews/checklist.md` (CREATED — /checklist output)
- `docs/answer-citation/plan/answer-citation.plan.md` (CREATED — /plan output)

## Open Questions
| # | Question | Owner | Due |
|---|----------|-------|-----|
| ~~Q1~~ | ~~A01: Is `source_url NULL` acceptable?~~ | ✅ Resolved — Option A accepted | 2026-04-14 |
| ~~Q2~~ | ~~A04: Consumer lenient JSON parsing?~~ | ✅ Resolved — consumers not yet built; constraint in S004 AC9 | 2026-04-14 |
| ~~Q3~~ | ~~A03: Graceful fallback sufficient?~~ | ✅ Resolved — yes for v1; monitor post-launch | 2026-04-14 |

## CONSTITUTION Violations Found
_None — updated by /checklist or /rules._

---

## Sync: 2026-04-14 (session #046)
Decisions added: none (checklist validation only)
Tasks changed: none (/plan not yet run)
Files touched:
  - docs/answer-citation/reviews/checklist.md (CREATED — 29/30 PASS, 1 WARN)
  - .claude/memory/HOT.md (updated: status → CHECKLIST PASS, Recent Decisions, Next Session Start)
  - .claude/memory/WARM/answer-citation.mem.md (updated: status, files touched)
Questions resolved: none
New blockers: WARN — `documents.lang` nullability not pre-verified. Mitigation: pre-migration `SELECT COUNT(*) FROM documents WHERE lang IS NULL`; add `d.lang or "und"` fallback if any rows found. Pending lb_mui approval before /plan.

## Sync: 2026-04-14 (session #045)
Decisions added: D-CIT-06, D-CIT-07, D-CIT-08
Tasks changed: none (/plan not yet run)
Files touched:
  - docs/answer-citation/clarify/answer-citation.clarify.md (CREATED)
  - docs/answer-citation/spec/answer-citation.spec.md (updated: S004 AC9 added)
  - .claude/memory/WARM/answer-citation.mem.md (updated: decisions, questions resolved, status)
  - .claude/memory/HOT.md (updated: In Progress → CLARIFIED, Recent Decisions, Next Session Start)
  - .claude/memory/feedback_api_additive_consumer_contract.md (CREATED)
Questions resolved: Q1 (source_url NULL ok), Q2 (consumers not built → contract AC), Q3 (graceful fallback ok)
New blockers: none

## Sync: 2026-04-14 (session #044)
Decisions added: D-CIT-01, D-CIT-02, D-CIT-03, D-CIT-04, D-CIT-05
Tasks changed: none (/plan not yet run)
Files touched:
  - docs/answer-citation/spec/answer-citation.spec.md (CREATED)
  - docs/answer-citation/sources/answer-citation.sources.md (CREATED)
  - .claude/memory/WARM/answer-citation.mem.md (CREATED)
  - .claude/memory/HOT.md (updated: In Progress, Recent Decisions, Next Session Start)
Questions resolved: A05 (no score filter — confirmed lb_mui), A06 (title NOT NULL — confirmed ORM)
New blockers: none
