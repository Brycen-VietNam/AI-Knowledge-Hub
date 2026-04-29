# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-29 | Session: #136 (embed-model-migration — D13 confidence fix + citation parser + live eval PASS) | /sync ✅

---

## Completed Features (All Archived)
auth-api-key-oidc, rbac-document-filter, cjk-tokenizer, llm-provider, document-ingestion,
multilingual-rag-pipeline, query-endpoint, document-parser, answer-citation, confidence-scoring,
citation-quality, admin-spa, user-management, change-password, ux-form-validation,
frontend-theme, frontend-spa, **embed-model-migration** (2026-04-29), **security-audit** (2026-04-29)
→ All archived in `.claude/memory/COLD/`

---

## In Progress (max 3)

---

## Recent Decisions (last 3)
- 2026-04-29: **D13 — Presence-based confidence** — `cited_count > 0 → 0.9`, no cite → `0.5`, no answer → `0.2`. SUPERSEDES `cited_ratio × 0.8 + 0.2`. Rationale: old formula unfairly penalised LLM for not citing all retrieved docs.
- 2026-04-29: **Live eval PASS** — seeded 12 fixture docs via `scripts/seed_eval_fixtures.py`; recall@10 = 1.0, MRR = 0.964 on synthetic 120-query set; S005 fully verified end-to-end.
- 2026-04-29: **S005 ALL DONE** — T003 harness CLI (14/14 unit PASS, `--model` AC6, P002 batch embed, `<=>` pgvector) + T004 mock tests + `recall_e5.md` report template; full S005 story complete

---

## Active Blockers
- (none)
