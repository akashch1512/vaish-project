import ast
import math
import operator

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


MAX_ABS_VALUE = 10**15
MAX_EXPRESSION_LENGTH = 160

BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


class CalculatorError(ValueError):
    pass


def format_number(value):
    if not math.isfinite(value):
        raise CalculatorError("Result is not a finite number.")

    if abs(value) > MAX_ABS_VALUE:
        return f"{value:.10e}"

    if float(value).is_integer():
        return str(int(value))

    return f"{value:.12g}"


def normalize_expression(expression):
    return (
        expression.replace("×", "*")
        .replace("÷", "/")
        .replace("^", "**")
        .replace("π", "pi")
    )


def evaluate_node(node):
    if isinstance(node, ast.Expression):
        return evaluate_node(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        left = evaluate_node(node.left)
        right = evaluate_node(node.right)

        if isinstance(node.op, (ast.Div, ast.Mod)) and right == 0:
            raise CalculatorError("Cannot divide by zero.")

        if isinstance(node.op, ast.Pow) and abs(right) > 12:
            raise CalculatorError("Power is too large.")

        result = BIN_OPS[type(node.op)](left, right)
        if abs(result) > MAX_ABS_VALUE:
            raise CalculatorError("Result is too large.")
        return result

    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](evaluate_node(node.operand))

    if isinstance(node, ast.Name) and node.id in CONSTANTS:
        return CONSTANTS[node.id]

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = FUNCTIONS.get(node.func.id)
        if not function or len(node.args) != 1 or node.keywords:
            raise CalculatorError("Unsupported function.")

        argument = evaluate_node(node.args[0])
        try:
            return function(argument)
        except ValueError as exc:
            raise CalculatorError("Invalid function input.") from exc

    raise CalculatorError("Use numbers, operators, parentheses, and calculator functions only.")


def calculate_expression(expression):
    cleaned = normalize_expression(expression.strip())

    if not cleaned:
        raise CalculatorError("Enter a calculation first.")

    if len(cleaned) > MAX_EXPRESSION_LENGTH:
        raise CalculatorError("Calculation is too long.")

    try:
        parsed = ast.parse(cleaned, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError("That calculation is incomplete.") from exc

    result = evaluate_node(parsed)
    return format_number(result)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/calculate")
def calculate():
    data = request.get_json(silent=True) or {}
    expression = str(data.get("expression", ""))

    try:
        result = calculate_expression(expression)
    except CalculatorError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, "result": result})


if __name__ == "__main__":
    app.run(debug=True)
