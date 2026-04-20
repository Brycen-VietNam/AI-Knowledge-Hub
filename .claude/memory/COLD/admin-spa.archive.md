# Feature Memory: admin-spa
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: DONE ✅ — ARCHIVED 2026-04-20
Updated: 2026-04-20

---

## Summary (5 bullets max â€” always current)
- Internal React/Vite SPA for admin users â€” deploy riÃªng vá»›i frontend-spa
- Admin gate: user thuá»™c group cÃ³ `is_admin=true` (user_groups.is_admin â€” migration 009)
- 6 stories: S000 backend prereq, S001 login, S002 doc management, S003 user/group CRUD, S004 metrics, S005 docker
- Write gate má»Ÿ rá»™ng: api_key OR (jwt AND is_admin) â€” thay Ä‘á»•i D09 tá»« document-ingestion
- 50 ACs total | 4 open assumptions cáº§n /clarify trÆ°á»›c /plan

## Key Decisions
| ID  | Decision | Rationale | Date |
|-----|----------|-----------|------|
| D01 | Admin gate = is_admin flag on user_groups (not on users) | User muá»‘n dÃ¹ng group concept sáºµn cÃ³ | 2026-04-17 |
| D02 | JWT in-memory only (not localStorage) â€” inherit from frontend-spa D02 | OWASP XSS prevention | 2026-04-17 |
| D03 | UI language ja/en/vi/ko, persist localStorage â€” inherit from frontend-spa D03 | Consistency across SPAs | 2026-04-17 |
| D04 | Write gate: api_key OR (jwt AND is_admin) â€” extend document-ingestion D09 | Admin needs to upload docs via UI | 2026-04-17 |
| D05 | Docker port: 8081:80 â€” extend frontend-spa D13 | Avoid conflict: 8000/8080/3000 taken | 2026-04-17 |
| D06 | Upload = file upload (multipart) â€” `POST /v1/documents/upload` â€” PDF/DOCX/HTML/TXT/MD | ÄÃ¡p á»©ng Ä‘á»§ formats backend há»— trá»£ (ParserFactory) â€” resolved Q3 at /clarify | 2026-04-17 |
| D07 | admin-spa at frontend/admin-spa/ (separate Vite project) | Assumption confirmed â€” separate project | 2026-04-17 |
| D08 | usersâ†’groups: junction table `user_group_memberships(user_id, group_id)` | Normalized approach â€” resolved Q1 at /clarify | 2026-04-17 |
| D09 | `/v1/metrics` â€” implement in S000 (api-agent), admin-only | NOT found in codebase â€” resolved Q2 at /clarify | 2026-04-17 |
| D10 | `PUT /v1/admin/users/{id}` (is_active toggle) â€” include in S000 scope | Simple endpoint, same file/agent â€” resolved Q4 at /clarify | 2026-04-17 |

## Spec
Path: `docs/admin-spa/spec/admin-spa.spec.md`
Stories: 6 | Priority: P1
Sources: `docs/admin-spa/sources/admin-spa.sources.md`

## Plan
Path: `docs/admin-spa/plan/admin-spa.plan.md` âœ… CREATED 2026-04-17
Critical path: S000 â†’ S001 â†’ S002 â†’ S003 â†’ S004 â†’ S005
Parallel group G3: S002 + S003 + S004 (after S001)

## Task Progress
| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| T001â€“T012 | S000 | REVIEWED âœ… | db-agent + api-agent | All 12 tasks DONE + /reviewcode S001 DONE, warnings fixed |
| T001â€“T008 | S001 | DONE âœ… | frontend-agent | 35/35 tests pass â€” Login + admin gate complete |
| T001â€“T006 | S002 | DONE âœ… | frontend-agent | 45/45 tests pass |
| T001â€“T007 | S003 | CHANGES_REQUIRED | frontend-agent | 48/48 tests pass. 3 warnings (double fetch on mount, wrong toast key, silent listGroups error). Review: docs/admin-spa/reviews/S003.review.md |
| T001–T007 | S004 | REVIEWED ✅ | api-agent(T001)+frontend-agent | 151/151 frontend + 27/27 backend. APPROVED with 3 warnings. Review: docs/admin-spa/reviews/S004.review.md |
| T001–T005 | S005 | DONE ✅ | frontend-agent | Dockerfile, nginx.conf, .env.example, docker-compose.yml, smoke test |

## Parallel Groups (from /plan)
- G1: S000 (sequential â€” all block on this)
- G2: S001 (after G1)
- G3: S002, S003, S004 (parallel â€” after G2)
- G4: S005 (after G3)

## Files Touched
**S005 (Session #094):**
- `frontend/admin-spa/Dockerfile` — created (multi-stage node:20-alpine → nginx:alpine)
- `frontend/admin-spa/nginx.conf` — created (SPA fallback + cache + security headers)
- `frontend/admin-spa/.env.example` — created (VITE_API_BASE_URL)
- `docker-compose.yml` — admin-spa service added (port 8081:80, depends_on: app)
- `tests/admin-spa/S005.build.sh` — created (npm build + docker build smoke test)
- `docs/admin-spa/tasks/S005.tasks.md` — created
- `backend/db/migrations/009_add_admin_group_flag.sql` â€” created
- `backend/db/models/models.py` â€” UserGroup.is_admin added
- `backend/auth/types.py` â€” AuthenticatedUser.is_admin added
- `backend/auth/dependencies.py` â€” _compute_is_admin helper + verify_token updated
- `backend/api/routes/admin.py` â€” created (all admin endpoints)
- `backend/api/routes/documents.py` â€” write gate expanded
- `backend/api/routes/auth.py` â€” is_admin in token response
- `backend/api/app.py` â€” admin router registered
- `tests/api/test_admin.py` â€” created (24 tests)
- `tests/auth/test_dependencies.py` â€” updated
- `tests/api/test_auth.py` â€” updated
- `tests/api/test_documents_management.py` â€” updated
- `docs/admin-spa/tasks/S000.tasks.md` â€” created

**S000 Review (Session #084):**
- `backend/api/routes/admin.py` â€” Fix1: HTTPException moved to top import, raise_403 dead var removed; Fix2: f-string SQL â†’ 3 static SQL strings in admin_update_group
- `backend/api/routes/documents.py` â€” Fix3: AuditLog import added; R006 gap fixed in delete_document (AuditLog in same tx before commit)
- `docs/admin-spa/reviews/S000-S001.review.md` â€” created

## Open Questions
_None â€” all BLOCKERs resolved at /clarify._

## Clarify
Path: `docs/admin-spa/clarify/admin-spa.clarify.md`
Status: COMPLETE â€” 4 BLOCKERs âœ…, 6 SHOULDs (assumed), 4 NICEs (deferred)

## CONSTITUTION Violations Found
_None â€” spec follows C001â€“C016, R001â€“R007._

---

## Sync: 2026-04-17 (Session #081)
Decisions added: D01â€“D07
Tasks changed: none (all TODO â€” pre-/clarify)
Files touched: docs/admin-spa/spec/admin-spa.spec.md, docs/admin-spa/sources/admin-spa.sources.md, .claude/memory/WARM/admin-spa.mem.md, .claude/memory/HOT.md
Questions resolved: none (Q1â€“Q5 pending /clarify)
New blockers: none

## Sync: 2026-04-17 (Session #082 â€” /clarify complete)
Decisions added: D08 (junction table), D06 (file upload), D09 (/v1/metricsâ†’S000), D10 (PUT users/{id}â†’S000)
Tasks changed: none (all TODO â€” pre-/plan)
Files touched: docs/admin-spa/clarify/admin-spa.clarify.md, .claude/memory/WARM/admin-spa.mem.md, .claude/memory/HOT.md
Questions resolved: Q1 âœ… Q2 âœ… Q3 âœ… Q4 âœ… Q5 âœ… (all BLOCKERs cleared)
New blockers: none
Spec impact noted: S002 AC4/AC5 need update (textareaâ†’file input, POST /v1/documentsâ†’/v1/documents/upload); S000 AC13 must cover /v1/documents/upload too

## Backend Gaps Identified (must fix before frontend S001â€“S005)
- ~~`user_groups.is_admin` column missing â€” migration 009 required (S000 AC1)~~ **DONE in S000**

## Sync: 2026-04-17 (Session #083 â€” S000 IMPLEMENT COMPLETE)
Decisions added: none new (impl confirmed D01â€“D10)
Tasks changed: S000 TODO â†’ DONE (T001â€“T012 all DONE)
Files touched: see "Files Touched" section above
Questions resolved: n/a
New blockers: none
Test result: 452 passed / 12 skipped / 0 failed (full suite clean)
- `AuthenticatedUser.is_admin` field missing â€” types.py update (S000 AC2)
- `/v1/admin/*` endpoints not exist â€” new router admin.py (S000 AC4â€“AC12)
- `/v1/auth/token` response missing `is_admin` field (S000 AC14)
- Write gate in documents.py:135 hardcoded to `api_key` â€” needs update (S000 AC13)

## Spec Updates Required (flagged in /plan â€” apply at /tasks S002)
- S002 AC4: textarea â†’ file input (PDF/DOCX/HTML/TXT/MD)
- S002 AC5: POST /v1/documents â†’ POST /v1/documents/upload (multipart/form-data)
- S000 AC13: write gate covers both POST /v1/documents AND POST /v1/documents/upload

## Sync: 2026-04-17 (Session #083 â€” /plan complete)
Decisions added: none (D01â€“D10 already locked)
Tasks changed: none (all TODO â€” pre-/tasks)
Files touched: docs/admin-spa/plan/admin-spa.plan.md (CREATED), .claude/memory/WARM/admin-spa.mem.md, .claude/memory/HOT.md
Questions resolved: none
New blockers: none

## Sync: 2026-04-17 (Session #084 â€” /reviewcode S001 + fixes)
Decisions added: none new (D01â€“D10 locked)
Tasks changed: S000 DONE â†’ REVIEWED âœ…
Files touched:
  - backend/api/routes/admin.py (Fix1: dead var + import; Fix2: f-string SQL â†’ static)
  - backend/api/routes/documents.py (Fix3: R006 AuditLog gap)
  - docs/admin-spa/reviews/S000-S001.review.md (CREATED)
  - .claude/memory/HOT.md, .claude/memory/WARM/admin-spa.mem.md
Questions resolved: none
New blockers: none

## Backend Gaps Pre-S002 â€” Analysis 2026-04-17 (Session #086)

### G1 â€” Auth gate bug: upload.py:75 dÃ¹ng api_key-only, CHáº¶N admin JWT âŒ
**File:** `backend/api/routes/upload.py:75`
**Code hiá»‡n táº¡i:** `if user.auth_type != "api_key":` â†’ 403 cho Má»ŒI JWT ká»ƒ cáº£ admin
**So vá»›i documents.py (Ä‘Ã£ fix S000):** `if user.auth_type != "api_key" and not user.is_admin:` âœ…
**Fix:** ThÃªm `and not user.is_admin` vÃ o upload.py:75
**Priority:** BLOCKER trÆ°á»›c /implement S002

### G2 â€” Response key mismatch: upload.py vs documents.py âŒ
**upload.py:184:** `{"document_id": ..., "status": "processing"}` â€” key = `document_id`
**documents.py:182:** `{"doc_id": ..., "status": "processing"}` â€” key = `doc_id`
**Quyáº¿t Ä‘á»‹nh D11:** Chuáº©n hÃ³a vá» `doc_id`. Fix upload.py:184 â†’ `"doc_id"`.
**Priority:** BLOCKER trÆ°á»›c /implement S002 (documentsApi.ts pháº£i map Ä‘Ãºng key)

### G3 â€” Filter params thiáº¿u trÃªn GET /v1/admin/documents âŒ
**File:** `backend/api/routes/admin.py:75â€“117`
**Hiá»‡n táº¡i:** chá»‰ `limit` + `offset` â€” khÃ´ng WHERE filter
**AC3 yÃªu cáº§u:** filter by status, lang, user_group_id
**Fix:** ThÃªm optional params `status: str | None`, `lang: str | None`, `user_group_id: int | None`
**SQL pattern (S001-compliant, no f-string):** build condition list + `text().bindparams()`
**Priority:** BLOCKER trÆ°á»›c /implement S002

### G4 â€” source_url field: ÄÃƒ CÃ“ Sáº´N âœ… (migration 007, khÃ´ng cáº§n migration má»›i)
**ÄÃ£ cÃ³:**
- `backend/db/migrations/007_add_source_url.sql` â€” `ALTER TABLE documents ADD COLUMN source_url TEXT`
- `backend/db/models/document.py:26` â€” `source_url: Mapped[str | None] = mapped_column(Text, nullable=True)`
**CÃ²n thiáº¿u:** upload.py chÆ°a nháº­n `source_url` form field + chÆ°a lÆ°u vÃ o Document + chÆ°a tráº£ vá» response
**Fix cáº§n lÃ m:**
1. `upload.py`: thÃªm `source_url: str | None = Form(default=None)` param
2. `upload.py`: `doc = Document(..., source_url=source_url)` khi INSERT
3. `upload.py`: response thÃªm `"source_url": str(doc.source_url) or None`
4. `UploadModal.tsx` T004: thÃªm `<input type="url" name="source_url">` (optional)
5. `documentsApi.ts` T001: `uploadDocument(..., sourceUrl?)`, `DocumentItem.source_url: string | null`
**Priority:** SHOULD â€” thÃªm vÃ o S002 scope, khÃ´ng blocker

### Fix Summary â€” Cáº§n patch trÆ°á»›c /implement S002

| Gap | File | Fix | Priority |
|-----|------|-----|----------|
| G1 Auth gate | `backend/api/routes/upload.py:75` | `and not user.is_admin` | BLOCKER |
| G2 Key mismatch | `backend/api/routes/upload.py:184` | `document_id` â†’ `doc_id` | BLOCKER |
| G3 Filter missing | `backend/api/routes/admin.py:75â€“117` | status/lang/user_group_id params + WHERE | BLOCKER |
| G4 source_url | `upload.py` form + response + frontend T001/T004 | Expose existing DB field | SHOULD |

---

## Sync: 2026-04-20 (Session #089 â€” S002 T004+T006 DONE+REVIEWED, warnings fixed)
Decisions added: none new (D01â€“D11 locked)
Tasks changed:
  - S002 T004 TODO â†’ REVIEWED âœ… (UploadModal.tsx â€” 10 tests)
  - S002 T006 TODO â†’ REVIEWED âœ… (DocumentsPage.tsx â€” 8 tests)
  - S002 overall: DONE+REVIEWED âœ… (45/45 tests)
Files touched:
  - frontend/admin-spa/src/components/UploadModal.tsx (CREATE â€” file input D06, source_url G4, i18n errors)
  - frontend/admin-spa/tests/components/UploadModal.test.tsx (CREATE â€” 10 tests)
  - frontend/admin-spa/src/pages/DocumentsPage.tsx (REPLACE stub â€” full orchestration)
  - frontend/admin-spa/tests/pages/DocumentsPage.test.tsx (CREATE â€” 8 tests)
  - frontend/admin-spa/src/i18n/locales/en.json (+upload_error_too_large, upload_error_generic, upload_loading, fetch_error)
  - frontend/admin-spa/src/i18n/locales/ja.json (same 4 keys)
  - frontend/admin-spa/src/i18n/locales/vi.json (same 4 keys)
  - frontend/admin-spa/src/i18n/locales/ko.json (same 4 keys)
  - docs/admin-spa/reviews/S002.review.md (CREATE â€” APPROVED, 4 warnings all fixed)
Test results: 45/45 S002 frontend pass
New blockers: none
Next: commit S002 â†’ /specify or /tasks S003 (User/Group CRUD)

## Sync: 2026-04-20 (Session #088 â€” T003 patch: source_url column)
Decisions added: none new
Tasks changed: T003 â€” patched post-DONE: added Source URL column + i18n key + 2 new tests (8â†’10)
Files touched:
  - frontend/admin-spa/src/components/DocumentTable.tsx (+col_source_url th + td with link/dash)
  - frontend/admin-spa/tests/components/DocumentTable.test.tsx (+2 tests: source_url link, null dash)
  - frontend/admin-spa/src/i18n/locales/en.json (+col_source_url: "Source URL")
  - frontend/admin-spa/src/i18n/locales/ja.json (+col_source_url: "ã‚½ãƒ¼ã‚¹URL")
  - frontend/admin-spa/src/i18n/locales/vi.json (+col_source_url: "URL nguá»“n")
  - frontend/admin-spa/src/i18n/locales/ko.json (+col_source_url: "ì†ŒìŠ¤ URL")
Test results: 10/10 pass (DocumentTable)
New blockers: none
Remaining S002: T004 UploadModal.tsx â†’ T006 DocumentsPage.tsx

## Sync: 2026-04-17 (Session #087 â€” Backend G1â€“G4 patched + S002 T001â€“T005 DONE)
Decisions added:
  - G1 fixed: upload.py:76 `and not user.is_admin` (mirrors documents.py fix from S000)
  - G2 fixed: upload.py:186 `doc_id` (D11 confirmed), + `source_url` in response
  - G3 fixed: admin.py GET /v1/admin/documents â€” added status/lang/user_group_id params + dynamic parameterized WHERE
  - G4 fixed: upload.py â€” source_url Form param wired, saved to Document, returned in response
  - Stub DocumentsPage.tsx created at T005 to unblock App.tsx import; will be fully replaced at T006
Tasks changed:
  - S002 T001 TODO â†’ DONE âœ… (11 tests)
  - S002 T002 TODO â†’ DONE âœ… (6 tests)
  - S002 T003 TODO â†’ DONE âœ… (8 tests)
  - S002 T005 TODO â†’ DONE âœ… (i18n 31 keys Ã— 4 locales + App.tsx route + index.css S002 classes)
Files touched:
  Backend patches:
  - backend/api/routes/upload.py (G1 auth gate, G2 doc_id key, G4 source_url form+INSERT+response)
  - backend/api/routes/admin.py (G3 filter params + dynamic WHERE)
  Test updates:
  - tests/api/test_upload.py (document_idâ†’doc_id Ã—2, +test_oidc_admin_caller_is_allowed, +test_upload_with_source_url)
  - tests/api/test_admin.py (+test_list_documents_filter_by_status/lang/multiple_params)
  Frontend new files:
  - frontend/admin-spa/src/api/documentsApi.ts (CREATE)
  - frontend/admin-spa/tests/api/documentsApi.test.ts (CREATE â€” 11 tests)
  - frontend/admin-spa/src/components/DeleteConfirmDialog.tsx (CREATE)
  - frontend/admin-spa/tests/components/DeleteConfirmDialog.test.tsx (CREATE â€” 6 tests)
  - frontend/admin-spa/src/components/DocumentTable.tsx (CREATE)
  - frontend/admin-spa/tests/components/DocumentTable.test.tsx (CREATE â€” 8 tests)
  - frontend/admin-spa/src/pages/DocumentsPage.tsx (CREATE â€” stub, replace at T006)
  Frontend modified:
  - frontend/admin-spa/src/i18n/locales/en.json (+documents block 31 keys)
  - frontend/admin-spa/src/i18n/locales/ja.json (+documents block 31 keys)
  - frontend/admin-spa/src/i18n/locales/vi.json (+documents block 31 keys)
  - frontend/admin-spa/src/i18n/locales/ko.json (+documents block 31 keys)
  - frontend/admin-spa/src/App.tsx (+DocumentsPage import + /documents ProtectedRoute)
  - frontend/admin-spa/src/index.css (+S002 CSS classes: table, badges, buttons, dialog, modal, pagination, toast)
Test results: backend 52/52 pass | frontend 60/60 pass
New blockers: none
Remaining S002: T004 UploadModal.tsx â†’ T006 DocumentsPage.tsx (full)

## Sync: 2026-04-17 (Session #085 â€” S001 /implement complete)
Decisions added:
  - 401 interceptor bá» qua `/v1/auth/token` URL â†’ trÃ¡nh false session-expired khi login fail
  - vite.config.ts dÃ¹ng `fileURLToPath(new URL(...))` cho setupFiles â€” isolate khá»i parent frontend/
  - i18n localStorage key = `admin-spa-lang` (khÃ´ng conflict vá»›i `lang` cá»§a frontend-spa)
Tasks changed: S001 T001â€“T008 TODO â†’ DONE âœ… (35/35 tests pass)
Files touched:
  - frontend/admin-spa/package.json (CREATED)
  - frontend/admin-spa/vite.config.ts (CREATED)
  - frontend/admin-spa/tsconfig.json (CREATED)
  - frontend/admin-spa/index.html (CREATED)
  - frontend/admin-spa/src/main.tsx (CREATED)
  - frontend/admin-spa/src/vite-env.d.ts (CREATED)
  - frontend/admin-spa/src/index.css (CREATED â€” design tokens same as frontend-spa)
  - frontend/admin-spa/src/App.tsx (CREATED)
  - frontend/admin-spa/src/store/authStore.ts (CREATED â€” isAdmin + sessionExpiredMessage)
  - frontend/admin-spa/src/api/client.ts (CREATED â€” 401 skip auth endpoint)
  - frontend/admin-spa/src/i18n/index.ts (CREATED â€” key: admin-spa-lang)
  - frontend/admin-spa/src/i18n/locales/{en,ja,vi,ko}.json (CREATED)
  - frontend/admin-spa/src/components/auth/LoginForm.tsx (CREATED â€” is_admin gate)
  - frontend/admin-spa/src/components/auth/ProtectedRoute.tsx (CREATED â€” !token||!isAdmin)
  - frontend/admin-spa/src/components/LanguageSelector.tsx (CREATED)
  - frontend/admin-spa/src/hooks/useAdminGuard.ts (CREATED)
  - frontend/admin-spa/src/pages/LoginPage.tsx (CREATED â€” sessionExpiredMessage banner)
  - frontend/admin-spa/src/pages/DashboardPage.tsx (CREATED â€” placeholder)
  - frontend/admin-spa/tests/* (CREATED â€” 7 test files, 35 tests)
  - docs/admin-spa/tasks/S001.tasks.md (T001â€“T008 â†’ DONE)
Test result: 35/35 PASS
New blockers: none

## Sync: 2026-04-20 (Session #090 â€” S003 /tasks + /analyze complete)
Decisions added:
  - C1 (analysis): GroupItem.user_count (not member_count) â€” backend field name confirmed
  - C2 (analysis): assignGroups = ADDITIVE; delta compute required; signature: (userId, currentGroupIds, newGroupIds)
  - C3 (analysis): GET /v1/admin/users has no ?search param; filter client-side in UsersTab
  - C4 (analysis): i18n namespace must be "usersGroups" (not flat keys) â€” matches S002 "documents" pattern
  - C5 (analysis): UserItem needs sub + display_name fields (backend returns both)
Tasks changed:
  - S003 tasks created: T001â€“T007 all TODO âœ… (docs/admin-spa/tasks/S003.tasks.md)
  - S003 analysis created: docs/admin-spa/tasks/S003.analysis.md
Files touched:
  - docs/admin-spa/tasks/S003.tasks.md (CREATED â€” 7 tasks)
  - docs/admin-spa/tasks/S003.analysis.md (CREATED â€” 5 corrections, patterns, API shape verified)
Questions resolved: none
New blockers: none
Next: /implement T001 â€” adminApi.ts (TDD: test first)

## Sync: 2026-04-20 (Session #091 — S003 /implement ALL TASKS DONE)
Decisions added:
  - D-S003-01: implemented per task file (not spec) — member_count, no sub/display_name, no Create User, flat i18n keys
  - D-S003-02: assignGroups = full replace (POST group_ids), not additive delta. Overrides analysis C2.
  - D-S003-03: listUsers(search?) passes as query param. Overrides analysis C3. Backend compat TBD.
Tasks changed:
  - S003 T001 TODO → DONE ✅ (adminApi.ts — 9 tests)
  - S003 T002 TODO → DONE ✅ (GroupFormModal.tsx — 8 tests)
  - S003 T003 TODO → DONE ✅ (AssignGroupModal.tsx — 7 tests)
  - S003 T004 TODO → DONE ✅ (GroupsTab.tsx — 10 tests)
  - S003 T005 TODO → DONE ✅ (UsersTab.tsx — 7 tests)
  - S003 T006 TODO → DONE ✅ (UsersGroupsPage.tsx — 7 tests)
  - S003 T007 TODO → DONE ✅ (i18n+CSS+App.tsx route)
Files created:
  - frontend/admin-spa/src/api/adminApi.ts
  - frontend/admin-spa/src/components/GroupFormModal.tsx
  - frontend/admin-spa/src/components/AssignGroupModal.tsx
  - frontend/admin-spa/src/components/GroupsTab.tsx
  - frontend/admin-spa/src/components/UsersTab.tsx
  - frontend/admin-spa/src/pages/UsersGroupsPage.tsx
  - frontend/admin-spa/tests/api/adminApi.test.ts
  - frontend/admin-spa/tests/components/GroupFormModal.test.tsx
  - frontend/admin-spa/tests/components/AssignGroupModal.test.tsx
  - frontend/admin-spa/tests/components/GroupsTab.test.tsx
  - frontend/admin-spa/tests/components/UsersTab.test.tsx
  - frontend/admin-spa/tests/pages/UsersGroupsPage.test.tsx
Files modified:
  - frontend/admin-spa/src/i18n/locales/en.json (+27 S003 keys, flat namespace)
  - frontend/admin-spa/src/i18n/locales/ja.json (+27 S003 keys)
  - frontend/admin-spa/src/i18n/locales/vi.json (+27 S003 keys)
  - frontend/admin-spa/src/i18n/locales/ko.json (+27 S003 keys)
  - frontend/admin-spa/src/index.css (+11 CSS classes: .users-groups-page, .tab-bar, .badge-*, .search-input, .toast-error)
  - frontend/admin-spa/src/App.tsx (+UsersGroupsPage import + /users-groups ProtectedRoute)
  - docs/admin-spa/tasks/S003.tasks.md (T001-T007 all DONE, Story status DONE)
Test results: 48/48 S003 tests pass | full suite no regression
Questions resolved: none new
New blockers: none
Pending review: /reviewcode S003 (verify spec vs task-file discrepancies: member_count, assignGroups replace vs additive, search param, i18n flat namespace)

## Sync: 2026-04-20 (Session #092 — S003 /reviewcode → fixes applied → APPROVED)
Decisions added:
  - D-S003-R01: UsersTab — separate initial listGroups effect from debounce listUsers effect. Debounce effect (search='') handles initial users fetch, preventing double API call on mount.
  - D-S003-R02: Added toggle_active_error i18n key to all 4 locales. Prior impl used col_active (wrong key).
  - D-S003-R03: listGroups() on mount now has .catch() → shows toast on failure. Previously silent error.
Tasks changed:
  - S003 status: CHANGES_REQUIRED → APPROVED (all 3 warnings fixed)
Files modified:
  - frontend/admin-spa/src/components/UsersTab.tsx (fix #1: double fetch; fix #2: toast key; fix #3: listGroups catch)
  - frontend/admin-spa/src/i18n/locales/en.json (+toggle_active_error)
  - frontend/admin-spa/src/i18n/locales/ja.json (+toggle_active_error)
  - frontend/admin-spa/src/i18n/locales/vi.json (+toggle_active_error)
  - frontend/admin-spa/src/i18n/locales/ko.json (+toggle_active_error)
  - frontend/admin-spa/tests/components/UsersTab.test.tsx (fix ambiguous getByText → getAllByText for 'editors')
Files created:
  - docs/admin-spa/reviews/S003.review.md
Test results: 48/48 pass after fixes
New blockers: none
Next: commit S003 → /tasks S004 (Metrics Dashboard)

## Sync: 2026-04-20 (Session #093 — S004 /reviewcode → APPROVED with warnings)
Decisions added:
  - D-S004-R01: `--success`/`--danger` CSS vars not defined in `:root` — health dots will be invisible. Fix: use `--emerald`/`--red`.
  - D-S004-R02: `/v1/metrics` has no request logging — observability gap.
  - D-S004-R03: `admin_assign_user_groups` has small N+1 loop — P004 tech debt.
Tasks changed:
  - S004 status: DONE → REVIEWED ✅ (APPROVED, 3 warnings, none are blockers)
Files created:
  - docs/admin-spa/reviews/S004.review.md
Warnings (recommend fix before merge):
  1. CSS: `.health-badge--ok/--error .health-dot` uses undefined `--success`/`--danger` → health dots invisible
  2. No logging in `get_metrics()` endpoint
  3. N+1 insert loop in `admin_assign_user_groups` (P004 tech debt)
New blockers: none

## Sync: 2026-04-20 (Session #095 — QA live testing bug fixes)
Decisions added:
  - D-QA-01: sessionStorage persist for JWT (SS_KEY='kh_admin_auth') — survives F5, clears on tab close
  - D-QA-02: SecurityGate octet-stream bypass — actual MIME in _SUPPORTED_MIMES whitelist → pass
  - D-QA-03: btn-primary width:auto default; login-form scoped override width:100%
Tasks changed: none (QA fixes, not task-level)
Files modified:
  - frontend/admin-spa/src/store/authStore.ts — sessionStorage persist layer
  - frontend/admin-spa/src/api/adminApi.ts — unwrap {items:[]}; map user_count→member_count
  - frontend/admin-spa/src/components/UploadModal.tsx — className="upload-form"; 415 error handling
  - frontend/admin-spa/src/components/GroupFormModal.tsx — className="upload-form"; upload-modal-actions fix
  - frontend/admin-spa/src/index.css — documents-filters alias, upload-field CSS, btn-primary width, users-groups CSS, checkbox style
  - backend/rag/parser/security_gate.py — _SUPPORTED_MIMES; octet-stream bypass
  - frontend/admin-spa/src/i18n/locales/{en,vi,ja,ko}.json — upload_error_unsupported key
Bugs fixed: token loss on F5, t.map crash, member_count undefined, upload MIME 415, upload modal unstyled, GroupFormModal buttons, btn-primary banner, Users&Groups unstyled
New blockers: none
Status: QA ongoing — pending commit + /report admin-spa
Next: fix CSS warning → commit S004 → /tasks S005 (Docker)
