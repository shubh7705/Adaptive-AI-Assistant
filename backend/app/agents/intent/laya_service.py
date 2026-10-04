import threading
from typing import Optional, Any
from app.config.logger import logger
from app.config.settings import settings

LAYA_QUESTIONS = {
    "task": {
        "instructions": "What is the primary category or intent of this user request?",
        "type": "choice",
        "criteria": [
            "coding",
            "math",
            "sql",
            "translation",
            "creative",
            "summarization",
            "chat",
            "rag",
            "tool_usage",
            "data_analysis",
            "reasoning",
            "question_answering",
            "unknown",
        ],
    },
    "complexity": {
        "instructions": "What is the estimated execution complexity of fulfilling this user request?",
        "type": "choice",
        "criteria": ["low", "medium", "high"],
    },
    "requires_tools": {
        "instructions": "Does this request require external tools, code execution, web search, or file retrieval to answer?",
        "type": "choice",
        "criteria": ["no", "yes"],
    },
}


class LayaService:
    """
    Service wrapper around Convai Innovations' Laya System 1 decision model.
    Provides fast, non-autoregressive intent and complexity classification.
    """
    _instance: Optional["LayaService"] = None
    _init_lock = threading.Lock()
    _agent: Any = None
    _is_loaded: bool = False

    def __new__(cls) -> "LayaService":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super(LayaService, cls).__new__(cls)
                    cls._instance._init_model()
        return cls._instance

    def _init_model(self) -> None:
        if not settings.LAYA_ENABLED:
            logger.info("Laya System 1 decision model is disabled via settings (LAYA_ENABLED=False).")
            return

        try:
            import laya  # type: ignore

            logger.info(f"Loading Laya System 1 model '{settings.LAYA_MODEL_NAME}'...")
            self._agent = laya.load(settings.LAYA_MODEL_NAME)
            self._is_loaded = True
            logger.info("Laya System 1 model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Failed to load Laya model '{settings.LAYA_MODEL_NAME}': {e}. "
                "System will fall back to ChromaDB anchor search for all requests."
            )
            self._agent = None
            self._is_loaded = False

    @property
    def is_available(self) -> bool:
        return self._is_loaded and self._agent is not None

    def predict(self, query: str) -> Optional[dict]:
        """
        Run synchronous prediction on the query.
        Returns a dict with parsed fields or None if inference fails.
        """
        if not self.is_available:
            return None

        try:
            state = [{"role": "user", "content": query}]
            response = self._agent.predict(state, questions=LAYA_QUESTIONS)
            answers = response.get("answers", {})

            task_ans = answers.get("task", {})
            task_choice = task_ans.get("choice", "unknown")
            task_confidence = float(task_ans.get("answer_confidence", task_ans.get("confidence", 0.0)))

            complexity_ans = answers.get("complexity", {})
            complexity_choice = complexity_ans.get("choice")

            tools_ans = answers.get("requires_tools", {})
            tools_choice = tools_ans.get("choice")
            requires_tools = (tools_choice == "yes") if tools_choice in ("yes", "no") else None

            return {
                "task": task_choice,
                "confidence": task_confidence,
                "complexity": complexity_choice,
                "requires_tools": requires_tools,
                "raw": answers,
            }
        except Exception as e:
            logger.warning(f"Laya inference encountered an error: {e}. Falling back to ChromaDB.")
            return None
