import sqlite3
from app.config import DB_PATH


def get_exchange_stats(exchange: str, hours: int = 6):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            COUNT(*),
            COALESCE(SUM(amount_usd),0)
        FROM events
        WHERE
            (
                from_entity LIKE ?
                OR to_entity LIKE ?
            )
        AND timestamp >= datetime('now', ?)
        """,
        (
            f"%{exchange}%",
            f"%{exchange}%",
            f"-{hours} hours",
        ),
    )

    count, total = cur.fetchone()

    conn.close()

    return {
        "count": count or 0,
        "total_usd": float(total or 0),
        "hours": hours,
    }
