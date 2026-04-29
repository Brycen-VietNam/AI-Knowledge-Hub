# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-29 | Session: #135 (embed-model-migration — S005 ALL DONE ✅ T003+T004, 14/14 PASS) | /sync ✅

---

## Completed Features (All Archived)
auth-api-key-oidc, rbac-document-filter, cjk-tokenizer, llm-provider, document-ingestion,
multilingual-rag-pipeline, query-endpoint, document-parser, answer-citation, confidence-scoring,
citation-quality, admin-spa, user-management, change-password, ux-form-validation,
frontend-theme, frontend-spa
→ All archived in `.claude/memory/COLD/`

---

## In Progress (max 3)

### embed-model-migration — P0
WARM: `.claude/memory/WARM/embed-model-migration.mem.md`
- S001 DONE ✅ — embedder refactored (embed_query/embed_passage/batch_embed_passage), legacy API removed, 18 tests PASS
- S002 DONE ✅ — documents.py batch_embed → batch_embed_passage, 8 tests (7 PASS + 1 SKIP)
- S003 DONE ✅ — query_processor embed_one → embed_query, retriever <-> → <=>, 37 PASS + 1 SKIP
- S004 DONE ✅ — truncate script + ollama_setup.md + license.md/LICENSE.e5 + .env.example, 12/12 PASS
- S005 DONE ✅ — T001–T004 ALL DONE | 14/14 unit tests PASS | recall_e5.md template ready for live run
  Files: `backend/rag/eval/__init__.py`, `backend/rag/eval/multilingual_recall.py`, `tests/rag/test_multilingual_recall.py`, `docs/embed-model-migration/reports/recall_e5.md`
  **Next: live eval run** — `python -m backend.rag.eval.multilingual_recall --model zylonai/multilingual-e5-large` (requires S002+S003+S004 on target DB)

### security-audit — P1
WARM: `.claude/memory/WARM/security-audit.mem.md`
Report DONE 2026-04-23 | awaiting lb_mui sign-off → `/report security-audit --finalize`
S001 ✅ + S002 ✅ REVIEWED | 20/20 ACs | 118/118 backend + 32/32 frontend tests

---

## Recent Decisions (last 3)
- 2026-04-29: **S005 ALL DONE** — T003 harness CLI (14/14 unit PASS, `--model` AC6, P002 batch embed, `<=>` pgvector) + T004 mock tests + `recall_e5.md` report template; full S005 story complete
- 2026-04-29: **S004 ALL DONE** — truncate script (12/12 PASS), ollama_setup.md, license.md+LICENSE.e5, coordination check PASS
- 2026-04-29: **S003 DONE** — embed_one→embed_query swap + cosine <->→<=> fix; 37 PASS + 1 SKIP

---

## Active Blockers
- (none)
