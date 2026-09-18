import pytest
from app.tools.python_executor import python_executor
from app.memory.redis_store import RedisMemoryStore
from app.agents.routing.cost_optimizer import CostOptimizationAgent
from app.schemas.intent import IntentClassification

def test_python_executor_safe_math():
    result = python_executor.invoke({"code": "2 + 3 * 4"})
    assert result == "14"

    result_pow = python_executor.invoke({"code": "2 ** 8"})
    assert result_pow == "256"

def test_python_executor_blocks_malicious_code():
    result = python_executor.invoke({"code": "__import__('os').system('echo pwned')"})
    assert "Execution Error" in result

    result_open = python_executor.invoke({"code": "open('test.txt', 'w')"})
    assert "Execution Error" in result

@pytest.mark.asyncio
async def test_memory_store_user_isolation():
    store = RedisMemoryStore()
    
    # User 1 message in session "s1"
    await store.add_message("s1", {"role": "user", "content": "Secret User 1"}, user_id="user1@example.com")
    
    # User 2 message in same session name "s1"
    await store.add_message("s1", {"role": "user", "content": "Secret User 2"}, user_id="user2@example.com")
    
    hist1 = await store.get_history("s1", user_id="user1@example.com")
    hist2 = await store.get_history("s1", user_id="user2@example.com")
    
    assert len(hist1) >= 1
    assert len(hist2) >= 1
    assert hist1[-1]["content"] == "Secret User 1"
    assert hist2[-1]["content"] == "Secret User 2"

def test_cost_optimizer_budget_and_tier():
    optimizer = CostOptimizationAgent()
    
    intent_complex = IntentClassification(
        task="coding",
        confidence=0.9,
        complexity="high",
        requires_tools=True,
        recommended_tier="powerful"
    )
    cost_res = optimizer.execute("Implement quicksort in Python", intent_complex)
    assert cost_res.recommended_tier == "powerful"
    assert cost_res.max_budget_usd >= 0.05

    intent_simple = IntentClassification(
        task="chat",
        confidence=0.9,
        complexity="low",
        requires_tools=False,
        recommended_tier="fast"
    )
    cost_simple = optimizer.execute("hi", intent_simple)
    assert cost_simple.recommended_tier in ("tiny", "fast")
    assert cost_simple.max_budget_usd <= 0.01
