from pydantic import BaseModel, Field
from typing import Literal

# Tiers corresponding to model classes (e.g. tiny=Qwen-1.5B, fast=GPT-4o-mini, powerful=DeepSeek-V3)
ModelTier = Literal["tiny", "fast", "powerful"]

class CostOptimization(BaseModel):
    estimated_tokens: int = Field(
        ...,
        description="The estimated number of input tokens based on local tokenization."
    )
    recommended_tier: ModelTier = Field(
        ...,
        description="The recommended model tier to fulfill this request efficiently."
    )
    max_budget_usd: float = Field(
        ...,
        description="The maximum allowed budget in USD for this query."
    )
    rationale: str = Field(
        ...,
        description="A brief explanation of why this tier and budget were chosen."
    )
