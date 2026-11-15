from searcher import contains_keyword


def test_uppercase_keyword_match():
    assert contains_keyword("hello world", "WORLD") is True


def test_no_match():
    assert contains_keyword("apple orange", "banana") is False

