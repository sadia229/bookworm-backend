from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.envelope import paginated, success
from app.deps import get_current_user_id
from app.models.bookmarks import CreateBookmarkRequest
from app.services import bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


@router.post("")
def create_bookmark(
    payload: CreateBookmarkRequest, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    data = bookmark_service.create_bookmark(user_id, payload.book_id)
    return JSONResponse(status_code=201, content=success(data, "Bookmarked"))


@router.get("")
def list_bookmarks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    items, total = bookmark_service.list_bookmarks(user_id, page, size)
    return JSONResponse(
        status_code=200,
        content=success(paginated(items, page, size, total), "Bookmarks retrieved"),
    )


@router.delete("")
def delete_bookmark_by_book(
    book_id: str, user_id: str = Depends(get_current_user_id)
) -> JSONResponse:
    bookmark_service.delete_bookmark_by_book(user_id, book_id)
    return JSONResponse(status_code=200, content=success({}, "Bookmark removed"))


@router.delete("/{bookmark_id}")
def delete_bookmark(bookmark_id: str, user_id: str = Depends(get_current_user_id)) -> JSONResponse:
    bookmark_service.delete_bookmark(user_id, bookmark_id)
    return JSONResponse(status_code=200, content=success({}, "Bookmark removed"))
