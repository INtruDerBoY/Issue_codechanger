def is_numeric_list(items: list) -> bool:
    return all(isinstance(x, (int, float)) for x in items)
