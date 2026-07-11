import json
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BybitPerpetualFundingError(RuntimeError):
    """Raised when Bybit perpetual funding data cannot be loaded."""


class BybitPerpetualFundingSnapshotService:
    """
    Public read-only Bybit linear perpetual funding source.

    Provides:
    - current funding rate;
    - funding history;
    - mark, index and last prices;
    - next funding time;
    - basis;
    - open interest snapshot;
    - funding trend and crowding assessment.

    No API key.
    No account access.
    No order placement.
    """

    BASE_URL = "https://api.bybit.com"

    QUOTE_ASSETS = (
        "USDT",
        "USDC",
    )

    def __init__(
        self,
        quote_asset: str = "USDT",
        timeout: float = 12.0,
        history_limit: int = 24,
    ) -> None:
        self.quote_asset = str(
            quote_asset or "USDT"
        ).strip().upper()

        self.timeout = max(
            float(timeout),
            1.0,
        )

        self.history_limit = max(
            1,
            min(
                int(history_limit),
                200,
            ),
        )

        if self.quote_asset not in self.QUOTE_ASSETS:
            raise ValueError(
                "quote_asset must be USDT or USDC."
            )

    def build(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        symbol = self._normalize_symbol(
            asset
        )

        captured_at = datetime.now(
            timezone.utc
        )

        ticker_payload = self._request_json(
            path="/v5/market/tickers",
            parameters={
                "category": "linear",
                "symbol": symbol,
            },
        )

        history_payload = self._request_json(
            path="/v5/market/funding/history",
            parameters={
                "category": "linear",
                "symbol": symbol,
                "limit": self.history_limit,
            },
        )

        instrument_payload = self._request_json(
            path="/v5/market/instruments-info",
            parameters={
                "category": "linear",
                "symbol": symbol,
            },
        )

        ticker_rows = self._result_rows(
            ticker_payload
        )

        history_rows = self._result_rows(
            history_payload
        )

        instrument_rows = self._result_rows(
            instrument_payload
        )

        if not ticker_rows:
            raise BybitPerpetualFundingError(
                f"No ticker data for {symbol}."
            )

        ticker = ticker_rows[0]

        instrument = (
            instrument_rows[0]
            if instrument_rows
            else {}
        )

        current_rate = self._number(
            ticker.get("fundingRate")
        )

        current_percent = (
            current_rate * 100.0
        )

        mark_price = self._number(
            ticker.get("markPrice")
        )

        index_price = self._number(
            ticker.get("indexPrice")
        )

        last_price = self._number(
            ticker.get("lastPrice")
        )

        open_interest = self._number(
            ticker.get("openInterest")
        )

        open_interest_value = self._number(
            ticker.get("openInterestValue")
        )

        next_funding_ms = self._integer(
            ticker.get("nextFundingTime")
        )

        funding_interval_hours = (
            self._first_integer(
                ticker,
                instrument,
                keys=(
                    "fundingIntervalHour",
                    "fundingInterval",
                ),
            )
        )

        history = self._parse_history(
            history_rows
        )

        rates = [
            item["funding_rate"]
            for item in history
        ]

        average_rate = (
            mean(rates)
            if rates
            else current_rate
        )

        minimum_rate = (
            min(rates)
            if rates
            else current_rate
        )

        maximum_rate = (
            max(rates)
            if rates
            else current_rate
        )

        positive_periods = sum(
            rate > 0
            for rate in rates
        )

        negative_periods = sum(
            rate < 0
            for rate in rates
        )

        zero_periods = sum(
            rate == 0
            for rate in rates
        )

        basis_percent = self._basis_percent(
            mark_price=mark_price,
            index_price=index_price,
        )

        funding_trend = self._funding_trend(
            rates
        )

        funding_state = self._funding_state(
            current_percent
        )

        crowding = self._crowding(
            current_percent=current_percent,
            average_percent=(
                average_rate * 100.0
            ),
            trend=funding_trend,
        )

        seconds_to_funding = None

        if next_funding_ms > 0:
            seconds_to_funding = max(
                (
                    next_funding_ms / 1000.0
                    - captured_at.timestamp()
                ),
                0.0,
            )

        return {
            "status": "completed",
            "exchange": "Bybit",
            "exchange_key": "bybit",
            "symbol": symbol,
            "instrument": symbol,
            "instrument_type": "PERPETUAL",
            "category": "linear",
            "base_asset": self._base_asset(
                symbol
            ),
            "quote_asset": self._quote_asset(
                symbol
            ),
            "mark_price": mark_price,
            "index_price": index_price,
            "last_price": last_price,
            "basis_percent": round(
                basis_percent,
                4,
            ),
            "open_interest": (
                open_interest
            ),
            "open_interest_value": (
                open_interest_value
            ),
            "current_funding_rate": (
                current_rate
            ),
            "current_funding_percent": round(
                current_percent,
                6,
            ),
            "average_funding_rate": (
                average_rate
            ),
            "average_funding_percent": round(
                average_rate * 100.0,
                6,
            ),
            "minimum_funding_percent": round(
                minimum_rate * 100.0,
                6,
            ),
            "maximum_funding_percent": round(
                maximum_rate * 100.0,
                6,
            ),
            "funding_state": funding_state,
            "funding_trend": funding_trend,
            "crowding": crowding,
            "positive_periods": (
                positive_periods
            ),
            "negative_periods": (
                negative_periods
            ),
            "zero_periods": zero_periods,
            "history_samples": len(
                history
            ),
            "funding_interval_hours": (
                funding_interval_hours
            ),
            "funding_interval_seconds": (
                funding_interval_hours * 3600
                if funding_interval_hours > 0
                else 0
            ),
            "next_funding_at": (
                self._timestamp_ms(
                    next_funding_ms
                )
            ),
            "seconds_to_funding": (
                round(
                    seconds_to_funding,
                    1,
                )
                if seconds_to_funding
                is not None
                else None
            ),
            "history": history,
            "captured_at": (
                captured_at.isoformat()
            ),
            "source": (
                "bybit-v5-public-linear"
            ),
            "mode": "Live read-only",
            "error": None,
        }

    def _request_json(
        self,
        path: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        query = urlencode(
            parameters
        )

        url = (
            f"{self.BASE_URL}{path}"
            f"?{query}"
        )

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "Whale-Radar-AI/15"
                ),
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                payload = (
                    response.read()
                    .decode("utf-8")
                )

        except HTTPError as exc:
            body = ""

            try:
                body = (
                    exc.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )
            except Exception:
                pass

            raise BybitPerpetualFundingError(
                f"Bybit HTTP error "
                f"{exc.code}: "
                f"{body or exc.reason}"
            ) from exc

        except URLError as exc:
            raise BybitPerpetualFundingError(
                "Bybit connection error: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise BybitPerpetualFundingError(
                "Bybit request timed out."
            ) from exc

        try:
            data = json.loads(
                payload
            )

        except json.JSONDecodeError as exc:
            raise BybitPerpetualFundingError(
                "Bybit returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise BybitPerpetualFundingError(
                "Unexpected Bybit response."
            )

        return_code = self._integer(
            data.get("retCode")
        )

        if return_code != 0:
            raise BybitPerpetualFundingError(
                f"Bybit API error "
                f"{return_code}: "
                f"{data.get('retMsg')}"
            )

        return data

    @staticmethod
    def _result_rows(
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        result = payload.get("result")

        if not isinstance(result, dict):
            return []

        rows = result.get("list")

        if not isinstance(rows, list):
            return []

        return [
            row
            for row in rows
            if isinstance(row, dict)
        ]

    @classmethod
    def _parse_history(
        cls,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result = []

        for row in rows:
            rate = cls._number(
                row.get("fundingRate")
            )

            timestamp_ms = cls._integer(
                row.get(
                    "fundingRateTimestamp"
                )
            )

            result.append({
                "funding_time": (
                    cls._timestamp_ms(
                        timestamp_ms
                    )
                ),
                "funding_time_ms": (
                    timestamp_ms
                ),
                "funding_rate": rate,
                "funding_percent": round(
                    rate * 100.0,
                    6,
                ),
            })

        result.sort(
            key=lambda item: (
                item["funding_time_ms"]
            )
        )

        return result

    def _normalize_symbol(
        self,
        asset: str,
    ) -> str:
        value = str(
            asset or ""
        ).strip().upper()

        value = (
            value.replace("/", "")
            .replace("-", "")
            .replace("_", "")
            .replace(" ", "")
            .replace("PERPETUAL", "")
            .replace("PERP", "")
            .replace("SWAP", "")
        )

        if not value:
            raise ValueError(
                "Asset cannot be empty."
            )

        for quote_asset in self.QUOTE_ASSETS:
            if (
                value.endswith(
                    quote_asset
                )
                and len(value)
                > len(quote_asset)
            ):
                return value

        return (
            f"{value}"
            f"{self.quote_asset}"
        )

    def _base_asset(
        self,
        symbol: str,
    ) -> str:
        quote_asset = self._quote_asset(
            symbol
        )

        if (
            quote_asset
            and symbol.endswith(
                quote_asset
            )
        ):
            return symbol[
                :-len(quote_asset)
            ]

        return symbol

    def _quote_asset(
        self,
        symbol: str,
    ) -> str:
        for quote_asset in self.QUOTE_ASSETS:
            if symbol.endswith(
                quote_asset
            ):
                return quote_asset

        return self.quote_asset

    @staticmethod
    def _basis_percent(
        mark_price: float,
        index_price: float,
    ) -> float:
        if index_price <= 0:
            return 0.0

        return (
            mark_price
            - index_price
        ) / index_price * 100.0

    @staticmethod
    def _funding_trend(
        rates: List[float],
    ) -> str:
        if len(rates) < 4:
            return "unknown"

        midpoint = len(rates) // 2

        older = rates[:midpoint]
        newer = rates[midpoint:]

        difference = (
            mean(newer)
            - mean(older)
        )

        if difference >= 0.00003:
            return "rising"

        if difference <= -0.00003:
            return "falling"

        return "stable"

    @staticmethod
    def _funding_state(
        percent: float,
    ) -> str:
        if percent >= 0.05:
            return "Longs heavily paying"

        if percent >= 0.015:
            return "Longs paying"

        if percent > 0:
            return "Slight long bias"

        if percent <= -0.05:
            return "Shorts heavily paying"

        if percent <= -0.015:
            return "Shorts paying"

        if percent < 0:
            return "Slight short bias"

        return "Neutral"

    @staticmethod
    def _crowding(
        current_percent: float,
        average_percent: float,
        trend: str,
    ) -> str:
        if (
            current_percent >= 0.05
            or (
                current_percent >= 0.025
                and trend == "rising"
            )
        ):
            return "long overcrowding"

        if (
            current_percent <= -0.05
            or (
                current_percent <= -0.025
                and trend == "falling"
            )
        ):
            return "short overcrowding"

        if (
            abs(current_percent) <= 0.01
            and abs(average_percent) <= 0.01
        ):
            return "balanced"

        return "moderate imbalance"

    @staticmethod
    def _first_integer(
        *sources: Dict[str, Any],
        keys: tuple,
    ) -> int:
        for source in sources:
            if not isinstance(
                source,
                dict,
            ):
                continue

            for key in keys:
                value = source.get(
                    key
                )

                if value not in {
                    None,
                    "",
                }:
                    return (
                        BybitPerpetualFundingSnapshotService
                        ._integer(value)
                    )

        return 0

    @staticmethod
    def _timestamp_ms(
        milliseconds: int,
    ):
        if milliseconds <= 0:
            return None

        return datetime.fromtimestamp(
            milliseconds / 1000.0,
            tz=timezone.utc,
        ).isoformat()

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _integer(
        value: Any,
    ) -> int:
        try:
            return int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0


def format_bybit_perpetual_funding(
    result: Dict[str, Any],
) -> str:
    funding = float(
        result.get(
            "current_funding_percent"
        )
        or 0.0
    )

    emoji = (
        "🔴"
        if funding > 0
        else (
            "🟢"
            if funding < 0
            else "⚪"
        )
    )

    return "\n".join([
        "⚡ <b>Bybit Perpetual Funding</b>",
        "<i>Live public linear data</i>",
        "",
        (
            "<b>"
            f"{result.get('symbol')}"
            "</b>"
        ),
        (
            "Mark Price: "
            f"{result.get('mark_price')}"
        ),
        (
            "Index Price: "
            f"{result.get('index_price')}"
        ),
        (
            "Last Price: "
            f"{result.get('last_price')}"
        ),
        (
            "Basis: "
            f"{float(result.get('basis_percent') or 0):+.4f}%"
        ),
        "",
        (
            f"{emoji} Current Funding: "
            f"{funding:+.6f}%"
        ),
        (
            "Funding State: "
            f"{result.get('funding_state')}"
        ),
        (
            "Funding Trend: "
            f"{result.get('funding_trend')}"
        ),
        (
            "Average Funding: "
            f"{float(result.get('average_funding_percent') or 0):+.6f}%"
        ),
        (
            "Funding Range: "
            f"{float(result.get('minimum_funding_percent') or 0):+.6f}% "
            "→ "
            f"{float(result.get('maximum_funding_percent') or 0):+.6f}%"
        ),
        (
            "Positive / Negative / Zero: "
            f"{result.get('positive_periods')} / "
            f"{result.get('negative_periods')} / "
            f"{result.get('zero_periods')}"
        ),
        (
            "Samples: "
            f"{result.get('history_samples')}"
        ),
        "",
        (
            "Open Interest Value: "
            f"{result.get('open_interest_value')}"
        ),
        (
            "Crowding: "
            f"{result.get('crowding')}"
        ),
        (
            "Funding Interval: "
            f"{result.get('funding_interval_hours')}h"
        ),
        (
            "Next Funding: "
            f"{result.get('next_funding_at')}"
        ),
        (
            "Seconds to Funding: "
            f"{result.get('seconds_to_funding')}"
        ),
        "",
        (
            "Source: "
            f"{result.get('source')}"
        ),
        "Mode: Live read-only",
    ])
