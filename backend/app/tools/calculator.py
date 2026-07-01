from langchain_core.tools import tool
import numexpr

@tool
def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression.
    Useful for precise calculations (e.g., '6754 * 9922').
    Provide the input as a mathematical string.
    """
    try:
        # numexpr is much safer and faster than eval() for math
        result = numexpr.evaluate(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"
