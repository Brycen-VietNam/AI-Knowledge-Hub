# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-14 | Session: #043 (document-parser live test + SecurityGate fix)

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

## In Progress (max 3)
_(none)_

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-14: SecurityGate MIME fix — added `frozenset({"text/plain","text/markdown"})` to _COMPATIBLE_PAIRS; libmagic detects .md as text/plain, declared text/markdown now accepted; not yet committed
- 2026-04-14: OpenRouter key rotated — old key sk-or-v1-...e610 rejected (401); new key sk-or-v1-0861b...1c880 active; model openai/gpt-oss-120b:free confirmed working; OPENAI_API_KEY in .env updated
- 2026-04-13: S004-fix DONE — FIX-T001 (A003 blocker resolved: langdetect replaces "en" fallback); FIX-T002–T008 (warn fixes: duplicate dep, query_hash sentinel, filename sanitize, title cap, chunked read, md_parser CJK encoding, SecurityGate request_id logging); 18/18 unit tests pass

## Pending Commits (uncommitted fixes on feature/document-parser)
- SecurityGate: skip magic check when file_bytes=b"" (pre-read pass) — security_gate.py:47
- SecurityGate: text/markdown ↔ text/plain compatible pair — security_gate.py:18
- docker-compose.yml: RETRIEVAL_TIMEOUT_OVERRIDE=15.0 (CPU Ollama dev machine)

## Active Blockers
_(none)_

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> All features in sprint chain DONE. No active In Progress items.
> Next: identify next sprint goal or feature backlog item.
