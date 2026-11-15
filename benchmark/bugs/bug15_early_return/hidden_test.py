from schema import validate_required_fields


def test_all_fields_present():
    data = {"id": 1, "username": "admin", "active": True}
    assert validate_required_fields(data, ["id", "username", "active"]) is True


def test_first_field_missing():
    assert validate_required_fields({"b": 2}, ["a", "b"]) is False

