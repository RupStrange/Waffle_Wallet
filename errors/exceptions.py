class AppException(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "An unexpected error occurred", details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"


class BadRequestError(AppException):
    status_code = 400
    code = "bad_request"


class UnauthorizedError(AppException):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppException):
    status_code = 403
    code = "forbidden"


class ConflictError(AppException):
    status_code = 409
    code = "conflict"
