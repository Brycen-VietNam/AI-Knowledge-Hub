# Spec: docs/specs/db-schema-embeddings.spec.md#S004
# Task: T001 — Async engine + session factory
# Decision: D03 — asyncpg driver (postgresql+asyncpg://)
# Decision: D04 — pool_size=5, max_overflow=15 (effective max=20, C011)
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL")

# Guard: engine is None when DATABASE_URL is unset (e.g. during ORM unit tests).
# Production startup will fail fast if DATABASE_URL is missing via health check.
engine = (
    create_async_engine(DATABASE_URL, pool_size=5, max_overflow=15, pool_pre_ping=True)
    if DATABASE_URL
    else None
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False) if engine else None
