from validator import is_numeric_list


# Bug: ZeroDivisionError on empty list instead of returning 0.0
def calculate_mean(numbers: list) -> float:
    return sum(numbers) / len(numbers)
