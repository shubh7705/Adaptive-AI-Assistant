from typing import List
from app.models.registry import ModelRegistry
from app.schemas.intent import IntentClassification

class CapabilityFilter:
    """
    Stage 1: Filters models based on hard constraints from the required intent.
    If no model satisfies all constraints, relaxes the least important constraints gracefully.
    """
    
    @staticmethod
    def filter(models: List[ModelRegistry], intent: IntentClassification, budget: float = 100.0) -> List[ModelRegistry]:
        eligible = []
        
        # Primary strict filtering
        for m in models:
            if not m.is_active:
                continue
            if intent.requires_tools and not m.supports_tools:
                continue
            if intent.task == "vision" and not m.supports_vision:
                continue
            if m.cost_per_1k_tokens > budget:
                continue
            
            eligible.append(m)
            
        if eligible:
            return eligible
            
        # Relaxation 1: Drop budget requirement
        relaxed_eligible_budget = [m for m in models if m.is_active and (not intent.requires_tools or m.supports_tools) and (intent.task != "vision" or m.supports_vision)]
        if relaxed_eligible_budget:
            return relaxed_eligible_budget
            
        # Relaxation 2: Drop tools and budget requirement
        if intent.requires_tools:
            relaxed_eligible_tools = [m for m in models if m.is_active and (intent.task != "vision" or m.supports_vision)]
            if relaxed_eligible_tools:
                return relaxed_eligible_tools
                
        # Ultimate fallback: return all active models
        return [m for m in models if m.is_active]
