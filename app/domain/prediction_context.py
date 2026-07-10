from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


ALLOWED_TRENDS = {
    "bullish",
    "bearish",
    "neutral",
    "unknown",
}

ALLOWED_VOLATILITY = {
    "ultra-low",
    "low",
    "normal",
    "high",
    "extreme",
    "unknown",
}

ALLOWED_SESSIONS = {
    "asia",
    "london",
    "new-york",
    "overlap",
    "off-hours",
    "unknown",
}


@dataclass
class PredictionContext:
    prediction_id: int
    asset: str

    market_regime: str = "Unknown"
    market_heat: Optional[float] = None
    wallet_behaviour: str = "Unknown"

    asset_trend: str = "unknown"
    btc_trend: str = "unknown"
    eth_trend: str = "unknown"

    volatility_regime: str = "unknown"
    atr_percent: Optional[float] = None

    funding_rate: Optional[float] = None
    open_interest_change: Optional[float] = None

    session: str = "unknown"
    weekday: Optional[str] = None
    hour_utc: Optional[int] = None

    captured_at: Optional[str] = None
    source: str = "prediction-snapshot"
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    context_id: Optional[int] = None

    def __post_init__(self) -> None:
        self.prediction_id = int(
            self.prediction_id
        )

        if self.prediction_id <= 0:
            raise ValueError(
                "prediction_id must be greater than zero."
            )

        self.asset = str(
            self.asset or ""
        ).strip().upper()

        if not self.asset:
            raise ValueError(
                "asset cannot be empty."
            )

        self.market_regime = str(
            self.market_regime or "Unknown"
        ).strip()

        self.wallet_behaviour = str(
            self.wallet_behaviour or "Unknown"
        ).strip()

        self.asset_trend = self._normalize_choice(
            self.asset_trend,
            ALLOWED_TRENDS,
            "unknown",
        )

        self.btc_trend = self._normalize_choice(
            self.btc_trend,
            ALLOWED_TRENDS,
            "unknown",
        )

        self.eth_trend = self._normalize_choice(
            self.eth_trend,
            ALLOWED_TRENDS,
            "unknown",
        )

        self.volatility_regime = (
            self._normalize_choice(
                self.volatility_regime,
                ALLOWED_VOLATILITY,
                "unknown",
            )
        )

        self.session = self._normalize_choice(
            self.session,
            ALLOWED_SESSIONS,
            "unknown",
        )

        self.market_heat = self._optional_float(
            self.market_heat
        )

        if self.market_heat is not None:
            self.market_heat = max(
                0.0,
                min(
                    100.0,
                    self.market_heat,
                ),
            )

        self.atr_percent = self._optional_float(
            self.atr_percent
        )

        self.funding_rate = self._optional_float(
            self.funding_rate
        )

        self.open_interest_change = (
            self._optional_float(
                self.open_interest_change
            )
        )

        if self.hour_utc is not None:
            self.hour_utc = int(
                self.hour_utc
            )

            if not 0 <= self.hour_utc <= 23:
                raise ValueError(
                    "hour_utc must be between 0 and 23."
                )

        if not isinstance(
            self.metadata,
            dict,
        ):
            self.metadata = {}

        if self.captured_at is None:
            now = datetime.now(
                timezone.utc
            )

            self.captured_at = now.isoformat()

            if self.weekday is None:
                self.weekday = now.strftime(
                    "%A"
                )

            if self.hour_utc is None:
                self.hour_utc = now.hour

        elif self.weekday is None:
            parsed = self._parse_datetime(
                self.captured_at
            )

            if parsed is not None:
                self.weekday = parsed.strftime(
                    "%A"
                )

                if self.hour_utc is None:
                    self.hour_utc = parsed.hour

        if self.weekday is not None:
            self.weekday = str(
                self.weekday
            ).strip().title()

        self.source = str(
            self.source
            or "prediction-snapshot"
        ).strip()

    @property
    def has_market_data(self) -> bool:
        return any([
            self.market_heat is not None,
            self.atr_percent is not None,
            self.funding_rate is not None,
            self.open_interest_change is not None,
        ])

    @property
    def trend_alignment(self) -> str:
        trends = {
            self.asset_trend,
            self.btc_trend,
        }

        if (
            "unknown" in trends
            or "neutral" in trends
        ):
            return "unclear"

        if len(trends) == 1:
            return "aligned"

        return "divergent"

    @property
    def context_key(self) -> str:
        return "|".join([
            self.market_regime.lower(),
            self.volatility_regime,
            self.asset_trend,
            self.btc_trend,
            self.session,
        ])

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)

        data.update({
            "has_market_data": (
                self.has_market_data
            ),
            "trend_alignment": (
                self.trend_alignment
            ),
            "context_key": self.context_key,
        })

        return data

    @staticmethod
    def _normalize_choice(
        value: Any,
        allowed: set,
        default: str,
    ) -> str:
        normalized = str(
            value or default
        ).strip().lower()

        if normalized not in allowed:
            return default

        return normalized

    @staticmethod
    def _optional_float(
        value: Any,
    ) -> Optional[float]:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _parse_datetime(
        value: str,
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
