import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import DB_PATH


class AnalysisStateRepository:
    """
    Stores the latest /analyze result per asset.

    Used only for change tracking.
    No trading execution.
    """

    def __init__(
        self,
        db_path: str = DB_PATH,
    ) -> None:
        self.db_path = str(db_path)
        self._init_table()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(
        self,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_state (
                    asset TEXT PRIMARY KEY,
                    analyzed_at TEXT NOT NULL,
                    snapshot_id TEXT,
                    status TEXT,
                    bias TEXT,
                    trade_readiness REAL,
                    confidence REAL,
                    payload_json TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_analysis_state_analyzed_at
                ON analysis_state(analyzed_at)
                """
            )

    def get_latest(
        self,
        asset: str,
    ) -> Optional[Dict[str, Any]]:
        normalized_asset = self._asset(
            asset
        )

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    asset,
                    analyzed_at,
                    snapshot_id,
                    status,
                    bias,
                    trade_readiness,
                    confidence,
                    payload_json
                FROM analysis_state
                WHERE asset = ?
                LIMIT 1
                """,
                (normalized_asset,),
            ).fetchone()

        if row is None:
            return None

        try:
            payload = json.loads(
                row["payload_json"]
            )
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            payload = {}

        return {
            "asset": row["asset"],
            "analyzed_at": row["analyzed_at"],
            "snapshot_id": row["snapshot_id"],
            "status": row["status"],
            "bias": row["bias"],
            "trade_readiness": (
                row["trade_readiness"]
            ),
            "confidence": row["confidence"],
            "payload": payload,
        }

    def save(
        self,
        asset: str,
        snapshot_id: Optional[str],
        trade: Dict[str, Any],
    ) -> None:
        normalized_asset = self._asset(
            asset
        )

        analyzed_at = datetime.now(
            timezone.utc
        ).isoformat()

        payload_json = json.dumps(
            trade,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO analysis_state (
                    asset,
                    analyzed_at,
                    snapshot_id,
                    status,
                    bias,
                    trade_readiness,
                    confidence,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset) DO UPDATE SET
                    analyzed_at = excluded.analyzed_at,
                    snapshot_id = excluded.snapshot_id,
                    status = excluded.status,
                    bias = excluded.bias,
                    trade_readiness =
                        excluded.trade_readiness,
                    confidence = excluded.confidence,
                    payload_json = excluded.payload_json
                """,
                (
                    normalized_asset,
                    analyzed_at,
                    snapshot_id,
                    str(
                        trade.get("status")
                        or "UNKNOWN"
                    ),
                    str(
                        trade.get("bias")
                        or "NEUTRAL"
                    ),
                    self._number(
                        trade.get(
                            "trade_readiness"
                        )
                    ),
                    self._number(
                        trade.get("confidence")
                    ),
                    payload_json,
                ),
            )

    @staticmethod
    def _asset(
        asset: str,
    ) -> str:
        value = str(
            asset or ""
        ).strip().upper()

        if not value:
            raise ValueError(
                "asset cannot be empty."
            )

        return value

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0
