# COLD Archive: cjk-tokenizer
Created: 2026-04-06 | Archived: 2026-04-06 | Status: DONE ✅ | Tests: 56/0/0 (Docker)

---

## Spec Summary
Language-aware tokenizer layer for BM25 search.
Replaces PostgreSQL `simple` (whitespace) dictionary in `_bm25_search()` (retriever.py:74).

**4 stories:** S001 (backends) → S002 (Factory) → S003 (detection) → S004 (tests)
**22 ACs | 0 open blockers**

---

## Key Decisions
- D01 (2026-04-06): TokenizerFactory.get(lang) pattern — Option A, lb_mui
- D02 (2026-04-06): Output format `list[str]` — Option A; caller formats for tsquery
- D03 (2026-04-06): Language detection failure → raise LanguageDetectionError — Option A
- D04 (2026-03-18): kiwipiepy (MIT) for Korean — replaces KoNLPy (Java dependency)
- D05 (2026-04-06): Lazy loading in Factory — MeCab/kiwipiepy init is expensive
- D06 (2026-04-06): text < 8 chars → raise LanguageDetectionError immediately; ≥ 8 → confidence ≥ 0.85
- D11 (2026-04-06): Dockerfile mecabrc symlink — apt-get installs /etc/mecabrc but mecab-python3 looks in /usr/local/etc/mecabrc; fix: `ln -s /etc/mecabrc /usr/local/etc/mecabrc` → 56/56 in Docker
- D07 (2026-04-06): MeCab not in Docker — S001-T005 must add apt-get install to Dockerfile
- D08 (2026-04-06): langdetect non-deterministic → set DetectorFactory.seed = 0 in detection.py
- D09 (2026-04-06): Japanese surface forms (MeCab default ipadic); Korean all morphemes (form only)
- D10 (2026-04-06): zh-cn / zh-tw both map to "zh" (jieba handles both)

---

## Files to Touch
```
NEW:
  backend/rag/tokenizers/__init__.py
  backend/rag/tokenizers/base.py
  backend/rag/tokenizers/exceptions.py
  backend/rag/tokenizers/japanese.py        ← MeCab, parseToNode surface forms
  backend/rag/tokenizers/korean.py          ← kiwipiepy, Kiwi().tokenize → .form
  backend/rag/tokenizers/chinese.py         ← jieba.cut(), suppress stderr
  backend/rag/tokenizers/vietnamese.py      ← underthesea.word_tokenize()
  backend/rag/tokenizers/whitespace.py      ← text.split(), en only
  backend/rag/tokenizers/factory.py         ← lazy singleton, threading.Lock
  backend/rag/tokenizers/detection.py       ← detect_language(), seed=0
  tests/rag/test_tokenizers.py              ← new, TDD-first

MODIFY:
  requirements.txt    ← add: mecab-python3, kiwipiepy, jieba, underthesea, langdetect
  Dockerfile          ← add MeCab apt-get layer (confirm path first — not found in repo root)
```

---

## Analysis Findings (pre-implement)
- `requirements.txt` missing all 5 packages — add in S001-T001
- Dockerfile not found in repo root — locate before S001-T005
- `DetectorFactory.seed = 0` required for deterministic CI (S003-T001)
- jieba logs to stderr on import → suppress with `jieba.setLogLevel(logging.WARNING)`
- `pytest.ini` `performance` marker already registered — S004-T002 needs NO pytest.ini change
- `tests/rag/__init__.py` already exists — no change needed
- Test file header pattern: `# Spec: ...` `# Task: T00X — ...` (follow test_retriever_rbac.py)

---

## SHOULD Assumptions (unblocking defaults)
- Q3: Japanese surface forms (default MeCab) ✅
- Q4: Chinese simplified only (jieba default) ✅
- Q5: underthesea `word_tokenize` confirmed ✅
- Q6: Korean all morphemes, form only ✅
- Q7: detect_language() reusable for query + ingestion ✅

---

## Status per Story
| Story | Status |
|---|---|
| S001 — Tokenizer backends | DONE ✅ |
| S002 — TokenizerFactory | DONE ✅ |
| S003 — Language detection | DONE ✅ |
| S004 — Tests | DONE ✅ |

---

## Task Files
- `docs/cjk-tokenizer/tasks/S001.tasks.md` — 5 tasks
- `docs/cjk-tokenizer/tasks/S002.tasks.md` — 2 tasks
- `docs/cjk-tokenizer/tasks/S003.tasks.md` — 2 tasks
- `docs/cjk-tokenizer/tasks/S004.tasks.md` — 2 tasks

## Analysis File
- `docs/cjk-tokenizer/tasks/all-stories.analysis.md`

---

## Phase Tracker
- [x] /specify
- [x] /clarify ✅ 2 BLOCKERs resolved
- [x] /checklist ✅ WARN-approved 2026-04-06
- [x] /plan ✅ G1→G2→G3(∥)
- [x] /tasks ✅ 11 tasks total
- [x] /analyze ✅ 5 gaps found + resolved
- [x] /implement ✅ 2026-04-06 — 48 pass, 8 skip (MeCab/Windows), 0 fail
- [x] /reviewcode ✅ 2026-04-06 — APPROVED, 3 non-blocking warnings
- [x] /report ✅ 2026-04-06 — docs/cjk-tokenizer/reports/cjk-tokenizer.report.md
