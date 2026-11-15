from formatter import format_currency


def test_zero_amount():
    assert format_currency(0.0, "USD") == "$0.00"


def test_eur_currency():
    assert format_currency(99.99, "EUR") == "€99.99"
