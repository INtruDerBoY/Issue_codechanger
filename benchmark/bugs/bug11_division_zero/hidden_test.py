from ratios import compute_ratio


def test_normal_division():
    assert compute_ratio(10.0, 2.0) == 5.0


def test_both_zero():
    assert compute_ratio(0.0, 0.0) == 0.0

