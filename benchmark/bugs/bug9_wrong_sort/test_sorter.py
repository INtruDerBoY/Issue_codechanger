from models import make_student
from sorter import get_leaderboard


def test_highest_scorer_first():
    students = [make_student("Alice", 70), make_student("Bob", 95), make_student("Charlie", 80)]
    board = get_leaderboard(students)
    assert board[0]["name"] == "Bob"
    assert board[-1]["name"] == "Alice"
