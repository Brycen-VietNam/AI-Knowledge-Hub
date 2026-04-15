# COLD Memory Archive
# Features moved here when status = DONE.
# Never auto-loaded. Access via: /context <feature> --from-cold

---

## How to archive
Triggered automatically by `/report` when feature is APPROVED. Manual steps:
  1. Move `WARM/<feature>.mem.md` → `COLD/<feature>.archive.md`
  2. Add one row to Archive Index below
  3. Update `HOT.md` — remove from In Progress, clear blockers if applicable

---

## Archive Index

| Feature | Completed | Stories | Tests | Unblocks | Report |
|---------|-----------|---------|-------|----------|--------|
| db-schema-embeddings | 2026-03-19 | S001–S004 | 21/21 | auth-api-key-oidc, rbac-document-filter | docs/reports/db-schema-embeddings.report.md |
| auth-api-key-oidc | 2026-03-24 | S001–S004 | 51/51 | rbac-document-filter, document-ingestion, query-endpoint | docs/reports/auth-api-key-oidc.report.md |
| rbac-document-filter | 2026-04-06 | S001–S005 | 41 AC / all PASS | document-ingestion, multilingual-rag-pipeline, query-endpoint | docs/rbac-document-filter/reports/rbac-document-filter.report.md |
| cjk-tokenizer | 2026-04-06 | S001–S004 | 48 pass / 8 skip (MeCab/Windows) / 0 fail | document-ingestion, multilingual-rag-pipeline | docs/cjk-tokenizer/reports/cjk-tokenizer.report.md |
| llm-provider | 2026-04-06 | S001–S005 | 36/38 pass (2 async mock, non-critical) / 94% cov | query-endpoint (answer generation), multilingual-rag-pipeline | docs/llm-provider/reports/llm-provider.report.md |
| document-ingestion | 2026-04-08 | S001–S005 (split: db+api) | 61 new / 230 total pass / 22 AC PASS | query-endpoint, multilingual-rag-pipeline | docs/document-ingestion/reports/document-ingestion.report.md |
| multilingual-rag-pipeline | 2026-04-13 | S002–S005 | 15 pass / 1 skip / 24 AC PASS / 100% cov | query-endpoint | docs/multilingual-rag-pipeline/reports/multilingual-rag-pipeline.report.md |
| query-endpoint | 2026-04-13 | S001–S005 | 42/42 pass / 35 AC PASS / 95% cov | — (sprint complete) | docs/query-endpoint/reports/query-endpoint.report.md |
| document-parser | 2026-04-13 | P0 + S001–S004 | 18/18 unit pass / 24 AC PASS / 3 integration defined | — | docs/document-parser/reports/document-parser.report.md |
| answer-citation | 2026-04-15 | S001–S005 | 80/80 pass / 35 AC PASS / citation 100% / query 92% / generator 100% / retriever 91% | citation-quality, confidence-scoring | docs/answer-citation/reports/answer-citation.report.md |
