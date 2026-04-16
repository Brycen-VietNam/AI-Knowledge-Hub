# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-16 | Session: #074 (/sync — frontend-spa S004 DONE)

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
- confidence-scoring — DONE ✅ PR merged 2026-04-16; 34 tests pass; formula cited_ratio*0.8+0.2; fixed sentinel 0.9 Ollama+Claude
  Archive: (no archive yet)
  Unblocks: —
- citation-quality — DONE ✅ PR merged 2026-04-16; 21/21 AC PASS, 389 pass, 0 failures, citation_parser 100%
  WARM: `.claude/memory/WARM/citation-quality.mem.md`
  Report: `docs/citation-quality/reports/citation-quality.report.md`
  Unblocks: —

## In Progress (max 3)
- frontend-spa — S004 IMPLEMENTED ✅ (208/208 pass); S005 is next
  WARM: `.claude/memory/WARM/frontend-spa.mem.md`
  Plan: `docs/frontend-spa/plan/frontend-spa.plan.md`
  S003: DONE ✅ 188/188 pass
  S004: DONE ✅ 208/208 pass — Next: /reviewcode frontend-spa S004 → /tasks S005

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-16: S004 IMPLEMENTED — 208/208 pass (20 new tests); HistoryItem CJK truncation=[...str].slice(0,60); HistoryPanel returns null when empty; authStore.logout calls clearHistory first; addHistory only on successful submitQuery; reset() preserves history (D004)
- 2026-04-16: S004 /tasks DONE — 5 tasks; G1[T001]→G2[T002∥T004]→G3[T003]→G4[T005]; CJK truncation=[...str].slice(0,60); reset() preserves history; logout→clearHistory; addHistory only on successful submitQuery
- 2026-04-16: S003 IMPLEMENTED — 188/188 pass; AnswerPanel isLoading=spinner/error=alert/empty=no-results/answer-no-citations=no-source-warning; LowConfidenceWarning at confidence<0.4; App.test regression fixed (results-area div removed)

## Pending Commits (uncommitted fixes on feature/document-parser)
- SecurityGate: skip magic check when file_bytes=b"" (pre-read pass) — security_gate.py:47
- SecurityGate: text/markdown ↔ text/plain compatible pair — security_gate.py:18
- docker-compose.yml: RETRIEVAL_TIMEOUT_OVERRIDE=15.0 (CPU Ollama dev machine)

## Active Blockers
- (none)

## Deferred Features (post answer-citation)
- (none remaining)

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> frontend-spa S003 IMPLEMENTED (188/188 pass). S004 tasks ready (5 tasks, all TODO).
> Priority 1: /reviewcode frontend-spa S003
> Priority 2: /implement frontend-spa S004 (after S003 review approved)
