from dataclasses import dataclass, field
from typing import List, Dict, Optional
from app.models.registry import ModelRegistry
from app.models.analytics import ModelMetrics
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
        metrics: Optional[Dict[str, ModelMetrics]] = None,
    ) -> CandidateResult:
        threshold = settings.CIRCUIT_BREAKER_ERROR_THRESHOLD

        def _is_circuit_broken(m: ModelRegistry) -> bool:
            """True if this model should be hard-excluded due to high error rate."""
            if metrics is None:
                return False
            model_metrics = metrics.get(str(m.id))
            if model_metrics is None:
                return False
            return model_metrics.error_rate > threshold

        active = [m for m in models if m.is_active and not _is_circuit_broken(m)]

        # --- Level 1: Strict — all constraints satisfied ---
        strict = [
            m for m in active
            if (not intent.requires_tools or m.supports_tools)
            and (intent.task != "vision" or m.supports_vision)
            and (m.cost_per_1k_tokens <= budget)
        ]
        if strict:
            return CandidateResult(models=strict, relaxation_level="strict")

        # --- Level 2: Drop budget constraint ---
        dropped_budget = [
            m for m in active
            if (not intent.requires_tools or m.supports_tools)
            and (intent.task != "vision" or m.supports_vision)
        ]
        if dropped_budget:
            return CandidateResult(
                models=dropped_budget,
                relaxation_level="dropped_budget",
                dropped_constraints=["budget"],
            )

        # --- Level 3: Drop tools constraint (budget already dropped) ---
        if intent.requires_tools:
            dropped_tools = [
                m for m in active
                if (intent.task != "vision" or m.supports_vision)
            ]
            if dropped_tools:
                return CandidateResult(
                    models=dropped_tools,
                    relaxation_level="dropped_tools",
                    dropped_constraints=["budget", "tools"],
                )

        # --- Level 4: Drop vision constraint (if applicable) ---
        if intent.task == "vision":
            dropped_vision = list(active)
            if dropped_vision:
                return CandidateResult(
                    models=dropped_vision,
                    relaxation_level="dropped_vision",
                    dropped_constraints=["budget", "tools", "vision"],
                )

        # --- Level 5: Ultimate fallback — all active models ---
        return CandidateResult(
            models=active,
            relaxation_level="fallback_all_active",
            dropped_constraints=["budget", "tools", "vision"],
        )
