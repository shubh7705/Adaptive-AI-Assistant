from pydantic import BaseModel
from typing import Dict

class DashboardSummary(BaseModel):
    total_requests: int
    cache_hit_rate: float
    avg_latency_ms: float
    total_cost_usd: float
    success_rate: float
    total_tokens: int

class RoutingDistribution(BaseModel):
    distribution: Dict[str, int] # e.g. {"deepseek-chat": 45, "gemma": 20}
