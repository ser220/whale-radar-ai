import sqlite3
from datetime import datetime

from app.config import DB_PATH


MODULES = [
    "Probability Engine",
    "Risk Engine",
    "Campaign Detector",
    "Wallet Behaviour",
    "Scenario Engine",
    "Decision Engine",
]


def init_module_learning_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS module_learning(
            module TEXT PRIMARY KEY,
            predictions INTEGER DEFAULT 0,
            hits INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0,
            updated_at TEXT
        )
    """)

    for module in MODULES:
        cur.execute("""
            INSERT OR IGNORE INTO module_learning(
                module,
                predictions,
                hits,
                accuracy,
                updated_at
            )
            VALUES (?, 0, 0, 0, ?)
        """, (module, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def update_module_learning(module: str, hit: bool):
    init_module_learning_table()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT predictions, hits
        FROM module_learning
        WHERE module = ?
    """, (module,))

    row = cur.fetchone()

    if not row:
        conn.close()
        return

    predictions = row[0] + 1
    hits = row[1] + (1 if hit else 0)
    accuracy = round((hits / predictions) * 100, 1) if predictions else 0

    cur.execute("""
        UPDATE module_learning
        SET predictions = ?,
            hits = ?,
            accuracy = ?,
            updated_at = ?
        WHERE module = ?
    """, (
        predictions,
        hits,
        accuracy,
        datetime.utcnow().isoformat(),
        module,
    ))

    conn.commit()
    conn.close()


def get_module_learning_stats():
    init_module_learning_table()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT module, predictions, hits, accuracy, updated_at
        FROM module_learning
        ORDER BY accuracy DESC, predictions DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def format_module_learning_stats(rows) -> str:
    if not rows:
        return "No module learning data yet."

    lines = ["🧠 <b>Module Learning</b>", ""]

    for row in rows:
        lines.append(
            f"<b>{row['module']}</b>\n"
            f"Predictions: {row['predictions']}\n"
            f"Hits: {row['hits']}\n"
            f"Accuracy: {row['accuracy']}%\n"
        )

    return "\n".join(lines)
