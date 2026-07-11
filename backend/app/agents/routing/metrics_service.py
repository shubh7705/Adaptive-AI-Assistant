from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.analytics import ModelMetrics
from app.config.settings import settings
from typing import Dict, List
import time

class MetricsService:
    """
    Stage 5: Runtime Metrics
    Fetches and manages runtime metrics for routing scoring, with a short TTL
    in-process cache so the routing hot-path never hits Postgres directly.
    """
    _cache: Dict[str, tuple] = {}  # key -> (data, expires_at)

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ttl = settings.ROUTING_CACHE_TTL_SECONDS

    @classmethod
    def invalidate(cls, model_id: str):
        """Call after writing updated metrics to drop stale cache entries."""
        cls._cache = {k: v for k, v in cls._cache.items() if model_id not in k}

    async def get_metrics(self, eligible_ids: List[str] = None) -> Dict[str, ModelMetrics]:
        cache_key = "all" if eligible_ids is None else "|".join(sorted(eligible_ids))
        now = time.monotonic()
        if cache_key in MetricsService._cache:
            data, expires_at = MetricsService._cache[cache_key]
            if now < expires_at:
                return data

        if eligible_ids is not None:
            result = await self.db.execute(select(ModelMetrics).where(ModelMetrics.model_id.in_(eligible_ids)))
        else:
            result = await self.db.execute(select(ModelMetrics))
        metrics = result.scalars().all()
        data = {m.model_id: m for m in metrics}

        MetricsService._cache[cache_key] = (data, now + self._ttl)
        return data
    async def get_metrics_for_model(self, model_id: str) -> ModelMetrics:
        result = await self.db.execute(select(ModelMetrics).where(ModelMetrics.model_id == model_id))
        return result.scalars().first()
        
    async def update_metrics_after_request(self, model_id: str, latency_ms: float, success: bool, tokens_per_sec: float = 0.0):
        # In a real system, this would be an upsert or atomic update.
        # For simplicity, we fetch, update, and commit.
        metrics = await self.get_metrics_for_model(model_id)
        if not metrics:
            metrics = ModelMetrics(model_id=model_id)
            self.db.add(metrics)
            
        metrics.requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            
        metrics.success_rate = metrics.successful_requests / metrics.requests
        metrics.error_rate = metrics.failed_requests / metrics.requests
        
        # Exponential moving average for latency and tps
        alpha = 0.1
        metrics.average_latency_ms = (alpha * latency_ms) + ((1 - alpha) * metrics.average_latency_ms) if metrics.average_latency_ms else latency_ms
        if tokens_per_sec > 0:
            metrics.average_tokens_per_sec = (alpha * tokens_per_sec) + ((1 - alpha) * metrics.average_tokens_per_sec) if metrics.average_tokens_per_sec else tokens_per_sec
            
        await self.db.flush()
        # Invalidate cached entries for this model so the next routing request
        # reads fresh metrics rather than stale cached data.
        MetricsService.invalidate(model_id)
