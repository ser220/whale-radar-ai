import sqlite3

from app.config import DB_PATH


def init_context_learning_table():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS context_learning(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            market_regime TEXT,
            market_heat TEXT,
            wallet_behaviour TEXT,

            predictions INTEGER DEFAULT 0,
            hits INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def update_context_learning(
    market_regime,
    market_heat,
    wallet_behaviour,
    hit,
):

    init_context_learning_table()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM context_learning
        WHERE
            market_regime=?
        AND market_heat=?
        AND wallet_behaviour=?
    """,(
        market_regime,
        market_heat,
        wallet_behaviour,
    ))

    row = cur.fetchone()

    if row:

        predictions = row["predictions"] + 1
        hits = row["hits"] + (1 if hit else 0)
        accuracy = round(hits / predictions * 100, 1)

        cur.execute("""
            UPDATE context_learning
            SET
                predictions=?,
                hits=?,
                accuracy=?
            WHERE id=?
        """,(
            predictions,
            hits,
            accuracy,
            row["id"],
        ))

    else:

        cur.execute("""
            INSERT INTO context_learning(

                market_regime,
                market_heat,
                wallet_behaviour,

                predictions,
                hits,
                accuracy

            )

            VALUES(?,?,?,?,?,?)
        """,(
            market_regime,
            market_heat,
            wallet_behaviour,
            1,
            1 if hit else 0,
            100 if hit else 0,
        ))

    conn.commit()
    conn.close()


def get_context_stats():

    init_context_learning_table()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM context_learning
        ORDER BY predictions DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def format_context_stats(rows):

    lines = ["🧠 <b>Context Learning</b>", ""]

    for r in rows:

        lines.append(
            f"<b>{r['market_regime']}</b>"
        )

        lines.append(
            f"{r['market_heat']} | {r['wallet_behaviour']}"
        )

        lines.append(
            f"Predictions: {r['predictions']}"
        )

        lines.append(
            f"Accuracy: {r['accuracy']}%"
        )

        lines.append("")

    return "\n".join(lines)
