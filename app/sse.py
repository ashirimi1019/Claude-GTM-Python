"""SSE streaming helper using sse-starlette."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

# Maximum time (seconds) an SSE stream can stay open before auto-closing.
SSE_TIMEOUT_SECONDS = 600  # 10 minutes


async def sse_skill_stream(channel: str, redis_url: str, request: Request) -> EventSourceResponse:
    """Create an SSE response that streams skill run events from a Redis pub/sub channel.

    Args:
        channel: Redis pub/sub channel name (e.g. "skill-run:offer:campaign:1").
        redis_url: Redis connection URL.
        request: The incoming Starlette request (used for disconnect detection).

    Returns:
        An EventSourceResponse that yields events as they arrive.
    """
    r = aioredis.from_url(redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    async def event_generator() -> AsyncGenerator[dict, None]:
        start_time = time.monotonic()
        try:
            async for message in pubsub.listen():
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                # Check for idle timeout
                if time.monotonic() - start_time > SSE_TIMEOUT_SECONDS:
                    yield {"data": json.dumps({"type": "timeout", "message": "Stream timed out"})}
                    break

                if message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    yield {"data": data}

                    # Check for termination signal in the message
                    try:
                        parsed = json.loads(data)
                        if parsed.get("type") == "done" or parsed.get("step") == "done":
                            break
                    except (json.JSONDecodeError, AttributeError):
                        pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await r.aclose()

    return EventSourceResponse(event_generator())
