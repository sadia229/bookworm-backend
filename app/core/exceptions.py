class AppError(Exception):
    """Base class for domain errors mapped to the API's failure envelope.

    `data` becomes the envelope's `data` field verbatim -- callers pass
    whatever shape api-doc.md documents for that error (e.g. `{"errors": {...}}`
    for validation failures, `{"is_premium": False}` for the premium gate).
    """

    status_code: int = 400

    def __init__(self, message: str, data: dict | None = None) -> None:
        self.message = message
        self.data = data or {}
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401

    def __init__(self, message: str = "Not authenticated", errors: dict | None = None) -> None:
        super().__init__(message, errors)


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ValidationAppError(AppError):
    status_code = 422


class TooManyRequestsError(AppError):
    status_code = 429


class PayloadTooLargeError(AppError):
    status_code = 413


class UnsupportedMediaTypeError(AppError):
    status_code = 415


class BadGatewayError(AppError):
    status_code = 502
