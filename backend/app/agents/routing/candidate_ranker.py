import random
from typing import List, Dict, Any, Tuple
from app.models.registry import ModelRegistry

class CandidateRanker:
    """
    Stage 8: Top-K Candidate Selection and Weighted Randomness
    """
    @staticmethod
    def select_best_model(scored_models: List[Tuple[ModelRegistry, float, Dict[str, Any]]], top_k: int = 3) -> Tuple[ModelRegistry, float, Dict[str, Any], List[Dict]]:
        # Sort by score descending
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_models:
            raise ValueError("No scored models available.")
            
        top_candidates = scored_models[:top_k]
        
        # Extract the highest score
        highest_score = top_candidates[0][1]
        
        # Determine eligible candidates within 5% of the highest score (or at least 0.5 points)
        margin = max(abs(highest_score * 0.05), 0.5)
        
        eligible_for_random = [c for c in top_candidates if (highest_score - c[1]) <= margin]
        
        if len(eligible_for_random) == 1:
            selected = eligible_for_random[0]
            reason = "Clear winner with highest score."
        else:
            # Weighted random selection based on score
            # Shift scores to be positive for weight calculation if they are negative
            min_score = min(c[1] for c in eligible_for_random)
            shift = abs(min_score) + 1 if min_score <= 0 else 0
            
            weights = [(c[1] + shift) for c in eligible_for_random]
            
            selected = random.choices(eligible_for_random, weights=weights, k=1)[0]
            reason = f"Selected via weighted random selection among top {len(eligible_for_random)} tied models."
            
        selected_model, selected_score, selected_meta = selected
        
        runner_ups = [
            {"model_id": c[0].id, "name": c[0].name, "score": c[1]} 
            for c in top_candidates if c[0].id != selected_model.id
        ]
        
        selected_meta["reason"] = reason
        
        return selected_model, selected_score, selected_meta, runner_ups
