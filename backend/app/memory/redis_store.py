import redis.asyncio as redis
import json
from typing import List, Dict, Any
from app.config.settings import settings

# Global fallback memory
_fallback_memory: Dict[str, List[Dict[str, Any]]] = {}
_redis_warned = False

class RedisMemoryStore:
    """
    Manages short-term conversation history for fast retrieval by LangGraph agents.
    Uses Redis as the backing store, falls back to in-memory dict if Redis is offline.
    """
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client = None

    async def get_client(self):
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def add_message(self, session_id: str, message: Dict[str, Any]):
        """
        Appends a message to the Redis list for this session.
        Limits history to the last 50 messages to prevent token bloat.
        """
        client = await self.get_client()
        key = f"chat_history:{session_id}"
        
        try:
            await client.rpush(key, json.dumps(message))
            await client.ltrim(key, -50, -1)
            await client.expire(key, 86400)
        except Exception:
            global _redis_warned
            if not _redis_warned:
                print("Warning: Redis connection failed. Falling back to in-memory chat history.")
                _redis_warned = True
            
            if session_id not in _fallback_memory:
                _fallback_memory[session_id] = []
            _fallback_memory[session_id].append(message)
            _fallback_memory[session_id] = _fallback_memory[session_id][-50:]

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the recent conversation history from Redis or fallback memory.
        """
        client = await self.get_client()
        key = f"chat_history:{session_id}"
        
        try:
            raw_messages = await client.lrange(key, 0, -1)
            return [json.loads(m) for m in raw_messages]
        except Exception:
            return _fallback_memory.get(session_id, [])
