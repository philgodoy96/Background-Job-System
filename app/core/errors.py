class AppError(Exception):
    """
    Base class for application-level errors.

    Application and domain layers should raise AppError subclasses instead of
    framework-specific exceptions such as FastAPI's HTTPException.
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class ValidationError(AppError):
    """
    Raised when input data is invalid.
    """


class NotFoundError(AppError):
    """
    Raised when a requested resource does not exist.
    """


class ConflictError(AppError):
    """
    Raised when an operation conflicts with the current system state.
    """


class InfrastructureError(AppError):
    """
    Raised when an infrastructure dependency fails unexpectedly.
    """