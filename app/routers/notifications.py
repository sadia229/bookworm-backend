from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.deps import get_current_user_id
from app.models.notifications import RegisterDeviceTokenRequest
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/token")
def register_token(
    payload: RegisterDeviceTokenRequest, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    data = notification_service.register_device_token(
        user_id, payload.token, payload.platform.value if payload.platform else None
    )
    return JSONResponse(status_code=200, content=success(data, "Device token registered"))


@router.delete("/token")
def remove_token(token: str, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    notification_service.remove_device_token(user_id, token)
    return JSONResponse(status_code=200, content=success({}, "Device token removed"))


@router.get("")
def list_notifications(
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    items, total, unread_count = notification_service.list_notifications(
        user_id, unread_only, page, size
    )
    total_pages = (total + size - 1) // size if size else 0
    data = {
        "unread_count": unread_count,
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }
    return JSONResponse(status_code=200, content=success(data, "Notifications retrieved"))


@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    data = notification_service.mark_read(user_id, notification_id)
    return JSONResponse(status_code=200, content=success(data, "Notification marked as read"))


@router.post("/read-all")
def mark_all_read(user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    data = notification_service.mark_all_read(user_id)
    return JSONResponse(
        status_code=200, content=success(data, "All notifications marked as read")
    )


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    notification_service.delete_notification(user_id, notification_id)
    return JSONResponse(status_code=200, content=success({}, "Notification dismissed"))
