from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple

from app.domain.candle import Candle
from app.intelligence.data_sources import (
    DerivativesSnapshot,
    MarketSnapshot,
    OpenInterestSnapshot,
)

from app.domain.market import TradingInstrument


@dataclass(frozen=True)
class MarketFeed:
    instrument: TradingInstrument
    candles: Tuple[Candle, ...]
    market_snapshot: MarketSnapshot
    derivatives_snapshot: Optional[DerivativesSnapshot]
    open_interest_snapshot: Optional[OpenInterestSnapshot]
    captured_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, TradingInstrument):
            raise TypeError(
                "instrument must be a TradingInstrument"
            )

        if isinstance(
            self.candles,
            (str, bytes, bytearray),
        ):
            raise TypeError(
                "candles must contain Candle instances"
            )

        try:
            candles = tuple(self.candles)
        except TypeError as exc:
            raise TypeError(
                "candles must be an iterable of Candle instances"
            ) from exc

        if not candles:
            raise ValueError(
                "candles must not be empty"
            )

        if not all(
            isinstance(candle, Candle)
            for candle in candles
        ):
            raise TypeError(
                "candles must contain Candle instances"
            )

        object.__setattr__(
            self,
            "candles",
            candles,
        )

        if not isinstance(
            self.market_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "market_snapshot must be a MarketSnapshot"
            )

        if (
            self.derivatives_snapshot is not None
            and not isinstance(
                self.derivatives_snapshot,
                DerivativesSnapshot,
            )
        ):
            raise TypeError(
                "derivatives_snapshot must be a "
                "DerivativesSnapshot or None"
            )

        if (
            self.open_interest_snapshot is not None
            and not isinstance(
                self.open_interest_snapshot,
                OpenInterestSnapshot,
            )
        ):
            raise TypeError(
                "open_interest_snapshot must be an "
                "OpenInterestSnapshot or None"
            )

        instrument_symbol = (
            self.instrument.identity.symbol
        )

        if self.market_snapshot.symbol != instrument_symbol:
            raise ValueError(
                "market snapshot symbol must match instrument symbol"
            )

        if (
            self.derivatives_snapshot is not None
            and self.derivatives_snapshot.symbol
            != instrument_symbol
        ):
            raise ValueError(
                "derivatives snapshot symbol must match instrument symbol"
            )

        if not isinstance(self.captured_at, datetime):
            raise TypeError(
                "captured_at must be a datetime"
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at must be timezone aware"
            )

        object.__setattr__(
            self,
            "captured_at",
            self.captured_at.astimezone(
                timezone.utc
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument": self.instrument.to_dict(),
            "candles": [
                candle.to_dict()
                for candle in self.candles
            ],
            "market_snapshot": (
                self.market_snapshot.to_dict()
            ),
            "derivatives_snapshot": (
                self.derivatives_snapshot.to_dict()
                if self.derivatives_snapshot
                is not None
                else None
            ),
            "open_interest_snapshot": (
                self.open_interest_snapshot.to_dict()
                if self.open_interest_snapshot
                is not None
                else None
            ),
            "captured_at": (
                self.captured_at.isoformat()
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "MarketFeed":
        if not isinstance(data, Mapping):
            raise TypeError(
                "market feed payload must be a mapping"
            )

        expected_fields = {
            "instrument",
            "candles",
            "market_snapshot",
            "derivatives_snapshot",
            "open_interest_snapshot",
            "captured_at",
        }
        supplied_fields = set(data)

        unknown_fields = (
            supplied_fields - expected_fields
        )
        if unknown_fields:
            raise ValueError(
                "unknown fields: {0}".format(
                    ", ".join(
                        sorted(unknown_fields)
                    )
                )
            )

        missing_fields = (
            expected_fields - supplied_fields
        )
        if missing_fields:
            raise ValueError(
                "missing fields: {0}".format(
                    ", ".join(
                        sorted(missing_fields)
                    )
                )
            )

        payload = dict(data)

        payload["instrument"] = (
            TradingInstrument.from_dict(
                payload["instrument"]
            )
        )

        payload["candles"] = tuple(
            Candle(**candle)
            for candle in payload["candles"]
        )

        payload["market_snapshot"] = (
            MarketSnapshot.from_dict(
                payload["market_snapshot"]
            )
        )

        derivatives = payload[
            "derivatives_snapshot"
        ]
        payload["derivatives_snapshot"] = (
            DerivativesSnapshot.from_dict(
                derivatives
            )
            if derivatives is not None
            else None
        )

        open_interest = payload[
            "open_interest_snapshot"
        ]
        payload["open_interest_snapshot"] = (
            OpenInterestSnapshot.from_dict(
                open_interest
            )
            if open_interest is not None
            else None
        )

        captured_at = payload["captured_at"]
        if not isinstance(captured_at, str):
            raise TypeError(
                "captured_at must be an ISO datetime string"
            )

        payload["captured_at"] = (
            datetime.fromisoformat(
                captured_at.replace(
                    "Z",
                    "+00:00",
                )
            )
        )

        return cls(**payload)
