import sqlite3

from app.config import DB_PATH
from app.storage.database import init_db


def get_wallet_profile(wallet: str) -> dict:
    init_db()

    if not wallet:
        return {
            "wallet": "Unknown",
            "seen": 0,
            "total_usd": 0,
            "avg_transfer": 0,
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(amount_usd),0)
        FROM events
        WHERE from_entity = ?
           OR to_entity = ?
        """,
        (wallet, wallet),
    )

    count, total = cursor.fetchone()
    conn.close()

    avg = total / count if count else 0

    return {
        "wallet": wallet,
        "seen": count,
        "total_usd": total,
        "avg_transfer": avg,
    }
