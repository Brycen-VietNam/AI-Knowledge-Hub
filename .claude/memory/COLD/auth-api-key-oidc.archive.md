# Feature Archive: auth-api-key-oidc
> Archived: 2026-03-24 | Status: DONE | Report: docs/reports/auth-api-key-oidc.report.md

---

## Summary
Auth middleware for Knowledge-Hub: API-key (bots) + OIDC Bearer (human users) + unified `verify_token`.
4 stories (S001–S004), 16 tasks, 51 tests, 20/20 ACs pass. Unblocks rbac, ingestion, query sprints.

## Key Decisions (D01–D12)
| ID | Decision | Date |
|----|----------|------|
| D01 | JWT groups claim = group names (strings) → DB lookup | 2026-03-23 |
| D02 | JIT user provisioning on first OIDC login | 2026-03-23 |
| D03 | PyJWT >= 2.8 + cryptography | 2026-03-23 |
| D04 | Migration sentinel sub='__migration_placeholder__' | 2026-03-23 |
| D05 | X-API-Key takes precedence over Bearer | 2026-03-23 |
| D06 | Empty groups → permissive login (user_group_ids=[]) | 2026-03-23 |
| D07 | JWT claim mapping configurable via env vars | 2026-03-23 |
| D08 | audit_logs empty → simple migration | 2026-03-23 |
| D09 | API key creation = manual SQL seed | 2026-03-23 |
| D10 | ApiKey has no is_active; verify_api_key joins User.is_active | 2026-03-23 |
| D11 | fastapi added to requirements.txt | 2026-03-23 |
| D12 | AuthenticatedUser canonical home = backend/auth/types.py | 2026-03-23 |

## Files Created
backend/auth/__init__.py, _errors.py, api_key.py, oidc.py, types.py, dependencies.py
backend/db/migrations/004_create_users_api_keys.sql
backend/db/models/user.py, api_key.py
tests/auth/__init__.py, conftest.py, test_api_key.py, test_oidc.py, test_dependencies.py
tests/db/test_auth_models.py

## Files Modified
backend/db/models/__init__.py, audit_log.py
backend/db/session.py
requirements.txt
tests/db/test_models.py

## Dependencies Added
PyJWT>=2.8.0, cryptography>=42.0.0, httpx>=0.27.0, fastapi

## Public Interface
```python
from backend.auth import verify_token, AuthenticatedUser
# Usage: user: AuthenticatedUser = Depends(verify_token)
```
