from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.auth import get_current_user
from app.services.streaming import StreamingService
from app.config.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.agents.intent.agent import IntentAgent
from app.agents.routing.model_selector import ModelSelectionAgent
from app.schemas.cost import CostOptimization

router = APIRouter()

from typing import Optional
from sqlalchemy.future import select
from app.models.registry import ModelRegistry

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default_session"
    manual_model_id: Optional[str] = None

@router.post("/stream")
async def stream_chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts a user query, orchestrates intent/routing (or manual selection), and streams back the LLM response.
    """
    logger.info(f"Received query: {request.query}")
    
    model_name = "gemini-2.5-flash"
    provider = "google"
    
    # 0. Check for Manual Model Selection
    model_id = None
    intent_task = "chat"
    intent_complexity = "low"
    
    if request.manual_model_id:
        logger.info(f"Manual routing requested for model ID: {request.manual_model_id}")
        result = await db.execute(select(ModelRegistry).where(ModelRegistry.id == request.manual_model_id))
        manual_model = result.scalars().first()
        if manual_model:
            model_name = manual_model.name
            provider = manual_model.provider
            model_id = manual_model.id
            logger.info(f"MANUAL SELECTION SUCCESS: {model_name} (provider: {provider})")
        else:
            logger.error(f"Manual model ID not found: {request.manual_model_id}. Falling back to default.")
    else:
        # 1. Analyze Intent
        intent_agent = IntentAgent()
        try:
            intent_data = await intent_agent.execute(request.query)
            logger.info(f"INTENT SUCCESS: {intent_data}")
        except Exception as e:
            logger.error(f"INTENT FAILED: {e}")
            # Fallback intent if analysis fails
            from app.schemas.intent import IntentClassification
            intent_data = IntentClassification(
                task="chat",
                confidence=0.5,
                complexity="low",
                requires_tools=False
            )
            
        intent_task = intent_data.task
        intent_complexity = intent_data.complexity
    
        # 2. Map Intent Complexity to Cost/Tier
        recommended_tier = "fast"
        if intent_data.task in ["coding", "programming", "sql", "math", "reasoning"]:
            recommended_tier = "powerful"
        elif intent_data.complexity == "high":
            recommended_tier = "powerful"
        elif intent_data.complexity == "medium":
            recommended_tier = "powerful" if intent_data.requires_tools else "fast"
            
        cost_data = CostOptimization(
            estimated_tokens=500,  # naive placeholder
            recommended_tier=recommended_tier,
            max_budget_usd=0.05,
            rationale=f"Intent complexity is {intent_data.complexity}."
        )
        logger.info(f"MAPPED TIER: {recommended_tier}")
    
        # 3. Dynamically Select Best Model
        model_selector = ModelSelectionAgent()
        try:
            selection = await model_selector.execute(db, intent_data, cost_data)
            model_name = selection.selected_model_name
            provider = selection.provider
            model_id = selection.selected_model_id
            logger.info(f"MODEL SELECTION SUCCESS: {model_name} (provider: {provider})")
        except Exception as e:
            logger.error(f"MODEL SELECTION FAILED: {e}")
            # Fallback if no models in DB or selection fails
            model_name = "gemini-2.5-flash"
            provider = "google"

    # Save Routing Log
    if not model_id:
        # Fallback query for ID if we defaulted
        result = await db.execute(select(ModelRegistry.id).where(ModelRegistry.name == model_name))
        model_id = result.scalars().first()
        
    if model_id:
        from app.models.analytics import RoutingLog
        new_log = RoutingLog(
            model_id=model_id,
            intent_detected=intent_task,
            complexity_score=intent_complexity,
            total_tokens=150, # Mock average tokens for streaming queries
            latency_ms=250.0, # Mock average latency
            estimated_cost=0.0001
        )
        db.add(new_log)
        await db.commit()

    # Log query and intent to CSV
    import os
    import csv
    try:
        csv_path = "chat_intents.csv"
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['query', 'intent'])
            writer.writerow([request.query, intent_task])
    except Exception as e:
        logger.error(f"Failed to write to CSV: {e}")

    # 4. Stream response using the selected model
    streamer = StreamingService(model_name=model_name, provider=provider)
    
    return StreamingResponse(
        streamer.stream_chat(request.query, request.session_id),
        media_type="text/event-stream"
    )
