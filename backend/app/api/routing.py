from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database.session import get_db
from app.schemas.intent import IntentClassification
from app.schemas.cost import CostOptimization
from app.schemas.selection import ModelSelection
from app.agents.routing.model_selector import ModelSelectionAgent

router = APIRouter()

class RoutingExplainRequest(BaseModel):
    intent: IntentClassification
    cost: CostOptimization

@router.post("/explain", response_model=ModelSelection)
async def explain_routing(
    request: RoutingExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Dry-run endpoint for the routing engine. 
    Passes an intent and budget through the transparent routing waterfall
    and returns a trace of how each model was scored, ranked, or dropped.
    """
    model_selector = ModelSelectionAgent()
    selection = await model_selector.execute(
        db=db, 
        intent_data=request.intent, 
        cost_data=request.cost
    )
    return selection
