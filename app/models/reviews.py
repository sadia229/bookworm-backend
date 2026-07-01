from pydantic import BaseModel, Field, field_validator


class UpdateReviewRequest(BaseModel):
    summary: str = Field(..., min_length=1, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)

    @field_validator("summary")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()
