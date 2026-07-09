import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH


def detect_campaign(asset: str, wallet: str, direction: str, hours: int = 24) -> dict:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    wallet_lower = (wallet or "").lower()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT asset, amount_usd, from_entity, to_entity, timestamp
        FROM events
        WHERE asset = ?
          AND timestamp >= ?
        ORDER BY timestamp DESC
        """,
        (asset.upper(), since),
    )

    rows = cur.fetchall()
    conn.close()

    matched = []

    for row in rows:
        from_entity = (row["from_entity"] or "").lower()
        to_entity = (row["to_entity"] or "").lower()

        if wallet_lower and (wallet_lower in from_entity or wallet_lower in to_entity):
            matched.append(row)

    count = len(matched)
    total_usd = sum((row["amount_usd"] or 0) for row in matched)

    if count >= 8 and total_usd >= 250_000_000:
        confidence = 95
        label = "Strong Institutional Campaign"
    elif count >= 5 and total_usd >= 150_000_000:
        confidence = 85
        label = "Active Institutional Campaign"
    elif count >= 3 and total_usd >= 75_000_000:
        confidence = 70
        label = "Developing Campaign"
    else:
        confidence = 40
        label = "No clear campaign yet"

    if direction == "bearish":
        campaign_type = "Distribution"
    elif direction == "bullish":
        campaign_type = "Accumulation"
    else:
        campaign_type = "Neutral / Unknown"

    return {
        "type": campaign_type,
        "label": label,
        "events": count,
        "total_usd": total_usd,
        "hours": hours,
        "confidence": confidence,
    }


def format_campaign(campaign: dict) -> str:
    return (
        f"Type: {campaign['type']}\n"
        f"Status: {campaign['label']}\n"
        f"Events: {campaign['events']}\n"
        f"Total: ${campaign['total_usd']:,.0f}\n"
        f"Period: {campaign['hours']}h\n"
        f"Confidence: {campaign['confidence']}/100"
    )
