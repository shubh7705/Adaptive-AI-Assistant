from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy import Integer

from app.database.session import get_db
from app.models.analytics import RoutingLog
from app.models.registry import ModelRegistry
from app.schemas.analytics import DashboardSummary, RoutingDistribution

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns high-level aggregate metrics for the dashboard using SQL aggregates.
    """
    from sqlalchemy import func, case
    
    stmt = select(
        func.count(RoutingLog.id).label("total_requests"),
        func.sum(func.cast(RoutingLog.cache_hit, Integer)).label("cache_hits"),
        func.avg(RoutingLog.latency_ms).label("avg_latency_ms"),
        func.sum(RoutingLog.estimated_cost).label("total_cost"),
        func.sum(RoutingLog.total_tokens).label("total_tokens"),
        func.sum(case((RoutingLog.is_fallback == True, 1), else_=0)).label("fallbacks"),
    )
    result = await db.execute(stmt)
    row = result.one()
    
    total_requests = row.total_requests or 0
    cache_hits = row.cache_hits or 0
    total_latency = row.avg_latency_ms or 0.0
    total_cost = row.total_cost or 0.0
    total_tokens = row.total_tokens or 0
    fallbacks = row.fallbacks or 0
    
    return DashboardSummary(
        total_requests=total_requests,
        cache_hit_rate=(cache_hits / total_requests) * 100 if total_requests > 0 else 0.0,
        avg_latency_ms=total_latency if total_requests > 0 else 0.0,
        total_cost_usd=total_cost,
        success_rate=((total_requests - fallbacks) / total_requests) * 100 if total_requests > 0 else 100.0,
        total_tokens=total_tokens
    )

@router.get("/routing-distribution", response_model=RoutingDistribution)
async def get_routing_distribution(
    db: AsyncSession = Depends(get_db),
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

@router.get("/cost-by-provider")
async def get_cost_by_provider(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the total estimated cost grouped by AI provider.
    """
    stmt = (
        select(ModelRegistry.provider, func.sum(RoutingLog.estimated_cost))
        .select_from(RoutingLog)
        .join(ModelRegistry, RoutingLog.model_id == ModelRegistry.id)
        .group_by(ModelRegistry.provider)
    )
    result = await db.execute(stmt)
    
    data = [{"provider": row[0].capitalize() if row[0] else "Unknown", "cost": round(row[1], 4)} for row in result.all()]
    if not data:
        data = [{"provider": "Google", "cost": 0.0}]
        
    return data

@router.get("/time-series")
async def get_time_series(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the latest 20 routing logs formatted for a time-series chart.
    """
    stmt = select(RoutingLog).order_by(RoutingLog.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    logs.reverse() # Chronological order
    
    data = []
    for log in logs:
        data.append({
            "time": log.created_at.strftime("%H:%M:%S") if log.created_at else "00:00:00",
            "tokens": log.total_tokens,
            "cost": round(log.estimated_cost, 4)
        })
        
    if not data:
        data = [{"time": "00:00:00", "tokens": 0, "cost": 0.0}]
        
    return data
