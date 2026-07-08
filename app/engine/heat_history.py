import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH


def init_heat_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            heat_score INTEGER NOT NULL,
            heat_label TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def record_heat(asset: str, heat_score: int, heat_label: str):
    init_heat_history()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO heat_history (asset, heat_score, heat_label, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (asset.upper(), heat_score, heat_label, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()


def get_heat_change(asset: str, current_heat: int, hours: int = 6) -> dict:
    init_heat_history()

    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT heat_score
        FROM heat_history
        WHERE asset = ?
          AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (asset.upper(), since),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "change": 0,
            "direction": "learning",
            "text": "Building Heat History..."
        }

    previous_heat = row[0]
    change = current_heat - previous_heat

    if change >= 10:
        direction = "up"
        text = f"↑ +{change} over {hours}h. Institutional activity accelerating."
    elif change <= -10:
        direction = "down"
        text = f"↓ {change} over {hours}h. Institutional activity fading."
    else:
        direction = "flat"
        text = f"→ {change:+d} over {hours}h. Heat is stable."

    return {
        "change": change,
        "direction": direction,
        "text": text,
    }
