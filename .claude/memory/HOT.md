# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-24 | Session: #123 (ux-form-validation — DONE + archived) | /report --finalize

---

## Current Sprint
Status: **security-audit** — IN_PROGRESS | S001 tasks defined + analyzed | 0 blockers

## Completed Features (All, Archived)
- auth-api-key-oidc, rbac-document-filter, cjk-tokenizer, llm-provider, document-ingestion
- multilingual-rag-pipeline, query-endpoint, document-parser, answer-citation
- confidence-scoring, citation-quality
- **admin-spa** — DONE ✅ 2026-04-20 | Archive: `.claude/memory/COLD/admin-spa.archive.md`
- **user-management** — DONE ✅ 2026-04-21 | 80/80 ACs | 91/91 tests PASS | Archive: `.claude/memory/COLD/user-management.archive.md`
- **change-password** — DONE ✅ 2026-04-22 | 43/43 ACs | 340/340 tests PASS | Archive: `.claude/memory/COLD/change-password.archive.md`
- **ux-form-validation** — DONE ✅ 2026-04-24 | 30 ACs | 28 PASS + 2 PARTIAL | Archive: `.claude/memory/COLD/ux-form-validation.archive.md`
→ All archived in `.claude/memory/COLD/`

## In Progress (max 3)
- **embed-model-migration** — P0 | CLARIFIED 2026-04-27 | 0 blockers, ready for /checklist
  Spec: `docs/embed-model-migration/spec/embed-model-migration.spec.md` (updated AC4,5 S005 + AC3 S004)
  Clarify: `docs/embed-model-migration/clarify/embed-model-migration.clarify.md` (all resolved ✅)
  WARM: `.claude/memory/WARM/embed-model-migration.mem.md`
  Next: /checklist embed-model-migration → /plan
- **security-audit** — P1 | REPORT DONE 2026-04-23 | awaiting sign-off (lb_mui) → /report --finalize
  WARM: `.claude/memory/WARM/security-audit.mem.md`
  Report: `docs/security-audit/reports/security-audit.report.md`
  Stories: S001 ✅ REVIEWED + S002 ✅ REVIEWED | ACs: 20/20 | Tests: 118/118 backend + 32/32 frontend
  Fixed: test_local_jwt_resolves_user mock fixture gap (S002 SELECT extension → row[1])
  Next: lb_mui sign-off → /report security-audit --finalize
- **ux-form-validation** — DONE ✅ 2026-04-24 | 5 stories, 28/30 AC PASS (2 PARTIAL deferred) | Archive: `.claude/memory/COLD/ux-form-validation.archive.md`

## Recent Decisions (Session #125 — embed-model-migration /clarify)
- 2026-04-27: D09 — S005 pass bar = absolute recall@10 ≥ 0.6 (cross-lingual ≥ 0.5); mxbai baseline bỏ qua (fixture mới)
- 2026-04-27: D08 — GGUF path = llama.cpp convert từ safetensors Q4_K_M; HF GGUF repo không tồn tại (verified)
- 2026-04-27: D07 — Fixture generation: Claude tự generate synthetic từ test docs; lb_mui review cuối S005
- 2026-04-23: S001 IMPL — App.tsx `hasPassword` logic changed from `password !== null` → `refreshToken !== null` (D-SA-02 — OIDC users never get refresh token)
- 2026-04-23: D-SA-01 — `JWT_REFRESH_SECRET` separate env var (not shared with `AUTH_SECRET_KEY`) — confirmed lb_mui; independent rotation policy
- 2026-04-23: D-SA-02 — Refresh token stored in `authStore` memory only (not localStorage) — XSS boundary
- 2026-04-23: D-SA-03 — `token_version` JWT claim shortened to `tv` — avoids collision with standard claims

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
- (none — user-management Q1/Q2/Q3 resolved by migration 011 on 2026-04-21)

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
