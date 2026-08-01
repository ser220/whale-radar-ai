from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .enums import InstrumentType, MarketType


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "{0} must be a string".format(field_name)
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            "{0} must not be empty".format(field_name)
        )

    return normalized


@dataclass(frozen=True)
class MarketIdentity:
    market_type: MarketType
    instrument_type: InstrumentType
    symbol: str
    venue: str
    currency: str
    timezone: str

    def __post_init__(self) -> None:
        if not isinstance(self.market_type, MarketType):
            raise TypeError(
                "market_type must be a MarketType"
            )

        if not isinstance(
            self.instrument_type,
            InstrumentType,
        ):
            raise TypeError(
                "instrument_type must be an InstrumentType"
            )

        for field_name in (
            "symbol",
            "venue",
            "currency",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name),
                    field_name,
                ).upper(),
            )

        object.__setattr__(
            self,
            "timezone",
            _required_text(
                self.timezone,
                "timezone",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_type": self.market_type.value,
            "instrument_type": self.instrument_type.value,
            "symbol": self.symbol,
            "venue": self.venue,
            "currency": self.currency,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "MarketIdentity":
        if not isinstance(data, Mapping):
            raise TypeError(
                "market identity payload must be a mapping"
            )

        expected_fields = {
            "market_type",
            "instrument_type",
            "symbol",
            "venue",
            "currency",
            "timezone",
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
        payload["market_type"] = MarketType(
            payload["market_type"]
        )
        payload["instrument_type"] = InstrumentType(
            payload["instrument_type"]
        )

        return cls(**payload)
