# Sources Traceability: admin-spa
Created: 2026-04-17 | Feature spec: `docs/admin-spa/spec/admin-spa.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S000: Backend — Admin Group Flag + Admin Endpoints

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Migration 009 is_admin on user_groups | Conversation | lb_mui 2026-04-17 — "xem xét tạo group cho admin" | User chose group-based admin rather than per-user flag | 2026-04-17 |
| AC2–AC3: AuthenticatedUser.is_admin | Business logic | AuthenticatedUser dataclass in backend/auth/types.py | Admin context must be carried in request scope for gate checks | 2026-04-17 |
| AC4–AC5: GET/DELETE /v1/admin/documents | Conversation | lb_mui 2026-04-16 — frontend-spa Out of Scope: "Document upload/management → admin-spa" | Admin sees all docs (bypass RBAC) | 2026-04-17 |
| AC6–AC12: Group + User CRUD endpoints | Conversation | lb_mui 2026-04-17 — "Có — full CRUD" (Q3 answer) | Full group/user management via /v1/admin/* | 2026-04-17 |
| AC13: Write gate expanded | Conversation | lb_mui 2026-04-17 — "Mở rộng: JWT admin được write" (Q2 answer) | Extend D09: api_key OR (jwt AND is_admin) | 2026-04-17 |
| AC14: is_admin in token response | Business logic | UX requirement — SPA needs admin flag immediately at login | Avoid extra round-trip to check admin status | 2026-04-17 |
| AC15: 403 for non-admin | Existing behavior | HARD.md R003 — all /v1/* require auth; 403 pattern from ARCH.md A005 | Consistent error shape across all protected endpoints | 2026-04-17 |

### Story S001: Admin Login + Admin Gate

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC3: Login form + JWT in-memory | Existing behavior | frontend-spa S001 (D02 — OWASP XSS prevention) | Reuse login pattern; no localStorage for JWT | 2026-04-17 |
| AC4: Block non-admin after login | Conversation | lb_mui 2026-04-17 — admin gate via is_admin group flag | Show "Access denied" if is_admin=false | 2026-04-17 |
| AC5: Redirect to /dashboard | Business logic | Admin SPA entry point after successful admin auth | Standard post-login redirect pattern | 2026-04-17 |
| AC6–AC7: Token expiry + logout | Existing behavior | frontend-spa S001 AC5–AC6 — same session management pattern | Reuse proactive refresh (D11) | 2026-04-17 |
| AC8–AC9: Auth guard + error display | Existing behavior | frontend-spa S001 AC7–AC8 — route guard + error message | No backend detail exposed in frontend | 2026-04-17 |
| AC10: i18n language selector | Existing behavior | frontend-spa D03 — UI language ja/en/vi/ko, persist localStorage | Same 4-language support for admin tool | 2026-04-17 |

### Story S002: Document Management

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2: Document list + pagination | Conversation | frontend-spa Out of Scope 2026-04-16 — "Document upload/management → admin-spa" | List all docs, paginated 20/page | 2026-04-17 |
| AC3: Filter by status/lang/group | Business logic | Operational UX — admin needs to locate docs quickly across groups | Client-side or query param filter | 2026-04-17 |
| AC4–AC6: Upload modal + toast | Business logic | Admin needs UI to add knowledge content without API calls | POST /v1/documents with raw text content | 2026-04-17 |
| AC5: JWT admin write gate | Conversation | lb_mui 2026-04-17 — "JWT admin được write" | Extended from D09: api_key only → api_key OR jwt+admin | 2026-04-17 |
| AC7–AC8: Delete with confirm | Business logic | Destructive action pattern — confirm dialog prevents accidental deletion | UX safety standard for admin tools | 2026-04-17 |
| AC9: Status badge colors | Existing behavior | document-ingestion spec — status enum: pending/processing/ready/error | Visual status indicator for ops monitoring | 2026-04-17 |
| AC10: No RBAC filter for admin | Business logic | Admin must see cross-group documents to manage full knowledge base | Intentional admin privilege bypass | 2026-04-17 |

### Story S003: User & Group Management

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC4: Group CRUD | Conversation | lb_mui 2026-04-17 — "full CRUD" + "is_admin flag on user_groups" | Full group management including admin flag toggle | 2026-04-17 |
| AC4: 409 on delete with users | Business logic | Data integrity — deleting group with users breaks RBAC | Backend returns 409 Conflict; frontend shows error | 2026-04-17 |
| AC5–AC7: User list + group assign | Conversation | lb_mui 2026-04-17 — full CRUD answer includes assign user→group | Multi-select group assignment UI | 2026-04-17 |
| AC8: Toggle user active | Business logic | Admin needs to deactivate users without deleting (preserve audit trail) | PUT /v1/admin/users/{id} with is_active field | 2026-04-17 |
| AC9: Client-side search | Business logic | Internal tool — user count typically < 1000, client-side filter sufficient | Avoid pagination complexity for internal admin | 2026-04-17 |

### Story S004: Metrics Dashboard

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2: Dashboard landing + count cards | Business logic | Standard admin dashboard UX — key metrics at a glance | /dashboard as post-login landing page | 2026-04-17 |
| AC3: Query volume chart | Existing behavior | audit_logs table (migration 001) already tracks queries with timestamp | 7-day query count from audit_logs | 2026-04-17 |
| AC4: System health | Business logic | Ops monitoring — admin needs to know if backend/DB are up | Simple green/red health indicators | 2026-04-17 |
| AC5: GET /v1/metrics | Existing behavior | CLAUDE.md stack — /v1/metrics listed as platform endpoint | Needs implementation if not yet done | 2026-04-17 |
| AC6–AC7: Auto-refresh + error handling | Business logic | Dashboard should stay current; graceful degradation if metrics fail | setInterval 60s + try/catch with "unavailable" fallback | 2026-04-17 |

### Story S005: Build & Docker Packaging

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC3: npm build + Dockerfile + nginx | Existing behavior | frontend-spa S005 (D07) — same Vite + multi-stage Docker pattern | Reuse: node:20-alpine build → nginx:alpine serve | 2026-04-17 |
| AC4: VITE_API_BASE_URL env var | Existing behavior | frontend-spa S005 AC4 + CONSTITUTION.md — zero hardcoded config | Same Vite env var pattern | 2026-04-17 |
| AC5: Port 8081:80 | Business logic | Avoid port conflict: backend=8000, frontend-spa=8080, dev=3000 | D13 pattern from frontend-spa extended for admin-spa | 2026-04-17 |
| AC6–AC8: Build + run validation | Existing behavior | frontend-spa S005 AC5–AC6 — same validation ACs | Identical packaging quality gate | 2026-04-17 |

---

## Summary

**Total ACs:** 50
**Fully traced:** 50/50 ✓
**Pending sources:** 0

**Open Assumptions (flag for /clarify):**
- A1 (S000): user_group_memberships junction table — does it exist? Need to verify before planning
- A2 (S002): Upload is raw text only — no binary file upload in v1
- A3 (S004): /v1/metrics endpoint — not yet implemented (only in CLAUDE.md stack reference)
- A4 (S005): admin-spa lives at `frontend/admin-spa/` (separate Vite project)

---

## How to Update

When spec changes or new ACs discovered:
1. Add row to relevant Story table
2. Include source type + reference (must be findable)
3. Add date
4. Update Summary section
5. Commit with message: `docs: update sources traceability for admin-spa`

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |
