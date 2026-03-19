# Spec: docs/specs/db-schema-embeddings.spec.md#S004
# Task: T001 — Unit tests for session.py
# No live DB required — introspect engine config + isinstance checks
import os

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def test_session_imports():
    """engine and async_session_factory must be importable from backend.db.session."""
    from backend.db.session import async_session_factory, engine
    assert engine is not None
    assert async_session_factory is not None


def test_engine_is_async():
    """engine must be an AsyncEngine instance."""
    from backend.db.session import engine
    assert isinstance(engine, AsyncEngine)


def test_session_factory_is_async_sessionmaker():
    """async_session_factory must be an async_sessionmaker instance."""
    from backend.db.session import async_session_factory
    assert isinstance(async_session_factory, async_sessionmaker)


def test_session_factory_class_is_async_session():
    """Sessions produced by factory must be AsyncSession."""
    from backend.db.session import async_session_factory
    assert async_session_factory.class_ is AsyncSession


def test_pool_size():
    """pool_size must be 5 (D04, C011)."""
    from backend.db.session import engine
    assert engine.pool.size() == 5


def test_pool_max_overflow():
    """max_overflow must be 15 — effective max connections = 20 (D04, C011)."""
    from backend.db.session import engine
    assert engine.pool._max_overflow == 15


def test_db_package_exports():
    """async_session_factory and engine must be importable from backend.db package."""
    from backend.db import async_session_factory as sf, engine as eng
    assert sf is not None
    assert eng is not None
