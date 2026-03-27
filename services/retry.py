"""Retry utility — exponential backoff with jitter for API calls."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


async def retry_with_backoff(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """Execute an async function with exponential backoff + jitter.

    Args:
        fn: Async callable to execute.
        max_retries: Maximum number of retry attempts (0 = no retries).
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        retryable_exceptions: Exception types that trigger a retry.

    Returns:
        The return value of fn().

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e

            if attempt >= max_retries:
                logger.error(
                    "Retry exhausted",
                    fn=fn.__name__,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )
                raise

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            logger.warn(
                "Retrying after error",
                fn=fn.__name__,
                attempt=attempt + 1,
                delay=round(delay, 2),
                error=str(e),
            )
            await asyncio.sleep(delay)

    # Should never reach here, but satisfy type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic error")
