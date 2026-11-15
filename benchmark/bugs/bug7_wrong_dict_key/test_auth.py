from auth import get_user_email


def test_standard_email_payload():
    payload = {"username": "alice", "email": "Alice@Example.com"}
    assert get_user_email(payload) == "alice@example.com"
