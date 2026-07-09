import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH


def analyze_event_memory(event, direction: str, hours: int = 2) -> dict:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT asset, amount_usd, from_entity, to_entity, timestamp
        FROM events
        WHERE asset = ?
          AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (
        event.asset,
        since,
    ))

    rows = cur.fetchall()
    conn.close()

    wallet = event.from_entity if direction == "bearish" else event.to_entity
    wallet_lower = (wallet or "").lower()

    matched = []

    for row in rows:
        from_entity = (row["from_entity"] or "").lower()
        to_entity = (row["to_entity"] or "").lower()

        if wallet_lower and (wallet_lower in from_entity or wallet_lower in to_entity):
            matched.append(row)

    count = len(matched)
    total_usd = sum((row["amount_usd"] or 0) for row in matched)

    if count >= 5:
        status = "Strong repeated activity"
    elif count >= 3:
        status = "Repeated activity detected"
    elif count >= 2:
        status = "Follow-up event detected"
    else:
        status = "Isolated event"

    return {
        "wallet": wallet or "Unknown Wallet",
        "events": count,
        "total_usd": total_usd,
        "hours": hours,
        "status": status,
    }


def format_event_memory(memory: dict) -> str:
    return (
        f"Wallet: {memory['wallet']}\n"
        f"Status: {memory['status']}\n"
        f"Events: {memory['events']} in {memory['hours']}h\n"
        f"Total Flow: ${memory['total_usd']:,.0f}"
    )
