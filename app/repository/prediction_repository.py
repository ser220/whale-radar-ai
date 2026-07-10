import json
import sqlite3
from typing import List, Optional

from app.config import DB_PATH
from app.domain.prediction import Prediction


class PredictionRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_prediction(row: sqlite3.Row) -> Prediction:
        keys = row.keys()

        snapshot = {}
        if "ai_snapshot" in keys and row["ai_snapshot"]:
            try:
                snapshot = json.loads(row["ai_snapshot"])
            except (TypeError, json.JSONDecodeError):
                snapshot = {}

        return Prediction(
            id=row["id"],
            asset=row["asset"],
            direction=row["direction"],
            entry_price=row["entry_price"],
            target_price=row["target_price"],
            expected_move=(
                row["expected_move"]
                if "expected_move" in keys and row["expected_move"] is not None
                else 0.0
            ),
            eta=(
                row["eta"]
                if "eta" in keys and row["eta"] is not None
                else ""
            ),
            created_at=(
                row["created_at"]
                if "created_at" in keys
                else None
            ),
            current_price=(
                row["current_price"]
                if "current_price" in keys
                else None
            ),
            actual_move=(
                row["actual_move"]
                if "actual_move" in keys
                else None
            ),
            target_hit=(
                bool(row["target_hit"])
                if "target_hit" in keys
                else False
            ),
            outcome_checked=(
                bool(row["outcome_checked"])
                if "outcome_checked" in keys
                else False
            ),
            accuracy=(
                row["accuracy"]
                if "accuracy" in keys
                else None
            ),
            checked_at=(
                row["checked_at"]
                if "checked_at" in keys
                else None
            ),
            ai_snapshot=snapshot,
        )

    def get(self, prediction_id: int) -> Optional[Prediction]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM prediction_history
                WHERE id = ?
                """,
                (prediction_id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_prediction(row)

    def exists(self, prediction_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1
                FROM prediction_history
                WHERE id = ?
                LIMIT 1
                """,
                (prediction_id,),
            )
            return cur.fetchone() is not None

    def list_open(self, limit: int = 50) -> List[Prediction]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM prediction_history
                WHERE outcome_checked = 0
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()

        return [self._row_to_prediction(row) for row in rows]

    def list_closed(self, limit: int = 50) -> List[Prediction]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM prediction_history
                WHERE outcome_checked = 1
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()

        return [self._row_to_prediction(row) for row in rows]
