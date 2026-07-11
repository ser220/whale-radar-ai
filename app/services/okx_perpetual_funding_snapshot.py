import json
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OKXPerpetualFundingError(RuntimeError):
    """Raised when OKX perpetual funding data cannot be loaded."""


class OKXPerpetualFundingSnapshotService:
    """
    Public read-only OKX perpetual funding source.

    Provides:
    - current funding;
    - funding history;
    - mark price;
    - index price;
    - basis;
    - funding trend;
    - crowding assessment.
    """

    BASE_URL = "https://www.okx.com"

    QUOTE_ASSETS = (
        "USDT",
        "USDC",
        "USD",
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
            1,
            min(
                int(history_limit),
                100,
            ),
        )

    def build(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        instrument = self._normalize_instrument(
            asset
        )

        index_instrument = self._index_instrument(
            instrument
        )

        captured_at = datetime.now(
            timezone.utc
        )

        current_payload = self._request(
            path="/api/v5/public/funding-rate",
            parameters={
                "instId": instrument,
            },
        )

        history_payload = self._request(
            path="/api/v5/public/funding-rate-history",
            parameters={
                "instId": instrument,
                "limit": self.history_limit,
            },
        )

        mark_payload = self._request(
            path="/api/v5/public/mark-price",
            parameters={
                "instType": "SWAP",
                "instId": instrument,
            },
        )

        index_payload = self._request(
            path="/api/v5/market/index-tickers",
            parameters={
                "instId": index_instrument,
            },
        )

        current_rows = self._data_rows(
            current_payload
        )
        history_rows = self._data_rows(
            history_payload
        )
        mark_rows = self._data_rows(
            mark_payload
        )
        index_rows = self._data_rows(
            index_payload
        )

        if not current_rows:
            raise OKXPerpetualFundingError(
                f"No current funding data for {instrument}."
            )

        current = current_rows[0]

        funding_rate = self._number(
            current.get("fundingRate")
        )

        funding_percent = (
            funding_rate * 100.0
        )

        next_funding_ms = self._integer(
            current.get("nextFundingTime")
        )

        funding_time_ms = self._integer(
            current.get("fundingTime")
            or current.get("ts")
        )

        mark_price = (
            self._number(
                mark_rows[0].get("markPx")
            )
            if mark_rows
            else 0.0
        )

        index_price = (
            self._number(
                index_rows[0].get("idxPx")
            )
            if index_rows
            else 0.0
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
            else funding_rate
        )

        minimum_rate = (
            min(rates)
            if rates
            else funding_rate
        )

        maximum_rate = (
            max(rates)
            if rates
            else funding_rate
        )

        positive_count = sum(
            value > 0
            for value in rates
        )

        negative_count = sum(
            value < 0
            for value in rates
        )

        basis_percent = self._basis_percent(
            mark_price=mark_price,
            index_price=index_price,
        )

        funding_trend = self._funding_trend(
            rates
        )

        funding_state = self._funding_state(
            funding_percent
        )

        crowding = self._crowding(
            current_percent=funding_percent,
            average_percent=(
                average_rate * 100.0
            ),
            trend=funding_trend,
        )

        seconds_to_funding = None

        if next_funding_ms > 0:
            seconds_to_funding = max(
                (
                    next_funding_ms
                    / 1000.0
                    - captured_at.timestamp()
                ),
                0.0,
            )

        return {
            "status": "completed",
            "exchange": "OKX",
            "symbol": instrument,
            "instrument_type": "PERPETUAL",
            "base_asset": self._base_asset(
                instrument
            ),
            "quote_asset": self._quote_asset(
                instrument
            ),
            "mark_price": mark_price,
            "index_price": index_price,
            "basis_percent": round(
                basis_percent,
                4,
            ),
            "current_funding_rate": (
                funding_rate
            ),
            "current_funding_percent": round(
                funding_percent,
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
            "positive_periods": positive_count,
            "negative_periods": negative_count,
            "history_samples": len(
                history
            ),
            "funding_time": self._timestamp(
                funding_time_ms
            ),
            "next_funding_at": self._timestamp(
                next_funding_ms
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
            "source": "okx-public-swap",
            "mode": "Live read-only",
            "error": None,
        }

    def _request(
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

            raise OKXPerpetualFundingError(
                f"OKX HTTP error {exc.code}: "
                f"{body or exc.reason}"
            ) from exc

        except URLError as exc:
            raise OKXPerpetualFundingError(
                "OKX connection error: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise OKXPerpetualFundingError(
                "OKX request timed out."
            ) from exc

        try:
            data = json.loads(
                payload
            )

        except json.JSONDecodeError as exc:
            raise OKXPerpetualFundingError(
                "OKX returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise OKXPerpetualFundingError(
                "Unexpected OKX response."
            )

        code = str(
            data.get("code")
            or ""
        )

        if code != "0":
            raise OKXPerpetualFundingError(
                f"OKX API error {code}: "
                f"{data.get('msg')}"
            )

        return data

    @staticmethod
    def _data_rows(
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        rows = payload.get("data")

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

            funding_time_ms = cls._integer(
                row.get("fundingTime")
            )

            result.append({
                "funding_time": cls._timestamp(
                    funding_time_ms
                ),
                "funding_time_ms": (
                    funding_time_ms
                ),
                "funding_rate": rate,
                "funding_percent": round(
                    rate * 100.0,
                    6,
                ),
                "realized_rate": cls._number(
                    row.get(
                        "realizedRate"
                    )
                ),
            })

        result.sort(
            key=lambda item: (
                item["funding_time_ms"]
            )
        )

        return result

    def _normalize_instrument(
        self,
        asset: str,
    ) -> str:
        value = str(
            asset or ""
        ).strip().upper()

        value = (
            value.replace("/", "-")
            .replace("_", "-")
            .replace(" ", "")
        )

        if not value:
            raise ValueError(
                "Asset cannot be empty."
            )

        if value.endswith("-SWAP"):
            return value

        if value.endswith("SWAP"):
            value = value[:-4].rstrip("-")

        compact = value.replace("-", "")

        for quote in self.QUOTE_ASSETS:
            if (
                compact.endswith(quote)
                and len(compact) > len(quote)
            ):
                base = compact[
                    :-len(quote)
                ]

                return (
                    f"{base}-{quote}-SWAP"
                )

        return (
            f"{compact}-"
            f"{self.quote_asset}-SWAP"
        )

    @staticmethod
    def _index_instrument(
        instrument: str,
    ) -> str:
        parts = instrument.split("-")

        if len(parts) < 2:
            return instrument

        return (
            f"{parts[0]}-{parts[1]}"
        )

    @staticmethod
    def _base_asset(
        instrument: str,
    ) -> str:
        parts = instrument.split("-")

        return (
            parts[0]
            if parts
            else instrument
        )

    @staticmethod
    def _quote_asset(
        instrument: str,
    ) -> str:
        parts = instrument.split("-")

        return (
            parts[1]
            if len(parts) > 1
            else "USDT"
        )

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
    def _timestamp(
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


def format_okx_perpetual_funding(
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
        "⚡ <b>OKX Perpetual Funding</b>",
        "<i>Live public swap data</i>",
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
            "Positive / Negative: "
            f"{result.get('positive_periods')} / "
            f"{result.get('negative_periods')}"
        ),
        (
            "Samples: "
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
