from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.core.rate_limit import rate_limit
from app.deps import get_current_user_id
from app.models.premium import RevenueCatWebhook
from app.services import premium_service

router = APIRouter(tags=["Premium"])


@router.post("/webhooks/revenuecat")
def revenuecat_webhook(
    payload: RevenueCatWebhook,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    data = premium_service.process_webhook(authorization, payload)
    return JSONResponse(status_code=200, content=success(data, "Webhook processed"))


@router.post(
    "/users/me/premium/sync",
    dependencies=[Depends(rate_limit("premium-sync", 5, 60))],
)
def sync_premium(user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    data = premium_service.sync_premium(user_id)
    return JSONResponse(status_code=200, content=success(data, "Premium status synced"))
