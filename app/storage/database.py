import sqlite3
from app.models.event import MarketEvent


DB_PATH = "data/whale_radar.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        event_type TEXT,
        asset TEXT,
        amount_usd REAL,
        from_entity TEXT,
        to_entity TEXT,
        network TEXT,
        tx_hash TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_event(event: MarketEvent) -> None:
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO events (
        source,
        event_type,
        asset,
        amount_usd,
        from_entity,
        to_entity,
        network,
        tx_hash,
        timestamp
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event.source,
        event.event_type,
        event.asset,
        event.amount_usd,
        event.from_entity,
        event.to_entity,
        event.network,
        event.tx_hash,
        event.timestamp.isoformat(),
    ))

    conn.commit()
    conn.close()
