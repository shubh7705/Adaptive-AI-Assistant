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

    def _create_llm(self, model_name: str, provider: str):
        provider = provider.lower()
        if provider == "google":
            api_key = settings.GOOGLE_API_KEY
            return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, streaming=True) if api_key else None
        elif provider == "openrouter":
            api_key = settings.OPENROUTER_API_KEY
            return ChatOpenAI(model=model_name, api_key=api_key, base_url="https://openrouter.ai/api/v1", streaming=True, max_tokens=2000) if api_key else None
        elif provider == "groq":
            api_key = settings.GROQ_API_KEY
            return ChatOpenAI(model=model_name, api_key=api_key, base_url="https://api.groq.com/openai/v1", streaming=True) if api_key else None
        return None

    async def stream_chat(
        self,
        query: str,
        session_id: str = "default_session",
        user_id: str = "default_user",
        fallback_candidates: list = None,
    ) -> AsyncGenerator[str, None]:
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
        raw_history = await self.memory_store.get_history(session_id, user_id=user_id)
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
        
        full_response_parts: list[str] = []
        has_emitted_tokens = False
        
        try:
            # Yield the model being used
            yield f"data: {json.dumps({'model': self.model_name})}\n\n"
            
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    has_emitted_tokens = True
                    full_response_parts.append(chunk.content)
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                    
            full_response = "".join(full_response_parts)
            await self.memory_store.add_message(session_id, {"role": "user", "content": query}, user_id=user_id)
            await self.memory_store.add_message(session_id, {"role": "assistant", "content": full_response}, user_id=user_id)
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            from app.config.logger import logger
            logger.error(f"Primary model {self.model_name} failed: {e}. Executing fallback routing...")
            
            # Select fallback target: runner up from candidate pool or default Gemini
            fallback_model_name = "gemini-2.5-flash"
            fallback_provider = "google"
            if fallback_candidates:
                for cand in fallback_candidates:
                    c_name = cand.get("name") or cand.get("model_name")
                    c_prov = cand.get("provider", "google")
                    if c_name and c_name != self.model_name:
                        fallback_model_name = c_name
                        fallback_provider = c_prov
                        break
            
            try:
                # Notify frontend of fallback
                yield f"data: {json.dumps({'fallback': True, 'model': fallback_model_name, 'error': f'Primary model unavailable ({str(e)[:100]}). Switched to {fallback_model_name}.'})}\n\n"
                
                fallback_llm = self._create_llm(fallback_model_name, fallback_provider)
                if not fallback_llm:
                    # Final safety fallback to Gemini if secondary failed to init
                    fallback_model_name = "gemini-2.5-flash"
                    fallback_provider = "google"
                    fallback_llm = self._create_llm(fallback_model_name, fallback_provider)
                
                if not fallback_llm:
                    raise ValueError("No API key available for fallback model initialization.")
                
                # If partial output was already emitted to the user, add a clear separator to avoid token mixing
                if has_emitted_tokens:
                    separator = "\n\n*[Connection interrupted. Resuming with fallback model...]*\n\n"
                    full_response_parts.append(separator)
                    yield f"data: {json.dumps({'token': separator})}\n\n"

                fallback_parts: list[str] = []
                async for chunk in fallback_llm.astream(messages):
                    if chunk.content:
                        fallback_parts.append(chunk.content)
                        yield f"data: {json.dumps({'token': chunk.content})}\n\n"
                
                total_response = "".join(full_response_parts) + "".join(fallback_parts)
                await self.memory_store.add_message(session_id, {"role": "user", "content": query}, user_id=user_id)
                await self.memory_store.add_message(session_id, {"role": "assistant", "content": total_response}, user_id=user_id)
                
                yield "data: [DONE]\n\n"
            except Exception as fallback_e:
                logger.error(f"Fallback model ({fallback_model_name}) failed: {fallback_e}")
                yield f"data: {json.dumps({'error': 'Both primary and fallback models failed. Please try again later.'})}\n\n"
                yield "data: [DONE]\n\n"
