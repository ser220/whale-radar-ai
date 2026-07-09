import sqlite3
from datetime import datetime

from app.config import DB_PATH


def save_prediction(
    asset: str,
    direction: str,
    entry_price: float,
    target_price: float,
    expected_move: float,
    eta: str,
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT,
            direction TEXT,
            entry_price REAL,
            target_price REAL,
            expected_move REAL,
            eta TEXT,
            created_at TEXT,
            outcome_checked INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        INSERT INTO prediction_history(
            asset,
            direction,
            entry_price,
            target_price,
            expected_move,
            eta,
            created_at
        )
        VALUES(?,?,?,?,?,?,?)
    """,(
        asset,
        direction,
        entry_price,
        target_price,
        expected_move,
        eta,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()
