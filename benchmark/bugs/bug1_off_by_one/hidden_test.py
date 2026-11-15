from paginate import paginate_items


def test_pagination_multiple_pages():
    data = list(range(20))
    page2 = paginate_items(data, page=2, page_size=5)
    assert page2 == [5, 6, 7, 8, 9]


def test_pagination_last_page_overflow():
    data = [1, 2, 3]
    page2 = paginate_items(data, page=2, page_size=2)
    assert page2 == [3]


def test_pagination_empty():
    assert paginate_items([], page=1, page_size=5) == []

