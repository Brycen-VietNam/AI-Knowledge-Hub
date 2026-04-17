# Plan: admin-spa
Generated: 2026-04-17 | Spec: admin-spa.spec.md | Status: READY
Checklist: Skipped (all 4 BLOCKERs resolved at /clarify, WARM status=READY_FOR_PLAN)

---

## LAYER 1 — Plan Summary

Stories: 6 | Sessions est.: 4 | Critical path: S000 → S001 → S002 → S003 → S004 → S005

**Parallel groups:**
- G1 (sequential prerequisite): S000 — db-agent + api-agent (backend must land first)
- G2 (after G1): S001 — frontend-agent (login + admin gate)
- G3 (after G2, parallel-safe): S002, S003, S004 — frontend-agent (can run concurrently — different components, no shared files)
- G4 (after G3): S005 — frontend-agent (build + Docker — needs all components complete)

**Token budget total:** ~22k (6 stories × avg ~3.5k)

**Agent assignments:**
| Agent | Stories |
|-------|---------|
| db-agent | S000 (migration 009) |
| api-agent | S000 (admin.py routes + verify_token update + /v1/metrics) |
| frontend-agent | S001, S002, S003, S004, S005 |

**Key risks:**
- S000 is highest risk — touches auth core (verify_token), migration, and 3 new endpoints
- `user_group_memberships` junction table is net-new — migration must run before any verify_token change
- Write gate change (documents.py:135) must not break existing api_key flow
- S002 spec has stale AC4/AC5 (textarea → file upload per D06) — must update during /tasks
- **[NEW] 3 backend BLOCKERs identified pre-S002 — must patch before /implement S002 (see Risk Register)**

---

## LAYER 2 — Per-Story Plans

---

### S000: Backend — Admin Group Flag + Admin Endpoints
**Agent:** db-agent (migration) + api-agent (routes) | **Group:** G1 | **Depends:** none
**Sequential:** YES — all other stories block on this

**Files:**
| Op | File | Notes |
|----|------|-------|
| CREATE | `backend/db/migrations/009_add_admin_group_flag.sql` | `is_admin` col + `user_group_memberships` table |
| MODIFY | `backend/db/models/user_group.py` | Add `is_admin: Mapped[bool]` |
| MODIFY | `backend/auth/types.py` | Add `is_admin: bool = False` to `AuthenticatedUser` |
| MODIFY | `backend/auth/dependencies.py` | `verify_token` — JOIN to compute `is_admin` |
| CREATE | `backend/api/routes/admin.py` | All `/v1/admin/*` endpoints (AC4–AC12) + `GET /v1/metrics` |
| MODIFY | `backend/api/routes/documents.py` | Write gate: `api_key` OR (`jwt` AND `user.is_admin`) — AC13 |
| MODIFY | `backend/api/routes/auth.py` | Add `is_admin` to token response — AC14 |
| MODIFY | `backend/api/main.py` | Register `admin` router |
| CREATE | `tests/api/test_admin.py` | Unit tests for all admin endpoints (AC4–AC15) |

**Migration 009 content (critical):**
```sql
-- 009_add_admin_group_flag.sql
ALTER TABLE user_groups ADD COLUMN is_admin BOOL NOT NULL DEFAULT FALSE;

CREATE TABLE user_group_memberships (
  user_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id INTEGER NOT NULL REFERENCES user_groups(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, group_id)
);

-- Rollback:
-- DROP TABLE user_group_memberships;
-- ALTER TABLE user_groups DROP COLUMN is_admin;
```

**verify_token update (critical):**
```python
# dependencies.py — after user lookup
result = await db.execute(
    text("""
        SELECT BOOL_OR(ug.is_admin) as is_admin
        FROM user_group_memberships ugm
        JOIN user_groups ug ON ug.id = ugm.group_id
        WHERE ugm.user_id = :user_id
    """).bindparams(user_id=user.id)
)
user.is_admin = result.scalar() or False
```

**Admin guard dependency:**
```python
# admin.py
async def require_admin(user: AuthenticatedUser = Depends(verify_token)):
    if not user.is_admin:
        raise HTTPException(403, detail={"error": {"code": "FORBIDDEN", "message": "Admin access required"}})
    return user
```

**Est. tokens:** ~5k (largest story — auth + migration + 8 endpoints)
**Test:** `pytest tests/api/test_admin.py tests/auth/test_verify_token.py`
**Subagent dispatch:** YES — db-agent runs migration first, then api-agent takes routes

---

### S001: Admin Login + Admin Gate
**Agent:** frontend-agent | **Group:** G2 | **Depends:** S000 (is_admin in token response)

**Files:**
| Op | File | Notes |
|----|------|-------|
| CREATE | `frontend/admin-spa/` | New Vite project (D07 — separate from frontend/) |
| CREATE | `frontend/admin-spa/src/App.tsx` | Router: /login → LoginPage, /dashboard → Dashboard (protected) |
| CREATE | `frontend/admin-spa/src/store/authStore.ts` | Zustand in-memory token + is_admin state |
| CREATE | `frontend/admin-spa/src/pages/LoginPage.tsx` | Login form (reuse frontend-spa pattern) |
| CREATE | `frontend/admin-spa/src/api/authApi.ts` | `POST /v1/auth/token` call + is_admin extraction |
| CREATE | `frontend/admin-spa/src/components/LanguageSelector.tsx` | ja/en/vi/ko picker (reuse pattern from frontend-spa) |
| CREATE | `frontend/admin-spa/src/i18n/` | react-i18next setup + 4 locale files |
| CREATE | `frontend/admin-spa/src/hooks/useAdminGuard.ts` | Redirect to /login if !token || !is_admin |
| CREATE | `frontend/admin-spa/package.json` | Vite + React + Zustand + react-i18next + axios |
| CREATE | `frontend/admin-spa/vite.config.ts` | Standard Vite config |
| CREATE | `tests/admin-spa/S001.test.tsx` | Login flow + admin gate tests |

**Admin gate logic:**
```typescript
// authStore.ts
interface AuthState {
  token: string | null;
  isAdmin: boolean;
  setAuth: (token: string, isAdmin: boolean) => void;
  logout: () => void;
}
// On login: if (!isAdmin) → show "Access denied. Admin privileges required."
// If isAdmin → navigate('/dashboard')
```

**Est. tokens:** ~3k
**Test:** `npm test` — login flow, admin gate block, session expiry
**Subagent dispatch:** YES (self-contained frontend setup)

---

### S002: Document Management
**Agent:** frontend-agent | **Group:** G3 | **Depends:** S001 (auth), S000 (admin endpoints)
**Parallel-safe with:** S003, S004

**Files:**
| Op | File | Notes |
|----|------|-------|
| CREATE | `frontend/admin-spa/src/pages/DocumentsPage.tsx` | List + pagination + filter |
| CREATE | `frontend/admin-spa/src/components/DocumentTable.tsx` | Table with status badge + actions |
| CREATE | `frontend/admin-spa/src/components/UploadModal.tsx` | File input (PDF/DOCX/HTML/TXT/MD) + Title + Lang + Group |
| CREATE | `frontend/admin-spa/src/components/DeleteConfirmDialog.tsx` | Shared confirm dialog component |
| CREATE | `frontend/admin-spa/src/api/documentsApi.ts` | `GET /v1/admin/documents`, `POST /v1/documents/upload`, `DELETE /v1/admin/documents/{id}` |
| CREATE | `tests/admin-spa/S002.test.tsx` | Document list, upload, delete tests |

**IMPORTANT — Spec correction per D06 (Q3 resolved at /clarify):**
- AC4: Upload modal uses **file input** (PDF/DOCX/HTML/TXT/MD), NOT textarea
- AC5: Calls `POST /v1/documents/upload` (multipart/form-data), NOT `POST /v1/documents` (JSON)

**Backend patches required pre-S002 (identified Session #086):**
- **G1 BLOCKER** `upload.py:75` — auth gate bug: `if user.auth_type != "api_key":` chặn admin JWT → fix: `and not user.is_admin`
- **G2 BLOCKER** `upload.py:184` — response key `document_id` → chuẩn hóa về `doc_id` (D11)
- **G3 BLOCKER** `admin.py:75–117` — `GET /v1/admin/documents` thiếu filter params `status`, `lang`, `user_group_id` → thêm optional params + parameterized WHERE
- **G4 SHOULD** `upload.py` — expose `source_url` field (DB column đã có từ migration 007, chỉ cần wire form + response)

**Upload call (updated với source_url + doc_id key):**
```typescript
// documentsApi.ts
const uploadDocument = async (file: File, title?: string, lang?: string, groupId?: number, sourceUrl?: string) => {
  const form = new FormData();
  form.append('file', file);
  if (title) form.append('title', title);
  if (lang) form.append('lang', lang);
  if (groupId) form.append('user_group_id', String(groupId));
  if (sourceUrl) form.append('source_url', sourceUrl);
  return axios.post('/v1/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  // Response: { doc_id: string, status: string, source_url: string | null }
};
```

**DocumentItem interface (updated):**
```typescript
export interface DocumentItem {
  id: string; title: string; lang: string; user_group_id: number | null;
  status: 'pending' | 'processing' | 'ready' | 'error';
  created_at: string; chunk_count: number;
  source_url: string | null;  // G4: từ migration 007
}
```

**Est. tokens:** ~3.5k
**Test:** `npm test S002` — list pagination, upload modal, delete confirm
**Subagent dispatch:** YES (parallel with S003, S004)

---

### S003: User & Group Management
**Agent:** frontend-agent | **Group:** G3 | **Depends:** S001, S000
**Parallel-safe with:** S002, S004

**Files:**
| Op | File | Notes |
|----|------|-------|
| CREATE | `frontend/admin-spa/src/pages/UsersGroupsPage.tsx` | Tabs: Groups / Users |
| CREATE | `frontend/admin-spa/src/components/GroupsTab.tsx` | CRUD groups table + modals |
| CREATE | `frontend/admin-spa/src/components/UsersTab.tsx` | Users table + search + assign group |
| CREATE | `frontend/admin-spa/src/components/GroupFormModal.tsx` | Name + is_admin toggle |
| CREATE | `frontend/admin-spa/src/components/AssignGroupModal.tsx` | Multi-select groups for user |
| CREATE | `frontend/admin-spa/src/api/adminApi.ts` | All `/v1/admin/groups/*` + `/v1/admin/users/*` calls |
| CREATE | `tests/admin-spa/S003.test.tsx` | Groups CRUD, user assign, 409 handling |

**Group delete 409 handling (per Q10 assumption):**
```typescript
// GroupsTab.tsx
catch (err) {
  if (err.response?.status === 409) {
    toast.error("Cannot delete: group has active users");
  }
}
```

**Est. tokens:** ~4k (complex CRUD + multi-tab)
**Test:** `npm test S003` — group create/edit/delete, user assign/remove, search
**Subagent dispatch:** YES (parallel with S002, S004)

---

### S004: Metrics Dashboard
**Agent:** frontend-agent | **Group:** G3 | **Depends:** S001, S000 (/v1/metrics endpoint)
**Parallel-safe with:** S002, S003

**Files:**
| Op | File | Notes |
|----|------|-------|
| CREATE | `frontend/admin-spa/src/pages/DashboardPage.tsx` | Landing page after login (/dashboard) |
| CREATE | `frontend/admin-spa/src/components/MetricCards.tsx` | 4 cards: docs/users/groups/active docs |
| CREATE | `frontend/admin-spa/src/components/QueryVolumeChart.tsx` | recharts BarChart — 7-day queries |
| CREATE | `frontend/admin-spa/src/components/HealthIndicators.tsx` | DB + Backend API green/red status |
| CREATE | `frontend/admin-spa/src/api/metricsApi.ts` | `GET /v1/metrics` call |
| CREATE | `frontend/admin-spa/src/hooks/useAutoRefresh.ts` | `setInterval` 60s + cleanup |
| CREATE | `tests/admin-spa/S004.test.tsx` | Dashboard render, metrics fetch, refresh, error state |

**Auto-refresh pattern (per Q8 assumption):**
```typescript
// useAutoRefresh.ts
export function useAutoRefresh(fn: () => void, intervalMs = 60_000) {
  useEffect(() => {
    fn(); // initial load
    const id = setInterval(fn, intervalMs);
    return () => clearInterval(id);
  }, [fn, intervalMs]);
}
```

**Error fallback (AC7):**
```typescript
// DashboardPage.tsx
{metricsError && <p className="metrics-unavailable">Metrics unavailable</p>}
```

**Est. tokens:** ~3k
**Test:** `npm test S004` — dashboard render, metrics cards, chart data, auto-refresh, error state
**Subagent dispatch:** YES (parallel with S002, S003)

---

### S005: Build & Docker Packaging
**Agent:** frontend-agent | **Group:** G4 | **Depends:** S001, S002, S003, S004 (all UI complete)

**Files:**
| Op | File | Notes |
|----|------|-------|
| CREATE | `frontend/admin-spa/Dockerfile` | Multi-stage: node:20-alpine → nginx:alpine |
| CREATE | `frontend/admin-spa/nginx.conf` | SPA fallback: `try_files $uri $uri/ /index.html` |
| CREATE | `frontend/admin-spa/.env.example` | `VITE_API_BASE_URL=http://localhost:8000` |
| MODIFY | `docker-compose.yml` | Add `admin-spa` service (port 8081:80) |
| CREATE | `tests/admin-spa/S005.build.sh` | `npm run build && docker build` smoke test |

**Dockerfile pattern (reuse frontend-spa):**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**docker-compose.yml addition:**
```yaml
admin-spa:
  build:
    context: ./frontend/admin-spa
    args:
      VITE_API_BASE_URL: ${API_BASE_URL:-http://localhost:8000}
  ports:
    - "8081:80"
  depends_on:
    - api
```

**Est. tokens:** ~2k
**Test:** `npm run build` (no errors), `docker build` succeeds, `docker run -p 8081:80` serves app
**Subagent dispatch:** YES (after G3 complete)

---

## Execution Order

```
SESSION 1: S000 (db-agent + api-agent) — backend prereq
  ├── db-agent: migration 009 (is_admin col + junction table)
  └── api-agent: verify_token update + admin.py + write gate + /v1/metrics

SESSION 2: S001 (frontend-agent) — Vite project scaffold + login + admin gate
  └── frontend-agent: new frontend/admin-spa/ project

SESSION 3 (parallel dispatch): S002 + S003 + S004 (frontend-agent)
  ├── S002: Document management (file upload via POST /v1/documents/upload)
  ├── S003: User & Group management (CRUD)
  └── S004: Metrics dashboard (recharts + auto-refresh)

SESSION 4: S005 (frontend-agent) — build + Docker
  └── frontend-agent: Dockerfile + nginx + docker-compose update
```

---

## Risk Register

| Risk | Story | Mitigation |
|------|-------|------------|
| verify_token JOIN breaks existing auth | S000 | Test with api_key path + OIDC path separately — no regression |
| write gate change breaks api_key upload | S000 | Preserve `api_key OR (jwt AND is_admin)` — never `AND` only |
| S002 AC4/AC5 stale (textarea → file upload) | S002 | Fix during /tasks S002 — use D06 resolution |
| /v1/metrics aggregate query slow | S000 | Add DB index on audit_logs.timestamp; target < 1s per AC7 |
| recharts bundle size | S004 | Tree-shake — import only BarChart, XAxis, YAxis, Tooltip |
| Port 8081 conflict | S005 | Confirm host before docker run; flag in .env.example |
| **[G1] upload.py auth gate blocks admin JWT** | **S002** | **Patch upload.py:75 — `and not user.is_admin` — BEFORE /implement S002** |
| **[G2] upload.py response key `document_id` ≠ `doc_id`** | **S002** | **D11: fix upload.py:184 → `doc_id` before /implement S002** |
| **[G3] admin/documents filter params missing** | **S002** | **Patch admin.py:75–117 — add status/lang/user_group_id + WHERE before /implement S002** |
| **[G4] source_url not exposed via upload endpoint** | **S002** | **Wire upload.py form field + response; migration 007 already exists** |

---

## Spec Updates Required (before /tasks)

1. **S002 AC4** — update: "Upload modal: chọn **file** (PDF/DOCX/HTML/TXT/MD) + Title (optional, default=filename stem) + Language (optional, auto-detect) + Group (optional) + **Source URL (optional)**"
2. **S002 AC5** — update: "Upload gọi `POST /v1/documents/upload` (multipart/form-data) với JWT admin Bearer"
3. **S000 AC13** — update: "Write gate mở rộng áp dụng cho cả `POST /v1/documents/upload` (không chỉ `POST /v1/documents`)"

## Backend Pre-Patches Required (Session #086 — before /implement S002)

| ID | File | Change | Decision |
|----|------|--------|----------|
| G1 | `backend/api/routes/upload.py:75` | `and not user.is_admin` | BLOCKER |
| G2 | `backend/api/routes/upload.py:184` | `"document_id"` → `"doc_id"` | D11 |
| G3 | `backend/api/routes/admin.py:75–117` | Add `status`, `lang`, `user_group_id` filter params + dynamic WHERE | BLOCKER |
| G4 | `backend/api/routes/upload.py` | Nhận `source_url` Form field, lưu vào doc, trả về response | SHOULD |

> `source_url` column đã có từ migration 007 (`ALTER TABLE documents ADD COLUMN source_url TEXT`) — không cần migration mới.
