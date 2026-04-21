from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_agent, Role
from app.core.config import settings
from app.models.order import OrderStatus
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderListResponse,
    OrderStatusResponse, OrderCancelRequest
)
from app.services.order_service import (
    create_order, list_orders, get_order,
    get_order_status, cancel_order
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    summary="Create a new exam order",
)
def post_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    role: Role = Depends(require_agent),
):
    """
    Creates a new exam order.

    - Validates all exam codes against the active catalog.
    - Persists order, line items, initial status history and audit log.
    - Returns the full order detail.

    **Auth:** requires `agent` or `admin` API key.
    """
    return create_order(db, payload, actor=role.value)


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List orders",
)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    status: OrderStatus | None = Query(None, description="Filter by order status"),
    user_ref: str | None = Query(None, description="Filter by user reference"),
    db: Session = Depends(get_db),
    role: Role = Depends(require_agent),
):
    """
    Returns a paginated list of orders with optional filters.

    **Auth:** requires `agent` or `admin` API key.
    """
    return list_orders(db, page=page, page_size=page_size, status_filter=status, user_ref=user_ref)


@router.get(
    "/statuses",
    response_model=list[str],
    summary="List all possible order statuses",
)
def get_order_statuses(role: Role = Depends(require_agent)):
    """
    Returns all valid order status values and their semantics.

    | Status      | Meaning                                          |
    |-------------|--------------------------------------------------|
    | PENDING     | Order received, awaiting confirmation            |
    | CONFIRMED   | Order confirmed by the lab                       |
    | COLLECTED   | Sample collected — terminal state                |
    | CANCELLED   | Order cancelled — terminal state                 |

    **Auth:** requires `agent` or `admin` API key.
    """
    return [s.value for s in OrderStatus]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order detail",
)
def get_order_detail(
    order_id: str = Path(..., description="Order UUID"),
    db: Session = Depends(get_db),
    role: Role = Depends(require_agent),
):
    """
    Returns full detail of a single order including items and status history.

    **Auth:** requires `agent` or `admin` API key.
    """
    return get_order(db, order_id)


@router.get(
    "/{order_id}/status",
    response_model=OrderStatusResponse,
    summary="Get order status and history",
)
def get_order_status_route(
    order_id: str = Path(..., description="Order UUID"),
    db: Session = Depends(get_db),
    role: Role = Depends(require_agent),
):
    """
    Returns the current status and full status history of an order.

    **Auth:** requires `agent` or `admin` API key.
    """
    return get_order_status(db, order_id)


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel an order",
)
def patch_cancel_order(
    order_id: str = Path(..., description="Order UUID"),
    body: OrderCancelRequest = OrderCancelRequest(),
    db: Session = Depends(get_db),
    role: Role = Depends(require_agent),
):
    """
    Cancels an order. Terminal states (`COLLECTED`, `CANCELLED`) cannot be cancelled again.

    **Auth:** requires `agent` or `admin` API key.
    """
    return cancel_order(db, order_id, reason=body.reason, actor=role.value)
