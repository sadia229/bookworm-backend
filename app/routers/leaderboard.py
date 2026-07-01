from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.deps import get_current_user_id
from app.models.common import LeaderboardPeriod
from app.services import leaderboard_service

router = APIRouter(tags=["Leaderboard"])


@router.get("/leaderboard")
def get_leaderboard(
    period: LeaderboardPeriod = LeaderboardPeriod.all_time,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    me, items, total = leaderboard_service.get_leaderboard(user_id, period.value, page, size)
    total_pages = (total + size - 1) // size if size else 0
    data = {
        "period": period.value,
        "me": me,
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }
    return JSONResponse(status_code=200, content=success(data, "Leaderboard retrieved"))
