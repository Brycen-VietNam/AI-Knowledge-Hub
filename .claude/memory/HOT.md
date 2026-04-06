# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-06 | Session: #012

---

## Active Sprint
Goal: Auth layer — unblock RBAC, document ingestion, query endpoint
Sprint end: _[date TBD]_

## Completed Features
- auth-api-key-oidc — DONE ✅ 4 stories, 16 tasks, 51 tests, 20/20 ACs
  Archive: `.claude/memory/COLD/auth-api-key-oidc.archive.md`
  Report: `docs/reports/auth-api-key-oidc.report.md`
  Unblocks: rbac-document-filter, document-ingestion, query-endpoint
- rbac-document-filter — DONE ✅ 5 stories, 41 ACs, all PASS — approved by lb_mui 2026-04-06
  Archive: `.claude/memory/COLD/rbac-document-filter.archive.md`
  Report: `docs/rbac-document-filter/reports/rbac-document-filter.report.md`
  Unblocks: document-ingestion, multilingual-rag-pipeline, query-endpoint

## In Progress (max 3)
_None. Next candidates: document-ingestion, multilingual-rag-pipeline, query-endpoint_

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-06: rbac-document-filter finalized — approved lb_mui, archived WARM→COLD
- 2026-04-03: rbac-document-filter plan complete — G1(S001)→G2(S002)→G3(S003∥S004)→G4(S005)
- 2026-03-24: auth-api-key-oidc finalized — all sign-offs collected
- 2026-03-23: D10 — ApiKey has no is_active; verify_api_key joins User.is_active

## Active Blockers
_None._

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> When starting a new session, run: `/context <active-feature>`
> Then check blockers above before picking up work.
> Next candidates: rbac-document-filter, document-ingestion, query-endpoint
