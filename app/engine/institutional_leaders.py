import sqlite3

from app.config import DB_PATH


def get_institutional_leaders(limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT h.asset,
               h.institutional_score,
               h.market_heat,
               h.market_regime,
               h.timestamp
        FROM institutional_history h
        INNER JOIN (
            SELECT asset, MAX(id) AS last_id
            FROM institutional_history
            GROUP BY asset
        ) latest
        ON h.id = latest.last_id
        ORDER BY h.institutional_score DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    leaders = []

    for row in rows:
        leaders.append({
            "asset": row["asset"],
            "score": row["institutional_score"],
            "heat": row["market_heat"],
            "regime": row["market_regime"],
            "timestamp": row["timestamp"],
        })

    return leaders
