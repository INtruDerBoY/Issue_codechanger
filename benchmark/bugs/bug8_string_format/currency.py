def get_symbol(currency_code: str) -> str:
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    return symbols.get(currency_code, "$")
