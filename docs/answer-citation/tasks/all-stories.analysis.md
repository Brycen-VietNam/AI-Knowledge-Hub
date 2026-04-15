# Analysis: answer-citation — All Stories (S001–S005)
Generated: 2026-04-14 | Depth: shallow | Files scanned: 9

---

## Code Map (per story)

### S001 — DB Migration + RetrievedDocument Enrichment

**`backend/db/migrations/`** — last migration: `006_add_document_status_and_chunk_text.sql`
- Next file: `007_add_source_url.sql` (does NOT exist yet — must be created)

**`backend/db/models/document.py`**
```python
class Document(Base):
    id: Mapped[uuid.UUID]
    title: Mapped[str]           # NOT NULL — title already exists ✅
    lang: Mapped[str]            # CHAR(2), NOT NULL — no NULL risk for T001 pre-check
    user_group_id: Mapped[Optional[int]]
    created_at / updated_at / content_fts / status
    # source_url: MISSING — T002+T003 must add
```
- `source_url` column: absent from ORM and schema → migration 007 is genuinely new.
- `lang` is `NOT NULL` in ORM (CHAR(2), nullable=False) — T001 pre-check (`WHERE lang IS NULL`) will return 0 on clean installs. `d.lang or "und"` fallback in T004 is defensive-only.

**`backend/rag/retriever.py`**
```python
@dataclass
class RetrievedDocument:
    doc_id: uuid.UUID
    chunk_index: int
    score: float
    user_group_id: int | None
    content: str | None = None
    # title, lang, source_url: MISSING — T004 must add

async def _dense_search(session, query_embedding, user_group_ids, top_k):
    # SELECT e.doc_id, e.chunk_index, e.user_group_id, e.text, distance
    # FROM embeddings e
    # WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)
    # No JOIN to documents — T005 must add INNER JOIN + 3 SELECT columns

async def _bm25_search(session, bm25_query, user_group_ids, top_k):
    # SELECT d.id AS doc_id, 0 AS chunk_index, d.user_group_id, ts_rank(...)
    # FROM documents d
    # WHERE RBAC + FTS
    # Already JOINs documents — T005 must add d.title, d.lang, d.source_url

def _merge(dense, bm25, top_k):
    # Uses: RetrievedDocument(**{**vars(all_docs[did]), "score": scores[did]})
    # ✅ spread pattern is generic — new fields auto-propagated, no _merge change needed
```

---

### S002 — CitationObject Model + QueryResponse Extension

**`backend/api/models/`** — directory is EMPTY (no `__init__.py`, no files)
- `citation.py` must be CREATED (T001).
- `backend/api/models/__init__.py` must be CREATED if absent.

**`backend/api/routes/query.py`**
```python
class QueryResponse(BaseModel):
    request_id: str
    answer: str | None
    sources: list[str]       # ← must remain unchanged (D-CIT-01 additive)
    low_confidence: bool
    reason: str | None = None
    # citations: MISSING — T002 must add

# Call site (L217–223):
return QueryResponse(
    request_id=request_id,
    answer=llm_response.answer,
    sources=[str(d.doc_id) for d in docs],
    low_confidence=llm_response.confidence < _LOW_CONFIDENCE_THRESHOLD,
    reason=None,
)
# doc_titles, citations build: MISSING — S002-T002 + S003-T006 must add

# generate_answer() call (L191–196):
llm_response = await asyncio.wait_for(
    generate_answer(query=body.query, chunks=[d.content for d in docs if d.content]),
    timeout=_LLM_TIMEOUT,
)
# doc_titles not passed → S003-T006 must update this call
```

---

### S003 — LLM Prompt Engineering

**`backend/rag/llm/base.py`**
```python
@dataclass
class LLMResponse:
    answer: str
    sources: list[str]   # ← DELETE per D-CIT-09 (GAP-1 resolved)
    confidence: float
    provider: str
    model: str
    low_confidence: bool
    # inline_markers_present: MISSING — T001 must add

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse:
        # doc_titles: MISSING — T002 must add to signature
```

**`backend/rag/llm/ollama.py`** — `OllamaAdapter.complete()` L26
- Uses `{context}` placeholder (old format) — T004 must switch to `{sources_index}`.
- `sources=context_chunks` in `LLMResponse(...)` L47 — must remove (D-CIT-09).
- `confidence=0.9` sentinel hardcoded — BACKLOG-2 (out of scope now).

**`backend/rag/llm/claude.py`** — `ClaudeAdapter.complete()` L23
- Same `{context}` placeholder + `sources=context_chunks` — T006 must fix both.

**`backend/rag/llm/openai.py`** — `OpenAIAdapter.complete()` L27
- Same `{context}` placeholder + `sources=context_chunks` — T005 must fix both.

**`backend/rag/llm/prompts/answer.txt`** — current content:
```
Given the following context documents, answer the question accurately and concisely.
Cite the source document IDs in your answer.

Context:
{context}

Question:
{question}

Answer:
```
- T003 must replace `{context}` with `{sources_index}` and add `[N]` marker instruction.
- `{context}` placeholder referenced in all 3 adapters — must be renamed in sync with T003.

**`backend/rag/generator.py`**
```python
async def generate_answer(query: str, chunks: list[str]) -> LLMResponse:
    provider = LLMProviderFactory.get()
    return await provider.complete(query, chunks)
# doc_titles: MISSING — S003-T006 must add to signature + pass through
```

---

### S004 — Consumer Rendering Contract (Documentation)

**`docs/query-endpoint/api-reference.md`** — exists. T002 adds 1 link line.
**`docs/answer-citation/citation-rendering-contract.md`** — does NOT exist. T001 creates it.

No code changes — documentation only.

---

### S005 — Tests and Coverage

**Test files that must be extended/created:**
- `tests/api/test_citation.py` — does NOT exist (S002-T001 creates skeleton; S005-T001 completes it)
- `tests/api/test_query.py` — exists (extend with AC9–AC11)
- `tests/rag/test_generator.py` — exists (extend with AC5–AC8 + GAP-2 OOB test)
- `tests/rag/test_retriever_rbac.py` — exists (extend with AC12 enrichment test)

Coverage targets (AC13):
- `backend/api/models/citation.py` → 100%
- `backend/api/routes/query.py` → ≥ 80%
- `backend/rag/generator.py` → ≥ 80%
- `backend/rag/retriever.py` → ≥ 80%

---

## Patterns to Follow

| Pattern | Location | Use in |
|---------|----------|--------|
| `text().bindparams()` SQL style | [retriever.py:41-52](backend/rag/retriever.py#L41) | S001-T005 INNER JOIN |
| RBAC `ANY(:group_ids)` WHERE | [retriever.py:44](backend/rag/retriever.py#L44) | S001-T005: must remain unchanged |
| `**{**vars(doc), "score": x}` spread | [retriever.py:113](backend/rag/retriever.py#L113) | S001-T005: no _merge change needed |
| `Mapped[str \| None] = mapped_column(Text, nullable=True)` | [document.py:24](backend/db/models/document.py#L24) `content_fts` | S001-T003 `source_url` field |
| `Field(default_factory=list)` | — | S002-T002 `citations` field |
| `from .base import LLMProvider, LLMResponse` | [ollama.py:7](backend/rag/llm/ollama.py#L7) | S003 adapters already import correctly |
| Lazy `import anthropic` | [claude.py:31](backend/rag/llm/claude.py#L31) | Keep — do not hoist to module level |
| Auth fixtures from conftest | existing tests | S005 — reuse, do not duplicate |

---

## Conflicts & Gaps Found

### ❌ CRITICAL — `{context}` placeholder mismatch (S003-T003/T004/T005/T006)
**All 3 adapters** use `_PROMPT_TEMPLATE.format(context=..., question=...)`.
T003 renames placeholder to `{sources_index}`. T004/T005/T006 must switch to
`format(sources_index=..., question=...)` **in the same PR** — if done out of order,
any adapter will `KeyError` at runtime.
**Fix order**: T003 (template) → T004, T005, T006 in parallel (all format calls updated).

### ❌ CRITICAL — `LLMResponse.sources` in all 3 adapters (S003-T001)
[base.py:10](backend/rag/llm/base.py#L10): `sources: list[str]` must be deleted (D-CIT-09).
Adapter instantiation sites:
- [ollama.py:48](backend/rag/llm/ollama.py#L48): `sources=context_chunks` → **remove**
- [claude.py:44](backend/rag/llm/claude.py#L44): `sources=context_chunks` → **remove**
- [openai.py:52](backend/rag/llm/openai.py#L52): `sources=context_chunks` → **remove**
T001 must handle base.py + all 3 adapter sites atomically.

### ⚠️ WARN — `backend/api/models/` directory is empty
No `__init__.py` exists. S002-T001 must create both `citation.py` AND `__init__.py`.
If `__init__.py` is missing, `from backend.api.models.citation import CitationObject` will still
work (Python 3.3+ namespace packages), but explicit `__init__.py` matches project convention.

### ⚠️ WARN — `_bm25_search` returns `chunk_index=0` hardcoded ([retriever.py:76](backend/rag/retriever.py#L76))
BM25 queries `documents` table (no `embeddings` join) so chunk_index is unavailable.
`chunk_index=0` is intentional — no fix needed, but test for AC12 should assert `chunk_index >= 0`
not `chunk_index == real_value` for the BM25 path.

### ⚠️ WARN — `generate_answer()` signature must change in two places (S003-T006)
1. [generator.py:7](backend/rag/generator.py#L7): `generate_answer(query, chunks)` → add `doc_titles`
2. [query.py:192](backend/api/routes/query.py#L192): call site must pass `doc_titles=[d.title or "" for d in docs if d.content]`
The `if d.content` filter on `docs` means `doc_titles` and `chunks` must be built from the
**same filtered list** to keep indices aligned. Risk: length mismatch if built separately.
**Fix**: build once: `content_docs = [d for d in docs if d.content]`, then derive both lists.

### ⚠️ INFO — `Document.lang` is `NOT NULL` in ORM
[document.py:20](backend/db/models/document.py#L20): `nullable=False` → T001 pre-check will
return count=0 on any clean install. The `d.lang or "und"` fallback in T004 is defensive only
and should remain (future proofing), but no migration blocker.

### ⚠️ INFO — BACKLOG-2 sentinel `confidence=0.9` in Ollama + Claude (out of scope)
[ollama.py:49](backend/rag/llm/ollama.py#L49), [claude.py:46](backend/rag/llm/claude.py#L46):
`low_confidence` never triggers for these providers. Deferred to feature `confidence-scoring`.
Do NOT fix in this feature.

---

## RBAC Verification

R001 compliant in current code — INNER JOIN in `_dense_search` (S001-T005) must be added
**after** the existing WHERE clause, not replacing it:
```sql
-- CORRECT addition for _dense_search:
SELECT e.doc_id, e.chunk_index, e.user_group_id, e.text,
       d.title, d.lang, d.source_url,          -- ADD
       e.embedding <-> cast(:query_vec AS vector) AS distance
FROM embeddings e
INNER JOIN documents d ON d.id = e.doc_id      -- ADD
WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)
ORDER BY distance
LIMIT :top_k
```
RBAC filter (`e.user_group_id`) stays on `embeddings` table — not `documents.user_group_id`.
This is correct per D02: dense filter on embeddings, BM25 filter on documents.

---

## Recommended Implementation Order

| Phase | Tasks | Parallel? | Notes |
|-------|-------|-----------|-------|
| 1 | S001-T001 | solo | Pre-check comment only |
| 2 | S001-T002, S001-T003 | ✅ parallel | DDL + ORM |
| 3 | S001-T004 | after T002+T003 | RetrievedDocument fields |
| 4 | S001-T005 | after T004 | Retriever SQL + test |
| 5 | S002-T001, S003-T001 | ✅ parallel | CitationObject + LLMResponse fix |
| 6 | S002-T002, S003-T002, S003-T003 | ✅ parallel | QueryResponse + abstract sig + prompt template |
| 7 | S003-T004, S003-T005, S003-T006 | ✅ parallel | All 3 adapters + generator + query.py |
| 8 | S002-T003 | after S002-T002 | Citation tests AC1–AC4, AC10 |
| 9 | S004-T001, S004-T002 | ✅ parallel | Docs only |
| 10 | S005-T001–T004 | ✅ parallel | All test extensions |
| 11 | S005-T005 | after T001–T004 | Coverage gate |

---

## Token budget
Files scanned: 9 source files + 5 task files + WARM memory
Analysis saved: `docs/answer-citation/tasks/all-stories.analysis.md`
