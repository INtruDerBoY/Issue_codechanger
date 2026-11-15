from pagination import calculate_offset


def test_string_query_params():
    # When passed strings like in query dicts {"page": "2", "limit": "10"} -> offset should be (2-1)*10 = 10
    params = {"page": "2", "limit": "10"}
    assert calculate_offset(params) == 10

