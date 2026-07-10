from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.domain.prediction import Prediction
from app.domain.prediction_lifecycle import PredictionLifecycle


class PredictionLifecycleBuilder:
    """
    Builds a PredictionLifecycle from a Prediction and OHLC candles.

    Expected candle fields:
        timestamp / time / open_time
        high
        low
        close

    Candle may be either:
        - dict
        - object with matching attributes

    Timestamp may be:
        - ISO datetime string
        - Unix seconds
        - Unix milliseconds
        - datetime object
    """

    @staticmethod
    def build(
        prediction: Prediction,
        candles: Iterable[Any],
        stop_price: Optional[float] = None,
    ) -> PredictionLifecycle:
        normalized = PredictionLifecycleBuilder._normalize_candles(candles)

        if not normalized:
            latest_price = (
                prediction.current_price
                if prediction.current_price is not None
                else prediction.entry_price
            )

            return PredictionLifecycle.from_prediction(
                prediction=prediction,
                latest_price=latest_price,
                highest_price=max(prediction.entry_price, latest_price),
                lowest_price=min(prediction.entry_price, latest_price),
                stop_price=stop_price,
            )

        filtered = PredictionLifecycleBuilder._filter_from_creation(
            normalized,
            prediction.created_at,
        )

        if not filtered:
            filtered = normalized

        highest_candle = max(
            filtered,
            key=lambda candle: candle["high"],
        )
        lowest_candle = min(
            filtered,
            key=lambda candle: candle["low"],
        )
        latest_candle = max(
            filtered,
            key=lambda candle: candle["timestamp_sort"],
        )

        lifecycle = PredictionLifecycle(
            prediction_id=prediction.id or 0,
            asset=prediction.asset,
            direction=prediction.direction,
            entry_price=prediction.entry_price,
            target_price=prediction.target_price,
            latest_price=latest_candle["close"],
            highest_price=highest_candle["high"],
            lowest_price=lowest_candle["low"],
            created_at=prediction.created_at,
            updated_at=latest_candle["timestamp"],
            stop_price=stop_price,
            highest_at=highest_candle["timestamp"],
            lowest_at=lowest_candle["timestamp"],
        )

        lifecycle.target_touched_at = (
            PredictionLifecycleBuilder._find_target_touch(
                prediction=prediction,
                candles=filtered,
            )
        )

        lifecycle.stop_touched_at = (
            PredictionLifecycleBuilder._find_stop_touch(
                prediction=prediction,
                candles=filtered,
                stop_price=stop_price,
            )
        )

        return lifecycle

    @staticmethod
    def _normalize_candles(
        candles: Iterable[Any],
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []

        for candle in candles or []:
            timestamp_raw = PredictionLifecycleBuilder._read_value(
                candle,
                "timestamp",
                "time",
                "open_time",
                "openTime",
                "ts",
            )
            high_raw = PredictionLifecycleBuilder._read_value(
                candle,
                "high",
                "h",
            )
            low_raw = PredictionLifecycleBuilder._read_value(
                candle,
                "low",
                "l",
            )
            close_raw = PredictionLifecycleBuilder._read_value(
                candle,
                "close",
                "c",
            )

            if (
                timestamp_raw is None
                or high_raw is None
                or low_raw is None
                or close_raw is None
            ):
                continue

            try:
                high = float(high_raw)
                low = float(low_raw)
                close = float(close_raw)
                timestamp = (
                    PredictionLifecycleBuilder._normalize_timestamp(
                        timestamp_raw
                    )
                )
            except (TypeError, ValueError):
                continue

            if high <= 0 or low <= 0 or close <= 0:
                continue

            if high < low:
                continue

            normalized.append({
                "timestamp": timestamp.isoformat(),
                "timestamp_sort": timestamp.timestamp(),
                "high": high,
                "low": low,
                "close": close,
            })

        normalized.sort(
            key=lambda candle: candle["timestamp_sort"]
        )

        return normalized

    @staticmethod
    def _read_value(
        candle: Any,
        *names: str,
    ) -> Any:
        if isinstance(candle, dict):
            for name in names:
                if name in candle:
                    return candle[name]
            return None

        for name in names:
            if hasattr(candle, name):
                return getattr(candle, name)

        return None

    @staticmethod
    def _normalize_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            result = value

        elif isinstance(value, (int, float)):
            numeric = float(value)

            # Convert milliseconds to seconds.
            if numeric > 10_000_000_000:
                numeric /= 1000

            result = datetime.fromtimestamp(
                numeric,
                tz=timezone.utc,
            )

        else:
            text = str(value).strip()

            if text.isdigit():
                return PredictionLifecycleBuilder._normalize_timestamp(
                    int(text)
                )

            result = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )

        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)

        return result.astimezone(timezone.utc)

    @staticmethod
    def _filter_from_creation(
        candles: List[Dict[str, Any]],
        created_at: Optional[str],
    ) -> List[Dict[str, Any]]:
        if not created_at:
            return candles

        try:
            created = (
                PredictionLifecycleBuilder._normalize_timestamp(
                    created_at
                )
            )
        except (TypeError, ValueError):
            return candles

        created_ts = created.timestamp()

        return [
            candle
            for candle in candles
            if candle["timestamp_sort"] >= created_ts
        ]

    @staticmethod
    def _find_target_touch(
        prediction: Prediction,
        candles: List[Dict[str, Any]],
    ) -> Optional[str]:
        for candle in candles:
            if (
                prediction.direction == "bullish"
                and candle["high"] >= prediction.target_price
            ):
                return candle["timestamp"]

            if (
                prediction.direction == "bearish"
                and candle["low"] <= prediction.target_price
            ):
                return candle["timestamp"]

        return None

    @staticmethod
    def _find_stop_touch(
        prediction: Prediction,
        candles: List[Dict[str, Any]],
        stop_price: Optional[float],
    ) -> Optional[str]:
        if stop_price is None:
            return None

        stop = float(stop_price)

        for candle in candles:
            if (
                prediction.direction == "bullish"
                and candle["low"] <= stop
            ):
                return candle["timestamp"]

            if (
                prediction.direction == "bearish"
                and candle["high"] >= stop
            ):
                return candle["timestamp"]

        return None
