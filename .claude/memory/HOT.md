# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-14 | Session: #047 (/plan answer-citation — PLAN COMPLETE)

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
- answer-citation — P1 | PLAN COMPLETE | 5 stories, 41 ACs | Critical path: S001→S002→S003→S005 | next: /tasks S001
  WARM: `.claude/memory/WARM/answer-citation.mem.md`
  Spec: `docs/answer-citation/spec/answer-citation.spec.md`
  Plan: `docs/answer-citation/plan/answer-citation.plan.md`
  Checklist: `docs/answer-citation/reviews/checklist.md`

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-14: answer-citation /plan COMPLETE — 4 parallel groups (G1:S001, G2:S002, G3:S003‖S004, G4:S005); WARN lang-nullability mitigated in S001 task scope; plan saved to `docs/answer-citation/plan/answer-citation.plan.md`
- 2026-04-14: answer-citation /clarify — all 3 blockers resolved: Q1 Option A (NULL ok), Q2 N/A (consumers not built → S004 AC9 mandates permissive JSON parsing), Q3 graceful fallback sufficient; S004 AC9 added; status → CLARIFIED
- 2026-04-14: answer-citation /specify — Option C (additive `citations` field, no breaking change); `citations` mirrors `sources` exactly (no score filter); migration 007 adds `source_url TEXT NULL`; 5 stories, 40 ACs
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
> Active feature: answer-citation (PLAN COMPLETE).
> Next: `/tasks S001 answer-citation` — db-agent, G1 (start immediately). No blockers.
