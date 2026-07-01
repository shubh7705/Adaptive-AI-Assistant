from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.registry import ModelRegistry
from app.schemas.intent import IntentClassification
from app.schemas.cost import CostOptimization
from app.schemas.selection import ModelSelection

class ModelSelectionAgent:
    """
    Agent responsible for dynamically selecting the best model based on
    intent, required capabilities, and a multi-factor scoring algorithm.
    """
    def __init__(self):
        # We can configure weights for the scoring formula here
        self.w_quality = 0.4
        self.w_latency = 0.3
        self.w_cost = 0.3

    async def execute(
        self, 
        db: AsyncSession, 
        intent_data: IntentClassification, 
        cost_data: CostOptimization
    ) -> ModelSelection:
        
        # 1. Fetch all active models
        result = await db.execute(select(ModelRegistry).where(ModelRegistry.is_active))
        models = result.scalars().all()
        
        if not models:
            raise ValueError("No active models found in the registry!")

        best_model = None
        highest_score = -float('inf')
        
        # 2. Hard requirements filtering
        eligible_models = []
        for m in models:
            # Check constraints (e.g., if intent requires tools, model MUST support tools)
            if intent_data.requires_tools and not m.supports_tools:
                continue
            if intent_data.task == "vision" and not m.supports_vision:
                continue
            # Budget constraint
            if m.cost_per_1k_tokens > cost_data.max_budget_usd:
                continue
            
            eligible_models.append(m)
            
        # If strict filtering removes all models, fallback to the entire list to prevent total failure
        if not eligible_models:
            eligible_models = models

        # 3. Scoring Algorithm
        # Score = (Quality) - (Latency Penalty) - (Cost Penalty) + Availability
        # For this prototype, we simulate latency/quality from the Tier requirement and Cost
        
        for m in eligible_models:
            score = 0.0
            
            # Quality approximation (In production, this comes from Benchmarks table)
            quality = 0.8
            if cost_data.recommended_tier == "powerful":
                # Favor models with higher cost (proxy for power) if powerful tier is needed
                quality += min(m.cost_per_1k_tokens * 10, 0.2) 
            elif cost_data.recommended_tier == "fast":
                quality += 0.1
                
            # Cost Penalty (cheaper is better)
            cost_penalty = m.cost_per_1k_tokens * self.w_cost
            
            # Latency Penalty approximation
            # Usually cheaper models are faster
            latency_penalty = (1.0 if m.cost_per_1k_tokens > 0.01 else 0.2) * self.w_latency
            
            # Availability (Assuming 1.0 if it's active for now)
            availability = 1.0
            
            final_score = (quality * self.w_quality) - latency_penalty - cost_penalty + availability
            
            if final_score > highest_score:
                highest_score = final_score
                best_model = m

        return ModelSelection(
            selected_model_id=best_model.id,
            selected_model_name=best_model.name,
            provider=best_model.provider,
            score=highest_score,
            rationale=f"Selected based on Score {highest_score:.2f} (Quality/Cost tradeoff for {cost_data.recommended_tier} tier)."
        )
