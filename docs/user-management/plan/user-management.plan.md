# Plan: user-management
Generated: 2026-04-21 | Checklist: PASS ✅ 25/25 | Status: READY FOR /tasks

---

## Layer 1 — Plan Summary

```
Stories: 8 | Sessions est.: 2 | Critical path: S001 → S003 → S004 → S005 → S006 → S007 → S008
Token budget total: ~20k

Parallel groups:
  G1 (run together): S001 (api-agent), S002 (api-agent)*
  G2 (after G1):     S003 (api-agent)
  G3 (after G2):     S004 (api-agent)
  G4 (after G3):     S005 (frontend-agent)
  G5 (after G4):     S006 (frontend-agent), S007 (frontend-agent) — parallel-safe
  G6 (after G5):     S008 (frontend-agent)

* S001 + S002 touch same file (admin.py) → serialize within G1. Run S001 first, S002 after.
```

**Note on G1 parallelism:** S001 and S002 both modify `backend/api/routes/admin.py`. Per parallelization rules, two stories touching the same file cannot run concurrently. Run sequentially: S001 → S002 (both in G1 session). Frontend G5 (S006 + S007) are safe to parallelize — separate new files.

---

## Layer 2 — Per-Story Plan

---

### S001: Backend — POST /v1/admin/users (Create User)
**Agent:** api-agent | **Group:** G1 (first) | **Depends:** none
**Parallel:** sequential with S002 (same file)

**Files:**
- MODIFY: `backend/api/routes/admin.py` — add `create_user` route after `admin_list_users`

**Key logic:**
```python
@router.post("/v1/admin/users", dependencies=[Depends(require_admin)], status_code=201)
async def admin_create_user(payload: UserCreate, db=Depends(get_db), req: Request = None):
    # 1. Strip + validate sub/email/display_name
    # 2. Check duplicate sub → 409 SUB_CONFLICT
    # 3. bcrypt hash password (rounds=12)
    # 4. INSERT user row (text().bindparams)
    # 5. INSERT group memberships ON CONFLICT DO NOTHING (same transaction)
    # 6. Return 201 with user + groups
```

**Pydantic model:**
```python
class UserCreate(BaseModel):
    sub: str = Field(..., min_length=3, max_length=200, pattern=r"^[a-zA-Z0-9_.@-]+$")
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=200)
    password: str = Field(..., min_length=12)
    group_ids: List[int] = []
```

**Est. tokens:** ~3k
**Test:** `pytest tests/api/test_admin_users.py::test_create_user*`
**AC count:** 10
**Subagent dispatch:** YES (self-contained within admin.py)

---

### S002: Backend — DELETE /v1/admin/users/{user_id} (Delete User)
**Agent:** api-agent | **Group:** G1 (second, after S001) | **Depends:** S001 schema
**Parallel:** sequential with S001 (same file)

**Files:**
- MODIFY: `backend/api/routes/admin.py` — add `delete_user` route

**Key logic:**
```python
@router.delete("/v1/admin/users/{user_id}", dependencies=[Depends(require_admin)])
async def admin_delete_user(user_id: str, db=Depends(get_db), req: Request = None):
    # 1. Check user exists → 404 if not
    # 2. DELETE api_keys WHERE user_id (text().bindparams)
    # 3. DELETE user_group_memberships WHERE user_id
    # 4. DELETE users WHERE id
    # All in one transaction; rollback on error
    # 5. Return 200 {"deleted": user_id}
```

**Note:** `audit_logs.user_id` FK is `ON DELETE SET NULL` (migration 011) — no pre-delete needed.

**Est. tokens:** ~2k
**Test:** `pytest tests/api/test_admin_users.py::test_delete_user*`
**AC count:** 7
**Subagent dispatch:** YES (same subagent session as S001)

---

### S003: Backend — POST /v1/admin/users/{user_id}/api-keys (Generate API Key)
**Agent:** api-agent | **Group:** G2 | **Depends:** S001 (user must exist to generate key)
**Parallel:** sequential (depends on G1)

**Files:**
- MODIFY: `backend/api/routes/admin.py` — add `generate_api_key` route

**Key logic:**
```python
@router.post("/v1/admin/users/{user_id}/api-keys", dependencies=[Depends(require_admin)], status_code=201)
async def admin_generate_api_key(user_id: str, body: ApiKeyCreate, db=Depends(get_db), req: Request = None):
    # 1. Check user exists → 404
    # 2. plaintext = "kh_" + secrets.token_hex(16)  # 36 chars
    # 3. key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    # 4. key_prefix = plaintext[:8]
    # 5. INSERT into api_keys (key_hash, key_prefix, name, user_id, created_at)
    # 6. Return 201 {key_id, key: plaintext, key_prefix, name, created_at}
    # plaintext NEVER stored — only returned once
```

**Est. tokens:** ~2k
**Test:** `pytest tests/api/test_admin_api_keys.py::test_generate_api_key*`
**AC count:** 9
**Subagent dispatch:** YES

---

### S004: Backend — GET + DELETE /v1/admin/users/{user_id}/api-keys (List + Revoke)
**Agent:** api-agent | **Group:** G3 | **Depends:** S003 (api_keys rows must exist)
**Parallel:** sequential (depends on G2)

**Files:**
- MODIFY: `backend/api/routes/admin.py` — add `list_api_keys` + `revoke_api_key` routes

**Key logic:**
```python
# GET — never return key_hash or plaintext
@router.get("/v1/admin/users/{user_id}/api-keys", dependencies=[Depends(require_admin)])
async def admin_list_api_keys(user_id: str, db=Depends(get_db)):
    # SELECT key_id, key_prefix, name, created_at FROM api_keys WHERE user_id
    # Return {"items": [...]}

# DELETE
@router.delete("/v1/admin/users/{user_id}/api-keys/{key_id}", dependencies=[Depends(require_admin)])
async def admin_revoke_api_key(user_id: str, key_id: str, db=Depends(get_db)):
    # Check user exists → 404; check key exists → 404
    # DELETE FROM api_keys WHERE id = key_id AND user_id = user_id
    # Return 200 {"revoked": key_id}
```

**Est. tokens:** ~2k
**Test:** `pytest tests/api/test_admin_api_keys.py::test_list_api_keys* test_revoke_api_key*`
**AC count:** 7
**Subagent dispatch:** YES

---

### S005: Frontend — adminApi.ts additions
**Agent:** frontend-agent | **Group:** G4 | **Depends:** S001–S004 (backend endpoints live)
**Parallel:** sequential (depends on G3)

**Files:**
- MODIFY: `frontend/admin-spa/src/api/adminApi.ts` — add 5 new functions + 3 interfaces

**Key additions:**
```typescript
export interface UserCreatePayload { sub: string; email?: string; display_name?: string; password: string; group_ids?: number[]; }
export interface ApiKeyCreated      { key_id: string; key: string; key_prefix: string; name: string; created_at: string; }
export interface ApiKeyItem         { key_id: string; key_prefix: string; name: string; created_at: string; }

export async function createUser(payload: UserCreatePayload): Promise<UserItem> { ... }
export async function deleteUser(userId: string): Promise<void> { ... }
export async function generateApiKey(userId: string, name?: string): Promise<ApiKeyCreated> { ... }
export async function listApiKeys(userId: string): Promise<ApiKeyItem[]> { ... }
export async function revokeApiKey(userId: string, keyId: string): Promise<void> { ... }
```

**Est. tokens:** ~2k
**Test:** `tests/api/adminApi.test.ts` — mock axios, verify endpoint paths + payloads
**AC count:** 7
**Subagent dispatch:** YES

---

### S006: Frontend — UserFormModal.tsx (NEW)
**Agent:** frontend-agent | **Group:** G5 | **Depends:** S005 (uses createUser, UserCreatePayload)
**Parallel:** G5-safe (separate new file from S007)

**Files:**
- CREATE: `frontend/admin-spa/src/components/UserFormModal.tsx`

**Key logic:**
- Pattern: copy structure from `GroupFormModal.tsx`
- Fields: sub (required), email (optional), display_name (optional), password (required, min 12), groups (checkbox list)
- "Generate password" button: `crypto.getRandomValues` → 16-char alphanumeric → fill field
- Error handling: 409 → "Username already taken" inline; 422 → server message inline
- Props: `{ onSave: (user: UserItem) => void; onClose: () => void; groups: GroupItem[] }`
- i18n: all strings via `t()` — no hardcoded English

**Est. tokens:** ~3k
**Test:** `tests/components/UserFormModal.test.tsx`
**AC count:** 9
**Subagent dispatch:** YES (can parallelize with S007)

---

### S007: Frontend — ApiKeyPanel.tsx (NEW)
**Agent:** frontend-agent | **Group:** G5 | **Depends:** S005 (uses listApiKeys, generateApiKey, revokeApiKey)
**Parallel:** G5-safe (separate new file from S006)

**Files:**
- CREATE: `frontend/admin-spa/src/components/ApiKeyPanel.tsx`

**Key logic:**
- List: `key_prefix`, `name`, `created_at` — hash never shown
- Generate flow: optional name input → call generateApiKey → show plaintext in one-time dialog
- One-time dialog: copy-to-clipboard + "I've copied it" dismiss
- Revoke flow: `DeleteConfirmDialog` → `revokeApiKey` → remove from list
- Props: `{ userId: string }`
- i18n: all strings via `t()`

**Est. tokens:** ~3k
**Test:** `tests/components/ApiKeyPanel.test.tsx`
**AC count:** 8
**Subagent dispatch:** YES (can parallelize with S006)

---

### S008: Frontend — UsersTab.tsx wiring
**Agent:** frontend-agent | **Group:** G6 | **Depends:** S006 + S007 (components must exist)
**Parallel:** sequential (depends on G5)

**Files:**
- MODIFY: `frontend/admin-spa/src/components/UsersTab.tsx`

**Key additions:**
```tsx
// State
const [modalMode, setModalMode] = useState<null | 'create'>(null)
const [expandedUserId, setExpandedUserId] = useState<string | null>(null)
const [groups, setGroups] = useState<GroupItem[]>([])

// On mount: fetch groups once → pass to UserFormModal
// Toolbar: <button className="btn-primary" onClick={() => setModalMode('create')}>Create User</button>
// Per-row: <button className="btn-danger" onClick={() => confirmDelete(user.id)}>Delete</button>
// Per-row expand: toggle expandedUserId → render <ApiKeyPanel userId={user.id} />
// Modal: {modalMode === 'create' && <UserFormModal groups={groups} onSave={handleSave} onClose={close} />}
// Delete: DeleteConfirmDialog → deleteUser() → 404 error toast (no premature row remove)
```

**Regression check:** toggle-active must remain functional after wiring.

**Est. tokens:** ~3k
**Test:** `tests/components/UsersTab.test.tsx` — toolbar button, modal open/close, delete confirm, expand/collapse
**AC count:** 8
**Subagent dispatch:** YES

---

## Execution Schedule

| Session | Stories | Agent | Notes |
|---------|---------|-------|-------|
| Session A | S001, S002 | api-agent | Sequential in admin.py; complete before Session B |
| Session B | S003, S004 | api-agent | Sequential in admin.py; depends on Session A |
| Session C | S005 | frontend-agent | Typed API client; depends on Session B |
| Session D | S006 + S007 | frontend-agent | Parallel dispatch (2 subagents); depends on Session C |
| Session E | S008 | frontend-agent | Final wiring; depends on Session D |

Total sessions: 5 | Can compress Sessions A+B if api-agent handles all 4 stories sequentially.

---

## Risk Register

| Risk | Story | Mitigation |
|------|-------|------------|
| `admin.py` grows large | S001–S004 | Keep handlers thin — extract helpers to `_user_helpers.py` if file > 400 lines |
| `api_keys` schema mismatch | S003 | Migration 011 adds `key_prefix` + `name` (DONE ✅) — verify before implement |
| `DeleteConfirmDialog` props API | S007, S008 | Read existing component before copying pattern |
| Password field XSS | S006 | Always `type="password"` — never innerHTML of password value |
| Regression in toggle-active | S008 | Run existing UsersTab tests before + after |

---

## Rules Cross-check

| Rule | Relevant Stories | Requirement |
|------|-----------------|-------------|
| R001 (RBAC before retrieval) | — | N/A — admin endpoints skip user RBAC |
| R003 (Auth on every endpoint) | S001–S004 | `Depends(require_admin)` on all 5 new routes |
| R004 (API version prefix) | S001–S004 | All routes under `/v1/admin/` ✅ |
| S001 (SQL injection) | S001–S004 | `text().bindparams()` only — no f-strings |
| S003 (Input sanitization) | S001, S006 | Strip control chars; validate email; min-length password |
| S005 (Secret management) | S003 | SHA-256 hash stored; plaintext returned once, never persisted |
| A005 (Error shape) | S001–S004 | All errors: `{"error": {"code": ..., "message": ..., "request_id": ...}}` |
