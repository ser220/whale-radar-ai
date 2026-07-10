from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from app.domain.prediction import Prediction
from app.domain.prediction_context import (
    PredictionContext,
)
from app.repository.prediction_repository import (
    PredictionRepository,
)


class PredictionContextBuilder:
    """
    Builds PredictionContext from a stored Prediction
    and its AI snapshot.

    Current stage:
    - uses existing prediction.ai_snapshot;
    - does not call external market APIs;
    - missing fields remain unknown / None;
    - does not save automatically.
    """

    def __init__(
        self,
        prediction_repository: Optional[
            PredictionRepository
        ] = None,
    ) -> None:
        self.prediction_repository = (
            prediction_repository
            or PredictionRepository()
        )

    def build(
        self,
        prediction_id: int,
    ) -> Optional[PredictionContext]:
        prediction = self.prediction_repository.get(
            int(prediction_id)
        )

        if prediction is None:
            return None

        return self.build_from_prediction(
            prediction
        )

    def build_from_prediction(
        self,
        prediction: Prediction,
    ) -> PredictionContext:
        snapshot = (
            prediction.ai_snapshot
            if isinstance(
                prediction.ai_snapshot,
                dict,
            )
            else {}
        )

        captured_at = (
            prediction.created_at
            or datetime.now(
                timezone.utc
            ).isoformat()
        )

        market_regime = self._first_text(
            snapshot,
            paths=[
                ("market_regime",),
                ("regime",),
                ("market", "regime"),
                ("context", "market_regime"),
                ("market_context", "regime"),
            ],
            default="Unknown",
        )

        market_heat = self._first_number(
            snapshot,
            paths=[
                ("market_heat",),
                ("heat",),
                ("market", "heat"),
                ("context", "market_heat"),
                ("market_context", "heat"),
            ],
        )

        wallet_behaviour = self._first_text(
            snapshot,
            paths=[
                ("wallet_behaviour",),
                ("wallet_behavior",),
                ("wallet_rank",),
                ("wallet_ai",),
                ("wallet", "behaviour"),
                ("wallet", "behavior"),
                ("wallet", "classification"),
            ],
            default="Unknown",
        )

        asset_trend = self._normalize_trend(
            self._first_value(
                snapshot,
                paths=[
                    ("asset_trend",),
                    ("trend",),
                    ("asset_ai", "trend"),
                    ("technical", "trend"),
                    ("market_context", "asset_trend"),
                ],
            ),
            fallback=prediction.direction,
        )

        btc_trend = self._normalize_trend(
            self._first_value(
                snapshot,
                paths=[
                    ("btc_trend",),
                    ("btc", "trend"),
                    ("market_context", "btc_trend"),
                    ("context", "btc_trend"),
                ],
            )
        )

        eth_trend = self._normalize_trend(
            self._first_value(
                snapshot,
                paths=[
                    ("eth_trend",),
                    ("eth", "trend"),
                    ("market_context", "eth_trend"),
                    ("context", "eth_trend"),
                ],
            )
        )

        atr_percent = self._first_number(
            snapshot,
            paths=[
                ("atr_percent",),
                ("atr_pct",),
                ("volatility", "atr_percent"),
                ("technical", "atr_percent"),
            ],
        )

        volatility_regime = self._normalize_volatility(
            self._first_value(
                snapshot,
                paths=[
                    ("volatility_regime",),
                    ("volatility", "regime"),
                    ("market_context", "volatility"),
                    ("context", "volatility_regime"),
                ],
            ),
            atr_percent=atr_percent,
        )

        funding_rate = self._first_number(
            snapshot,
            paths=[
                ("funding_rate",),
                ("funding",),
                ("derivatives", "funding_rate"),
                ("market_context", "funding_rate"),
            ],
        )

        open_interest_change = self._first_number(
            snapshot,
            paths=[
                ("open_interest_change",),
                ("oi_change",),
                ("open_interest", "change"),
                ("derivatives", "open_interest_change"),
                ("market_context", "oi_change"),
            ],
        )

        session = self._normalize_session(
            self._first_value(
                snapshot,
                paths=[
                    ("session",),
                    ("market_session",),
                    ("context", "session"),
                    ("market_context", "session"),
                ],
            ),
            captured_at=captured_at,
        )

        pressure = self._first_text(
            snapshot,
            paths=[
                ("pressure",),
                ("whale_pressure",),
                ("market", "pressure"),
            ],
            default="Unknown",
        )

        institutional_score = self._first_number(
            snapshot,
            paths=[
                ("institutional_score",),
                ("institutional", "score"),
                ("scores", "institutional"),
            ],
        )

        metadata = {
            "prediction_direction": prediction.direction,
            "entry_price": prediction.entry_price,
            "target_price": prediction.target_price,
            "expected_move": prediction.expected_move,
            "eta": prediction.eta,
            "pressure": pressure,
            "institutional_score": institutional_score,
            "snapshot_keys": sorted(
                str(key)
                for key in snapshot.keys()
            ),
        }

        return PredictionContext(
            prediction_id=int(prediction.id),
            asset=prediction.asset,
            market_regime=market_regime,
            market_heat=market_heat,
            wallet_behaviour=wallet_behaviour,
            asset_trend=asset_trend,
            btc_trend=btc_trend,
            eth_trend=eth_trend,
            volatility_regime=volatility_regime,
            atr_percent=atr_percent,
            funding_rate=funding_rate,
            open_interest_change=open_interest_change,
            session=session,
            captured_at=captured_at,
            source="ai-snapshot",
            metadata=metadata,
        )

    @classmethod
    def _first_value(
        cls,
        data: Dict[str, Any],
        paths: Iterable[tuple],
    ) -> Any:
        for path in paths:
            value = cls._get_path(
                data,
                path,
            )

            if value is not None:
                return value

        return None


    @classmethod
    def _first_text(
        cls,
        data: Dict[str, Any],
        paths: Iterable[tuple],
        default: str,
    ) -> str:
        value = cls._first_value(
            data,
            paths,
        )

        if isinstance(value, dict):
            for key in (
                "regime",
                "behaviour",
                "behavior",
                "name",
                "label",
                "state",
                "classification",
                "type",
                "bias",
                "value",
            ):
               
                nested = value.get(key)

                if nested is not None:
                    value = nested
                    break

        text = str(
            value or ""
        ).strip()

        return text if text else default

    @classmethod
    def _first_number(
        cls,
        data: Dict[str, Any],
        paths: Iterable[tuple],
    ) -> Optional[float]:
        value = cls._first_value(
            data,
            paths,
        )

        if isinstance(value, dict):
            for key in (
                "score",
                "value",
                "percent",
                "rate",
                "change",
            ):
                if key in value:
                    value = value[key]
                    break

        return cls._to_number(value)

    @staticmethod
    def _get_path(
        data: Dict[str, Any],
        path: tuple,
    ) -> Any:
        current: Any = data

        for key in path:
            if not isinstance(
                current,
                dict,
            ):
                return None

            if key not in current:
                return None

            current = current[key]

        return current

    @staticmethod
    def _to_number(
        value: Any,
    ) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, str):
            normalized = (
                value.strip()
                .replace("%", "")
                .replace(",", "")
            )

            if not normalized:
                return None

            value = normalized

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _normalize_trend(
        value: Any,
        fallback: Optional[str] = None,
    ) -> str:
        text = str(
            value or fallback or ""
        ).lower().strip()

        bullish_words = (
            "bullish",
            "bull",
            "uptrend",
            "up",
            "long",
            "accumulation",
        )

        bearish_words = (
            "bearish",
            "bear",
            "downtrend",
            "down",
            "short",
            "distribution",
        )

        neutral_words = (
            "neutral",
            "sideways",
            "range",
            "ranging",
            "flat",
        )

        if any(
            word in text
            for word in bullish_words
        ):
            return "bullish"

        if any(
            word in text
            for word in bearish_words
        ):
            return "bearish"

        if any(
            word in text
            for word in neutral_words
        ):
            return "neutral"

        return "unknown"

    @staticmethod
    def _normalize_volatility(
        value: Any,
        atr_percent: Optional[float],
    ) -> str:
        text = str(
            value or ""
        ).lower().strip()

        if "extreme" in text:
            return "extreme"

        if "high" in text:
            return "high"

        if "normal" in text or "medium" in text:
            return "normal"

        if "ultra" in text:
            return "ultra-low"

        if "low" in text:
            return "low"

        if atr_percent is None:
            return "unknown"

        atr = abs(
            float(atr_percent)
        )

        if atr >= 5.0:
            return "extreme"

        if atr >= 2.0:
            return "high"

        if atr >= 0.8:
            return "normal"

        if atr >= 0.3:
            return "low"

        return "ultra-low"

    @classmethod
    def _normalize_session(
        cls,
        value: Any,
        captured_at: str,
    ) -> str:
        text = str(
            value or ""
        ).lower().strip()

        if "overlap" in text:
            return "overlap"

        if "new" in text or "ny" in text:
            return "new-york"

        if "london" in text or "europe" in text:
            return "london"

        if "asia" in text or "tokyo" in text:
            return "asia"

        parsed = cls._parse_datetime(
            captured_at
        )

        if parsed is None:
            return "unknown"

        hour = parsed.hour

        if 12 <= hour < 16:
            return "overlap"

        if 7 <= hour < 12:
            return "london"

        if 16 <= hour < 21:
            return "new-york"

        if 0 <= hour < 7:
            return "asia"

        return "off-hours"

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> Optional[datetime]:
        try:
            normalized = str(value).replace(
                "Z",
                "+00:00",
            )

            parsed = datetime.fromisoformat(
                normalized
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        except (
            TypeError,
            ValueError,
        ):
            return None


def format_prediction_context(
    context: Optional[PredictionContext],
) -> str:
    if context is None:
        return (
            "🌍 <b>Prediction Context</b>\n\n"
            "Prediction was not found."
        )

    return "\n".join([
        "🌍 <b>Prediction Context</b>",
        "",
        f"Prediction ID: {context.prediction_id}",
        f"Asset: {context.asset}",
        f"Regime: {context.market_regime}",
        f"Market Heat: {context.market_heat}",
        f"Wallet: {context.wallet_behaviour}",
        f"Asset Trend: {context.asset_trend}",
        f"BTC Trend: {context.btc_trend}",
        f"ETH Trend: {context.eth_trend}",
        (
            "Volatility: "
            f"{context.volatility_regime}"
        ),
        f"ATR: {context.atr_percent}",
        f"Funding: {context.funding_rate}",
        (
            "Open Interest Change: "
            f"{context.open_interest_change}"
        ),
        f"Session: {context.session}",
        f"Weekday: {context.weekday}",
        f"Hour UTC: {context.hour_utc}",
        (
            "Trend Alignment: "
            f"{context.trend_alignment}"
        ),
        f"Context Key: {context.context_key}",
        "",
        f"Source: {context.source}",
    ])
