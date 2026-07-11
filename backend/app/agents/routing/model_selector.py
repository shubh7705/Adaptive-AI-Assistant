from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.registry import ModelRegistry
from app.schemas.intent import IntentClassification
from app.schemas.cost import CostOptimization
from app.schemas.selection import ModelSelection

from app.agents.routing.capability_filter import CapabilityFilter
from app.agents.routing.weight_generator import DynamicWeightGenerator
from app.agents.routing.benchmark_service import BenchmarkService
from app.agents.routing.metrics_service import MetricsService
from app.agents.routing.history_service import RoutingHistoryService
from app.agents.routing.scoring_service import ScoringService
from app.agents.routing.candidate_ranker import CandidateRanker

import logging

logger = logging.getLogger(__name__)

class ModelSelectionAgent:
    """
    Agent responsible for dynamically selecting the best model based on
    intent, required capabilities, and a multi-factor scoring algorithm.
    Refactored to production-grade AI Gateway standards with graceful fallbacks.
    """
    def __init__(self):
        # Keep stateless initializations here if applicable, 
        # but service logic handling DB interactions should accept the session per request.
        pass

    async def execute(
        self, 
        db: AsyncSession, 
        intent_data: IntentClassification, 
        cost_data: CostOptimization
    ) -> ModelSelection:
        
        # 1. Fetch all active models
        result = await db.execute(select(ModelRegistry).where(ModelRegistry.is_active))
        all_models = result.scalars().all()
        
        if not all_models:
            raise ValueError("No active models found in the registry!")

        # 2. Hard Requirements Filtering (Stage 1)
        eligible_models = CapabilityFilter.filter(all_models, intent_data, cost_data.max_budget_usd)
        
        # --- Stage 2: Fallback Handling Strategy ---
        # If hard constraints wipe out candidates, fall back to all active models 
        # to ensure system availability, but flag it in the rationale.
        using_fallback = False
        if not eligible_models:
            logger.warning(
                f"No models met strict criteria for task '{intent_data.task}' "
                f"with budget ${cost_data.max_budget_usd}. Invoking fallback routing."
            )
            eligible_models = all_models
            using_fallback = True
        
        # 3. Dynamic Weight Generation (Stage 3)
        weights = DynamicWeightGenerator.get_weights(intent_data.task)
        
        # 4. Fetch Runtime Metadata (Stages 5, 6, 9)
        # Pass the current request's async session to isolate database transactions
        benchmark_service = BenchmarkService(db)
        metrics_service = MetricsService(db)
        history_service = RoutingHistoryService(db) 
        
        eligible_ids = [m.id for m in eligible_models]
        benchmarks = await benchmark_service.get_benchmarks(eligible_ids)
        metrics = await metrics_service.get_metrics(eligible_ids)
        recent_selections = await history_service.get_recent_selections()
        
        # 5. Multi-Dimensional Scoring (Stage 4, 7, 9)
        scored_models = []
        for m in eligible_models:
            score, metadata = ScoringService.score_model(
                model=m,
                weights=weights,
                benchmark=benchmarks.get(m.id),
                metrics=metrics.get(m.id),
                recent_selections=recent_selections,
                confidence=intent_data.confidence,
                recommended_tier=cost_data.recommended_tier
            )
            scored_models.append((m, score, metadata))
            
        # 6. Top-K Candidate Selection (Stage 8)
        selected_model, final_score, routing_meta, runner_ups = CandidateRanker.select_best_model(scored_models, top_k=3)
        
        # 7. Record History (Stage 9)
        await history_service.record_selection(selected_model.id)
        
        # 8. Return Explainable Payload (Stage 10)
        rationale = routing_meta.pop("reason", "Selected by hybrid router.")
        if using_fallback:
            rationale = f"[FALLBACK ACTIVATED] {rationale} (Strict constraints relaxed to maintain service availability)."
            routing_meta["fallback_triggered"] = True

        return ModelSelection(
            selected_model_id=selected_model.id,
            selected_model_name=selected_model.name,
            provider=selected_model.provider,
            score=final_score,
            rationale=rationale,
            runner_ups=runner_ups,
            routing_metadata=routing_meta
        )
