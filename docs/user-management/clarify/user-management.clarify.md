# Clarify: user-management
Generated: 2026-04-21 | Spec: v1 DRAFT | Stories: S001–S008 | **BLOCKERS RESOLVED 2026-04-21**

---

## BLOCKER — Must answer before /plan

| # | Story | Question | Answer | Owner | Due |
|---|-------|----------|--------|-------|-----|
| Q1 | S003 | `api_keys` missing `key_prefix TEXT`, `name TEXT` columns | ✅ **FIXED** — migration 011 adds both columns | Dev | 2026-04-21 |
| Q2 | S002 | `audit_logs.user_id` FK ON DELETE strategy — RESTRICT blocks user delete | ✅ **FIXED** — migration 011: DROP + re-add FK with `ON DELETE SET NULL`; `user_id` made nullable (preserves audit trail) | Dev | 2026-04-21 |
| Q3 | S001 | `users` missing `password_hash TEXT` column | ✅ **ALREADY FIXED** — migration 008 added `password_hash TEXT` (nullable) | — | — |

---

## SHOULD — Assume if unanswered by sprint start

| # | Story | Question | Default assumption |
|---|-------|----------|--------------------|
| Q4 | S003 | `api_keys` currently has `user_group_ids INTEGER[]` baked at creation (auth-agent pattern). S003 spec says generate key for a user — should `user_group_ids` be auto-populated from user's current group memberships at key creation time? | Yes — copy user's current `user_group_memberships` into `user_group_ids` at INSERT |
| Q5 | S003/S004 | Is there a limit on number of API keys per user? | No limit in spec — default: unlimited |
| Q6 | S006 | Password "show" toggle (eye icon) — does spec require it, or is "Generate password" (one-time reveal) sufficient? | Generate button is sufficient; no toggle required (spec says "type=password always unless show") |
| Q7 | S006 | `listGroups()` is called from `UsersTab` and passed to `UserFormModal`. If group fetch fails, should modal open with empty group list (degraded) or block open? | Open with empty list (degraded) — group assignment is optional |
| Q8 | S007/S008 | How is `ApiKeyPanel` embedded in `UsersTab`? Expanded row (inline below row) or modal/drawer? | Collapsible inline row — spec says "expanded row or collapsible section per user" — default to collapsible section |
| Q9 | S008 | Should "Create User" button be disabled when groups are still loading? | No — group assignment is optional; form can open before groups load |

---

## NICE — Won't block

| # | Story | Question |
|---|-------|----------|
| Q10 | S006 | Should password field have a strength indicator? |
| Q11 | S007 | Should `ApiKeyPanel` show `last_used_at` (available in `api_keys` table)? |
| Q12 | S008 | Toast placement / duration for delete-404 error — match existing pattern or customizable? |
| Q13 | S001 | Should admin creating a user also receive an email notification (or any webhook event)? |

---

## Auto-answered from existing files

| Q | Source | Answer |
|---|--------|--------|
| "Must all /v1/admin/* routes use `require_admin`?" | HARD.md R003 + CONSTITUTION.md C003 | Yes — `require_admin` wraps `verify_token`; confirmed in `admin.py:35–54` |
| "Error shape for 403/404/409/422?" | ARCH.md A005 + `admin.py:26–28` | `{"error": {"code": "...", "message": "...", "request_id": "..."}}` — `_error()` helper already exists |
| "SQL injection prevention method?" | SECURITY.md S001 / HARD.md R007 | `text().bindparams()` only — confirmed as project-wide constraint |
| "bcrypt rounds?" | Spec S001 AC4 | `rounds=12` (~200ms, acceptable for latency SLA of 500ms p95) |
| "API key format?" | Spec D5 | `kh_<secrets.token_hex(16)>` → 36 chars; stored as SHA-256 hash |
| "API key plaintext exposure policy?" | HARD.md S005 + CONSTITUTION.md C002 | Returned once in response, never stored — confirmed |
| "password_hash nullable for OIDC?" | Spec OIDC Future-Proofing note | Yes — column should be nullable (migration 008 referenced in spec) |
| "i18n for frontend strings?" | CONSTITUTION.md (Language in Code) | All user-facing strings via `t()` — no hardcoded English in JSX |
| "audit_logs FK ON DELETE behavior?" | migration 004 line 46–48 | FK added with `NOT VALID` then `VALIDATE` — **no ON DELETE rule** → defaults to RESTRICT → **BLOCKER Q2** |
| "`api_keys` table schema columns?" | migration 004 lines 30–37 | Columns: `id`, `user_id`, `key_hash`, `user_group_ids`, `last_used_at`, `created_at` — **no `key_prefix` or `name`** → **BLOCKER Q1** |
| "`users` table schema columns?" | migration 004 lines 14–21 | Columns: `id`, `sub`, `email`, `display_name`, `is_active`, `created_at` — **no `password_hash`** → **BLOCKER Q3** |

---

## Summary
**3 blockers** (Q1–Q3 — schema gaps requiring new migration before backend stories can start)
**10 auto-answered** from existing files
**6 SHOULD assumptions** (safe to default)
**4 NICE** (post-launch polish)

### Critical Path Impact
All 3 blockers are schema issues resolvable with a single migration file (e.g., `009_user_management_schema.sql`):
1. `ALTER TABLE users ADD COLUMN password_hash TEXT;` (nullable — OIDC-ready)
2. `ALTER TABLE api_keys ADD COLUMN key_prefix TEXT;`
3. `ALTER TABLE api_keys ADD COLUMN name TEXT;`

Once PO/Dev confirms ON DELETE strategy for `audit_logs.user_id` FK (Q2), the migration can be written before `/plan` begins.
