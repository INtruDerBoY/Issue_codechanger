from models import make_student


# Bug: sorts ascending instead of descending by score
def get_leaderboard(students: list) -> list:
    return sorted(students, key=lambda s: s["score"])
