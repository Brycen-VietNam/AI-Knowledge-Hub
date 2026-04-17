# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-17 | Session: #085 (admin-spa S001 — /implement complete, 35/35 tests pass)

---

## Current Sprint (Session #086)
Status: **admin-spa S001 DONE** ✅ | 35/35 tests pass | **3 backend BLOCKERs identified pre-S002**
Next: Fix G1+G2+G3 (backend patches) → /analyze T001 (admin-spa S002 — documentsApi.ts)
Branch: `feature/admin-spa`

## Completed Features (All Prior, Archived)
- auth-api-key-oidc, rbac-document-filter, cjk-tokenizer, llm-provider, document-ingestion
- multilingual-rag-pipeline, query-endpoint, document-parser, answer-citation
- confidence-scoring, citation-quality
→ All archived in `.claude/memory/COLD/`

## In Progress (max 3)
- admin-spa — S000 DONE+REVIEWED ✅ | **S001 DONE ✅** | S002–S005 pending (frontend-agent)
  WARM: `.claude/memory/WARM/admin-spa.mem.md`
  Plan: `docs/admin-spa/plan/admin-spa.plan.md`
  Tasks: `docs/admin-spa/tasks/S001.tasks.md` ✅ ALL DONE (T001–T008)
  Next: /analyze T001 (admin-spa S002 — documentsApi.ts)

## Recent Decisions (Session #086)
- 2026-04-17: admin-spa S002 — D11: chuẩn hóa upload response key về `doc_id` (fix upload.py:184, bỏ `document_id`) [gap]
- 2026-04-17: admin-spa S002 — G4 source_url: đã có migration 007 + Document model, chỉ cần expose qua upload.py form + frontend T001/T004 [gap]
- 2026-04-17: admin-spa S001 — 401 interceptor skips `/v1/auth/token` URL to avoid false session-expired on login fail [impl]

## Pending Commits (uncommitted fixes on feature/document-parser)
- SecurityGate: skip magic check when file_bytes=b"" — security_gate.py:47
- SecurityGate: text/markdown ↔ text/plain compatible pair — security_gate.py:18
- docker-compose.yml: RETRIEVAL_TIMEOUT_OVERRIDE=15.0

## Session #080 Summary ✅ COMPLETE
**Task:** Finalize frontend-theme + frontend-spa reports; ghi nhận backend language preference issue

**Completed:**
1. ✅ /report frontend-theme → `docs/frontend-theme/reports/frontend-theme.report.md` (48/48 ACs, 208/208 tests)
2. ✅ /report frontend-spa → `docs/frontend-spa/reports/frontend-spa.report.md` (48/48 ACs, 208/208 tests)
3. ✅ Commit: "Report: frontend-theme + frontend-spa — Feature complete, 100% test coverage"
4. ✅ Updated HOT.md + ghi nhận backend language preference issue

**Key Decision: D008**
- Backend Language Preference: `generate_answer()` does NOT receive `lang` parameter
- Frontend correctly sends `lang` (user's UI language preference)
- Backend detects query language but ignores user preference in LLM generation
- Action: Backend team to add `lang` param to generate_answer(), control LLM output language
- Impact: Post-launch fix (medium UX friction)
- Fully documented in both reports + HOT.md

**Status:**
- Branch: `feature/frontend-spa` (all code committed, reports signed)
- Tests: 208/208 PASS (0 failures)
- Ready: Await PO approval (lb_mui) → merge to main

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

## Pending Commits
- (none — all fixes committed in `6ee36f7 final document parser`)

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
