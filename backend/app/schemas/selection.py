from pydantic import BaseModel, Field
from typing import Dict, Any, List

class ModelSelection(BaseModel):
    selected_model_id: str
    selected_model_name: str
    provider: str
    score: float
    rationale: str
    runner_ups: List[Dict[str, Any]] = Field(default_factory=list)
    routing_metadata: Dict[str, Any] = Field(default_factory=dict)
