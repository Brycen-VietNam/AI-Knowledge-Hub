# WARM: user-management
Created: 2026-04-21 | Status: CLARIFY COMPLETE + BLOCKERS RESOLVED → ready for /checklist

---

## Spec Summary
- 8 stories: S001–S004 backend (api-agent), S005–S008 frontend (frontend-agent)
- Critical path: S001 → S003 → S004 → S005 → S006 → S007 → S008
- Parallel-safe: S001 + S002 (backend); S006 + S007 (frontend)
- Branch: `feature/user-management` (not yet created)
- Blocked by: admin-spa (DONE ✅)

## What it does
Full user CRUD + API key lifecycle via admin UI:
- `POST /v1/admin/users` — create user (bcrypt password, optional groups)
- `DELETE /v1/admin/users/{id}` — delete user + cascade memberships + api_keys
- `POST/GET/DELETE /v1/admin/users/{id}/api-keys` — generate / list / revoke
- Frontend: `UserFormModal`, `ApiKeyPanel`, `UsersTab` wiring

## Design Decisions (locked)
| # | Decision |
|---|----------|
| D1 | `sub` = admin-typed username (not auto-generated) |
| D2 | Password: admin types or clicks "Generate" → 16-char secure, shown once |
| D3 | API keys generated per-user, flow independent of create-user |
| D4 | Service accounts use group convention ("Service Accounts") — no new column |
| D5 | API key format: `kh_<secrets.token_hex(16)>` stored as SHA-256 hash |

## Clarify Status
File: `docs/user-management/clarify/user-management.clarify.md`

### Blockers — ALL RESOLVED (2026-04-21)
| Q | Resolution |
|---|------------|
| Q1 | `api_keys` — `key_prefix TEXT`, `name TEXT` added via migration 011 |
| Q2 | `audit_logs.user_id` FK — DROP + re-add with `ON DELETE SET NULL`; column made nullable (audit trail preserved) — migration 011 |
| Q3 | `users.password_hash TEXT` — already added in migration 008 (pre-existing) |

### SHOULD defaults (assumed unless overridden)
- `user_group_ids` in `api_keys` auto-populated from user's memberships at key creation
- No limit on API keys per user
- `ApiKeyPanel` = collapsible inline section (not modal)
- Groups load before modal but modal can open with empty list (degraded)

## Files to Touch
| Story | Files |
|-------|-------|
| S001–S004 | `backend/api/routes/admin.py` + migration `011_api_keys_key_prefix_name.sql` (DONE) |
| S005 | `frontend/admin-spa/src/api/adminApi.ts` |
| S006 | `frontend/admin-spa/src/components/UserFormModal.tsx` (NEW) |
| S007 | `frontend/admin-spa/src/components/ApiKeyPanel.tsx` (NEW) |
| S008 | `frontend/admin-spa/src/components/UsersTab.tsx` |

## Open Questions
- (none — all blockers resolved)

## Deferred — Resolve in future sprint

| # | Issue | Detail |
|---|-------|--------|
| F1 | **Email notification on user create** | Khi admin tạo user, system không gửi email thông báo. Admin phải tự gửi credentials qua kênh riêng. Cần: email service integration + template + SMTP/SES config. (Xem clarify Q13) |
| F2 | **Force password change on first login** | User được tạo với admin-set password, không bị bắt đổi lần đầu login. Cần: `must_change_password BOOLEAN` column trên `users` table + middleware check + `/v1/auth/change-password` endpoint mới. |

## Phase Status
- [x] /specify — DONE (2026-04-20)
- [x] /clarify — DONE (2026-04-21)
- [x] Blockers resolved — migration 011 written (2026-04-21)
- [x] /checklist — PASS ✅ 25/25 (2026-04-21)
- [x] /plan — DONE (2026-04-21) → `docs/user-management/plan/user-management.plan.md`
- [x] /tasks — DONE (2026-04-21) → `docs/user-management/tasks/S00[1-8].tasks.md`
- [x] /implement S001–S004 — DONE ✅ (2026-04-21)
- [x] /reviewcode S001–S003 — APPROVED ✅ (2026-04-21, 0 blockers)
- [ ] /implement S005–S008 (frontend)
- [ ] /report

## Plan Summary
Critical path: S001 → S002 → S003 → S004 → S005 → S006+S007 → S008
Groups: G1(S001,S002 seq), G2(S003), G3(S004), G4(S005), G5(S006+S007 parallel), G6(S008)
Sessions: 5 (A: S001–S002, B: S003–S004, C: S005, D: S006+S007, E: S008)

---

## Sync: 2026-04-21 (session #097)
Decisions added: D-UM-01 (migration 011 schema fixes), D-UM-02 (Q3 pre-existing)
Tasks changed: clarify → DONE; blockers Q1/Q2/Q3 → RESOLVED
Files touched: `backend/db/migrations/011_api_keys_key_prefix_name.sql` (NEW), `docs/user-management/clarify/user-management.clarify.md` (updated), `WARM/user-management.mem.md` (created), `HOT.md` (updated)
Questions resolved: Q1, Q2, Q3
New blockers: none

## Sync: 2026-04-21 (session #099)
Decisions added: D-UM-05 (/tasks DONE; TDD enforced; 27 tasks generated)
Tasks changed: /tasks → DONE ✅; phase status updated; /implement next
Files created: `docs/user-management/tasks/S001.tasks.md` through `S008.tasks.md` (8 files)
Files touched: `WARM/user-management.mem.md` (phase + plan summary updated), `HOT.md` (session updated)
Questions resolved: (none)
New blockers: none (risk mitigations logged in plan)

## Sync: 2026-04-21 (security review)
Decisions added:
- D-SEC-01: Plain SHA-256 approved for API key hashing at 128-bit entropy; HMAC-SHA-256 deferred as optional future improvement
- D-SEC-02: AUTH_SECRET_KEY correctly scoped to JWT only; NOT used for password hashing (bcrypt) or API key hashing (SHA-256)
- D-SEC-03: bcrypt.gensalt(rounds=12) confirmed correct — unique 16-byte salt per call, embedded in hash output
Reviews completed: `docs/user-management/reviews/S001-S003-security.review.md` — APPROVED (0 blockers, 2 warnings)
Warnings tracked:
- W1: HMAC-SHA-256 for API keys (defense-in-depth, non-critical at 128-bit entropy) — future sprint
- W2: Missing try/except on API key INSERT commit in S003 — **FIXED** (admin.py L598–612)
Questions resolved: user concern about "muoi" (salt) for password + API key — fully addressed

## Sync: 2026-04-21 (session #104 — W2 fix)
Decisions: W2 resolved — try/except + rollback added to admin_generate_api_key
Files touched: `backend/api/routes/admin.py` (L598–612, try/except wrap)
Tasks changed: S003 W2 → FIXED ✅
New blockers: none
Next: /implement S005–S008 (frontend stories)
