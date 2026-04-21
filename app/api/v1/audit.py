from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin, Role
from app.core.config import settings
from app.schemas.audit import AuditLogListResponse
from app.services.audit_list_service import list_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List audit logs",
)
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    resource: str | None = Query(None, description="Filter by resource type (e.g. 'orders')"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    correlation_id: str | None = Query(None, description="Filter by correlation ID"),
    actor: str | None = Query(None, description="Filter by actor"),
    db: Session = Depends(get_db),
    _role: Role = Depends(require_admin),
):
    """
    Returns a paginated list of audit log entries.

    Audit logs are immutable records of every state-changing action
    performed on the API (order creation, cancellation, etc.).

    **Auth:** requires `admin` API key only.
    """
    return list_audit_logs(
        db,
        page=page,
        page_size=page_size,
        resource=resource,
        resource_id=resource_id,
        correlation_id=correlation_id,
        actor=actor,
    )
