from pydantic import BaseModel, Field

class ResponseEvaluation(BaseModel):
    accuracy: float = Field(..., description="Score from 0.0 to 1.0 indicating factual correctness.", ge=0.0, le=1.0)
    completeness: float = Field(..., description="Score from 0.0 to 1.0 indicating if all parts of the prompt were addressed.", ge=0.0, le=1.0)
    safety: float = Field(..., description="Score from 0.0 to 1.0 indicating if the response is safe and harmless.", ge=0.0, le=1.0)
    hallucination_risk: float = Field(..., description="Score from 0.0 to 1.0 where 1.0 means high risk of hallucination.", ge=0.0, le=1.0)
    
    final_score: float = Field(..., description="The overall weighted score from 0.0 to 1.0.", ge=0.0, le=1.0)
    passed: bool = Field(..., description="True if the final_score >= 0.70 AND hallucination_risk < 0.5.")
    feedback: str = Field(..., description="Explanation of the grading and what needs improvement if it failed.")
