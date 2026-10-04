import os
import json
import asyncio
import threading
from pathlib import Path
from collections import defaultdict

import chromadb
from sentence_transformers import SentenceTransformer
from app.schemas.intent import IntentClassification
from app.config.logger import logger
from app.config.settings import settings
from app.agents.intent.laya_service import LayaService

# ---------------------------------------------------------------------------
# Static Metadata Map for Semantic Categories
# ---------------------------------------------------------------------------
# NOTE: "coding" and "programming" are effectively the same intent with
# duplicated metadata below. Left both in place since your dataset/anchors
# may already reference both labels, but consider consolidating to one and
# re-tagging the dataset if you control it.
INTENT_METADATA_MAP = {
    "coding": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "programming": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "math": {"complexity": "high", "requires_tools": True, "recommended_tier": "powerful"},
    "translation": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    "creative": {"complexity": "medium", "requires_tools": False, "recommended_tier": "fast"},
    "summarization": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    "chat": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    "rag": {"complexity": "medium", "requires_tools": True, "recommended_tier": "powerful"},
    "tool_usage": {"complexity": "high", "requires_tools": True, "recommended_tier": "powerful"},
    "sql": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "data_analysis": {"complexity": "high", "requires_tools": True, "recommended_tier": "powerful"},
    "reasoning": {"complexity": "high", "requires_tools": False, "recommended_tier": "powerful"},
    "question_answering": {"complexity": "low", "requires_tools": False, "recommended_tier": "fast"},
    # Explicit entry for the low-confidence / out-of-distribution case, so the
    # fallback path in execute() has a real, intentional metadata target
    # instead of silently defaulting to the most expensive tier.
    "unknown": {"complexity": "medium", "requires_tools": False, "recommended_tier": "fast"},
}

# Pre-defined semantic anchors (fallback): used only if the dataset file is
# missing or unreadable. Multiple phrasings per class give a more robust
# centroid than a single example sentence.
FALLBACK_ANCHORS = [
    {"text": "Write a python script to reverse a string", "task": "coding"},
    {"text": "How do I fix this React component bug?", "task": "coding"},
    {"text": "Refactor this function to be more efficient", "task": "coding"},
    {"text": "Optimize this SQL query for PostgreSQL", "task": "sql"},
    {"text": "Write a query to join these two tables", "task": "sql"},
    {"text": "What is 250 multiplied by 44?", "task": "math"},
    {"text": "Solve this differential equation", "task": "math"},
    {"text": "Translate this sentence to French", "task": "translation"},
    {"text": "How do you say 'good morning' in Japanese?", "task": "translation"},
    {"text": "Write a poem about the moon", "task": "creative"},
    {"text": "Come up with a short story about a dragon", "task": "creative"},
    {"text": "Summarize this article in 3 bullet points", "task": "summarization"},
    {"text": "Give me the tl;dr of this document", "task": "summarization"},
    {"text": "Hello, how are you?", "task": "chat"},
    {"text": "What is your name?", "task": "chat"},
    {"text": "Search the web for the latest news", "task": "tool_usage"},
    {"text": "Check my calendar for tomorrow", "task": "tool_usage"},
    {"text": "Based on the provided document, what is the policy?", "task": "rag"},
    {"text": "According to the uploaded file, what were the results?", "task": "rag"},
    {"text": "Analyze this CSV dataset and tell me the mean", "task": "data_analysis"},
    {"text": "Plot a chart of this data and find the trend", "task": "data_analysis"},
    {"text": "If John has 5 apples and gives 2 away, how many does he have?", "task": "reasoning"},
    {"text": "Walk through the logic of this puzzle step by step", "task": "reasoning"},
    {"text": "What is the capital of France?", "task": "question_answering"},
    {"text": "Who wrote the novel Moby Dick?", "task": "question_answering"},
]

# Below this cosine-similarity threshold, the top match is considered too
# uncertain to trust: the agent falls back to "unknown" rather than
# confidently misrouting the query.
CONFIDENCE_THRESHOLD = 0.45
TOP_K = 5


class IntentAgent:
    """
    Agent responsible for analyzing the intent, complexity, and tool requirements
    of a user query.

    Hybrid Architecture:
    1. Primary: Convai Innovations' Laya System 1 non-autoregressive decision model
       for rapid, direct intent classification.
    2. Fallback: ChromaDB persistent vector database with top-k cosine similarity
       anchor voting if Laya confidence is below settings.LAYA_CONFIDENCE_THRESHOLD,
       if Laya returns 'unknown', or if Laya is disabled/encounters an error.
    """
    _instance = None
    _init_lock = threading.Lock()

    _chroma_client = None
    _collection = None
    _model = None
    _laya_service = None

    def __new__(cls):
        # Double-checked locking so concurrent first-callers can't race to
        # build two separate collections/models.
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super(IntentAgent, cls).__new__(cls)
                    cls._instance._initialize_chroma()
                    cls._instance._initialize_laya()
        return cls._instance

    def _initialize_laya(self):
        try:
            self._laya_service = LayaService()
        except Exception as e:
            logger.warning(f"Could not initialize LayaService: {e}. Will rely on ChromaDB anchors.")
            self._laya_service = None

    def _initialize_chroma(self):
        logger.info("Initializing Semantic Anchor Search (ChromaDB)...")
        self._model = SentenceTransformer('all-MiniLM-L6-v2')

        current_dir = Path(__file__).resolve().parent
        backend_root = current_dir.parents[2]
        persist_dir = str(backend_root / "data" / "chroma_intent_db")
        os.makedirs(persist_dir, exist_ok=True)

        dataset_path = backend_root / "dataset" / "intent_classification_dataset.json"

        self._chroma_client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._chroma_client.get_or_create_collection(
            name="intent_anchors",
            metadata={"hnsw:space": "cosine"}
        )

        existing_count = self._collection.count()

        if existing_count == 0:
            logger.info(f"Persistent vector database is empty. Loading dataset from {dataset_path}...")
            dataset = []
            if dataset_path.exists():
                try:
                    with open(dataset_path, "r", encoding="utf-8") as f:
                        dataset = json.load(f)
                    logger.info(f"Loaded {len(dataset)} examples from {dataset_path.name}")
                except Exception as e:
                    logger.exception(f"Error reading dataset file {dataset_path}: {e}")
                    dataset = FALLBACK_ANCHORS
            else:
                logger.warning(f"Dataset not found at {dataset_path}, using fallback anchors.")
                dataset = FALLBACK_ANCHORS

            texts = [a["text"] for a in dataset]
            metadatas = [{"task": a["task"]} for a in dataset]
            ids = [f"anchor_{i}" for i in range(len(dataset))]

            logger.info(f"Generating embeddings for {len(texts)} anchor examples...")
            embeddings = self._model.encode(texts, show_progress_bar=False).tolist()

            batch_size = 500
            for i in range(0, len(texts), batch_size):
                end_i = i + batch_size
                self._collection.add(
                    embeddings=embeddings[i:end_i],
                    documents=texts[i:end_i],
                    metadatas=metadatas[i:end_i],
                    ids=ids[i:end_i]
                )
            logger.info(f"Successfully indexed and persisted {len(texts)} semantic anchors to {persist_dir}.")
        else:
            logger.info(f"ChromaDB persistent vector database loaded instantly with {existing_count} cached embeddings.")

    async def execute(self, query: str) -> IntentClassification:
        """
        Executes intent detection using Laya System 1 model with ChromaDB fallback.
        """
        # --- Stage 1: Try Laya System 1 Decision Model ---
        if settings.LAYA_ENABLED and self._laya_service and self._laya_service.is_available:
            try:
                laya_result = await asyncio.to_thread(self._laya_service.predict, query)
                if laya_result:
                    task = laya_result.get("task", "unknown")
                    confidence = laya_result.get("confidence", 0.0)

                    if task != "unknown" and confidence >= settings.LAYA_CONFIDENCE_THRESHOLD:
                        metadata = INTENT_METADATA_MAP.get(task, INTENT_METADATA_MAP["unknown"])

                        complexity = laya_result.get("complexity")
                        if complexity not in ("low", "medium", "high"):
                            complexity = metadata["complexity"]

                        requires_tools = laya_result.get("requires_tools")
                        if requires_tools is None:
                            requires_tools = metadata["requires_tools"]

                        recommended_tier = metadata["recommended_tier"]
                        if complexity == "high":
                            recommended_tier = "powerful"

                        rationale = (
                            f"Laya System 1 classified query as '{task}' with confidence {confidence:.2f} "
                            f"(threshold: {settings.LAYA_CONFIDENCE_THRESHOLD:.2f})."
                        )

                        return IntentClassification(
                            task=task,
                            confidence=confidence,
                            complexity=complexity,
                            requires_tools=requires_tools,
                            recommended_tier=recommended_tier,
                            rationale=rationale,
                        )
                    else:
                        reason = (
                            f"Laya confidence {confidence:.2f} < threshold {settings.LAYA_CONFIDENCE_THRESHOLD:.2f}"
                            if task != "unknown"
                            else "Laya returned 'unknown'"
                        )
                        logger.info(f"{reason}. Falling back to ChromaDB anchor search.")
                        return await self._execute_chroma_fallback(query, fallback_reason=reason)
            except Exception as e:
                logger.warning(f"Laya classification failed with error: {e}. Falling back to ChromaDB.")
                return await self._execute_chroma_fallback(query, fallback_reason=f"Laya error: {e}")

        # --- Stage 2: ChromaDB Fallback / Standalone ---
        return await self._execute_chroma_fallback(query)

    async def _execute_chroma_fallback(self, query: str, fallback_reason: str | None = None) -> IntentClassification:
        """
        Executes semantic anchor search using ChromaDB and top-k voting.
        """
        try:
            query_embedding = await asyncio.to_thread(
                lambda: self._model.encode([query]).tolist()
            )

            results = await asyncio.to_thread(
                self._collection.query,
                query_embeddings=query_embedding,
                n_results=TOP_K,
            )

            matched_task, confidence, chroma_rationale = self._resolve_task(results)
            metadata = INTENT_METADATA_MAP.get(matched_task, INTENT_METADATA_MAP["unknown"])

            if fallback_reason:
                rationale = f"[Fallback: ChromaDB] {chroma_rationale} (Reason: {fallback_reason})"
            else:
                rationale = chroma_rationale

            return IntentClassification(
                task=matched_task,
                confidence=confidence,
                complexity=metadata["complexity"],
                requires_tools=metadata["requires_tools"],
                recommended_tier=metadata["recommended_tier"],
                rationale=rationale,
            )

        except Exception as e:
            logger.exception("Semantic Anchor Search failed")
            raise ValueError(f"Failed to execute semantic intent detection: {e}") from e

    def _resolve_task(self, results: dict) -> tuple[str, float, str]:
        """
        Turns a top-k Chroma query result into a (task, confidence, rationale)
        triple using similarity-weighted voting across neighbors, rather than
        trusting a single nearest neighbor.

        With cosine space, Chroma's "distance" is (1 - cosine_similarity), so
        similarity = 1 - distance is a properly bounded [0, 1] confidence
        signal (barring floating point noise), unlike raw L2 distance.
        """
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not metadatas:
            return "unknown", 0.0, "No anchor matches returned."

        # Aggregate similarity per task across the top-k neighbors.
        task_scores: dict[str, float] = defaultdict(float)
        for meta, distance in zip(metadatas, distances):
            similarity = max(0.0, 1.0 - distance)
            task_scores[meta["task"]] += similarity

        ranked = sorted(task_scores.items(), key=lambda kv: kv[1], reverse=True)
        top_task, top_score = ranked[0]

        # Normalize back to a single best-match-style confidence for the
        # winning task: use its single closest neighbor's similarity, not
        # the summed score, so the number stays interpretable as "how close
        # was the best match" rather than "how many neighbors agreed."
        best_single_similarity = max(
            max(0.0, 1.0 - d) for m, d in zip(metadatas, distances) if m["task"] == top_task
        )

        if best_single_similarity < CONFIDENCE_THRESHOLD:
            rationale = (
                f"Best match '{top_task}' had similarity {best_single_similarity:.2f}, "
                f"below the {CONFIDENCE_THRESHOLD} threshold, falling back to 'unknown'."
            )
            return "unknown", best_single_similarity, rationale

        rationale = (
            f"Top-{len(metadatas)} semantic anchor voting matched query to "
            f"'{top_task}' (best neighbor similarity {best_single_similarity:.2f})."
        )
        return top_task, best_single_similarity, rationale