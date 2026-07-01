from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.timeutils import iso
from app.db.container import get_repositories
from app.models.reviews import UpdateReviewRequest


def _get_finished_owned_book(repos, user_id: str, book_id: str) -> dict:
    book = repos.books.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book not found")
    if book["user_id"] != user_id:
        raise ForbiddenError("You can only edit your own reviews")
    return book


def update_review(user_id: str, book_id: str, payload: UpdateReviewRequest) -> dict:
    repos = get_repositories()
    book = _get_finished_owned_book(repos, user_id, book_id)
    if book["status"] != "already_read":
        raise ConflictError("Only finished books can have a review")

    fields = payload.model_dump(mode="json")
    updated = repos.books.update(
        book_id, {"summary": fields["summary"], "rating": fields.get("rating")}
    )
    return {
        "book_id": updated["id"],
        "rating": updated.get("rating"),
        "summary": updated.get("summary"),
        "updated_at": iso(updated["updated_at"]),
    }


def delete_review(user_id: str, book_id: str) -> None:
    repos = get_repositories()
    _get_finished_owned_book(repos, user_id, book_id)
    repos.books.update(book_id, {"summary": None, "rating": None})
