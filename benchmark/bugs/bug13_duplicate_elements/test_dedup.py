from dedup import get_unique_items


def test_dedup_preserves_order():
    items = ["b", "a", "b", "c", "a"]
    assert get_unique_items(items) == ["b", "a", "c"]

