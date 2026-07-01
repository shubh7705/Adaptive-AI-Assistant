from pydantic import BaseModel

class ModelSelection(BaseModel):
    selected_model_id: str
    selected_model_name: str
    provider: str
    score: float
    rationale: str
