"""Apollo client error handling."""

from __future__ import annotations

from app.errors import AppError


class ApolloError(AppError):
    """Apollo API error with retry information."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        apollo_code: str = "",
        retryable: bool = False,
    ):
        code = f"APOLLO_{apollo_code}" if apollo_code else "APOLLO_ERROR"
        super().__init__(message=message, status_code=status_code, code=code)
        self.retryable = retryable
        self.apollo_code = apollo_code


def handle_apollo_error(status_code: int, body: str = "") -> ApolloError:
    """Convert an HTTP error to an ApolloError."""
    if status_code == 429:
        return ApolloError(
            message="Apollo rate limit exceeded — retry after backoff",
            status_code=429,
            apollo_code="RATE_LIMITED",
            retryable=True,
        )
    elif status_code == 401:
        return ApolloError(
            message="Apollo API key is invalid or expired",
            status_code=401,
            apollo_code="AUTH_FAILED",
            retryable=False,
        )
    elif status_code == 402:
        return ApolloError(
            message="Apollo account has insufficient credits",
            status_code=402,
            apollo_code="INSUFFICIENT_CREDITS",
            retryable=False,
        )
    elif status_code == 403:
        return ApolloError(
            message="Apollo API access forbidden — check plan permissions",
            status_code=403,
            apollo_code="FORBIDDEN",
            retryable=False,
        )
    elif status_code == 404:
        return ApolloError(
            message=f"Apollo resource not found: {body}",
            status_code=404,
            apollo_code="NOT_FOUND",
            retryable=False,
        )
    elif status_code == 422:
        return ApolloError(
            message=f"Apollo validation error: {body}",
            status_code=422,
            apollo_code="VALIDATION_ERROR",
            retryable=False,
        )
    elif status_code >= 500:
        return ApolloError(
            message=f"Apollo server error ({status_code}): {body}",
            status_code=status_code,
            apollo_code="SERVER_ERROR",
            retryable=True,
        )
    else:
        return ApolloError(
            message=f"Apollo error ({status_code}): {body}",
            status_code=status_code,
            apollo_code="UNKNOWN",
            retryable=False,
        )
