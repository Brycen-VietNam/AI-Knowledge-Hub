# Spec: docs/specs/db-schema-embeddings.spec.md#S001
# Task: T002 — Shared DeclarativeBase for all ORM models
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
