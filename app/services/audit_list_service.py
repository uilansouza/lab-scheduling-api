import math
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.audit import AuditLog
from app.schemas.audit import AuditLogListResponse, AuditLogResponse


def list_audit_logs(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    resource: str | None = None,
    resource_id: str | None = None,
    correlation_id: str | None = None,
    actor: str | None = None,
) -> AuditLogListResponse:
    query = select(AuditLog)
    if resource:
        query = query.where(AuditLog.resource == resource)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if correlation_id:
        query = query.where(AuditLog.correlation_id == correlation_id)
    if actor:
        query = query.where(AuditLog.actor == actor)

    total: int = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    offset = (page - 1) * page_size
    rows = db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
