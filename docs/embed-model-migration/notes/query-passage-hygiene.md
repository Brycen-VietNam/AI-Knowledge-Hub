# Query/Passage Hygiene — Deferred Findings
Created: 2026-04-28 (post-/tasks S001 analysis) | Status: FLAGGED — review after S005 eval

> **Purpose**: catalog of input-handling concerns identified when designing S001/S002/S003. Most are out-of-scope for embed-model-migration (#29) per "Option A — Conservative" decision. This file is the single reference for re-opening if S005 recall numbers are unsatisfactory or related bugs surface.

> **Scope decision (2026-04-28, lb_mui)**: ship #29 with E5 prefixes only; defer normalization/validation work until S005 eval gives evidence. Q3 + X3 folded into S001 T002/T003 review criteria as cheap defensive measures.

---

## In-Scope (folded into S001 — completed)

### Q3 — Double-prefix guard
**Risk**: caller (bot adapter, future code) prepends `"query: "` manually → embedder prepends again → `"query: query: ..."` → embedding lệch, silent recall drop.
**Action taken**: T002/T003 review criteria require `embed_query`/`embed_passage` to raise `ValueError` if input already starts with `"query: "` or `"passage: "`. Shared `_check_no_prefix(text)` helper.
**Status**: ✅ in S001 scope.

### X3 — Exact byte-level prefix
**Risk**: variants like `"Query:"`, `"query:"` (no space), `"q: "` would silently degrade recall — E5 is instruction-tuned on the exact 2 prefixes.
**Action taken**: T002/T003 tests assert exact `startswith("query: ")` (7 chars) and `startswith("passage: ")` (9 chars).
**Status**: ✅ in S001 scope.

---

## Deferred — Re-evaluate after S005

### P1 — Truncation cuts content tail
**Risk**: `OLLAMA_MAX_EMBED_CHARS=1400` after `"passage: "` prefix (9 chars) leaves 1391 chars. CHUNK_SIZE=512 tokens × ~3 chars/token ≈ 1500+ chars for EN/VI → ~6–7% of long chunks lose tail content. CJK ≈ 512 chars (1 char/token) — safe.
**Re-open trigger**: S005 recall < 0.6 for EN/VI (mono-lingual subset).
**Mitigation options**: (a) raise `OLLAMA_MAX_EMBED_CHARS` to ~2000 (E5 supports 512 tokens ≈ 2048 BPE chars); (b) lower `CHUNK_SIZE` for non-CJK langs.
**Owner**: rag-agent.

### P2 — CJK chunk reconstruction may not match raw text
**Risk**: `chunker.py:69` reconstructs chunk via `"".join(window)` (CJK) or `" ".join(window)` (others). With Sudachi mode A or jieba subwords, reconstruction can differ from original substring → embedded text ≠ user-readable text.
**Re-open trigger**: visual inspection of 5 JA/KO chunks during S005 fixture generation shows divergence; OR cross-lingual recall < 0.5.
**Mitigation**: store raw substring `content[start:end]` in `Chunk.text` instead of token-join.
**Owner**: rag-agent (chunker scope).

### P4 — Title/heading not boosted in passage
**Risk**: E5 paper recommends `"passage: {title}. {body}"` for retrieve-document tasks. Current ingest treats heading as plain text → loses title-boost signal.
**Re-open trigger**: S005 reveals top-1 retrieval often misses doc whose title clearly matches query.
**Mitigation**: parser surfaces title; passage formatter prepends. Cross-cuts document-parser + embedder.
**Owner**: rag-agent + parser.
**Note**: D06 already deferred query-rewriting; passage-formatting is the symmetric ingest-side concern — could be folded into the same future feature.

### P5 — Metadata leakage into chunk text
**Risk**: document-parser may inline filename/page-number/footer into content → embedded as semantic content → noise. R002 only blocks PII in vector METADATA table, not in chunk.text body.
**Re-open trigger**: spot-check ingested chunks shows obvious header/footer noise; OR confidence-scoring drops post-#29.
**Mitigation**: parser-side filter; out-of-scope for rag-agent.
**Owner**: parser maintainer.

### Q1 — Query not normalized (NFKC + whitespace)
**Risk**: raw user input → embedding sensitive to: trailing whitespace, multiple spaces, full-width vs half-width JA (`ＶＰＮ` vs `VPN`), zenkaku/hankaku, emoji, markdown leftovers. Semantically-identical queries get different vectors → unstable retrieval.
**Re-open trigger**: any bug report of "same query, different results"; OR S005 shows variance > 5% across re-runs of identical queries.
**Mitigation**: `query_processor.embed_query` façade applies `unicodedata.normalize("NFKC", text).strip()` and `re.sub(r"\s+", " ", text)` BEFORE calling `OllamaEmbedder.embed_query`.
**Owner**: rag-agent.
**⚠ Symmetry constraint (X1)**: if applied to query, MUST also apply to passage at ingest — otherwise embedding spaces diverge.

### X1 — Symmetric normalization between query and passage
**Risk**: if query is normalized but passage is not (or vice versa), the embedding spaces diverge → cross-side recall drops.
**Re-open trigger**: any time Q1 is implemented.
**Mitigation**: shared `_normalize(text)` static method on `OllamaEmbedder`, called inside both `embed_query` and `embed_passage` BEFORE prefix prepend. This way callers stay simple and symmetry is enforced by construction.
**Owner**: rag-agent.

### X2 — Truncation symmetry — long-doc tail recall
**Risk**: queries are almost always < 200 chars (encode 100% of intent). Passages frequently hit 1400-char truncation (encode only head). Queries about tail content of long docs → systematic recall miss.
**Re-open trigger**: S005 fixture should include 5 queries deliberately targeting tail content of long ingested docs. If recall < 0.5 for that subset, this is the cause.
**Mitigation**: bump `OLLAMA_MAX_EMBED_CHARS` OR shrink `CHUNK_SIZE` for non-CJK (same lever as P1).
**Owner**: rag-agent.

---

## Out-of-Scope — Open as separate features if surface

### Q2 — Query length validation at API layer
**Risk**: queries > 1400 chars get silently truncated. SECURITY S003 says "limit to 512 tokens before embedding" — currently not enforced at API gate.
**Mitigation**: API-layer gate at `/v1/query` — reject > N chars with `400 ERR_QUERY_TOO_LONG`.
**Suggested feature name**: `query-input-validation`.
**Owner**: api-agent.

### Q4 — Query language auto-detection at /v1/query entry
**Risk**: A003 mandates auto-detect query language. If frontend sends wrong `lang`, BM25 tokenizer tokenizes wrong (e.g. JA query split by whitespace) → BM25 path produces zero matches. Dense path unaffected (E5 is multilingual).
**Re-open trigger**: verify whether `detect_language` is called in `backend/api/routes/query.py` — if absent, this is a live A003 violation regardless of #29.
**Mitigation**: add `detect_language(query)` at route entry; ignore frontend-sent `lang` for BM25, keep it for response language.
**Suggested feature name**: `query-lang-autodetect` or fold into `query-rewriting` (D06).
**Owner**: api-agent.

### Q5 — Empty/whitespace-only query
**Risk**: `embed_query("")` behavior undefined. Ollama may return zero vector → recall@10 returns random docs.
**Mitigation**: API-layer validation — query must be ≥ 2 chars after strip; reject with `400 ERR_QUERY_EMPTY`.
**Suggested feature name**: `query-input-validation` (with Q2).
**Owner**: api-agent.

### Q6 — Query expansion / synonym handling
**Already deferred**: D06 → feature `query-rewriting` (post #29).

### Q7 — Question vs keyword query style
**Risk**: E5 trained on both but performs better on natural-language questions vs raw keywords.
**Mitigation**: cannot fix at system level; UI hint to encourage question-style queries.
**Owner**: frontend (out of backend scope).

---

## Re-Open Decision Tree (post-S005)

```
S005 recall@10 ≥ 0.6 overall AND ≥ 0.5 cross-lingual?
├─ YES → ship #29; this file stays as future-reference only
└─ NO  → investigate in this order (cheap → expensive):
         1. Q4 (lang auto-detect)  — most likely BM25 path is broken
         2. P1/X2 (truncation)     — check if low recall correlates with long docs
         3. Q1/X1 (normalization)  — check if recall variance is high across re-runs
         4. P2 (CJK reconstruct)   — only if JA/KO recall specifically low
         5. P4 (title boost)       — last resort, requires parser cooperation
```

---

## References
- S001 analysis: `docs/embed-model-migration/tasks/S001.analysis.md`
- S005 plan: `docs/embed-model-migration/plan/embed-model-migration.plan.md` §S005
- E5 paper: https://arxiv.org/abs/2402.05672 (multilingual-e5)
- Spike A: `docs/embed-model-migration/spike/spike_e5_compare.py` (2026-04-28 — verified raw input acceptable for cross-lingual at cos=0.94)
