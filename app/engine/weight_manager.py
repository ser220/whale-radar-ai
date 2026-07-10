import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import DB_PATH
from app.engine.learning_review_engine import (
    APPROVE,
    LearningReview,
)


DEFAULT_MANAGED_WEIGHTS = {
    "Probability Engine": 0.70,
    "Campaign Detector": 0.90,
    "Wallet Behaviour": 0.80,
    "Scenario Engine": 0.85,
    "Risk Engine": 1.10,
    "Decision Engine": 1.00,
}

MIN_WEIGHT = 0.10
MAX_WEIGHT = 2.00


class WeightManager:
    """
    Versioned weight storage and controlled update manager.

    Current stage:
    - stored separately from production adaptive_weights.py;
    - no production decision uses these weights yet;
    - changes require APPROVE review and human_approved=True;
    - every change creates a version for rollback.
    """

    def __init__(
        self,
        db_path: str = DB_PATH,
        default_weights: Optional[
            Dict[str, float]
        ] = None,
    ) -> None:
        self.db_path = db_path
        self.default_weights = dict(
            default_weights
            or DEFAULT_MANAGED_WEIGHTS
        )

        self._init_tables()
        self._ensure_initial_version()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weight_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    weights TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    rolled_back_from INTEGER
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_weight_versions_active
                ON weight_versions(is_active)
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weight_change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER NOT NULL,
                    module TEXT NOT NULL,
                    old_weight REAL NOT NULL,
                    new_weight REAL NOT NULL,
                    change_amount REAL NOT NULL,
                    review_decision TEXT,
                    review_confidence REAL,
                    samples INTEGER,
                    human_approved INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_weight_change_log_version
                ON weight_change_log(version_id)
                """
            )

            conn.commit()

    def _ensure_initial_version(self) -> None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM weight_versions
                LIMIT 1
                """
            ).fetchone()

            if row is not None:
                return

            conn.execute(
                """
                INSERT INTO weight_versions (
                    weights,
                    reason,
                    source,
                    created_at,
                    is_active,
                    rolled_back_from
                )
                VALUES (?, ?, ?, ?, 1, NULL)
                """,
                (
                    json.dumps(
                        self._normalize_weights(
                            self.default_weights
                        ),
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    "Initial managed weight version.",
                    "system-default",
                    self._now(),
                ),
            )

            conn.commit()

    def get_current_weights(
        self,
    ) -> Dict[str, float]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT weights
                FROM weight_versions
                WHERE is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return self._normalize_weights(
                self.default_weights
            )

        try:
            data = json.loads(row["weights"])
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            return self._normalize_weights(
                self.default_weights
            )

        return self._normalize_weights(data)

    def get_active_version(
        self,
    ) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM weight_versions
                WHERE is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        return (
            self._version_row_to_dict(row)
            if row is not None
            else None
        )

    def list_versions(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM weight_versions
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(int(limit), 1),),
            ).fetchall()

        return [
            self._version_row_to_dict(row)
            for row in rows
        ]

    def preview(
        self,
        reviews: List[LearningReview],
    ) -> Dict[str, Any]:
        current = self.get_current_weights()
        proposed = dict(current)

        accepted = []
        skipped = []

        for review in reviews:
            if review.decision != APPROVE:
                skipped.append({
                    "module": review.module,
                    "decision": review.decision,
                    "reason": (
                        "Only APPROVE reviews are eligible."
                    ),
                })
                continue

            old_weight = current.get(
                review.module,
                review.current_weight,
            )

            new_weight = self._clamp_weight(
                review.suggested_weight
            )

            proposed[review.module] = new_weight

            accepted.append({
                "module": review.module,
                "old_weight": round(
                    old_weight,
                    4,
                ),
                "new_weight": round(
                    new_weight,
                    4,
                ),
                "change": round(
                    new_weight - old_weight,
                    4,
                ),
                "confidence": review.confidence,
                "samples": review.samples,
            })

        return {
            "current_weights": current,
            "proposed_weights": proposed,
            "accepted": accepted,
            "skipped": skipped,
            "eligible_count": len(accepted),
            "skipped_count": len(skipped),
            "mode": "Dry run",
        }

    def apply_reviews(
        self,
        reviews: List[LearningReview],
        human_approved: bool = False,
        reason: str = (
            "Human-approved learning review update."
        ),
    ) -> Dict[str, Any]:
        preview = self.preview(reviews)

        if not human_approved:
            return {
                **preview,
                "status": "not_applied",
                "error": (
                    "Explicit human approval is required."
                ),
                "version_id": None,
                "mode": "Shadow only",
            }

        if preview["eligible_count"] == 0:
            return {
                **preview,
                "status": "nothing_to_apply",
                "error": (
                    "No APPROVE reviews were eligible."
                ),
                "version_id": None,
                "mode": "Shadow only",
            }

        created_at = self._now()

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE weight_versions
                SET is_active = 0
                WHERE is_active = 1
                """
            )

            cursor = conn.execute(
                """
                INSERT INTO weight_versions (
                    weights,
                    reason,
                    source,
                    created_at,
                    is_active,
                    rolled_back_from
                )
                VALUES (?, ?, ?, ?, 1, NULL)
                """,
                (
                    json.dumps(
                        preview["proposed_weights"],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    str(reason or "").strip()
                    or "Human-approved update.",
                    "learning-review",
                    created_at,
                ),
            )

            version_id = cursor.lastrowid

            for change in preview["accepted"]:
                review = next(
                    item
                    for item in reviews
                    if item.module == change["module"]
                    and item.decision == APPROVE
                )

                conn.execute(
                    """
                    INSERT INTO weight_change_log (
                        version_id,
                        module,
                        old_weight,
                        new_weight,
                        change_amount,
                        review_decision,
                        review_confidence,
                        samples,
                        human_approved,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        version_id,
                        change["module"],
                        change["old_weight"],
                        change["new_weight"],
                        change["change"],
                        review.decision,
                        review.confidence,
                        review.samples,
                        created_at,
                    ),
                )

            conn.commit()

        return {
            **preview,
            "status": "applied",
            "error": None,
            "version_id": version_id,
            "mode": (
                "Managed weights only — "
                "not connected to production decisions"
            ),
        }

    def rollback(
        self,
        version_id: int,
        human_approved: bool = False,
    ) -> Dict[str, Any]:
        if not human_approved:
            return {
                "status": "not_applied",
                "error": (
                    "Explicit human approval is required."
                ),
                "version_id": None,
                "mode": "Shadow only",
            }

        with self._connect() as conn:
            target = conn.execute(
                """
                SELECT *
                FROM weight_versions
                WHERE id = ?
                """,
                (int(version_id),),
            ).fetchone()

            if target is None:
                return {
                    "status": "not_found",
                    "error": (
                        "Requested weight version was not found."
                    ),
                    "version_id": None,
                    "mode": "Shadow only",
                }

            try:
                weights = self._normalize_weights(
                    json.loads(target["weights"])
                )
            except (
                TypeError,
                json.JSONDecodeError,
            ):
                return {
                    "status": "invalid_version",
                    "error": (
                        "Requested version contains invalid weights."
                    ),
                    "version_id": None,
                    "mode": "Shadow only",
                }

            conn.execute(
                """
                UPDATE weight_versions
                SET is_active = 0
                WHERE is_active = 1
                """
            )

            cursor = conn.execute(
                """
                INSERT INTO weight_versions (
                    weights,
                    reason,
                    source,
                    created_at,
                    is_active,
                    rolled_back_from
                )
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (
                    json.dumps(
                        weights,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    (
                        f"Rollback to weight version "
                        f"{int(version_id)}."
                    ),
                    "rollback",
                    self._now(),
                    int(version_id),
                ),
            )

            new_version_id = cursor.lastrowid
            conn.commit()

        return {
            "status": "rolled_back",
            "version_id": new_version_id,
            "rolled_back_from": int(version_id),
            "weights": weights,
            "error": None,
            "mode": (
                "Managed weights only — "
                "not connected to production decisions"
            ),
        }

    def get_change_log(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM weight_change_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(int(limit), 1),),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def _normalize_weights(
        self,
        weights: Dict[str, Any],
    ) -> Dict[str, float]:
        result = dict(self.default_weights)

        if isinstance(weights, dict):
            for module, value in weights.items():
                try:
                    result[str(module)] = (
                        self._clamp_weight(
                            float(value)
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        return {
            module: round(weight, 4)
            for module, weight in result.items()
        }

    @staticmethod
    def _clamp_weight(
        value: float,
    ) -> float:
        return round(
            max(
                MIN_WEIGHT,
                min(
                    MAX_WEIGHT,
                    float(value),
                ),
            ),
            4,
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _version_row_to_dict(
        row: sqlite3.Row,
    ) -> Dict[str, Any]:
        try:
            weights = json.loads(
                row["weights"]
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            weights = {}

        return {
            "id": row["id"],
            "weights": weights,
            "reason": row["reason"],
            "source": row["source"],
            "created_at": row["created_at"],
            "is_active": bool(
                row["is_active"]
            ),
            "rolled_back_from": row[
                "rolled_back_from"
            ],
        }


def format_weight_manager_preview(
    result: Dict[str, Any],
) -> str:
    lines = [
        "⚖️ <b>Weight Manager Preview</b>",
        "<i>Dry run — production weights unchanged</i>",
        "",
        f"Eligible: {result['eligible_count']}",
        f"Skipped: {result['skipped_count']}",
        "",
    ]

    for item in result["accepted"]:
        lines.extend([
            f"<b>{item['module']}</b>",
            (
                f"{item['old_weight']} "
                f"→ {item['new_weight']}"
            ),
            f"Change: {item['change']:+.4f}",
            f"Confidence: {item['confidence']}/100",
            f"Samples: {item['samples']}",
            "",
        ])

    if result["skipped"]:
        lines.append("<b>Skipped:</b>")

        for item in result["skipped"]:
            lines.append(
                f"• {item['module']}: "
                f"{item['decision']}"
            )

        lines.append("")

    lines.append(
        "Mode: Managed weights shadow storage"
    )

    return "\n".join(lines)
