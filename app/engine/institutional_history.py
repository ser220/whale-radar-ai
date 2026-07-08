import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH


def init_institutional_history():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutional_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            institutional_score INTEGER NOT NULL,
            market_heat INTEGER NOT NULL,
            event_importance INTEGER NOT NULL,
            market_regime TEXT NOT NULL,
            pressure_bias TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def record_institutional_snapshot(
    asset: str,
    institutional_score: int,
    market_heat: int,
    event_importance: int,
    market_regime: str,
    pressure_bias: str,
):
    init_institutional_history()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO institutional_history (
            asset,
            timestamp,
            institutional_score,
            market_heat,
            event_importance,
            market_regime,
            pressure_bias
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset.upper(),
            datetime.utcnow().isoformat(),
            institutional_score,
            market_heat,
            event_importance,
            market_regime,
            pressure_bias,
        ),
    )

    conn.commit()
    conn.close()


def get_institutional_trend_from_db(asset: str, current_score: int, hours: int = 24) -> dict:
    init_institutional_history()

    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT institutional_score
        FROM institutional_history
        WHERE asset = ?
          AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (asset.upper(), since),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return {
            "change": 0,
            "direction": "learning",
            "text": "Collecting institutional history..."
        }

    previous_score = row[0]
    change = current_score - previous_score

    if change >= 15:
        return {
            "change": change,
            "direction": "up",
            "text": f"🟢 Institutional demand rising (+{change})"
        }

    if change <= -15:
        return {
            "change": change,
            "direction": "down",
            "text": f"🔴 Institutional demand falling ({change})"
        }

    return {
        "change": change,
        "direction": "flat",
        "text": f"🟡 Institutional trend stable ({change:+d})"
    }
