from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.common import Gender, Genre, validate_dob, validate_reminder_time

_PHONE_RE = __import__("re").compile(r"^\+?[0-9]{1,20}$")


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=50)
    name_hidden: bool | None = None
    phone: str | None = Field(default=None, max_length=20)
    avatar_id: str | None = None
    gender: Gender | None = None
    dob: date | None = None
    reading_preferences: list[Genre] | None = Field(default=None, max_length=10)
    daily_goal_pages: int | None = Field(default=None, ge=1, le=500)
    yearly_goal_books: int | None = Field(default=None, ge=1, le=365)
    reminder_time: str | None = None

    @field_validator("display_name")
    @classmethod
    def _trim(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("phone")
    @classmethod
    def _phone_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not _PHONE_RE.match(v):
            raise ValueError("phone must be E.164 format")
        return v

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

    @field_validator("reminder_time")
    @classmethod
    def _reminder_time_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_reminder_time(v)
