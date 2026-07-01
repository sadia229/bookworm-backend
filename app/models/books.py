from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.common import BookStatus, Genre, validate_not_future


class CreateBookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=120)
    genre: Genre | None = None
    total_pages: int | None = Field(default=None, ge=1, le=20000)
    status: BookStatus = BookStatus.currently_reading
    current_page: int = Field(default=0, ge=0)
    started_at: datetime | None = None

    @field_validator("title", "author")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()

    @field_validator("started_at")
    @classmethod
    def _not_future(cls, v: datetime | None) -> datetime | None:
        return validate_not_future(v) if v else v

    @field_validator("current_page")
    @classmethod
    def _within_total(cls, v: int, info) -> int:
        total = info.data.get("total_pages")
        if total is not None and v > total:
            raise ValueError("current_page cannot exceed total_pages")
        return v


class UpdateBookRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=120)
    genre: Genre | None = None
    total_pages: int | None = Field(default=None, ge=1, le=20000)
    current_page: int | None = Field(default=None, ge=0)
    status: BookStatus | None = None

    @field_validator("title", "author")
    @classmethod
    def _trim(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class FinishBookRequest(BaseModel):
    summary: str = Field(..., min_length=1, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)
    finished_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()

    @field_validator("finished_at")
    @classmethod
    def _not_future(cls, v: datetime | None) -> datetime | None:
        return validate_not_future(v) if v else v


class BookListQuery(BaseModel):
    status: BookStatus | None = None
    q: str | None = None
    genre: Genre | None = None
    sort: str = "-updated_at"
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
