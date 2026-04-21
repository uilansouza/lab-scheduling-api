from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.exam import ExamListResponse, ExamResponse
from app.services.exam_service import list_exams, get_exam_by_code
from app.core.config import settings

router = APIRouter(prefix="/exams", tags=["Catalog"])


@router.get("", response_model=ExamListResponse, summary="List exam catalog")
def get_exams(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    code: str | None = Query(None, description="Filter by exact exam code"),
    search: str | None = Query(None, description="Search term in name or description"),
    active_only: bool = Query(True, description="Return only active exams"),
    db: Session = Depends(get_db),
):
    """Public endpoint. Lists all exams with pagination and optional filters."""
    return list_exams(db, page=page, page_size=page_size, code=code, search=search, active_only=active_only)


@router.get("/{code}", response_model=ExamResponse, summary="Get exam by code")
def get_exam(code: str, db: Session = Depends(get_db)):
    """Public endpoint. Returns a single exam by its code."""
    exam = get_exam_by_code(db, code)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Exam '{code}' not found"},
        )
    return exam
