from schema import validate_required_fields


def test_missing_second_field_fails():
    data = {"name": "Alice"}
    # 'age' is missing, so it must return False
    assert validate_required_fields(data, ["name", "age"]) is False

