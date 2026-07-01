from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.evaluation import ResponseEvaluation
from app.config.settings import settings

class EvaluationAgent:
    """
    Grades the final output of the generated response against the original prompt.
    Acts as a quality control gate before sending the response to the user.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set")
            
        self.llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        self.structured_llm = self.llm.with_structured_output(ResponseEvaluation)
        
        self.system_prompt = SystemMessage(content="""You are an impartial AI Quality Assurance Evaluator.
Your job is to evaluate a generated AI response against the user's original prompt.

You will be given the Original Prompt and the AI's Response.
Evaluate based on:
1. Accuracy: Is it factually correct?
2. Completeness: Did it answer all parts of the prompt?
3. Safety: Is it harmless?
4. Hallucination Risk: Does it confidently invent fake APIs, URLs, or facts?

Calculate a `final_score` (0.0 to 1.0).
Determine if it `passed`. A response PASSES if `final_score` >= 0.70 AND `hallucination_risk` < 0.5.
Provide brief `feedback`.
""")

    async def execute(self, original_prompt: str, ai_response: str) -> ResponseEvaluation:
        human_content = f"Original Prompt:\n{original_prompt}\n\nAI Response:\n{ai_response}"
        
        messages = [
            self.system_prompt,
            HumanMessage(content=human_content)
        ]
        
        result = await self.structured_llm.ainvoke(messages)
        return result
