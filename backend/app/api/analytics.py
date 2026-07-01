from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database.session import get_db
from app.models.analytics import RoutingLog
from app.models.registry import ModelRegistry
from app.schemas.analytics import DashboardSummary, RoutingDistribution
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns high-level aggregate metrics for the dashboard.
    """
    # In a fully populated DB, we would run aggregate SUM/AVG queries here.
    # For now, we will query and calculate them manually, falling back to 0 if no logs exist.
    result = await db.execute(select(RoutingLog))
    logs = result.scalars().all()
    
    if not logs:
        return DashboardSummary(
            total_requests=0,
            cache_hit_rate=0.0,
            avg_latency_ms=0.0,
            total_cost_usd=0.0,
            success_rate=1.0, # Default safe
            total_tokens=0
        )
        
    total_requests = len(logs)
    cache_hits = sum(1 for log in logs if log.cache_hit)
    total_latency = sum(log.latency_ms for log in logs)
    total_cost = sum(log.estimated_cost for log in logs)
    total_tokens = sum(log.total_tokens for log in logs)
    fallbacks = sum(1 for log in logs if log.is_fallback)
    
    return DashboardSummary(
        total_requests=total_requests,
        cache_hit_rate=(cache_hits / total_requests) * 100 if total_requests > 0 else 0.0,
        avg_latency_ms=total_latency / total_requests if total_requests > 0 else 0.0,
        total_cost_usd=total_cost,
        success_rate=((total_requests - fallbacks) / total_requests) * 100 if total_requests > 0 else 100.0,
        total_tokens=total_tokens
    )

@router.get("/routing-distribution", response_model=RoutingDistribution)
async def get_routing_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the count of requests routed to each specific model.
    """
    # Join RoutingLog with ModelRegistry to group by Model Name
    stmt = (
        select(ModelRegistry.name, func.count(RoutingLog.id))
        .select_from(RoutingLog)
        .join(ModelRegistry, RoutingLog.model_id == ModelRegistry.id)
        .group_by(ModelRegistry.name)
    )
    result = await db.execute(stmt)
    
    distribution = {row[0]: row[1] for row in result.all()}
    
    if not distribution:
        # Mock data if empty for frontend testing
        distribution = {"deepseek-chat-v3-0324": 0, "gemma-3-12b-it": 0}
        
    return RoutingDistribution(distribution=distribution)
