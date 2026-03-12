# PERFORMANCE RULES
# Checked by /analyze and /reviewcode for RAG and API tasks.

## P001 — Query Latency SLA
```
RULE: /v1/query p95 < 2000ms end-to-end. Hard timeout at 1800ms.
WRONG: serial pipeline — embed → retrieve → rerank → generate (no timeout)
RIGHT: async pipeline with asyncio.gather where possible; timeout=1800ms;
       fallback to BM25-only if dense embedding > 500ms
APPLIES TO: src/api/routes/query.py, src/rag/retriever.py
CHECK: look for asyncio.wait_for or equivalent timeout wrapper
```

## P002 — Embedding Batch Calls
```
RULE: Never call embedding API per-document in a loop. Batch minimum 32 docs.
WRONG: for doc in docs: embed(doc)
RIGHT: embedder.batch_embed(docs, batch_size=32)
APPLIES TO: src/rag/embedder.py, any ingestion pipeline
CHECK: grep -n "embed(" src/rag/ | grep "for \|loop"
```

## P003 — pgvector Index Required
```
RULE: Vector search must use HNSW index. No sequential scan on embeddings table.
WRONG: SELECT ... ORDER BY embedding <-> $1 LIMIT N  (no index)
RIGHT: CREATE INDEX idx_embeddings_hnsw ON embeddings USING hnsw(embedding vector_cosine_ops)
       WITH (m=16, ef_construction=64)
APPLIES TO: src/db/migrations/
CHECK: \d embeddings in psql — confirm hnsw index exists
```

## P004 — N+1 Query Prevention
```
RULE: No N+1 queries. Use joins or IN clauses for batch document fetches.
WRONG: for doc_id in results: db.get(Document, doc_id)
RIGHT: db.execute(select(Document).where(Document.id.in_(doc_ids)))
APPLIES TO: src/db/, src/api/routes/
CHECK: SQLAlchemy query count in test — use sqlalchemy event listener
```

## P005 — Connection Pool
```
RULE: PostgreSQL connection pool min=5 max=20. Never open per-request connection.
WRONG: engine = create_engine(url) inside request handler
RIGHT: pool configured at app startup via create_async_engine(pool_size=10)
APPLIES TO: src/db/session.py
CHECK: grep -n "create_engine\|create_async_engine" src/db/
```
