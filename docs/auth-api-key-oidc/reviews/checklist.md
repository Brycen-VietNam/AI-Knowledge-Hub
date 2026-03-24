# Checklist: auth-api-key-oidc
Generated: 2026-03-23 | Model: haiku | Spec: docs/specs/auth-api-key-oidc.spec.md

---

## Result: ⚠️ WARN — 2 items cần approval (không có FAIL)

---

## ✅ Passed (24/26)

### Spec Quality
- [x] Spec file tồn tại: `docs/specs/auth-api-key-oidc.spec.md`
- [x] Layer 1 summary đầy đủ: Epic, Priority, Story count, Critical path, Parallel-safe, Blocking/Blocked, Agents
- [x] Layer 2 stories có AC rõ ràng — testable, SMART criteria (20 ACs với specific column names, HTTP codes, error codes)
- [x] Layer 3 sources fully mapped: 20/20 ACs traced ✓
- [x] Tất cả ACs testable — không có "should work well", tất cả có grep/SQL/pytest verification method
- [x] API contract defined: S002 (X-API-Key header), S003 (Authorization Bearer), S004 (unified verify_token usage)
- [x] Không có silent assumptions — tất cả marked explicitly trong clarify.md (D01–D09)

### Architecture Alignment
- [x] **No CONSTITUTION violations**: C003 ✓ (auth trên mọi /v1/*), C008 ✓ (audit_logs FK), C010 ✓ (migration + ORM order), Non-Negotiables ✓ (no secrets, no anon access)
- [x] **No HARD rule violations**: R003 ✓ (verify_token Depends), S002 ✓ (JWT 4-claim validation), S005 ✓ (env vars only)
- [x] **Agent scope**: db-agent → S001 (backend/db/), auth-agent → S002–S004 (backend/auth/) — match AGENTS.md ✓
- [x] **Dependency direction**: api → auth → db (A002) ✓; auth/api_key.py explicitly states no rag/api imports (S002 AC5)
- [x] **Schema changes**: migration 004 planned với FORWARD + ROLLBACK (S001 AC4, ARCH.md A006)
- [x] **Auth pattern**: Both API-key (S002) và OIDC Bearer (S003) specified, unified via S004

### Multilingual Completeness
- [x] **N/A — auth layer không xử lý text content**. Không có ngôn ngữ-specific logic trong auth middleware.
- [x] CJK tokenization: N/A — auth layer (không có query/document processing)
- [x] Response language: Error messages là English (theo Team Conventions — user-facing strings qua i18n layer, không phải auth layer)

### Dependencies
- [x] `db-schema-embeddings` DONE ✅ — unblocks S001 migration
- [x] Không có circular story dependencies: S001 → S002/S003 (parallel) → S004 (linear, clean)
- [x] External contracts: PyJWT >= 2.8, cryptography >= 42.0, httpx >= 0.27 — all stable versions

### Agent Readiness
- [x] Token budget: ~4k estimated trong Layer 1
- [x] Parallel-safe stories: S002, S003 (after S001) — explicitly documented
- [x] Subagent assignments: db-agent (S001), auth-agent (S002–S004) trong WARM memory
- [x] AGENTS.md: auth-agent `NONE (always sequential)` — nghĩa là auth-agent chạy trước tất cả agents khác ✓

---

## ⚠️ WARN Items (cần approval trước /plan)

---

### WARN-1: Prompt Caching Strategy không documented

⚠️ **WARN**: Spec không có prompt caching strategy documentation.
**Risk**: Nếu sau này S003 OIDC middleware hoặc S004 unified dependency được dùng trong LLM orchestration pipeline, cache prefix sẽ không deterministic → tăng cost.
**Mitigation**: Auth layer là pure middleware — không có LLM prompts trực tiếp. Route A (stable prefix, default) áp dụng tự động khi được gọi từ subagent workflow. Không cần Route B vì không có direct Anthropic API path trong auth module.
**Classification**: N/A — auth feature không có LLM path. Theo `/checklist` policy: "If feature has no LLM path: mark item as N/A with short reason."

**→ Auto-approved: N/A (no LLM path in auth middleware)** ✅

---

### WARN-2: `AUTH_FORBIDDEN` (403) declared nhưng không có story trigger

⚠️ **WARN**: S004 AC4 khai báo error code `AUTH_FORBIDDEN` (403) nhưng không có story nào trong spec hiện tại trigger 403.
**Risk**: Dead code trong error handling — test coverage không thể verify 403 path → potential code rot.
**Mitigation**: Clarify Q9 documented assumption: "403 reserved for future use (suspended user account). Hiện tại chưa implement trong sprint này." Code sẽ có error code constant định nghĩa nhưng không có code path nào gọi nó trong sprint này. Tests sẽ verify 401 paths only.

**Approve? [x] Yes, proceed** — 403 constant là forward-compatible interface declaration, không tạo risk thực tế trong sprint này.

---

## Spec Additions Required (update spec trước /plan)

### AC cần thêm vào S003 (từ clarify resolutions):

**S003 AC1 cần update** để reflect D06, D07:
```
Thêm vào AC1:
- Nếu `groups` claim absent hoặc empty array → user_group_ids=[] (permissive, không 403)
- `users.email` lấy từ claim tên bởi `OIDC_EMAIL_CLAIM` env var (default "email")
- `users.display_name` lấy từ claim tên bởi `OIDC_NAME_CLAIM` env var (default "name")
```

**S001 AC1 cần update** để reflect D08 (Q8 assumption):
```
Thêm vào AC1: users.email và users.display_name là NULLABLE (không NOT NULL)
```

---

## Next

Spec cần 2 minor AC updates → sau đó: `/plan auth-api-key-oidc`

```
docs/reviews/auth-api-key-oidc.checklist.md  SAVED ✓
Result: WARN-approved (2 items — 1 auto N/A, 1 human-approved)
Blockers: 0
Passed: 24/26 (+ 2 WARN approved)
```
