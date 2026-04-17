# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-17 | Session: #079 (/sync — frontend-theme S001–S005 ALL DONE)

---

## Active Sprint
Goal: Frontend theme + SPA finalization → /report both features → merge to main
Sprint end: _[date TBD]_

## Completed Features
- auth-api-key-oidc — DONE ✅ 4 stories, 16 tasks, 51 tests, 20/20 ACs
  Archive: `.claude/memory/COLD/auth-api-key-oidc.archive.md`
- rbac-document-filter — DONE ✅ 5 stories, 41 ACs — approved lb_mui 2026-04-06
  Archive: `.claude/memory/COLD/rbac-document-filter.archive.md`
- cjk-tokenizer — DONE ✅ 4 stories, 22 ACs, 56/0/0 Docker — approved 2026-04-06
  Archive: `.claude/memory/COLD/cjk-tokenizer.archive.md`
- llm-provider — DONE ✅ 5 stories, 22 ACs, 36/38 pass — finalized 2026-04-06
  Archive: `.claude/memory/COLD/llm-provider.archive.md`
- document-ingestion — DONE ✅ 5 stories, 22 ACs, 230 pass — approved lb_mui 2026-04-08
  Archive: `.claude/memory/COLD/document-ingestion.archive.md`
- multilingual-rag-pipeline — DONE ✅ 4 stories, 24 ACs, 100% coverage
  Archive: `.claude/memory/COLD/multilingual-rag-pipeline.archive.md`
- query-endpoint — DONE ✅ 5 stories, 42/42 tests, 35/35 ACs, 95% cov — finalized 2026-04-13
  Archive: `.claude/memory/COLD/query-endpoint.archive.md`
- document-parser — DONE ✅ P0+S001–S004, 18/18 tests, 24/24 ACs — finalized 2026-04-13
  Archive: `.claude/memory/COLD/document-parser.archive.md`
- answer-citation — DONE ✅ S001–S005, 80/80 tests, 35/35 ACs — approved lb_mui 2026-04-15
  Archive: `.claude/memory/COLD/answer-citation.archive.md`
- confidence-scoring — DONE ✅ PR merged 2026-04-16; 34 tests; cited_ratio*0.8+0.2
- citation-quality — DONE ✅ PR merged 2026-04-16; 21/21 ACs, 389 pass
  Report: `docs/citation-quality/reports/citation-quality.report.md`

## In Progress (max 3)
- (none — ready for merge to main)

## Recent Decisions (last 3)
- 2026-04-17: D007 — Global CSS classes in index.css (no modules, no inline style) [User]
- 2026-04-17: D006 — Logo: "Knowledge Hub" + "BRYSEN GROUP" [User]
- 2026-04-17: D005 — Header on all pages; user pill hidden when token === null [User]

## Pending Commits (uncommitted fixes on feature/document-parser)
- SecurityGate: skip magic check when file_bytes=b"" — security_gate.py:47
- SecurityGate: text/markdown ↔ text/plain compatible pair — security_gate.py:18
- docker-compose.yml: RETRIEVAL_TIMEOUT_OVERRIDE=15.0

## Completed Features (Session #080 — /report frontend-theme + frontend-spa)
- **frontend-theme** — ALL DONE ✅ S001–S005 (5 stories, 48 ACs, 208/208 tests, build 1.95s clean)
  Report: `docs/frontend-theme/reports/frontend-theme.report.md` (READY for merge)
  Archive: → COLD/frontend-theme.archive.md after merge to main
- **frontend-spa** — ALL DONE ✅ S001–S005 (5 stories, 48 ACs, 208/208 tests)
  Report: `docs/frontend-spa/reports/frontend-spa.report.md` (READY for merge)
  Archive: → COLD/frontend-spa.archive.md after merge to main

## Known Deferred Issues
- **Backend Language Preference** (P1, backend team):
  - Issue: `generate_answer()` does not receive `lang` parameter from `/v1/query`
  - Effect: Query "what is knowledge hub?" + UI language="Tiếng Việt" → English answer (uses detected query lang, not UI pref)
  - Root: Backend language detection for retrieval is correct, but LLM generation ignores user's language preference
  - Action: Add `lang` parameter to `generate_answer()`, control LLM output language via prompt
  - Ticket: (separate backend issue to be created)
  - Impact: Medium UX friction (users in non-native language get results in wrong language) — post-launch fix

## Active Blockers
- (none)

## Session #079 — What was done
**frontend-theme S002–S005 implemented (this session):**

| Story | Files modified | Result |
|-------|---------------|--------|
| S002 | index.css (header+grid CSS), App.tsx, QueryPage.tsx, QueryPage.test.tsx | 208 ✅ |
| S003 | index.css (search CSS), SearchInput.tsx, LanguageSelector.tsx | 208 ✅ |
| S004 | index.css (results CSS), AnswerPanel.tsx, ConfidenceBadge.tsx+test, LowConfidenceWarning.tsx, CitationList.tsx, CitationItem.tsx | 208 ✅ |
| S005 | index.css (login+history CSS), LoginPage.tsx, LoginForm.tsx, HistoryPanel.tsx, HistoryItem.tsx | 208 ✅ |

**Tasks files created:** S002.tasks.md, S003.tasks.md, S004.tasks.md, S005.tasks.md

**Key changes summary:**
- `frontend/src/index.css`: grew from ~80 lines (tokens only) to ~490 lines (full design system)
- All Tailwind classes removed from 9 components (AnswerPanel, ConfidenceBadge, LowConfidenceWarning, CitationList, CitationItem, LoginPage, LoginForm, HistoryPanel, HistoryItem)
- LanguageSelector moved from QueryPage → App.tsx header
- CSS bundle: 2.52 KB → 11.58 KB (gzip 2.89 KB)

## Next Session Start
> Priority 1: /report frontend-theme → commit + merge feature/frontend-theme → main
> Priority 2: /report frontend-spa → commit + merge feature/frontend-spa → main
> Both features fully implemented and tested (208/208 green)

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
- frontend-theme — S001–S005 ALL DONE ✅ (5 stories, 48 ACs, 208/208 tests, build 1.95s clean)
  WARM: `.claude/memory/WARM/frontend-theme.mem.md`
  Next: /report frontend-theme → commit + merge to main
- frontend-spa — S005 READY for /report (all stories DONE + REVIEWED)
  WARM: `.claude/memory/WARM/frontend-spa.mem.md`
  S003: DONE ✅ 188/188 pass — REVIEWED 2026-04-16
  S004: DONE ✅ 208/208 pass — REVIEWED 2026-04-17
  Next: /report frontend-spa → commit + merge to main

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-17: D007 — Global CSS classes in index.css (no modules, no inline style) — supports pseudo-states, single file [User]
- 2026-04-17: D006 — Logo: "Knowledge Hub" + "BRYSEN GROUP" — confirmed from reference [User]
- 2026-04-17: D005 — Header on all pages; user pill hidden on LoginPage (token === null); username only, no role [User]

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
> frontend-theme PLANNED (D005–D007 locked, checklist + plan complete).
> Priority 1: /tasks frontend-theme S001 (token creation task definition)
> Priority 2: Implement stories S001–S005 sequentially (all in one feature branch session)
> Or: /report frontend-spa → finalize + commit + merge feature/frontend-spa to main
