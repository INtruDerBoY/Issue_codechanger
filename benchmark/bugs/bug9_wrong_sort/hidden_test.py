from models import make_student
from sorter import get_leaderboard


def test_empty_students():
    assert get_leaderboard([]) == []


def test_single_student():
    s = [make_student("Solo", 100)]
    assert get_leaderboard(s) == s
