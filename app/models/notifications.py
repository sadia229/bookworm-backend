from pydantic import BaseModel, Field

from app.models.common import NotificationPlatform


class RegisterDeviceTokenRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=4096)
    platform: NotificationPlatform | None = None
