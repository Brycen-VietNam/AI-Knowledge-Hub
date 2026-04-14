# Analysis: query-endpoint — Full Feature (S001–S005)
Date: 2026-04-08 | Depth: shallow | Files scanned: 9

---

## Code Map

### `backend/api/routes/query.py` — MAIN TARGET
```
QueryRequest(BaseModel)
  query: str = Field(..., max_length=512)
  top_k: int = Field(default=10, ge=1, le=100)
  ← MISSING: lang: str | None = None  [S001-T002]

QueryResponse(BaseModel)
  request_id: str
  answer: str | None
  sources: list[str]
  low_confidence: bool
  reason: str | None = None

async def embed(text: str) -> list[float]   ← MUST DELETE [S001-T001]
  # Lines 57–64 — bypasses language detection, violates A003

async def _write_audit(user_id, docs, query_hash) -> None   ← KEEP, already correct

router = APIRouter()

@router.post("/v1/query", response_model=QueryResponse)
async def query_documents(body, background_tasks, user, db):
  request_id = str(uuid4())
  query_hash = hashlib.sha256(body.query.encode()).hexdigest()
  # PROBLEM: calls embed() + retrieve() directly — NOT search() [S001-T004]
  # PROBLEM: sources=[d.content for d in docs if d.content]  ← PII BUG R002 [S001-T001]
  # MISSING: generate_answer() not called [S002-T002]
  # MISSING: lang not passed anywhere [S001-T002, S001-T004]
  # MISSING: rate limit check [S003-T003]
  # MISSING: NoRelevantChunksError → 200 null (currently empty docs returns null, but wrong path) [S002-T003]
  # MISSING: low_confidence set from LLM response [S002-T004]
```

### `backend/rag/search.py` — WIRE TARGET
```
async def search(
  query: str,
  user_group_ids: list[int],
  session: AsyncSession,
  top_k: int = 10,
  lang: str | None = None,   ← matches D4 decision
) -> list[RetrievedDocument]
  # Raises: LanguageDetectionError, UnsupportedLanguageError, EmbedderError, QueryTimeoutError
  # Step 1: detect/validate lang
  # Step 2: tokenize_query(query, lang)
  # Step 3: embed_query(query)
  # Step 4: retrieve(query, query_embedding, bm25_query, user_group_ids, session, top_k)
```

### `backend/rag/generator.py`
```
async def generate_answer(query: str, chunks: list[str]) -> LLMResponse
  # Takes chunks: list[str] — NOT list[RetrievedDocument]
  # ⚠️ MISMATCH: tasks say docs=docs but signature requires chunks: list[str]
  # MUST pass: [d.content for d in docs] as chunks arg
```

### `backend/rag/llm/base.py`
```
@dataclass LLMResponse:
  answer: str
  sources: list[str]
  confidence: float
  provider: str
  model: str
  low_confidence: bool
```

### `backend/rag/llm/exceptions.py`
```
class LLMError(Exception)
class NoRelevantChunksError(LLMError)
  ← import path: backend.rag.llm (via __init__)
  ← NOT backend.rag.llm.exceptions directly
```

### `backend/api/app.py` — MINIMAL (needs exception handlers + Valkey startup)
```
def create_app() -> FastAPI:
  app = FastAPI(title="Knowledge Hub API")
  app.include_router(query.router)
  app.include_router(documents.router)
  return app
  ← MISSING: exception handler registrations [S004-T002]
  ← MISSING: Valkey connection pool startup [S003-T003]
  ← MISSING: request_id middleware [S004-T003]
```

### `backend/auth/_errors.py`
```
def auth_error(request, code, message, status) -> HTTPException:
  # Uses request.state.request_id if present, else generates fresh UUID
  # A005-compliant: {"error": {"code", "message", "request_id"}}
  ← REUSE PATTERN for exception handlers in S004
```

### `backend/auth/dependencies.py`
```
async def verify_token(request, x_api_key, authorization, db) -> AuthenticatedUser
async def get_db() -> AsyncGenerator[AsyncSession, None]
```

### `backend/rag/retriever.py`
```
class QueryTimeoutError(Exception)

@dataclass RetrievedDocument:
  doc_id: uuid.UUID
  chunk_index: int
  score: float
  user_group_id: int | None
  content: str | None = None   ← content field EXISTS but must NOT go in sources (R002)
```

---

## Existing Tests (already written — do NOT duplicate)
`tests/api/test_query_route.py` — 3 tests, patches `retrieve` + `generate_answer` + `_write_audit` directly.
These tests will BREAK after S001 (search() replaces retrieve()) — must update patch targets.

`tests/api/test_query_rbac.py` — RBAC isolation tests (existing)
`tests/api/conftest.py` — stubs OIDC env vars only

---

## Conflicts & Gaps Found

### ❌ CRITICAL — PII BUG (R002)
`query.py:152` — `sources=[d.content for d in docs if d.content]`
Content field leaks document text into API response. Must be `[str(d.doc_id) for d in docs]`.

### ❌ CRITICAL — Bypasses Language Detection (A003)
`query.py:57–64` — `embed()` helper hardcodes `lang="en"` inside a Chunk object.
Must be deleted. search() handles detection end-to-end.

### ❌ CRITICAL — generate_answer() signature mismatch
`generator.py:7` — signature is `generate_answer(query: str, chunks: list[str])`
Tasks say pass `docs=docs` but actual arg is `chunks: list[str]`.
**Fix**: pass `chunks=[d.content for d in docs if d.content]` — NOT docs directly.
This is the ONLY place content is legitimately used (LLM context, not response).

### ⚠️ WARNING — Existing tests patch wrong targets
`test_query_route.py` patches `backend.api.routes.query.retrieve` and `backend.api.routes.query.embed`.
After S001-T004 wires search(), the patch target must change to `backend.api.routes.query.search`.
These 3 existing tests will fail after S001 — must be updated in S001-T005 or S005-T001.

### ⚠️ WARNING — No `LLMUnavailableError` class found
`backend/rag/llm/exceptions.py` only defines `LLMError` and `NoRelevantChunksError`.
`LLMUnavailableError` referenced in S004-T002 does NOT exist.
**Fix**: Add `class LLMUnavailableError(LLMError)` to `backend/rag/llm/exceptions.py` and export from `__init__`.
Or catch `LLMError` as the 503 trigger (simpler, covers same surface).

### ⚠️ WARNING — `backend/api/config.py` does not exist
Tasks reference `backend/api/config.py` for `VALKEY_URL`. File not found in glob.
Must CREATE `backend/api/config.py` in S003-T001.

### ⚠️ WARNING — `backend/api/middleware/` directory does not exist
Must CREATE `backend/api/middleware/__init__.py` + `rate_limiter.py` in S003-T001/T002.

### ⚠️ WARNING — `tests/api/test_query.py` does not exist yet
Tasks reference this file across S001–S005. Must CREATE in S001-T003.
Existing tests in `test_query_route.py` use different fixture pattern — align new tests with that pattern.

### ⚠️ WARNING — `request_id` not stored in `request.state`
`query.py:113` generates `request_id = str(uuid4())` locally but never sets `request.state.request_id`.
Exception handlers (auth_error pattern) read from `request.state.request_id`.
**Fix**: add `request.state.request_id = request_id` at S004-T003.
Route signature must include `request: Request` parameter (not currently present).

### INFO — timeout budget split
Search timeout: 1.0s (asyncio.wait_for(..., timeout=1.0))
LLM timeout: 0.8s (asyncio.wait_for(..., timeout=0.8))
Total SLA: 1.8s — matches A2 confirmed assumption. Do NOT use the existing 1.8s single timeout.

---

## Patterns to Follow

### Auth param injection
`query.py:103` — `user: Annotated[AuthenticatedUser, Depends(verify_token)]` ← keep this pattern
`user.user_group_ids` → pass to `search()` as `user_group_ids`

### A005 error shape (from `_errors.py`)
```python
return JSONResponse(
    status_code=N,
    content={"error": {"code": "ERR_CODE", "message": "...", "request_id": request_id}},
)
```

### BackgroundTask pattern (already correct in query.py:137)
```python
background_tasks.add_task(_write_audit, user.user_id, docs, query_hash)
```

### pgvector / SQLAlchemy
Use `text().bindparams()` — never f-strings (S001).

---

## Recommended Approach by Story

### S001 (5 tasks — critical path first)
1. **T001**: Delete `embed()` (lines 57–64). Change `sources` to `[str(d.doc_id) for d in docs]`.
2. **T002**: Add `lang: str | None = None` to `QueryRequest` in `query.py` (schemas.py doesn't exist; QueryRequest is inline in query.py).
3. **T003**: Create `tests/api/test_query.py` with fixtures — patch `backend.api.routes.query.search` (not retrieve).
4. **T004**: Import `search` from `backend.rag.search`. Replace embed+retrieve block with `asyncio.wait_for(search(...), timeout=1.0)`. Add `Request` param to route, set `request.state.request_id`.
5. **T005**: Fix audit log (already present). Update 3 existing tests in `test_query_route.py` that patch `retrieve` → `search`.

### S002 (4 tasks)
1. Add `mock_generate_answer` fixture to test file.
2. After search() returns docs, call `asyncio.wait_for(generate_answer(query=..., chunks=[d.content for d in docs if d.content]), timeout=0.8)`.
3. `NoRelevantChunksError` catch → 200 `{answer: null, reason: "no_relevant_chunks"}`.
4. `low_confidence = (response.confidence < 0.4)` — use named constant `LOW_CONFIDENCE_THRESHOLD = 0.4`.

### S003 (4 tasks)
1. Create `backend/api/config.py` with `VALKEY_URL = os.getenv("VALKEY_URL", "valkey://localhost:6379")`.
2. Create `backend/api/middleware/__init__.py` + `rate_limiter.py` with `RateLimiter` class (valkey-py, sliding window).
3. Register in `app.py`: Valkey pool at startup, `RateLimiter` dependency on query route.
4. Fail-open: wrap Valkey ops in try/except, log warning, return (True, limit, reset_ts) on error.

### S004 (3 tasks)
1. Validators already partially present (`max_length=512`, `ge=1, le=100`) — add `@field_validator` for control char stripping. Add `lang` field (done in S001).
2. Register `@app.exception_handler` for 5 RAG error types. Create `LLMUnavailableError` in `backend/rag/llm/exceptions.py` first.
3. Add `request: Request` to route signature, `request.state.request_id = request_id`.

### S005 (3 tasks)
1. Extend `test_query.py` with parametrized lang tests + all AC bodies.
2. Add AC10 rate limit mock test to `test_rate_limiter.py`.
3. Run coverage gate: `pytest tests/api/ --cov=backend/api/routes/query.py --cov=backend/api/middleware/rate_limiter.py --cov-fail-under=80`.

---

## Token Budget
Files scanned: 9 source + 2 test + 5 task files
Analysis saved: `docs/query-endpoint/tasks/query-endpoint.analysis.md`
