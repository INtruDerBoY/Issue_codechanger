from stats import calculate_mean


def test_positive_mean():
    assert calculate_mean([2, 4, 6]) == 4.0


def test_single_element_mean():
    assert calculate_mean([10]) == 10.0
