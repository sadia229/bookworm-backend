from typing import Any


def success(data: Any = None, message: str = "success") -> dict:
    return {"success": True, "message": message, "data": data if data is not None else {}}


def failure(message: str = "fail", data: Any = None) -> dict:
    return {"success": False, "message": message, "data": data if data is not None else {}}


def paginated(items: list, page: int, size: int, total: int) -> dict:
    total_pages = (total + size - 1) // size if size else 0
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }
