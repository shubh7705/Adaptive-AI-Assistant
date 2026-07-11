from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.registry import ModelRegistry
from app.schemas.intent import IntentClassification
from app.schemas.cost import CostOptimization
from app.schemas.selection import ModelSelection

from app.agents.routing.capability_filter import CapabilityFilter, CandidateResult
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
        # CandidateResult surfaces which constraints were relaxed (if any).
        candidate_result: CandidateResult = CapabilityFilter.filter(all_models, intent_data, cost_data.max_budget_usd)
        eligible_models = candidate_result.models
        relaxation_level = candidate_result.relaxation_level
        dropped_constraints = candidate_result.dropped_constraints

        if relaxation_level != "strict":
            logger.warning(
                f"Constraint relaxation triggered for task '{intent_data.task}': "
                f"level='{relaxation_level}', dropped={dropped_constraints}"
            )
        
        # 3. Dynamic Weight Generation (Stage 3)
        weights = DynamicWeightGenerator.get_weights(intent_data.task)
        
        # 4. Fetch Runtime Metadata (Stages 5, 6, 9)
        # Pass the current request's async session to isolate database transactions
        benchmark_service = BenchmarkService(db)
        metrics_service = MetricsService(db)
        history_service = RoutingHistoryService()
        
        eligible_ids = [m.id for m in eligible_models]
        benchmarks = await benchmark_service.get_benchmarks(eligible_ids)
        metrics = await metrics_service.get_metrics(eligible_ids)
        recent_selections = await history_service.get_recent_selections()
        
        # 5. Multi-Dimensional Scoring (Stage 4, 7, 9)
        # Pre-compute max cost among eligible models to normalize cost_penalty correctly.
        max_eligible_cost = max(
            (m.cost_per_1k_tokens for m in eligible_models), default=0.06
        )
        scored_models = []
        for m in eligible_models:
            score, metadata = ScoringService.score_model(
                model=m,
                weights=weights,
                benchmark=benchmarks.get(m.id),
                metrics=metrics.get(m.id),
                recent_selections=recent_selections,
                confidence=intent_data.confidence,
                recommended_tier=cost_data.recommended_tier,
                max_eligible_cost=max_eligible_cost,
            )
            scored_models.append((m, score, metadata))
            
        # 6. Top-K Candidate Selection (Stage 8)
        selected_model, final_score, routing_meta, runner_ups = CandidateRanker.select_best_model(scored_models, top_k=3)
        
        # 7. Record History — cast to str so it matches what Redis returns as strings.
        await history_service.record_selection(str(selected_model.id))
        
        # 8. Return Explainable Payload (Stage 10)
        rationale = routing_meta.pop("reason", "Selected by hybrid router.")
        if relaxation_level != "strict":
            rationale = (
                f"[CONSTRAINT RELAXATION: {relaxation_level.upper()}] {rationale} "
                f"(Dropped constraints: {dropped_constraints})"
            )
            routing_meta["relaxation_level"] = relaxation_level
            routing_meta["dropped_constraints"] = dropped_constraints

        return ModelSelection(
            selected_model_id=selected_model.id,
            selected_model_name=selected_model.name,
            provider=selected_model.provider,
            score=final_score,
            rationale=rationale,
            runner_ups=runner_ups,
            routing_metadata=routing_meta
        )
