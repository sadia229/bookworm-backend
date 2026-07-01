from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from app.core.timeutils import iso
from app.db.container import get_repositories
from app.models.books import BookListQuery, CreateBookRequest, FinishBookRequest, UpdateBookRequest
from app.services import notification_service, storage_service
from app.services.world_service import STAGES

_WORLD_THRESHOLDS = [0, 5, 15, 30, 50, 100]


def _progress(book: dict) -> float:
    total = book.get("total_pages")
    if not total:
        return 0.0
    return max(0.0, min(1.0, book["current_page"] / total))


def _serialize_list_item(book: dict) -> dict:
    return {
        "id": book["id"],
        "title": book["title"],
        "author": book["author"],
        "genre": book.get("genre"),
        "cover_url": book.get("cover_url"),
        "total_pages": book.get("total_pages"),
        "current_page": book["current_page"],
        "status": book["status"],
        "progress": round(_progress(book), 4),
        "rating": book.get("rating"),
        "finished_at": iso(book.get("finished_at")),
    }


def _serialize_full(book: dict) -> dict:
    return {
        "id": book["id"],
        "user_id": book["user_id"],
        "title": book["title"],
        "author": book["author"],
        "genre": book.get("genre"),
        "cover_url": book.get("cover_url"),
        "total_pages": book.get("total_pages"),
        "current_page": book["current_page"],
        "status": book["status"],
        "progress": round(_progress(book), 4),
        "started_at": iso(book.get("started_at")),
        "finished_at": iso(book.get("finished_at")),
        "rating": book.get("rating"),
        "summary": book.get("summary"),
        "created_at": iso(book["created_at"]),
        "updated_at": iso(book["updated_at"]),
    }


def _next_threshold_info(books_completed: int) -> tuple[int | None, int | None]:
    for threshold in _WORLD_THRESHOLDS:
        if books_completed < threshold:
            return threshold, threshold - books_completed
    return None, None


def get_owned_book(repos, user_id: str, book_id: str) -> dict:
    book = repos.books.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book not found")
    if book["user_id"] != user_id:
        raise ForbiddenError("You do not have access to this book")
    return book


def create_book(user_id: str, payload: CreateBookRequest) -> dict:
    repos = get_repositories()
    fields = payload.model_dump(mode="json")
    fields["user_id"] = user_id
    book = repos.books.create(fields)
    return _serialize_full(book)


def list_books(user_id: str, query: BookListQuery) -> tuple[list[dict], int]:
    repos = get_repositories()
    items, total = repos.books.list_by_user(
        user_id,
        query.status.value if query.status else None,
        query.q,
        query.genre.value if query.genre else None,
        query.sort,
        query.page,
        query.size,
    )
    return [_serialize_list_item(b) for b in items], total


def get_book(user_id: str, book_id: str) -> dict:
    repos = get_repositories()
    return _serialize_full(get_owned_book(repos, user_id, book_id))


def update_book(user_id: str, book_id: str, payload: UpdateBookRequest) -> dict:
    repos = get_repositories()
    book = get_owned_book(repos, user_id, book_id)

    fields = payload.model_dump(exclude_unset=True, mode="json")
    if not fields:
        raise BadRequestError("No fields provided to update")

    if fields.get("status") == "already_read":
        raise ConflictError("Use the finish endpoint to mark a book as read")

    total_pages = fields.get("total_pages", book.get("total_pages"))
    current_page = fields.get("current_page", book["current_page"])
    if total_pages is not None and current_page > total_pages:
        raise ValidationAppError(
            "current_page cannot exceed total_pages",
            {"errors": {"current_page": "out_of_range"}},
        )

    updated = repos.books.update(book_id, fields)
    return {
        "id": updated["id"],
        "title": updated["title"],
        "author": updated["author"],
        "genre": updated.get("genre"),
        "total_pages": updated.get("total_pages"),
        "current_page": updated["current_page"],
        "status": updated["status"],
        "progress": round(_progress(updated), 4),
        "updated_at": iso(updated["updated_at"]),
    }


def delete_book(user_id: str, book_id: str) -> None:
    repos = get_repositories()
    get_owned_book(repos, user_id, book_id)
    repos.books.delete(book_id)


def upload_cover(user_id: str, book_id: str, content: bytes, content_type: str) -> dict:
    repos = get_repositories()
    get_owned_book(repos, user_id, book_id)
    if not content:
        raise BadRequestError("No file provided")
    url = storage_service.upload_cover(book_id, content, content_type)
    repos.books.update(book_id, {"cover_url": url})
    return {"book_id": book_id, "cover_url": url}


def finish_book(user_id: str, book_id: str, payload: FinishBookRequest) -> dict:
    repos = get_repositories()
    fields = payload.model_dump(mode="json")
    result = repos.books.finish(
        book_id, user_id, fields["summary"], fields.get("rating"), fields.get("finished_at")
    )
    book = result["book"]
    progression = result["progression"]
    total = book.get("total_pages")
    progress = round(book["current_page"] / total, 4) if total else 1.0
    next_threshold, books_to_next = _next_threshold_info(progression["books_completed"])

    if progression["stage_changed"]:
        stage_label = STAGES[progression["world_stage"]]["label"]
        notification_service.notify_and_push(
            user_id,
            title="Your forest grew!",
            body=f"{stage_label} — {progression['books_completed']} books finished.",
            data={"type": "world_stage", "stage": str(progression["world_stage"])},
        )

    return {
        "book": {
            "id": book["id"],
            "title": book["title"],
            "status": book["status"],
            "finished_at": iso(book["finished_at"]),
            "rating": book.get("rating"),
            "summary": book.get("summary"),
            "current_page": book["current_page"],
            "progress": progress,
        },
        "progression": {
            "books_completed": progression["books_completed"],
            "points_awarded": progression["points_awarded"],
            "points_total": progression["points_total"],
            "previous_world_stage": progression["previous_world_stage"],
            "world_stage": progression["world_stage"],
            "stage_changed": progression["stage_changed"],
            "next_threshold": next_threshold,
            "books_to_next_stage": books_to_next,
        },
    }


def list_public_finished(
    viewer_id: str, target_user_id: str, sort: str, page: int, size: int
) -> tuple[list[dict], int]:
    repos = get_repositories()
    target = repos.users.get_by_id(target_user_id)
    if not target:
        raise NotFoundError("User not found")

    items, total = repos.books.list_public_finished(target_user_id, sort, page, size)
    book_ids = [b["id"] for b in items]
    bookmarked = repos.bookmarks.bookmarked_book_ids(viewer_id, book_ids)

    serialized = [
        {
            "id": b["id"],
            "title": b["title"],
            "author": b["author"],
            "genre": b.get("genre"),
            "cover_url": b.get("cover_url"),
            "rating": b.get("rating"),
            "summary": b.get("summary"),
            "finished_at": iso(b.get("finished_at")),
            "bookmarked_by_me": b["id"] in bookmarked,
        }
        for b in items
    ]
    return serialized, total
