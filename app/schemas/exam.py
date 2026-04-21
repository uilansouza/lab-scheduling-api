from pydantic import BaseModel, Field
from typing import Optional


class ExamBase(BaseModel):
    code: str = Field(..., examples=["EXM-0001"])
    name: str = Field(..., examples=["Hemograma Completo Sintético"])
    description: Optional[str] = None
    category: Optional[str] = None
    active: bool = True


class ExamResponse(ExamBase):
    model_config = {"from_attributes": True}


class ExamListResponse(BaseModel):
    items: list[ExamResponse]
    total: int
    page: int
    page_size: int
    pages: int
