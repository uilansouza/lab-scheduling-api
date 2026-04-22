from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.models.order import OrderStatus


class OrderItemResponse(BaseModel):
    exam_code: str
    exam_name: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderStatusHistoryResponse(BaseModel):
    status: OrderStatus
    changed_at: datetime
    changed_by: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    user_ref: str = Field(..., min_length=3, max_length=64, examples=["USR-0001"])
    org_ref: Optional[str] = Field(None, max_length=64, examples=["ORG-0001"])
    exam_codes: list[str] = Field(..., min_length=1, examples=[["EXM-0001", "EXM-0042"]])
    window_start: Optional[datetime] = Field(None, examples=["2025-02-01T08:00:00Z"])
    window_end: Optional[datetime] = Field(None, examples=["2025-02-01T18:00:00Z"])
    notes: Optional[str] = Field(None, max_length=512)

    @field_validator("exam_codes")
    @classmethod
    def exam_codes_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("exam_codes must contain at least one code")
        codes = [c.strip().upper() for c in v]
        if len(codes) != len(set(codes)):
            raise ValueError("exam_codes must not contain duplicates")
        return codes

    @field_validator("window_end")
    @classmethod
    def window_end_after_start(cls, v: datetime | None, info) -> datetime | None:
        start = info.data.get("window_start")
        if v and start and v <= start:
            raise ValueError("window_end must be after window_start")
        return v


class OrderResponse(BaseModel):
    id: str
    correlation_id: str
    user_ref: str
    org_ref: Optional[str]
    status: OrderStatus
    window_start: Optional[datetime]
    window_end: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []
    status_history: list[OrderStatusHistoryResponse] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class OrderStatusResponse(BaseModel):
    id: str
    correlation_id: str
    status: OrderStatus
    status_history: list[OrderStatusHistoryResponse]

    model_config = {"from_attributes": True}


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=256, examples=["Cancelamento solicitado pelo agente"])
