from parser import sanitize_email


# Bug: accesses 'user_email' instead of 'email' key
def get_user_email(payload: dict) -> str:
    raw_email = payload.get("user_email", "")
    return sanitize_email(raw_email)
