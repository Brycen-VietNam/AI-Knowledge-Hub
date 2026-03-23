# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-03-23 | Session: #008

---

## Active Sprint
Goal: Auth layer — unblock RBAC, document ingestion, query endpoint
Sprint end: _[date TBD]_

## In Progress (max 3)
- [x] db-schema-embeddings (P0) — FINALIZED ✅ archived COLD
- [ ] auth-api-key-oidc (P0) — TASKS ✅ 16 tasks across 4 stories | next: /analyze S001-T001
- [ ] Story: _none yet_

## Recent Decisions (last 3 — oldest drops off)
- 2026-03-23: D07 — JWT claim mapping configurable: OIDC_EMAIL_CLAIM (default "email"), OIDC_NAME_CLAIM (default "name")
- 2026-03-23: D06 — groups claim empty/absent → user_group_ids=[], login OK (permissive, not 403)
- 2026-03-23: D09 — API key creation = manual seed via SQL this sprint; admin endpoint deferred

## Active Blockers
_None._

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> When starting a new session, run: `/context <active-feature>`
> Then check blockers above before picking up work.
