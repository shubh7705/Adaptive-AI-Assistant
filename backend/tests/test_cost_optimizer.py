import pytest
from app.agents.routing.cost_optimizer import CostOptimizationAgent
from app.schemas.intent import IntentClassification

@pytest.fixture
def cost_agent():
    return CostOptimizationAgent()

def test_cost_optimizer_simple_prompt(cost_agent):
    """
    Tests that a short, simple prompt with low complexity is routed to the 'tiny' tier.
    """
    prompt = "What is 2 + 2?"
    intent = IntentClassification(
        task="math",
        confidence=0.99,
        complexity="low",
        requires_tools=False
    )
    
    result = cost_agent.execute(prompt, intent)
    
    assert result.recommended_tier == "tiny"
    assert result.max_budget_usd == 0.001
    assert result.estimated_tokens < 20

def test_cost_optimizer_complex_prompt(cost_agent):
    """
    Tests that a high complexity prompt is escalated to the 'powerful' tier.
    """
    prompt = "Design a highly scalable microservice architecture for a global banking system."
    intent = IntentClassification(
        task="reasoning",
        confidence=0.95,
        complexity="high",
        requires_tools=False
    )
    
    result = cost_agent.execute(prompt, intent)
    
    assert result.recommended_tier == "powerful"
    assert result.max_budget_usd == 0.10
