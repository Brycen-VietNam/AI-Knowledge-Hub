# Sources Traceability: query-endpoint
Created: 2026-04-08 | Feature spec: `docs/query-endpoint/spec/query-endpoint.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source.
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Wire search() into POST /v1/query

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: search() replaces inline embed+retrieve | Existing behavior | `backend/rag/search.py` lines 18–70 | `search()` already implements full pipeline: detect→tokenize→embed→retrieve | 2026-04-08 |
| AC2: lang override in request body | Business logic | D4 decision (HOT.md 2026-04-08) | `lang: str\|None = None` — None=auto-detect, override=skip detect | 2026-04-08 |
| AC3: LanguageDetectionError → 422 | Constitution | C009 — auto-detect required | Detection must succeed; failure is a client-correctable condition | 2026-04-08 |
| AC4: UnsupportedLanguageError → 422 | Existing behavior | `backend/rag/search.py` line 51 | Error raised for langs not in `_SUPPORTED` set | 2026-04-08 |
| AC5: EmbedderError → 503 | Existing behavior | `backend/rag/embedder.py` — `EmbedderError` class | Embedding API failure is transient/upstream, not client error | 2026-04-08 |
| AC6: QueryTimeoutError → 504 | Existing behavior | `backend/api/routes/query.py` lines 127–135 | Timeout handler already present — must not regress | 2026-04-08 |
| AC7: 0-group users → public results | Business logic | D04 (rbac-document-filter, 2026-04-06) | Approved decision: no 403 for 0-group; return public documents | 2026-04-08 |
| AC8: Audit log background task | HARD.md R006 | R006 — every retrieval logged | user_id, doc_id, timestamp, query_hash required | 2026-04-08 |

### Story S002: Wire generate_answer() for AI responses

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: generate_answer() called on non-empty docs | Existing behavior | `backend/rag/generator.py` lines 7–10 | Service layer exists; currently not called (stub returns `reason: "llm_disabled"`) | 2026-04-08 |
| AC2: answer non-null on LLM success | Existing behavior | `QueryResponse.answer: str\|None` in query.py | Field exists; must be populated | 2026-04-08 |
| AC3: sources = doc_id list, not content | HARD.md R002 | R002 — No PII in vector metadata; doc_id safe | Current stub leaks `d.content` into sources — this is the bug to fix | 2026-04-08 |
| AC4: low_confidence on confidence < 0.4 | Constitution | C014 — confidence < 0.4 triggers warning | Threshold is a constitution constraint, not configurable at story level | 2026-04-08 |
| AC5: NoRelevantChunksError → 200 null | Business logic | D09 decision (llm-provider feature) | 200 with null answer preferred over 4xx — search succeeded, no answer found | 2026-04-08 |
| AC6: LLM unavailable → 503 | Constitution | P005 — fail fast, fail visibly | LLM failure is upstream/transient; 503 is correct HTTP semantics | 2026-04-08 |
| AC7: ≥1 source required | Constitution | C014 — no answer if 0 relevant chunks | Platform integrity: never generate unsourced answers | 2026-04-08 |
| AC8: reason only when answer null | Existing behavior | D09/D10 decisions, QueryResponse in query.py | `reason` field defined with `= None` default; only meaningful when answer absent | 2026-04-08 |

### Story S003: Rate limiting — 60 req/min per user

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: 429 on limit exceeded | SECURITY.md S004 | S004 — 60 req/min /v1/query | Standard rate limit response code | 2026-04-08 |
| AC2: sliding window algorithm | SECURITY.md S004 | S004 — "Redis sliding window" specified | Fixed bucket allows burst at window boundary; sliding is safer | 2026-04-08 |
| AC3: Valkey backend | Constitution | C016 — Redis ≥7.4 RSALv2 forbidden | Valkey is drop-in BSD-3 replacement; already in tech stack | 2026-04-08 |
| AC4: rate limit key pattern | Business logic | SECURITY.md S004 + auth types | `AuthenticatedUser.user_id` is unified key across both auth paths | 2026-04-08 |
| AC5: reusable middleware | Business logic | /v1/documents also rate-limited (20/min) | Single middleware avoids duplication when documents endpoint adds limits | 2026-04-08 |
| AC6: fail-open on Valkey down | Business logic | Platform availability > strict enforcement | Valkey outage should not block legitimate queries | 2026-04-08 |
| AC7: rate limit headers | Business logic | RFC 6585 standard headers | `X-RateLimit-Remaining`, `X-RateLimit-Reset` expected by API consumers | 2026-04-08 |

### Story S004: Structured error handling & observability

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: unified error shape | ARCH.md A005 | A005 — error response shape | `{"error": {"code": "...", "message": "...", "request_id": "..."}}` | 2026-04-08 |
| AC2: no stack traces | ARCH.md A005 | A005 — internal paths forbidden in prod | Debug info available in logs, not API responses | 2026-04-08 |
| AC3: 400 on invalid input | Existing behavior | `QueryRequest` Pydantic validators in query.py | `max_length=512`, `ge=1, le=100` constraints already defined | 2026-04-08 |
| AC4: 401 on missing/invalid auth | Existing behavior | auth-api-key-oidc feature — must not regress | verify_token raises 401 — error handler must not swallow it | 2026-04-08 |
| AC5: no 403 for 0-group | Business logic | D04 (rbac-document-filter) | Already in current implementation — regression guard | 2026-04-08 |
| AC6: request_id in all responses | Existing behavior | `request_id = str(uuid4())` in query.py line 113 | Present in success; must also be in error responses | 2026-04-08 |

### Story S005: Integration tests — query endpoint full coverage

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: multilingual happy path | Constitution | P003 — multilingual by design | All supported languages must be tested | 2026-04-08 |
| AC2: RBAC isolation test | Constitution | C001 — RBAC at WHERE clause | Test verifies no cross-group data leakage | 2026-04-08 |
| AC3: 0-group → public results | Business logic | D04 | Regression guard for public-access behavior | 2026-04-08 |
| AC4–AC10: error path tests | Constitution | P005 — fail fast, fail visibly | Each error code needs a test | 2026-04-08 |
| AC11: lang override test | Existing behavior | `search()` lang parameter (search.py) | Validates bypass of auto-detection | 2026-04-08 |
| AC12: ≥80% coverage | Constitution | Testing conventions | Enforced on new code in query.py + middleware | 2026-04-08 |

---

## Summary

**Total ACs:** 34
**Fully traced:** 34/34 ✓
**Pending sources:** 0

---

## Source Type Reference

| Type | Examples |
|------|----------|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Constitution** | CONSTITUTION.md constraint or principle |
| **HARD.md** | Hard rule (never-violate) |
| **ARCH.md** | Architecture rule |
| **SECURITY.md** | Security rule |
