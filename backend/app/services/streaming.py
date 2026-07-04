import json
import asyncio
from typing import AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config.settings import settings
from app.memory.redis_store import RedisMemoryStore

from langchain_openai import ChatOpenAI

class StreamingService:
    """
    Handles streaming generation of tokens from LLMs back to the FastAPI client.
    """
    def __init__(self, model_name: str, provider: str):
        self.model_name = model_name
        self.provider = provider.lower()
        self.memory_store = RedisMemoryStore()
        
        if self.provider == "google":
            self.api_key = settings.GOOGLE_API_KEY
            if self.api_key:
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model_name, 
                    api_key=self.api_key,
                    streaming=True
                )
            else:
                self.llm = None
        elif self.provider == "openrouter":
            self.api_key = settings.OPENROUTER_API_KEY
            if self.api_key:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=self.api_key,
                    base_url="https://openrouter.ai/api/v1",
                    streaming=True,
                    max_tokens=2000
                )
            else:
                self.llm = None
        elif self.provider == "groq":
            self.api_key = settings.GROQ_API_KEY
            if self.api_key:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1",
                    streaming=True
                )
            else:
                self.llm = None
        else:
            self.llm = None

    async def stream_chat(self, query: str, session_id: str = "default_session") -> AsyncGenerator[str, None]:
        """
        Yields tokens as Server-Sent Events (SSE) with conversation memory.
        """
        if not self.llm:
            # Fallback mock streaming if API key is missing
            mock_response = f"I am simulating a streaming response for your query: '{query}'. Please configure your API key in the .env file."
            for word in mock_response.split():
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                await asyncio.sleep(0.05)
            yield "data: [DONE]\n\n"
            return

        # 1. Fetch conversational history from Redis (Limit to last 6 messages to prevent TPM errors)
        raw_history = await self.memory_store.get_history(session_id)
        raw_history = raw_history[-6:]
        
        # 2. Format history into LangChain messages
        messages = []
        for msg in raw_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))
                
        # 3. Append the current query
        messages.append(HumanMessage(content=query))
        
        full_response = ""
        
        try:
            # Yield the model being used
            yield f"data: {json.dumps({'model': self.model_name})}\n\n"
            
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    # Yield in standard SSE format
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                    
            # 4. Save the new exchange to Redis memory
            await self.memory_store.add_message(session_id, {"role": "user", "content": query})
            await self.memory_store.add_message(session_id, {"role": "assistant", "content": full_response})
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
