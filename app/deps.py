from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.container import get_repositories

_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None:
        raise UnauthorizedError()
    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:
        raise UnauthorizedError() from exc
    if payload.get("type") != "access":
        raise UnauthorizedError()
    return payload["sub"]


def get_current_user(user_id: str = Depends(get_current_user_id)) -> dict:
    repos = get_repositories()
    user = repos.users.get_by_id(user_id)
    if not user:
        raise UnauthorizedError()
    return user


def get_timezone(x_timezone: str | None = Header(default=None, alias="X-Timezone")) -> str:
    return x_timezone or "UTC"
