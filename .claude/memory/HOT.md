# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-06 | Session: #019

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
- cjk-tokenizer — DONE ✅ 4 stories, 22 ACs, **56/0/0 Docker** — approved 2026-04-06
  Archive: `.claude/memory/COLD/cjk-tokenizer.archive.md`
  Report: `docs/cjk-tokenizer/reports/cjk-tokenizer.report.md`
  Unblocks: document-ingestion, multilingual-rag-pipeline

## In Progress (max 3)
- llm-provider — Phase: /reviewcode ✅ APPROVED → /report next | WARM: `.claude/memory/WARM/llm-provider.mem.md`

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-06: llm-provider /reviewcode APPROVED — B001 (sync→async clients), W001–W004 fixed; all security checks pass
- 2026-04-06: llm-provider /analyze — QueryResponse breaking change D10: results[]→answer+sources+low_confidence+reason; request_id retained (D12)
- 2026-04-06: llm-provider /plan DONE — G3 parallel dispatch (S003∥S004); api-agent QueryResponse update post-G3

## Active Blockers
_None._

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> Active feature: `llm-provider`
> Phase: /report — final step
> Review: APPROVED 2026-04-06 (docs/llm-provider/reviews/llm-provider.review.md)
