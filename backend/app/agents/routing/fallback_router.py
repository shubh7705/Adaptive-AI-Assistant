from typing import List
from app.models.registry import ModelRegistry

class FallbackRouter:
    """
    Handles automatic model switching if the primary model fails 
    (e.g., API timeout, bad evaluation score).
    """
    
    @staticmethod
    def get_fallback_model(failed_model_id: str, available_models: List[ModelRegistry]) -> ModelRegistry:
        """
        Selects the next best model from the available pool, excluding the one that failed.
        """
        # Filter out the model that just failed
        fallback_pool = [m for m in available_models if str(m.id) != failed_model_id]
        
        if not fallback_pool:
            raise ValueError("No fallback models available. All models exhausted.")
            
        # In a real scenario, we might re-run the Model Selection Agent's scoring algorithm 
        # on the remaining pool. For now, we pick the most reliable/powerful remaining model 
        # as a safe fallback to ensure the request succeeds.
        
        # Sort by cost (proxy for capability) descending as a safe fallback mechanism
        fallback_pool.sort(key=lambda x: x.cost_per_1k_tokens, reverse=True)
        
        return fallback_pool[0]
