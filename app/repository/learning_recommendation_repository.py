import json
import sqlite3
from typing import List, Optional

from app.config import DB_PATH
from app.domain.learning_recommendation import (
    LearningRecommendation,
)


class LearningRecommendationRepository:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._init_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    module TEXT NOT NULL,
                    current_weight REAL NOT NULL,
                    suggested_change REAL NOT NULL,
                    suggested_weight REAL NOT NULL,
                    confidence REAL DEFAULT 0,
                    sample_count INTEGER DEFAULT 1,
                    average_module_score REAL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    reason TEXT NOT NULL,
                    evidence TEXT,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    applied_at TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_learning_recommendations_module
                ON learning_recommendations(module)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_learning_recommendations_status
                ON learning_recommendations(status)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_learning_recommendations_prediction
                ON learning_recommendations(prediction_id)
                """
            )

            conn.commit()

    def save(
        self,
        recommendation: LearningRecommendation,
    ) -> LearningRecommendation:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO learning_recommendations (
                    prediction_id,
                    module,
                    current_weight,
                    suggested_change,
                    suggested_weight,
                    confidence,
                    sample_count,
                    average_module_score,
                    status,
                    reason,
                    evidence,
                    created_at,
                    reviewed_at,
                    applied_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recommendation.prediction_id,
                    recommendation.module,
                    recommendation.current_weight,
                    recommendation.suggested_change,
                    recommendation.suggested_weight,
                    recommendation.confidence,
                    recommendation.sample_count,
                    recommendation.average_module_score,
                    recommendation.status,
                    recommendation.reason,
                    json.dumps(
                        recommendation.evidence,
                        ensure_ascii=False,
                    ),
                    recommendation.created_at,
                    recommendation.reviewed_at,
                    recommendation.applied_at,
                ),
            )

            conn.commit()
            recommendation.recommendation_id = cursor.lastrowid

        return recommendation

    def get(
        self,
        recommendation_id: int,
    ) -> Optional[LearningRecommendation]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM learning_recommendations
                WHERE id = ?
                """,
                (recommendation_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_domain(row)

    def list_pending(
        self,
        limit: int = 100,
    ) -> List[LearningRecommendation]:
        return self._list_by_status(
            status="pending",
            limit=limit,
        )

    def list_approved(
        self,
        limit: int = 100,
    ) -> List[LearningRecommendation]:
        return self._list_by_status(
            status="approved",
            limit=limit,
        )

    def list_by_module(
        self,
        module: str,
        limit: int = 100,
    ) -> List[LearningRecommendation]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM learning_recommendations
                WHERE module = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    module,
                    max(int(limit), 1),
                ),
            ).fetchall()

        return [
            self._row_to_domain(row)
            for row in rows
        ]

    def update_status(
        self,
        recommendation: LearningRecommendation,
    ) -> None:
        if recommendation.recommendation_id is None:
            raise ValueError(
                "recommendation_id is required for update."
            )

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE learning_recommendations
                SET status = ?,
                    reviewed_at = ?,
                    applied_at = ?
                WHERE id = ?
                """,
                (
                    recommendation.status,
                    recommendation.reviewed_at,
                    recommendation.applied_at,
                    recommendation.recommendation_id,
                ),
            )

            conn.commit()

    def approve(
        self,
        recommendation_id: int,
    ) -> Optional[LearningRecommendation]:
        recommendation = self.get(
            recommendation_id
        )

        if recommendation is None:
            return None

        recommendation.approve()
        self.update_status(recommendation)

        return recommendation

    def reject(
        self,
        recommendation_id: int,
    ) -> Optional[LearningRecommendation]:
        recommendation = self.get(
            recommendation_id
        )

        if recommendation is None:
            return None

        recommendation.reject()
        self.update_status(recommendation)

        return recommendation

    def mark_applied(
        self,
        recommendation_id: int,
    ) -> Optional[LearningRecommendation]:
        recommendation = self.get(
            recommendation_id
        )

        if recommendation is None:
            return None

        recommendation.mark_applied()
        self.update_status(recommendation)

        return recommendation

    def count_by_status(
        self,
    ) -> dict:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS total
                FROM learning_recommendations
                GROUP BY status
                """
            ).fetchall()

        return {
            row["status"]: row["total"]
            for row in rows
        }

    def _list_by_status(
        self,
        status: str,
        limit: int,
    ) -> List[LearningRecommendation]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM learning_recommendations
                WHERE status = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    status,
                    max(int(limit), 1),
                ),
            ).fetchall()

        return [
            self._row_to_domain(row)
            for row in rows
        ]

    @staticmethod
    def _row_to_domain(
        row: sqlite3.Row,
    ) -> LearningRecommendation:
        evidence = {}

        if row["evidence"]:
            try:
                evidence = json.loads(
                    row["evidence"]
                )
            except (
                TypeError,
                json.JSONDecodeError,
            ):
                evidence = {}

        return LearningRecommendation(
            recommendation_id=row["id"],
            prediction_id=row["prediction_id"],
            module=row["module"],
            current_weight=row["current_weight"],
            suggested_change=row["suggested_change"],
            confidence=row["confidence"],
            sample_count=row["sample_count"],
            average_module_score=row[
                "average_module_score"
            ],
            status=row["status"],
            reason=row["reason"],
            evidence=evidence,
            created_at=row["created_at"],
            reviewed_at=row["reviewed_at"],
            applied_at=row["applied_at"],
        )
