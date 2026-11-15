from formatter import format_currency


def test_standard_usd_formatting():
    # 12.5 should format as $12.50
    assert format_currency(12.5, "USD") == "$12.50"
