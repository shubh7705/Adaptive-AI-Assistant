from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.analytics import ModelBenchmarks
from app.config.settings import settings
from typing import Dict, List, Optional
import time

class BenchmarkService:
    """
    Stage 6: Benchmark Scores
    Fetches benchmark scores from the database, with a short TTL in-process cache
    so the routing hot-path never hits Postgres directly on every request.
    """
    _cache: Dict[str, tuple] = {}  # key -> (data, expires_at)

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ttl = settings.ROUTING_CACHE_TTL_SECONDS

    async def get_benchmarks(self, eligible_ids: List[str] = None) -> Dict[str, ModelBenchmarks]:
        cache_key = "all" if eligible_ids is None else "|".join(sorted(eligible_ids))
        now = time.monotonic()
        if cache_key in BenchmarkService._cache:
            data, expires_at = BenchmarkService._cache[cache_key]
            if now < expires_at:
                return data

        if eligible_ids is not None:
            result = await self.db.execute(select(ModelBenchmarks).where(ModelBenchmarks.model_id.in_(eligible_ids)))
        else:
            result = await self.db.execute(select(ModelBenchmarks))
        benchmarks = result.scalars().all()
        data = {b.model_id: b for b in benchmarks}

        BenchmarkService._cache[cache_key] = (data, now + self._ttl)
        return data

    @classmethod
    def invalidate(cls, model_id: str):
        """Call after writing a new benchmark row to drop stale cache entries."""
        cls._cache = {k: v for k, v in cls._cache.items() if model_id not in k}
    async def get_benchmark_for_model(self, model_id: str) -> ModelBenchmarks:
        result = await self.db.execute(select(ModelBenchmarks).where(ModelBenchmarks.model_id == model_id))
        return result.scalars().first()
