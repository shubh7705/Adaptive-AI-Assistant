import os
import chromadb
from sentence_transformers import SentenceTransformer
from app.schemas.intent import IntentClassification
from app.config.logger import logger

# Static Metadata Map for Semantic Categories
INTENT_METADATA_MAP = {
    "coding": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "math": {"complexity": "high", "requires_tools": True, "recommended_tier": "powerful"},
    "translation": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    "creative": {"complexity": "medium", "requires_tools": False, "recommended_tier": "fast"},
    "summarization": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    "chat": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    "rag": {"complexity": "medium", "requires_tools": True, "recommended_tier": "powerful"},
    "tool_usage": {"complexity": "high", "requires_tools": True, "recommended_tier": "powerful"},
    "programming": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "sql": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "data_analysis": {"complexity": "high", "requires_tools": True, "recommended_tier": "powerful"},
    "reasoning": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "question_answering": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
}

# Pre-defined semantic anchors
ANCHORS = [
    {"text": "Write a python script to reverse a string", "task": "coding"},
    {"text": "How do I fix this React component bug?", "task": "coding"},
    {"text": "Optimize this SQL query for PostgreSQL", "task": "sql"},
    {"text": "What is 250 multiplied by 44?", "task": "math"},
    {"text": "Solve this differential equation", "task": "math"},
    {"text": "Translate this sentence to French", "task": "translation"},
    {"text": "Write a poem about the moon", "task": "creative"},
    {"text": "Summarize this article in 3 bullet points", "task": "summarization"},
    {"text": "Hello, how are you?", "task": "chat"},
    {"text": "What is your name?", "task": "chat"},
    {"text": "Search the web for the latest news", "task": "tool_usage"},
    {"text": "Based on the provided document, what is the policy?", "task": "rag"},
    {"text": "Analyze this CSV dataset and tell me the mean", "task": "data_analysis"},
    {"text": "If John has 5 apples and gives 2 away, how many does he have?", "task": "reasoning"},
    {"text": "What is the capital of France?", "task": "question_answering"},
]

class IntentAgent:
    """
    Agent responsible for analyzing the intent, complexity, and tool requirements 
    of a user query. Designed to be blazing fast using Semantic Anchor Search (ChromaDB).
    """
    _instance = None
    _chroma_client = None
    _collection = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IntentAgent, cls).__new__(cls)
            cls._instance._initialize_chroma()
        return cls._instance

    def _initialize_chroma(self):
        logger.info("Initializing Semantic Anchor Search (ChromaDB)...")
        # Initialize embedding model locally
        self._model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ephemeral in-memory ChromaDB client
        self._chroma_client = chromadb.Client()
        self._collection = self._chroma_client.create_collection(name="intent_anchors")
        
        # Seed the collection
        texts = [a["text"] for a in ANCHORS]
        tasks = [{"task": a["task"]} for a in ANCHORS]
        ids = [f"anchor_{i}" for i in range(len(ANCHORS))]
        
        # Compute embeddings locally
        embeddings = self._model.encode(texts).tolist()
        
        self._collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=tasks,
            ids=ids
        )
        logger.info("Semantic Anchor Search initialized successfully.")

    async def execute(self, query: str) -> IntentClassification:
        try:
            # Vectorize the incoming query
            query_embedding = self._model.encode([query]).tolist()
            
            # Query the DB for the nearest neighbor
            results = self._collection.query(
                query_embeddings=query_embedding,
                n_results=1
            )
            
            # Extract the best match
            best_match_meta = results['metadatas'][0][0]
            distance = results['distances'][0][0]
            
            matched_task = best_match_meta["task"]
            
            # Convert L2 distance to a mock confidence score (0.0 to 1.0)
            # Distance 0.0 means perfect match (1.0 confidence)
            confidence = max(0.0, 1.0 - distance)
            
            # Look up predetermined metadata
            metadata = INTENT_METADATA_MAP.get(matched_task, {
                "complexity": "medium", 
                "requires_tools": False, 
                "recommended_tier": "powerful"
            })
            
            rationale = f"Semantic Anchor Search matched query to '{matched_task}' with distance {distance:.2f}."
            
            return IntentClassification(
                task=matched_task,
                confidence=confidence,
                complexity=metadata["complexity"],
                requires_tools=metadata["requires_tools"],
                recommended_tier=metadata["recommended_tier"],
                rationale=rationale
            )
            
        except Exception as e:
            logger.error(f"Semantic Anchor Search failed: {e}")
            raise ValueError(f"Failed to execute semantic intent detection: {e}")
