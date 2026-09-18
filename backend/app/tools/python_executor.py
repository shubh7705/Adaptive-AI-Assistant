import ast
import operator
from langchain_core.tools import tool

@tool
def python_executor(code: str) -> str:
    """
    Evaluates a small, side-effect-free subset of Python expressions.
    Imports, statements, file access, and function calls are intentionally unsupported.
    """
    if len(code) > 2_000:
        return "Error: Expression is too long."

    binary_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
    }
    unary_operators = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str, bool, type(None))):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in binary_operators:
            return binary_operators[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_operators:
            return unary_operators[type(node.op)](evaluate(node.operand))
        if isinstance(node, (ast.List, ast.Tuple)):
            return [evaluate(item) for item in node.elts]
        raise ValueError("Only literal values and arithmetic expressions are allowed")

    try:
        tree = ast.parse(code.strip(), mode="eval")
        return str(evaluate(tree.body))
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
        return f"Execution Error: {error}"
