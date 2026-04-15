# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-15 | Session: #059 (/reviewcode citation-quality — APPROVED)

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
- document-ingestion — DONE ✅ 5 stories, 22 ACs, 61 new tests / 230 pass — approved by lb_mui 2026-04-08
  Archive: `.claude/memory/COLD/document-ingestion.archive.md`
  Report: `docs/document-ingestion/reports/document-ingestion.report.md`
  Unblocks: query-endpoint, multilingual-rag-pipeline
- multilingual-rag-pipeline — DONE ✅ 4 stories (S002–S005), 7 tasks, 24 ACs, 100% coverage (15 pass, 1 skip)
  Archive: `.claude/memory/COLD/multilingual-rag-pipeline.archive.md`
  Report: `docs/multilingual-rag-pipeline/reports/multilingual-rag-pipeline.report.md`
  Unblocks: query-endpoint
- query-endpoint — DONE ✅ 5 stories, 19 tasks, 42/42 tests, 35/35 ACs, 95% coverage — finalized 2026-04-13
  Archive: `.claude/memory/COLD/query-endpoint.archive.md`
  Report: `docs/query-endpoint/reports/query-endpoint.report.md`
  Unblocks: — (sprint chain complete)
- document-parser — DONE ✅ P0+S001–S004, 18/18 unit tests, 24/24 ACs, 5 formats (PDF/DOCX/HTML/TXT/MD) — finalized 2026-04-13
  Archive: `.claude/memory/COLD/document-parser.archive.md`
  Report: `docs/document-parser/reports/document-parser.report.md`
  Unblocks: —
- answer-citation — DONE ✅ S001–S005, 80/80 tests, 35/35 ACs, citation 100%/query 92%/generator 100%/retriever 91% — approved lb_mui 2026-04-15
  Archive: `.claude/memory/COLD/answer-citation.archive.md`
  Report: `docs/answer-citation/reports/answer-citation.report.md`
  Unblocks: citation-quality, confidence-scoring

## In Progress (max 3)
- citation-quality — REPORT PENDING SIGN-OFF (2026-04-15) — /report complete; awaiting Tech Lead + PO + QA approval
  WARM: `.claude/memory/WARM/citation-quality.mem.md`
  Plan: `docs/citation-quality/plan/citation-quality.plan.md`
  Review: `docs/citation-quality/reviews/citation-quality.review.md`
  Report: `docs/citation-quality/reports/citation-quality.report.md`
  Results: 21/21 AC PASS, 389 pass, 0 failures, citation_parser 100% — pending /report --finalize

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-15: citation-quality /report SAVED — 21/21 AC PASS, 389 pass, 0 failures; pending lb_mui sign-off
- 2026-04-15: citation-quality APPROVED by /reviewcode — 0 blockers; 2 minor warnings (id() invariant, __all__ underscore); ready for /report
- 2026-04-15: citation-quality PLAN COMPLETE — checklist 30/30 PASS; G1 S001 rag-agent → G2 S002 api-agent → G3 S003 api-agent; A-CQ-01 resolved

## Pending Commits (uncommitted fixes on feature/document-parser)
- SecurityGate: skip magic check when file_bytes=b"" (pre-read pass) — security_gate.py:47
- SecurityGate: text/markdown ↔ text/plain compatible pair — security_gate.py:18
- docker-compose.yml: RETRIEVAL_TIMEOUT_OVERRIDE=15.0 (CPU Ollama dev machine)

## Active Blockers
- (none)

## Deferred Features (post answer-citation)
- `confidence-scoring` — fix sentinel 0.9 in Ollama+Claude adapters. Ref: answer-citation BACKLOG-2

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> citation-quality REPORT SAVED ✅ — /report complete; 21/21 AC PASS, 389 tests pass.
> Next: collect sign-offs (Tech Lead + PO + QA), then /report citation-quality --finalize
