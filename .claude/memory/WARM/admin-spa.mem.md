# Feature Memory: admin-spa
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: S001_COMPLETE
Updated: 2026-04-17

---

## Summary (5 bullets max — always current)
- Internal React/Vite SPA for admin users — deploy riêng với frontend-spa
- Admin gate: user thuộc group có `is_admin=true` (user_groups.is_admin — migration 009)
- 6 stories: S000 backend prereq, S001 login, S002 doc management, S003 user/group CRUD, S004 metrics, S005 docker
- Write gate mở rộng: api_key OR (jwt AND is_admin) — thay đổi D09 từ document-ingestion
- 50 ACs total | 4 open assumptions cần /clarify trước /plan

## Key Decisions
| ID  | Decision | Rationale | Date |
|-----|----------|-----------|------|
| D01 | Admin gate = is_admin flag on user_groups (not on users) | User muốn dùng group concept sẵn có | 2026-04-17 |
| D02 | JWT in-memory only (not localStorage) — inherit from frontend-spa D02 | OWASP XSS prevention | 2026-04-17 |
| D03 | UI language ja/en/vi/ko, persist localStorage — inherit from frontend-spa D03 | Consistency across SPAs | 2026-04-17 |
| D04 | Write gate: api_key OR (jwt AND is_admin) — extend document-ingestion D09 | Admin needs to upload docs via UI | 2026-04-17 |
| D05 | Docker port: 8081:80 — extend frontend-spa D13 | Avoid conflict: 8000/8080/3000 taken | 2026-04-17 |
| D06 | Upload = file upload (multipart) — `POST /v1/documents/upload` — PDF/DOCX/HTML/TXT/MD | Đáp ứng đủ formats backend hỗ trợ (ParserFactory) — resolved Q3 at /clarify | 2026-04-17 |
| D07 | admin-spa at frontend/admin-spa/ (separate Vite project) | Assumption confirmed — separate project | 2026-04-17 |
| D08 | users→groups: junction table `user_group_memberships(user_id, group_id)` | Normalized approach — resolved Q1 at /clarify | 2026-04-17 |
| D09 | `/v1/metrics` — implement in S000 (api-agent), admin-only | NOT found in codebase — resolved Q2 at /clarify | 2026-04-17 |
| D10 | `PUT /v1/admin/users/{id}` (is_active toggle) — include in S000 scope | Simple endpoint, same file/agent — resolved Q4 at /clarify | 2026-04-17 |

## Spec
Path: `docs/admin-spa/spec/admin-spa.spec.md`
Stories: 6 | Priority: P1
Sources: `docs/admin-spa/sources/admin-spa.sources.md`

## Plan
Path: `docs/admin-spa/plan/admin-spa.plan.md` ✅ CREATED 2026-04-17
Critical path: S000 → S001 → S002 → S003 → S004 → S005
Parallel group G3: S002 + S003 + S004 (after S001)

## Task Progress
| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| T001–T012 | S000 | REVIEWED ✅ | db-agent + api-agent | All 12 tasks DONE + /reviewcode S001 DONE, warnings fixed |
| T001–T008 | S001 | DONE ✅ | frontend-agent | 35/35 tests pass — Login + admin gate complete |
| T001–T006 | S002 | TODO | frontend-agent | Tasks created ✅ — 6 tasks, G1[T001,T002,T003,T005] → G2[T004] → G3[T006] |
| — | S003 | TODO | frontend-agent | Depends S000 admin endpoints |
| — | S004 | TODO | frontend-agent | Depends /v1/metrics existence |
| — | S005 | TODO | frontend-agent | Reuse frontend-spa S005 pattern |

## Parallel Groups (from /plan)
- G1: S000 (sequential — all block on this)
- G2: S001 (after G1)
- G3: S002, S003, S004 (parallel — after G2)
- G4: S005 (after G3)

## Files Touched
**S000 (Session #083):**
- `backend/db/migrations/009_add_admin_group_flag.sql` — created
- `backend/db/models/models.py` — UserGroup.is_admin added
- `backend/auth/types.py` — AuthenticatedUser.is_admin added
- `backend/auth/dependencies.py` — _compute_is_admin helper + verify_token updated
- `backend/api/routes/admin.py` — created (all admin endpoints)
- `backend/api/routes/documents.py` — write gate expanded
- `backend/api/routes/auth.py` — is_admin in token response
- `backend/api/app.py` — admin router registered
- `tests/api/test_admin.py` — created (24 tests)
- `tests/auth/test_dependencies.py` — updated
- `tests/api/test_auth.py` — updated
- `tests/api/test_documents_management.py` — updated
- `docs/admin-spa/tasks/S000.tasks.md` — created

**S000 Review (Session #084):**
- `backend/api/routes/admin.py` — Fix1: HTTPException moved to top import, raise_403 dead var removed; Fix2: f-string SQL → 3 static SQL strings in admin_update_group
- `backend/api/routes/documents.py` — Fix3: AuditLog import added; R006 gap fixed in delete_document (AuditLog in same tx before commit)
- `docs/admin-spa/reviews/S000-S001.review.md` — created

## Open Questions
_None — all BLOCKERs resolved at /clarify._

## Clarify
Path: `docs/admin-spa/clarify/admin-spa.clarify.md`
Status: COMPLETE — 4 BLOCKERs ✅, 6 SHOULDs (assumed), 4 NICEs (deferred)

## CONSTITUTION Violations Found
_None — spec follows C001–C016, R001–R007._

---

## Sync: 2026-04-17 (Session #081)
Decisions added: D01–D07
Tasks changed: none (all TODO — pre-/clarify)
Files touched: docs/admin-spa/spec/admin-spa.spec.md, docs/admin-spa/sources/admin-spa.sources.md, .claude/memory/WARM/admin-spa.mem.md, .claude/memory/HOT.md
Questions resolved: none (Q1–Q5 pending /clarify)
New blockers: none

## Sync: 2026-04-17 (Session #082 — /clarify complete)
Decisions added: D08 (junction table), D06 (file upload), D09 (/v1/metrics→S000), D10 (PUT users/{id}→S000)
Tasks changed: none (all TODO — pre-/plan)
Files touched: docs/admin-spa/clarify/admin-spa.clarify.md, .claude/memory/WARM/admin-spa.mem.md, .claude/memory/HOT.md
Questions resolved: Q1 ✅ Q2 ✅ Q3 ✅ Q4 ✅ Q5 ✅ (all BLOCKERs cleared)
New blockers: none
Spec impact noted: S002 AC4/AC5 need update (textarea→file input, POST /v1/documents→/v1/documents/upload); S000 AC13 must cover /v1/documents/upload too

## Backend Gaps Identified (must fix before frontend S001–S005)
- ~~`user_groups.is_admin` column missing — migration 009 required (S000 AC1)~~ **DONE in S000**

## Sync: 2026-04-17 (Session #083 — S000 IMPLEMENT COMPLETE)
Decisions added: none new (impl confirmed D01–D10)
Tasks changed: S000 TODO → DONE (T001–T012 all DONE)
Files touched: see "Files Touched" section above
Questions resolved: n/a
New blockers: none
Test result: 452 passed / 12 skipped / 0 failed (full suite clean)
- `AuthenticatedUser.is_admin` field missing — types.py update (S000 AC2)
- `/v1/admin/*` endpoints not exist — new router admin.py (S000 AC4–AC12)
- `/v1/auth/token` response missing `is_admin` field (S000 AC14)
- Write gate in documents.py:135 hardcoded to `api_key` — needs update (S000 AC13)

## Spec Updates Required (flagged in /plan — apply at /tasks S002)
- S002 AC4: textarea → file input (PDF/DOCX/HTML/TXT/MD)
- S002 AC5: POST /v1/documents → POST /v1/documents/upload (multipart/form-data)
- S000 AC13: write gate covers both POST /v1/documents AND POST /v1/documents/upload

## Sync: 2026-04-17 (Session #083 — /plan complete)
Decisions added: none (D01–D10 already locked)
Tasks changed: none (all TODO — pre-/tasks)
Files touched: docs/admin-spa/plan/admin-spa.plan.md (CREATED), .claude/memory/WARM/admin-spa.mem.md, .claude/memory/HOT.md
Questions resolved: none
New blockers: none

## Sync: 2026-04-17 (Session #084 — /reviewcode S001 + fixes)
Decisions added: none new (D01–D10 locked)
Tasks changed: S000 DONE → REVIEWED ✅
Files touched:
  - backend/api/routes/admin.py (Fix1: dead var + import; Fix2: f-string SQL → static)
  - backend/api/routes/documents.py (Fix3: R006 AuditLog gap)
  - docs/admin-spa/reviews/S000-S001.review.md (CREATED)
  - .claude/memory/HOT.md, .claude/memory/WARM/admin-spa.mem.md
Questions resolved: none
New blockers: none

## Backend Gaps Pre-S002 — Analysis 2026-04-17 (Session #086)

### G1 — Auth gate bug: upload.py:75 dùng api_key-only, CHẶN admin JWT ❌
**File:** `backend/api/routes/upload.py:75`
**Code hiện tại:** `if user.auth_type != "api_key":` → 403 cho MỌI JWT kể cả admin
**So với documents.py (đã fix S000):** `if user.auth_type != "api_key" and not user.is_admin:` ✅
**Fix:** Thêm `and not user.is_admin` vào upload.py:75
**Priority:** BLOCKER trước /implement S002

### G2 — Response key mismatch: upload.py vs documents.py ❌
**upload.py:184:** `{"document_id": ..., "status": "processing"}` — key = `document_id`
**documents.py:182:** `{"doc_id": ..., "status": "processing"}` — key = `doc_id`
**Quyết định D11:** Chuẩn hóa về `doc_id`. Fix upload.py:184 → `"doc_id"`.
**Priority:** BLOCKER trước /implement S002 (documentsApi.ts phải map đúng key)

### G3 — Filter params thiếu trên GET /v1/admin/documents ❌
**File:** `backend/api/routes/admin.py:75–117`
**Hiện tại:** chỉ `limit` + `offset` — không WHERE filter
**AC3 yêu cầu:** filter by status, lang, user_group_id
**Fix:** Thêm optional params `status: str | None`, `lang: str | None`, `user_group_id: int | None`
**SQL pattern (S001-compliant, no f-string):** build condition list + `text().bindparams()`
**Priority:** BLOCKER trước /implement S002

### G4 — source_url field: ĐÃ CÓ SẴN ✅ (migration 007, không cần migration mới)
**Đã có:**
- `backend/db/migrations/007_add_source_url.sql` — `ALTER TABLE documents ADD COLUMN source_url TEXT`
- `backend/db/models/document.py:26` — `source_url: Mapped[str | None] = mapped_column(Text, nullable=True)`
**Còn thiếu:** upload.py chưa nhận `source_url` form field + chưa lưu vào Document + chưa trả về response
**Fix cần làm:**
1. `upload.py`: thêm `source_url: str | None = Form(default=None)` param
2. `upload.py`: `doc = Document(..., source_url=source_url)` khi INSERT
3. `upload.py`: response thêm `"source_url": str(doc.source_url) or None`
4. `UploadModal.tsx` T004: thêm `<input type="url" name="source_url">` (optional)
5. `documentsApi.ts` T001: `uploadDocument(..., sourceUrl?)`, `DocumentItem.source_url: string | null`
**Priority:** SHOULD — thêm vào S002 scope, không blocker

### Fix Summary — Cần patch trước /implement S002

| Gap | File | Fix | Priority |
|-----|------|-----|----------|
| G1 Auth gate | `backend/api/routes/upload.py:75` | `and not user.is_admin` | BLOCKER |
| G2 Key mismatch | `backend/api/routes/upload.py:184` | `document_id` → `doc_id` | BLOCKER |
| G3 Filter missing | `backend/api/routes/admin.py:75–117` | status/lang/user_group_id params + WHERE | BLOCKER |
| G4 source_url | `upload.py` form + response + frontend T001/T004 | Expose existing DB field | SHOULD |

---

## Sync: 2026-04-17 (Session #085 — S001 /implement complete)
Decisions added:
  - 401 interceptor bỏ qua `/v1/auth/token` URL → tránh false session-expired khi login fail
  - vite.config.ts dùng `fileURLToPath(new URL(...))` cho setupFiles — isolate khỏi parent frontend/
  - i18n localStorage key = `admin-spa-lang` (không conflict với `lang` của frontend-spa)
Tasks changed: S001 T001–T008 TODO → DONE ✅ (35/35 tests pass)
Files touched:
  - frontend/admin-spa/package.json (CREATED)
  - frontend/admin-spa/vite.config.ts (CREATED)
  - frontend/admin-spa/tsconfig.json (CREATED)
  - frontend/admin-spa/index.html (CREATED)
  - frontend/admin-spa/src/main.tsx (CREATED)
  - frontend/admin-spa/src/vite-env.d.ts (CREATED)
  - frontend/admin-spa/src/index.css (CREATED — design tokens same as frontend-spa)
  - frontend/admin-spa/src/App.tsx (CREATED)
  - frontend/admin-spa/src/store/authStore.ts (CREATED — isAdmin + sessionExpiredMessage)
  - frontend/admin-spa/src/api/client.ts (CREATED — 401 skip auth endpoint)
  - frontend/admin-spa/src/i18n/index.ts (CREATED — key: admin-spa-lang)
  - frontend/admin-spa/src/i18n/locales/{en,ja,vi,ko}.json (CREATED)
  - frontend/admin-spa/src/components/auth/LoginForm.tsx (CREATED — is_admin gate)
  - frontend/admin-spa/src/components/auth/ProtectedRoute.tsx (CREATED — !token||!isAdmin)
  - frontend/admin-spa/src/components/LanguageSelector.tsx (CREATED)
  - frontend/admin-spa/src/hooks/useAdminGuard.ts (CREATED)
  - frontend/admin-spa/src/pages/LoginPage.tsx (CREATED — sessionExpiredMessage banner)
  - frontend/admin-spa/src/pages/DashboardPage.tsx (CREATED — placeholder)
  - frontend/admin-spa/tests/* (CREATED — 7 test files, 35 tests)
  - docs/admin-spa/tasks/S001.tasks.md (T001–T008 → DONE)
Test result: 35/35 PASS
New blockers: none
