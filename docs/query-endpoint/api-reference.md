# Knowledge Hub — API Reference

Generated: 2026-04-13 | Version: v1 | Branch: feature/query-endpoint

---

## Overview

The Knowledge Hub API provides hybrid RAG (Retrieval-Augmented Generation) search over internal documents. All endpoints are prefixed with `/v1/`. Authentication is required on every endpoint except `/v1/health` (not yet implemented).

**Base URL:** `http://<host>:8000`

**Authentication:** All requests must include one of:
- `X-API-Key: <key>` — for bots and service accounts
- `Authorization: Bearer <jwt>` — for human users (OIDC/SSO)

---

## Endpoints

### POST /v1/query

Perform a hybrid RAG query over the document store. Returns an AI-generated answer grounded in retrieved documents, filtered by the caller's RBAC groups.

#### Request

```http
POST /v1/query
Content-Type: application/json
X-API-Key: <key>
```

**Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural language question. Max 512 characters. Control characters are stripped automatically. |
| `top_k` | integer | No | Number of documents to retrieve. Range: 1–100. Default: `10`. |
| `lang` | string \| null | No | Language code override (e.g. `"ja"`, `"vi"`, `"en"`, `"ko"`). If omitted, language is auto-detected from the query text. |

**Example**

```json
{
  "query": "What is the leave policy for contractors?",
  "top_k": 5,
  "lang": "en"
}
```

#### Response — 200 OK

```json
{
  "request_id": "a2ddb50e-33d0-40bf-bae1-a46e870fa7a6",
  "answer": "Contractors are entitled to ...",
  "sources": [
    "100038c2-ad58-40fe-990e-66171a50f840",
    "abce4c10-1589-4b5e-bf28-4910501f4190"
  ],
  "low_confidence": false,
  "reason": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string (UUID) | Unique ID for this request. Include in support tickets. Present on all responses. |
| `answer` | string \| null | AI-generated answer. `null` when no relevant documents were found. |
| `sources` | string[] | List of document UUIDs used to generate the answer. Empty when `answer` is null. |
| `low_confidence` | boolean | `true` when model confidence < 0.4. Treat the answer as uncertain. |
| `reason` | string \| null | Populated only when `answer` is null. Value: `"no_relevant_chunks"`. |

**Response headers (always present)**

| Header | Description |
|--------|-------------|
| `X-RateLimit-Remaining` | Requests remaining in the current 60-second window. |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit window resets. |

#### No-answer response (200)

When no relevant documents match the query:

```json
{
  "request_id": "...",
  "answer": null,
  "sources": [],
  "low_confidence": false,
  "reason": "no_relevant_chunks"
}
```

#### Error Responses

All error responses follow the shape:

```json
{
  "error": {
    "code": "ERR_CODE",
    "message": "Human-readable description",
    "request_id": "uuid"
  }
}
```

| HTTP Status | Code | Trigger |
|-------------|------|---------|
| 400 | `REQUEST_VALIDATION_ERROR` | `query` exceeds 512 chars, or `top_k` out of 1–100. |
| 401 | `AUTH_MISSING` | No `X-API-Key` or `Authorization` header. |
| 401 | `AUTH_INVALID_KEY` | API key not found or inactive. |
| 401 | `AUTH_TOKEN_INVALID` | JWT expired, wrong issuer, wrong audience, or bad signature. |
| 403 | `AUTH_FORBIDDEN` | Valid token but insufficient group permissions (not returned for 0-group users — they receive public results instead). |
| 422 | `LANG_DETECT_FAILED` | Language auto-detection failed. Retry with explicit `lang` field. |
| 422 | `UNSUPPORTED_LANGUAGE` | Detected or specified language is not supported. Supported: `ja`, `ko`, `zh`, `vi`, `en`. |
| 429 | `RATE_LIMIT_EXCEEDED` | Exceeded 60 requests/minute per `user_id`. Check `X-RateLimit-Reset` before retrying. |
| 503 | `EMBEDDER_UNAVAILABLE` | Embedding service (Ollama) is unreachable. |
| 503 | `LLM_UNAVAILABLE` | LLM generation failed or timed out (> 800 ms budget). |
| 504 | `QUERY_TIMEOUT` | Retrieval exceeded 1000 ms SLA. |

---

### GET /v1/documents

List documents accessible to the authenticated user.

> Full schema: see `docs/document-ingestion/` spec.

---

### POST /v1/documents

Ingest a new document.

> Full schema: see `docs/document-ingestion/` spec.

---

### GET /v1/documents/{doc_id}

Retrieve metadata for a single document by UUID.

---

### DELETE /v1/documents/{doc_id}

Delete a document by UUID.

---

## Authentication

### API Key (bots / service accounts)

Pass the key in the `X-API-Key` header. Keys are stored hashed in PostgreSQL and scoped to one or more user groups.

```http
X-API-Key: sk-your-api-key
```

### OIDC Bearer Token (human users)

Obtain a JWT from your identity provider and pass it in the `Authorization` header.

```http
Authorization: Bearer eyJhbGci...
```

JWT validation: signature, expiry (`exp`), issuer (`iss`), and audience (`aud`) are all verified on every request. Any failure returns `401 AUTH_TOKEN_INVALID` — no details are leaked in the response.

---

## Rate Limiting

- **Limit:** 60 requests per minute per `user_id`
- **Algorithm:** Sliding window (Valkey ZADD/ZCOUNT)
- **Key:** `ratelimit:query:{user_id}`
- **Headers:** `X-RateLimit-Remaining` and `X-RateLimit-Reset` are present on every response, including 429s.
- **Fail-open:** If Valkey is unavailable, requests are allowed through (logged as warning).

When rate-limited:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1744530000

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 60 requests per minute exceeded",
    "request_id": "..."
  }
}
```

---

## SLA & Timeouts

| Stage | Timeout | Fallback |
|-------|---------|---------|
| Retrieval (hybrid search) | 1000 ms | Returns `504 QUERY_TIMEOUT` |
| LLM generation | 800 ms | Returns `503 LLM_UNAVAILABLE` |
| Total p95 target | < 2000 ms | — |

Override for local dev via env vars: `RETRIEVAL_TIMEOUT_OVERRIDE`, `LLM_TIMEOUT_OVERRIDE`.

---

## LLM Configuration

The LLM provider is runtime-configurable via environment variables. No code changes required to switch providers.

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_PROVIDER` | Provider name: `openai`, `ollama`, `claude` | `openai` |
| `LLM_MODEL` | Model identifier for the chosen provider | `openai/gpt-oss-120b:free` |
| `OPENAI_API_KEY` | API key (OpenAI or OpenRouter) | `sk-or-v1-...` |
| `OPENAI_BASE_URL` | Base URL override — set to OpenRouter to use free/alternative models | `https://openrouter.ai/api/v1` |
| `OLLAMA_LLM_URL` | Ollama server URL (used when `LLM_PROVIDER=ollama`) | `http://localhost:11434` |

**Using OpenRouter (free models):**

```env
LLM_PROVIDER=openai
LLM_MODEL=openai/gpt-oss-120b:free
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

---

## RBAC

Documents are tagged with `user_group_id`. The retrieval layer applies a hard filter at the database level (`WHERE user_group_id = ANY(:group_ids)`) — Python-level post-filtering is never used.

- Users with one or more groups receive documents scoped to those groups plus public documents (where `user_group_id IS NULL`).
- Users with zero groups receive public documents only — not a `403`.
- No document content is exposed in API responses. `sources` contains doc UUIDs only (R002 PII rule).

---

## Audit Logging

Every successful retrieval writes one row to `audit_logs` per retrieved document:

| Column | Value |
|--------|-------|
| `user_id` | Authenticated user ID |
| `doc_id` | Retrieved document UUID |
| `query_hash` | SHA-256 of the raw query string |
| `timestamp` | Server time at request |

Audit writes run as a background task and do not affect response latency.

---

## Supported Languages

| Code | Language | Tokenizer |
|------|----------|-----------|
| `ja` | Japanese | MeCab |
| `ko` | Korean | (CJK-aware) |
| `zh` | Chinese | jieba |
| `vi` | Vietnamese | underthesea |
| `en` | English | whitespace |

Language is auto-detected from the query if `lang` is not specified.
