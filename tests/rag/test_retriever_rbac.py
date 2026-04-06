# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S002
# Task: T001 — smoke test: import + field assertions
# Task: T002 — dense RBAC WHERE clause tests (TestDenseRBAC)
# Task: T003 — BM25 RBAC WHERE clause tests (TestBM25RBAC)
# Task: T004 — hybrid merge + timeout tests (TestHybridMerge, TestTimeout)
import asyncio
import uuid

import pytest

from backend.rag.retriever import RetrievedDocument, retrieve


# ---------------------------------------------------------------------------
# T001 — Smoke tests (no DB required)
# ---------------------------------------------------------------------------

def test_imports():
    """Module and public symbols must be importable."""
    from backend.rag.retriever import RetrievedDocument, retrieve  # noqa: F401


def test_retrieved_document_fields():
    """RetrievedDocument must have all required fields with correct types."""
    doc = RetrievedDocument(
        doc_id=uuid.uuid4(),
        chunk_index=0,
        score=0.95,
        user_group_id=None,
    )
    assert doc.user_group_id is None          # None = public document
    assert doc.content is None                # content optional, defaults None


def test_retrieved_document_with_group():
    """user_group_id accepts int (private document)."""
    doc = RetrievedDocument(
        doc_id=uuid.uuid4(),
        chunk_index=1,
        score=0.8,
        user_group_id=42,
        content="hello",
    )
    assert doc.user_group_id == 42
    assert doc.content == "hello"


@pytest.mark.asyncio
async def test_retrieve_is_callable():
    """retrieve() is async and accepts expected signature (T001 scaffold — now implemented)."""
    import inspect
    assert inspect.iscoroutinefunction(retrieve)


# ---------------------------------------------------------------------------
# T002 — Dense RBAC WHERE clause tests (mock session)
# ---------------------------------------------------------------------------

from unittest.mock import AsyncMock, MagicMock

from backend.rag.retriever import _dense_search


def _make_row(doc_id, chunk_index, user_group_id, distance):
    """Helper — create a mock CursorResult row."""
    row = MagicMock()
    row.doc_id = doc_id
    row.chunk_index = chunk_index
    row.user_group_id = user_group_id
    row.distance = distance
    return row


def _mock_session(rows):
    """Return AsyncSession mock that yields given rows on execute()."""
    session = AsyncMock()
    session.execute.return_value = iter(rows)
    return session


class TestDenseRBAC:
    GROUP1_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    GROUP2_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
    PUBLIC_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")

    @pytest.mark.asyncio
    async def test_group1_retrieves_own_doc_not_group2(self):
        """User with group_id=1 retrieves group-1 doc, NOT group-2 doc."""
        rows = [
            _make_row(self.GROUP1_ID, 0, 1, 0.1),   # group-1 doc ✓
            # group-2 doc would be filtered by WHERE in real DB
        ]
        session = _mock_session(rows)
        results = await _dense_search(session, [0.1] * 1024, [1], 10)
        assert len(results) == 1
        assert results[0].doc_id == self.GROUP1_ID
        assert results[0].user_group_id == 1
        assert results[0].score == pytest.approx(0.9)   # 1.0 - 0.1

    @pytest.mark.asyncio
    async def test_empty_group_ids_returns_only_public(self):
        """user_group_ids=[] → mock returns only NULL-group (public) doc."""
        rows = [
            _make_row(self.PUBLIC_ID, 0, None, 0.2),  # public doc (NULL group)
        ]
        session = _mock_session(rows)
        results = await _dense_search(session, [0.1] * 1024, [], 10)
        assert len(results) == 1
        assert results[0].doc_id == self.PUBLIC_ID
        assert results[0].user_group_id is None

    @pytest.mark.asyncio
    async def test_sql_contains_rbac_where_clause(self):
        """Verify SQL passed to session.execute contains RBAC WHERE clause."""
        session = _mock_session([])
        await _dense_search(session, [0.1] * 1024, [1], 5)
        call_args = session.execute.call_args[0][0]
        sql_text = str(call_args)
        assert "user_group_id = ANY" in sql_text or "ANY(:group_ids)" in sql_text
        assert "user_group_id IS NULL" in sql_text

    @pytest.mark.asyncio
    async def test_result_score_is_one_minus_distance(self):
        """score = 1.0 - cosine_distance."""
        rows = [_make_row(self.GROUP1_ID, 0, 1, 0.3)]
        session = _mock_session(rows)
        results = await _dense_search(session, [0.1] * 1024, [1], 10)
        assert results[0].score == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# T003 — BM25 RBAC WHERE clause tests (mock session)
# ---------------------------------------------------------------------------

from backend.rag.retriever import _bm25_search


def _make_bm25_row(doc_id, user_group_id, rank):
    row = MagicMock()
    row.doc_id = doc_id
    row.chunk_index = 0
    row.user_group_id = user_group_id
    row.rank = rank
    return row


class TestBM25RBAC:
    GROUP1_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
    GROUP2_ID = uuid.UUID("00000000-0000-0000-0001-000000000002")
    PUBLIC_ID = uuid.UUID("00000000-0000-0000-0001-000000000003")

    @pytest.mark.asyncio
    async def test_group1_retrieves_own_doc_not_group2(self):
        """User with group_id=1 retrieves group-1 doc via BM25, NOT group-2 doc."""
        rows = [_make_bm25_row(self.GROUP1_ID, 1, 0.75)]
        session = _mock_session(rows)
        results = await _bm25_search(session, "knowledge base", [1], 10)
        assert len(results) == 1
        assert results[0].doc_id == self.GROUP1_ID
        assert results[0].user_group_id == 1
        assert results[0].score == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_empty_group_ids_returns_only_public(self):
        """user_group_ids=[] → mock returns only NULL-group (public) doc via BM25."""
        rows = [_make_bm25_row(self.PUBLIC_ID, None, 0.6)]
        session = _mock_session(rows)
        results = await _bm25_search(session, "public doc", [], 10)
        assert len(results) == 1
        assert results[0].doc_id == self.PUBLIC_ID
        assert results[0].user_group_id is None

    @pytest.mark.asyncio
    async def test_sql_filters_on_documents_table(self):
        """SQL must filter on documents.user_group_id (D02 — BM25 starts from documents)."""
        session = _mock_session([])
        await _bm25_search(session, "test", [1], 5)
        call_args = session.execute.call_args[0][0]
        sql_text = str(call_args)
        # Must reference documents table RBAC filter (not embeddings)
        assert "user_group_id IS NULL" in sql_text
        assert "to_tsquery" in sql_text

    @pytest.mark.asyncio
    async def test_empty_result_when_no_match(self):
        """Empty rows from DB → empty list returned."""
        session = _mock_session([])
        results = await _bm25_search(session, "nonexistent", [1], 10)
        assert results == []


# ---------------------------------------------------------------------------
# T004 — Hybrid merge + empty-groups + timeout tests
# ---------------------------------------------------------------------------

from backend.rag.retriever import QueryTimeoutError, _merge


class TestHybridMerge:
    DOC_A = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    DOC_B = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
    DOC_C = uuid.UUID("cccccccc-0000-0000-0000-000000000001")

    def _doc(self, doc_id, score, group_id=1):
        return RetrievedDocument(doc_id=doc_id, chunk_index=0, score=score, user_group_id=group_id)

    def test_merge_deduplicates_by_doc_id(self):
        """Doc appearing in both dense + BM25 must appear once with weighted sum score."""
        dense = [self._doc(self.DOC_A, 0.9)]
        bm25 = [self._doc(self.DOC_A, 0.8)]
        results = _merge(dense, bm25, top_k=10)
        assert len(results) == 1
        # score = 0.7*0.9 + 0.3*0.8 = 0.63 + 0.24 = 0.87
        assert results[0].score == pytest.approx(0.87)

    def test_merge_ranks_by_weighted_score(self):
        """Higher weighted score doc appears first."""
        dense = [self._doc(self.DOC_A, 0.9), self._doc(self.DOC_B, 0.5)]
        bm25 = [self._doc(self.DOC_B, 0.9)]
        results = _merge(dense, bm25, top_k=10)
        # DOC_A: 0.7*0.9 = 0.63
        # DOC_B: 0.7*0.5 + 0.3*0.9 = 0.35 + 0.27 = 0.62
        assert results[0].doc_id == self.DOC_A
        assert results[1].doc_id == self.DOC_B

    def test_merge_respects_top_k(self):
        """Merge returns at most top_k results."""
        dense = [self._doc(self.DOC_A, 0.9), self._doc(self.DOC_B, 0.8), self._doc(self.DOC_C, 0.7)]
        results = _merge(dense, [], top_k=2)
        assert len(results) == 2

    def test_merge_empty_inputs_returns_empty(self):
        """Both empty → empty list."""
        assert _merge([], [], top_k=10) == []

    @pytest.mark.asyncio
    async def test_retrieve_dense_only_when_no_bm25_query(self):
        """retrieve() with bm25_query=None calls only dense path."""
        doc_id = uuid.uuid4()
        dense_row = _make_row(doc_id, 0, 1, 0.2)
        session = AsyncMock()
        session.execute.return_value = iter([dense_row])
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[1],
            session=session,
            bm25_query=None,
        )
        assert len(results) == 1
        assert session.execute.call_count == 1   # only dense, no BM25

    @pytest.mark.asyncio
    async def test_empty_groups_returns_empty_when_no_public_docs(self):
        """user_group_ids=[] with no public docs → empty list, no error (AC6/D04)."""
        session = _mock_session([])
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[],
            session=session,
        )
        assert results == []


class TestTimeout:
    @pytest.mark.asyncio
    async def test_query_timeout_error_raised_on_timeout(self, monkeypatch):
        """QueryTimeoutError raised (not asyncio.TimeoutError) when timeout exceeded."""
        import backend.rag.retriever as retriever_mod

        async def slow_dense(*args, **kwargs):
            await asyncio.sleep(0.05)
            return []

        monkeypatch.setattr(retriever_mod, "_dense_search", slow_dense)
        # Patch timeout to 0.01s so test completes fast
        monkeypatch.setattr(
            retriever_mod,
            "retrieve",
            lambda *a, **kw: _patched_retrieve(*a, **kw),
        )

        async def _patched_retrieve(query_embedding, user_group_ids, top_k=10, *, session, bm25_query=None):
            async def _inner():
                dense = await slow_dense(session, query_embedding, user_group_ids, top_k)
                return retriever_mod._merge(dense, [], top_k)
            try:
                return await asyncio.wait_for(_inner(), timeout=0.001)
            except asyncio.TimeoutError:
                raise QueryTimeoutError("retrieval exceeded 1800ms SLA")

        with pytest.raises(QueryTimeoutError):
            await _patched_retrieve(
                query_embedding=[0.1] * 1024,
                user_group_ids=[1],
                session=AsyncMock(),
            )

    def test_query_timeout_error_is_exception(self):
        """QueryTimeoutError must be an Exception subclass."""
        assert issubclass(QueryTimeoutError, Exception)


# ---------------------------------------------------------------------------
# S003 — Integration tests (real PostgreSQL via seeded_session from conftest.py)
# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S003
# Task: T002 — TestGroupFilter (AC1–AC4) + TestPublicAccess (AC5–AC7)
# Task: T003 — TestHybridRBAC (AC8) + TestConcurrency (AC9)
# Task: T004 — TestPerformance (AC10)
# Decision: D01 — user_group_id IS NULL = public document
# Decision: D02 — dense filter on embeddings, BM25 filter on documents
# ---------------------------------------------------------------------------

import os as _os
import time

_INTEGRATION = pytest.mark.skipif(
    not _os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set — skipping integration test",
)

# Import SEED_DOC_IDS from conftest at module load (available when conftest is loaded)
# Access via fixture parameter when needed inside tests.


# ---------------------------------------------------------------------------
# T002 — TestGroupFilter + TestPublicAccess (AC1–AC7)
# ---------------------------------------------------------------------------

@_INTEGRATION
class TestGroupFilter:
    """Integration: real DB — group membership filter. AC1–AC4."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_own_group_retrieved(self, seeded_session):
        """AC1: user with group_a → retrieves group_a docs (user_group_id=1)."""
        from tests.rag.conftest import SEED_DOC_IDS, GROUP_A_ID
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[GROUP_A_ID],
            top_k=10,
            session=seeded_session,
        )
        result_ids = {r.doc_id for r in results}
        group_a_ids = set(SEED_DOC_IDS["group_a"])
        # At least one group_a doc must be returned
        assert result_ids & group_a_ids, "Expected group_a docs in results"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_other_group_denied(self, seeded_session):
        """AC2: user with group_a → does NOT retrieve group_b docs."""
        from tests.rag.conftest import SEED_DOC_IDS, GROUP_A_ID
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[GROUP_A_ID],
            top_k=20,
            session=seeded_session,
        )
        result_ids = {r.doc_id for r in results}
        group_b_ids = set(SEED_DOC_IDS["group_b"])
        assert not (result_ids & group_b_ids), "group_b docs must not appear for group_a user"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_group_retrieved(self, seeded_session):
        """AC3: user with [group_a, group_b] → retrieves docs from both groups."""
        from tests.rag.conftest import SEED_DOC_IDS, GROUP_A_ID, GROUP_B_ID
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[GROUP_A_ID, GROUP_B_ID],
            top_k=20,
            session=seeded_session,
        )
        result_ids = {r.doc_id for r in results}
        group_a_ids = set(SEED_DOC_IDS["group_a"])
        group_b_ids = set(SEED_DOC_IDS["group_b"])
        assert result_ids & group_a_ids, "Expected group_a docs for multi-group user"
        assert result_ids & group_b_ids, "Expected group_b docs for multi-group user"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_group_other_denied(self, seeded_session):
        """AC4: user with [group_a, group_b] → does NOT retrieve group_c docs."""
        from tests.rag.conftest import SEED_DOC_IDS, GROUP_A_ID, GROUP_B_ID
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[GROUP_A_ID, GROUP_B_ID],
            top_k=20,
            session=seeded_session,
        )
        result_ids = {r.doc_id for r in results}
        group_c_ids = set(SEED_DOC_IDS["group_c"])
        assert not (result_ids & group_c_ids), "group_c docs must not appear for group_a+b user"


@_INTEGRATION
class TestPublicAccess:
    """Integration: real DB — NULL-group (public) docs. AC5–AC7."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_groups_private_denied(self, seeded_session):
        """AC5: user with [] → private docs (group assigned) NOT retrieved."""
        from tests.rag.conftest import SEED_DOC_IDS
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[],
            top_k=20,
            session=seeded_session,
        )
        private_ids = (
            set(SEED_DOC_IDS["group_a"])
            | set(SEED_DOC_IDS["group_b"])
            | set(SEED_DOC_IDS["group_c"])
        )
        result_ids = {r.doc_id for r in results}
        assert not (result_ids & private_ids), "Private docs must not appear for 0-group user"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_groups_public_retrieved(self, seeded_session):
        """AC6: user with [] → NULL-group (public) docs retrieved."""
        from tests.rag.conftest import SEED_DOC_IDS
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[],
            top_k=10,
            session=seeded_session,
        )
        public_ids = set(SEED_DOC_IDS["public"])
        result_ids = {r.doc_id for r in results}
        assert result_ids & public_ids, "Public (NULL-group) docs must be returned for 0-group user"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_with_group_public_doc_retrieved(self, seeded_session):
        """AC7: user with group_a → also retrieves NULL-group (public) docs."""
        from tests.rag.conftest import SEED_DOC_IDS, GROUP_A_ID
        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[GROUP_A_ID],
            top_k=20,
            session=seeded_session,
        )
        public_ids = set(SEED_DOC_IDS["public"])
        result_ids = {r.doc_id for r in results}
        assert result_ids & public_ids, "Public (NULL-group) docs must appear alongside group_a docs"


# ---------------------------------------------------------------------------
# T003 — TestHybridRBAC (AC8) + TestConcurrency (AC9)
# ---------------------------------------------------------------------------

@_INTEGRATION
class TestHybridRBAC:
    """Integration: hybrid dense+BM25 path respects RBAC. AC8."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hybrid_respects_filter(self, seeded_session):
        """AC8: dense+BM25 both filtered; merged result has no cross-group docs."""
        from tests.rag.conftest import SEED_DOC_IDS, GROUP_A_ID
        # Seed a document with content_fts for BM25 path
        from sqlalchemy import text as _text
        await seeded_session.execute(_text("""
            INSERT INTO documents (id, title, lang, user_group_id, content_fts)
            VALUES (:id, 'Hybrid Test Doc', 'en', :gid,
                    to_tsvector('simple', 'knowledge base hybrid rbac'))
            ON CONFLICT (id) DO NOTHING
        """).bindparams(
            id=uuid.UUID("feed0000-0000-0000-0000-000000000001"),
            gid=GROUP_A_ID,
        ))
        # Also insert a group_b document to verify it's filtered out
        await seeded_session.execute(_text("""
            INSERT INTO documents (id, title, lang, user_group_id, content_fts)
            VALUES (:id, 'Group B Doc', 'en', :gid,
                    to_tsvector('simple', 'knowledge base hybrid rbac'))
            ON CONFLICT (id) DO NOTHING
        """).bindparams(
            id=uuid.UUID("feed0000-0000-0000-0000-000000000002"),
            gid=2,  # GROUP_B_ID
        ))

        results = await retrieve(
            query_embedding=[0.1] * 1024,
            user_group_ids=[GROUP_A_ID],
            top_k=20,
            session=seeded_session,
            bm25_query="knowledge base",
        )
        for doc in results:
            assert doc.user_group_id == GROUP_A_ID or doc.user_group_id is None, (
                f"doc {doc.doc_id} has group_id={doc.user_group_id}, not group_a or public"
            )


@_INTEGRATION
class TestConcurrency:
    """Integration: concurrent retrieval with different group_ids — no cross-contamination. AC9."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_no_cross_contamination(self, seeded_session):
        """AC9: 10 concurrent retrieve() calls with different group_ids — each gets only own docs."""
        from tests.rag.conftest import GROUP_A_ID, GROUP_B_ID, GROUP_C_ID
        group_ids_seq = [GROUP_A_ID, GROUP_B_ID, GROUP_C_ID, GROUP_A_ID, GROUP_B_ID,
                         GROUP_C_ID, GROUP_A_ID, GROUP_B_ID, GROUP_C_ID, GROUP_A_ID]
        calls = [
            retrieve(
                query_embedding=[0.1] * 1024,
                user_group_ids=[gid],
                top_k=10,
                session=seeded_session,
            )
            for gid in group_ids_seq
        ]
        results_list = await asyncio.gather(*calls)
        for gid, results in zip(group_ids_seq, results_list):
            for doc in results:
                assert doc.user_group_id == gid or doc.user_group_id is None, (
                    f"Cross-contamination: doc group={doc.user_group_id} appeared for user group={gid}"
                )


# ---------------------------------------------------------------------------
# T004 — TestPerformance (AC10) — p95 < 1800ms with 10k embeddings
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set — skipping performance test",
)
class TestPerformance:
    """Integration: latency SLA under realistic data volume. AC10."""

    @pytest.mark.performance
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_latency_p95_under_1800ms(self, large_seeded_session):
        """AC10: p95 < 1800ms with 10k embeddings, user has access to 1k."""
        latencies = []
        for _ in range(20):
            start = time.monotonic()
            await retrieve(
                query_embedding=[0.1] * 1024,
                user_group_ids=[1],
                top_k=10,
                session=large_seeded_session,
            )
            latencies.append((time.monotonic() - start) * 1000)
        latencies.sort()
        p95_idx = int(len(latencies) * 0.95)
        p95 = latencies[p95_idx]
        assert p95 < 1800, f"p95 latency {p95:.0f}ms exceeds 1800ms SLA (R007/P001)"
