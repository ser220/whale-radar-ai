import json
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PerpetualFundingError(RuntimeError):
    """Raised when perpetual funding data cannot be loaded."""


class PerpetualFundingSnapshotService:
    """
    Loads Binance USD-M perpetual funding data.

    Public read-only data:
    - mark price;
    - index price;
    - current funding rate;
    - next funding time;
    - recent funding history;
    - premium/basis;
    - funding trend and crowding interpretation.
    """

    BASE_URL = "https://fapi.binance.com"

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
            quote_asset
        ).strip().upper()

        self.timeout = max(
            float(timeout),
            1.0,
        )

        self.history_limit = max(
            min(
                int(history_limit),
                1000,
            ),
            1,
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

        premium = self._request_json(
            path="/fapi/v1/premiumIndex",
            parameters={
                "symbol": symbol,
            },
        )

        history = self._request_json(
            path="/fapi/v1/fundingRate",
            parameters={
                "symbol": symbol,
                "limit": self.history_limit,
            },
        )

        if not isinstance(premium, dict):
            raise PerpetualFundingError(
                "Unexpected premium index response."
            )

        if not isinstance(history, list):
            raise PerpetualFundingError(
                "Unexpected funding history response."
            )

        current_rate = self._number(
            premium.get(
                "lastFundingRate"
            )
        )

        mark_price = self._number(
            premium.get("markPrice")
        )

        index_price = self._number(
            premium.get("indexPrice")
        )

        next_funding_ms = int(
            premium.get(
                "nextFundingTime"
            )
            or 0
        )

        server_time_ms = int(
            premium.get("time")
            or captured_at.timestamp() * 1000
        )

        funding_history = (
            self._parse_history(
                history
            )
        )

        recent_rates = [
            item["funding_rate"]
            for item in funding_history
        ]

        average_rate = (
            mean(recent_rates)
            if recent_rates
            else current_rate
        )

        minimum_rate = (
            min(recent_rates)
            if recent_rates
            else current_rate
        )

        maximum_rate = (
            max(recent_rates)
            if recent_rates
            else current_rate
        )

        positive_count = sum(
            rate > 0
            for rate in recent_rates
        )

        negative_count = sum(
            rate < 0
            for rate in recent_rates
        )

        basis_percent = self._basis_percent(
            mark_price=mark_price,
            index_price=index_price,
        )

        funding_trend = self._funding_trend(
            recent_rates
        )

        funding_state = self._funding_state(
            current_rate
        )

        crowding = self._crowding_state(
            current_rate=current_rate,
            average_rate=average_rate,
            funding_trend=funding_trend,
        )

        next_funding_at = (
            self._timestamp(
                next_funding_ms
            )
            if next_funding_ms > 0
            else None
        )

        seconds_to_funding = (
            max(
                (
                    next_funding_ms
                    - server_time_ms
                ) / 1000,
                0.0,
            )
            if next_funding_ms > 0
            else None
        )

        return {
            "status": "completed",
            "exchange": "Binance USD-M Futures",
            "symbol": symbol,
            "instrument_type": "PERPETUAL",
            "base_asset": self._base_asset(
                symbol
            ),
            "quote_asset": self._quote_asset(
                symbol
            ),
            "mark_price": mark_price,
            "index_price": index_price,
            "basis_percent": round(
                basis_percent,
                4,
            ),
            "current_funding_rate": (
                current_rate
            ),
            "current_funding_percent": round(
                current_rate * 100,
                6,
            ),
            "average_funding_rate": (
                average_rate
            ),
            "average_funding_percent": round(
                average_rate * 100,
                6,
            ),
            "minimum_funding_percent": round(
                minimum_rate * 100,
                6,
            ),
            "maximum_funding_percent": round(
                maximum_rate * 100,
                6,
            ),
            "funding_state": funding_state,
            "funding_trend": funding_trend,
            "crowding": crowding,
            "positive_periods": positive_count,
            "negative_periods": negative_count,
            "history_samples": len(
                funding_history
            ),
            "next_funding_at": (
                next_funding_at
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
            "funding_history": (
                funding_history
            ),
            "captured_at": (
                captured_at.isoformat()
            ),
            "source": (
                "binance-usdm-public"
            ),
            "mode": "Live read-only",
            "error": None,
        }

    def _request_json(
        self,
        path: str,
        parameters: Dict[str, Any],
    ) -> Any:
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

            raise PerpetualFundingError(
                f"Binance HTTP error "
                f"{exc.code}: "
                f"{body or exc.reason}"
            ) from exc

        except URLError as exc:
            raise PerpetualFundingError(
                "Binance connection error: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise PerpetualFundingError(
                "Binance request timed out."
            ) from exc

        try:
            data = json.loads(
                payload
            )

        except json.JSONDecodeError as exc:
            raise PerpetualFundingError(
                "Binance returned invalid JSON."
            ) from exc

        if (
            isinstance(data, dict)
            and "code" in data
        ):
            raise PerpetualFundingError(
                "Binance API error "
                f"{data.get('code')}: "
                f"{data.get('msg')}"
            )

        return data

    @staticmethod
    def _parse_history(
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result = []

        for row in rows:
            timestamp_ms = int(
                row.get(
                    "fundingTime"
                )
                or 0
            )

            rate = (
                PerpetualFundingSnapshotService
                ._number(
                    row.get(
                        "fundingRate"
                    )
                )
            )

            result.append({
                "funding_time": (
                    PerpetualFundingSnapshotService
                    ._timestamp(
                        timestamp_ms
                    )
                ),
                "funding_time_ms": (
                    timestamp_ms
                ),
                "funding_rate": rate,
                "funding_percent": round(
                    rate * 100,
                    6,
                ),
                "mark_price": (
                    PerpetualFundingSnapshotService
                    ._number(
                        row.get(
                            "markPrice"
                        )
                    )
                ),
            })

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
            .replace("PERP", "")
            .replace("SWAP", "")
        )

        if not value:
            raise ValueError(
                "Asset cannot be empty."
            )

        for quote in self.QUOTE_ASSETS:
            if (
                value.endswith(quote)
                and len(value) > len(quote)
            ):
                return value

        return (
            f"{value}"
            f"{self.quote_asset}"
        )

    @staticmethod
    def _funding_state(
        funding_rate: float,
    ) -> str:
        funding_percent = (
            funding_rate * 100
        )

        if funding_percent >= 0.05:
            return "Longs heavily paying"

        if funding_percent >= 0.015:
            return "Longs paying"

        if funding_percent > 0:
            return "Slight long bias"

        if funding_percent <= -0.05:
            return "Shorts heavily paying"

        if funding_percent <= -0.015:
            return "Shorts paying"

        if funding_percent < 0:
            return "Slight short bias"

        return "Neutral"

    @staticmethod
    def _funding_trend(
        rates: List[float],
    ) -> str:
        if len(rates) < 4:
            return "unknown"

        midpoint = len(rates) // 2

        older = rates[:midpoint]
        newer = rates[midpoint:]

        older_average = mean(
            older
        )

        newer_average = mean(
            newer
        )

        difference = (
            newer_average
            - older_average
        )

        if difference >= 0.00003:
            return "rising"

        if difference <= -0.00003:
            return "falling"

        return "stable"

    @staticmethod
    def _crowding_state(
        current_rate: float,
        average_rate: float,
        funding_trend: str,
    ) -> str:
        current_percent = (
            current_rate * 100
        )

        average_percent = (
            average_rate * 100
        )

        if (
            current_percent >= 0.05
            or (
                current_percent >= 0.025
                and funding_trend == "rising"
            )
        ):
            return "long overcrowding"

        if (
            current_percent <= -0.05
            or (
                current_percent <= -0.025
                and funding_trend == "falling"
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

    def _base_asset(
        self,
        symbol: str,
    ) -> str:
        quote = self._quote_asset(
            symbol
        )

        return (
            symbol[:-len(quote)]
            if quote
            else symbol
        )

    def _quote_asset(
        self,
        symbol: str,
    ) -> str:
        for quote in self.QUOTE_ASSETS:
            if symbol.endswith(
                quote
            ):
                return quote

        return self.quote_asset

    @staticmethod
    def _timestamp(
        timestamp_ms: int,
    ) -> str:
        return datetime.fromtimestamp(
            timestamp_ms / 1000,
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


def format_perpetual_funding_snapshot(
    result: Dict[str, Any],
) -> str:
    funding = float(
        result.get(
            "current_funding_percent"
        )
        or 0.0
    )

    funding_emoji = (
        "🔴"
        if funding > 0
        else (
            "🟢"
            if funding < 0
            else "⚪"
        )
    )

    return "\n".join([
        "⚡ <b>Perpetual Funding Snapshot</b>",
        "<i>Binance USD-M Futures</i>",
        "",
        (
            "<b>"
            f"{result.get('symbol')} "
            "PERPETUAL"
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
            "Basis: "
            f"{float(result.get('basis_percent') or 0):+.4f}%"
        ),
        "",
        (
            f"{funding_emoji} Current Funding: "
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
            "Positive Periods: "
            f"{result.get('positive_periods')}"
        ),
        (
            "Negative Periods: "
            f"{result.get('negative_periods')}"
        ),
        (
            "History Samples: "
            f"{result.get('history_samples')}"
        ),
        "",
        (
            "Crowding: "
            f"{result.get('crowding')}"
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
