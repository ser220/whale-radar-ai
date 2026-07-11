from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domain.perpetual_exchange_registry import (
    PerpetualExchangeRegistry,
)
from app.services.bybit_perpetual_funding_snapshot import (
    BybitPerpetualFundingSnapshotService,
)
from app.services.gate_perpetual_funding_snapshot import (
    GatePerpetualFundingSnapshotService,
)
from app.services.okx_perpetual_funding_snapshot import (
    OKXPerpetualFundingSnapshotService,
)
from app.services.perpetual_funding_snapshot import (
    PerpetualFundingSnapshotService,
)


class UnifiedFundingHubService:
    """
    Aggregates perpetual funding across execution markets.

    Current live sources:
    - OKX;
    - Binance USD-M;
    - Gate.io.

    Safety:
    - public read-only APIs;
    - no API keys;
    - no account access;
    - no order placement;
    - no production decision changes.
    """

    def __init__(
        self,
        registry: Optional[
            PerpetualExchangeRegistry
        ] = None,
        history_limit: int = 24,
        timeout: float = 12.0,
    ) -> None:
        self.registry = (
            registry
            or PerpetualExchangeRegistry()
        )

        self.history_limit = max(
            int(history_limit),
            1,
        )

        self.timeout = max(
            float(timeout),
            1.0,
        )

        self.sources = {
            "okx": (
                OKXPerpetualFundingSnapshotService(
                    history_limit=self.history_limit,
                    timeout=self.timeout,
                )
            ),
            "binance": (
                PerpetualFundingSnapshotService(
                    history_limit=self.history_limit,
                    timeout=self.timeout,
                )
            ),
            "gate": (
                GatePerpetualFundingSnapshotService(
                    history_limit=self.history_limit,
                    timeout=self.timeout,
                )
            ),
            "bybit": (
                BybitPerpetualFundingSnapshotService(
                    history_limit=self.history_limit,
                    timeout=self.timeout,
                )
            ),
        }

    def build(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        normalized_asset = str(
            asset or ""
        ).strip().upper()

        if not normalized_asset:
            raise ValueError(
                "Asset cannot be empty."
            )

        captured_at = datetime.now(
            timezone.utc
        )

        results: Dict[
            str,
            Dict[str, Any]
        ] = {}

        errors: Dict[
            str,
            str
        ] = {}

        worker_count = max(
            min(
                len(self.sources),
                6,
            ),
            1,
        )

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:
            futures = {
                executor.submit(
                    source.build,
                    normalized_asset,
                ): exchange_key
                for (
                    exchange_key,
                    source,
                ) in self.sources.items()
            }

            for future in as_completed(
                futures
            ):
                exchange_key = futures[
                    future
                ]

                try:
                    raw_result = future.result()

                    results[
                        exchange_key
                    ] = self._normalize_result(
                        exchange_key=exchange_key,
                        result=raw_result,
                    )

                except Exception as exc:
                    errors[
                        exchange_key
                    ] = str(exc)

        available_keys = list(
            results.keys()
        )

        active_execution = (
            self.registry
            .active_execution_set(
                available_keys=available_keys,
                required_count=3,
            )
        )

        active_execution_keys = [
            exchange.key
            for exchange in active_execution
        ]

        active_rows = [
            results[key]
            for key in active_execution_keys
            if key in results
        ]

        analytics = self._analytics(
            active_rows
        )

        all_execution_keys = [
            exchange.key
            for exchange
            in self.registry.execution()
        ]

        unavailable_execution = [
            key
            for key in all_execution_keys
            if key not in results
        ]

        configured_backup = [
            exchange.key
            for exchange
            in self.registry.hot_backup()
        ]

        status = (
            "completed"
            if results
            else "unavailable"
        )

        return {
            "status": status,
            "asset": normalized_asset,
            "market_type": "perpetual",
            "available_exchanges": sorted(
                available_keys
            ),
            "unavailable_exchanges": (
                errors
            ),
            "unavailable_execution": (
                unavailable_execution
            ),
            "active_execution_set": (
                active_execution_keys
            ),
            "configured_hot_backup": (
                configured_backup
            ),
            "exchange_count": len(
                results
            ),
            "execution_exchange_count": len(
                active_rows
            ),
            "exchanges": results,
            "analytics": analytics,
            "captured_at": (
                captured_at.isoformat()
            ),
            "mode": "Live read-only",
            "production_influence": False,
        }

    def _normalize_result(
        self,
        exchange_key: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        exchange = self.registry.get(
            exchange_key
        )

        funding_percent = self._number(
            result.get(
                "current_funding_percent"
            )
        )

        average_percent = self._number(
            result.get(
                "average_funding_percent"
            )
        )

        return {
            "exchange_key": exchange_key,
            "exchange_name": (
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
            "symbol": result.get(
                "symbol"
            ),
            "funding_percent": round(
                funding_percent,
                6,
            ),
            "average_funding_percent": round(
                average_percent,
                6,
            ),
            "funding_trend": result.get(
                "funding_trend"
            ),
            "funding_state": result.get(
                "funding_state"
            ),
            "crowding": result.get(
                "crowding"
            ),
            "mark_price": self._number(
                result.get(
                    "mark_price"
                )
            ),
            "index_price": self._number(
                result.get(
                    "index_price"
                )
            ),
            "basis_percent": round(
                self._number(
                    result.get(
                        "basis_percent"
                    )
                ),
                4,
            ),
            "next_funding_at": result.get(
                "next_funding_at"
            ),
            "seconds_to_funding": (
                result.get(
                    "seconds_to_funding"
                )
            ),
            "history_samples": int(
                result.get(
                    "history_samples"
                )
                or 0
            ),
            "source": result.get(
                "source"
            ),
            "status": result.get(
                "status",
                "completed",
            ),
        }

    def _analytics(
        self,
        rows: List[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:
        if not rows:
            return {
                "weighted_funding_percent": 0.0,
                "simple_average_funding_percent": 0.0,
                "funding_spread_percent": 0.0,
                "consensus": "unavailable",
                "consensus_strength": 0.0,
                "divergence": "unavailable",
                "execution_risk": "unknown",
                "strongest_long_bias": None,
                "strongest_short_bias": None,
                "positive_exchanges": 0,
                "negative_exchanges": 0,
                "neutral_exchanges": 0,
                "interpretation": (
                    "No execution-market funding "
                    "data is available."
                ),
            }

        rates = [
            float(
                row[
                    "funding_percent"
                ]
            )
            for row in rows
        ]

        weights = [
            max(
                float(
                    row.get("weight")
                    or 0.0
                ),
                0.0,
            )
            for row in rows
        ]

        total_weight = sum(
            weights
        )

        weighted_average = (
            sum(
                rate * weight
                for rate, weight in zip(
                    rates,
                    weights,
                )
            )
            / total_weight
            if total_weight > 0
            else sum(rates) / len(rates)
        )

        simple_average = (
            sum(rates)
            / len(rates)
        )

        maximum_rate = max(
            rates
        )
        minimum_rate = min(
            rates
        )

        spread = (
            maximum_rate
            - minimum_rate
        )

        neutral_limit = 0.001

        positive_rows = [
            row
            for row in rows
            if float(
                row["funding_percent"]
            ) > neutral_limit
        ]

        negative_rows = [
            row
            for row in rows
            if float(
                row["funding_percent"]
            ) < -neutral_limit
        ]

        neutral_rows = [
            row
            for row in rows
            if abs(
                float(
                    row[
                        "funding_percent"
                    ]
                )
            ) <= neutral_limit
        ]

        consensus, strength = (
            self._consensus(
                total=len(rows),
                positive=len(
                    positive_rows
                ),
                negative=len(
                    negative_rows
                ),
                neutral=len(
                    neutral_rows
                ),
            )
        )

        divergence = self._divergence(
            spread
        )

        strongest_long = max(
            rows,
            key=lambda row: float(
                row[
                    "funding_percent"
                ]
            ),
        )

        strongest_short = min(
            rows,
            key=lambda row: float(
                row[
                    "funding_percent"
                ]
            ),
        )

        maximum_absolute_rate = max(
            abs(rate)
            for rate in rates
        )

        execution_risk = self._risk(
            maximum_absolute_rate=(
                maximum_absolute_rate
            ),
            divergence=divergence,
            consensus=consensus,
        )

        return {
            "weighted_funding_percent": round(
                weighted_average,
                6,
            ),
            "simple_average_funding_percent": round(
                simple_average,
                6,
            ),
            "funding_spread_percent": round(
                spread,
                6,
            ),
            "maximum_funding_percent": round(
                maximum_rate,
                6,
            ),
            "minimum_funding_percent": round(
                minimum_rate,
                6,
            ),
            "consensus": consensus,
            "consensus_strength": round(
                strength,
                1,
            ),
            "divergence": divergence,
            "execution_risk": execution_risk,
            "strongest_long_bias": {
                "exchange": (
                    strongest_long[
                        "exchange_name"
                    ]
                ),
                "exchange_key": (
                    strongest_long[
                        "exchange_key"
                    ]
                ),
                "funding_percent": (
                    strongest_long[
                        "funding_percent"
                    ]
                ),
            },
            "strongest_short_bias": {
                "exchange": (
                    strongest_short[
                        "exchange_name"
                    ]
                ),
                "exchange_key": (
                    strongest_short[
                        "exchange_key"
                    ]
                ),
                "funding_percent": (
                    strongest_short[
                        "funding_percent"
                    ]
                ),
            },
            "positive_exchanges": len(
                positive_rows
            ),
            "negative_exchanges": len(
                negative_rows
            ),
            "neutral_exchanges": len(
                neutral_rows
            ),
            "interpretation": (
                self._interpretation(
                    consensus=consensus,
                    divergence=divergence,
                    risk=execution_risk,
                )
            ),
        }

    @staticmethod
    def _consensus(
        total: int,
        positive: int,
        negative: int,
        neutral: int,
    ):
        if total <= 0:
            return (
                "unavailable",
                0.0,
            )

        largest = max(
            positive,
            negative,
            neutral,
        )

        strength = (
            largest / total * 100.0
        )

        if positive == total:
            return (
                "strong-long-bias",
                strength,
            )

        if negative == total:
            return (
                "strong-short-bias",
                strength,
            )

        if positive > negative:
            return (
                "long-bias",
                strength,
            )

        if negative > positive:
            return (
                "short-bias",
                strength,
            )

        if neutral == total:
            return (
                "neutral",
                strength,
            )

        return (
            "mixed",
            strength,
        )

    @staticmethod
    def _divergence(
        spread: float,
    ) -> str:
        if spread >= 0.030:
            return "extreme"

        if spread >= 0.015:
            return "high"

        if spread >= 0.0075:
            return "moderate"

        return "low"

    @staticmethod
    def _risk(
        maximum_absolute_rate: float,
        divergence: str,
        consensus: str,
    ) -> str:
        if (
            maximum_absolute_rate
            >= 0.050
            or divergence == "extreme"
        ):
            return "high"

        if (
            maximum_absolute_rate
            >= 0.025
            or divergence == "high"
        ):
            return "elevated"

        if (
            maximum_absolute_rate
            >= 0.010
            or divergence == "moderate"
        ):
            return "moderate"

        if consensus == "mixed":
            return "moderate"

        return "low"

    @staticmethod
    def _interpretation(
        consensus: str,
        divergence: str,
        risk: str,
    ) -> str:
        consensus_text = {
            "strong-long-bias": (
                "All execution markets show "
                "positive funding."
            ),
            "long-bias": (
                "Most execution markets show "
                "positive funding."
            ),
            "strong-short-bias": (
                "All execution markets show "
                "negative funding."
            ),
            "short-bias": (
                "Most execution markets show "
                "negative funding."
            ),
            "neutral": (
                "Execution-market funding is "
                "broadly neutral."
            ),
            "mixed": (
                "Execution markets disagree on "
                "funding direction."
            ),
        }.get(
            consensus,
            "Funding consensus is unavailable.",
        )

        return (
            f"{consensus_text} "
            f"Cross-exchange divergence is "
            f"{divergence}; execution risk is "
            f"{risk}."
        )

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


def format_unified_funding_hub(
    result: Dict[str, Any],
) -> str:
    analytics = (
        result.get("analytics")
        or {}
    )

    exchanges = (
        result.get("exchanges")
        or {}
    )

    lines = [
        "🌐 <b>Unified Perpetual Funding</b>",
        "<i>Execution-market intelligence</i>",
        "",
        (
            "<b>Asset: "
            f"{result.get('asset')}</b>"
        ),
        (
            "Available Sources: "
            f"{result.get('exchange_count', 0)}"
        ),
        (
            "Active Execution Set: "
            + ", ".join(
                result.get(
                    "active_execution_set"
                )
                or []
            )
        ),
        "",
        "<b>Execution Markets</b>",
    ]

    ordered_keys = [
        "okx",
        "binance",
        "gate",
    ]

    for key in ordered_keys:
        row = exchanges.get(
            key
        )

        if row is None:
            error = (
                result.get(
                    "unavailable_exchanges",
                    {},
                ).get(key)
            )

            lines.append(
                f"• {key.upper()}: "
                f"UNAVAILABLE"
                + (
                    f" — {error}"
                    if error
                    else ""
                )
            )

            continue

        funding = float(
            row.get(
                "funding_percent"
            )
            or 0.0
        )

        emoji = (
            "🔴"
            if funding > 0.001
            else (
                "🟢"
                if funding < -0.001
                else "⚪"
            )
        )

        lines.append(
            f"{emoji} "
            f"{row['exchange_name']}: "
            f"{funding:+.6f}% "
            f"| basis "
            f"{float(row.get('basis_percent') or 0):+.4f}% "
            f"| {row.get('funding_trend')}"
        )

    lines.extend([
        "",
        "<b>Consensus</b>",
        (
            "Weighted Funding: "
            f"{float(analytics.get('weighted_funding_percent') or 0):+.6f}%"
        ),
        (
            "Simple Average: "
            f"{float(analytics.get('simple_average_funding_percent') or 0):+.6f}%"
        ),
        (
            "Funding Spread: "
            f"{float(analytics.get('funding_spread_percent') or 0):.6f}%"
        ),
        (
            "Consensus: "
            f"{analytics.get('consensus')}"
        ),
        (
            "Consensus Strength: "
            f"{analytics.get('consensus_strength')}%"
        ),
        (
            "Divergence: "
            f"{analytics.get('divergence')}"
        ),
        (
            "Execution Risk: "
            f"{analytics.get('execution_risk')}"
        ),
        "",
        "<b>Extremes</b>",
    ])

    strongest_long = (
        analytics.get(
            "strongest_long_bias"
        )
        or {}
    )

    strongest_short = (
        analytics.get(
            "strongest_short_bias"
        )
        or {}
    )

    lines.extend([
        (
            "Strongest Long Bias: "
            f"{strongest_long.get('exchange')} "
            f"{float(strongest_long.get('funding_percent') or 0):+.6f}%"
        ),
        (
            "Strongest Short Bias: "
            f"{strongest_short.get('exchange')} "
            f"{float(strongest_short.get('funding_percent') or 0):+.6f}%"
        ),
        "",
        (
            "Interpretation: "
            f"{analytics.get('interpretation')}"
        ),
        "",
        (
            "Hot Backup: "
            + ", ".join(
                result.get(
                    "configured_hot_backup"
                )
                or []
            )
            + " (source not connected yet)"
        ),
        "",
        "Mode: Live read-only",
        "Production decision unchanged.",
    ])

    return "\n".join(
        lines
    )
