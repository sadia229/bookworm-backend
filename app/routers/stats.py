from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.deps import get_current_user_id, get_timezone
from app.services import stats_service

router = APIRouter(tags=["Stats / Dashboard"])


@router.get("/stats/dashboard")
def get_dashboard(
    user_id: str = Depends(get_current_user_id), tz: str = Depends(get_timezone)
) -> JSONResponse:
    data = stats_service.get_dashboard(user_id, tz)
    return JSONResponse(status_code=200, content=success(data, "Dashboard retrieved"))


@router.get("/stats/wrapped")
def get_wrapped(
    month: str | None = None,
    user_id: str = Depends(get_current_user_id),
    tz: str = Depends(get_timezone),
) -> JSONResponse:
    data = stats_service.get_wrapped(user_id, month, tz)
    return JSONResponse(status_code=200, content=success(data, "Wrapped stats retrieved"))
