from tracker import track_event


def test_independent_events_do_not_share_tags():
    event1 = track_event("login")
    event2 = track_event("logout")
    # Due to mutable default list, event2 tags will have ['active', 'active']
    assert event2["tags"] == ["active"]

