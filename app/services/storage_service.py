import uuid

from app.core.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError
from app.db.supabase_client import AVATAR_BUCKET, COVER_BUCKET, get_supabase

_ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_MAX_BYTES = 5 * 1024 * 1024


def _validate(content_type: str, size: int, too_large_message: str) -> str:
    if content_type not in _ALLOWED_TYPES:
        raise UnsupportedMediaTypeError("Only JPEG, PNG, or WebP images are allowed")
    if size > _MAX_BYTES:
        raise PayloadTooLargeError(too_large_message)
    return _ALLOWED_TYPES[content_type]


def upload_avatar(user_id: str, content: bytes, content_type: str) -> tuple[str, str]:
    ext = _validate(content_type, len(content), "Avatar must be 5 MB or smaller")
    path = f"{user_id}/{uuid.uuid4()}.{ext}"
    client = get_supabase()
    client.storage.from_(AVATAR_BUCKET).upload(
        path, content, {"content-type": content_type, "upsert": "true"}
    )
    url = client.storage.from_(AVATAR_BUCKET).get_public_url(path)
    return path, url


def delete_avatar(path: str) -> None:
    if not path:
        return
    try:
        get_supabase().storage.from_(AVATAR_BUCKET).remove([path])
    except Exception:
        pass


def upload_cover(book_id: str, content: bytes, content_type: str) -> str:
    ext = _validate(content_type, len(content), "Cover must be 5 MB or smaller")
    path = f"{book_id}/{uuid.uuid4()}.{ext}"
    client = get_supabase()
    client.storage.from_(COVER_BUCKET).upload(
        path, content, {"content-type": content_type, "upsert": "true"}
    )
    return client.storage.from_(COVER_BUCKET).get_public_url(path)
