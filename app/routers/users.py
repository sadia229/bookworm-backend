from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.deps import get_current_user_id
from app.models.users import UpdateProfileRequest
from app.services import user_service

router = APIRouter(tags=["User Profile"])


@router.get("/users/me")
def get_me(user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    data = user_service.get_me(user_id)
    return JSONResponse(status_code=200, content=success(data, "Profile retrieved"))


@router.patch("/users/me")
def update_me(
    payload: UpdateProfileRequest, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    data = user_service.update_me(user_id, payload)
    return JSONResponse(status_code=200, content=success(data, "Profile updated"))


@router.post("/users/me/avatar")
async def upload_avatar(
    file: UploadFile, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    content = await file.read()
    data = user_service.upload_avatar(user_id, content, file.content_type or "")
    return JSONResponse(status_code=201, content=success(data, "Avatar uploaded"))


@router.get("/users/{user_id}")
def get_user(user_id: str, _: str = Depends(get_current_user_id)) -> JSONResponse:
    data = user_service.get_public_profile(user_id)
    return JSONResponse(status_code=200, content=success(data, "Profile retrieved"))
