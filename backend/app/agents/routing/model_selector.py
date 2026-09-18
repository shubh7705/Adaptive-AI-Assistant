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

        # 2. Fetch Runtime Metadata (Stages 5, 6, 9)
        # We fetch this BEFORE filtering now because the new Tier Match logic in 
        # CapabilityFilter requires arena_score (from benchmarks) and error_rate (from metrics).
        benchmark_service = BenchmarkService(db)
        metrics_service = MetricsService(db)
        history_service = RoutingHistoryService()
        
        all_ids = [m.id for m in all_models]
        all_benchmarks = await benchmark_service.get_benchmarks(all_ids)
        all_metrics = await metrics_service.get_metrics(all_ids)

        # 3. Hard Requirements & Tier Filtering (Stage 1)
        candidate_result: CandidateResult = CapabilityFilter.filter(
            models=all_models, 
            intent=intent_data, 
            budget=cost_data.max_budget_usd, 
            estimated_tokens=cost_data.estimated_tokens,
            metrics=all_metrics,
            benchmarks=all_benchmarks,
            recommended_tier=cost_data.recommended_tier
        )
        
        eligible_models = candidate_result.models
        relaxation_level = candidate_result.relaxation_level
        dropped_constraints = candidate_result.dropped_constraints
        trace = candidate_result.trace

        if relaxation_level != "strict":
            logger.warning(
                f"Constraint relaxation triggered for task '{intent_data.task}': "
                f"level='{relaxation_level}', dropped={dropped_constraints}"
            )
        
        # 4. Dynamic Weight Generation (Stage 3)
        weights = DynamicWeightGenerator.get_weights(intent_data.task)
        
        # 5. Multi-Dimensional Scoring (Stage 4, 7, 9)
        recent_selections = await history_service.get_recent_selections(task_type=intent_data.task)
        
        max_eligible_cost = max(
            (m.cost_per_1k_tokens for m in eligible_models), default=0.06
        )
        scored_models = []
        
        for m in eligible_models:
            m_id = str(m.id)
            score, metadata = ScoringService.score_model(
                model=m,
                weights=weights,
                benchmark=all_benchmarks.get(m.id),
                metrics=all_metrics.get(m.id),
                recent_selections=recent_selections,
                confidence=intent_data.confidence,
                recommended_tier=cost_data.recommended_tier,
                max_eligible_cost=max_eligible_cost,
            )
            scored_models.append((m, score, metadata))
            
            # Trace eligible but not-yet-ranked models
            trace[m_id] = {
                "status": "scored",
                "stage": "scoring_service",
                "final_score": score,
                "breakdown": metadata.get("breakdown", {})
            }
            
        # 6. Top-K Candidate Selection (Stage 8)
        selected_model, final_score, routing_meta, runner_ups = CandidateRanker.select_best_model(
            scored_models=scored_models, 
            trace=trace,
            top_k=3
        )
        
        # 7. History and runtime metrics are updated from the final stream outcome.
        # Recording here would count failed requests and duplicate the Redis-stream consumer.

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
            routing_metadata=routing_meta,
            trace=trace
        )
