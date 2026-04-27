# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T005 — scaffold + require_admin + document endpoints (AC4, AC5, AC15)
# Task: T006 — group CRUD (AC6–AC9)
# Task: T007 — user endpoints (AC10–AC12, D10) + GET /v1/metrics (D09)
# Spec: docs/user-management/spec/user-management.spec.md#S001
# Task: S001/T001 — UserCreate Pydantic model
# Task: S001/T002 — POST /v1/admin/users handler (duplicate check + bcrypt + INSERT)
# Task: S001/T003 — Group membership insert in same transaction
# Rule: R003 — all /v1/admin/* use require_admin (wraps verify_token); /v1/metrics same
# Rule: R004 — /v1/ prefix on all routes
# Rule: R006 — audit log on document delete (admin action)
# Rule: S001 — parameterized SQL only: text().bindparams(); no f-string user-value injection
# Rule: A005 — error shape: {"error": {"code", "message", "request_id"}}
# Rule: P004 — no N+1 queries (subquery/JOIN for user_count, group lists)
import hashlib
import re
import secrets
import uuid
from typing import Annotated, Any, List, Optional

import bcrypt as _bcrypt_lib
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.auth.utils import generate_password

router = APIRouter()


def _error(request_id: str, code: str, message: str) -> dict:
    """A005-compliant error shape."""
    return {"error": {"code": code, "message": message, "request_id": request_id}}


# ---------------------------------------------------------------------------
# Admin guard dependency (AC15)
# ---------------------------------------------------------------------------

async def require_admin(
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
) -> AuthenticatedUser:
    """Raise 403 FORBIDDEN if authenticated user is not an admin.

    # Spec: docs/admin-spa/spec/admin-spa.spec.md#S000/AC15
    # Rule: R003 — wraps verify_token; does not duplicate auth logic
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Admin access required",
                    "request_id": str(uuid.uuid4()),
                }
            },
        )
    return user


# ---------------------------------------------------------------------------
# Audit log helper
# ---------------------------------------------------------------------------

async def _write_audit_log(user_id: uuid.UUID, doc_id: uuid.UUID) -> None:
    """Write audit_log for admin document delete (R006). Opens own session."""
    from backend.db.models.audit_log import AuditLog
    from backend.db.session import async_session_factory

    async with async_session_factory() as session:
        async with session.begin():
            session.add(AuditLog(user_id=user_id, doc_id=doc_id, query_hash="ADMIN_DELETE"))


# ---------------------------------------------------------------------------
# T005: Document endpoints (AC4, AC5)
# ---------------------------------------------------------------------------

@router.get("/v1/admin/documents")
async def admin_list_documents(
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    lang: str | None = None,
    user_group_id: int | None = None,
) -> JSONResponse:
    """AC4: List ALL documents (no RBAC filter), paginated. Admin only.
    Optional filters: status, lang, user_group_id.
    """
    request_id = str(uuid.uuid4())

    if limit > 100:
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", "limit must not exceed 100"),
        )

    # Build dynamic WHERE conditions — S001: values always parameterized.
    # where_clause is assembled from static string literals only (never user data).
    conditions: list[str] = []
    bind_params: dict = {"limit": limit, "offset": offset}

    if status is not None:
        conditions.append("d.status = :status")
        bind_params["status"] = status
    if lang is not None:
        conditions.append("d.lang = :lang")
        bind_params["lang"] = lang
    if user_group_id is not None:
        conditions.append("d.user_group_id = :user_group_id")
        bind_params["user_group_id"] = user_group_id

    # Static fragment list — no user input injected into SQL text
    base_select = (
        "SELECT d.id, d.title, d.lang, d.user_group_id, g.name AS user_group_name, d.status, d.created_at, "
        "(SELECT COUNT(*) FROM embeddings e WHERE e.doc_id = d.id) AS chunk_count "
        "FROM documents d "
        "LEFT JOIN user_groups g ON d.user_group_id = g.id"
    )
    base_count = "SELECT COUNT(*) FROM documents d"
    filter_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    filter_params = {k: v for k, v in bind_params.items() if k not in ("limit", "offset")}

    stmt = text(
        base_select + filter_sql + " ORDER BY d.created_at DESC LIMIT :limit OFFSET :offset"
    ).bindparams(**bind_params)

    count_stmt = text(base_count + filter_sql).bindparams(**filter_params)

    rows = (await db.execute(stmt)).mappings().all()
    total = (await db.execute(count_stmt)).scalar()

    items = [
        {
            "id": str(r["id"]),
            "title": r["title"],
            "lang": r["lang"],
            "user_group_id": r["user_group_id"],
            "user_group_name": r["user_group_name"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
            "chunk_count": r["chunk_count"],
        }
        for r in rows
    ]
    return JSONResponse(content={"items": items, "total": total, "limit": limit, "offset": offset})


@router.delete("/v1/admin/documents/{doc_id}")
async def admin_delete_document(
    doc_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC5: Delete document + cascade embeddings. Audit log required (R006)."""
    request_id = str(uuid.uuid4())

    exists = (await db.execute(
        text("SELECT id FROM documents WHERE id = :doc_id").bindparams(doc_id=doc_id)
    )).fetchone()
    if exists is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "Document not found"),
        )

    # R006: write audit log before delete
    await _write_audit_log(user.user_id, doc_id)

    # Remove existing audit_log rows referencing this doc (FK constraint, no CASCADE)
    await db.execute(text("DELETE FROM audit_logs WHERE doc_id = :doc_id").bindparams(doc_id=doc_id))
    await db.execute(text("DELETE FROM documents WHERE id = :doc_id").bindparams(doc_id=doc_id))
    await db.commit()

    return JSONResponse(content={"deleted": str(doc_id)})


# ---------------------------------------------------------------------------
# T006: Group CRUD (AC6–AC9)
# ---------------------------------------------------------------------------

class GroupCreate(BaseModel):
    name: str = Field(..., max_length=200)
    is_admin: bool = False


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    is_admin: bool | None = None


@router.get("/v1/admin/groups")
async def admin_list_groups(
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC6: List all user_groups with user_count (subquery — no N+1)."""
    stmt = text(
        "SELECT ug.id, ug.name, ug.is_admin, ug.created_at, "
        "(SELECT COUNT(*) FROM user_group_memberships ugm WHERE ugm.group_id = ug.id) AS user_count "
        "FROM user_groups ug "
        "ORDER BY ug.id"
    )
    rows = (await db.execute(stmt)).mappings().all()
    return JSONResponse(content={"items": [
        {
            "id": r["id"],
            "name": r["name"],
            "is_admin": r["is_admin"],
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
            "user_count": r["user_count"],
        }
        for r in rows
    ]})


@router.post("/v1/admin/groups")
async def admin_create_group(
    body: GroupCreate,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC7: Create new user_group. Returns 201 with full row."""
    stmt = text(
        "INSERT INTO user_groups (name, is_admin) "
        "VALUES (:name, :is_admin) "
        "RETURNING id, name, is_admin, created_at"
    ).bindparams(name=body.name, is_admin=body.is_admin)

    row = (await db.execute(stmt)).mappings().first()
    await db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "id": row["id"],
            "name": row["name"],
            "is_admin": row["is_admin"],
            "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
        },
    )


@router.put("/v1/admin/groups/{group_id}")
async def admin_update_group(
    group_id: int,
    body: GroupUpdate,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC8: Update group name and/or is_admin flag."""
    request_id = str(uuid.uuid4())

    # S001: static SQL per case — no dynamic construction, no f-string interpolation
    params: dict[str, Any] = {"group_id": group_id}
    if body.name is not None and body.is_admin is not None:
        params["name"] = body.name
        params["is_admin"] = body.is_admin
        sql = "UPDATE user_groups SET name = :name, is_admin = :is_admin WHERE id = :group_id RETURNING id, name, is_admin, created_at"
    elif body.name is not None:
        params["name"] = body.name
        sql = "UPDATE user_groups SET name = :name WHERE id = :group_id RETURNING id, name, is_admin, created_at"
    elif body.is_admin is not None:
        params["is_admin"] = body.is_admin
        sql = "UPDATE user_groups SET is_admin = :is_admin WHERE id = :group_id RETURNING id, name, is_admin, created_at"
    else:
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", "No fields to update"),
        )

    stmt = text(sql).bindparams(**params)

    row = (await db.execute(stmt)).mappings().first()
    if row is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "Group not found"),
        )
    await db.commit()
    return JSONResponse(content={
        "id": row["id"],
        "name": row["name"],
        "is_admin": row["is_admin"],
        "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
    })


@router.delete("/v1/admin/groups/{group_id}")
async def admin_delete_group(
    group_id: int,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC9: Delete group. 409 if group has users. Audit not required (no doc_id)."""
    request_id = str(uuid.uuid4())

    exists = (await db.execute(
        text("SELECT id FROM user_groups WHERE id = :group_id").bindparams(group_id=group_id)
    )).fetchone()
    if exists is None:
        return JSONResponse(status_code=404, content=_error(request_id, "NOT_FOUND", "Group not found"))

    # AC9: refuse deletion if users are still in the group
    member_count = (await db.execute(
        text("SELECT COUNT(*) FROM user_group_memberships WHERE group_id = :group_id")
        .bindparams(group_id=group_id)
    )).scalar()
    if member_count > 0:
        return JSONResponse(
            status_code=409,
            content=_error(
                request_id,
                "GROUP_HAS_USERS",
                f"Cannot delete group: {member_count} user(s) still assigned",
            ),
        )

    await db.execute(text("DELETE FROM user_groups WHERE id = :group_id").bindparams(group_id=group_id))
    await db.commit()
    return JSONResponse(content={"deleted": group_id})


# ---------------------------------------------------------------------------
# T007: User endpoints (AC10–AC12, D10) + /v1/metrics (D09)
# ---------------------------------------------------------------------------

class UserGroupAssign(BaseModel):
    group_ids: list[int]


class UserActiveUpdate(BaseModel):
    is_active: bool


# ---------------------------------------------------------------------------
# S001/T001: UserCreate Pydantic model
# Spec: docs/user-management/spec/user-management.spec.md#S001
# Rule: S003 — validated at entry; sub pattern enforced by Pydantic
# ---------------------------------------------------------------------------

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class UserCreate(BaseModel):
    sub: str = Field(..., min_length=3, max_length=200, pattern=r"^[a-zA-Z0-9_.@-]+$")
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(default=None, max_length=200)
    password: str = Field(..., min_length=12)
    group_ids: List[int] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# S003/T001: ApiKeyCreate model + key generation helper
# Spec: docs/user-management/spec/user-management.spec.md#S003
# Decision: D5 — key format kh_<secrets.token_hex(16)>; SHA-256 hash stored
# Rule: S005 — plaintext key never stored; only SHA-256 hash in DB
# ---------------------------------------------------------------------------

class ApiKeyCreate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)


def _generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (plaintext, key_hash, key_prefix).

    plaintext  : kh_ + 32 hex chars (35 chars total) — returned once, never stored.
    key_hash   : SHA-256 hex digest of plaintext — stored in DB.
    key_prefix : first 8 chars of plaintext — stored for identification.
    """
    plaintext = "kh_" + secrets.token_hex(16)
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    key_prefix = plaintext[:8]
    return plaintext, key_hash, key_prefix


# ---------------------------------------------------------------------------
# S001/T002 + T003: POST /v1/admin/users — create user + group memberships
# Spec: docs/user-management/spec/user-management.spec.md#S001
# Rule: R003 — require_admin dependency
# Rule: R004 — /v1/admin/ prefix
# Rule: S001 — text().bindparams() only; no f-string injection
# Rule: S003 — strip control chars from string fields
# Rule: A005 — error shape {"error": {"code", "message", "request_id"}}
# Rule: P004 — single SELECT IN for group fetch (not N+1)
# Decision: D5 — bcrypt rounds=12 via direct bcrypt library (not passlib)
# ---------------------------------------------------------------------------

@router.post("/v1/admin/users", dependencies=[Depends(require_admin)], status_code=201)
async def admin_create_user(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """S001: Create a new user with bcrypt-hashed password and optional group memberships.

    Returns 201 {id, sub, email, display_name, is_active, groups}.
    409 SUB_CONFLICT if sub already exists.
    """
    request_id = str(uuid.uuid4())

    # S003: strip leading/trailing whitespace and control chars from string fields
    sub = _CONTROL_CHAR_RE.sub("", body.sub.strip())
    display_name = (
        _CONTROL_CHAR_RE.sub("", body.display_name.strip())
        if body.display_name is not None
        else None
    )

    # Duplicate sub check — 409 SUB_CONFLICT (A005 shape)
    existing = (await db.execute(
        text("SELECT id FROM users WHERE sub = :sub").bindparams(sub=sub)
    )).fetchone()
    if existing is not None:
        return JSONResponse(
            status_code=409,
            content=_error(request_id, "SUB_CONFLICT", f"User with sub '{sub}' already exists"),
        )

    # bcrypt hash — rounds=12; plaintext never stored or logged (S005)
    password_hash: str = _bcrypt_lib.hashpw(
        body.password.encode(), _bcrypt_lib.gensalt(rounds=12)
    ).decode()

    # T002: INSERT user — S001 parameterized
    try:
        user_row = (await db.execute(
            text(
                "INSERT INTO users (sub, email, display_name, password_hash, is_active) "
                "VALUES (:sub, :email, :display_name, :password_hash, TRUE) "
                "RETURNING id, sub, email, display_name, is_active"
            ).bindparams(
                sub=sub,
                email=str(body.email) if body.email is not None else None,
                display_name=display_name,
                password_hash=password_hash,
            )
        )).mappings().first()

        new_user_id: uuid.UUID = user_row["id"]

        # T003: group memberships in the same transaction — ON CONFLICT DO NOTHING
        if body.group_ids:
            for gid in body.group_ids:
                await db.execute(
                    text(
                        "INSERT INTO user_group_memberships (user_id, group_id) "
                        "VALUES (:user_id, :group_id) ON CONFLICT DO NOTHING"
                    ).bindparams(user_id=new_user_id, group_id=gid)
                )

        await db.commit()

    except Exception:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content=_error(request_id, "INTERNAL_ERROR", "Failed to create user"),
        )

    # T003: fetch groups with single IN query — P004 (no N+1)
    groups: list[dict] = []
    if body.group_ids:
        group_rows = (await db.execute(
            text(
                "SELECT id, name, is_admin FROM user_groups "
                "WHERE id = ANY(:group_ids)"
            ).bindparams(group_ids=list(body.group_ids))
        )).mappings().all()
        groups = [
            {"id": r["id"], "name": r["name"], "is_admin": r["is_admin"]}
            for r in group_rows
        ]

    return JSONResponse(
        status_code=201,
        content={
            "id": str(new_user_id),
            "sub": user_row["sub"],
            "email": user_row["email"],
            "display_name": user_row["display_name"],
            "is_active": user_row["is_active"],
            "groups": groups,
        },
    )


# ---------------------------------------------------------------------------
# S002/T001+T002: DELETE /v1/admin/users/{user_id} — cascade delete
# Spec: docs/user-management/spec/user-management.spec.md#S002
# Rule: R003 — require_admin dependency
# Rule: R004 — /v1/admin/ prefix
# Rule: S001 — text().bindparams() only; no f-string injection
# Rule: A005 — 404/500 error shape
# Delete order: api_keys → user_group_memberships → users (FK safety)
# audit_logs.user_id — NOT deleted; FK is ON DELETE SET NULL (migration 011)
# ---------------------------------------------------------------------------

@router.delete("/v1/admin/users/{user_id}", dependencies=[Depends(require_admin)])
async def admin_delete_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """S002: Delete user + cascade api_keys and group memberships.

    audit_logs rows are preserved with user_id set to NULL (migration 011).
    Returns 200 {"deleted": "<uuid>"}.
    404 NOT_FOUND if user does not exist.
    """
    request_id = str(uuid.uuid4())

    # Existence check — 404 before any DELETE (A005 shape)
    exists = (await db.execute(
        text("SELECT id FROM users WHERE id = :user_id").bindparams(user_id=user_id)
    )).fetchone()
    if exists is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "User not found"),
        )

    # T001+T002: cascade deletes in a single transaction — S001 parameterized
    try:
        # 1. api_keys (references users.id)
        await db.execute(
            text("DELETE FROM api_keys WHERE user_id = :user_id").bindparams(user_id=user_id)
        )
        # 2. user_group_memberships (references users.id)
        await db.execute(
            text("DELETE FROM user_group_memberships WHERE user_id = :user_id").bindparams(user_id=user_id)
        )
        # 3. users row (audit_logs.user_id → SET NULL by DB — no explicit DELETE needed)
        await db.execute(
            text("DELETE FROM users WHERE id = :user_id").bindparams(user_id=user_id)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content=_error(request_id, "INTERNAL_ERROR", "Failed to delete user"),
        )

    return JSONResponse(content={"deleted": str(user_id)})


# ---------------------------------------------------------------------------
# S003/T002: POST /v1/admin/users/{user_id}/api-keys — generate API key
# Spec: docs/user-management/spec/user-management.spec.md#S003
# Rule: R003 — require_admin dependency
# Rule: R004 — /v1/admin/ prefix
# Rule: S001 — text().bindparams() only; no f-string injection
# Rule: S003 — strip whitespace from name field
# Rule: S005 — plaintext key NEVER stored; only SHA-256 hash in DB
# Decision: D5 — key format kh_<secrets.token_hex(16)>; returned once
# ---------------------------------------------------------------------------

@router.post(
    "/v1/admin/users/{user_id}/api-keys",
    dependencies=[Depends(require_admin)],
    status_code=201,
)
async def admin_generate_api_key(
    user_id: uuid.UUID,
    body: ApiKeyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """S003: Generate a new API key for a user.

    Returns 201 {key_id, key (plaintext — shown once), key_prefix, name, created_at}.
    404 NOT_FOUND if user does not exist.
    Only the SHA-256 hash is stored — plaintext is never persisted (S005).
    """
    request_id = str(uuid.uuid4())

    # Existence check — 404 before any INSERT (A005 shape)
    exists = (await db.execute(
        text("SELECT id FROM users WHERE id = :user_id").bindparams(user_id=user_id)
    )).fetchone()
    if exists is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "User not found"),
        )

    # S003: strip whitespace from name
    name: str | None = (
        _CONTROL_CHAR_RE.sub("", body.name.strip()) if body.name is not None else None
    )

    # Generate key — plaintext returned once, hash stored (S005)
    plaintext, key_hash, key_prefix = _generate_api_key()
    key_id = uuid.uuid4()

    # INSERT api_key — S001 parameterized
    try:
        row = (await db.execute(
            text(
                "INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name) "
                "VALUES (:id, :user_id, :key_hash, :key_prefix, :name) "
                "RETURNING id, key_prefix, name, created_at"
            ).bindparams(
                id=key_id,
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
            )
        )).mappings().first()
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content=_error(request_id, "INTERNAL_ERROR", "Failed to create API key"),
        )

    return JSONResponse(
        status_code=201,
        content={
            "key_id": str(row["id"]),
            "key": plaintext,
            "key_prefix": row["key_prefix"],
            "name": row["name"],
            "created_at": (
                row["created_at"].isoformat()
                if hasattr(row["created_at"], "isoformat")
                else str(row["created_at"])
            ),
        },
    )


# ---------------------------------------------------------------------------
# S004/T001: GET /v1/admin/users/{user_id}/api-keys — list keys (no hash)
# Spec: docs/user-management/spec/user-management.spec.md#S004
# Rule: R003 — require_admin; R004 — /v1/admin/
# Rule: S001 — text().bindparams(); S005 — key_hash NEVER selected or returned
# ---------------------------------------------------------------------------

@router.get(
    "/v1/admin/users/{user_id}/api-keys",
    dependencies=[Depends(require_admin)],
)
async def admin_list_api_keys(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """S004: List all API keys for a user (no hash, no plaintext).

    Returns 200 {"items": [{key_id, key_prefix, name, created_at}, ...]}.
    404 NOT_FOUND if user does not exist.
    """
    request_id = str(uuid.uuid4())

    exists = (await db.execute(
        text("SELECT id FROM users WHERE id = :user_id").bindparams(user_id=user_id)
    )).fetchone()
    if exists is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "User not found"),
        )

    # S005: SELECT only id, key_prefix, name, created_at — never key_hash
    rows = (await db.execute(
        text(
            "SELECT id AS key_id, key_prefix, name, created_at "
            "FROM api_keys WHERE user_id = :user_id ORDER BY created_at DESC"
        ).bindparams(user_id=user_id)
    )).mappings().all()

    return JSONResponse(content={"items": [
        {
            "key_id": str(r["key_id"]),
            "key_prefix": r["key_prefix"],
            "name": r["name"],
            "created_at": (
                r["created_at"].isoformat()
                if hasattr(r["created_at"], "isoformat")
                else str(r["created_at"])
            ),
        }
        for r in rows
    ]})


# ---------------------------------------------------------------------------
# S004/T002: DELETE /v1/admin/users/{user_id}/api-keys/{key_id} — revoke key
# Spec: docs/user-management/spec/user-management.spec.md#S004
# Rule: R003 — require_admin; R004 — /v1/admin/
# Rule: S001 — text().bindparams()
# Security: WHERE includes both key_id AND user_id — prevents cross-user key enumeration
# ---------------------------------------------------------------------------

@router.delete(
    "/v1/admin/users/{user_id}/api-keys/{key_id}",
    dependencies=[Depends(require_admin)],
)
async def admin_revoke_api_key(
    user_id: uuid.UUID,
    key_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """S004: Revoke (delete) a specific API key belonging to a user.

    Returns 200 {"revoked": "<key_id>"}.
    404 NOT_FOUND if user or key does not exist / key does not belong to user.
    """
    request_id = str(uuid.uuid4())

    # User existence check
    user_exists = (await db.execute(
        text("SELECT id FROM users WHERE id = :user_id").bindparams(user_id=user_id)
    )).fetchone()
    if user_exists is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "User not found"),
        )

    # DELETE with both key_id AND user_id — prevents cross-user key access
    try:
        result = await db.execute(
            text(
                "DELETE FROM api_keys WHERE id = :key_id AND user_id = :user_id "
                "RETURNING id"
            ).bindparams(key_id=key_id, user_id=user_id)
        )
        if result.fetchone() is None:
            return JSONResponse(
                status_code=404,
                content=_error(request_id, "NOT_FOUND", "API key not found"),
            )
        await db.commit()
    except Exception:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content=_error(request_id, "INTERNAL_ERROR", "Failed to revoke API key"),
        )

    return JSONResponse(content={"revoked": str(key_id)})


@router.get("/v1/admin/users")
async def admin_list_users(
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC10: List all users with group memberships. Single JOIN — no N+1 (P004)."""
    stmt = text(
        "SELECT u.id, u.sub, u.email, u.display_name, u.is_active, "
        "(u.password_hash IS NOT NULL) AS has_password, "
        "COALESCE(json_agg(json_build_object('id', ug.id, 'name', ug.name, 'is_admin', ug.is_admin)) "
        "FILTER (WHERE ug.id IS NOT NULL), '[]') AS groups "
        "FROM users u "
        "LEFT JOIN user_group_memberships ugm ON ugm.user_id = u.id "
        "LEFT JOIN user_groups ug ON ug.id = ugm.group_id "
        "GROUP BY u.id, u.sub, u.email, u.display_name, u.is_active, u.password_hash "
        "ORDER BY u.sub"
    )
    rows = (await db.execute(stmt)).mappings().all()
    return JSONResponse(content={"items": [
        {
            "id": str(r["id"]),
            "sub": r["sub"],
            "email": r["email"],
            "display_name": r["display_name"],
            "is_active": r["is_active"],
            "has_password": bool(r["has_password"]),
            "groups": r["groups"],
        }
        for r in rows
    ]})


@router.put("/v1/admin/users/{user_id}")
async def admin_update_user(
    user_id: uuid.UUID,
    body: UserActiveUpdate,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """D10: Toggle is_active flag for a user. 404 if user not found."""
    request_id = str(uuid.uuid4())
    stmt = text(
        "UPDATE users SET is_active = :is_active WHERE id = :user_id "
        "RETURNING id, sub, is_active"
    ).bindparams(is_active=body.is_active, user_id=user_id)

    row = (await db.execute(stmt)).mappings().first()
    if row is None:
        return JSONResponse(status_code=404, content=_error(request_id, "NOT_FOUND", "User not found"))
    await db.commit()
    return JSONResponse(content={"id": str(row["id"]), "sub": row["sub"], "is_active": row["is_active"]})


@router.post("/v1/admin/users/{user_id}/groups")
async def admin_assign_user_groups(
    user_id: uuid.UUID,
    body: UserGroupAssign,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC11: Batch assign user to groups. ON CONFLICT DO NOTHING (upsert-safe)."""
    request_id = str(uuid.uuid4())
    if not body.group_ids:
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", "group_ids must not be empty"),
        )

    for group_id in body.group_ids:
        await db.execute(
            text(
                "INSERT INTO user_group_memberships (user_id, group_id) "
                "VALUES (:user_id, :group_id) ON CONFLICT DO NOTHING"
            ).bindparams(user_id=user_id, group_id=group_id)
        )
    await db.commit()
    return JSONResponse(content={"user_id": str(user_id), "group_ids": body.group_ids})


@router.delete("/v1/admin/users/{user_id}/groups/{group_id}")
async def admin_remove_user_group(
    user_id: uuid.UUID,
    group_id: int,
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC12: Remove user from a specific group."""
    request_id = str(uuid.uuid4())
    result = await db.execute(
        text(
            "DELETE FROM user_group_memberships "
            "WHERE user_id = :user_id AND group_id = :group_id "
            "RETURNING user_id"
        ).bindparams(user_id=user_id, group_id=group_id)
    )
    if result.fetchone() is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "Membership not found"),
        )
    await db.commit()
    return JSONResponse(content={"user_id": str(user_id), "removed_group_id": group_id})


# ---------------------------------------------------------------------------
# S002/T001: POST /v1/admin/users/{id}/password-reset (Admin Force-Reset)
# Spec: docs/change-password/spec/change-password.spec.md#S002
# Rule: R003 — Depends(require_admin)
# Rule: R004 — /v1/ prefix
# Rule: R006 — audit log on admin reset
# Rule: S001 — parameterized SQL only
# Decision: D2 — generate=true → 200+{password}; explicit new_password → 204
# Decision: D3 — OIDC users → 400 ERR_PASSWORD_NOT_APPLICABLE
# Decision: Q3 — always set must_change_password = True
# ---------------------------------------------------------------------------

class PasswordResetRequest(BaseModel):
    generate: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


@router.post("/v1/admin/users/{user_id}/password-reset", dependencies=[Depends(require_admin)])
async def admin_password_reset(
    user_id: uuid.UUID,
    body: PasswordResetRequest,
    admin_user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Admin force-reset for a target user's password.

    generate=true → generates 16-char random password, returns 200 + {"password": "..."}
    new_password   → validates 8–128 chars, returns 204
    Always sets must_change_password = True on target user (Q3).
    OIDC users (no password_hash) → 400 ERR_PASSWORD_NOT_APPLICABLE (D3).
    Unknown user → 404 ERR_USER_NOT_FOUND.
    """
    request_id = str(uuid.uuid4())

    # Fetch target user
    row = (await db.execute(
        text("SELECT id, password_hash FROM users WHERE id = :user_id AND is_active = TRUE")
        .bindparams(user_id=user_id)
    )).fetchone()

    if row is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "ERR_USER_NOT_FOUND", "User not found"),
        )

    stored_hash: str | None = row[1]

    # D3: OIDC users have no password_hash — reset not applicable
    if stored_hash is None:
        return JSONResponse(
            status_code=400,
            content=_error(
                request_id,
                "ERR_PASSWORD_NOT_APPLICABLE",
                "Password reset is not available for SSO accounts",
            ),
        )

    if body.generate:
        # D2: generate random 16-char password, return plaintext to admin
        plaintext = generate_password(16)
        new_hash = _bcrypt_lib.hashpw(plaintext.encode(), _bcrypt_lib.gensalt(rounds=12)).decode()

        await db.execute(
            text(
                "UPDATE users SET password_hash = :hash, must_change_password = TRUE, "
                "token_version = token_version + 1 "
                "WHERE id = :user_id"
            ).bindparams(hash=new_hash, user_id=user_id)
        )
        await db.commit()

        # R006: audit log — admin reset action
        await db.execute(
            text(
                "INSERT INTO audit_logs (user_id, doc_id, query_hash, accessed_at) "
                "VALUES (:user_id, NULL, :query_hash, NOW())"
            ).bindparams(
                user_id=admin_user.user_id,
                query_hash=hashlib.sha256(
                    f"admin_password_reset:{user_id}".encode()
                ).hexdigest(),
            )
        )
        await db.commit()

        return JSONResponse(status_code=200, content={"password": plaintext})

    elif body.new_password is not None:
        # D2: explicit new password provided by admin
        new_hash = _bcrypt_lib.hashpw(
            body.new_password.encode(), _bcrypt_lib.gensalt(rounds=12)
        ).decode()

        await db.execute(
            text(
                "UPDATE users SET password_hash = :hash, must_change_password = TRUE, "
                "token_version = token_version + 1 "
                "WHERE id = :user_id"
            ).bindparams(hash=new_hash, user_id=user_id)
        )
        await db.commit()

        # R006: audit log — admin reset action
        await db.execute(
            text(
                "INSERT INTO audit_logs (user_id, doc_id, query_hash, accessed_at) "
                "VALUES (:user_id, NULL, :query_hash, NOW())"
            ).bindparams(
                user_id=admin_user.user_id,
                query_hash=hashlib.sha256(
                    f"admin_password_reset:{user_id}".encode()
                ).hexdigest(),
            )
        )
        await db.commit()

        return JSONResponse(status_code=204, content=None)

    else:
        return JSONResponse(
            status_code=422,
            content=_error(
                request_id,
                "INVALID_INPUT",
                "Provide either 'generate': true or 'new_password'",
            ),
        )


@router.get("/v1/metrics")
async def get_metrics(
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """D09: System metrics endpoint — admin only (R003). AC5: nested response shape."""
    # 1. Documents breakdown by status
    doc_rows = (await db.execute(text(
        "SELECT status, COUNT(*) AS cnt FROM documents GROUP BY status"
    ))).mappings().all()
    doc_counts: dict = {r["status"]: r["cnt"] for r in doc_rows}

    # 2. Users total + active
    user_row = (await db.execute(text(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS active "
        "FROM users"
    ))).mappings().one()

    # 3. Groups total
    group_total = (await db.execute(text("SELECT COUNT(*) FROM user_groups"))).scalar()

    # 4. 7-day daily query volume
    query_rows = (await db.execute(text(
        "SELECT DATE(accessed_at) AS day, COUNT(*) AS cnt "
        "FROM audit_logs "
        "WHERE accessed_at >= NOW() - INTERVAL '7 days' "
        "GROUP BY day ORDER BY day ASC"
    ))).mappings().all()

    return JSONResponse(content={
        "documents": {
            "total": sum(doc_counts.values()),
            "ready": doc_counts.get("ready", 0),
            "processing": doc_counts.get("processing", 0),
            "error": doc_counts.get("error", 0),
        },
        "users": {
            "total": user_row["total"],
            "active": user_row["active"] or 0,
        },
        "groups": {"total": group_total},
        "queries": {
            "last_7_days": [
                {"date": str(r["day"]), "count": r["cnt"]} for r in query_rows
            ]
        },
        "health": {"database": "ok", "api": "ok"},
    })
