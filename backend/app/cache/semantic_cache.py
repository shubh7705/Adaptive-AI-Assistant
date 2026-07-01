from langchain_community.cache import RedisSemanticCache
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.globals import set_llm_cache
from app.config.settings import settings

class SemanticCacheManager:
    """
    Manages semantic caching for LLM responses using Redis Vector Search.
    Identical or highly similar queries will hit the cache instead of the LLM.
    """
    def __init__(self, score_threshold: float = 0.90):
        self.redis_url = settings.REDIS_URL
        self.score_threshold = score_threshold
        
        # We use Google's embedding model for fast, high-quality vectorization
        api_key = settings.GOOGLE_API_KEY
        if api_key:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key
            )
        else:
            self.embeddings = None

    def initialize_cache(self):
        """
        Injects the semantic cache into LangChain's global caching mechanism.
        """
        if not self.embeddings:
            print("Warning: GOOGLE_API_KEY not set. Semantic cache disabled.")
            return

        try:
            # We attempt to connect to Redis. If it fails, we catch it so the app remains runnable.
            # RedisSemanticCache requires Redis with the RediSearch module installed.
            set_llm_cache(
                RedisSemanticCache(
                    redis_url=self.redis_url,
                    embedding=self.embeddings,
                    score_threshold=self.score_threshold
                )
            )
            print("Semantic Cache initialized successfully.")
        except Exception as e:
            print(f"Warning: Failed to initialize Semantic Cache. Ensure Redis with RediSearch is running. Error: {e}")

    # For manual caching outside of LangChain globals:
    async def check_cache(self, query: str) -> str | None:
        """
        Manually checks the cache for a given query (useful if not using standard Langchain LLMs).
        """
        # In a custom implementation, you would vectorize the query and run a Redis KNN search here.
        # LangChain's global cache handles this automatically for .invoke() calls.
        pass
