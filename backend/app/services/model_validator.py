import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config.settings import settings

logger = logging.getLogger(__name__)

async def validate_model_active(model_name: str, provider: str) -> bool:
    """
    Validates if a model is accessible and active by sending a minimal test prompt
    to the respective provider's API.
    
    Raises ValueError if validation fails or API keys are missing.
    Returns True if the model successfully responds.
    """
    provider = provider.lower()
    llm = None
    
    try:
        if provider == "google":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured.")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                api_key=settings.GOOGLE_API_KEY,
                max_tokens=5
            )
            
        elif provider == "openrouter":
            if not settings.OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY is not configured.")
            llm = ChatOpenAI(
                model=model_name,
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                max_tokens=5
            )
            
        elif provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not configured.")
            llm = ChatOpenAI(
                model=model_name,
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
                max_tokens=5
            )
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Send a minimal ping to verify model exists and API key is valid
        logger.info(f"Validating model {model_name} on {provider}...")
        response = await llm.ainvoke("Respond with 'ok'")
        
        if response and response.content:
            logger.info(f"Model {model_name} validation successful.")
            return True
            
        raise ValueError("Model returned empty response.")
        
    except Exception as e:
        logger.error(f"Model validation failed for {model_name} ({provider}): {str(e)}")
        raise ValueError(f"Failed to validate model. Ensure the model name is correct and active. Error: {str(e)}")
