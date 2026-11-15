from eligibility import is_senior_eligible


def test_age_under_threshold():
    assert is_senior_eligible(64) is False


def test_age_over_threshold():
    assert is_senior_eligible(70) is True

