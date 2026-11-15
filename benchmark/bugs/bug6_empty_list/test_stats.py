from stats import calculate_mean


def test_empty_list_mean():
    assert calculate_mean([]) == 0.0
