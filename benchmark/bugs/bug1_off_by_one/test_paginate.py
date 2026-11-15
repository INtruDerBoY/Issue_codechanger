from paginate import paginate_items


def test_first_page_size():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = paginate_items(data, page=1, page_size=3)
    assert result == [1, 2, 3]

