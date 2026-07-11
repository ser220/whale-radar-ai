import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.domain.perpetual_exchange_registry import (
    PerpetualExchangeRegistry,
)


class OpenInterestHubError(RuntimeError):
    """Raised when open-interest data cannot be loaded."""


class UnifiedOpenInterestHubService:
    """
    Cross-exchange perpetual open-interest snapshot.

    Sources:
    - OKX;
    - Binance USD-M;
    - Gate.io;
    - Bybit.

    Public read-only data only.
    """

    SOURCE_ORDER = (
        "okx",
        "binance",
        "gate",
        "bybit",
    )

    def __init__(
        self,
        registry: Optional[PerpetualExchangeRegistry] = None,
        timeout: float = 12.0,
    ) -> None:
        self.registry = (
            registry
            or PerpetualExchangeRegistry()
        )

        self.timeout = max(
            float(timeout),
            1.0,
        )

        self.sources = {
            "okx": self._load_okx,
            "binance": self._load_binance,
            "gate": self._load_gate,
            "bybit": self._load_bybit,
        }

    def build(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        asset = self._normalize_asset(
            asset
        )

        snapshots = {}
        errors = {}

        with ThreadPoolExecutor(
            max_workers=len(self.sources)
        ) as executor:
            futures = {
                executor.submit(
                    loader,
                    asset,
                ): exchange_key
                for exchange_key, loader
                in self.sources.items()
            }

            for future in as_completed(
                futures
            ):
                exchange_key = futures[
                    future
                ]

                try:
                    raw = future.result()

                    snapshots[
                        exchange_key
                    ] = self._decorate(
                        exchange_key,
                        raw,
                    )

                except Exception as exc:
                    errors[
                        exchange_key
                    ] = str(exc)

        available_keys = [
            key
            for key in self.SOURCE_ORDER
            if key in snapshots
        ]

        active_execution = (
            self.registry
            .active_execution_set(
                available_keys,
                required_count=3,
            )
        )

        active_execution_keys = [
            exchange.key
            for exchange in active_execution
        ]

        ordered = [
            snapshots[key]
            for key in available_keys
        ]

        execution_rows = [
            row
            for row in ordered
            if row["exchange_key"]
            in active_execution_keys
        ]

        return {
            "status": (
                "completed"
                if ordered
                else "unavailable"
            ),
            "asset": asset,
            "market_type": "perpetual",
            "available_exchanges": (
                available_keys
            ),
            "unavailable_exchanges": (
                sorted(errors)
            ),
            "active_execution_set": (
                active_execution_keys
            ),
            "exchange_count": len(
                ordered
            ),
            "snapshots": ordered,
            "errors": errors,
            "analytics": self._analytics(
                ordered,
                execution_rows,
            ),
            "captured_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "source": (
                "multi-exchange-open-interest-hub"
            ),
            "mode": "Live read-only",
            "production_influence": False,
        }

    def _load_binance(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        symbol = f"{asset}USDT"

        oi = self._request_json(
            "https://fapi.binance.com"
            "/fapi/v1/openInterest",
            {
                "symbol": symbol,
            },
        )

        premium = self._request_json(
            "https://fapi.binance.com"
            "/fapi/v1/premiumIndex",
            {
                "symbol": symbol,
            },
        )

        mark_price = self._number(
            premium.get("markPrice")
        )

        oi_base = self._number(
            oi.get("openInterest")
        )

        return {
            "symbol": symbol,
            "mark_price": mark_price,
            "open_interest": oi_base,
            "open_interest_base": oi_base,
            "open_interest_unit": asset,
            "open_interest_usd": (
                oi_base * mark_price
            ),
            "source": (
                "binance-usdm-public"
            ),
        }

    def _load_okx(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        instrument = (
            f"{asset}-USDT-SWAP"
        )

        payload = self._request_json(
            "https://www.okx.com"
            "/api/v5/public/open-interest",
            {
                "instType": "SWAP",
                "instId": instrument,
            },
        )

        rows = payload.get("data")

        if (
            not isinstance(rows, list)
            or not rows
        ):
            raise OpenInterestHubError(
                f"No OKX OI for {instrument}."
            )

        row = rows[0]

        return {
            "symbol": instrument,
            "mark_price": 0.0,
            "open_interest": self._number(
                row.get("oi")
            ),
            "open_interest_base": (
                self._number(
                    row.get("oiCcy")
                )
            ),
            "open_interest_unit": (
                "contracts"
            ),
            "open_interest_usd": (
                self._number(
                    row.get("oiUsd")
                )
            ),
            "source": "okx-public-swap",
        }

    def _load_gate(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        contract = f"{asset}_USDT"

        rows = self._request_json(
            "https://api.gateio.ws"
            "/api/v4/futures/usdt/tickers",
            {
                "contract": contract,
            },
        )

        if (
            not isinstance(rows, list)
            or not rows
        ):
            raise OpenInterestHubError(
                f"No Gate OI for {contract}."
            )

        row = rows[0]

        total_size = self._number(
            row.get("total_size")
        )

        multiplier = self._number(
            row.get("quanto_multiplier")
        )

        mark_price = self._number(
            row.get("mark_price")
        )

        oi_base = (
            total_size
            * multiplier
        )

        return {
            "symbol": contract,
            "mark_price": mark_price,
            "open_interest": total_size,
            "open_interest_base": oi_base,
            "open_interest_unit": (
                "contracts"
            ),
            "contract_multiplier": (
                multiplier
            ),
            "open_interest_usd": (
                oi_base * mark_price
            ),
            "source": (
                "gate-public-usdt-perpetual"
            ),
        }

    def _load_bybit(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        symbol = f"{asset}USDT"

        payload = self._request_json(
            "https://api.bybit.com"
            "/v5/market/tickers",
            {
                "category": "linear",
                "symbol": symbol,
            },
        )

        if self._integer(
            payload.get("retCode")
        ) != 0:
            raise OpenInterestHubError(
                "Bybit API error: "
                f"{payload.get('retMsg')}"
            )

        result = payload.get(
            "result"
        ) or {}

        rows = result.get(
            "list"
        ) or []

        if not rows:
            raise OpenInterestHubError(
                f"No Bybit OI for {symbol}."
            )

        row = rows[0]

        mark_price = self._number(
            row.get("markPrice")
        )

        oi_base = self._number(
            row.get("openInterest")
        )

        oi_usd = self._number(
            row.get("openInterestValue")
        )

        if oi_usd <= 0:
            oi_usd = (
                oi_base * mark_price
            )

        return {
            "symbol": symbol,
            "mark_price": mark_price,
            "open_interest": oi_base,
            "open_interest_base": oi_base,
            "open_interest_unit": asset,
            "open_interest_usd": oi_usd,
            "source": (
                "bybit-v5-public-linear"
            ),
        }

    def _decorate(
        self,
        exchange_key: str,
        row: Dict[str, Any],
    ) -> Dict[str, Any]:
        exchange = self.registry.get(
            exchange_key
        )

        return {
            "exchange_key": exchange_key,
            "exchange": (
                exchange.name
                if exchange
                else exchange_key
            ),
            "layer": (
                exchange.layer
                if exchange
                else "unknown"
            ),
            "weight": (
                exchange.initial_weight
                if exchange
                else 1.0
            ),
            "symbol": row.get("symbol"),
            "mark_price": self._number(
                row.get("mark_price")
            ),
            "open_interest": self._number(
                row.get("open_interest")
            ),
            "open_interest_base": (
                self._number(
                    row.get(
                        "open_interest_base"
                    )
                )
            ),
            "open_interest_unit": (
                row.get(
                    "open_interest_unit"
                )
            ),
            "contract_multiplier": (
                self._number(
                    row.get(
                        "contract_multiplier"
                    )
                )
            ),
            "open_interest_usd": round(
                self._number(
                    row.get(
                        "open_interest_usd"
                    )
                ),
                2,
            ),
            "source": row.get("source"),
            "status": "online",
        }

    def _analytics(
        self,
        rows: List[Dict[str, Any]],
        execution_rows: List[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:
        total_oi = sum(
            max(
                row["open_interest_usd"],
                0.0,
            )
            for row in rows
        )

        execution_oi = sum(
            max(
                row["open_interest_usd"],
                0.0,
            )
            for row in execution_rows
        )

        shares = {
            row["exchange_key"]: round(
                (
                    row["open_interest_usd"]
                    / total_oi
                    * 100.0
                )
                if total_oi > 0
                else 0.0,
                2,
            )
            for row in rows
        }

        leader = (
            max(
                rows,
                key=lambda row: (
                    row[
                        "open_interest_usd"
                    ]
                ),
            )
            if rows
            else None
        )

        execution_leader = (
            max(
                execution_rows,
                key=lambda row: (
                    row[
                        "open_interest_usd"
                    ]
                ),
            )
            if execution_rows
            else None
        )

        largest_share = max(
            shares.values(),
            default=0.0,
        )

        if largest_share >= 60:
            concentration = "high"
        elif largest_share >= 40:
            concentration = "moderate"
        else:
            concentration = "distributed"

        return {
            "total_open_interest_usd": round(
                total_oi,
                2,
            ),
            "execution_open_interest_usd": round(
                execution_oi,
                2,
            ),
            "market_shares": shares,
            "largest_market": (
                {
                    "exchange": (
                        leader["exchange"]
                    ),
                    "exchange_key": (
                        leader[
                            "exchange_key"
                        ]
                    ),
                    "open_interest_usd": (
                        leader[
                            "open_interest_usd"
                        ]
                    ),
                    "market_share_percent": (
                        shares.get(
                            leader[
                                "exchange_key"
                            ],
                            0.0,
                        )
                    ),
                }
                if leader
                else None
            ),
            "execution_leader": (
                {
                    "exchange": (
                        execution_leader[
                            "exchange"
                        ]
                    ),
                    "exchange_key": (
                        execution_leader[
                            "exchange_key"
                        ]
                    ),
                    "open_interest_usd": (
                        execution_leader[
                            "open_interest_usd"
                        ]
                    ),
                }
                if execution_leader
                else None
            ),
            "concentration": concentration,
        }

    def _request_json(
        self,
        url: str,
        parameters: Dict[str, Any],
    ) -> Any:
        query = urlencode(
            parameters
        )

        if query:
            url = f"{url}?{query}"

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "Whale-Radar-AI/16"
                ),
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                return json.loads(
                    response.read()
                    .decode("utf-8")
                )

        except HTTPError as exc:
            raise OpenInterestHubError(
                f"HTTP {exc.code}: "
                f"{exc.reason}"
            ) from exc

        except URLError as exc:
            raise OpenInterestHubError(
                f"Connection error: "
                f"{exc.reason}"
            ) from exc

    @staticmethod
    def _normalize_asset(
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

        for quote in (
            "USDT",
            "USDC",
            "USD",
        ):
            if (
                value.endswith(quote)
                and len(value) > len(quote)
            ):
                value = value[
                    :-len(quote)
                ]
                break

        if not value:
            raise ValueError(
                "Asset cannot be empty."
            )

        return value

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


def _money(
    value: Any,
) -> str:
    number = float(
        value or 0.0
    )

    if abs(number) >= 1_000_000_000:
        return (
            f"${number / 1_000_000_000:.2f}B"
        )

    if abs(number) >= 1_000_000:
        return (
            f"${number / 1_000_000:.2f}M"
        )

    if abs(number) >= 1_000:
        return (
            f"${number / 1_000:.2f}K"
        )

    return f"${number:.2f}"


def format_unified_open_interest(
    result: Dict[str, Any],
) -> str:
    analytics = (
        result.get("analytics")
        or {}
    )

    active = set(
        result.get(
            "active_execution_set"
        )
        or []
    )

    lines = [
        "📊 <b>Unified Open Interest</b>",
        "<i>Cross-exchange perpetual snapshot</i>",
        "",
        (
            "<b>Asset: "
            f"{result.get('asset')}</b>"
        ),
        (
            "Available Sources: "
            f"{result.get('exchange_count')}"
        ),
        (
            "Active Execution Set: "
            + ", ".join(active)
        ),
        "",
        "<b>Exchange Open Interest</b>",
    ]

    shares = analytics.get(
        "market_shares",
        {},
    )

    for row in result.get(
        "snapshots",
        [],
    ):
        marker = (
            "✅"
            if row["exchange_key"]
            in active
            else "ℹ️"
        )

        lines.append(
            f"{marker} "
            f"<b>{row['exchange']}</b>: "
            f"{_money(row['open_interest_usd'])} "
            f"({shares.get(row['exchange_key'], 0):.2f}%)"
        )

    largest = (
        analytics.get(
            "largest_market"
        )
        or {}
    )

    execution_leader = (
        analytics.get(
            "execution_leader"
        )
        or {}
    )

    lines.extend([
        "",
        "<b>Market Structure</b>",
        (
            "Total Visible OI: "
            f"{_money(analytics.get('total_open_interest_usd'))}"
        ),
        (
            "Execution OI: "
            f"{_money(analytics.get('execution_open_interest_usd'))}"
        ),
        (
            "Largest Market: "
            f"{largest.get('exchange')} "
            f"({_money(largest.get('open_interest_usd'))})"
        ),
        (
            "Execution Leader: "
            f"{execution_leader.get('exchange')} "
            f"({_money(execution_leader.get('open_interest_usd'))})"
        ),
        (
            "Concentration: "
            f"{analytics.get('concentration')}"
        ),
        "",
        "Mode: Live read-only",
        "Production decision unchanged.",
    ])

    return "\n".join(lines)
