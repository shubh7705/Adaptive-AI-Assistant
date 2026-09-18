import hashlib
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.services.streaming import StreamingService
from app.config.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal, get_db
from app.agents.intent.agent import IntentAgent
from app.agents.routing.model_selector import ModelSelectionAgent
from app.agents.routing.cost_optimizer import CostOptimizationAgent
from app.events.outcome_publisher import publish_outcome_event
from app.models.analytics import RoutingLog
from app.schemas.cost import CostOptimization

router = APIRouter()

from typing import Optional
from sqlalchemy.future import select
from app.models.registry import ModelRegistry

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="The user query")
    session_id: str = Field(
        default="default_session",
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
        description="Session identifier",
    )
    manual_model_id: Optional[str] = None

@router.post("/stream")
async def stream_chat_endpoint(
    request: ChatRequest,
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
    routing_log_id: Optional[str] = None
    intent_task = "chat"
    intent_complexity = "low"
    # Manual routing does not need classification, but telemetry still needs a safe fallback estimate.
    cost_data = CostOptimization(
        estimated_tokens=0,
        recommended_tier="fast",
        max_budget_usd=0.01,
        rationale="Manual-routing fallback estimate.",
    )
    
    runner_ups = []
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
        # 1. Analyze intent before choosing a cost/quality tier.
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
                requires_tools=False,
                recommended_tier="fast",
                rationale="Fallback default due to analysis failure."
            )
            
        intent_task = intent_data.task
        intent_complexity = intent_data.complexity
    
        # 2. Use the dedicated optimizer so routing, budget, and tests agree.
        try:
            cost_data = CostOptimizationAgent().execute(request.query, intent_data)
        except Exception as e:
            logger.warning(f"Cost optimization failed: {e}. Using conservative fallback.")
            cost_data = CostOptimization(
                estimated_tokens=500,
                recommended_tier=intent_data.recommended_tier,
                max_budget_usd=0.01,
                rationale="Fallback budget due to tokenization failure.",
            )
        logger.info(
            f"DYNAMIC TIER SELECTED: {cost_data.recommended_tier} "
            f"(Estimated Tokens: {cost_data.estimated_tokens})"
        )
    
        # 3. Dynamically Select Best Model
        model_selector = ModelSelectionAgent()
        try:
            selection = await model_selector.execute(db, intent_data, cost_data)
            model_name = selection.selected_model_name
            provider = selection.provider
            model_id = selection.selected_model_id
            runner_ups = selection.runner_ups or []
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
        new_log = RoutingLog(
            model_id=model_id,
            intent_detected=intent_task,
            complexity_score=intent_complexity,
            total_tokens=0,
            latency_ms=0.0,
            estimated_cost=0.0
        )
        db.add(new_log)
        await db.commit()
        routing_log_id = new_log.id

    user_email = "anonymous"

    # 4. Stream response using the selected model and finalize telemetry afterwards.
    streamer = StreamingService(model_name=model_name, provider=provider)

    async def instrumented_stream():
        started_at = time.perf_counter()
        output_tokens = 0
        failed = False
        used_fallback = False
        completed = False
        try:
            async for event in streamer.stream_chat(
                query=request.query,
                session_id=request.session_id,
                user_id=user_email,
                fallback_candidates=runner_ups,
            ):
                if event.startswith("data: "):
                    payload = event[6:].strip()
                    if payload == "[DONE]":
                        completed = True
                    else:
                        try:
                            parsed = json.loads(payload)
                            token = parsed.get("token", "")
                            if token:
                                # A provider-neutral estimate; provider usage metadata can replace it later.
                                output_tokens += len(token.split())
                            failed = failed or bool(parsed.get("error"))
                            used_fallback = used_fallback or bool(parsed.get("fallback"))
                        except json.JSONDecodeError:
                            logger.warning("Ignoring malformed SSE event while collecting telemetry")
                yield event
        except Exception:
            failed = True
            raise
        finally:
            latency_ms = (time.perf_counter() - started_at) * 1000
            success = completed and not failed
            total_tokens = cost_data.estimated_tokens + output_tokens
            # A model can disappear between selection and streaming; telemetry must not break the response.
            try:
                async with AsyncSessionLocal() as telemetry_db:
                    if model_id:
                        result = await telemetry_db.execute(
                            select(ModelRegistry.cost_per_1k_tokens).where(ModelRegistry.id == model_id)
                        )
                        model_cost = result.scalar_one_or_none() or 0.0
                        estimated_cost = (total_tokens / 1000) * model_cost
                        log = await telemetry_db.get(RoutingLog, routing_log_id) if routing_log_id else None
                        if log:
                            log.total_tokens = total_tokens
                            log.latency_ms = latency_ms
                            log.estimated_cost = estimated_cost
                            log.is_fallback = used_fallback
                            await telemetry_db.commit()
                        await publish_outcome_event(
                            model_id=str(model_id),
                            task_type=intent_task,
                            latency_ms=latency_ms,
                            success=success,
                            tokens_per_sec=(output_tokens / (latency_ms / 1000)) if latency_ms else 0.0,
                            cost=estimated_cost,
                        )
            except Exception as exc:
                logger.warning(f"Failed to finalize routing telemetry: {exc}")
    
    return StreamingResponse(
        instrumented_stream(),
        media_type="text/event-stream"
    )
