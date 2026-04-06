# Analysis: llm-provider — All Stories (T001–T014)
Generated: 2026-04-06 | Depth: shallow + key bodies | Stories: S001–S004 + Post-G3

---

## Code Map

### Patterns to Follow (existing codebase)

#### `backend/rag/tokenizers/factory.py` — TokenizerFactory (D05 reference)
```
class TokenizerFactory:
    _registry: dict[str, BaseTokenizer] = {}     ← dict keyed by string
    _lock = threading.Lock()
    get(lang: str) -> BaseTokenizer               ← double-checked locking pattern
    _create(lang: str) -> BaseTokenizer           ← lazy imports per branch
```
**LLMProviderFactory (T009) must mirror this exactly**: `_instances` dict, `_lock`, double-checked locking, lazy imports in `_create()`. Key difference: `LLMProviderFactory._instances` is keyed by provider name (not lang), and `get()` takes no argument (reads env internally).

#### `backend/rag/tokenizers/base.py` — BaseTokenizer (S001 reference)
```
class BaseTokenizer(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[str]: ...
```
**LLMProvider ABC (T002)** follows same shape: one abstract async method. Note: `BaseTokenizer.tokenize()` is sync; `LLMProvider.complete()` must be `async` (D07 — entire stack async).

#### `backend/rag/tokenizers/exceptions.py` — exception hierarchy
```
class UnsupportedLanguageError(ValueError): ...    ← domain-specific base
class LanguageDetectionError(RuntimeError): ...
```
**LLMError hierarchy (T001)**: `LLMError(Exception)` → `NoRelevantChunksError(LLMError)`. Keep distinct from `LanguageDetectionError` (spec AC3 explicit requirement).

#### `backend/api/routes/query.py` — existing query route (T014 target)
```
imports:
  from backend.rag.retriever import QueryTimeoutError, RetrievedDocument, retrieve

QueryRequest(BaseModel):  query: str (max_length=512), top_k: int
QueryResult(BaseModel):   doc_id, chunk_index, score, is_public, content
QueryResponse(BaseModel): request_id: str, results: list[QueryResult]   ← D10: MUST CHANGE

@router.post("/v1/query", response_model=QueryResponse)
async def query_documents(body, background_tasks, user: Annotated[..., Depends(verify_token)], db):
    embed() → retrieve() under asyncio.wait_for(timeout=1.8) → background audit → return
```
**Critical for T014**: existing `QueryResponse` has `results: list[QueryResult]` — D10 replaces this with `answer + sources + low_confidence`. Existing tests in `test_query_rbac.py` assert `body["results"]` — **these will break and must be updated.**

#### `tests/api/test_query_rbac.py` — existing API tests (T014 reference)
```
Pattern: _make_app(user) → FastAPI app with dependency_overrides
         patch("backend.api.routes.query.retrieve", new=AsyncMock(...))
         patch("backend.api.routes.query._write_audit", new=AsyncMock())
         TestClient(app).post("/v1/query", json={"query": "..."})
```
**T014 must follow this exact pattern** for new tests. New patch target: `backend.api.routes.query.generate_answer` (replacing retrieve mock in LLM path).

#### `tests/rag/test_tokenizers.py` — tokenizer test structure (S004 reference)
```
import pytest, unittest.mock (patch, MagicMock)
_mecab_available() guard for OS-dependent tests
class-based test grouping: one class per story concern
```
**T011 TestAnswerGate** should follow same class-based structure. No OS-guard needed — all LLM adapters are mocked.

---

## Conflicts / Gaps Found

### ⚠️ CRITICAL — D10 breaks existing tests in test_query_rbac.py
```
tests/api/test_query_rbac.py:
  L85:  assert body["results"].__len__() == 2       ← will fail after D10
  L103: assert len(body["results"]) == 1             ← will fail after D10
  L119: assert body["results"][0]["is_public"] ...   ← will fail after D10
  L133: assert resp.json()["results"] == []          ← will fail after D10
  L198: body.get("request_id", "")                   ← request_id stays in new schema ✅
```
**Resolution for T014**: these tests must be updated alongside `QueryResponse` schema change. The `request_id` field should be **kept** in the new `QueryResponse` (not in spec but needed to avoid breaking `test_request_id_in_response` at L186). Add `request_id` to new QueryResponse. **Flag this to /implement.**

### ⚠️ gap — test_query_rbac.py imports QueryResponse directly
```
L17: from backend.api.routes.query import QueryResponse, router
```
After D10 `QueryResponse` field change, the import still works but downstream assertions on `results` will fail. All 4 affected tests need updating in T014.

### ⚠️ gap — `tests/api/test_query_route.py` does not exist yet
Task file S005 T014 refers to `tests/api/test_query_route.py` as the target. This file doesn't exist. **Resolution**: T014 must CREATE this file (new LLM-path tests) AND MODIFY `tests/api/test_query_rbac.py` (update broken assertions). TOUCH list in task file needs correction.

### ⚠️ gap — `backend/rag/generator.py` does not exist yet
Correct — T013 creates it. No conflict.

### ✅ No circular import risk
`backend/rag/llm/` → imports only from stdlib + third-party SDKs (lazy).
`backend/rag/generator.py` → imports from `backend/rag/llm/` only.
`backend/api/routes/query.py` → imports `generate_answer` from `backend/rag/generator`.
Direction: `api → rag/generator → rag/llm` — clean, matches ARCH A002.

### ✅ `requirements.txt` — openai and anthropic not present yet
Current `requirements.txt` L1–22 has no `openai` or `anthropic`. T005 adds them. No conflict with existing deps.

### ✅ `pytest-asyncio` already in requirements (L22)
`pytest-asyncio==0.25.3` present. `@pytest.mark.asyncio` decorators in S002/S004 tasks will work without additional installs.

### ✅ `conftest.py` pattern — OIDC env stubs
`tests/api/conftest.py` stubs `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URI`. LLM tests need `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `LLM_PROVIDER` — these should use `monkeypatch.setenv` per test (not conftest), consistent with tokenizer test pattern.

### ✅ `tests/rag/__init__.py` exists
`tests/rag/test_llm_provider.py` (T001 creates it) can be placed immediately — package already exists.

---

## Recommended Approach Adjustments

### T002 — base.py: `complete()` signature correction
Task file shows `complete(self, prompt: str, context_chunks: list[str])`. Verify: `prompt` here is the **raw user query** (not the filled template). The adapter fills the template internally using `{question}=prompt`. This is correct per spec — keep as is.

### T006 — OllamaAdapter: async httpx pattern
Existing `backend/api/routes/query.py` uses `httpx` via `httpx.AsyncClient` (imported in requirements). The pattern for context manager:
```python
async with httpx.AsyncClient() as client:
    resp = await client.post(url, json=body, timeout=5.0)
    resp.raise_for_status()
```
`raise_for_status()` raises `httpx.HTTPStatusError` — catch all `Exception` and re-raise as `LLMError`.

### T009 — factory.py: key difference from TokenizerFactory
`TokenizerFactory.get(lang)` takes a parameter. `LLMProviderFactory.get()` takes no parameter — reads `LLM_PROVIDER` internally. The `_instances` dict is still keyed by provider name string (for singleton-per-provider). Double-checked locking pattern is identical.

### T014 — query.py: keep `request_id` in new QueryResponse
`test_request_id_in_response` (L186 in test_query_rbac.py) asserts `request_id` in response body. New `QueryResponse` must retain `request_id: str`. This is not in the spec task definition but is required to avoid breaking the existing test suite. Add to new `QueryResponse`:
```python
class QueryResponse(BaseModel):
    request_id: str          # retained — R005 traceability
    answer: str | None
    sources: list[str]
    low_confidence: bool
    reason: str | None = None
```

### T014 — TOUCH list correction (from task file)
Task file says: MODIFY `tests/api/test_query_route.py`. **Correction**: that file doesn't exist.
- CREATE `tests/api/test_query_route.py` — new LLM-path tests (happy path, NoRelevantChunks, low_confidence)
- MODIFY `tests/api/test_query_rbac.py` — update 4 broken assertions (L85, L103, L119, L133) to match new response shape

---

## Token Budget
| Story | Tasks | Est. implementation tokens |
|-------|-------|---------------------------|
| S001 | T001–T004 | ~2k |
| S002 | T005–T008 | ~5k |
| S003 | T009–T010 | ~2k |
| S004 | T011–T012 | ~2.5k |
| Post-G3 | T013–T014 | ~3k |
| **Total** | **14 tasks** | **~14.5k** |

---

## Implementation Order (confirmed safe)

```
Session 1 — Sequential:
  T001 (exceptions.py)
  T002 + T003 (base.py + __init__ stub) — parallel
  T004 (TestLLMBase complete)
  T005 (prompts + requirements)
  T006 + T007 + T008 (3 adapters) — parallel

Session 2 — Parallel then sequential:
  T009 (factory.py) ∥ T011 (TestAnswerGate)
  T010 (exports) — after T009
  T012 (coverage sweep) — after T011
  T013 (generator.py) — after T009/T010
  T014 (query.py + test updates) — after T013
```
