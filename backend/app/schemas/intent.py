from pydantic import BaseModel, Field
from typing import Literal

# Using Literal to strictly enforce intent categories based on requirements
IntentType = Literal[
    "coding",
    "math",
    "translation",
    "creative",
    "summarization",
    "chat",
    "rag",
    "vision",
    "ocr",
    "tool_usage",
    "programming",
    "sql",
    "data_analysis",
    "reasoning",
    "classification",
    "extraction",
    "question_answering",
    "unknown"
]

class IntentClassification(BaseModel):
    task: IntentType = Field(
        ...,
        description="The primary intent or task type of the user's query."
    )
    confidence: float = Field(
        ...,
        description="A confidence score between 0.0 and 1.0 representing how certain the model is of this classification.",
        ge=0.0,
        le=1.0
    )
    complexity: Literal["low", "medium", "high"] = Field(
        ...,
        description="The estimated complexity of fulfilling this task."
    )
    requires_tools: bool = Field(
        False,
        description="Whether the user request likely requires external tools (like calculator, search, execution) to answer."
    )
    recommended_tier: Literal["fast", "powerful"] = Field(
        "fast",
        description="The recommended model tier for this query based on its semantic complexity and task type."
    )
    rationale: str = Field(
        "",
        description="The exact reasoning for why this tier was selected."
    )
