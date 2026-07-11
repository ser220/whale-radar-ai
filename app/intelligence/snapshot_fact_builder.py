from typing import Any, List

from app.decision.facts import MarketFact
from app.intelligence.market_snapshot import MarketSnapshot


class SnapshotFactBuilder:
    """
    Converts a live MarketSnapshot into normalized MarketFact objects.

    Current OI and price snapshots remain neutral until
    historical delta calculations are available.
    """

    def build(
        self,
        snapshot: MarketSnapshot,
    ) -> List[MarketFact]:
        if not isinstance(snapshot, MarketSnapshot):
            raise TypeError(
                "snapshot must be MarketSnapshot."
            )

        facts: List[MarketFact] = []

        facts.extend(
            self._arkham_facts(snapshot)
        )

        facts.extend(
            self._funding_facts(snapshot)
        )

        facts.extend(
            self._oi_facts(snapshot)
        )

        facts.extend(
            self._price_facts(snapshot)
        )

        return facts

    def _arkham_facts(
        self,
        snapshot: MarketSnapshot,
    ) -> List[MarketFact]:
        block = dict(snapshot.arkham)

        if not block:
            return []

        event_type = str(
            block.get("event_type")
            or "whale_transfer"
        ).lower()

        amount = self._number(
            block.get("amount_usd")
        )

        if amount >= 100_000_000:
            strength = "extreme"
        elif amount >= 50_000_000:
            strength = "strong"
        elif amount >= 20_000_000:
            strength = "moderate"
        else:
            strength = "weak"

        from_entity = str(
            block.get("from_entity")
            or "Unknown Wallet"
        )

        to_entity = str(
            block.get("to_entity")
            or "Unknown Wallet"
        )

        if event_type == "exchange_inflow":
            direction = "bearish"
            title = (
                f"${amount:,.0f} "
                f"{snapshot.asset} exchange inflow"
            )
            description = (
                f"{from_entity} transferred funds to "
                f"{to_entity}. Exchange-side liquidity "
                "may have increased."
            )
            exchange = to_entity.lower()

        elif event_type == "exchange_outflow":
            direction = "bullish"
            title = (
                f"${amount:,.0f} "
                f"{snapshot.asset} exchange outflow"
            )
            description = (
                f"Funds left {from_entity} for "
                f"{to_entity}. Immediately available "
                "sell-side liquidity may have decreased."
            )
            exchange = from_entity.lower()

        else:
            direction = "neutral"
            title = (
                f"${amount:,.0f} "
                f"{snapshot.asset} whale transfer"
            )
            description = (
                "A large transfer occurred without "
                "confirmed exchange direction."
            )
            exchange = None

        return [
            MarketFact(
                source="arkham",
                fact_type=event_type,
                asset=snapshot.asset,
                direction=direction,
                strength=strength,
                confidence=snapshot.quality.arkham,
                title=title,
                description=description,
                value=amount,
                unit="USD",
                exchange=exchange,
                metadata={
                    "snapshot_id": snapshot.snapshot_id,
                    "tx_hash": block.get("tx_hash"),
                    "network": block.get("network"),
                    "event_timestamp": block.get(
                        "event_timestamp"
                    ),
                },
            )
        ]

    def _funding_facts(
        self,
        snapshot: MarketSnapshot,
    ) -> List[MarketFact]:
        block = dict(snapshot.funding)

        if not block:
            return []

        weighted = self._number(
            block.get(
                "weighted_funding_percent"
            )
        )

        consensus = str(
            block.get("consensus")
            or "unknown"
        ).lower()

        consensus_strength = self._number(
            block.get(
                "consensus_strength"
            )
        )

        confidence = min(
            snapshot.quality.funding,
            max(consensus_strength, 50.0),
        )

        absolute_funding = abs(weighted)

        if absolute_funding >= 0.03:
            strength = "extreme"
        elif absolute_funding >= 0.015:
            strength = "strong"
        elif absolute_funding >= 0.005:
            strength = "moderate"
        else:
            strength = "weak"

        if weighted > 0 and "long" in consensus:
            direction = "bearish"
            fact_type = "positive_funding"
            title = "Leveraged long crowding"
            description = (
                f"Weighted funding is {weighted:+.6f}% "
                f"with {consensus_strength:.1f}% consensus. "
                "Long-side squeeze vulnerability is elevated."
            )

        elif weighted < 0 and "short" in consensus:
            direction = "bullish"
            fact_type = "negative_funding"
            title = "Leveraged short crowding"
            description = (
                f"Weighted funding is {weighted:+.6f}% "
                f"with {consensus_strength:.1f}% consensus. "
                "Short-side squeeze vulnerability is elevated."
            )

        else:
            direction = "neutral"
            fact_type = "funding_neutral"
            title = "Funding is neutral"
            description = (
                f"Weighted funding is {weighted:+.6f}% "
                f"and consensus is {consensus}."
            )

        return [
            MarketFact(
                source="funding",
                fact_type=fact_type,
                asset=snapshot.asset,
                direction=direction,
                strength=strength,
                confidence=confidence,
                title=title,
                description=description,
                value=weighted,
                unit="percent",
                metadata={
                    "snapshot_id": snapshot.snapshot_id,
                    "consensus": consensus,
                    "divergence": block.get(
                        "divergence"
                    ),
                    "execution_risk": block.get(
                        "execution_risk"
                    ),
                },
            )
        ]

    def _oi_facts(
        self,
        snapshot: MarketSnapshot,
    ) -> List[MarketFact]:
        block = dict(
            snapshot.open_interest
        )

        if not block:
            return []

        total_oi = self._number(
            block.get("total_visible_usd")
        )

        leader = str(
            block.get("largest_market_name")
            or block.get("leader_name")
            or block.get("largest_market")
            or block.get("leader")
            or "Unknown"
        )

        leader_key = str(
            block.get("largest_market")
            or block.get("leader")
            or ""
        ).lower()

        leader_share = self._number(
            block.get("largest_market_share")
            or block.get(
                "leader_share_percent"
            )
        )

        concentration = str(
            block.get("concentration")
            or "unknown"
        ).lower()

        facts = [
            MarketFact(
                source="oi",
                fact_type="open_interest_snapshot",
                asset=snapshot.asset,
                direction="neutral",
                strength=(
                    "strong"
                    if total_oi >= 1_000_000_000
                    else "moderate"
                ),
                confidence=(
                    snapshot.quality.open_interest
                ),
                title="Visible perpetual open interest",
                description=(
                    f"Visible OI is ${total_oi:,.0f}. "
                    f"{leader} leads with "
                    f"{leader_share:.2f}% market share. "
                    "Direction remains neutral until "
                    "OI Delta is calculated."
                ),
                value=total_oi,
                unit="USD",
                exchange=leader_key or None,
                metadata={
                    "snapshot_id": snapshot.snapshot_id,
                    "concentration": concentration,
                    "market_shares": block.get(
                        "market_shares"
                    ),
                },
            )
        ]

        if concentration == "high":
            facts.append(
                MarketFact(
                    source="oi",
                    fact_type="oi_concentration",
                    asset=snapshot.asset,
                    direction="neutral",
                    strength="strong",
                    confidence=(
                        snapshot.quality.open_interest
                    ),
                    title="Open-interest concentration risk",
                    description=(
                        f"{leader} controls "
                        f"{leader_share:.2f}% of visible OI."
                    ),
                    value=leader_share,
                    unit="percent",
                    exchange=leader_key or None,
                    metadata={
                        "snapshot_id": (
                            snapshot.snapshot_id
                        ),
                    },
                )
            )

        return facts

    def _price_facts(
        self,
        snapshot: MarketSnapshot,
    ) -> List[MarketFact]:
        block = dict(snapshot.price)

        if not block:
            return []

        mark_price = self._number(
            block.get("mark_price")
        )

        index_price = self._number(
            block.get("index_price")
        )

        basis = self._number(
            block.get("basis_percent")
        )

        return [
            MarketFact(
                source="price_delta",
                fact_type="price_snapshot",
                asset=snapshot.asset,
                direction="neutral",
                strength="weak",
                confidence=snapshot.quality.price,
                title="Current price snapshot",
                description=(
                    f"Mark price is {mark_price}; "
                    f"index price is {index_price}; "
                    f"basis is {basis:+.4f}%. "
                    "Direction remains neutral until "
                    "Price Delta is calculated."
                ),
                value=mark_price,
                unit="price",
                exchange=(
                    snapshot.execution_exchange
                ),
                metadata={
                    "snapshot_id": snapshot.snapshot_id,
                    "index_price": index_price,
                    "basis_percent": basis,
                },
            )
        ]

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
