from pagination import calculate_offset


def test_integer_params():
    assert calculate_offset({"page": 3, "limit": 15}) == 30


def test_empty_params_uses_defaults():
    assert calculate_offset({}) == 0

