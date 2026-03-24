# Spec: docs/specs/auth-api-key-oidc.spec.md#S001
# Task: T002 — User ORM model
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sub: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(nullable=True)
    display_name: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
