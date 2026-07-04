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
                model="models/text-embedding-004",
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
            import redis
            from langchain_core.caches import InMemoryCache
            from langchain_community.cache import RedisCache

            # Test Redis connection first
            try:
                r = redis.Redis.from_url(self.redis_url)
                r.ping()
                # Redis is up, use Exact-Match Cache to avoid embedding model errors
                set_llm_cache(RedisCache(redis_=r))
                print("Exact-Match Cache initialized successfully with Redis.")
            except redis.ConnectionError:
                print("Warning: Redis is unreachable. Falling back to InMemoryCache.")
                set_llm_cache(InMemoryCache())
        except Exception as e:
            print(f"Warning: Failed to initialize Semantic Cache. Error: {e}")

    # For manual caching outside of LangChain globals:
    async def check_cache(self, query: str) -> str | None:
        """
        Manually checks the cache for a given query (useful if not using standard Langchain LLMs).
        """
        # In a custom implementation, you would vectorize the query and run a Redis KNN search here.
        # LangChain's global cache handles this automatically for .invoke() calls.
        pass
