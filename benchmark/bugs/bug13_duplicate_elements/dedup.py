from sanitizer import normalize_token


# Bug: list(set(...)) loses original element order
def get_unique_items(items: list) -> list:
    cleaned = [normalize_token(x) for x in items]
    return list(set(cleaned))

