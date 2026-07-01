from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.core.rate_limit import rate_limit
from app.deps import get_current_user_id
from app.models.auth import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmBody,
    PasswordResetRequestBody,
    RefreshRequest,
    SignupRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", dependencies=[Depends(rate_limit("signup", 5, 3600))])
def signup(payload: SignupRequest) -> JSONResponse:
    data = auth_service.signup(payload)
    return JSONResponse(status_code=201, content=success(data, "Account created successfully"))


@router.post("/login", dependencies=[Depends(rate_limit("login", 10, 900))])
def login(payload: LoginRequest) -> JSONResponse:
    data = auth_service.login(payload.email, payload.password)
    return JSONResponse(status_code=200, content=success(data, "Logged in successfully"))


@router.post("/refresh")
def refresh(payload: RefreshRequest) -> JSONResponse:
    data = auth_service.refresh(payload.refresh_token)
    return JSONResponse(status_code=200, content=success(data, "Token refreshed"))


@router.post("/logout")
def logout(payload: LogoutRequest, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    auth_service.logout(payload.refresh_token, payload.all_devices, user_id)
    return JSONResponse(status_code=200, content=success({}, "Logged out"))


@router.post(
    "/password-reset/request",
    dependencies=[Depends(rate_limit("password-reset-request", 3, 3600))],
)
def password_reset_request(payload: PasswordResetRequestBody) -> JSONResponse:
    auth_service.request_password_reset(payload.email)
    return JSONResponse(
        status_code=200,
        content=success({}, "If an account exists for that email, a reset link has been sent"),
    )


@router.post("/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirmBody) -> JSONResponse:
    auth_service.confirm_password_reset(payload.token, payload.new_password)
    return JSONResponse(
        status_code=200, content=success({}, "Password has been reset. Please log in.")
    )
