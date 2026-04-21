import math
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.exam import Exam
from app.schemas.exam import ExamListResponse, ExamResponse


def list_exams(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    code: str | None = None,
    search: str | None = None,
    active_only: bool = True,
) -> ExamListResponse:
    query = select(Exam)

    if active_only:
        query = query.where(Exam.active.is_(True))
    if code:
        query = query.where(Exam.code == code.upper())
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(Exam.name.ilike(term), Exam.description.ilike(term))
        )

    total_query = select(func.count()).select_from(query.subquery())
    total: int = db.execute(total_query).scalar_one()

    offset = (page - 1) * page_size
    rows = db.execute(query.order_by(Exam.code).offset(offset).limit(page_size)).scalars().all()

    return ExamListResponse(
        items=[ExamResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


def get_exam_by_code(db: Session, code: str) -> Exam | None:
    return db.execute(select(Exam).where(Exam.code == code.upper())).scalar_one_or_none()
