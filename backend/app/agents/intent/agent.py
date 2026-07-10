import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.intent import IntentClassification
from app.config.settings import settings

class IntentAgent:
    """
    Agent responsible for analyzing the intent, complexity, and tool requirements 
    of a user query. Designed to be fast and cheap using Gemini Flash.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in configuration")
            
        # Using a fast, cheap model for routing logic
        self.llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        
        self.system_prompt = SystemMessage(content="""You are the master routing intelligence of the ModelRouter AI system.
Your goal is to analyze the user's query and classify it precisely.

Determine the primary intent category (task). Must be one of:
'coding', 'math', 'translation', 'creative', 'summarization', 'chat', 'rag', 'vision', 'ocr', 'tool_usage', 'programming', 'sql', 'data_analysis', 'reasoning', 'classification', 'extraction', 'question_answering', 'unknown'

Estimate the complexity. Must be one of: 'low', 'medium', 'high'.
Determine if it strictly requires external tools (boolean).
Assign a confidence score between 0.0 and 1.0.

CRITICAL NEW STEP: Based on the complexity and the semantic nature of the task, output a "recommended_tier". 
- Use "fast" for basic chat, greeting, summarization, translation, extraction, etc.
- Use "powerful" for ANY coding, sql, math, programming, heavy reasoning, or if requires_tools is true.
Provide a clear "rationale" explaining why this tier was selected based on the task and complexity.

Return ONLY a raw JSON object with NO markdown formatting, strictly matching this schema:
{
  "task": "...",
  "confidence": 0.95,
  "complexity": "medium",
  "requires_tools": false,
  "recommended_tier": "fast",
  "rationale": "The user is asking a basic question that does not require heavy reasoning."
}
""")

    async def execute(self, query: str) -> IntentClassification:
        messages = [
            self.system_prompt,
            HumanMessage(content=query)
        ]
        
        result = await self.llm.ainvoke(messages)
        
        try:
            # Strip potential markdown formatting from the response
            clean_json = result.content.strip().strip('```json').strip('```').strip()
            parsed_data = json.loads(clean_json)
            return IntentClassification(**parsed_data)
        except Exception as e:
            # Fallback if the LLM refuses to return valid JSON
            raise ValueError(f"Failed to parse LLM intent response: {e}. Raw content: {result.content}")
