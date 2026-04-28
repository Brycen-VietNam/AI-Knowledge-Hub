# Spec: embed-model-migration
Created: 2026-04-27 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | rag |
| Priority | P0 |
| Story count | 5 |
| Token budget est. | ~6k |
| Critical path | S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S004 (ops/infra) parallel with S001–S003 |
| Blocking specs | — |
| Blocked by | — |
| Agents needed | rag-agent, db-agent (truncate script), ops |

### Problem Statement
Current dense embedder `mxbai-embed-large` is English-centric, hurting recall for Japanese/Vietnamese/Korean queries and cross-lingual search (a primary KH use case across Brysen Group). Backlog matrix and `db-schema-embeddings.mem.md` (D01) already locked `multilingual-e5-large` from day 1; implementation drifted to mxbai during ingestion phase. Need to realign before P3 SDD-AI features (#22, #24, #25) compound the drift.

### Solution Summary
- Replace embedder model with `intfloat/multilingual-e5-large` (MIT, self-hosted from HF GGUF q4_k_m).
- Schema unchanged: vector(1024) + HNSW cosine — no migration of column or index.
- Add E5-required `query: ` / `passage: ` prefix logic in `OllamaEmbedder` (split into `embed_query` / `embed_passage`).
- Truncate + re-ingest test data (no production data exists yet) — no maintenance window or version-tracking column.
- Eval set 120 query (30 × JA/EN/VI/KO) to prove ≥15% recall@10 lift, especially cross-lingual.
- Demo deployment on AWS `t3.medium` (~$30/month) with self-built Ollama Modelfile.

### Out of Scope
- BGE-M3 evaluation (deferred to feature #30+ if KPI miss).
- Production zero-downtime migration (Strategy B from plan) — current data is test-only.
- Query rewriting/expansion — separate feature `query-rewriting` (P1).
- Re-tuning hybrid weights (`RAG_DENSE_WEIGHT=0.7` / `RAG_BM25_WEIGHT=0.3`) — kept default.
- Frontend / API contract changes — `/v1/query` and `/v1/documents` unchanged externally.

---

## LAYER 2 — Story Detail

### S001: OllamaEmbedder refactor — query/passage prefix + batch variants

**Role / Want / Value**
- As a: rag-agent maintainer
- I want: embedder API split into `embed_query` and `embed_passage` with E5-required prefixes
- So that: dense retrieval quality matches E5 published benchmarks (no silent 5–10% recall loss from missing prefix)

**Acceptance Criteria**
- [ ] AC1: `EMBEDDING_MODEL` env default changes from `mxbai-embed-large` → `multilingual-e5-large`. Override path preserved for rollback.
- [ ] AC2: `OllamaEmbedder.embed_query(text)` automatically prepends `"query: "` before sending to Ollama `/api/embeddings`. Returns `list[float]` length 1024.
- [ ] AC3: `OllamaEmbedder.embed_passage(text)` automatically prepends `"passage: "`. Returns `list[float]` length 1024.
- [ ] AC4: `OllamaEmbedder.batch_embed_passage(chunks: list[Chunk], batch_size: int = 32)` replaces old `batch_embed`. Preserves order; uses `asyncio.gather` per batch (P002).
- [ ] AC5: Old `embed_one` / `batch_embed` removed (no shim — test data will be truncated, no callers in stable position).
- [ ] AC6: Truncation `OLLAMA_MAX_EMBED_CHARS` (default 1400) applied AFTER prefix is prepended (prefix counts toward limit).
- [ ] AC7: Unit tests cover: prefix presence, dim=1024, batch ordering, truncation behavior, EmbedderError on non-200.

**Implementation notes**
- File: [backend/rag/embedder.py](backend/rag/embedder.py)
- Decision D11 (chunk text stored in `Embedding.text`) unchanged.
- Rule R002 (no PII in metadata) unchanged.

---

### S002: Wire ingest path to `batch_embed_passage`

**Role / Want / Value**
- As a: api-agent maintainer
- I want: document ingestion pipeline uses `batch_embed_passage` for all chunks
- So that: stored embeddings carry the correct `passage: ` semantic prefix that matches query-time `query: ` retrieval

**Acceptance Criteria**
- [ ] AC1: `POST /v1/documents` ingestion handler calls `OllamaEmbedder().batch_embed_passage(chunks)` instead of legacy `batch_embed`.
- [ ] AC2: `insert_embeddings(chunks, vectors, doc, db)` signature unchanged — only the upstream caller changes.
- [ ] AC3: Ingest of multilingual fixture set (≥4 docs: JA/EN/VI/KO) succeeds end-to-end; `embeddings.lang` populated correctly per chunk.
- [ ] AC4: Existing R002 / P002 / P004 contracts preserved — no per-doc embedding loop, no PII in embedding metadata, single `db.add_all` commit.
- [ ] AC5: Integration test asserts vector dimension = 1024 for stored rows after E5 ingest.

**Implementation notes**
- File: [backend/api/routes/documents.py](backend/api/routes/documents.py) (ingest caller).
- Helper [backend/rag/embedder.py](backend/rag/embedder.py) `insert_embeddings` body unchanged.

---

### S003: Wire query path to `embed_query`

**Role / Want / Value**
- As a: rag-agent maintainer
- I want: dense retrieval uses `embed_query` with `query: ` prefix
- So that: query and passage vectors live in matching E5 semantic spaces

**Acceptance Criteria**
- [ ] AC1: `retriever._dense_search(query_text, ...)` calls `embedder.embed_query(query_text)` (prefix applied internally).
- [ ] AC2: Hybrid weights remain `RAG_DENSE_WEIGHT=0.7` / `RAG_BM25_WEIGHT=0.3` (env-configurable, A004).
- [ ] AC3: HNSW cosine ANN search unchanged (vector_cosine_ops, m=16, ef=64).
- [ ] AC4: Cross-lingual smoke test: query `"検索する方法"` returns ≥1 EN doc about "search guide" within top-10 (recall sanity).
- [ ] AC5: Query-time embedding p95 latency < 400ms on `t3.medium` (within total p95 < 2000ms budget per P001).

**Implementation notes**
- File: [backend/rag/retriever.py](backend/rag/retriever.py) `_dense_search`.
- BM25 path untouched; CJK tokenizers (R005) unchanged.

---

### S004: Truncate-and-reset script + AWS Ollama Modelfile setup

**Role / Want / Value**
- As a: ops engineer
- I want: a documented, idempotent way to wipe test data and stand up the new model on AWS
- So that: demo environments can be rebuilt repeatably without manual SQL or model-pulling guesswork

**Acceptance Criteria**
- [ ] AC1: Script `scripts/truncate_and_reset.py` runs `TRUNCATE embeddings, documents CASCADE` and resets sequences. Refuses to run without `--confirm` flag. Logs row counts before/after.
- [ ] AC2: Script idempotent — running twice produces same end state, no errors.
- [ ] AC3: Ops doc `docs/embed-model-migration/ops/ollama_setup.md` includes: AWS `t3.medium` provisioning steps, Ollama install, **llama.cpp convert steps** (`python convert-hf-to-gguf.py intfloat/multilingual-e5-large --outtype q4_k_m`), Modelfile content, `ollama create` command, env vars. (D08: không có HF GGUF repo — verified 2026-04-27.)
- [ ] AC4: License doc `docs/embed-model-migration/ops/license.md` records: HF model URL, license = MIT, GGUF source (HF or self-converted), distribution policy, checksum of distributed GGUF.
- [ ] AC5: After running setup on a fresh `t3.medium`, `curl POST :11434/api/embeddings -d '{"model":"multilingual-e5-large","prompt":"query: test"}'` returns a 1024-element float array.
- [ ] AC6: `.env.example` updated with `EMBEDDING_MODEL=multilingual-e5-large`.

**Implementation notes**
- Truncate script must use SQLAlchemy with `text()` and named params (S001 SQL injection rule) — no f-string SQL.
- License doc satisfies free/OSS constraint per backlog (Decision 2026-03-18).

---

### S005: Multilingual recall@10 evaluation harness + 120-query fixtures

**Role / Want / Value**
- As a: stakeholder (lb_mui)
- I want: a reproducible recall@10 number per language and for cross-lingual subset
- So that: the model switch decision is data-backed, not vibes-based

**Acceptance Criteria**
- [ ] AC1: Fixture file `backend/rag/eval/multilingual_recall.fixtures.json` contains 120 entries: 30 query × {JA, EN, VI, KO}. Each entry has `{id, query, query_lang, expected_doc_ids[], category}` where category ∈ {`mono`, `cross-lingual`, `multi-intent`}.
- [ ] AC2: Cross-lingual subset (~25% = ~30 entries) covers at least these pairs: VI→EN, JA→EN, KO→EN, EN→JA.
- [ ] AC3: Eval harness `backend/rag/eval/multilingual_recall.py` runs against a populated DB, computes recall@10 + MRR globally and per language, and per category.
- [ ] AC4: Output report (markdown) saved to `docs/embed-model-migration/reports/recall_e5.md` with E5 recall@10 + MRR per lang + per category. ~~mxbai baseline~~ bỏ qua (D09: fixture set mới, không apples-to-apples).
- [ ] AC5: E5 recall@10 ≥ **0.6** trên toàn fixture set (absolute threshold, D09). Cross-lingual subset recall@10 ≥ 0.5 (harder subset, documented separately).
- [ ] AC6: Eval runnable as `python -m backend.rag.eval.multilingual_recall --model <model_name>` with model name plumbed via env override.
- [ ] AC7: Fixture curation traceable — every `expected_doc_ids` entry maps to a doc that actually exists in the test ingest set.

**Implementation notes**
- Files (new): `backend/rag/eval/multilingual_recall.py`, `backend/rag/eval/multilingual_recall.fixtures.json`, `docs/embed-model-migration/reports/recall_baseline.md`, `docs/embed-model-migration/reports/recall_e5.md`.
- Curation owner — open question Q1 (see WARM memory).

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Plan decision D-EM-01 + WARM `db-schema-embeddings.mem.md` D01 | `.claude/plans/xem-x-t-c-c-feature-streamed-kazoo.md` §2 | 2026-04-27 |
| AC2 | E5 paper / HF model card | https://huggingface.co/intfloat/multilingual-e5-large (MIT) — "query: " prefix mandatory | 2026-04-27 |
| AC3 | Same as AC2 | "passage: " prefix mandatory | 2026-04-27 |
| AC4 | Existing rule P002 + plan §6 | `.claude/rules/PERF.md` P002 (batch ≥32) | 2026-04-27 |
| AC5 | Plan D-EM-01 (test data truncated) | Conversation 2026-04-27 with lb_mui | 2026-04-27 |
| AC6 | Existing behavior | [backend/rag/embedder.py:38](backend/rag/embedder.py#L38) `OLLAMA_MAX_EMBED_CHARS=1400` | 2026-04-27 |
| AC7 | Engineering practice | Existing test pattern in `backend/rag/tests/test_embedder.py` | 2026-04-27 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Plan §6 file modification table | Plan file §6 | 2026-04-27 |
| AC2 | Existing behavior | [backend/rag/embedder.py:62-88](backend/rag/embedder.py#L62-L88) `insert_embeddings` | 2026-04-27 |
| AC3 | Plan §8 verification step 2 | Plan file §8 | 2026-04-27 |
| AC4 | HARD/PERF rules | `.claude/rules/HARD.md` R002, `.claude/rules/PERF.md` P002, P004 | 2026-04-27 |
| AC5 | Schema | [backend/db/models/embedding.py:26](backend/db/models/embedding.py#L26) `Vector(1024)` | 2026-04-27 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Plan §6 file modification | Plan file §6 | 2026-04-27 |
| AC2 | ARCH rule A004 | `.claude/rules/ARCH.md` A004 | 2026-04-27 |
| AC3 | Existing migration | [backend/db/migrations/002_add_pgvector_hnsw.sql:23-26](backend/db/migrations/002_add_pgvector_hnsw.sql#L23-L26) | 2026-04-27 |
| AC4 | Plan §8 verification step 3 | Plan file §8 | 2026-04-27 |
| AC5 | HARD rule R007 / PERF P001 | `.claude/rules/HARD.md` R007, `.claude/rules/PERF.md` P001 | 2026-04-27 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Plan D-EM-01 + §6 | Plan file §2, §6 | 2026-04-27 |
| AC2 | Engineering practice | Conversation 2026-04-27 | 2026-04-27 |
| AC3 | Plan §7 AWS demo | Plan file §7 | 2026-04-27 |
| AC4 | Plan D-EM-04 (license) + backlog license matrix | [docs/backlog.md:113](docs/backlog.md#L113), HF model card | 2026-04-27 |
| AC5 | Ollama API contract | https://github.com/ollama/ollama/blob/main/docs/api.md | 2026-04-27 |
| AC6 | Existing convention | `.env.example` pattern | 2026-04-27 |

### S005 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Plan D-EM-03 | Plan file §2, conversation 2026-04-27 | 2026-04-27 |
| AC2 | Plan §1 cross-lingual problem statement | Plan file §1 | 2026-04-27 |
| AC3 | Standard IR eval methodology | recall@10 + MRR — common practice | 2026-04-27 |
| AC4 | Engineering practice | Plan §8 verification | 2026-04-27 |
| AC5 | Plan AC8 | Plan file §4 feature #29 AC8 | 2026-04-27 |
| AC6 | Engineering practice | Plan §6 | 2026-04-27 |
| AC7 | Engineering practice | Conversation 2026-04-27 | 2026-04-27 |

---
