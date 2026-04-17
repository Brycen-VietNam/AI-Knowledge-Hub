# Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
# Task: T005 — scaffold + require_admin + document endpoints (AC4, AC5, AC15)
# Task: T006 — group CRUD (AC6–AC9)
# Task: T007 — user endpoints (AC10–AC12, D10) + GET /v1/metrics (D09)
# Rule: R003 — all /v1/admin/* use require_admin (wraps verify_token); /v1/metrics same
# Rule: R004 — /v1/ prefix on all routes
# Rule: R006 — audit log on document delete (admin action)
# Rule: S001 — parameterized SQL only: text().bindparams(); no f-string user-value injection
# Rule: A005 — error shape: {"error": {"code", "message", "request_id"}}
# Rule: P004 — no N+1 queries (subquery/JOIN for user_count, group lists)
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser

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
) -> JSONResponse:
    """AC4: List ALL documents (no RBAC filter), paginated. Admin only."""
    request_id = str(uuid.uuid4())

    if limit > 100:
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", "limit must not exceed 100"),
        )

    # AC4: no RBAC WHERE clause — admin sees all documents regardless of user_group
    stmt = text(
        "SELECT d.id, d.title, d.lang, d.user_group_id, d.status, d.created_at, "
        "(SELECT COUNT(*) FROM embeddings e WHERE e.doc_id = d.id) AS chunk_count "
        "FROM documents d "
        "ORDER BY d.created_at DESC "
        "LIMIT :limit OFFSET :offset"
    ).bindparams(limit=limit, offset=offset)

    count_stmt = text("SELECT COUNT(*) FROM documents")

    rows = (await db.execute(stmt)).mappings().all()
    total = (await db.execute(count_stmt)).scalar()

    items = [
        {
            "id": str(r["id"]),
            "title": r["title"],
            "lang": r["lang"],
            "user_group_id": r["user_group_id"],
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


@router.get("/v1/admin/users")
async def admin_list_users(
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """AC10: List all users with group memberships. Single JOIN — no N+1 (P004)."""
    stmt = text(
        "SELECT u.id, u.sub, u.email, u.display_name, u.is_active, "
        "COALESCE(json_agg(json_build_object('id', ug.id, 'name', ug.name, 'is_admin', ug.is_admin)) "
        "FILTER (WHERE ug.id IS NOT NULL), '[]') AS groups "
        "FROM users u "
        "LEFT JOIN user_group_memberships ugm ON ugm.user_id = u.id "
        "LEFT JOIN user_groups ug ON ug.id = ugm.group_id "
        "GROUP BY u.id, u.sub, u.email, u.display_name, u.is_active "
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


@router.get("/v1/metrics")
async def get_metrics(
    user: Annotated[AuthenticatedUser, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """D09: System metrics endpoint — admin only (R003)."""
    doc_count = (await db.execute(text("SELECT COUNT(*) FROM documents"))).scalar()
    active_users = (await db.execute(
        text("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
    )).scalar()
    query_count = (await db.execute(
        text("SELECT COUNT(*) FROM audit_logs WHERE timestamp >= NOW() - INTERVAL '24 hours'")
    )).scalar()

    return JSONResponse(content={
        "document_count": doc_count,
        "query_count_24h": query_count,
        "active_users_count": active_users,
        "health": "ok",
    })
