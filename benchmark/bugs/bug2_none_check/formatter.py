def format_full_name(user: dict) -> str:
    first = user.get("first", "").strip()
    last = user.get("last", "").strip()
    middle = user.get("middle")
    # Bug: crashes with AttributeError when middle is None
    clean_middle = middle.strip()
    if clean_middle:
        return f"{first} {clean_middle} {last}"
    return f"{first} {last}"

