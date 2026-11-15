from currency import get_symbol


# Bug: formats with 1 decimal place instead of 2 for currency
def format_currency(amount: float, code: str = "USD") -> str:
    symbol = get_symbol(code)
    return f"{symbol}{amount:.1f}"
