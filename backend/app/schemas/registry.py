from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

class ModelRegistryBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    provider: Literal["google", "groq", "openrouter"]
    description: Optional[str] = Field(default=None, max_length=2_000)
    cost_per_1k_tokens: float = Field(default=0.0, ge=0)
    supports_streaming: bool = False
    supports_vision: bool = False
    supports_tools: bool = False
    supports_function_calling: bool = False
    supports_json_mode: bool = False
    context_window: int = Field(default=8192, gt=0)
    max_output_tokens: int = Field(default=4096, gt=0)
    is_active: bool = True

    @field_validator(
        "supports_streaming",
        "supports_vision",
        "supports_tools",
        "supports_function_calling",
        "supports_json_mode",
        "is_active",
        mode="before",
    )
    @classmethod
    def default_bool(cls, value):
        return bool(value) if value is not None else False

    @field_validator("context_window", mode="before")
    @classmethod
    def default_context_window(cls, value):
        return int(value) if value is not None else 8192

    @field_validator("max_output_tokens", mode="before")
    @classmethod
    def default_max_output_tokens(cls, value):
        return int(value) if value is not None else 4096

    @field_validator("cost_per_1k_tokens", mode="before")
    @classmethod
    def default_cost(cls, value):
        return float(value) if value is not None else 0.0

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Model name cannot be blank")
        return value

class ModelRegistryCreate(ModelRegistryBase):
    pass

class ModelRegistryResponse(ModelRegistryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
