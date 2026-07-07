from pydantic import BaseModel, ConfigDict


class RevenueCatEvent(BaseModel):
    # RevenueCat sends many more fields; only the ones below are used and the
    # rest are ignored so schema changes on their side never 422 the webhook.
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    type: str | None = None
    app_user_id: str | None = None
    entitlement_ids: list[str] | None = None
    expiration_at_ms: int | None = None
    environment: str | None = None


class RevenueCatWebhook(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event: RevenueCatEvent
