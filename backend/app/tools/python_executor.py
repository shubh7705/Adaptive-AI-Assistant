import sys
import io
from langchain_core.tools import tool

@tool
def python_executor(code: str) -> str:
    """
    Executes Python code in a local REPL environment and returns the stdout output.
    Useful for data analysis, complex math, string manipulation, or executing algorithms.
    Ensure you print the final result so it can be captured!
    """
    # Redirect stdout to capture the output of the executed code
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        # Warning: Using exec() like this in production is a massive security risk (RCE).
        # In a real enterprise system, this MUST be sandboxed (e.g., Docker container, WASM, or restricted environment).
        # For the scope of this project, we implement it directly.
        exec(code, {})
        output = redirected_output.getvalue()
        if not output.strip():
            return "Code executed successfully, but nothing was printed to stdout."
        return output
    except Exception as e:
        return f"Execution Error: {str(e)}"
    finally:
        sys.stdout = old_stdout
