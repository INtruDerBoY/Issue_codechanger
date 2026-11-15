from pricing import calculate_final_price


def test_discount_reduces_price():
    # 100 with 20 discount should be 80 + (80 * 0.05 = 4) = 84.00
    assert calculate_final_price(100.0, 20.0, 0.05) == 84.00
