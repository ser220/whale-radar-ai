import json
import sqlite3
from datetime import datetime

from app.config import DB_PATH
from app.engine.live_market import get_price
from app.engine.module_learning import update_module_learning
from app.engine.module_evaluator import evaluate_modules


def save_prediction(
    asset: str,
    direction: str,
    entry_price: float,
    target_price: float,
    expected_move: float,
    eta: str,
    ai_snapshot: dict = None,
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

    try:
        cur.execute("""
            ALTER TABLE prediction_history
            ADD COLUMN ai_snapshot TEXT
        """)
        conn.commit()
    except sqlite3.OperationalError:
        pass

    cur.execute("""
        INSERT INTO prediction_history(
            asset,
            direction,
            entry_price,
            target_price,
            expected_move,
            eta,
            created_at,
            ai_snapshot
        )
        VALUES(?,?,?,?,?,?,?,?)
    """, (
        asset,
        direction,
        entry_price,
        target_price,
        expected_move,
        eta,
        datetime.utcnow().isoformat(),
        json.dumps(ai_snapshot or {}),
    ))

    conn.commit()
    conn.close()

from app.engine.live_market import get_price


def evaluate_open_predictions(limit: int = 50) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    columns = [
        ("current_price", "REAL"),
        ("actual_move", "REAL"),
        ("target_hit", "INTEGER DEFAULT 0"),
        ("accuracy", "REAL"),
        ("checked_at", "TEXT"),
    ]

    for name, column_type in columns:
        try:
            cur.execute(f"""
                ALTER TABLE prediction_history
                ADD COLUMN {name} {column_type}
            """)
            conn.commit()
        except sqlite3.OperationalError:
            pass
    cur.execute("""
        SELECT *
        FROM prediction_history
        WHERE outcome_checked = 0
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    checked = 0
    hits = 0

    module_updates = []

    checked_prediction_ids = []

    for row in rows:
        asset = row["asset"]
        direction = row["direction"]
        entry_price = row["entry_price"]
        target_price = row["target_price"]
        expected_move = row["expected_move"]

        current_price = get_price(asset)

        if not current_price or not entry_price:
            continue

        actual_move = ((current_price - entry_price) / entry_price) * 100

        if direction == "bearish":
            target_hit = current_price <= target_price
        elif direction == "bullish":
            target_hit = current_price >= target_price
        else:
            target_hit = False

        if expected_move:
            accuracy = max(0, 100 - abs(abs(actual_move) - abs(expected_move)) * 10)
        else:
            accuracy = 0

        cur.execute("""
            UPDATE prediction_history
            SET current_price = ?,
                actual_move = ?,
                target_hit = ?,
                accuracy = ?,
                checked_at = ?,
                outcome_checked = 1
            WHERE id = ?
        """, (
            current_price,
            actual_move,
            1 if target_hit else 0,
            accuracy,
            datetime.utcnow().isoformat(),
            row["id"],
        ))

        checked += 1
        checked_prediction_ids.append(
            int(row["id"])
        )

        if target_hit:
            hits += 1

        module_updates.append(
            evaluate_modules(
                prediction_hit=target_hit,
                probability={},
                campaign={},
                wallet_behaviour={},
                scenario={},
            )
        )

    conn.commit()
    conn.close()

    for updates in module_updates:
        for module, hit in updates.items():
            update_module_learning(module, hit)

    automatic_learning = {
        "predictions_received": 0,
        "processed_count": 0,
        "error_count": 0,
        "saved_total": 0,
        "skipped_total": 0,
        "processed": [],
        "errors": [],
        "mode": "Shadow only",
    }

    if checked_prediction_ids:
        try:
            from app.services.automatic_learning_pipeline import (
                AutomaticLearningPipeline,
            )

            automatic_learning = (
                AutomaticLearningPipeline()
                .run_for_predictions(
                    checked_prediction_ids
                )
            )

        except Exception as exc:
            automatic_learning = {
                "predictions_received": len(
                    checked_prediction_ids
                ),
                "processed_count": 0,
                "error_count": 1,
                "saved_total": 0,
                "skipped_total": 0,
                "processed": [],
                "errors": [{
                    "prediction_id": None,
                    "error": str(exc),
                }],
                "mode": "Shadow only",
            }

    return {
        "checked": checked,
        "hits": hits,
        "hit_rate": (
            round(
                (hits / checked) * 100,
                1,
            )
            if checked
            else 0
        ),
        "automatic_learning": automatic_learning,
    }
