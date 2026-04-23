# Spec: docs/specs/auth-api-key-oidc.spec.md#S001
# Spec: docs/change-password/spec/change-password.spec.md#S001
# Task: T002 — User ORM model
# Task: S001/T002 — add must_change_password field
import uuid
from datetime import datetime

from sqlalchemy import func, text as sa_text
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
    must_change_password: Mapped[bool] = mapped_column(
        nullable=False, server_default=sa_text("TRUE"), default=True
    )
