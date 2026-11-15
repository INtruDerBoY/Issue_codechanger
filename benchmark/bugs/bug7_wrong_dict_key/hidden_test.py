from auth import get_user_email


def test_missing_email_returns_empty():
    assert get_user_email({"username": "bob"}) == ""


def test_whitespace_email():
    assert get_user_email({"email": "  test@domain.com  "}) == "test@domain.com"
