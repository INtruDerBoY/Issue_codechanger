from pricing import calculate_final_price


def test_zero_discount():
    assert calculate_final_price(50.0, 0.0, 0.10) == 55.00


def test_full_discount():
    assert calculate_final_price(50.0, 50.0, 0.10) == 0.00
