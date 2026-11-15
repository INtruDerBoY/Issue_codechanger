def has_field(data: dict, key: str) -> bool:
    return key in data and data[key] is not None

