# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-07 | Session: #026

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
- llm-provider — DONE ✅ 5 stories, 22 ACs, 36/38 pass (94% cov) — finalized 2026-04-06
  Archive: `.claude/memory/COLD/llm-provider.archive.md`
  Report: `docs/llm-provider/reports/llm-provider.report.md`
  Unblocks: query-endpoint (answer generation), multilingual-rag-pipeline

## In Progress (max 3)
- document-ingestion — warnings fixed 2026-04-07 (W1+W2+W3 resolved) → next: /report

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-07: D12 — /reviewcode APPROVED after fixes: W1 removed double verify_token (all 4 routes), W2 added httpx timeout=10.0, W3 removed hardcoded "en" fallback (LanguageDetectionError now propagates, A003 compliant)
- 2026-04-07: D11 — raw content NOT stored in documents table (DB bloat); chunk text in embeddings.text TEXT NOT NULL; migration 006 covers both documents.status + embeddings.text
- 2026-04-07: document-ingestion /implement DONE — 61 new tests, 230 pass, 9 pre-existing fails

## Active Blockers
_None._

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> Active: document-ingestion — all warnings fixed, ready for /report
> WARM: `.claude/memory/WARM/document-ingestion.mem.md`
> Review: `docs/document-ingestion/reviews/document-ingestion.review.md`
