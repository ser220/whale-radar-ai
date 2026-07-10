import json
import time
from datetime import datetime, timezone
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.domain.candle import Candle
from app.sources.candle_source import CandleSource


class BinanceCandleSourceError(RuntimeError):
    """Raised when Binance candle data cannot be retrieved or parsed."""


class BinanceCandleSource(CandleSource):
    BASE_URL = "https://data-api.binance.vision"
    KLINES_PATH = "/api/v3/klines"

    SUPPORTED_INTERVALS = {
        "1s",
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1M",
    }

    QUOTE_ASSETS = {
        "USDT",
        "USDC",
        "BTC",
        "ETH",
        "BNB",
        "FDUSD",
        "TUSD",
        "EUR",
        "TRY",
    }

    def __init__(
        self,
        quote_asset: str = "USDT",
        timeout: float = 15.0,
        pause_seconds: float = 0.15,
        base_url: str = BASE_URL,
    ) -> None:
        self.quote_asset = quote_asset.upper().strip()
        self.timeout = float(timeout)
        self.pause_seconds = max(float(pause_seconds), 0.0)
        self.base_url = base_url.rstrip("/")

        if not self.quote_asset:
            raise ValueError("quote_asset cannot be empty.")

        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

    def source_name(self) -> str:
        return "binance-public-spot"

    def get_candles(
        self,
        asset: str,
        interval: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Candle]:
        interval = str(interval).strip()

        if interval not in self.SUPPORTED_INTERVALS:
            raise ValueError(
                f"Unsupported Binance interval: {interval}"
            )

        requested_limit = int(limit)

        if requested_limit <= 0:
            return []

        start_utc = self._ensure_utc(start_time)
        end_utc = self._ensure_utc(end_time) if end_time else None

        if end_utc is not None and end_utc < start_utc:
            raise ValueError(
                "end_time cannot be earlier than start_time."
            )

        symbol = self._normalize_symbol(asset)

        candles: List[Candle] = []
        next_start_ms = self._to_milliseconds(start_utc)
        end_ms = (
            self._to_milliseconds(end_utc)
            if end_utc is not None
            else None
        )

        while len(candles) < requested_limit:
            page_limit = min(
                requested_limit - len(candles),
                1000,
            )

            page = self._request_page(
                symbol=symbol,
                interval=interval,
                start_ms=next_start_ms,
                end_ms=end_ms,
                limit=page_limit,
            )

            if not page:
                break

            parsed_page = self._parse_page(page)

            if not parsed_page:
                break

            for candle in parsed_page:
                if candle.timestamp < start_utc:
                    continue

                if end_utc is not None and candle.timestamp > end_utc:
                    continue

                candles.append(candle)

                if len(candles) >= requested_limit:
                    break

            last_open_ms = int(page[-1][0])
            new_start_ms = last_open_ms + 1

            if new_start_ms <= next_start_ms:
                break

            next_start_ms = new_start_ms

            if end_ms is not None and next_start_ms > end_ms:
                break

            if len(page) < page_limit:
                break

            if self.pause_seconds:
                time.sleep(self.pause_seconds)

        unique = {
            candle.timestamp_ms: candle
            for candle in candles
        }

        return sorted(
            unique.values(),
            key=lambda candle: candle.timestamp,
        )[:requested_limit]

    def _request_page(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: Optional[int],
        limit: int,
    ) -> list:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "limit": min(max(int(limit), 1), 1000),
        }

        if end_ms is not None:
            params["endTime"] = end_ms

        url = (
            f"{self.base_url}{self.KLINES_PATH}"
            f"?{urlencode(params)}"
        )

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Whale-Radar-AI/11",
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                payload = response.read().decode("utf-8")

        except HTTPError as exc:
            body = ""

            try:
                body = exc.read().decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                pass

            raise BinanceCandleSourceError(
                f"Binance HTTP error {exc.code}: "
                f"{body or exc.reason}"
            ) from exc

        except URLError as exc:
            raise BinanceCandleSourceError(
                f"Binance connection error: {exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise BinanceCandleSourceError(
                "Binance request timed out."
            ) from exc

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise BinanceCandleSourceError(
                "Binance returned invalid JSON."
            ) from exc

        if isinstance(data, dict):
            code = data.get("code")
            message = data.get("msg", "Unknown Binance error")

            raise BinanceCandleSourceError(
                f"Binance API error {code}: {message}"
            )

        if not isinstance(data, list):
            raise BinanceCandleSourceError(
                "Unexpected Binance response format."
            )

        return data

    @staticmethod
    def _parse_page(rows: list) -> List[Candle]:
        candles: List[Candle] = []

        for row in rows:
            if not isinstance(row, list) or len(row) < 6:
                continue

            try:
                candles.append(
                    Candle(
                        timestamp=int(row[0]),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                    )
                )
            except (TypeError, ValueError):
                continue

        return candles

    def _normalize_symbol(self, asset: str) -> str:
        symbol = (
            str(asset or "")
            .upper()
            .replace("/", "")
            .replace("-", "")
            .replace("_", "")
            .replace(" ", "")
        )

        if not symbol:
            raise ValueError("asset cannot be empty.")

        for quote in sorted(
            self.QUOTE_ASSETS,
            key=len,
            reverse=True,
        ):
            if (
                symbol.endswith(quote)
                and len(symbol) > len(quote)
            ):
                return symbol

        return f"{symbol}{self.quote_asset}"

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(
                "start_time and end_time must be datetime objects."
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @staticmethod
    def _to_milliseconds(value: datetime) -> int:
        return int(value.timestamp() * 1000)
