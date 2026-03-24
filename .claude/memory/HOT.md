# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-03-24 | Session: #011

---

## Active Sprint
Goal: Auth layer — unblock RBAC, document ingestion, query endpoint
Sprint end: _[date TBD]_

## Completed Features
- auth-api-key-oidc — DONE ✅ 4 stories, 16 tasks, 51 tests, 20/20 ACs
  Archive: `.claude/memory/COLD/auth-api-key-oidc.archive.md`
  Report: `docs/reports/auth-api-key-oidc.report.md`
  Unblocks: rbac-document-filter, document-ingestion, query-endpoint

## In Progress (max 3)
_None — pick up next feature._

## Recent Decisions (last 3 — oldest drops off)
- 2026-03-24: auth-api-key-oidc finalized — all sign-offs collected
- 2026-03-23: D12 — AuthenticatedUser canonical home = backend/auth/types.py
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
