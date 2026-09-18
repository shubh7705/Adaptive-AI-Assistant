from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from app.models.registry import ModelRegistry
from app.models.analytics import ModelMetrics, ModelBenchmarks
from app.schemas.intent import IntentClassification
from app.config.settings import settings


@dataclass
class CandidateResult:
    """
    Structured result from CapabilityFilter.filter().
    Carries both the eligible model list AND an explanation of whether/which
    constraints had to be relaxed to produce a non-empty candidate set.
    """
    models: List[ModelRegistry]
    relaxation_level: str          # "strict" | "dropped_budget" | "dropped_tools" | "dropped_vision" | "fallback_all_active"
    dropped_constraints: List[str] = field(default_factory=list)
    trace: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class CapabilityFilter:
    """
    Stage 1: Filters models based on hard constraints from the required intent.
    Returns a CandidateResult that indicates which (if any) constraints were
    relaxed to guarantee a non-empty candidate set.
    """

    @staticmethod
    def filter(
        models: List[ModelRegistry],
        intent: IntentClassification,
        budget: float = 100.0,
        estimated_tokens: int = 0,
        metrics: Optional[Dict[str, ModelMetrics]] = None,
        benchmarks: Optional[Dict[str, ModelBenchmarks]] = None,
        recommended_tier: str = "fast"
    ) -> CandidateResult:
        threshold = settings.CIRCUIT_BREAKER_ERROR_THRESHOLD
        
        trace: Dict[str, Dict[str, Any]] = {}
        
        def _add_trace(m_id: str, reason: str):
            trace[m_id] = {
                "status": "dropped",
                "stage": "capability_filter",
                "reason": reason
            }

        def _is_circuit_broken(m: ModelRegistry) -> bool:
            """True if this model should be hard-excluded due to high error rate."""
            if metrics is None:
                return False
            model_metrics = metrics.get(str(m.id))
            if model_metrics is None:
                return False
            return model_metrics.error_rate > threshold
            
        def _is_tier_mismatch(m: ModelRegistry) -> bool:
            """True if model belongs to a tier entirely unsuited for the recommendation."""
            b = benchmarks.get(str(m.id)) if benchmarks else None
            arena_score = b.arena_score if b else 1000
            
            is_powerful = (m.cost_per_1k_tokens > 0.05) or (arena_score > 1150)
            
            if recommended_tier == "fast" and is_powerful:
                return True
            if recommended_tier == "powerful" and not is_powerful:
                return True
            return False

        registry_active = [m for m in models if m.is_active]
        if not registry_active:
            for m in models:
                _add_trace(str(m.id), "inactive_in_registry")
            return CandidateResult(models=[], relaxation_level="no_active_models", trace=trace)

        # 1. Circuit breaker check
        healthy = []
        for m in registry_active:
            m_id = str(m.id)
            if _is_circuit_broken(m):
                _add_trace(m_id, "circuit_breaker_triggered")
            else:
                healthy.append(m)

        base_pool = healthy if healthy else registry_active

        # 2. Tier match check (soft gate: if tier mismatch filters everything out, relax to base_pool)
        tier_matched = []
        for m in base_pool:
            m_id = str(m.id)
            if _is_tier_mismatch(m):
                _add_trace(m_id, "tier_mismatch")
            else:
                tier_matched.append(m)

        active = tier_matched if tier_matched else base_pool

        # Helper to check base constraints for the active list
        def _estimated_request_cost(m: ModelRegistry) -> float:
            # Registry pricing is dollars per 1K tokens; budget is dollars per request.
            return m.cost_per_1k_tokens * max(estimated_tokens, 0) / 1000

        def _check_strict(m: ModelRegistry) -> bool:
            if intent.requires_tools and not m.supports_tools:
                return False
            if intent.task == "vision" and not m.supports_vision:
                return False
            if _estimated_request_cost(m) > budget:
                return False
            return True

        # --- Level 1: Strict — all constraints satisfied ---
        strict = []
        for m in active:
            if _check_strict(m):
                strict.append(m)

        if strict:
            # For the ones that were dropped strictly, let's mark them.
            for m in active:
                if m not in strict:
                    # Determine exactly why it was dropped for the trace
                    m_id = str(m.id)
                    if _estimated_request_cost(m) > budget:
                        _add_trace(m_id, "budget_exceeded")
                    elif intent.requires_tools and not m.supports_tools:
                        _add_trace(m_id, "missing_tools_support")
                    elif intent.task == "vision" and not m.supports_vision:
                        _add_trace(m_id, "missing_vision_support")
                        
            return CandidateResult(models=strict, relaxation_level="strict", trace=trace)

        # If strict fails, we must relax constraints. We don't trace drop reasons for relaxed constraints
        # because the remaining models ARE selected (we are dropping the constraints, not the models).
        
        # --- Level 2: Drop budget constraint ---
        dropped_budget = [
            m for m in active
            if (not intent.requires_tools or m.supports_tools)
            and (intent.task != "vision" or m.supports_vision)
        ]
        if dropped_budget:
            # Mark only the ones truly excluded
            for m in active:
                if m not in dropped_budget:
                    m_id = str(m.id)
                    if intent.requires_tools and not m.supports_tools:
                        _add_trace(m_id, "missing_tools_support")
                    elif intent.task == "vision" and not m.supports_vision:
                        _add_trace(m_id, "missing_vision_support")
                        
            return CandidateResult(
                models=dropped_budget,
                relaxation_level="dropped_budget",
                dropped_constraints=["budget"],
                trace=trace
            )

        # --- Level 3: Drop tools constraint (budget already dropped) ---
        if intent.requires_tools:
            dropped_tools = [
                m for m in active
                if (intent.task != "vision" or m.supports_vision)
            ]
            if dropped_tools:
                for m in active:
                    if m not in dropped_tools:
                        _add_trace(str(m.id), "missing_vision_support")
                        
                return CandidateResult(
                    models=dropped_tools,
                    relaxation_level="dropped_tools",
                    dropped_constraints=["budget", "tools"],
                    trace=trace
                )

        # --- Level 4: Drop vision constraint (if applicable) ---
        if intent.task == "vision":
            dropped_vision = list(active)
            if dropped_vision:
                return CandidateResult(
                    models=dropped_vision,
                    relaxation_level="dropped_vision",
                    dropped_constraints=["budget", "tools", "vision"],
                    trace=trace
                )

        # --- Level 5: Ultimate fallback — all active models ---
        return CandidateResult(
            models=base_pool,
            relaxation_level="fallback_all_active",
            dropped_constraints=["budget", "tools", "vision", "tier"],
            trace=trace
        )
