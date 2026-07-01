import tiktoken
from app.schemas.cost import CostOptimization, ModelTier
from app.schemas.intent import IntentClassification

class CostOptimizationAgent:
    """
    Agent responsible for estimating tokens and determining the model tier.
    It uses local tokenization (tiktoken) to avoid an extra LLM API roundtrip.
    """
    def __init__(self):
        # We use cl100k_base as a fast generic proxy tokenizer for most modern LLMs (GPT-4, etc.)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def execute(self, prompt: str, intent_data: IntentClassification) -> CostOptimization:
        """
        Calculates estimated tokens locally and uses the intent complexity
        to map the request to a model tier.
        """
        # 1. Estimate tokens
        tokens = self.tokenizer.encode(prompt)
        token_count = len(tokens)
        
        # 2. Determine Tier & Budget based on Rules Engine
        tier: ModelTier = "fast"
        budget = 0.01  # default $0.01
        rationale = ""
        
        complexity = intent_data.complexity
        
        if complexity == "high" or token_count > 2000 or intent_data.requires_tools:
            tier = "powerful"
            budget = 0.10  # Allow up to 10 cents for complex/reasoning/tool tasks
            rationale = f"Assigned 'powerful' tier due to {complexity} complexity or large token count ({token_count})."
        elif complexity == "low" and token_count < 200:
            tier = "tiny"
            budget = 0.001
            rationale = f"Assigned 'tiny' tier because the prompt is simple ({complexity}) and short ({token_count} tokens)."
        else:
            tier = "fast"
            budget = 0.01
            rationale = f"Assigned 'fast' tier as a balanced choice for medium complexity ({token_count} tokens)."
            
        return CostOptimization(
            estimated_tokens=token_count,
            recommended_tier=tier,
            max_budget_usd=budget,
            rationale=rationale
        )
