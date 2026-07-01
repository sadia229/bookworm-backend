from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.deps import get_current_user_id
from app.services import world_service

router = APIRouter(tags=["World Comes to Life"])


@router.get("/world")
def get_world(user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    data = world_service.get_world(user_id)
    return JSONResponse(status_code=200, content=success(data, "World state retrieved"))
