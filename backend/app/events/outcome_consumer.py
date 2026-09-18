"""
Outcome Consumer — Change 8 (Phase 2)

Background worker that reads from the Redis Stream 'routing:outcomes' and
calls MetricsService and RoutingHistoryService asynchronously, fully decoupled
from the request path.

Wire into FastAPI lifespan:
    from app.events.outcome_consumer import start_outcome_consumer
    asyncio.create_task(start_outcome_consumer())
"""

import asyncio
import json
import logging
import redis.asyncio as redis

from app.config.settings import settings
from app.events.outcome_publisher import STREAM_KEY

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "routing_consumer_group"
CONSUMER_NAME = "worker-1"
BLOCK_MS = 5000  # How long to block waiting for new events before looping


async def _process_event(data: dict) -> None:
    """
    Handles a single routing outcome event.
    Updates RoutingHistoryService and MetricsService.
    """
    from app.agents.routing.history_service import RoutingHistoryService
    from app.agents.routing.metrics_service import MetricsService
    from app.database.session import AsyncSessionLocal

    model_id = data.get("model_id", "")
    task_type = data.get("task_type", "chat")
    latency_ms = float(data.get("latency_ms", 0.0))
    success = data.get("success") == "1"
    tokens_per_sec = float(data.get("tokens_per_sec", 0.0))

    # 1. Update diversity history (scoped by task_type — Change 9)
    history_service = RoutingHistoryService()
    await history_service.record_selection(model_id, task_type=task_type)

    # 2. Update runtime metrics in Postgres via a fresh DB session
    async with AsyncSessionLocal() as db:
        metrics_service = MetricsService(db)
        await metrics_service.update_metrics_after_request(
            model_id=model_id,
            latency_ms=latency_ms,
            success=success,
            tokens_per_sec=tokens_per_sec,
        )
        await db.commit()


async def start_outcome_consumer() -> None:
    """
    Long-running background coroutine. Reads from the Redis Stream and dispatches
    events to _process_event(). Must be launched as an asyncio task in FastAPI
    lifespan so it runs concurrently with the web server.
    """
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    warned_disconnected = False

    while True:
        try:
            # Create consumer group (idempotent — raises if already exists or fails if offline)
            try:
                await client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="$", mkstream=True)
            except Exception:
                pass  # Group already exists or redis is currently unavailable

            results = await client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM_KEY: ">"},
                count=10,
                block=BLOCK_MS,
            )

            if warned_disconnected:
                from app.config.logger import logger as loguru_logger
                loguru_logger.info("Redis connection established. Outcome consumer active.")
                warned_disconnected = False

            if not results:
                continue

            for _stream, messages in results:
                for msg_id, data in messages:
                    try:
                        await _process_event(data)
                        await client.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                    except Exception as e:
                        from app.config.logger import logger as loguru_logger
                        loguru_logger.error(f"Failed to process outcome event {msg_id}: {e}")

        except asyncio.CancelledError:
            from app.config.logger import logger as loguru_logger
            loguru_logger.info("Outcome consumer shutting down.")
            break
        except Exception as e:
            import redis as redis_lib
            if isinstance(e, redis_lib.exceptions.TimeoutError):
                continue

            # Connection or socket errors when Redis is not running locally
            if not warned_disconnected:
                from app.config.logger import logger as loguru_logger
                loguru_logger.warning("Redis is unreachable for outcome consumer. Standing by (falling back to in-memory processing)...")
                warned_disconnected = True

            await asyncio.sleep(10)

    try:
        await client.aclose()
    except Exception:
        pass
