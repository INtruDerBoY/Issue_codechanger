from ratios import compute_ratio


def test_zero_denominator_returns_zero():
    assert compute_ratio(10.0, 0.0) == 0.0

