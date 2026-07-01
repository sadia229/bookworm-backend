from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.envelope import paginated, success
from app.deps import get_current_user_id
from app.models.progress import GroupBy, LogProgressRequest
from app.services import progress_service

router = APIRouter(tags=["Reading Progress"])


@router.post("/books/{book_id}/progress")
def log_progress(
    book_id: str, payload: LogProgressRequest, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    data = progress_service.log_progress(user_id, book_id, payload)
    return JSONResponse(status_code=201, content=success(data, "Progress logged"))


@router.get("/books/{book_id}/progress")
def book_progress_history(
    book_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    items, total = progress_service.book_progress_history(user_id, book_id, page, size)
    return JSONResponse(
        status_code=200,
        content=success(paginated(items, page, size, total), "Progress history retrieved"),
    )


@router.get("/progress")
def activity_window(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = None,
    group_by: GroupBy = GroupBy.day,
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    data = progress_service.activity_window(user_id, from_, to, group_by.value)
    return JSONResponse(status_code=200, content=success(data, "Reading activity retrieved"))
