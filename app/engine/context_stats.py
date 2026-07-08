import sqlite3
from datetime import datetime, timedelta
from app.config import DB_PATH
from app.storage.database import init_db


def get_asset_stats(asset: str, hours: int = 24) -> dict:
    init_db()

    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            COALESCE(SUM(amount_usd), 0),
            COALESCE(MAX(amount_usd), 0)
        FROM events
        WHERE asset = ?
          AND timestamp >= ?
        """,
        (asset.upper(), since),
    )

    count, total_usd, max_transfer = cursor.fetchone()
    conn.close()

    return {
        "count": count or 0,
        "total_usd": float(total_usd or 0),
        "max_transfer": float(max_transfer or 0),
        "hours": hours,
    }
