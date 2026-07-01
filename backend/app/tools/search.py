from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def web_search(query: str) -> str:
    """
    Searches the web for current information, news, or factual data.
    Input should be a search query.
    """
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        
        # Format the output for the LLM
        formatted_results = "\n\n".join(
            [f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nURL: {r.get('href')}" for r in results]
        )
        return formatted_results
    except Exception as e:
        return f"Error executing web search: {str(e)}"
