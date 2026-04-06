# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S003
# Task: T001 — DB fixtures + real PostgreSQL async session for integration tests
# Decision: D01 — user_group_id IS NULL = public document
import json
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Integration tests require TEST_DATABASE_URL. No default — avoids hardcoded credentials (S005).
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "")

_integration_available = bool(os.getenv("TEST_DATABASE_URL"))


# ---------------------------------------------------------------------------
# Engine (session-scoped — created once per pytest session)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False, pool_pre_ping=True)
    yield engine
    await engine.dispose()


# ---------------------------------------------------------------------------
# Base session (function-scoped — fresh per test, uses SAVEPOINT for rollback)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    """Real AsyncSession. Uses nested transaction (SAVEPOINT) for test isolation."""
    async with async_sessionmaker(db_engine, expire_on_commit=False)() as session:
        async with session.begin():
            # Create SAVEPOINT so we can rollback seeded data without closing connection
            await session.begin_nested()
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# Seeded session — 3 groups + 18 embeddings (5 per group + 3 public NULL)
# ---------------------------------------------------------------------------

# Fixed UUIDs for deterministic test assertions
GROUP_A_ID = 1
GROUP_B_ID = 2
GROUP_C_ID = 3

# doc_ids seeded per group (5 per group + 3 public)
_SEED_DOC_IDS: dict[str, list[uuid.UUID]] = {
    "group_a": [uuid.UUID(f"aa000000-0000-0000-0000-{i:012x}") for i in range(1, 6)],
    "group_b": [uuid.UUID(f"bb000000-0000-0000-0000-{i:012x}") for i in range(1, 6)],
    "group_c": [uuid.UUID(f"cc000000-0000-0000-0000-{i:012x}") for i in range(1, 6)],
    "public":  [uuid.UUID(f"00000000-0000-0000-0000-{i:012x}") for i in range(100, 103)],
}

# Expose for use in test assertions
SEED_DOC_IDS = _SEED_DOC_IDS


async def _seed_groups(session: AsyncSession) -> None:
    """Ensure user_groups rows exist (idempotent — INSERT ... ON CONFLICT DO NOTHING)."""
    await session.execute(text("""
        INSERT INTO user_groups (id, name)
        VALUES (:id1, 'group_a'), (:id2, 'group_b'), (:id3, 'group_c')
        ON CONFLICT (id) DO NOTHING
    """).bindparams(id1=GROUP_A_ID, id2=GROUP_B_ID, id3=GROUP_C_ID))


async def _seed_embeddings(session: AsyncSession) -> None:
    """Seed 18 embeddings: 5 per group + 3 public (user_group_id NULL)."""
    group_map = {
        "group_a": GROUP_A_ID,
        "group_b": GROUP_B_ID,
        "group_c": GROUP_C_ID,
        "public":  None,
    }
    rows = []
    for label, gid in group_map.items():
        for i, doc_id in enumerate(_SEED_DOC_IDS[label]):
            # Vary embedding slightly so distance ordering is deterministic
            vec_val = [float(i + 1) / 1024] * 1024
            rows.append({
                "id": uuid.uuid4(),
                "doc_id": doc_id,
                "chunk_index": 0,
                "user_group_id": gid,
                "embedding_str": str(vec_val),
            })

    for row in rows:
        await session.execute(text("""
            INSERT INTO embeddings (id, doc_id, chunk_index, user_group_id, embedding)
            VALUES (:id, :doc_id, :chunk_index, :user_group_id,
                    cast(:embedding_str AS vector))
            ON CONFLICT (id) DO NOTHING
        """).bindparams(**row))


@pytest_asyncio.fixture
async def seeded_session(db_session: AsyncSession) -> AsyncSession:
    """Seeds 3 groups + 18 embeddings. Fixture isolation via SAVEPOINT in db_session."""
    if not _integration_available:
        pytest.skip("TEST_DATABASE_URL not set — skipping integration test")
    await _seed_groups(db_session)
    await _seed_embeddings(db_session)
    yield db_session


# ---------------------------------------------------------------------------
# Large seeded session — 10k embeddings for performance test (session-scoped)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def large_seeded_session(db_engine) -> AsyncSession:
    """
    Seeds 10k embeddings: 1k for group_id=1, 9k for other groups.
    Session-scoped — seeded once per pytest run (expensive).
    """
    if not _integration_available:
        pytest.skip("TEST_DATABASE_URL not set — skipping performance test")

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        async with session.begin():
            # Ensure group exists
            await session.execute(text("""
                INSERT INTO user_groups (id, name) VALUES (1, 'perf_group')
                ON CONFLICT (id) DO NOTHING
            """))

            # Bulk insert 10k embeddings using VALUES list in batches of 500
            batch_size = 500
            total = 10_000
            rows_group1 = 1_000

            all_rows = []
            for i in range(total):
                gid = 1 if i < rows_group1 else 2
                vec_val = str([float((i % 1024) + 1) / 1024] * 1024)
                all_rows.append({
                    "id": str(uuid.uuid4()),
                    "doc_id": str(uuid.uuid4()),
                    "chunk_index": 0,
                    "user_group_id": gid,
                    "embedding_str": vec_val,
                })

            for start in range(0, total, batch_size):
                batch = all_rows[start : start + batch_size]
                await session.execute(
                    text("""
                        INSERT INTO embeddings (id, doc_id, chunk_index, user_group_id, embedding)
                        SELECT
                            CAST(r.id AS uuid),
                            CAST(r.doc_id AS uuid),
                            CAST(r.chunk_index AS int),
                            CAST(r.user_group_id AS int),
                            CAST(r.embedding_str AS vector)
                        FROM jsonb_to_recordset(:data::jsonb)
                          AS r(id text, doc_id text, chunk_index text,
                               user_group_id text, embedding_str text)
                        ON CONFLICT (id) DO NOTHING
                    """).bindparams(
                        data=json.dumps([
                            {
                                "id": row["id"],
                                "doc_id": row["doc_id"],
                                "chunk_index": str(row["chunk_index"]),
                                "user_group_id": str(row["user_group_id"]),
                                "embedding_str": row["embedding_str"],
                            }
                            for row in batch
                        ])
                    )
                )

        yield session
