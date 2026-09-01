import ast
import math
import operator

_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "log": math.log10, "ln": math.log, "exp": math.exp,
    "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
}
_CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}


def evaluate(expression: str) -> float:
    if len(expression) > 500:
        raise ValueError("Expression is too long.")
    tree = ast.parse(expression.replace("^", "**"), mode="eval")
    return float(_eval(tree.body))


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent is too large.")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = _FUNCTIONS.get(node.func.id)
        if function and not node.keywords:
            return function(*[_eval(argument) for argument in node.args])
    raise ValueError("Unsupported expression.")


def format_number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("Result is not finite.")
    return f"{value:.12g}"


def mass_from_moles(moles: float, molecular_weight: float) -> float:
    return moles * molecular_weight


def moles_from_mass(mass_g: float, molecular_weight: float) -> float:
    if molecular_weight == 0: raise ValueError("Molecular weight cannot be zero.")
    return mass_g / molecular_weight


def molarity(moles: float, volume_l: float) -> float:
    if volume_l == 0: raise ValueError("Volume cannot be zero.")
    return moles / volume_l


def dilution_final_volume(c1: float, v1: float, c2: float) -> float:
    if c2 == 0: raise ValueError("Final concentration cannot be zero.")
    return c1 * v1 / c2


def ppm_mass(mass_solute_mg: float, solution_mass_kg: float) -> float:
    if solution_mass_kg == 0: raise ValueError("Solution mass cannot be zero.")
    return mass_solute_mg / solution_mass_kg
