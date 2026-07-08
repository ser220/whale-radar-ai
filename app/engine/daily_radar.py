import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH


def build_daily_radar(hours: int = 24, limit: int = 10) -> str:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT asset, COUNT(*), COALESCE(SUM(amount_usd), 0)
        FROM events
        WHERE timestamp >= ?
        GROUP BY asset
        ORDER BY SUM(amount_usd) DESC
        LIMIT ?
        """,
        (since, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "📊 Daily Institutional Radar\n\nNo whale events in the selected period."

    lines = [
        "📊 <b>Daily Institutional Radar</b>",
        "",
        f"Period: last {hours}h",
        "",
        "🔥 <b>Top Assets by Whale Flow</b>",
    ]

    for i, (asset, count, total_usd) in enumerate(rows, start=1):
        lines.append(
            f"{i}. {asset} — {count} events, ${total_usd:,.0f}"
        )

    return "\n".join(lines)
