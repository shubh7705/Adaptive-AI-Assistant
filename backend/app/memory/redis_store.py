import redis.asyncio as redis
import json
from typing import List, Dict, Any
from app.config.settings import settings

class RedisMemoryStore:
    """
    Manages short-term conversation history for fast retrieval by LangGraph agents.
    Uses Redis as the backing store.
    """
    def __init__(self):
        # We catch connection errors locally to ensure the app doesn't crash if Redis isn't running yet.
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
            # Keep only the last 50 messages
            await client.ltrim(key, -50, -1)
            # Expire short-term memory after 24 hours of inactivity
            await client.expire(key, 86400)
        except redis.ConnectionError:
            # Fallback for local development if Redis isn't up
            print(f"Warning: Redis connection failed. Message for {session_id} not cached.")

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the recent conversation history from Redis.
        """
        client = await self.get_client()
        key = f"chat_history:{session_id}"
        
        try:
            raw_messages = await client.lrange(key, 0, -1)
            return [json.loads(m) for m in raw_messages]
        except redis.ConnectionError:
            return []
