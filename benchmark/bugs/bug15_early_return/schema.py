from validator import has_field


# Bug: early return inside loop returns True after checking first key only
def validate_required_fields(data: dict, required_keys: list) -> bool:
    for key in required_keys:
        if not has_field(data, key):
            return False
        return True
    return True

