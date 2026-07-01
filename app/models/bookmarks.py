from pydantic import BaseModel


class CreateBookmarkRequest(BaseModel):
    book_id: str
