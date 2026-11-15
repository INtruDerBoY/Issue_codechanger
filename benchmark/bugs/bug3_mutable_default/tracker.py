from logger import format_event_log


# Bug: mutable default argument retains items between calls
def track_event(name: str, tags: list = []) -> dict:
    tags.append("active")
    event = {"name": name, "tags": tags}
    event["log"] = format_event_log(event)
    return event

