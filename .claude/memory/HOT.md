# HOT Memory
> Auto-updated by /sync. Loaded every session. Keep under 300 lines.

Updated: 2026-04-06 | Session: #016

---

## Active Sprint
Goal: Auth layer — unblock RBAC, document ingestion, query endpoint
Sprint end: _[date TBD]_

## Completed Features
- auth-api-key-oidc — DONE ✅ 4 stories, 16 tasks, 51 tests, 20/20 ACs
  Archive: `.claude/memory/COLD/auth-api-key-oidc.archive.md`
  Report: `docs/reports/auth-api-key-oidc.report.md`
  Unblocks: rbac-document-filter, document-ingestion, query-endpoint
- rbac-document-filter — DONE ✅ 5 stories, 41 ACs, all PASS — approved by lb_mui 2026-04-06
  Archive: `.claude/memory/COLD/rbac-document-filter.archive.md`
  Report: `docs/rbac-document-filter/reports/rbac-document-filter.report.md`
  Unblocks: document-ingestion, multilingual-rag-pipeline, query-endpoint
- cjk-tokenizer — DONE ✅ 4 stories, 22 ACs, **56/0/0 Docker** — approved 2026-04-06
  Archive: `.claude/memory/COLD/cjk-tokenizer.archive.md`
  Report: `docs/cjk-tokenizer/reports/cjk-tokenizer.report.md`
  Unblocks: document-ingestion, multilingual-rag-pipeline

## In Progress (max 3)
_None._

## Recent Decisions (last 3 — oldest drops off)
- 2026-04-06: D11 — Dockerfile mecabrc symlink fix: `ln -s /etc/mecabrc /usr/local/etc/mecabrc` — apt-get installs to /etc but mecab-python3 looks in /usr/local/etc; fix gives 56/56 in Docker
- 2026-04-06: cjk-tokenizer DONE ✅ — finalized, archived to COLD, sign-offs all APPROVED
- 2026-04-06: cjk-tokenizer /report — 22/22 ACs, 56/0/0 Docker, APPROVED

## Active Blockers
_None._

## Subagent Status
| Agent | Task | Status | Last updated |
|-------|------|--------|--------------|
| — | — | — | — |

## Next Session Start
> Next feature: `document-ingestion` or `multilingual-rag-pipeline` (both unblocked by cjk-tokenizer + rbac-document-filter)
> Run: `/specify <next-feature>` to begin
