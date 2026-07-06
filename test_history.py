from app.storage.history import get_recent_events

events = get_recent_events(10)

for e in events:
    print(
        e["id"],
        e["asset"],
        e["amount_usd"],
        e["from_entity"],
        "->",
        e["to_entity"],
        e["timestamp"],
    )
