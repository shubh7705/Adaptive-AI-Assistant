from dataclasses import dataclass
from app.schemas.intent import IntentType

@dataclass
class RoutingWeights:
    coding: float = 0.1
    reasoning: float = 0.2
    math: float = 0.1
    vision: float = 0.1
    creative: float = 0.1
    latency: float = 0.2
    cost: float = 0.2

class DynamicWeightGenerator:
    """
    Stage 3: Generates scoring weights dynamically based on the detected intent.
    """
    
    @staticmethod
    def get_weights(intent_task: IntentType) -> RoutingWeights:
        if intent_task in ("coding", "programming", "sql"):
            return RoutingWeights(coding=0.45, reasoning=0.25, latency=0.15, cost=0.15)
            
        elif intent_task == "vision":
            return RoutingWeights(vision=0.50, reasoning=0.20, latency=0.15, cost=0.15)
            
        elif intent_task in ("math", "data_analysis"):
            return RoutingWeights(math=0.50, reasoning=0.30, latency=0.10, cost=0.10)
            
        elif intent_task in ("summarization", "extraction"):
            return RoutingWeights(reasoning=0.30, creative=0.30, latency=0.20, cost=0.20)
            
        elif intent_task == "creative":
            return RoutingWeights(creative=0.60, reasoning=0.10, latency=0.10, cost=0.20)
            
        elif intent_task == "chat":
            return RoutingWeights(creative=0.20, reasoning=0.20, latency=0.40, cost=0.20)
            
        elif intent_task == "reasoning":
            return RoutingWeights(reasoning=0.60, coding=0.10, latency=0.15, cost=0.15)
            
        # Default balanced weights
        return RoutingWeights(reasoning=0.30, creative=0.10, coding=0.10, latency=0.25, cost=0.25)
