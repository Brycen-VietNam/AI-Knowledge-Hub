# HARD RULES — Never Violate
# Auto-checked by /rules command and hooked into /implement and /reviewcode.

---

## R001 — RBAC Before Retrieval
```
RULE: Apply user_group filter at pgvector WHERE clause level, BEFORE results are returned.
WRONG: retrieve all → filter in Python
RIGHT: SELECT ... WHERE user_group_id = ANY(:group_ids)
APPLIES TO: all retrieval paths in backend/rag/
CHECK: grep -n "user_group" backend/rag/retriever.py | grep "WHERE\|filter"
```

## R002 — No PII in Vector Metadata
```
RULE: pgvector embedding metadata must only contain: doc_id, lang, user_group_id, created_at
WRONG: storing email, name, content snippets in metadata
RIGHT: store doc_id → join PostgreSQL for any user-identifiable data
APPLIES TO: backend/rag/, backend/db/models/
CHECK: inspect embedding insert statements for PII fields
```

## R003 — Auth on Every Endpoint
```
RULE: All /v1/* endpoints require authentication. No anonymous access except /v1/health.
WRONG: missing Depends(verify_token) on route
RIGHT: @router.post("/v1/query", dependencies=[Depends(verify_token)])
APPLIES TO: backend/api/routes/
CHECK: grep -rn "router\.\(get\|post\|put\|delete\)" backend/api/routes/ | grep -v "verify_token\|health"
```

## R004 — API Version Prefix
```
RULE: All routes must start with /v1/. No breaking changes without new version prefix.
WRONG: @router.get("/query")
RIGHT: @router.get("/v1/query")
APPLIES TO: backend/api/routes/
CHECK: grep -rn "@router\." backend/api/routes/ | grep -v "/v1/"
```

## R005 — CJK-Aware Tokenization
```
RULE: Japanese and other CJK content must use language-aware tokenizer before BM25 indexing.
WRONG: whitespace split on Japanese text
RIGHT: MeCab/Sudachi for ja, underthesea for vi, jieba for zh
APPLIES TO: backend/rag/bm25_indexer.py, any text preprocessing
CHECK: grep -n "tokenize\|split" backend/rag/bm25_indexer.py
```

## R006 — Audit Log on Document Access
```
RULE: Every document retrieval must write to audit_logs table: user_id, doc_id, timestamp, query_hash.
WRONG: returning documents without logging
RIGHT: await audit_log.write(user_id, doc_ids, query_hash)
APPLIES TO: backend/api/routes/query.py, backend/rag/retriever.py
CHECK: grep -n "audit_log" backend/api/routes/query.py
```

## R007 — Latency SLA
```
RULE: /v1/query p95 < 2000ms. Reject implementation that cannot meet this.
WRONG: synchronous embedding + retrieval + rerank in serial without timeout
RIGHT: async pipeline, timeout=1800ms, fallback to BM25-only if dense slow
APPLIES TO: backend/api/routes/query.py, backend/rag/
CHECK: load test or add @pytest.mark.performance decorator
```
