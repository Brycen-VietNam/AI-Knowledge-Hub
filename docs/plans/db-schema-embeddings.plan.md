# Plan: db-schema-embeddings
Created: 2026-03-18 | Based on spec: v1 | Checklist: PASS

---

## LAYER 1 — Plan Summary

| Field | Value |
|-------|-------|
| Total stories | 4 |
| Sessions estimated | 1 (all db-agent, single scope) |
| Critical path | S001 → S002 → S003 ∥ S004 |
| Token budget total | ~4k tokens |

### Parallel Execution Groups
```
G1 (sequential):
  S001 — db-agent — core schema (4 tables, migration 001)
  S002 — db-agent — pgvector extension + HNSW index (migration 002)

G2 (after G1, parallel-safe):
  S003 — db-agent — CJK FTS column + GIN index (migration 003)
  S004 — db-agent — session.py connection pool (no migration)
```

### Agent Assignments
| Agent | Stories | Can start |
|-------|---------|-----------|
| db-agent | S001, S002, S003, S004 | S001 immediately; S002 after S001; S003+S004 after S002 |

### Risk
| Risk | Mitigation |
|------|-----------|
| pgvector not installed on target PG | `CREATE EXTENSION IF NOT EXISTS vector` — idempotent, safe |
| asyncpg version conflict | Pin `asyncpg==0.29.0` in requirements.txt |
| HNSW params wrong for dataset | m=16, ef=64 per PERF.md P003 — correct for <10M vectors |

---

## LAYER 2 — Story Plans

### S001: Create core database schema
**Agent**: db-agent | **Group**: G1-first | **Depends**: none

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/db/migrations/001_create_core_schema.sql` |
| CREATE | `backend/db/models/user_group.py` |
| CREATE | `backend/db/models/document.py` |
| CREATE | `backend/db/models/embedding.py` |
| CREATE | `backend/db/models/audit_log.py` |
| CREATE | `backend/db/models/__init__.py` |

**Key decisions**
- PK: UUID v4 via `gen_random_uuid()` — all tables
- `user_group_id`: INT FK (not UUID) — simpler joins
- `lang`: CHAR(2) ISO 639-1 (ja/en/vi/ko/zh)
- `audit_logs.user_id`: TEXT placeholder — auth schema defined later
- Rollback section at bottom of migration (`DROP TABLE CASCADE`)

**Test**: `psql -f 001_create_core_schema.sql` succeeds + `\dt` shows 4 tables
**Subagent dispatch**: YES
**Est. tokens**: ~1.5k

**Outputs** — ✅ COMPLETE (2026-03-18)
- [x] `001_create_core_schema.sql` with rollback section — REVIEWED
- [x] 4 SQLAlchemy ORM models (UserGroup, Document, Embedding, AuditLog) — REVIEWED
- [x] `models/__init__.py` exporting all models — REVIEWED
- [x] `tests/db/test_models.py` — 14 tests, all pass

---

### S002: Add pgvector extension and HNSW index
**Agent**: db-agent | **Group**: G1-second | **Depends**: S001

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/db/migrations/002_add_pgvector_hnsw.sql` |
| MODIFY | `backend/db/models/embedding.py` |

**Key decisions**
- `CREATE EXTENSION IF NOT EXISTS vector` — idempotent
- `vector(1024)` — multilingual-e5-large (confirmed 2026-03-17)
- HNSW: `m=16, ef_construction=64, vector_cosine_ops`
- Rollback: `DROP INDEX idx_embeddings_hnsw` → `DROP EXTENSION vector CASCADE`

**Test**: `\d embeddings` shows hnsw index + `SELECT typname FROM pg_type WHERE typname='vector'`
**Subagent dispatch**: YES
**Est. tokens**: ~0.8k

**Outputs**
- [ ] `002_add_pgvector_hnsw.sql` with rollback
- [ ] `embedding.py` updated with `Vector(1024)` column

---

### S003: Configure CJK-aware full-text search
**Agent**: db-agent | **Group**: G2-parallel | **Depends**: S001

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/db/migrations/003_add_fts_column.sql` |
| MODIFY | `backend/db/models/document.py` |

**Key decisions**
- `content_fts tsvector` — app-layer populated (NOT pg trigger)
- GIN index: `CREATE INDEX idx_documents_fts ON documents USING gin(content_fts)`
- rag-agent populates via tokenizers: MeCab(ja) / kiwipiepy(ko) / jieba(zh) / underthesea(vi)
- Rollback: `DROP INDEX idx_documents_fts` → `ALTER TABLE documents DROP COLUMN content_fts`

**Test**: `\d documents` shows `content_fts tsvector` + gin index `idx_documents_fts`
**Subagent dispatch**: YES
**Est. tokens**: ~0.8k

**Outputs**
- [ ] `003_add_fts_column.sql` with rollback
- [ ] `document.py` updated with `content_fts` column

---

### S004: Configure connection pool and session factory
**Agent**: db-agent | **Group**: G2-parallel | **Depends**: S001

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/db/session.py` |
| CREATE | `backend/db/__init__.py` |

**Key decisions**
- Driver: `asyncpg` (`postgresql+asyncpg://`)
- `pool_size=5, max_overflow=15, pool_pre_ping=True` → effective max 20 (C011)
- Engine init at module level — never per-request (PERF.md P005)
- Exports: `async_session_factory`, `engine`
- `DATABASE_URL = os.getenv("DATABASE_URL")` — no hardcoded secrets (SECURITY.md S005)

**Test**: Import `async_session_factory` + execute `SELECT 1` via pool
**Subagent dispatch**: YES
**Est. tokens**: ~0.8k

**Outputs**
- [ ] `session.py` with `create_async_engine` + `AsyncSession` factory
- [ ] `db/__init__.py` re-exporting `async_session_factory`

---

## Files to Create (complete list)
```
backend/db/
  migrations/
    001_create_core_schema.sql
    002_add_pgvector_hnsw.sql
    003_add_fts_column.sql
  models/
    __init__.py
    user_group.py
    document.py
    embedding.py
    audit_log.py
  __init__.py
  session.py
```

## Verification (end-to-end)
1. Run migrations in order: `001` → `002` → `003`
2. `psql \dt` — 4 tables: user_groups, documents, embeddings, audit_logs
3. `psql \d embeddings` — vector(1024) column + hnsw index
4. `psql \d documents` — content_fts tsvector + gin index
5. `python -c "from backend.db.session import async_session_factory"` — no import error
6. Rollback reverse: `003` → `002` → `001` — clean teardown confirmed
