from searcher import contains_keyword


def test_mixed_case_keyword_match():
    assert contains_keyword("Python Programming Language", "python") is True

