from math_helpers import safe_round


# Bug: ZeroDivisionError when denominator is zero, should return 0.0
def compute_ratio(numerator: float, denominator: float) -> float:
    return safe_round(numerator / denominator)

