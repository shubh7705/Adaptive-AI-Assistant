from app.tools.calculator import calculator
from app.tools.search import web_search
from app.tools.python_executor import python_executor

def get_all_tools():
    """
    Returns a list of all available LangChain tools in the framework.
    These can be bound to any tool-capable LLM (e.g. llm.bind_tools(get_all_tools()))
    """
    return [
        calculator,
        web_search,
        python_executor
    ]
