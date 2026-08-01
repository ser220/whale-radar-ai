from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from .identity import MarketIdentity, _required_text


@dataclass(frozen=True)
class TradingInstrument:
    identity: MarketIdentity
    base_symbol: str
    quote_symbol: Optional[str]
    settlement_currency: str
    expiry: Optional[datetime]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, MarketIdentity):
            raise TypeError(
                "identity must be a MarketIdentity"
            )

        object.__setattr__(
            self,
            "base_symbol",
            _required_text(
                self.base_symbol,
                "base_symbol",
            ).upper(),
        )

        if self.quote_symbol is not None:
            object.__setattr__(
                self,
                "quote_symbol",
                _required_text(
                    self.quote_symbol,
                    "quote_symbol",
                ).upper(),
            )

        object.__setattr__(
            self,
            "settlement_currency",
            _required_text(
                self.settlement_currency,
                "settlement_currency",
            ).upper(),
        )

        if self.expiry is not None:
            if not isinstance(self.expiry, datetime):
                raise TypeError(
                    "expiry must be a datetime"
                )

            if self.expiry.tzinfo is None:
                raise ValueError(
                    "expiry must be timezone aware"
                )

            object.__setattr__(
                self,
                "expiry",
                self.expiry.astimezone(timezone.utc),
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "base_symbol": self.base_symbol,
            "quote_symbol": self.quote_symbol,
            "settlement_currency": self.settlement_currency,
            "expiry": (
                self.expiry.isoformat()
                if self.expiry is not None
                else None
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "TradingInstrument":
        if not isinstance(data, Mapping):
            raise TypeError(
                "trading instrument payload must be a mapping"
            )

        expected_fields = {
            "identity",
            "base_symbol",
            "quote_symbol",
            "settlement_currency",
            "expiry",
        }
        supplied_fields = set(data)

        unknown_fields = supplied_fields - expected_fields
        if unknown_fields:
            raise ValueError(
                "unknown fields: {0}".format(
                    ", ".join(sorted(unknown_fields))
                )
            )

        missing_fields = expected_fields - supplied_fields
        if missing_fields:
            raise ValueError(
                "missing fields: {0}".format(
                    ", ".join(sorted(missing_fields))
                )
            )

        payload = dict(data)
        payload["identity"] = MarketIdentity.from_dict(
            payload["identity"]
        )

        if payload["expiry"] is not None:
            if not isinstance(payload["expiry"], str):
                raise TypeError(
                    "expiry must be an ISO datetime string"
                )

            payload["expiry"] = datetime.fromisoformat(
                payload["expiry"].replace(
                    "Z",
                    "+00:00",
                )
            )

        return cls(**payload)
