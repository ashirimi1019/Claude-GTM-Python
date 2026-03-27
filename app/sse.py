"""SSE streaming helper using sse-starlette."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request


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
        try:
            async for message in pubsub.listen():
                if await request.is_disconnected():
                    break
                if message["type"] == "message":
                    yield {"data": message["data"].decode("utf-8")}
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await r.aclose()

    return EventSourceResponse(event_generator())
