import sqlite3
from app.models.event import MarketEvent
from app.config import DB_PATH


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
        tx_hash TEXT UNIQUE,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def event_exists(tx_hash: str | None) -> bool:
    if not tx_hash:
        return False

    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM events WHERE tx_hash = ?", (tx_hash,))
    row = cursor.fetchone()

    conn.close()
    return row is not None


def save_event(event: MarketEvent) -> bool:
    init_db()

    if event_exists(event.tx_hash):
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO events (
            source, event_type, asset, amount_usd,
            from_entity, to_entity, network, tx_hash, timestamp
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
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()
