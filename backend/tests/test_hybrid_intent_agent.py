import pytest
from unittest.mock import patch, MagicMock
from app.agents.intent.agent import IntentAgent
from app.config.settings import settings
from app.schemas.intent import IntentClassification


@pytest.fixture(scope="module")
def intent_agent():
    return IntentAgent()


@pytest.mark.asyncio
async def test_laya_high_confidence_direct_route(intent_agent):
    """
    When Laya returns confidence >= LAYA_CONFIDENCE_THRESHOLD,
    IntentAgent should directly return Laya's classification.
    """
    mock_laya_result = {
        "task": "coding",
        "confidence": 0.95,
        "complexity": "high",
        "requires_tools": False,
        "raw": {}
    }

    mock_service = MagicMock()
    mock_service.is_available = True
    mock_service.predict.return_value = mock_laya_result

    with patch.object(intent_agent, "_laya_service", mock_service):
        result = await intent_agent.execute("Write a Python script to sort a list")

        assert isinstance(result, IntentClassification)
        assert result.task == "coding"
        assert result.confidence == 0.95
        assert result.complexity == "high"
        assert result.requires_tools is False
        assert result.recommended_tier == "powerful"
        assert "Laya System 1 classified query as 'coding'" in result.rationale


@pytest.mark.asyncio
async def test_laya_low_confidence_fallback_to_chroma(intent_agent):
    """
    When Laya returns confidence < LAYA_CONFIDENCE_THRESHOLD,
    IntentAgent must fall back to ChromaDB anchor search.
    """
    # Confidence 0.55 is below default threshold 0.70
    mock_laya_result = {
        "task": "tool_usage",
        "confidence": 0.55,
        "complexity": "low",
        "requires_tools": False,
        "raw": {}
    }

    mock_service = MagicMock()
    mock_service.is_available = True
    mock_service.predict.return_value = mock_laya_result

    with patch.object(intent_agent, "_laya_service", mock_service):
        result = await intent_agent.execute("Search the web for the latest news")

        assert isinstance(result, IntentClassification)
        assert result.task == "tool_usage"
        assert "[Fallback: ChromaDB]" in result.rationale
        assert "Laya confidence 0.55 < threshold" in result.rationale


@pytest.mark.asyncio
async def test_laya_unknown_fallback_to_chroma(intent_agent):
    """
    When Laya returns 'unknown', IntentAgent must fall back to ChromaDB.
    """
    mock_laya_result = {
        "task": "unknown",
        "confidence": 0.85,
        "complexity": "low",
        "requires_tools": False,
        "raw": {}
    }

    mock_service = MagicMock()
    mock_service.is_available = True
    mock_service.predict.return_value = mock_laya_result

    with patch.object(intent_agent, "_laya_service", mock_service):
        result = await intent_agent.execute("Search the web for NVIDIA stock price today")

        assert isinstance(result, IntentClassification)
        assert "[Fallback: ChromaDB]" in result.rationale
        assert "Reason: Laya returned 'unknown'" in result.rationale


@pytest.mark.asyncio
async def test_laya_error_graceful_fallback(intent_agent):
    """
    If Laya inference raises an exception, the system should catch it and
    transparently fall back to ChromaDB without failing the user's request.
    """
    mock_service = MagicMock()
    mock_service.is_available = True
    mock_service.predict.side_effect = RuntimeError("Laya tensor CUDA OOM")

    with patch.object(intent_agent, "_laya_service", mock_service):
        result = await intent_agent.execute("Write a query to join these two tables")

        assert isinstance(result, IntentClassification)
        assert result.task == "sql"
        assert "[Fallback: ChromaDB]" in result.rationale
        assert "Laya error" in result.rationale


@pytest.mark.asyncio
async def test_laya_disabled_setting(intent_agent):
    """
    When LAYA_ENABLED is False, queries route directly through ChromaDB.
    """
    with patch.object(settings, "LAYA_ENABLED", False):
        result = await intent_agent.execute("Write a query to join these two tables")

        assert isinstance(result, IntentClassification)
        assert result.task == "sql"
        assert "[Fallback: ChromaDB]" not in result.rationale
        assert "semantic anchor voting" in result.rationale


@pytest.mark.asyncio
async def test_real_hybrid_classification(intent_agent):
    """
    End-to-end integration test with real models loaded.
    Verifies that real queries route through Laya when confident.
    """
    result = await intent_agent.execute("Write a Python function to compute Fibonacci numbers")

    assert isinstance(result, IntentClassification)
    assert result.task in ("coding", "programming")
    assert result.recommended_tier == "powerful"
    assert result.confidence >= 0.70
    assert "Laya System 1" in result.rationale
