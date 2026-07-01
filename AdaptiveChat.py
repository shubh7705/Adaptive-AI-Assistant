import os
import json
import requests
from typing import Literal, Optional
from dotenv import load_dotenv
from IntentAnalyzer import IntentAnalyzer
from ModelSelector import ModelSelector

# Load environment variables
load_dotenv()

class AdaptiveChat:
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_key = api_key
        self.intent_analyzer = IntentAnalyzer()
        self.model_selector = ModelSelector()
        self.model_name = ""

    def ask(self, query: str, chat_history: list = []):
        # 1. Analyze Intent
        intent = self.intent_analyzer.analyze_intent(query)

        # 2. Select Model
        model_info = self.model_selector.get_model(intent.intent)

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",   # Optional
        "X-OpenRouter-Title": "AI Router",         # Optional
        }

        payload = {
        "model": model_info["model"],
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise Exception(
                f"Error {response.status_code}: {response.text}"
            )

        result = response.json()

        return result["choices"][0]["message"]["content"]



   

    
    

    