from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.envelope import success
from app.deps import get_current_user_id
from app.models.reviews import UpdateReviewRequest
from app.services import review_service

router = APIRouter(tags=["Reviews & Ratings"])


@router.put("/books/{book_id}/review")
def update_review(
    book_id: str, payload: UpdateReviewRequest, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    data = review_service.update_review(user_id, book_id, payload)
    return JSONResponse(status_code=200, content=success(data, "Review updated"))


@router.delete("/books/{book_id}/review")
def delete_review(book_id: str, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    review_service.delete_review(user_id, book_id)
    return JSONResponse(status_code=200, content=success({}, "Review removed"))
