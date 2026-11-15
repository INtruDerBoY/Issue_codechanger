from eligibility import is_senior_eligible


def test_boundary_age_65_eligible():
    assert is_senior_eligible(65) is True

