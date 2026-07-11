import asyncio
import redis.asyncio as redis
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings

# Global fallback for routing history
_fallback_routing_history: List[str] = []
_history_warned = False
_fallback_lock = asyncio.Lock()

class RoutingHistoryService:
    """
    Stage 9: Diversity Bonus
    Tracks recent routing history in Redis, falls back to in-memory list.
    """
    _redis_pool = None

    def __init__(self, db: Optional[AsyncSession] = None):
        self.redis_url = settings.REDIS_URL
        self.db = db

    @classmethod
    async def get_client(cls, redis_url: str):
        if cls._redis_pool is None:
            # Using from_url connection pool manager
            cls._redis_pool = redis.from_url(redis_url, decode_responses=True)
        return cls._redis_pool

    async def record_selection(self, model_id: str, limit: int = 10):
        client = await self.get_client(self.redis_url)
        key = "global_routing_history"
        try:
            await client.lpush(key, model_id)
            await client.ltrim(key, 0, limit - 1)
        except Exception:
            global _history_warned
            if not _history_warned:
                print("Warning: Redis connection failed. Falling back to in-memory routing history.")
                _history_warned = True
                
            async with _fallback_lock:
                _fallback_routing_history.insert(0, model_id)
                if len(_fallback_routing_history) > limit:
                    _fallback_routing_history.pop()

    async def get_recent_selections(self) -> List[str]:
        client = await self.get_client(self.redis_url)
        key = "global_routing_history"
        try:
            return await client.lrange(key, 0, -1)
        except Exception:
            async with _fallback_lock:
                return _fallback_routing_history.copy()
