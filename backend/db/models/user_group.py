# Spec: docs/specs/db-schema-embeddings.spec.md#S001
# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T002 — UserGroup ORM model
# Task: S000/T002 — add is_admin field (migration 009)
from datetime import datetime

from sqlalchemy import Identity, func, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    is_admin: Mapped[bool] = mapped_column(nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
