# Plan: embed-model-migration
Created: 2026-04-28 | Based on spec: v1 (DRAFT 2026-04-27) | Checklist: PASS (2026-04-28, 0 blockers / 1 WARN auto-approved)

---

## LAYER 1 — Plan Summary

| Field | Value |
|-------|-------|
| Total stories | 5 |
| Sessions estimated | 2 |
| Critical path | S001 → (S002 ∥ S003) → S005 |
| Token budget total | ~14k tokens |
| Sprint slot | In-progress (HOT.md, P0) |

### Parallel Execution Groups
```
G1 (start immediately, run together):
  S001 — rag-agent  — OllamaEmbedder refactor (query/passage prefix + batch)
  S004 — ops         — Truncate script + AWS Ollama Modelfile + license doc
                         (no code dependency on S001 — script + docs only)

G2 (after S001 lands):
  S002 — api-agent   — Wire ingest path → batch_embed_passage
  S003 — rag-agent   — Wire query path → embed_query
    Note: S002 and S003 touch disjoint files
    (backend/api/routes/documents.py vs backend/rag/retriever.py)
    → parallel-safe within G2.

G3 (after G2 + S004 complete — needs ingested data + working pipeline):
  S005 — rag-agent   — Eval harness + 120-query fixtures + recall@10 report
```

### Agent Assignments
| Agent | Stories | Can start |
|-------|---------|-----------|
| rag-agent | S001, S003, S005 | S001 immediately; S003 after S001; S005 after S002+S003+S004 |
| api-agent | S002 | after S001 (needs `batch_embed_passage` API) |
| ops | S004 | immediately (independent of code changes) |
| db-agent | — (S004 truncate script uses SQLAlchemy text() — owned by ops) | N/A |
| auth-agent | — | N/A |
| frontend-agent | — | N/A (out of scope, spec §Out of Scope) |

### Critical Path Reasoning
- S001 unblocks both S002 and S003 (they call the new embedder API).
- S004 has no code coupling — can run any time before S005's eval data load.
- S005 must wait for S002 (ingest path → so DB has E5-prefixed vectors) AND S003 (query path → so retrieval uses matching `query: ` prefix); without both, recall numbers are noise.
- S001 → (S002 ∥ S003) → S005 is the binding chain. S004 sits parallel.

### Risk
| Risk | Mitigation |
|------|------------|
| llama.cpp GGUF convert fails or produces wrong dim | S004 AC5: smoke-test `curl /api/embeddings` returns 1024-float array before declaring done |
| Removing `embed_one`/`batch_embed` (S001 AC5) breaks an unseen caller | Pre-flight grep before S001 implementation; spec assumption is "test data truncated, no stable callers" — verify in /tasks analysis |
| E5 recall@10 misses 0.6 absolute bar (D09) | S005 produces report; if miss, D09 says defer to feature #30+ (BGE-M3) — not a blocker for shipping the migration itself, only the eval verdict |
| Prefix counted twice (e.g. caller already prepends) | S001 AC2/AC3 — prefix applied **inside** embedder; S002/S003 callers must pass raw text. Enforce in /reviewcode |
| Truncation (1400 chars) cuts off real content after prefix prepended | S001 AC6 — prefix counts toward limit; document in unit test |

### Token Budget per Story
| Story | Est. tokens |
|-------|-------------|
| S001 | ~3k (refactor + 7 ACs of unit tests) |
| S002 | ~2k (one-line caller swap + integration test) |
| S003 | ~2k (one-line caller swap + smoke test) |
| S004 | ~3k (script + 2 ops docs + smoke verification) |
| S005 | ~4k (harness + 120 fixtures + report generation) |
| **Total** | **~14k** |

---

## LAYER 2 — Story Plans

### S001: OllamaEmbedder refactor — query/passage prefix + batch variants
**Agent**: rag-agent
**Parallel group**: G1
**Depends on**: none
**Spec reference**: spec.md §S001 (AC1–AC7)

**Files**
| Action | Path |
|--------|------|
| MODIFY | [backend/rag/embedder.py](backend/rag/embedder.py) |
| MODIFY | [backend/rag/tests/test_embedder.py](backend/rag/tests/test_embedder.py) |
| MODIFY | [.env.example](.env.example) (default `EMBEDDING_MODEL=multilingual-e5-large`) |

**Subagent dispatch**: YES (self-contained — only embedder.py + its tests)
**Est. tokens**: ~3k
**Test entry**: `pytest backend/rag/tests/test_embedder.py -v`

**Story-specific notes**
- Split `embed_one` → `embed_query` (prepend `"query: "`) + `embed_passage` (prepend `"passage: "`).
- Replace `batch_embed` → `batch_embed_passage(chunks, batch_size=32)`. Preserve order. Use `asyncio.gather` per batch (P002).
- Truncation order: prefix FIRST, then truncate to `OLLAMA_MAX_EMBED_CHARS=1400` — prefix consumes part of the budget (AC6).
- Remove old `embed_one` / `batch_embed` outright — no shim (AC5).
- `.env.example` default flips to `multilingual-e5-large`; rollback by setting env to `mxbai-embed-large`.

**Outputs expected**
- [ ] `embed_query(text) -> list[float]` (len 1024) with `query: ` prefix
- [ ] `embed_passage(text) -> list[float]` (len 1024) with `passage: ` prefix
- [ ] `batch_embed_passage(chunks, batch_size=32)` preserving order
- [ ] Old methods removed; `EMBEDDING_MODEL` default updated
- [ ] 7 ACs covered in unit tests (prefix, dim, order, truncation, error path)

---

### S002: Wire ingest path to `batch_embed_passage`
**Agent**: api-agent
**Parallel group**: G2 (after S001)
**Depends on**: S001
**Spec reference**: spec.md §S002 (AC1–AC5)

**Files**
| Action | Path |
|--------|------|
| MODIFY | [backend/api/routes/documents.py](backend/api/routes/documents.py) |
| MODIFY | (test file for documents ingestion — confirm path in /tasks /analyze) |

**Subagent dispatch**: YES (small surface, one caller change)
**Est. tokens**: ~2k
**Test entry**: `pytest backend/api/tests/test_documents.py -v` (path confirmed in /analyze)

**Story-specific notes**
- Single call-site change: `embedder.batch_embed(chunks)` → `embedder.batch_embed_passage(chunks)`.
- `insert_embeddings(...)` body untouched (S002 AC2).
- Integration test must ingest a JA/EN/VI/KO fixture set and assert `embeddings.lang` populated and `vector` dim=1024.
- A001: api-agent does NOT touch `backend/db/` directly — go through existing `insert_embeddings` helper.
- R002 (no PII in metadata) and P002/P004 (batch + no N+1) preserved by reusing existing helper.

**Outputs expected**
- [ ] Ingest caller switched to `batch_embed_passage`
- [ ] 4-language fixture ingest passes integration test
- [ ] Stored vector dim = 1024 verified in test
- [ ] No regression in existing documents.py tests

---

### S003: Wire query path to `embed_query`
**Agent**: rag-agent
**Parallel group**: G2 (after S001)
**Depends on**: S001
**Spec reference**: spec.md §S003 (AC1–AC5)

**Files**
| Action | Path |
|--------|------|
| MODIFY | [backend/rag/retriever.py](backend/rag/retriever.py) (`_dense_search`) |
| MODIFY | (retriever test file — confirm path in /tasks /analyze) |

**Subagent dispatch**: YES
**Est. tokens**: ~2k
**Test entry**: `pytest backend/rag/tests/test_retriever.py -v`

**Story-specific notes**
- `_dense_search` swaps to `embedder.embed_query(query_text)` — prefix applied internally.
- Hybrid weights stay env-driven (`RAG_DENSE_WEIGHT=0.7`, `RAG_BM25_WEIGHT=0.3`) per A004 — do NOT hardcode.
- HNSW cosine ANN (m=16, ef=64) untouched.
- Cross-lingual smoke test (AC4): query `"検索する方法"` → expect ≥1 EN doc about "search guide" in top-10.
- Latency check (AC5, P001): query-time embedding p95 < 400ms on `t3.medium`. Add timing log or test marker.
- R007 budget: total /v1/query p95 < 2000ms — embedding is one of several stages; respect existing 1800ms hard timeout.

**Outputs expected**
- [ ] `_dense_search` uses `embed_query`
- [ ] Cross-lingual smoke test passes
- [ ] No regression in BM25 path or hybrid scoring tests
- [ ] Latency assertion or telemetry hook in place

---

### S004: Truncate-and-reset script + AWS Ollama Modelfile setup
**Agent**: ops
**Parallel group**: G1 (independent of code)
**Depends on**: none
**Spec reference**: spec.md §S004 (AC1–AC6)

**Files**
| Action | Path |
|--------|------|
| CREATE | [scripts/truncate_and_reset.py](scripts/truncate_and_reset.py) |
| CREATE | [docs/embed-model-migration/ops/ollama_setup.md](docs/embed-model-migration/ops/ollama_setup.md) |
| CREATE | [docs/embed-model-migration/ops/license.md](docs/embed-model-migration/ops/license.md) |
| MODIFY | [.env.example](.env.example) (also touched by S001 — coordinate; S001 sets default, S004 documents) |

**Subagent dispatch**: YES (docs + script, no shared code surface with S001–S003)
**Est. tokens**: ~3k
**Test entry**: Manual — `python scripts/truncate_and_reset.py --confirm` on dev DB; `curl POST :11434/api/embeddings` smoke (AC5)

**Story-specific notes**
- Truncate script uses SQLAlchemy `text()` with named params — **no f-string SQL** (S001 SQL-injection rule + R001-style discipline). `TRUNCATE embeddings, documents CASCADE` + sequence reset.
- `--confirm` flag mandatory (AC1). Idempotent (AC2). Log row counts before/after.
- Ollama setup doc covers: AWS `t3.medium` provisioning, Ollama install, **llama.cpp convert** (`python convert-hf-to-gguf.py intfloat/multilingual-e5-large --outtype q4_k_m`), Modelfile, `ollama create`, env vars (D08).
- License doc records: HF model URL, MIT license text reference, GGUF source = self-converted, distribution policy, GGUF checksum (D04).
- `.env.example` flip is shared with S001 — ensure single canonical value `EMBEDDING_MODEL=multilingual-e5-large`. If both stories touch `.env.example`, S001 lands first; S004 confirms.

**Outputs expected**
- [ ] Idempotent truncate script with `--confirm` gate
- [ ] Ops setup doc with full provisioning + convert steps
- [ ] License doc with checksum
- [ ] Smoke `curl` returns 1024-float array on fresh box

---

### S005: Multilingual recall@10 evaluation harness + 120-query fixtures
**Agent**: rag-agent
**Parallel group**: G3 (after S002 + S003 + S004)
**Depends on**: S002 (ingest stores E5 passages), S003 (query uses E5 prefix), S004 (DB reset to clean state)
**Spec reference**: spec.md §S005 (AC1–AC7)

**Files**
| Action | Path |
|--------|------|
| CREATE | [backend/rag/eval/multilingual_recall.py](backend/rag/eval/multilingual_recall.py) |
| CREATE | [backend/rag/eval/multilingual_recall.fixtures.json](backend/rag/eval/multilingual_recall.fixtures.json) |
| CREATE | [docs/embed-model-migration/reports/recall_e5.md](docs/embed-model-migration/reports/recall_e5.md) |

**Subagent dispatch**: PARTIAL — fixture generation can be subagent (Claude synthesizes from test docs per D07); harness coding is rag-agent main thread for tighter feedback loop.
**Est. tokens**: ~4k
**Test entry**: `python -m backend.rag.eval.multilingual_recall --model multilingual-e5-large`

**Story-specific notes**
- Fixtures: 120 entries = 30 × {JA, EN, VI, KO}. Schema: `{id, query, query_lang, expected_doc_ids[], category}` where category ∈ `{mono, cross-lingual, multi-intent}` (AC1).
- Cross-lingual subset ~25% (~30 entries), pairs: VI→EN, JA→EN, KO→EN, EN→JA (AC2).
- Per D07: Claude synthesizes queries from S002 fixture ingest set; lb_mui reviews pass/fail at end.
- Per D09: pass bar is **absolute** recall@10 ≥ 0.6 overall, ≥ 0.5 cross-lingual subset. No mxbai baseline.
- Harness computes recall@10 + MRR per language and per category. Output markdown report at `docs/embed-model-migration/reports/recall_e5.md` (AC4).
- AC7 traceability: every `expected_doc_ids` must reference a doc actually present in the test ingest — verify before writing fixtures.

**Outputs expected**
- [ ] 120-query fixture JSON, schema-valid, traceable to ingested docs
- [ ] Eval harness CLI (`--model` flag plumbed via env override)
- [ ] Recall report markdown with per-lang + per-category numbers
- [ ] Pass/fail verdict against D09 thresholds (0.6 / 0.5)

---

## LAYER 3 — Cross-Story Hazards & Coordination

| Hazard | Stories | Coordination |
|--------|---------|--------------|
| `.env.example` shared edit | S001, S004 | S001 lands the default flip; S004 only documents in setup doc — do NOT re-edit if S001 already set the value |
| `OllamaEmbedder` API surface | S001 (defines), S002 (consumes), S003 (consumes), S005 (consumes via retriever) | S001 must merge before G2 dispatches — gate explicitly |
| DB state | S004 (truncates), S002 (ingests), S005 (reads) | Order: S004 truncate → S002 ingest fixtures → S005 eval |
| HOT.md "In Progress" slot | embed-model-migration is already listed | Update HOT.md "Recent Decisions" with plan-locked decisions D-EM-* if any new ones surface in /tasks |

---

## Plan Approval Gate
- Spec status: DRAFT (acceptable per checklist PASS)
- Checklist: PASS 2026-04-28 (0 blockers, 1 WARN auto-approved)
- Plan ready for: `/tasks embed-model-migration <story>` per story

---
