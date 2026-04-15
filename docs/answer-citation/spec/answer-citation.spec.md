# Spec: answer-citation
Created: 2026-04-14 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | query-endpoint |
| Priority | P1 |
| Story count | 5 |
| Token budget est. | ~5k |
| Critical path | S001 → S002 → S003 → S005 |
| Parallel-safe stories | S003 ‖ S004 (both after S002) |
| Blocking specs | — |
| Blocked by | query-endpoint (DONE ✅) |
| Agents needed | db-agent (S001 migration), api-agent (S002), rag-agent (S003), api-agent (S005) |

### Problem Statement
`/v1/query` returns `sources: list[str]` (opaque doc_ids) and plain-text `answer` with no inline attribution markers. Consumers (Web SPA, Teams bot, Slack bot) cannot render clickable citations without a separate API call that does not exist. Constitution C014 mandates source citation — the current implementation satisfies it technically but not practically.

### Solution Summary
- Add `source_url TEXT NULL` to `documents` table (migration 007) — prerequisite for CitationObject
- Enrich `_dense_search()` and `_bm25_search()` to JOIN `documents` and return `title`, `lang`, `source_url` — zero extra round-trips (SLA safe)
- Define `CitationObject` Pydantic model; add `citations: list[CitationObject]` to `QueryResponse` alongside existing `sources: list[str]` (Option C — additive, no breaking change)
- Update LLM prompt to number sources as `[N]` index and instruct model to emit inline markers; graceful fallback if model omits them
- Extend `generate_answer(query, chunks, doc_titles)` and `LLMProvider.complete()` to accept titles for prompt index construction

### Out of Scope
- Streaming citation markers (SSE / WebSocket)
- Citation anchors within multi-paragraph answers (`[1:3]` notation)
- Consumer-side rendering implementation (Web SPA, Teams bot, Slack bot)
- RTL layout or CJK rendering logic in any frontend
- Retroactive `source_url` population for existing documents
- Storing generated answers or citation lists in DB
- Any change to the audit log schema

---

## LAYER 2 — Story Detail

---

### S001: DB Migration + RetrievedDocument Enrichment

**Role / Want / Value**
- As a: platform operator
- I want: each retrieved document chunk to carry `title`, `lang`, and `source_url` from the `documents` table, fetched in the same retrieval query
- So that: the API layer can build CitationObject without any extra DB round-trip, staying within the R007 SLA budget

**Acceptance Criteria**
- [ ] AC1: Migration `backend/db/migrations/007_add_source_url.sql` adds `source_url TEXT NULL` to `documents`. No NOT NULL constraint, no default. Existing rows unaffected. Rollback section included.
- [ ] AC2: `Document` ORM (`backend/db/models/document.py`) gains `source_url: Mapped[str | None] = mapped_column(Text(), nullable=True)`.
- [ ] AC3: `RetrievedDocument` dataclass gains three optional fields with defaults: `title: str | None = None`, `source_url: str | None = None`, `lang: str | None = None`. Existing callers that omit these fields continue to work.
- [ ] AC4: `_dense_search()` adds `INNER JOIN documents d ON d.id = e.doc_id` and SELECTs `d.title, d.lang, d.source_url`. All three fields are set on returned `RetrievedDocument` instances.
- [ ] AC5: `_bm25_search()` already queries `documents d`; it must also SELECT `d.title, d.lang, d.source_url` and populate the new `RetrievedDocument` fields.
- [ ] AC6: `_merge()` propagates `title`, `lang`, `source_url` via the existing `**vars(all_docs[did])` spread. A test must verify all three new fields survive the merge.
- [ ] AC7: No additional SQL queries are issued per `search()` call. Enrichment happens entirely within the existing `_dense_search` and `_bm25_search` queries.
- [ ] AC8: R002 compliance — `title`, `source_url`, `lang` are non-PII document metadata. No user identity, email, IP, or query text stored.

**DB Contract**
```sql
-- backend/db/migrations/007_add_source_url.sql
ALTER TABLE documents ADD COLUMN source_url TEXT NULL;
-- ROLLBACK: ALTER TABLE documents DROP COLUMN source_url;
```

**Revised `_dense_search` SQL shape (illustrative):**
```sql
SELECT e.doc_id, e.chunk_index, e.user_group_id, e.text,
       e.embedding <-> cast(:query_vec AS vector) AS distance,
       d.title, d.lang, d.source_url
FROM embeddings e
INNER JOIN documents d ON d.id = e.doc_id
WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)
ORDER BY distance
LIMIT :top_k
```

**Auth Requirement**
- [x] Both (inherited from retrieval pipeline — no auth change)

**Non-functional**
- Latency: INNER JOIN on `documents.id` PK index is a nested loop scan. Expected overhead < 5ms p95 at top_k=100. Must stay within the 1.0s retrieval timeout.
- Audit log: not required (no change to retrieval audit behavior)
- CJK support: not applicable (metadata enrichment only)

**Implementation notes**
- `_bm25_search` already queries `documents d` — just add SELECT columns. No structural change.
- `_dense_search` needs JOIN added — verify `e.doc_id` FK matches `d.id` PK.
- Migration is zero-downtime: adding a nullable column with no constraint is safe in PostgreSQL.

---

### S002: CitationObject Model + QueryResponse Extension

**Role / Want / Value**
- As a: consumer developer (Web SPA, Teams bot, Slack bot)
- I want: a structured `citations` array in the `/v1/query` response with doc_id, title, source_url, chunk_index, score, and lang
- So that: I can render clickable attributed citations without a separate API call and without reverse-engineering opaque doc_ids

**Acceptance Criteria**
- [ ] AC1: New file `backend/api/models/citation.py` defines `CitationObject` Pydantic model with exactly the fields in the API contract below. No extra fields (R002).
- [ ] AC2: `QueryResponse` in `backend/api/routes/query.py` gains `citations: list[CitationObject] = Field(default_factory=list)`. The existing `sources: list[str]` field is NOT removed or renamed.
- [ ] AC3: When the query succeeds (answer non-null), `citations` is populated from the `RetrievedDocument` list returned by `search()`. Each `RetrievedDocument` produces exactly one `CitationObject`. Ordering matches `sources` — both are ordered by hybrid score descending (existing `_merge()` ordering).
- [ ] AC4: `citations` mirrors `sources` exactly — all retrieved docs are included regardless of score. No score filter. Consumers decide what to display.
- [ ] AC5: When `answer` is null (NoRelevantChunksError or low_confidence path returning null), `citations` is `[]` — never null.
- [ ] AC6: `CitationObject.score` is the hybrid score from `RetrievedDocument.score`, rounded to 4 decimal places.
- [ ] AC7: `CitationObject.source_url` is `null` when the document has no URL. Consumers must handle null.
- [ ] AC8: `CitationObject.lang` is always the 2-char ISO 639-1 code from `documents.lang`, never null.
- [ ] AC9: R002 — `CitationObject` must not contain: user_id, user_group_id, content/chunk text, email, IP, or query text.
- [ ] AC10: `citations` appears in serialized response even when empty (`[]`), not omitted.

**API Contract**

`CitationObject` (new Pydantic model — `backend/api/models/citation.py`):
```python
class CitationObject(BaseModel):
    doc_id: str          # UUID as string — matches existing sources[] format
    title: str           # from documents.title — always present (NOT NULL)
    source_url: str | None  # from documents.source_url — nullable
    chunk_index: int     # from embeddings.chunk_index
    score: float         # hybrid score, rounded to 4dp
    lang: str            # ISO 639-1 2-char code
```

Full `QueryResponse` after this story:
```json
{
  "request_id": "uuid",
  "answer": "According to [1], annual leave is 14 days. [2] confirms this applies from FY2026.",
  "sources": ["550e8400-...", "661f9511-..."],
  "citations": [
    {
      "doc_id": "550e8400-...",
      "title": "Employee Leave Policy FY2026",
      "source_url": "https://intranet.brysen.local/docs/leave-policy-2026.pdf",
      "chunk_index": 3,
      "score": 0.8712,
      "lang": "ja"
    },
    {
      "doc_id": "661f9511-...",
      "title": "HR Circular 2026-04",
      "source_url": null,
      "chunk_index": 0,
      "score": 0.6234,
      "lang": "ja"
    }
  ],
  "low_confidence": false,
  "reason": null
}
```

**Auth Requirement**
- [x] Both (inherited — no auth change)

**Non-functional**
- Backward compatibility: existing clients reading only `request_id, answer, sources, low_confidence, reason` are unaffected. `citations` is a new additive key.
- `doc_id` serialized as string (not UUID object) to match existing `sources: list[str]` format.

**Implementation notes**
- Call site in `query.py`: `citations=[CitationObject(doc_id=str(d.doc_id), title=d.title or "", source_url=d.source_url, chunk_index=d.chunk_index, score=round(d.score, 4), lang=d.lang or "") for d in docs]`
- Empty list `[]` when `answer is None` path (NoRelevantChunksError).

---

### S003: LLM Prompt Engineering for Inline Citation Markers

**Role / Want / Value**
- As a: user reading a query answer
- I want: the AI answer to contain inline `[N]` markers that correspond to the `citations` array
- So that: I can trace exactly which sentence or claim comes from which source document

**Acceptance Criteria**
- [ ] AC1: `generate_answer()` signature in `backend/rag/generator.py` extended to accept `doc_titles: list[str]` (parallel to `chunks`). Passed to `provider.complete()`.
- [ ] AC2: `LLMProvider.complete()` abstract method in `backend/rag/llm/base.py` extended to accept `doc_titles: list[str]`. All three adapters (Ollama, OpenAI, Claude) updated accordingly.
- [ ] AC3: Prompt template `backend/rag/llm/prompts/answer.txt` updated to present sources as a numbered `[N] title\nchunk_text` index and instruct model to emit `[N]` markers inline. See authoritative template below.
- [ ] AC4: Numbered index is built by each adapter as: `[1] {title_1}\n{chunk_text_1}\n\n[2] {title_2}\n{chunk_text_2}` etc. Title is included so the model can reference the document by name.
- [ ] AC5: Fallback — if model returns answer without any `[N]` markers, answer is used as-is. No error raised, no re-prompt. `citations` still populated from retrieval results. Only inline markers may be absent.
- [ ] AC6: Prompt works for all 5 supported languages (ja, en, vi, ko, zh). Model is instructed to answer in the language of the question. No language is hardcoded (A003).
- [ ] AC7: `LLMResponse` gains `inline_markers_present: bool = False`. Each adapter sets it to `True` if the returned answer contains at least one `\[\d+\]` pattern. Used for observability only — does not affect business logic.
- [ ] AC8: Call site in `query.py` passes `doc_titles=[d.title or "" for d in docs if d.content]` parallel to `chunks=[d.content for d in docs if d.content]`.
- [ ] AC9: `query.py` does NOT parse or validate marker indices from the answer. Marker integrity is the model's responsibility.

**Authoritative prompt template (`backend/rag/llm/prompts/answer.txt`):**
```
You are a multilingual knowledge assistant. Answer the question based ONLY on the numbered source documents provided below. Do not use any external knowledge.

For each claim or piece of information in your answer, insert an inline citation marker [N] where N is the source number (e.g., [1], [2]). Place the marker immediately after the sentence or clause it supports. If a single sentence draws from multiple sources, include all relevant markers (e.g., [1][2]).

Answer in the same language as the question. If the question is in Japanese, answer in Japanese. If in Vietnamese, answer in Vietnamese. And so on.

Sources:
{sources_index}

Question:
{question}

Answer:
```

Where `{sources_index}` is built by each adapter as:
```
[1] {title_1}
{chunk_text_1}

[2] {title_2}
{chunk_text_2}
```

**Updated signatures:**
```python
# generator.py
async def generate_answer(query: str, chunks: list[str], doc_titles: list[str]) -> LLMResponse: ...

# base.py
@abstractmethod
async def complete(self, prompt: str, context_chunks: list[str], doc_titles: list[str]) -> LLMResponse: ...
```

**Auth Requirement**
- [x] Both (inherited — no auth change)

**Non-functional**
- Latency: new prompt is ~80–120 tokens longer. Total context for top_k=10 at ~200 words/chunk ≈ 2000–3000 tokens — well within all three model context windows. LLM timeout (0.8s) unchanged.
- Prompt caching (ClaudeAdapter): stable prefix up to `Sources:` is preserved. `{sources_index}` and `{question}` remain volatile suffix. Cache efficiency intact.
- CJK support: ja / zh / vi / ko — prompt instruction language is English; answer language follows question.

**Implementation notes**
- The `if d.content` filter applied identically to both `chunks` and `doc_titles` to keep lists parallel.
- `LLMResponse.inline_markers_present` is a `bool` field with `field(default=False)` on the dataclass.

---

### S004: Consumer Rendering Contract (Documentation)

**Role / Want / Value**
- As a: consumer developer building Web SPA, Teams bot, or Slack bot
- I want: a clear documented contract for rendering `[N]` markers and the `citations` array
- So that: citation rendering is consistent across all surfaces from day one

**Acceptance Criteria**
- [ ] AC1: Document `docs/answer-citation/citation-rendering-contract.md` produced with `Contract-Version: 1.0` header.
- [ ] AC2: Contract specifies: consumers MUST render `[N]` as a clickable superscript/badge linking to `citations[N-1]` (0-indexed). If N is out of range, render `[N]` as plain text.
- [ ] AC3: Contract specifies: when `low_confidence: true`, consumers SHOULD display a visual warning. No specific UI mandated.
- [ ] AC4: Contract specifies: if `source_url` is non-null, title is a hyperlink. If null, title is plain text. Consumers MUST NOT construct URLs from doc_id.
- [ ] AC5: Contract specifies: `citations[0]` is highest-scoring source. Ordering is by hybrid score descending. `[N]` in answer maps to `citations[N-1]`.
- [ ] AC6: Contract specifies: when `citations: []`, no citation section is rendered. Occurs on null answer and low_confidence-null paths.
- [ ] AC7: Contract specifies: consumers that ignore `citations` and only read `sources` continue to receive valid doc_id strings (backward compat guarantee).
- [ ] AC8: Contract referenced in `docs/query-endpoint/api-reference.md` (add a link).
- [ ] AC9: Contract MUST specify that all consumer implementations are required to use permissive/lenient JSON deserialization — unknown fields in `QueryResponse` MUST be silently ignored. This is a forward-compatibility requirement covering `citations` and any future additive fields.

**Auth Requirement**
- [ ] Not applicable (documentation only)

**Non-functional**
- Documentation only. No code changes.

---

### S005: Tests and Coverage

**Role / Want / Value**
- As a: developer
- I want: unit and integration tests covering CitationObject construction, DB join enrichment, prompt template output, and the full query→citations flow
- So that: regressions in any layer are caught before merge

**Acceptance Criteria**
- [ ] AC1: Unit — `test_citation_object_construction`: `RetrievedDocument` with `title, source_url, lang` → correct `CitationObject` with all fields, `score` rounded to 4dp.
- [ ] AC2: Unit — `test_citation_object_no_source_url`: `source_url=None` → `CitationObject.source_url = null` (not empty string).
- [ ] AC3: Unit — `test_citations_mirror_sources`: all retrieved docs appear in `citations`, count matches `sources` count, ordering identical.
- [ ] AC4: Unit — `test_citations_empty_on_null_answer`: NoRelevantChunksError path → `citations = []`, not null.
- [ ] AC5: Unit — `test_prompt_template_builds_numbered_index`: 3 chunks with titles → `{sources_index}` contains `[1] Title1\nchunk1\n\n[2] Title2\nchunk2...`.
- [ ] AC6: Unit — `test_prompt_template_multilang` (parametrized: `["ja", "en", "vi", "ko", "zh"]`): filled prompt contains question text without multibyte corruption in CJK titles.
- [ ] AC7: Unit — `test_fallback_no_markers`: mocked provider returns answer with no `[N]` markers → route returns 200, answer as-is, `citations` populated, `inline_markers_present = False`.
- [ ] AC8: Unit — `test_inline_markers_present_flag`: answer with `[1]` → `inline_markers_present = True`; answer without → `False`.
- [ ] AC9: Integration — `test_full_query_citations_shape`: mocked `search()` returns `RetrievedDocument` objects with title/lang, mocked `generate_answer()` returns answer with `[1]`. Response has `citations` with correct shape, `sources` unchanged, `answer` contains `[1]`.
- [ ] AC10: Integration — `test_sources_unchanged_after_citation_feature`: `sources` in response remains `list[str]` of UUIDs — not CitationObjects.
- [ ] AC11: Integration — `test_low_confidence_citations_empty`: all docs score < 0.4 → `citations = []`, `sources` populated, `low_confidence = True`.
- [ ] AC12: Unit — `test_retriever_dense_enrichment`: mocked DB rows with `title, lang, source_url` → `RetrievedDocument` objects have all three fields populated.
- [ ] AC13: Coverage — `backend/api/models/citation.py` 100%; `backend/api/routes/query.py` regression (≥80% must not drop); `backend/rag/generator.py` ≥80%; `backend/rag/retriever.py` ≥80%.

**Test file locations:**
- `tests/api/test_citation.py` (NEW) — AC1–AC4, AC9–AC11
- `tests/api/test_query.py` — extend with AC9–AC11
- `tests/rag/test_generator.py` — extend with AC5–AC8
- `tests/rag/test_retriever_rbac.py` — extend with AC12

**Auth Requirement**
- [x] Both (existing test auth fixtures)

**Non-functional**
- Latency: not applicable (unit/integration tests)
- Audit log: not required
- CJK support: AC6 covers all 5 languages

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC8 (migration + enrichment) | Constitution | CONSTITUTION.md C014 | "AI answers must cite ≥1 source with confidence ≥0.4" — enrichment is prerequisite for CitationObject | 2026-03-18 |
| AC4 (dense JOIN) | Existing behavior | `backend/rag/retriever.py:41–63` | `_dense_search` queries `embeddings` only — no JOIN to `documents` today | 2026-04-14 |
| AC5 (BM25 select) | Existing behavior | `backend/rag/retriever.py:66–97` | `_bm25_search` queries `documents d` — `d.title, d.lang` available but not selected | 2026-04-14 |
| AC6 (merge spread) | Existing behavior | `backend/rag/retriever.py:114` | `**vars(all_docs[did])` spread naturally carries new dataclass fields | 2026-04-14 |
| AC8 (R002) | Requirement doc | `HARD.md R002` | "pgvector embedding metadata must only contain: doc_id, lang, user_group_id, created_at" | 2026-04-14 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC10 (CitationObject shape) | Constitution | CONSTITUTION.md C014 | Source citation mandate drives the CitationObject design | 2026-03-18 |
| AC2 (additive Option C) | Conversation | lb_mui, /specify session 2026-04-14 | Chose Option C (add `citations` alongside `sources`) to avoid breaking clients | 2026-04-14 |
| AC4 (no score filter) | Conversation | lb_mui, /specify session 2026-04-14 | `citations` mirrors `sources` exactly — consumers decide what to display | 2026-04-14 |
| AC9 (R002) | Requirement doc | `HARD.md R002` | No PII in citation objects | 2026-04-14 |

### S003 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC9 (prompt + markers) | Constitution | CONSTITUTION.md C014 | Source citation mandate; existing prompt ("Cite the source document IDs") produces unreliable results | 2026-04-14 |
| AC3 (prompt template) | Existing behavior | `backend/rag/llm/prompts/answer.txt` | Current prompt uses `{context}` (raw chunks) with no numbered index and no `[N]` instruction | 2026-04-14 |
| AC6 (multilingual) | Requirement doc | `CLAUDE.md`, `ARCH.md A003` | "Never hardcode lang='en' as fallback. Response language = detected query language." | 2026-04-14 |
| AC5 (fallback) | Business logic | SDD convention | Graceful degradation — model compliance is probabilistic; hard failure would break all citations | 2026-04-14 |

### S004 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC8 (rendering contract) | Business logic | Consumer team requirement | SPA, Teams bot, Slack bot need consistent citation rendering; no existing contract exists | 2026-04-14 |

### S005 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC13 (tests) | Requirement doc | `CLAUDE.md` team conventions | "≥80% test coverage" team standard; existing test patterns in `tests/api/test_query.py` | 2026-04-14 |

---

## Assumptions

| ID | Assumption | Status |
|----|------------|--------|
| A01 | `source_url NULL` for existing docs is acceptable | Open — confirm before /plan |
| A02 | `generate_answer()` has only 1 caller (`query.py`) — sig change safe | Confirmed by grep (2026-04-14) |
| A03 | Ollama/Llama produces `[N]` markers reliably enough; fallback sufficient | Open — confirm with team |
| A04 | All consumers use lenient JSON parsing (unknown keys OK) | Open — confirm before merge |
| A05 | `citations` mirrors `sources` exactly — no score filter | Confirmed by lb_mui 2026-04-14 |
| A06 | `documents.title` is always non-null | Confirmed: `nullable=False` in ORM (2026-04-14) |
