from tracker import track_event


def test_custom_tags_not_overwritten():
    event = track_event("upload", tags=["custom"])
    assert event["tags"] == ["custom", "active"]


def test_three_consecutive_calls():
    e1 = track_event("e1")
    e2 = track_event("e2")
    e3 = track_event("e3")
    assert e1["tags"] == ["active"]
    assert e2["tags"] == ["active"]
    assert e3["tags"] == ["active"]

