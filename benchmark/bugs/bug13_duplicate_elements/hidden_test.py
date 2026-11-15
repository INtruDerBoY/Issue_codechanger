from dedup import get_unique_items


def test_already_unique():
    assert get_unique_items(["x", "y", "z"]) == ["x", "y", "z"]


def test_empty_list():
    assert get_unique_items([]) == []

