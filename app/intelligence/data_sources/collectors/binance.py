"""Public Binance Spot market adapter for immutable MarketSnapshot output."""

from collections.abc import Mapping
from datetime import datetime, timezone
import json
import socket
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .._validation import finite_number, positive_number, required_text
from ..enums import DataSourceCategory, DataSourceType
from ..models import MarketSnapshot
from .exchange_market import ExchangeMarketCollectorMetadata


class BinanceMarketCollectorResponseError(ValueError):
    """Raised when Binance returns an invalid market payload."""


class BinanceMarketCollectorTimeoutError(TimeoutError):
    """Raised when the public Binance request exceeds its timeout."""


class BinanceMarketCollectorTransportError(RuntimeError):
    """Raised when the public Binance request cannot be completed."""


class BinanceMarketCollector:
    """Fetch and normalize public Binance 24-hour ticker observations."""

    _ENDPOINT = "https://data-api.binance.vision/api/v3/ticker/24hr"
    _METADATA = ExchangeMarketCollectorMetadata(
        source=DataSourceType.BINANCE,
        category=DataSourceCategory.EXCHANGE,
        supported_symbols=("BTCUSDT", "ETHUSDT"),
    )

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._timeout_seconds = positive_number(
            timeout_seconds, "timeout_seconds"
        )
        if not callable(opener):
            raise TypeError("opener must be callable")
        self._opener = opener

    @property
    def metadata(self) -> ExchangeMarketCollectorMetadata:
        return self._METADATA

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    def collect(self, symbol: str) -> MarketSnapshot:
        normalized_symbol = required_text(symbol, "symbol", uppercase=True)
        if normalized_symbol not in self.metadata.supported_symbols:
            raise ValueError(
                "symbol {0} is not supported by BinanceMarketCollector".format(
                    normalized_symbol
                )
            )
        query = urlencode({"symbol": normalized_symbol})
        request = Request(
            "{0}?{1}".format(self._ENDPOINT, query),
            headers={"Accept": "application/json"},
            method="GET",
        )
        payload = self._request_payload(request)
        snapshot = self.transform(payload)
        if snapshot.symbol != normalized_symbol:
            raise BinanceMarketCollectorResponseError(
                "response symbol does not match requested symbol"
            )
        return snapshot

    def transform(self, response: Mapping[str, Any]) -> MarketSnapshot:
        if not isinstance(response, Mapping):
            raise BinanceMarketCollectorResponseError(
                "Binance response must be a mapping"
            )
        required_fields = (
            "symbol",
            "lastPrice",
            "volume",
            "priceChangePercent",
            "closeTime",
        )
        missing = [
            field for field in required_fields if field not in response
        ]
        if missing:
            raise BinanceMarketCollectorResponseError(
                "Binance response is missing fields: {0}".format(
                    ", ".join(missing)
                )
            )
        try:
            symbol = required_text(
                response["symbol"], "symbol", uppercase=True
            )
            if symbol not in self.metadata.supported_symbols:
                raise ValueError("unsupported Binance response symbol")
            price = self._response_number(response["lastPrice"], "lastPrice")
            volume = self._response_number(response["volume"], "volume")
            change = self._response_number(
                response["priceChangePercent"], "priceChangePercent"
            )
            captured_at = self._response_timestamp(response["closeTime"])
            return MarketSnapshot(
                source_category=self.metadata.category,
                source=self.metadata.source,
                symbol=symbol,
                price=price,
                volume_24h=volume,
                change_24h=change,
                captured_at=captured_at,
            )
        except (TypeError, ValueError) as error:
            raise BinanceMarketCollectorResponseError(
                "invalid Binance market response: {0}".format(error)
            ) from error

    def _request_payload(self, request: Request) -> Mapping[str, Any]:
        try:
            with self._opener(
                request, timeout=self._timeout_seconds
            ) as response:
                status = getattr(response, "status", None)
                if status is None and hasattr(response, "getcode"):
                    status = response.getcode()
                if status is not None and status != 200:
                    raise BinanceMarketCollectorTransportError(
                        "Binance public endpoint returned HTTP {0}".format(
                            status
                        )
                    )
                body = response.read()
        except (socket.timeout, TimeoutError) as error:
            raise BinanceMarketCollectorTimeoutError(
                "Binance public request timed out after {0} seconds".format(
                    self._timeout_seconds
                )
            ) from error
        except HTTPError as error:
            raise BinanceMarketCollectorTransportError(
                "Binance public endpoint returned HTTP {0}".format(error.code)
            ) from error
        except URLError as error:
            if isinstance(error.reason, (socket.timeout, TimeoutError)):
                raise BinanceMarketCollectorTimeoutError(
                    "Binance public request timed out after {0} seconds".format(
                        self._timeout_seconds
                    )
                ) from error
            raise BinanceMarketCollectorTransportError(
                "Binance public request failed"
            ) from error
        if not isinstance(body, bytes):
            raise BinanceMarketCollectorResponseError(
                "Binance response body must be bytes"
            )
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BinanceMarketCollectorResponseError(
                "Binance response body must contain valid UTF-8 JSON"
            ) from error
        if not isinstance(payload, Mapping):
            raise BinanceMarketCollectorResponseError(
                "Binance response JSON must be an object"
            )
        return payload

    @staticmethod
    def _response_number(value: Any, field_name: str) -> float:
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                raise ValueError("{0} must not be empty".format(field_name))
            try:
                value = float(normalized)
            except ValueError as error:
                raise ValueError(
                    "{0} must be numeric".format(field_name)
                ) from error
        return finite_number(value, field_name)

    @staticmethod
    def _response_timestamp(value: Any) -> datetime:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(
                "closeTime must be an integer millisecond timestamp"
            )
        if value < 0:
            raise ValueError("closeTime must not be negative")
        try:
            return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as error:
            raise ValueError(
                "closeTime is outside the supported range"
            ) from error


__all__ = [
    "BinanceMarketCollector",
    "BinanceMarketCollectorResponseError",
    "BinanceMarketCollectorTimeoutError",
    "BinanceMarketCollectorTransportError",
]
