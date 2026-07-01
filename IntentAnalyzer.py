import os
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class IntentStructure(BaseModel):
    intent: Literal["Coding", "Summarization", "Creative"] = Field(
        ...,
        description="Intent of the query"
    )

class IntentAnalyzer:
    """
    Class to analyze the intent of a user's query using Google's Generative AI.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the IntentAnalyzer with the specified model and API key.
        If api_key is not provided, it will be extracted from the GOOGLE_API_KEY environment variable.
        """
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
            
        self.model = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        self.intent_llm = self.model.with_structured_output(IntentStructure)
        self.system_prompt = SystemMessage(content="""You are an intent classifier.

Classify the user's query.

Possible intents:

coding
creative
summarization""")

    def analyze_intent(self, query: str) -> IntentStructure:
        """
        Analyzes the given query and returns the structured intent.
        
        Args:
            query (str): The user's input query.
            
        Returns:
            IntentStructure: The classified intent structure.
        """
        messages = [
            self.system_prompt,
            HumanMessage(content=query)
        ]
        
        response = self.intent_llm.invoke(messages)
        return response

# Example usage:
if __name__ == "__main__":
    analyzer = IntentAnalyzer()
    
    sample_query = "Summarize this research paper"
    print(f"Query: {sample_query}")
    
    result = analyzer.analyze_intent(sample_query)
    print(f"Result: {result}")
