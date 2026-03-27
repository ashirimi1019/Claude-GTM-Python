"""Centralized error handling — AppError, to_app_error, error_response."""

from fastapi.responses import JSONResponse


class AppError(Exception):
    """Application-level error with HTTP status code and machine-readable code."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


def to_app_error(err: Exception) -> AppError:
    """Convert any exception to an AppError. Pass-through if already AppError."""
    if isinstance(err, AppError):
        return err
    return AppError(message=str(err))


def error_response(err: AppError) -> JSONResponse:
    """Build a JSON error response from an AppError."""
    return JSONResponse(
        status_code=err.status_code,
        content={"error": err.code, "message": err.message},
    )
