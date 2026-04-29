# Recall@10 Evaluation Report — multilingual-e5-large

> **Status: PENDING LIVE RUN**
> This template is pre-populated with metadata and pass/fail thresholds.
> Fill in results after running:
> `python -m backend.rag.eval.multilingual_recall --model zylonai/multilingual-e5-large`

---

## Run Metadata

| Field | Value |
|-------|-------|
| Run date | _fill after live run_ |
| Model tag | `zylonai/multilingual-e5-large` |
| Model digest | `sha256:c1522b1cf095b82080a9b804d86b4aa609e71a48bbdbcde7ea7864bb9b0cd76b` |
| Fixture file | `backend/rag/eval/multilingual_recall.fixtures.json` |
| Fixture version | `1` |
| Total queries | 120 (30 × EN / JA / VI / KO) |
| Cross-lingual queries | 35 (pairs: EN→JA, JA→EN, VI→EN, KO→EN) |
| DB state | Post-S004 truncate + full re-ingest of 12 eval corpus docs |
| Harness command | `python -m backend.rag.eval.multilingual_recall --model zylonai/multilingual-e5-large` |

---

## Results

### Global

| Metric | Value | Threshold (D09) | Verdict |
|--------|-------|-----------------|---------|
| Recall@10 (overall) | _fill_ | ≥ 0.60 | _PASS / FAIL_ |
| MRR (overall) | _fill_ | — | — |
| Recall@10 (cross-lingual) | _fill_ | ≥ 0.50 | _PASS / FAIL_ |

### Per Language

| Language | Recall@10 | MRR | Count |
|----------|-----------|-----|-------|
| EN | _fill_ | _fill_ | 30 |
| JA | _fill_ | _fill_ | 30 |
| VI | _fill_ | _fill_ | 30 |
| KO | _fill_ | _fill_ | 30 |

### Per Category

| Category | Recall@10 | MRR | Count |
|----------|-----------|-----|-------|
| mono | _fill_ | _fill_ | _fill_ |
| cross-lingual | _fill_ | _fill_ | 35 |
| multi-intent | _fill_ | _fill_ | _fill_ |

---

## D09 Verdict

Pass thresholds (Decision D09, 2026-04-27):
- Overall recall@10 ≥ **0.60** — production-viable per IR literature
- Cross-lingual recall@10 ≥ **0.50** — minimum bar for JA/VI/KO cross-lingual retrieval

**Overall verdict: _PASS / FAIL_**
**Cross-lingual verdict: _PASS / FAIL_**

_If FAIL: re-open query/passage hygiene deferred items per `.claude/memory/WARM/embed-model-migration.mem.md` §Query/Passage Hygiene — Deferred._

---

## Misses / Anomalies

_Fill after live run — note any patterns in missed queries (e.g., specific language pairs, categories, or doc IDs that never appear in top-10)._

---

## Traceability

- Fixture spec: `docs/embed-model-migration/tasks/S005.tasks.md` T001
- Fixture validation: `tests/rag/test_eval_fixtures.py` (9/9 PASS)
- Harness unit tests: `tests/rag/test_multilingual_recall.py` (14/14 PASS)
- Model provenance: `docs/embed-model-migration/ops/license.md`
- Re-open trigger (D11): POC → product promotion requires supply-chain verification
