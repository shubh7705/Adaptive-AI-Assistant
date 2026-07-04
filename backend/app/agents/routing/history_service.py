import redis.asyncio as redis
from typing import List
from app.config.settings import settings

# Global fallback for routing history
_fallback_routing_history: List[str] = []
_history_warned = False

class RoutingHistoryService:
    """
    Stage 9: Diversity Bonus
    Tracks recent routing history in Redis, falls back to in-memory list.
    """
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client = None

    async def get_client(self):
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def record_selection(self, model_id: str, limit: int = 10):
        client = await self.get_client()
        key = "global_routing_history"
        try:
            await client.lpush(key, model_id)
            await client.ltrim(key, 0, limit - 1)
        except Exception:
            global _history_warned
            if not _history_warned:
                print("Warning: Redis connection failed. Falling back to in-memory routing history.")
                _history_warned = True
                
            _fallback_routing_history.insert(0, model_id)
            if len(_fallback_routing_history) > limit:
                _fallback_routing_history.pop()

    async def get_recent_selections(self) -> List[str]:
        client = await self.get_client()
        key = "global_routing_history"
        try:
            return await client.lrange(key, 0, -1)
        except Exception:
            return _fallback_routing_history.copy()
