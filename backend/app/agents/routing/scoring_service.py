from typing import Tuple, Dict, Any
from app.models.registry import ModelRegistry
from app.models.analytics import ModelBenchmarks, ModelMetrics
from app.agents.routing.weight_generator import RoutingWeights

class ScoringService:
    """
    Stage 4 & 7: Multi-Dimensional Scoring & Confidence-Aware Routing.
    Calculates the final score and metadata for a specific model based on intent and constraints.
    """
    
    @staticmethod
    def score_model(
        model: ModelRegistry,
        weights: RoutingWeights,
        benchmark: ModelBenchmarks,
        metrics: ModelMetrics,
        recent_selections: list[str],
        confidence: float,
        recommended_tier: str = "fast"
    ) -> Tuple[float, Dict[str, Any]]:
        
        # 1. Base Benchmark Capability Score (Intent-weighted)
        b_coding = benchmark.coding_score if benchmark else 5.0
        b_reasoning = benchmark.reasoning_score if benchmark else 5.0
        b_math = benchmark.math_score if benchmark else 5.0
        b_vision = benchmark.vision_score if benchmark else 0.0
        b_creative = benchmark.creative_score if benchmark else 5.0
        
        capability_score = (
            (b_coding * weights.coding) +
            (b_reasoning * weights.reasoning) +
            (b_math * weights.math) +
            (b_vision * weights.vision) +
            (b_creative * weights.creative)
        )
        
        # 2. Confidence-Aware Adjustment (Stage 7)
        # If intent classification is weak, penalize highly specialized models (lower arena score)
        # and prefer strong generalists. We'll use arena_score as a proxy for "strong generalist".
        arena_bonus = 0.0
        if confidence < 0.6 and benchmark:
            # Normalize arena score (assume ~1000 is baseline, 1300 is max)
            arena_normalized = max(0, (benchmark.arena_score - 1000) / 30.0)
            arena_bonus = arena_normalized * 0.5  # Boost generalists when uncertain

        # 3. Cost & Latency Penalties
        cost_penalty = model.cost_per_1k_tokens * weights.cost * 10.0 # Scale cost penalty up
        
        avg_latency = metrics.average_latency_ms if metrics else 1000.0
        # Normalize latency penalty (e.g. 1000ms = 1 penalty point)
        latency_penalty = min((avg_latency / 1000.0) * weights.latency, 5.0)
        
        # 4. Reliability & Load Penalties
        error_rate = metrics.error_rate if metrics else 0.0
        error_penalty = min(error_rate * 5.0, 5.0) # Max 5 point penalty for 100% error rate
        
        # 5. Diversity Bonus / Penalty (Stage 9)
        # If the model was selected many times recently, penalize it slightly.
        recent_count = recent_selections.count(model.id)
        diversity_penalty = recent_count * 0.2
        
        # 6. Tier Match Penalty (Strict Enforcement)
        tier_penalty = 0.0
        # A model is "powerful" if it costs > $0.05 per 1k tokens OR has an arena score > 1150
        is_powerful = (model.cost_per_1k_tokens > 0.05) or (benchmark and benchmark.arena_score > 1150)
        
        if recommended_tier == "fast" and is_powerful:
            tier_penalty = 15.0  # Massive penalty for using an expensive/heavy model for simple tasks
        elif recommended_tier == "powerful" and not is_powerful:
            tier_penalty = 15.0  # Massive penalty for using a weak model for complex logic

        # Final Score Calculation
        final_score = capability_score + arena_bonus - latency_penalty - cost_penalty - error_penalty - diversity_penalty - tier_penalty
        
        metadata = {
            "final_score": round(final_score, 4),
            "capability_score": round(capability_score, 4),
            "arena_bonus": round(arena_bonus, 4),
            "latency_penalty": round(latency_penalty, 4),
            "cost_penalty": round(cost_penalty, 4),
            "error_penalty": round(error_penalty, 4),
            "diversity_penalty": round(diversity_penalty, 4),
            "tier_penalty": round(tier_penalty, 4)
        }
        
        return final_score, metadata
