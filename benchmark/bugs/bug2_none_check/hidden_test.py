from models import create_user
from formatter import format_full_name


def test_format_name_with_middle():
    user = create_user("John", "Doe", middle="Fitzgerald")
    assert format_full_name(user) == "John Fitzgerald Doe"


def test_format_name_with_empty_middle():
    user = create_user("Grace", "Hopper", middle="")
    assert format_full_name(user) == "Grace Hopper"


def test_format_name_with_none_middle():
    user = create_user("Grace", "Hopper", middle=None)
    assert format_full_name(user) == "Grace Hopper"


def test_format_name_with_whitespace_middle():
    user = create_user("Ada", "Lovelace", middle="   ")
    assert format_full_name(user) == "Ada Lovelace"
