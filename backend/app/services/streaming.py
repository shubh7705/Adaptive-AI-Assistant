import json
import asyncio
from typing import AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.config.settings import settings

class StreamingService:
    """
    Handles streaming generation of tokens from LLMs back to the FastAPI client.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.api_key = settings.GOOGLE_API_KEY
        
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name, 
                api_key=self.api_key,
                streaming=True
            )
        else:
            self.llm = None

    async def stream_chat(self, query: str) -> AsyncGenerator[str, None]:
        """
        Yields tokens as Server-Sent Events (SSE).
        """
        if not self.llm:
            # Fallback mock streaming if API key is missing
            mock_response = f"I am simulating a streaming response for your query: '{query}'. Please configure your API key in the .env file."
            for word in mock_response.split():
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                await asyncio.sleep(0.05)
            yield "data: [DONE]\n\n"
            return

        messages = [HumanMessage(content=query)]
        
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    # Yield in standard SSE format
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                    
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
