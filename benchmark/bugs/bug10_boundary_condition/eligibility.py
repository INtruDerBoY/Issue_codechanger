from rules import SENIOR_AGE_THRESHOLD


# Bug: uses strict greater than, rejecting age 65
def is_senior_eligible(age: int) -> bool:
    return age > SENIOR_AGE_THRESHOLD

