from cleaner import trim_text


# Bug: case-sensitive search instead of case-insensitive
def contains_keyword(text: str, keyword: str) -> bool:
    clean_text = trim_text(text)
    clean_kw = trim_text(keyword)
    return clean_kw in clean_text

