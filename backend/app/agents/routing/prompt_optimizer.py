from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.optimization import PromptOptimization
from app.config.settings import settings

class PromptOptimizationAgent:
    """
    Agent responsible for rewriting and optimizing user prompts before sending
    them to the heavier LLMs. This helps maximize generation quality.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in configuration")
            
        self.llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        self.structured_llm = self.llm.with_structured_output(PromptOptimization)
        
        self.system_prompt = SystemMessage(content="""You are an expert Prompt Engineer.
Your task is to take a user's raw prompt and rewrite it to be optimal for an LLM.

Guidelines for optimization:
1. Fix any grammar or spelling errors.
2. Expand vague instructions (e.g., if they ask for "python dfs", rewrite it to "Write an optimized Depth-First Search (DFS) implementation in Python. Include time and space complexity explanations, and provide clear usage examples.")
3. Do NOT change the user's original goal or intent.
4. Add structural constraints if needed (e.g., asking for markdown formatting, clear headings).

Return your optimized prompt and a list of changes you made.
""")

    async def execute(self, original_prompt: str) -> PromptOptimization:
        """
        Takes the original raw string and returns a structured PromptOptimization object.
        """
        # If the prompt is already very long, we might not want to touch it to avoid messing up context.
        # But for this implementation, we try to optimize it.
        messages = [
            self.system_prompt,
            HumanMessage(content=original_prompt)
        ]
        
        result = await self.structured_llm.ainvoke(messages)
        return result
