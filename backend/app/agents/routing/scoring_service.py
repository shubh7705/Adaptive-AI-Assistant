from typing import Tuple, Dict, Any, List
from app.models.registry import ModelRegistry
from app.models.analytics import ModelBenchmarks, ModelMetrics
from app.agents.routing.weight_generator import RoutingWeights

class ScoringService:
    """
    Stage 4 & 7: Multi-Dimensional Scoring & Confidence-Aware Routing.
    Calculates the final score (out of 100) and structured metadata for a specific model.
    """
    
    @staticmethod
    def score_model(
        model: ModelRegistry,
        weights: RoutingWeights,
        benchmark: ModelBenchmarks,
        metrics: ModelMetrics,
        recent_selections: List[str],
        confidence: float,
        recommended_tier: str = "fast",
        max_eligible_cost: float = 0.06,
    ) -> Tuple[float, Dict[str, Any]]:
        
        # 1. Base Benchmark Capability Score (Max 60 points)
        b_coding = benchmark.coding_score if benchmark else 5.0
        b_reasoning = benchmark.reasoning_score if benchmark else 5.0
        b_math = benchmark.math_score if benchmark else 5.0
        b_vision = benchmark.vision_score if benchmark else 5.0
        b_creative = benchmark.creative_score if benchmark else 5.0
        
        # Weighted sum is max ~10. Multiply by 6.0 to get max 60.
        raw_capability = (
            (b_coding * weights.coding) +
            (b_reasoning * weights.reasoning) +
            (b_math * weights.math) +
            (b_vision * weights.vision) +
            (b_creative * weights.creative)
        )
        base_capability = min(raw_capability * 6.0, 60.0)
        
        # 2. Modifiers: Arena Bonus (Max 20 points)
        arena_bonus = 0.0
        if benchmark:
            # Normalize arena score assuming 1000 is baseline, 1300 is max
            arena_normalized = max(0.0, min(1.0, (benchmark.arena_score - 1000.0) / 300.0))
            # If intent classification is weak, generalists get full bonus, otherwise half
            multiplier = 20.0 if confidence < 0.6 else 10.0
            arena_bonus = arena_normalized * multiplier

        # 3. Penalties (Max 40 points total)
        # Cost Penalty (Max 10 points)
        cost_ratio = model.cost_per_1k_tokens / max_eligible_cost if max_eligible_cost > 0 else 0.0
        cost_penalty = min(cost_ratio * weights.cost * 10.0, 10.0)
        
        # Latency Penalty (Max 10 points)
        avg_latency = metrics.average_latency_ms if metrics else 1000.0
        latency_penalty = min((avg_latency / 1000.0) * weights.latency * 2.0, 10.0)
        
        # Error Penalty (Max 10 points)
        error_rate = metrics.error_rate if metrics else 0.0
        error_penalty = min(error_rate * 10.0, 10.0) 
        
        # Diversity Penalty (Max 10 points)
        recent_count = recent_selections.count(str(model.id))
        diversity_penalty = min(recent_count * 2.0, 10.0)
        
        # Final Score Calculation
        final_score = base_capability + arena_bonus - latency_penalty - cost_penalty - error_penalty - diversity_penalty
        final_score = max(0.0, min(100.0, final_score)) # Clamp between 0 and 100
        
        # Structured Metadata (Routing Waterfall Format)
        metadata = {
            "final_score": round(final_score, 4),
            "breakdown": {
                "base_capability": round(base_capability, 4),
                "modifiers": {
                    "arena_bonus": round(arena_bonus, 4)
                },
                "penalties": {
                    "latency_penalty": round(latency_penalty, 4),
                    "cost_penalty": round(cost_penalty, 4),
                    "error_penalty": round(error_penalty, 4),
                    "diversity_penalty": round(diversity_penalty, 4)
                }
            }
        }
        
        return final_score, metadata
