"""
Outcome Publisher — Change 8 (Phase 2)

Emits a routing outcome event to a Redis Stream after every model call completes.
The streaming endpoint calls publish_outcome_event() instead of calling
MetricsService and RoutingHistoryService directly.

Stream key: routing:outcomes
Consumer: backend/app/events/outcome_consumer.py (runs as a FastAPI background task)
"""

import asyncio
import redis.asyncio as redis
from app.config.settings import settings

STREAM_KEY = "routing:outcomes"
_publisher_warned = False


async def publish_outcome_event(
    model_id: str,
    task_type: str,
    latency_ms: float,
    success: bool,
    tokens_per_sec: float = 0.0,
    cost: float = 0.0,
) -> None:
    """
    Publishes a {model_id, task_type, latency_ms, success, tokens_per_sec, cost}
    event to the Redis Stream 'routing:outcomes'.

    If Redis is down/unreachable, falls back to local in-process handling via _process_event.
    """
    payload = {
        "model_id": str(model_id),
        "task_type": task_type,
        "latency_ms": str(latency_ms),
        "success": "1" if success else "0",
        "tokens_per_sec": str(tokens_per_sec),
        "cost": str(cost),
    }

    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.xadd(STREAM_KEY, payload)
    except Exception:
        global _publisher_warned
        if not _publisher_warned:
            from app.config.logger import logger as loguru_logger
            loguru_logger.warning("Redis is unreachable for event publishing. Processing routing outcomes in-memory.")
            _publisher_warned = True
        # Direct in-process fallback
        try:
            from app.events.outcome_consumer import _process_event
            asyncio.create_task(_process_event(payload))
        except Exception:
            pass
    finally:
        try:
            await client.aclose()
        except Exception:
            pass
