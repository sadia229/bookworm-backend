from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.common import Gender, Genre, validate_dob, validate_password_strength


class SignupRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=50)
    dob: date | None = None
    gender: Gender | None = None
    reading_preferences: list[Genre] | None = Field(default=None, max_length=10)
    yearly_goal_books: int | None = Field(default=None, ge=1, le=365)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("display_name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("dob")
    @classmethod
    def _dob_valid(cls, v: date | None) -> date | None:
        if v is None:
            return v
        return validate_dob(v)

    @field_validator("reading_preferences")
    @classmethod
    def _unique_prefs(cls, v: list[Genre] | None) -> list[Genre] | None:
        if v is None:
            return v
        if len(set(v)) != len(v):
            raise ValueError("reading_preferences must be unique")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    all_devices: bool = False


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetConfirmBody(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return validate_password_strength(v)
