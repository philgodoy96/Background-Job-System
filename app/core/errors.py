class AppError(Exception):
    """
    Base class for application-level errors.

    These are expected errors that the API can safely convert
    into structured HTTP responses.
    """

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationAppError(AppError):
    status_code = 400
    error_code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class InternalAppError(AppError):
    status_code = 500
    error_code = "internal_error"