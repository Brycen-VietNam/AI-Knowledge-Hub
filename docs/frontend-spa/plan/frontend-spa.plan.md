# Plan: frontend-spa
Generated: 2026-04-16 | Spec: v1 DRAFT | Checklist: ✅ PASS (WARN approved)
Stories: 6 | ACs: 45 | Critical path: S000 → S001 → S002 → S003 → S004 → S005

---

## LAYER 1 — Plan Summary

| Field | Value |
|-------|-------|
| Stories | 6 (S000–S005) |
| Sessions est. | 3 |
| Critical path | S000 → S001 → S002 → S003 |
| Token budget total | ~22k |
| Agents | api-agent (S000), frontend-agent (S001–S005) |

### Parallel Groups

```
G1 (sequential, api-agent):   S000 — Backend auth endpoint
                                ↓ [integration gate: S000 deployed + smoke test]
G2 (sequential, frontend):    S001 — Login/logout
                                ↓
G3 (sequential, frontend):    S002 — Query page + language selector
                                ↓
G4 (parallel, frontend):      S003 — Results display
                               S004 — Query history (parallel-safe with S003)
                                ↓
G5 (sequential, frontend):    S005 — Build + Docker
```

**Why sequential G1→G2?** S001 unit tests mock /v1/auth/token contract. Integration tests require S000 deployed. WARN approved: contract-based mocking is the mitigation.

**Why G4 parallel?** S003 (results panel) and S004 (history sidebar) touch different component files. No shared file writes. Both depend only on S002 state shape (query store).

---

## LAYER 2 — Per-Story Plans

---

### S000: Backend — Username/Password Auth Endpoint
**Agent:** api-agent | **Group:** G1 | **Depends:** none
**Subagent dispatch:** YES — self-contained backend story, no frontend files touched

**Files:**
```
CREATE:  backend/api/routes/auth.py
CREATE:  backend/db/migrations/008_add_password_hash.sql
MODIFY:  backend/auth/dependencies.py       — dual-mode verify_token (HS256 + RS256/ES256)
MODIFY:  backend/api/main.py                — register auth router
MODIFY:  .env.example                       — add AUTH_SECRET_KEY, AUTH_TOKEN_EXPIRE_MINUTES
MODIFY:  backend/auth/__init__.py           — export updated verify_token (if needed)
```

**Key logic:**
```python
# backend/api/routes/auth.py
POST /v1/auth/token
  → bcrypt verify (passlib CryptContext)
  → jwt.encode({"sub": username, "user_id": id, "exp": now+expire}, AUTH_SECRET_KEY, "HS256")
  → return {"access_token": token, "token_type": "bearer", "expires_in": seconds}
  → rate_limit: 10 req/min per IP (SlowAPI + Valkey)
  → on failure: uniform 401 AUTH_FAILED (no username enumeration)
  → audit_log: AUTH_FAILED events (no password logged)

# backend/db/migrations/008_add_password_hash.sql
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
-- Rollback: ALTER TABLE users DROP COLUMN password_hash;

# backend/auth/dependencies.py — verify_token update
  try HS256 (local JWT, AUTH_SECRET_KEY)
  fallback RS256/ES256 (OIDC, existing oidc.py path)
  raise 401 if both fail
```

**Constraints (HARD rules):**
- R003: /v1/auth/token is explicitly public (exception, like /v1/health)
- R004: route prefix must be /v1/auth/token
- S001 (SECURITY.md): no SQL interpolation in user lookup
- S004 (SECURITY.md): rate limit 10 req/min per IP

**Est. tokens:** ~4k
**Test:** `pytest tests/api/test_auth.py -v`
**Integration gate:** `curl -X POST http://localhost:8000/v1/auth/token -d '{"username":"test","password":"test"}' → 401` before G2 starts

---

### S001: Authentication — Login / Logout
**Agent:** frontend-agent | **Group:** G2 | **Depends:** S000 (contract locked; unit tests mock)
**Subagent dispatch:** YES — frontend-only, no backend files touched

**Files:**
```
CREATE:  frontend/src/pages/LoginPage.tsx
CREATE:  frontend/src/store/authStore.ts      — Zustand, in-memory JWT only
CREATE:  frontend/src/api/client.ts           — Axios instance + interceptors
CREATE:  frontend/src/components/auth/LoginForm.tsx
MODIFY:  frontend/src/App.tsx                 — add ProtectedRoute + Router setup
MODIFY:  frontend/src/main.tsx                — wrap with providers
```

**Key logic:**
```tsx
// authStore.ts (Zustand)
{ token: string|null, login(t), logout() }
// NO localStorage for token — memory only

// client.ts (Axios)
interceptors.request → attach Authorization: Bearer <token>
interceptors.response → on 401: store.logout() + navigate("/login")

// Proactive refresh (D011): 
  decode JWT exp from token (no verify — just read exp)
  setInterval: if (exp - now < 5min) → call /v1/auth/token again with stored credentials
  Note: store credentials temporarily in authStore for refresh only; clear on logout

// LoginPage.tsx
  POST /v1/auth/token → store token in authStore
  on 401: show "Invalid username or password" (no detail from backend)
  on network error: show "Service unavailable"

// ProtectedRoute: if !token → <Navigate to="/login" />
```

**i18n strings needed (all 4 locales):**
- login.username, login.password, login.submit, login.error_invalid, login.error_unavailable, login.session_expired

**Est. tokens:** ~4k
**Test:** `npm run test -- src/store/authStore.test.ts src/api/client.test.ts src/pages/LoginPage.test.tsx`

---

### S002: Query Page — Search Input & Language Selector
**Agent:** frontend-agent | **Group:** G3 | **Depends:** S001
**Subagent dispatch:** YES

**Files:**
```
CREATE:  frontend/src/pages/QueryPage.tsx
CREATE:  frontend/src/store/queryStore.ts     — query state + history
CREATE:  frontend/src/components/query/SearchInput.tsx
CREATE:  frontend/src/components/query/LanguageSelector.tsx
CREATE:  frontend/src/i18n/index.ts           — react-i18next setup
CREATE:  frontend/src/i18n/locales/ja.json
CREATE:  frontend/src/i18n/locales/en.json
CREATE:  frontend/src/i18n/locales/vi.json
CREATE:  frontend/src/i18n/locales/ko.json
MODIFY:  frontend/src/App.tsx                 — add /query route
MODIFY:  frontend/package.json               — add react-i18next, i18next
```

**Key logic:**
```tsx
// LanguageSelector.tsx
  options: [{value:"ja", label:"日本語"}, {value:"en", label:"English"},
            {value:"vi", label:"Tiếng Việt"}, {value:"ko", label:"한국어"}]
  onChange: i18n.changeLanguage(lang) + localStorage.setItem("lang", lang)
  init: localStorage.getItem("lang") || navigator.language.split("-")[0] || "en"

// SearchInput.tsx
  maxLength: 512 (AC7) — character counter display
  disable submit: input.trim() === "" || input.length > 512
  loading state: disable input + button when isLoading
  IME: onKeyDown check e.nativeEvent.isComposing → block Enter submit during composition (Q8)

// Language detect order (S002 impl notes):
  localStorage("lang") → navigator.language prefix → "en"
```

**i18n keys (all 4 locales):**
- search.placeholder, search.button, search.char_count, lang.selector_label

**Est. tokens:** ~4k
**Test:** `npm run test -- src/components/query/ src/i18n/`

---

### S003: Query Results — Answer + Citations Display
**Agent:** frontend-agent | **Group:** G4 | **Depends:** S002 | **Parallel-safe with:** S004
**Subagent dispatch:** YES

**Files:**
```
CREATE:  frontend/src/components/results/AnswerPanel.tsx
CREATE:  frontend/src/components/results/CitationList.tsx
CREATE:  frontend/src/components/results/CitationItem.tsx
CREATE:  frontend/src/components/results/ConfidenceBadge.tsx
CREATE:  frontend/src/components/results/LowConfidenceWarning.tsx
MODIFY:  frontend/src/pages/QueryPage.tsx     — integrate results panel
MODIFY:  frontend/package.json               — add react-markdown
```

**Key logic:**
```tsx
// ConfidenceBadge.tsx
  score >= 0.7  → badge "HIGH"   (green)
  score >= 0.4  → badge "MEDIUM" (yellow)
  score <  0.4  → badge "LOW"    (red) + trigger LowConfidenceWarning

// CitationList.tsx
  citations.length > 3 → default collapsed (show "Show X more")
  each item: title + score formatted as "91%" (D012) + chunk preview

// AnswerPanel.tsx
  <ReactMarkdown>{answer}</ReactMarkdown>
  citations empty + answer empty → "No relevant documents found" (AC6)
  citations empty + answer present → show answer + warning "No source documents" (Q9 SHOULD default)

// API call (in queryStore):
  POST /v1/query {query, lang: "auto"} + Bearer header (via Axios interceptor)
  on 429: show "Rate limit exceeded, please wait"
  on 401: Axios interceptor handles (redirect to login)
  on 5xx: show "Service error, please try again"
```

**i18n keys:** results.no_results, results.low_confidence_warning, results.show_more, results.hide, results.error_rate_limit, results.error_service

**Est. tokens:** ~4k
**Test:** `npm run test -- src/components/results/`

---

### S004: Query History — Session-level
**Agent:** frontend-agent | **Group:** G4 | **Depends:** S002 | **Parallel-safe with:** S003
**Subagent dispatch:** YES

**Files:**
```
CREATE:  frontend/src/components/history/HistoryPanel.tsx
CREATE:  frontend/src/components/history/HistoryItem.tsx
MODIFY:  frontend/src/store/queryStore.ts     — add history[] to store
MODIFY:  frontend/src/pages/QueryPage.tsx     — integrate history sidebar
```

**Key logic:**
```tsx
// queryStore.ts addition
  history: QueryHistoryItem[]  (max 20, in-memory)
  addHistory(query, answer, citations): history.unshift({...}) — newest first, cap at 20
  clearHistory(): history = []
  selectHistory(item): restore query + answer + citations into current state

// HistoryItem.tsx
  display: truncate at 60 chars (CJK-safe)
  CJK truncation: [...str].slice(0, 60).join("") — NOT str.slice(0, 60)
  show: query text + timestamp (HH:mm format)

// HistoryPanel.tsx
  hidden when history.length === 0 (Q10 SHOULD default)
  on logout: queryStore.clearHistory() called from authStore logout action

// Layout: sidebar left OR collapsible panel — exact layout TBD in /tasks
```

**i18n keys:** history.title, history.empty (not shown — panel hidden), history.clear

**Est. tokens:** ~2k
**Test:** `npm run test -- src/store/queryStore.test.ts src/components/history/`

---

### S005: Build & Docker Packaging
**Agent:** frontend-agent | **Group:** G5 | **Depends:** S003 + S004 (all features complete)
**Subagent dispatch:** YES

**Files:**
```
CREATE:  frontend/Dockerfile
CREATE:  frontend/nginx.conf
CREATE:  frontend/.env.example
MODIFY:  frontend/vite.config.ts             — ensure VITE_ env vars exposed
MODIFY:  docker-compose.yml                  — add frontend-spa service (port 8080:80)
```

**Key logic:**
```dockerfile
# Dockerfile (multi-stage)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```nginx
# nginx.conf (SPA fallback)
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;
  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

```yaml
# docker-compose.yml addition
  frontend-spa:
    build: ./frontend
    ports:
      - "8080:80"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - app
```

```
# .env.example
VITE_API_BASE_URL=http://localhost:8000
```

**Est. tokens:** ~2k
**Test:** `npm run build && docker build -t frontend-spa . && docker run -p 8080:80 -e VITE_API_BASE_URL=http://localhost:8000 frontend-spa`

---

## Dispatch Sequence

```
[G1] api-agent         → S000 (backend auth endpoint)
      ↓ smoke test: POST /v1/auth/token returns 401 for bad creds ✓
[G2] frontend-agent    → S001 (login/logout)
      ↓
[G3] frontend-agent    → S002 (query page + i18n)
      ↓
[G4] frontend-agent    → S003 + S004 (parallel: results + history)
      ↓
[G5] frontend-agent    → S005 (build + docker)
```

## Token Budget Breakdown

| Story | Agent | Est. tokens |
|-------|-------|-------------|
| S000 | api-agent | ~4k |
| S001 | frontend-agent | ~4k |
| S002 | frontend-agent | ~4k |
| S003 | frontend-agent | ~4k |
| S004 | frontend-agent | ~2k |
| S005 | frontend-agent | ~2k |
| **Total** | | **~20k** |

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| S001 mocks diverge from S000 contract | Contract-based mocks; integration test gate after S000 deployed |
| Proactive token refresh (D011) needs credential re-storage | Store credentials in authStore during session only; clear on logout; no persistence |
| IME composition blocking Enter (Q8) — browser inconsistency | Use `e.nativeEvent.isComposing` (standard) + test on Chrome/Firefox |
| CJK truncation in S004 — emoji/surrogate pairs | Use `Intl.Segmenter` as preferred; `[...str]` as fallback |
| Docker image size > 50MB | nginx:alpine is ~23MB base; dist/ static typically <5MB — target met |
