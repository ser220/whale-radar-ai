from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.domain.prediction import Prediction
from app.engine.outcome_intelligence import (
    calculate_outcome_score,
    calculate_outcome_score_v2,
)
from app.repository.prediction_repository import PredictionRepository
from app.services.prediction_lifecycle_builder import (
    PredictionLifecycleBuilder,
)
from app.sources.binance_candle_source import (
    BinanceCandleSource,
    BinanceCandleSourceError,
)
from app.sources.candle_source import CandleSource


class PredictionReviewService:
    def __init__(
        self,
        repository: Optional[PredictionRepository] = None,
        candle_source: Optional[CandleSource] = None,
        candle_interval: str = "1h",
        candle_limit: int = 1000,
    ) -> None:
        self.repository = repository or PredictionRepository()
        self.candle_source = candle_source or BinanceCandleSource()
        self.candle_interval = candle_interval
        self.candle_limit = max(int(candle_limit), 1)

    def get_review(
        self,
        prediction_id: int,
    ) -> Optional[Dict[str, Any]]:
        prediction = self.repository.get(prediction_id)

        if prediction is None:
            return None

        outcome_v1 = self._build_outcome_v1(prediction)

        lifecycle = None
        outcome_v2 = None
        lifecycle_error = None
        candle_count = 0
        source_name = self.candle_source.source_name()

        try:
            start_time = self._parse_datetime(
                prediction.created_at
            )

            candles = self.candle_source.get_candles(
                asset=prediction.asset,
                interval=self.candle_interval,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                limit=self.candle_limit,
            )

            candle_count = len(candles)

            lifecycle = PredictionLifecycleBuilder.build(
                prediction=prediction,
                candles=candles,
                stop_price=self._extract_stop_price(
                    prediction
                ),
            )

            outcome_v2 = calculate_outcome_score_v2(
                lifecycle
            )

        except (
            BinanceCandleSourceError,
            TypeError,
            ValueError,
        ) as exc:
            lifecycle_error = str(exc)

        return {
            "prediction": prediction.to_dict(),
            "market": {
                "regime": prediction.ai_snapshot.get(
                    "market_regime",
                    {},
                ),
                "heat": prediction.ai_snapshot.get(
                    "market_heat",
                    {},
                ),
            },
            "ai": {
                "probability": prediction.ai_snapshot.get(
                    "probability",
                    {},
                ),
                "campaign": prediction.ai_snapshot.get(
                    "campaign",
                    {},
                ),
                "wallet_behaviour": (
                    prediction.ai_snapshot.get(
                        "wallet_behaviour",
                        {},
                    )
                ),
                "decision": prediction.ai_snapshot.get(
                    "decision",
                    {},
                ),
            },
            "outcome_v1": outcome_v1,
            "lifecycle": (
                lifecycle.to_dict()
                if lifecycle is not None
                else None
            ),
            "outcome_v2": outcome_v2,
            "lifecycle_source": {
                "name": source_name,
                "interval": self.candle_interval,
                "candles": candle_count,
                "error": lifecycle_error,
            },
            "learning": {
                "checked": prediction.outcome_checked,
                "target_hit": prediction.target_hit,
                "accuracy": prediction.accuracy,
                "checked_at": prediction.checked_at,
            },
            "summary": {
                "asset": prediction.asset,
                "direction": prediction.direction,
                "v1_quality": outcome_v1["label"],
                "v1_score": outcome_v1["score"],
                "v2_quality": (
                    outcome_v2["label"]
                    if outcome_v2
                    else None
                ),
                "v2_score": (
                    outcome_v2["score"]
                    if outcome_v2
                    else None
                ),
            },
        }

    @staticmethod
    def _build_outcome_v1(
        prediction: Prediction,
    ) -> Dict[str, Any]:
        evaluation_price = (
            prediction.current_price
            if prediction.current_price is not None
            else prediction.entry_price
        )

        return calculate_outcome_score(
            direction=prediction.direction,
            entry_price=prediction.entry_price,
            target_price=prediction.target_price,
            current_price=evaluation_price,
            expected_move=prediction.expected_move,
            eta=prediction.eta,
        )

    @staticmethod
    def _parse_datetime(
        value: Optional[str],
    ) -> datetime:
        if not value:
            return datetime.now(timezone.utc)

        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _extract_stop_price(
        prediction: Prediction,
    ) -> Optional[float]:
        snapshot = prediction.ai_snapshot or {}

        possible_objects = [
            snapshot.get("price_plan"),
            snapshot.get("trade_plan"),
            snapshot.get("entry_plan"),
            snapshot.get("decision"),
        ]

        possible_keys = (
            "stop_price",
            "stop",
            "sl",
            "stop_loss",
        )

        for obj in possible_objects:
            if not isinstance(obj, dict):
                continue

            for key in possible_keys:
                value = obj.get(key)

                if value is None:
                    continue

                try:
                    stop = float(value)

                    if stop > 0:
                        return stop

                except (TypeError, ValueError):
                    continue

        return None


def format_prediction_review(
    review: Optional[Dict[str, Any]],
) -> str:
    if review is None:
        return "Prediction not found."

    prediction = review["prediction"]
    learning = review["learning"]
    v1 = review["outcome_v1"]
    v2 = review.get("outcome_v2")
    lifecycle = review.get("lifecycle")
    source = review["lifecycle_source"]

    lines = [
        "🧠 <b>Prediction Review</b>",
        "",
        f"ID: {prediction['id']}",
        f"Asset: {prediction['asset']}",
        f"Direction: {prediction['direction']}",
        f"Entry: {prediction['entry_price']}",
        f"Target: {prediction['target_price']}",
        f"Stored Current: {prediction.get('current_price')}",
        f"Checked: {learning['checked']}",
        "",
        "<b>Outcome V1:</b>",
        f"Score: {v1['score']}/100",
        f"Quality: {v1['label']}",
        f"Direction: {v1['direction_score']}/40",
        f"Target: {v1['target_score']}/40",
        f"Move: {v1['move_score']}/20",
        f"Actual Move: {v1.get('actual_move', 0)}%",
        "",
        "<b>Outcome V2 — Lifecycle Shadow:</b>",
    ]

    if v2 and lifecycle:
        lines.extend([
            f"Score: {v2['score']}/100",
            f"Quality: {v2['label']}",
            f"State: {v2['state']}",
            f"Latest Price: {lifecycle['latest_price']}",
            f"Highest: {lifecycle['highest_price']}",
            f"Lowest: {lifecycle['lowest_price']}",
            f"MFE: {v2['mfe_percent']}%",
            f"MAE: {v2['mae_percent']}%",
            (
                "Target Progress: "
                f"{v2['target_progress_percent']}%"
            ),
            f"Target Touched: {v2['target_touched']}",
            f"Stop Touched: {v2['stop_touched']}",
            "",
            f"Source: {source['name']}",
            f"Interval: {source['interval']}",
            f"Candles: {source['candles']}",
            "Mode: Shadow only",
        ])
    else:
        lines.extend([
            "Lifecycle data unavailable.",
            f"Source: {source['name']}",
            f"Error: {source.get('error') or 'Unknown error'}",
        ])

    return "\n".join(lines)
