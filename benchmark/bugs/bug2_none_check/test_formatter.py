from models import create_user
from formatter import format_full_name


def test_format_name_without_middle():
    user = create_user("Alan", "Turing", middle=None)
    assert format_full_name(user) == "Alan Turing"

