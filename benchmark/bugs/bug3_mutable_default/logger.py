def format_event_log(event: dict) -> str:
    tags_str = ",".join(event.get("tags", []))
    return f"[{event['name']}] tags={tags_str}"

