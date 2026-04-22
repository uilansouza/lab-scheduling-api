from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_action(
    db: Session,
    *,
    action: str,
    resource: str,
    resource_id: str | None = None,
    correlation_id: str | None = None,
    actor: str,
    detail: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        resource=resource,
        resource_id=resource_id,
        correlation_id=correlation_id,
        actor=actor,
        detail=detail,
    )
    db.add(entry)
    db.flush()
    return entry
