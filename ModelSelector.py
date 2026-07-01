from typing import TypedDict, Dict

class ModelSelector:
    def __init__(self):
        self.models = {
            "coding": {
                "provider": "OpenRouter",
                "model": "deepseek/deepseek-chat-v3-0324",
                "description": "Optimized for programming, debugging, and code generation.",
            },
            "creative": {
                "provider": "OpenRouter",
                "model": "google/gemma-3-12b-it",
                "description": "Excellent for storytelling, blogs, emails, and creative writing.",
            },
            "summarization": {
                "provider": "OpenRouter",
                "model": "qwen/qwen3-8b",
                "description": "Optimized for summarization and long-context understanding.",
            },
        }
    
    def get_model(self, intent: str) -> Dict:
        if intent.lower() in self.models:
            return self.models[intent.lower()]
        else:
            raise ValueError(f"Invalid intent: {intent}")