"""
Outcome Publisher — Change 8 (Phase 2)

Emits a routing outcome event to a Redis Stream after every model call completes.
The streaming endpoint calls publish_outcome_event() instead of calling
MetricsService and RoutingHistoryService directly.

Stream key: routing:outcomes
Consumer: backend/app/events/outcome_consumer.py (runs as a FastAPI background task)
"""

import json
import redis.asyncio as redis
from app.config.settings import settings

STREAM_KEY = "routing:outcomes"


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

    This is a fire-and-forget call; the background consumer handles all downstream
    writes to RoutingHistoryService and MetricsService asynchronously.
    """
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.xadd(
            STREAM_KEY,
            {
                "model_id": str(model_id),
                "task_type": task_type,
                "latency_ms": str(latency_ms),
                "success": "1" if success else "0",
                "tokens_per_sec": str(tokens_per_sec),
                "cost": str(cost),
            },
        )
    except Exception as e:
        # Non-fatal: if Redis is down, we lose telemetry but the request still succeeds.
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish outcome event: {e}")
    finally:
        await client.aclose()
