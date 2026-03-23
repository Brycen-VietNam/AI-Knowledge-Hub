# Feature Memory: auth-api-key-oidc
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: PLANNED
Updated: 2026-03-23

---

## Summary (5 bullets max — always current)
- Auth middleware cho Knowledge-Hub: API-key (bots) + OIDC Bearer (human users) + unified `verify_token`
- 4 stories: S001 DB migration → S002 API-key → S003 OIDC (parallel) → S004 unified dependency
- Groups claim = **names (strings)** → cần DB lookup resolve sang `user_group_ids`
- **JIT user provisioning**: auto UPSERT vào `users` table khi OIDC login lần đầu
- Checklist WARN-approved (24/26 pass, 2 WARN approved). Spec updated với D06/D07/D08. Next step: `/plan auth-api-key-oidc`

## Key Decisions
| ID  | Decision | Rationale | Date |
|-----|----------|-----------|------|
| D01 | JWT `groups` claim = group **names** (strings) | Keycloak default; verify_oidc_token cần DB lookup `user_groups.name` → integer IDs | 2026-03-23 |
| D02 | User provisioning = **JIT** (auto UPSERT on first OIDC login) | Nhân viên mới không cần IT admin tạo KB account riêng; login Keycloak là dùng được | 2026-03-23 |
| D03 | JWT library = **PyJWT >= 2.8** (+ `cryptography` extra) | Nhẹ hơn python-jose; hỗ trợ RS256/ES256; stdlib SHA-256 đủ cho API-key | 2026-03-23 |
| D04 | Migration sentinel = `sub='__migration_placeholder__'` | Existing `audit_logs` rows có valid FK trước khi TEXT → UUID FK constraint được apply | 2026-03-23 |
| D05 | `X-API-Key` takes precedence khi cả hai headers present | Bot tokens là identity cụ thể hơn; tránh accidental OIDC fallback | 2026-03-23 |
| D06 | `groups` claim empty/absent → `user_group_ids=[]`, login OK (permissive) | Auth layer không enforce group membership; RBAC filter tự trả empty set | 2026-03-23 |
| D07 | JWT claim mapping configurable: `OIDC_EMAIL_CLAIM` (default `"email"`), `OIDC_NAME_CLAIM` (default `"name"`) | Tránh hardcode claim names; linh hoạt với Keycloak realm config | 2026-03-23 |
| D08 | `audit_logs` trống hoàn toàn — migration 004 đơn giản (không cần UPDATE existing rows) | Dev environment only; no production data to preserve | 2026-03-23 |
| D09 | API key creation = manual seed via SQL (admin endpoint sprint sau) | Giữ scope nhỏ; bots nhận key qua IT admin; `scripts/seed_api_key.py` helper | 2026-03-23 |

## Spec
Path: `docs/specs/auth-api-key-oidc.spec.md`
Stories: 4 | Priority: P0
Sources: `docs/sources/auth-api-key-oidc.sources.md` — 20/20 ACs traced

## Plan
Path: `docs/plans/auth-api-key-oidc.plan.md` ✅ APPROVED 2026-03-23
Critical path: S001 → S002 → S003 → S004 (auth-agent always sequential)
Groups: G1=S001(db-agent) → G2=S002→S003(auth-agent) → G3=S004(auth-agent)
Key design: AuthenticatedUser in `backend/auth/types.py` (avoids circular import)
New file: `backend/auth/_errors.py` (shared error helper for A005 compliance)

## Task Progress
Task files: `docs/tasks/auth-api-key-oidc/S001.tasks.md` — S004.tasks.md

| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| S001-T001 | S001 | TODO | db-agent | Migration 004 SQL |
| S001-T002 | S001 | TODO | db-agent | User ORM model |
| S001-T003 | S001 | TODO | db-agent | ApiKey ORM model |
| S001-T004 | S001 | TODO | db-agent | AuditLog FK update + __init__ |
| S001-T005 | S001 | TODO | db-agent | test_auth_models.py + fix test_models.py |
| S002-T001 | S002 | TODO | auth-agent | auth pkg scaffold + _errors.py |
| S002-T002 | S002 | TODO | auth-agent | verify_api_key implementation |
| S002-T003 | S002 | TODO | auth-agent | test_api_key.py |
| S003-T001 | S003 | TODO | auth-agent | Add PyJWT/cryptography/httpx to requirements.txt |
| S003-T002 | S003 | TODO | auth-agent | oidc.py env config + JWKS cache |
| S003-T003 | S003 | TODO | auth-agent | oidc.py verify_oidc_token + JIT UPSERT |
| S003-T004 | S003 | TODO | auth-agent | test_oidc.py |
| S004-T001 | S004 | TODO | auth-agent | AuthenticatedUser in types.py |
| S004-T002 | S004 | TODO | auth-agent | verify_token + get_db in dependencies.py |
| S004-T003 | S004 | TODO | auth-agent | Update __init__.py public interface |
| S004-T004 | S004 | TODO | auth-agent | test_dependencies.py + full suite |

## Files Touched
_Updated by /sync after each implement session._

## Open Questions
| # | Question | Owner | Due |
|---|----------|-------|-----|
| Q1 | RESOLVED: Groups claim = names → DB lookup (D01) | — | 2026-03-23 |
| Q2 | RESOLVED: JIT provisioning on first OIDC login (D02) | — | 2026-03-23 |
| Q3 | RESOLVED: PyJWT >= 2.8 (D03) | — | 2026-03-23 |
| Q4 | RESOLVED: Migration sentinel sub='__migration_placeholder__' (D04) | — | 2026-03-23 |
| Q5 | RESOLVED: empty groups → permissive login (D06) | — | 2026-03-23 |
| Q6 | RESOLVED: JWT claim mapping configurable via env vars (D07) | — | 2026-03-23 |
| Q7 | RESOLVED: audit_logs empty → simple migration (D08) | — | 2026-03-23 |
| Q8 | RESOLVED: API key creation = manual seed via SQL (D09) | — | 2026-03-23 |

## New Dependencies (thêm vào requirements.txt tại S003)
- `PyJWT>=2.8.0`
- `cryptography>=42.0.0`
- `httpx>=0.27.0`

## CONSTITUTION Violations Found
_None — updated by /checklist or /rules._

## Sync History
| Session | Date | Changes |
|---------|------|---------|
| #001 | 2026-03-23 | Spec created: 4 stories, 20 ACs. Decisions D01–D05 recorded via Q&A. |
| #002 | 2026-03-23 | /clarify: 4 BLOCKERs resolved (D06–D09). /checklist: WARN-approved (24/26). Spec AC updated (S001 AC1 nullable, S003 AC1 permissive groups + configurable claims). Status → PLANNING. |
| #003 | 2026-03-23 | /plan: Layer 1+2 plan generated and approved. 19 files (14 new, 5 modified). Dispatch packages ready. Status → PLANNED. |
| #004 | 2026-03-23 | /tasks: 16 atomic tasks across 4 stories (S001×5, S002×3, S003×4, S004×4). TDD enforced. Next: /analyze S001-T001 |
