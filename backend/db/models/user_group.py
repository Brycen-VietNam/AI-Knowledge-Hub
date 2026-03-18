# Spec: docs/specs/db-schema-embeddings.spec.md#S001
# Task: T002 — UserGroup ORM model
from datetime import datetime

from sqlalchemy import Identity, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
