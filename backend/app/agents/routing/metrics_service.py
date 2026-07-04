from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.analytics import ModelMetrics
from typing import Dict

class MetricsService:
    """
    Stage 5: Runtime Metrics
    Fetches and manages runtime metrics for routing scoring.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_metrics(self) -> Dict[str, ModelMetrics]:
        result = await self.db.execute(select(ModelMetrics))
        metrics = result.scalars().all()
        return {m.model_id: m for m in metrics}
        
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
            
        await self.db.commit()
