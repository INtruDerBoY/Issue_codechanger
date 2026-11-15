def sanitize_email(email: str) -> str:
    return email.strip().lower() if email else ""
