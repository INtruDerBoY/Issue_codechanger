from defaults import DEFAULT_PAGE, DEFAULT_LIMIT


# Bug: assumes page and limit are ints, crashes with TypeError when string from query
def calculate_offset(params: dict) -> int:
    page = params.get("page", DEFAULT_PAGE)
    limit = params.get("limit", DEFAULT_LIMIT)
    return (page - 1) * limit

