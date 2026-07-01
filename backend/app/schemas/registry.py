from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ModelRegistryBase(BaseModel):
    name: str
    provider: str
    description: Optional[str] = None
    cost_per_1k_tokens: float = 0.0
    supports_streaming: bool = False
    supports_vision: bool = False
    supports_tools: bool = False
    is_active: bool = True

class ModelRegistryCreate(ModelRegistryBase):
    pass

class ModelRegistryResponse(ModelRegistryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
