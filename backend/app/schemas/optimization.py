from pydantic import BaseModel, Field

class PromptOptimization(BaseModel):
    optimized_prompt: str = Field(
        ...,
        description="The rewritten, optimized version of the user's prompt."
    )
    changes_made: list[str] = Field(
        ...,
        description="A short list of specific improvements made to the prompt (e.g., 'Fixed grammar', 'Added formatting constraints')."
    )
