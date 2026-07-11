import json
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GatePerpetualFundingError(RuntimeError):
    """Raised when Gate.io perpetual funding data cannot be loaded."""


class GatePerpetualFundingSnapshotService:
    """
    Public read-only Gate.io USDT perpetual funding source.

    Provides:
    - current funding;
    - indicative/next funding when available;
    - funding history;
    - mark price;
    - index price;
    - basis;
    - funding trend;
    - crowding assessment.

    No API key.
    No account access.
    No order placement.
    """

    BASE_URL = "https://api.gateio.ws/api/v4"

    SUPPORTED_SETTLEMENTS = {
        "usdt",
        "btc",
        "usd",
    }

    def __init__(
        self,
        settlement: str = "usdt",
        timeout: float = 12.0,
        history_limit: int = 24,
    ) -> None:
        self.settlement = str(
            settlement
        ).strip().lower()

        self.timeout = max(
            float(timeout),
            1.0,
        )

        self.history_limit = max(
            1,
            min(
                int(history_limit),
                1000,
            ),
        )

        if (
            self.settlement
            not in self.SUPPORTED_SETTLEMENTS
        ):
            raise ValueError(
                "settlement must be usdt, btc, or usd."
            )

    def build(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        contract = self._normalize_contract(
            asset
        )

        captured_at = datetime.now(
            timezone.utc
        )

        contract_data = self._request_json(
            path=(
                f"/futures/{self.settlement}"
                f"/contracts/{contract}"
            ),
            parameters={},
        )

        ticker_rows = self._request_json(
            path=(
                f"/futures/{self.settlement}"
                "/tickers"
            ),
            parameters={
                "contract": contract,
            },
        )

        history_rows = self._request_json(
            path=(
                f"/futures/{self.settlement}"
                "/funding_rate"
            ),
            parameters={
                "contract": contract,
                "limit": self.history_limit,
            },
        )

        if not isinstance(
            contract_data,
            dict,
        ):
            raise GatePerpetualFundingError(
                "Unexpected Gate contract response."
            )

        ticker = {}

        if (
            isinstance(ticker_rows, list)
            and ticker_rows
            and isinstance(
                ticker_rows[0],
                dict,
            )
        ):
            ticker = ticker_rows[0]

        if not isinstance(
            history_rows,
            list,
        ):
            raise GatePerpetualFundingError(
                "Unexpected Gate funding history response."
            )

        mark_price = self._first_number(
            contract_data,
            ticker,
            keys=(
                "mark_price",
                "markPrice",
                "last",
            ),
        )

        index_price = self._first_number(
            contract_data,
            ticker,
            keys=(
                "index_price",
                "indexPrice",
            ),
        )

        current_rate = self._first_number(
            ticker,
            contract_data,
            keys=(
                "funding_rate",
                "fundingRate",
            ),
        )

        indicative_rate = self._first_number(
            ticker,
            contract_data,
            keys=(
                "funding_rate_indicative",
                "funding_rate_next",
                "funding_next_rate",
                "indicative_funding_rate",
            ),
        )

        next_funding_value = self._first_value(
            contract_data,
            ticker,
            keys=(
                "funding_next_apply",
                "next_funding_time",
                "funding_time",
            ),
        )

        next_funding_at = self._parse_timestamp(
            next_funding_value
        )

        funding_interval = self._first_integer(
            contract_data,
            ticker,
            keys=(
                "funding_interval",
                "funding_interval_sec",
            ),
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
            current_rate * 100.0
        )

        crowding = self._crowding(
            current_percent=(
                current_rate * 100.0
            ),
            average_percent=(
                average_rate * 100.0
            ),
            trend=funding_trend,
        )

        seconds_to_funding = None

        if next_funding_at is not None:
            next_dt = datetime.fromisoformat(
                next_funding_at
            )

            seconds_to_funding = max(
                (
                    next_dt
                    - captured_at
                ).total_seconds(),
                0.0,
            )

        return {
            "status": "completed",
            "exchange": "Gate.io",
            "symbol": contract,
            "instrument_type": "PERPETUAL",
            "settlement": self.settlement.upper(),
            "base_asset": self._base_asset(
                contract
            ),
            "quote_asset": self._quote_asset(
                contract
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
                current_rate * 100.0,
                6,
            ),
            "indicative_funding_rate": (
                indicative_rate
            ),
            "indicative_funding_percent": round(
                indicative_rate * 100.0,
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
            "funding_interval_seconds": (
                funding_interval
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
            "history": history,
            "captured_at": (
                captured_at.isoformat()
            ),
            "source": (
                "gate-public-usdt-perpetual"
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
            + (
                f"?{query}"
                if query
                else ""
            )
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

            raise GatePerpetualFundingError(
                f"Gate HTTP error "
                f"{exc.code}: "
                f"{body or exc.reason}"
            ) from exc

        except URLError as exc:
            raise GatePerpetualFundingError(
                "Gate connection error: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise GatePerpetualFundingError(
                "Gate request timed out."
            ) from exc

        try:
            data = json.loads(
                payload
            )

        except json.JSONDecodeError as exc:
            raise GatePerpetualFundingError(
                "Gate returned invalid JSON."
            ) from exc

        if (
            isinstance(data, dict)
            and (
                "label" in data
                or "message" in data
            )
            and not (
                "name" in data
                or "mark_price" in data
            )
        ):
            raise GatePerpetualFundingError(
                "Gate API error: "
                f"{data.get('label')} "
                f"{data.get('message')}"
            )

        return data

    @classmethod
    def _parse_history(
        cls,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result = []

        for row in rows:
            if not isinstance(
                row,
                dict,
            ):
                continue

            rate = cls._first_number(
                row,
                keys=(
                    "r",
                    "rate",
                    "funding_rate",
                ),
            )

            timestamp_value = (
                cls._first_value(
                    row,
                    keys=(
                        "t",
                        "time",
                        "funding_time",
                        "timestamp",
                    ),
                )
            )

            funding_time = (
                cls._parse_timestamp(
                    timestamp_value
                )
            )

            result.append({
                "funding_time": (
                    funding_time
                ),
                "funding_timestamp": (
                    timestamp_value
                ),
                "funding_rate": rate,
                "funding_percent": round(
                    rate * 100.0,
                    6,
                ),
            })

        result.sort(
            key=lambda item: (
                str(
                    item[
                        "funding_time"
                    ]
                    or ""
                )
            )
        )

        return result

    def _normalize_contract(
        self,
        asset: str,
    ) -> str:
        value = str(
            asset or ""
        ).strip().upper()

        value = (
            value.replace("/", "_")
            .replace("-", "_")
            .replace(" ", "")
        )

        value = (
            value.replace(
                "_SWAP",
                "",
            )
            .replace(
                "_PERPETUAL",
                "",
            )
            .replace(
                "SWAP",
                "",
            )
            .replace(
                "PERPETUAL",
                "",
            )
        )

        value = value.strip("_")

        if not value:
            raise ValueError(
                "Asset cannot be empty."
            )

        if "_" in value:
            parts = [
                part
                for part in value.split("_")
                if part
            ]

            if len(parts) >= 2:
                return (
                    f"{parts[0]}_"
                    f"{parts[1]}"
                )

        settlement = (
            self.settlement.upper()
        )

        if (
            value.endswith(settlement)
            and len(value)
            > len(settlement)
        ):
            base = value[
                :-len(settlement)
            ]

            return (
                f"{base}_{settlement}"
            )

        return (
            f"{value}_{settlement}"
        )

    @staticmethod
    def _base_asset(
        contract: str,
    ) -> str:
        return contract.split(
            "_"
        )[0]

    @staticmethod
    def _quote_asset(
        contract: str,
    ) -> str:
        parts = contract.split(
            "_"
        )

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
    def _parse_timestamp(
        value: Any,
    ):
        if value in {
            None,
            "",
            0,
            "0",
        }:
            return None

        try:
            timestamp = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        if timestamp > 10_000_000_000:
            timestamp /= 1000.0

        try:
            return datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            ).isoformat()
        except (
            OverflowError,
            OSError,
            ValueError,
        ):
            return None

    @staticmethod
    def _first_value(
        *sources: Dict[str, Any],
        keys: tuple,
    ) -> Any:
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
                    return value

        return None

    @classmethod
    def _first_number(
        cls,
        *sources: Dict[str, Any],
        keys: tuple,
    ) -> float:
        value = cls._first_value(
            *sources,
            keys=keys,
        )

        return cls._number(
            value
        )

    @classmethod
    def _first_integer(
        cls,
        *sources: Dict[str, Any],
        keys: tuple,
    ) -> int:
        value = cls._first_value(
            *sources,
            keys=keys,
        )

        try:
            return int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

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


def format_gate_perpetual_funding(
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
        "⚡ <b>Gate.io Perpetual Funding</b>",
        "<i>Live public futures data</i>",
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
            "Indicative Funding: "
            f"{float(result.get('indicative_funding_percent') or 0):+.6f}%"
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
            "Funding Interval: "
            f"{result.get('funding_interval_seconds')} sec"
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
