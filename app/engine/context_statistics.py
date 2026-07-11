import sqlite3
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional

from app.config import DB_PATH


MIN_WATCH_SAMPLES = 5
MIN_READY_SAMPLES = 20
MIN_DIRECTION_SHARE = 70.0


class ContextStatisticsEngine:
    """
    Aggregates learning recommendations by prediction context.

    Joins:
    - prediction_context
    - learning_recommendations

    Shadow only:
    - does not change weights;
    - does not approve recommendations;
    - only describes module performance by context.
    """

    def __init__(
        self,
        db_path: str = DB_PATH,
    ) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def build(
        self,
        context_key: Optional[str] = None,
        module: Optional[str] = None,
        limit: int = 5000,
        exclude_prediction_id: Optional[int] = None,
        market_type: Optional[str] = None,
        execution_exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_rows(
            limit=limit,
            exclude_prediction_id=exclude_prediction_id,
            market_type=market_type,
            execution_exchange=execution_exchange,
        )

        grouped: Dict[
            tuple,
            List[sqlite3.Row]
        ] = defaultdict(list)

        for row in rows:
            key = self._context_key(row)

            if (
                context_key is not None
                and key != context_key
            ):
                continue

            row_module = str(
                row["module"] or ""
            ).strip()

            if (
                module is not None
                and row_module != module
            ):
                continue

            grouped[
                (
                    key,
                    row_module,
                )
            ].append(row)

        result: List[Dict[str, Any]] = []

        for (
            key,
            row_module,
        ), items in grouped.items():
            result.append(
                self._build_group(
                    context_key=key,
                    module=row_module,
                    rows=items,
                )
            )

        return sorted(
            result,
            key=lambda item: (
                -item["samples"],
                item["context_key"],
                item["module"],
            ),
        )

    def _load_rows(
        self,
        limit: int,
        exclude_prediction_id: Optional[int] = None,
        market_type: Optional[str] = None,
        execution_exchange: Optional[str] = None,
    ) -> List[sqlite3.Row]:
        query = """
            SELECT
                pc.prediction_id,
                pc.asset,
                pc.market_type,
                pc.execution_exchange,
                pc.instrument,
                pc.market_regime,
                pc.market_heat,
                pc.wallet_behaviour,
                pc.asset_trend,
                pc.btc_trend,
                pc.eth_trend,
                pc.volatility_regime,
                pc.atr_percent,
                pc.funding_rate,
                pc.open_interest_change,
                pc.session,
                pc.weekday,
                pc.hour_utc,
                pc.captured_at,

                lr.id AS recommendation_id,
                lr.module,
                lr.current_weight,
                lr.suggested_change,
                lr.suggested_weight,
                lr.confidence,
                lr.sample_count,
                lr.average_module_score,
                lr.status,
                lr.created_at AS recommendation_created_at

            FROM prediction_context AS pc

            INNER JOIN learning_recommendations AS lr
                ON lr.prediction_id = pc.prediction_id
        """

        parameters = []
        conditions = []

        if exclude_prediction_id is not None:
            conditions.append(
                "pc.prediction_id != ?"
            )
            parameters.append(
                int(exclude_prediction_id)
            )

        if market_type is not None:
            conditions.append(
                "LOWER(COALESCE(pc.market_type, 'spot')) = ?"
            )
            parameters.append(
                str(market_type).strip().lower()
            )

        if execution_exchange is not None:
            conditions.append(
                "LOWER(COALESCE(pc.execution_exchange, 'unknown')) = ?"
            )
            parameters.append(
                str(execution_exchange).strip().lower()
            )

        if conditions:
            query += (
                "\nWHERE "
                + " AND ".join(conditions)
            )

        query += """
            ORDER BY lr.id DESC
            LIMIT ?
        """

        parameters.append(
            max(int(limit), 1)
        )

        with self._connect() as conn:
            rows = conn.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return list(rows)
    @classmethod
    def _build_group(
        cls,
        context_key: str,
        module: str,
        rows: List[sqlite3.Row],
    ) -> Dict[str, Any]:
        scores = [
            float(row["average_module_score"])
            for row in rows
            if row["average_module_score"]
            is not None
        ]

        confidences = [
            float(row["confidence"] or 0.0)
            for row in rows
        ]

        changes = [
            float(
                row["suggested_change"]
                or 0.0
            )
            for row in rows
        ]

        increases = sum(
            change > 0
            for change in changes
        )

        decreases = sum(
            change < 0
            for change in changes
        )

        holds = sum(
            change == 0
            for change in changes
        )

        samples = len(rows)

        increase_share = cls._share(
            increases,
            samples,
        )

        decrease_share = cls._share(
            decreases,
            samples,
        )

        hold_share = cls._share(
            holds,
            samples,
        )

        dominant_direction = "hold"
        dominant_share = hold_share

        shares = {
            "increase": increase_share,
            "decrease": decrease_share,
            "hold": hold_share,
        }

        dominant_direction = max(
            shares,
            key=shares.get,
        )

        dominant_share = shares[
            dominant_direction
        ]

        average_change = (
            mean(changes)
            if changes
            else 0.0
        )

        current_weight = float(
            rows[0]["current_weight"]
            or 1.0
        )

        suggested_weight = max(
            0.10,
            min(
                2.00,
                current_weight
                + average_change,
            ),
        )

        first = rows[0]

        status = cls._status(
            samples=samples,
            dominant_share=dominant_share,
        )

        return {
            "context_key": context_key,
            "module": module,
            "samples": samples,

            "market_type": (
                first["market_type"]
                or "spot"
            ),
            "execution_exchange": (
                first["execution_exchange"]
                or "unknown"
            ),
            "instrument": first["instrument"],

            "market_regime": first[
                "market_regime"
            ],
            "volatility_regime": first[
                "volatility_regime"
            ],
            "asset_trend": first[
                "asset_trend"
            ],
            "btc_trend": first[
                "btc_trend"
            ],
            "session": first["session"],

            "average_score": (
                round(
                    mean(scores),
                    2,
                )
                if scores
                else None
            ),

            "average_confidence": round(
                mean(confidences),
                2,
            ),

            "average_change": round(
                average_change,
                4,
            ),

            "increase_count": increases,
            "decrease_count": decreases,
            "hold_count": holds,

            "increase_share": increase_share,
            "decrease_share": decrease_share,
            "hold_share": hold_share,

            "dominant_direction": (
                dominant_direction
            ),
            "dominant_share": (
                dominant_share
            ),

            "current_weight": round(
                current_weight,
                4,
            ),
            "suggested_weight": round(
                suggested_weight,
                4,
            ),

            "status": status,
            "ready_for_review": (
                status == "READY"
            ),

            "prediction_ids": sorted({
                int(row["prediction_id"])
                for row in rows
            }),

            "mode": "Shadow only",
        }

    @staticmethod
    def _context_key(
        row: sqlite3.Row,
    ) -> str:
        values = [
            row["market_type"],
            row["execution_exchange"],
            row["market_regime"],
            row["volatility_regime"],
            row["asset_trend"],
            row["btc_trend"],
            row["session"],
        ]

        normalized = [
            str(
                value
                if value is not None
                else "unknown"
            )
            .strip()
            .lower()
            or "unknown"
            for value in values
        ]

        return "|".join(normalized)

    @staticmethod
    def _share(
        count: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return round(
            count / total * 100,
            2,
        )

    @staticmethod
    def _status(
        samples: int,
        dominant_share: float,
    ) -> str:
        if (
            samples >= MIN_READY_SAMPLES
            and dominant_share
            >= MIN_DIRECTION_SHARE
        ):
            return "READY"

        if samples >= MIN_WATCH_SAMPLES:
            return "WATCH"

        return "COLLECTING"


def format_context_statistics(
    rows: List[Dict[str, Any]],
    max_groups: int = 20,
) -> str:
    if not rows:
        return (
            "🌍 <b>Context Statistics</b>\n\n"
            "No joined context-learning data yet.\n"
            "Mode: Shadow only"
        )

    lines = [
        "🌍 <b>Context Statistics</b>",
        "<i>Shadow only — no contextual weights applied</i>",
        "",
    ]

    current_context = None
    shown_groups = 0

    for row in rows:
        if shown_groups >= max_groups:
            break

        if (
            row["context_key"]
            != current_context
        ):
            current_context = row[
                "context_key"
            ]

            lines.extend([
                "────────────",
                f"<b>{current_context}</b>",
                (
                    f"{row['market_type']} | "
                    f"{row['execution_exchange']} | "
                    f"{row['market_regime']} | "
                    f"{row['volatility_regime']} | "
                    f"{row['session']}"
                ),
                "",
            ])

        lines.extend([
            f"<b>{row['module']}</b>",
            f"Samples: {row['samples']}",
            (
                "Average Score: "
                f"{row['average_score']}"
            ),
            (
                "Average Confidence: "
                f"{row['average_confidence']}"
            ),
            (
                "Average Change: "
                f"{row['average_change']:+.4f}"
            ),
            (
                "Dominant: "
                f"{row['dominant_direction']} "
                f"({row['dominant_share']}%)"
            ),
            (
                "Weight: "
                f"{row['current_weight']} "
                f"→ {row['suggested_weight']}"
            ),
            f"Status: {row['status']}",
            "",
        ])

        shown_groups += 1

    if len(rows) > shown_groups:
        lines.append(
            f"... and "
            f"{len(rows) - shown_groups} "
            f"more groups"
        )
        lines.append("")

    lines.append(
        "Mode: Shadow only"
    )

    return "\n".join(lines)
