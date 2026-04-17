# WARM Memory: frontend-spa
Created: 2026-04-16 | Status: PLAN DONE — ready for /tasks

---

## Spec Summary
Public-facing React/Vite SPA — thin client cho end-users query tài liệu nội bộ.
6 stories, 45 ACs. Separate từ admin-spa (upload/management = internal only).
S000 = backend prerequisite (api-agent); S001–S005 = frontend (frontend-agent).

## Key Decisions
- D001: 2 app riêng (public-spa vs admin-spa) — security boundary + independent deploy
- D002: JWT in-memory only (không localStorage) — OWASP XSS prevention
- D003: UI language: user tự chọn 4 languages (ja/en/vi/ko), persist localStorage
- D004: Query history: session-only, in-memory, không persist
- D005: Auth: username/password JWT (SSO deferred)
- D006: conflict detection UI: skip hoàn toàn (feature deferred)
- D007: Build: Vite static + multi-stage Docker (node:alpine → nginx:alpine)
- D008: S000 prerequisite — POST /v1/auth/token chưa có → api-agent implement trước frontend; bcrypt + HS256 JWT; dual-mode verify_token (HS256 local + RS256/ES256 OIDC)
- D009: Migration số = 008_add_password_hash.sql (users table có sẵn từ 004, thiếu password_hash column)
- D010: AUTH_SECRET_KEY chưa có → generate + add vào .env & .env.example là một task trong S000
- D011: Token refresh = proactive (SPA tự refresh ~5 min trước exp, không đợi 401)
- D012: Citation score display = "91%" (percentage format, thân thiện UX)
- D013: Docker port frontend-spa = 8080:80 (tránh conflict với app:8000, dev server:3000, và port 80 cần root)

## Tech Choices
- State: Zustand (in-memory store)
- i18n: react-i18next
- HTTP: Axios với interceptor cho Bearer token + 401 handler
- Markdown: react-markdown
- Router: React Router v6
- Build: Vite + nginx:alpine Docker

## Stories
| ID | Title | Agent | Status |
|----|-------|-------|--------|
| S000 | Backend — Username/Password Auth Endpoint | api-agent | DONE ✅ |
| S001 | Authentication — Login/Logout | frontend-agent | SPEC |
| S002 | Query Page — Search Input & Language Selector | frontend-agent | SPEC |
| S003 | Query Results — Answer + Citations Display | frontend-agent | SPEC |
| S004 | Query History — Session-level | frontend-agent | DONE ✅ |
| S005 | Build & Docker Packaging | frontend-agent | SPEC |

## S000 Task Board — DONE ✅ (2026-04-16)
| Task | Title | Status |
|------|-------|--------|
| T001 | Migration 008 — add password_hash to users | DONE ✅ |
| T002 | POST /v1/auth/token route + bcrypt verify | DONE ✅ |
| T003 | Generate AUTH_SECRET_KEY + update .env.example | DONE ✅ |
| T004 | Dual-mode verify_token (HS256 + OIDC) | DONE ✅ |
| T005 | Register auth router in app.py + smoke test | DONE ✅ |
Tests: 12/12 pass | File: `docs/frontend-spa/tasks/S000.tasks.md`

### S000 Implementation Notes
- bcrypt: dùng trực tiếp `import bcrypt` (không qua passlib — incompatible với bcrypt 5.x)
- Timing attack prevention: dummy hash path chạy `bcrypt.checkpw()` ngay cả khi user không tồn tại
- Rate limit: 10 req/min per IP (client IP, vì user chưa authen tại thời điểm login)
- `_verify_local_jwt()` trong dependencies.py: return `None` on failure (không raise) → fall through to OIDC
- `AUTH_SECRET_KEY`: RuntimeError guard trong auth.py; soft check (None = skip) trong dependencies.py
- `auth_type="oidc"` cho local JWT users (Literal chưa mở rộng — out of S000 scope)

## Files Touched
- `docs/frontend-spa/spec/frontend-spa.spec.md` (created)
- `docs/frontend-spa/sources/frontend-spa.sources.md` (created)
- `docs/frontend-spa/clarify/frontend-spa.clarify.md` (created)
- `docs/frontend-spa/reviews/checklist.md` (created — PASS)
- `docs/frontend-spa/plan/frontend-spa.plan.md` (created)
- `docs/frontend-spa/tasks/S000.tasks.md` (created → all DONE)
- `docs/frontend-spa/tasks/T001.analysis.md` (created)
- `docs/frontend-spa/tasks/T002.analysis.md` (created)
- `docs/frontend-spa/tasks/T004.analysis.md` (created)
- `docs/frontend-spa/tasks/T005.analysis.md` (created)
- `backend/db/migrations/008_add_password_hash.sql` (created)
- `backend/api/routes/auth.py` (created)
- `backend/auth/dependencies.py` (modified — HS256 dual-mode)
- `backend/api/app.py` (modified — auth router registered)
- `tests/api/test_auth.py` (created — 12 tests)

## S004 Task Board — DONE ✅ (2026-04-16)
| Task | Title | Status |
|------|-------|--------|
| T001 | QueryHistoryItem type + history state (queryStore) | DONE ✅ |
| T002 | HistoryItem component | DONE ✅ |
| T003 | HistoryPanel component | DONE ✅ |
| T004 | addHistory in submitQuery (queryStore) | DONE ✅ |
| T005 | Wire QueryPage sidebar + logout clearHistory | DONE ✅ |
Tests: 208/208 pass (20 new) | File: `docs/frontend-spa/tasks/S004.tasks.md`

## Open Questions
- (none)

## Assumptions
- A001: Backend `/v1/query` response shape đã stable (answer-citation + confidence-scoring DONE)
- A002: VITE_API_BASE_URL point tới backend /v1 root

## S001 Task Board — REVIEWED ✅ (2026-04-16)
| Task | Title | Status |
|------|-------|--------|
| T001 | Vite + React scaffold + package.json | REVIEWED ✅ |
| T002 | authStore (Zustand) — token + login/logout + proactive refresh | REVIEWED ✅ |
| T003 | Axios client.ts — interceptors + 401 redirect | REVIEWED ✅ |
| T004 | LoginPage.tsx + LoginForm.tsx | REVIEWED ✅ |
| T005 | App.tsx — Router + ProtectedRoute | REVIEWED ✅ |
| T006 | i18n auth strings (4 locales) | REVIEWED ✅ |
Parallel groups: G1[T001] → G2[T002∥T003∥T006] → G3[T004] → G4[T005]
File: `docs/frontend-spa/tasks/S001.tasks.md`
Review: `docs/frontend-spa/reviews/S001.review.md` | Verdict: APPROVED | Tests: 55/55 pass

## S002 Task Board — IMPLEMENTED ✅ (2026-04-16)
| Task | Title | Status |
|------|-------|--------|
| T001 | queryStore.ts — query state (no history) | DONE ✅ |
| T002 | SearchInput.tsx — 512-char limit + IME guard | DONE ✅ |
| T003 | LanguageSelector.tsx — 4 locales + localStorage | DONE ✅ |
| T004 | i18n setup + 4 locale JSON files (S002 keys) | DONE ✅ |
| T005 | QueryPage.tsx — wire SearchInput + LanguageSelector | DONE ✅ |
| T006 | App.tsx — add /query route + update tests | DONE ✅ |
Tests: 107/107 pass (55 S001 regression + 52 new S002) | File: `docs/frontend-spa/tasks/S002.tasks.md`

## S003 Task Board — DONE ✅ (2026-04-16)
| Task | Title | Status |
|------|-------|--------|
| T001 | queryStore — submitQuery + API call + error states | DONE ✅ |
| T002 | ConfidenceBadge.tsx — score thresholds + badge colors | DONE ✅ |
| T003 | CitationItem.tsx — title + score% + chunk preview | DONE ✅ |
| T004 | CitationList.tsx — collapsed > 3 + show-more toggle | DONE ✅ |
| T005 | LowConfidenceWarning.tsx + i18n results keys (4 locales) | DONE ✅ |
| T006 | AnswerPanel.tsx + QueryPage integration + react-markdown | DONE ✅ |
Parallel groups: G1[T001] → G2[T002∥T003∥T005] → G3[T004] → G4[T006]
Tests: 188/188 pass (107 prior + 81 new S003) | File: `docs/frontend-spa/tasks/S003.tasks.md`

## S005 Task Board — DONE ✅ (2026-04-16)
| Task | Title | Status |
|------|-------|--------|
| T001 | Create frontend/Dockerfile (multi-stage) | DONE ✅ |
| T002 | Create frontend/nginx.conf (SPA routing) | DONE ✅ |
| T003 | Create frontend/.env.example | DONE ✅ |
| T004 | Add frontend-spa service to docker-compose.yml | DONE ✅ |
| T005 | Smoke test — npm run build passes | DONE ✅ |
Parallel groups: G1[T001∥T002∥T003] → G2[T004] → G3[T005]
Build: 208/208 tests pass, npm run build ✅ (0 TS errors, 393KB bundle, 2.18s)
File: `docs/frontend-spa/tasks/S005.tasks.md`

### S005 Implementation Notes
- Created `src/vite-env.d.ts` with `/// <reference types="vite/client" />` — fixes import.meta.env typing
- Fixed `tsconfig.json` include: `["src"]` only (removed `"tests"`) — prevents tsc from checking Vitest globals in build
- Vite bakes VITE_* vars at BUILD TIME — docker-compose uses `build.args`, not `environment:`
- Dockerfile: `ARG VITE_API_BASE_URL` + `ENV VITE_API_BASE_URL=$VITE_API_BASE_URL` in stage 1
- nginx: `try_files $uri $uri/ /index.html` SPA routing + static asset cache + security headers
- Port: 8080:80 (D013)
- Bundle: 393.69 kB (128.24 kB gzip) — well under 2MB guideline

## Files Touched (S005)
- `frontend/Dockerfile` (created)
- `frontend/nginx.conf` (created)
- `frontend/.env.example` (created)
- `frontend/src/vite-env.d.ts` (created — Vite env type reference)
- `frontend/tsconfig.json` (modified — exclude tests from tsc build)
- `docker-compose.yml` (modified — frontend-spa service added)

## Status
S000 DONE ✅ (2026-04-16) — 12/12 tests pass, auth router live in app.py
S001 REVIEWED ✅ (2026-04-16) — Opus review APPROVED, 55/55 tests pass, 0 blockers
S002 IMPLEMENTED ✅ (2026-04-16) — 6/6 tasks DONE, 107/107 tests pass, 0 regressions
S003 IMPLEMENTED ✅ (2026-04-16) — 6/6 tasks DONE, 188/188 tests pass, 0 regressions
S004 REVIEWED ✅ (2026-04-16) — 5/5 tasks DONE, 208/208 tests pass, APPROVED
S005 DONE ✅ (2026-04-16) — 5/5 tasks DONE, 208/208 tests pass, npm run build ✅
Next: `/reviewcode frontend-spa S005` → `/report frontend-spa`

## Clarify Output
File: `docs/frontend-spa/clarify/frontend-spa.clarify.md`
- 5 BLOCKERs: ALL RESOLVED ✅ (Q1–Q5)
- 6 SHOULDs: defaults applied (Q6–Q11)
- 5 NITEs: non-blocking (Q12–Q16)
- 10 Auto-answered from CONSTITUTION.md / HARD.md / WARM

---

## Sync: 2026-04-16 (session #062)
Decisions added: D001–D008
Tasks changed: spec created (S000–S005)
Files touched: frontend-spa.spec.md (created), frontend-spa.sources.md (created), WARM/frontend-spa.mem.md (created)
Questions resolved: OQ1 (POST /v1/auth/token chưa có → S000 added)
New blockers: none

## Sync: 2026-04-16 (session #064)
Decisions added: none (plan decisions captured in plan file)
Tasks changed: checklist → PASS, plan → DONE; stories S000–S005 status: SPEC→PLANNED
Files touched: reviews/checklist.md (PASS), plan/frontend-spa.plan.md (created)
Questions resolved: WARN approved (S001 mock isolation mitigation)
New blockers: none

## Sync: 2026-04-16 (session #063)
Decisions added: D009–D013
Tasks changed: clarify complete (all BLOCKERs resolved)
Files touched: frontend-spa.clarify.md (created), HOT.md (updated), WARM/frontend-spa.mem.md (updated)
Questions resolved: Q1 (migration=008), Q2 (AUTH_SECRET_KEY=generate in S000), Q3 (proactive refresh), Q4 (91%), Q5 (8080:80)
New blockers: none

## Sync: 2026-04-16 (session #065 — /tasks S001)
Decisions added: none new
Tasks changed: S001 → 6 tasks created (T001–T006, all TODO)
Files touched: docs/frontend-spa/tasks/S001.tasks.md (created), HOT.md (updated), WARM/frontend-spa.mem.md (updated)
Questions resolved: none
New blockers: none

## Sync: 2026-04-16 (S000 complete)
Decisions added: none new (implementation decisions noted in S000 Implementation Notes above)
Tasks changed: T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE; S000→DONE
Files touched: 008_add_password_hash.sql, auth.py (route), dependencies.py, app.py, test_auth.py (12 tests), T001–T005 analysis files
Questions resolved: passlib/bcrypt compat (use direct bcrypt), dummy hash timing attack, AUTH_SECRET_KEY guard strategy
New blockers: none

## Sync: 2026-04-16 (session #066 — S001 /analyze)
Decisions added: none new
Tasks changed: S001 analysis complete → docs/frontend-spa/tasks/S001.analysis.md
Files touched: docs/frontend-spa/tasks/S001.analysis.md (created)
Questions resolved: none
New blockers: none
Risk flags (noted in analysis, not blockers):
  - T003: navigate inject must happen after Router mounts (fix in T005 useEffect)
  - T004: POST must use URLSearchParams (form encoding), not JSON
  - T002: credentials (username/password) must be nulled on logout()

## Sync: 2026-04-16 (session #070 — S002 /implement)
Decisions added: none (implementation notes captured in HOT.md)
Tasks changed: T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE, T006→DONE; S002→IMPLEMENTED
Files touched:
  - frontend/src/store/queryStore.ts (created)
  - frontend/src/components/query/SearchInput.tsx (created)
  - frontend/src/components/query/LanguageSelector.tsx (created)
  - frontend/src/pages/QueryPage.tsx (created)
  - frontend/src/App.tsx (modified — real QueryPage import replacing stub)
  - frontend/src/i18n/locales/{en,ja,vi,ko}.json (modified — added search.* + lang.* keys)
  - frontend/tests/store/queryStore.test.ts (created — 10 tests)
  - frontend/tests/components/query/SearchInput.test.tsx (created — 13 tests)
  - frontend/tests/components/query/LanguageSelector.test.tsx (created — 6 tests)
  - frontend/tests/i18n/i18n.test.ts (modified — added S002 keys, 46 total)
  - frontend/tests/pages/QueryPage.test.tsx (created — 7 tests)
  - frontend/tests/App.test.tsx (created — 4 tests)
  - docs/frontend-spa/tasks/S002.tasks.md (all statuses → DONE)
Questions resolved: none
New blockers: none
Implementation notes:
  - IME guard: e.nativeEvent.isComposing correct in prod; tests use native KeyboardEvent({isComposing:true}) directly (jsdom compositionStart limitation)
  - vi.hoisted() required for vi.fn() spies referenced inside vi.mock factories (hoisting order)
  - Store state set before render() call to avoid React act() warnings
Total tests: 107/107 pass (55 S001 + 52 S002); 0 regressions

## Sync: 2026-04-16 (session #069 — S002 /tasks)
Decisions added: none new
Tasks changed: S002 → 6 tasks created (T001–T006, all TODO)
Files touched: docs/frontend-spa/tasks/S002.tasks.md (created), HOT.md (updated), WARM/frontend-spa.mem.md (updated)
Questions resolved: none
New blockers: none

## Sync: 2026-04-16 (session #067 — S001 /reviewcode quick)
Decisions added: none
Tasks changed: T001–T006 → REVIEWED ✅; S001 → REVIEWED (verdict: APPROVED)
Files touched: docs/frontend-spa/reviews/S001.review.md (created), docs/frontend-spa/tasks/S001.tasks.md (statuses updated)
Questions resolved: all 3 risk flags from /analyze confirmed mitigated in code:
  - T003 risk → setNavigate wrapped in useEffect in App.tsx ✅
  - T004 risk → URLSearchParams + form-urlencoded header in LoginForm ✅
  - T002 risk → logout() nulls username/password + token + clears refresh timer ✅
New blockers: none
Security/frontend checks (all pass): no hardcoded URLs/secrets, token never in localStorage, URLSearchParams POST, setNavigate in useEffect, all 7 i18n keys × 4 locales, Navigate replace=true, non-401 errors re-thrown
Next: `/implement frontend-spa S002` (Query Page — Search Input & Language Selector)

## Sync: 2026-04-16 (session #071 — S003 /tasks)
Decisions added: none new (design choices captured in S003 task file)
Tasks changed: S003 → 6 tasks created (T001–T006, all TODO)
Files touched: docs/frontend-spa/tasks/S003.tasks.md (created), HOT.md (updated), WARM/frontend-spa.mem.md (updated — S003 task board added)
Questions resolved: none
New blockers: none
Key task design notes:
  - chunk_preview: plain text only (ReactMarkdown skipped — XSS risk on partial RAG chunks)
  - Score display: Math.round(score * 100) + "%" per D012
  - CitationList empty array → renders nothing (AnswerPanel owns empty/no-source copy)
  - 7 i18n keys for results.* namespace across 4 locales in T005
  - react-markdown added to package.json in T006

## Sync: 2026-04-16 (session #072 — S003 /implement)
Decisions added: none new
Tasks changed: T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE, T006→DONE; S003→IMPLEMENTED
Files touched:
  - frontend/src/store/queryStore.ts (modified — added Citation/QueryResult types, result state, submitQuery)
  - frontend/src/components/results/ConfidenceBadge.tsx (created)
  - frontend/src/components/results/CitationItem.tsx (created)
  - frontend/src/components/results/CitationList.tsx (created)
  - frontend/src/components/results/LowConfidenceWarning.tsx (created)
  - frontend/src/components/results/AnswerPanel.tsx (created)
  - frontend/src/pages/QueryPage.tsx (modified — wire submitQuery + AnswerPanel)
  - frontend/src/i18n/locales/{en,ja,vi,ko}.json (modified — added results.* 7 keys each)
  - frontend/tests/store/queryStore.test.ts (modified — 9 submitQuery tests added)
  - frontend/tests/components/results/ConfidenceBadge.test.tsx (created — 9 tests)
  - frontend/tests/components/results/CitationItem.test.tsx (created — 8 tests)
  - frontend/tests/components/results/CitationList.test.tsx (created — 11 tests)
  - frontend/tests/components/results/LowConfidenceWarning.test.tsx (created — 3 tests)
  - frontend/tests/components/results/AnswerPanel.test.tsx (created — 12 tests)
  - frontend/tests/pages/QueryPage.test.tsx (modified — wired submitQuery mock, AnswerPanel mock, 8 tests)
  - frontend/tests/i18n/i18n.test.ts (modified — added 7 results.* keys × 4 locales)
  - frontend/tests/App.test.tsx (modified — removed results-area check, added result:null to setState)
Questions resolved: none
New blockers: none
Regression: App.test.tsx had getElementById('results-area') — removed (stub div replaced by AnswerPanel)
Total tests: 188/188 pass (107 prior + 81 new S003); 0 regressions

## Sync: 2026-04-16 (session #073 — S004 /tasks)
Decisions added: none new
Tasks changed: S004 → 5 tasks created (T001–T005, all TODO); S004 status SPEC→TASKS ✅
Files touched:
  - docs/frontend-spa/tasks/S004.tasks.md (created)
  - .claude/memory/WARM/frontend-spa.mem.md (updated — S004 task board, S004 status)
  - .claude/memory/HOT.md (updated — In Progress entry, Recent Decisions, Next Session Start)
Questions resolved: none
New blockers: none
Task design notes (S004):
  - T001: history[] in queryStore; addHistory cap=20, newest-first; reset() preserves history
  - T002: HistoryItem CJK-safe truncation=[...str].slice(0,60)+'…'; HH:mm timestamp
  - T003: HistoryPanel returns null when history.length===0 (AC Q10); i18n history.title + history.clear × 4 locales
  - T004: addHistory called inside submitQuery after success only; uses get() accessor
  - T005: QueryPage flex layout with sidebar; authStore.logout() calls clearHistory() first
Parallel groups: G1[T001] → G2[T002∥T004] → G3[T003] → G4[T005]
Next: /reviewcode frontend-spa S003 → then /implement frontend-spa S004

## Sync: 2026-04-16 (session #074 — S004 /implement)
Decisions added: none new
Tasks changed: T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE; S004→IMPLEMENTED ✅
Files touched:
  - frontend/src/store/queryStore.ts (modified — QueryHistoryItem interface, history state, addHistory/clearHistory/selectHistory actions, get() in submitQuery)
  - frontend/src/store/authStore.ts (modified — import useQueryStore, clearHistory() call in logout)
  - frontend/src/pages/QueryPage.tsx (modified — flex layout wrapper, HistoryPanel sidebar)
  - frontend/src/components/history/HistoryItem.tsx (created — CJK-safe truncation, HH:mm time)
  - frontend/src/components/history/HistoryPanel.tsx (created — null when empty, aside+clear button)
  - frontend/src/i18n/locales/en.json (modified — history.title, history.clear)
  - frontend/src/i18n/locales/ja.json (modified — 検索履歴, 履歴をクリア)
  - frontend/src/i18n/locales/vi.json (modified — Lịch sử tìm kiếm, Xóa lịch sử)
  - frontend/src/i18n/locales/ko.json (modified — 검색 기록, 기록 지우기)
  - frontend/tests/store/queryStore.test.ts (modified — history: [] in beforeEach; history tests added T001+T004)
  - frontend/tests/store/authStore.test.ts (modified — import queryStore; reset history in beforeEach; clearHistory on logout test)
  - frontend/tests/pages/QueryPage.test.tsx (modified — HistoryPanel mock; history field in setState calls; HistoryPanel tests added)
  - frontend/tests/components/history/HistoryItem.test.tsx (created — 5 tests)
  - frontend/tests/components/history/HistoryPanel.test.tsx (created — 5 tests)
  - docs/frontend-spa/tasks/S004.tasks.md (all statuses → DONE)
Questions resolved: none
New blockers: none
Test result: 208/208 pass, 18 test files, 0 failures
Next: /reviewcode frontend-spa S004 → /tasks frontend-spa S005
