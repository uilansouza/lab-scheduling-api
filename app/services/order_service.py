import math
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.order import Order, OrderItem, OrderStatusHistory, OrderStatus
from app.models.exam import Exam
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderListResponse,
    OrderStatusResponse, OrderItemResponse, OrderStatusHistoryResponse
)
from app.services.audit_service import log_action


def _load_order(db: Session, order_id: str) -> Order:
    row = db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.exam),
            selectinload(Order.status_history),
        )
        .where(Order.id == order_id)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Order {order_id} not found"},
        )
    return row


def _to_response(order: Order) -> OrderResponse:
    items = [
        OrderItemResponse(
            exam_code=i.exam_code,
            exam_name=i.exam.name if i.exam else None,
        )
        for i in order.items
    ]
    history = [
        OrderStatusHistoryResponse(
            status=h.status,
            changed_at=h.changed_at,
            changed_by=h.changed_by,
        )
        for h in sorted(order.status_history, key=lambda h: h.changed_at)
    ]
    return OrderResponse(
        id=order.id,
        correlation_id=order.correlation_id,
        user_ref=order.user_ref,
        org_ref=order.org_ref,
        status=order.status,
        window_start=order.window_start,
        window_end=order.window_end,
        notes=order.notes,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items,
        status_history=history,
    )


def create_order(db: Session, payload: OrderCreate, actor: str) -> OrderResponse:
    # Validate exam codes
    codes = [c.upper() for c in payload.exam_codes]
    found = db.execute(select(Exam.code).where(Exam.code.in_(codes), Exam.active.is_(True))).scalars().all()
    missing = set(codes) - set(found)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INVALID_EXAM_CODES",
                "message": "One or more exam codes are invalid or inactive",
                "details": {"invalid_codes": sorted(missing)},
            },
        )

    order = Order(
        user_ref=payload.user_ref,
        org_ref=payload.org_ref,
        window_start=payload.window_start,
        window_end=payload.window_end,
        notes=payload.notes,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.flush()  # get order.id

    for code in codes:
        db.add(OrderItem(order_id=order.id, exam_code=code))

    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PENDING, changed_by=actor))

    log_action(
        db,
        action="ORDER_CREATED",
        resource="orders",
        resource_id=order.id,
        correlation_id=order.correlation_id,
        actor=actor,
        detail=f"exam_codes={','.join(codes)}",
    )
    db.commit()
    return _to_response(_load_order(db, order.id))


def list_orders(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: OrderStatus | None = None,
    user_ref: str | None = None,
) -> OrderListResponse:
    query = select(Order)
    if status_filter:
        query = query.where(Order.status == status_filter)
    if user_ref:
        query = query.where(Order.user_ref == user_ref)

    total: int = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    offset = (page - 1) * page_size
    rows = db.execute(
        query.options(
            selectinload(Order.items).selectinload(OrderItem.exam),
            selectinload(Order.status_history),
        )
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    ).scalars().all()

    return OrderListResponse(
        items=[_to_response(o) for o in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


def get_order(db: Session, order_id: str) -> OrderResponse:
    return _to_response(_load_order(db, order_id))


def get_order_status(db: Session, order_id: str) -> OrderStatusResponse:
    order = _load_order(db, order_id)
    history = [
        OrderStatusHistoryResponse(
            status=h.status,
            changed_at=h.changed_at,
            changed_by=h.changed_by,
        )
        for h in sorted(order.status_history, key=lambda h: h.changed_at)
    ]
    return OrderStatusResponse(
        id=order.id,
        correlation_id=order.correlation_id,
        status=order.status,
        status_history=history,
    )


def cancel_order(db: Session, order_id: str, reason: str | None, actor: str) -> OrderResponse:
    order = _load_order(db, order_id)

    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "ALREADY_CANCELLED", "message": "Order is already cancelled"},
        )
    if order.status == OrderStatus.COLLECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "CANNOT_CANCEL", "message": "Cannot cancel an order that has already been collected"},
        )

    order.status = OrderStatus.CANCELLED
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.CANCELLED, changed_by=actor))
    log_action(
        db,
        action="ORDER_CANCELLED",
        resource="orders",
        resource_id=order.id,
        correlation_id=order.correlation_id,
        actor=actor,
        detail=reason,
    )
    db.commit()
    return _to_response(_load_order(db, order_id))
