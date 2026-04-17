# Sources Traceability: frontend-spa
Created: 2026-04-16 | Feature spec: `docs/frontend-spa/spec/frontend-spa.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source.
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### S000: Backend — Username/Password Auth Endpoint

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: POST /v1/auth/token | Conversation | lb_mui 2026-04-16 | Endpoint chưa tồn tại — cần tạo mới | 2026-04-16 |
| AC2: password_hash column | Business logic | Password storage standard | bcrypt hash, migration required per C010 | 2026-04-16 |
| AC3: bcrypt verify | Business logic | OWASP password storage cheat sheet | passlib[bcrypt], no plain/MD5/SHA1 | 2026-04-16 |
| AC4: JWT HS256 | Business logic | Internal JWT issuer pattern | AUTH_SECRET_KEY env var, ≥32 bytes | 2026-04-16 |
| AC5: Expiry configurable | Business logic | Ops flexibility | AUTH_TOKEN_EXPIRE_MINUTES default 60 | 2026-04-16 |
| AC6: Consistent 401 | Business logic | OWASP A07 — prevent username enumeration | Same error for wrong user OR wrong password | 2026-04-16 |
| AC7: Public route | Existing behavior | HARD.md R003 exception pattern | Same pattern as /v1/health | 2026-04-16 |
| AC8: Rate limit login | Business logic | Brute force protection | 10 req/min per IP | 2026-04-16 |
| AC9: verify_token dual mode | Existing behavior | backend/auth/oidc.py | Existing RS256/ES256 OIDC flow must still work | 2026-04-16 |

### S001: Authentication — Login / Logout

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Login form fields | Business logic | Standard login UX | username + password only, no SSO per lb_mui decision | 2026-04-16 |
| AC2: POST /v1/auth/token | Existing behavior | auth-api-key-oidc feature | JWT token endpoint already implemented | 2026-04-16 |
| AC3: JWT in-memory only | Business logic | OWASP Top 10 A03 | localStorage vulnerable to XSS — store in React context instead | 2026-04-16 |
| AC4: Auto Bearer header | Business logic | Axios interceptor pattern | Standard SPA auth pattern | 2026-04-16 |
| AC5: Token expiry redirect | Business logic | UX standard | 401 interceptor → logout + redirect | 2026-04-16 |
| AC6: Logout clears token | Business logic | Security hygiene | In-memory token GC on logout | 2026-04-16 |
| AC7: Unauthenticated redirect | Business logic | React Router guard | Protected route pattern | 2026-04-16 |
| AC8: No error detail leak | Requirement | CONSTITUTION.md A005 / SECURITY.md | Never expose stack trace or internal paths | 2026-04-16 |

### S002: Query Page — Search Input & Language Selector

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Search input | Business logic | Core feature — query page | Main interaction element | 2026-04-16 |
| AC2: 4-language selector | Conversation | lb_mui 2026-04-16 Q3 | ja/en/vi/ko — user selects UI language | 2026-04-16 |
| AC3: i18n label switch | Requirement | CONSTITUTION.md P003 | Multilingual by design — all 4 languages equal | 2026-04-16 |
| AC4: localStorage persist | Business logic | UX standard | Persist language preference across sessions | 2026-04-16 |
| AC5: Enter/button submit | Business logic | UX standard | Keyboard + mouse both supported | 2026-04-16 |
| AC6: Disable empty submit | Business logic | Input validation | Prevent empty query to backend | 2026-04-16 |
| AC7: 512 char limit | Existing behavior | SECURITY.md S003 | Query limit 512 tokens before embedding | 2026-04-16 |
| AC8: Loading state | Business logic | UX standard | Prevent double submit, show progress | 2026-04-16 |

### S003: Query Results — Answer + Citations Display

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Answer markdown | Business logic | UX — AI answers often contain lists/bold | react-markdown renderer | 2026-04-16 |
| AC2: Citation display | Existing behavior | answer-citation feature | doc_id, title, chunk, score in /v1/query response | 2026-04-16 |
| AC3: Confidence badge | Existing behavior | confidence-scoring feature | HIGH≥0.7 / MEDIUM 0.4–0.69 / LOW<0.4 | 2026-04-16 |
| AC4: LOW warning banner | Requirement | CONSTITUTION.md C014 | confidence < 0.4 → low-confidence warning mandatory | 2026-04-16 |
| AC5: Citations expand/collapse | Business logic | UX — avoid clutter for many citations | Default collapsed if >3 | 2026-04-16 |
| AC6: No results message | Existing behavior | query-endpoint feature | Backend returns empty citations array | 2026-04-16 |
| AC7: API error handling | Requirement | CONSTITUTION.md P005 | Fail visibly — structured errors, no silent failures | 2026-04-16 |
| AC8: Clear on new query | Business logic | UX standard | Stale results confuse user | 2026-04-16 |

### S004: Query History — Session-level

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: History list max 20 | Business logic | UX balance — too many = noisy | In-memory Zustand store | 2026-04-16 |
| AC2: Click to restore | Business logic | Reduce retyping friction | Restore answer + citations from store | 2026-04-16 |
| AC3: Session only, no persist | Conversation | lb_mui 2026-04-16 | No backend storage needed, privacy-friendly | 2026-04-16 |
| AC4: Clear on logout | Business logic | Security hygiene | No residual data after session ends | 2026-04-16 |
| AC5: Truncated display | Business logic | UX — long queries break layout | CJK-safe truncation at 60 chars | 2026-04-16 |

### S005: Build & Docker Packaging

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: npm run build | Business logic | Vite standard build output | dist/ static files | 2026-04-16 |
| AC2: Multi-stage Dockerfile | Conversation | lb_mui 2026-04-16 Q5 (c) | node:20-alpine build + nginx:alpine serve | 2026-04-16 |
| AC3: SPA nginx fallback | Business logic | React Router requirement | try_files → index.html for all routes | 2026-04-16 |
| AC4: VITE_API_BASE_URL env | Requirement | CONSTITUTION.md — zero hardcoded config | Configurable per deploy environment | 2026-04-16 |
| AC5: Clean build | Business logic | CI gate | No errors on fresh build | 2026-04-16 |
| AC6: Docker run works | Conversation | lb_mui 2026-04-16 | Independent deploy from admin-spa | 2026-04-16 |
| AC7: .env.example | Requirement | CONSTITUTION.md S005 | Zero secrets in code — env var documentation | 2026-04-16 |

---

## Summary

**Total ACs:** 45
**Fully traced:** 45/45 ✓
**Pending sources:** 0
