import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.config import DB_PATH
from app.decision.decision_engine import DecisionEngine
from app.decision.evidence import (
    EvidenceGraphBuilder,
    MarketFactEvidenceMapper,
)
from app.decision.trade_readiness_engine import (
    TradeReadinessEngine,
)
from app.intelligence.snapshot_builder import (
    MarketSnapshotBuilder,
)
from app.intelligence.snapshot_fact_builder import (
    SnapshotFactBuilder,
)
from app.models.event import MarketEvent
from app.repository.analysis_state_repository import (
    AnalysisStateRepository,
)


class AnalyzeService:
    """
    Live read-only analysis entry point.

    Pipeline:
        asset
        -> latest recent Arkham event
        -> live unified market snapshot
        -> normalized market facts
        -> evidence graph
        -> Decision Engine v2
        -> Trade Readiness Engine

    No order execution.
    """

    def __init__(
        self,
        execution_exchange: str = "okx",
        arkham_max_age_hours: int = 6,
    ) -> None:
        self.snapshot_builder = MarketSnapshotBuilder(
            execution_exchange=execution_exchange
        )

        self.fact_builder = SnapshotFactBuilder()
        self.evidence_mapper = MarketFactEvidenceMapper()
        self.graph_builder = EvidenceGraphBuilder()
        self.decision_engine = DecisionEngine()
        self.trade_engine = TradeReadinessEngine()
        self.analysis_state_repository = (
            AnalysisStateRepository()
        )

        self.arkham_max_age_hours = max(
            int(arkham_max_age_hours),
            1,
        )

    def analyze(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        normalized_asset = self._normalize_asset(
            asset
        )

        latest_event = self._load_latest_event(
            normalized_asset
        )

        snapshot = self.snapshot_builder.build(
            asset=normalized_asset,
            event=latest_event,
        )

        live_market_blocks = {
            "price": bool(snapshot.price),
            "funding": bool(snapshot.funding),
            "open_interest": bool(
                snapshot.open_interest
            ),
        }

        available_market_blocks = sum(
            live_market_blocks.values()
        )

        if available_market_blocks < 2:
            raise ValueError(
                f"{normalized_asset} is unavailable or has "
                "insufficient data on connected perpetual markets. "
                "Checked: OKX, Binance, Gate.io, Bybit."
            )

        facts = self.fact_builder.build(
            snapshot
        )

        evidence_nodes = (
            self.evidence_mapper.map_many(
                facts
            )
        )

        evidence_graph = (
            self.graph_builder.build(
                evidence_nodes
            )
        )

        decision_result = self.decision_engine.evaluate(
            asset=normalized_asset,
            facts=facts,
        )

        decision = decision_result.to_dict()

        trade = self.trade_engine.build(
            decision=decision,
            snapshot_quality=(
                snapshot.quality.to_dict()
            ),
            snapshot_id=snapshot.snapshot_id,
        )

        trade_payload = trade.to_dict()

        previous_state = (
            self.analysis_state_repository
            .get_latest(
                normalized_asset
            )
        )

        change = self._build_change(
            previous_state=previous_state,
            current_trade=trade_payload,
        )

        self.analysis_state_repository.save(
            asset=normalized_asset,
            snapshot_id=snapshot.snapshot_id,
            trade=trade_payload,
        )

        return {
            "status": "completed",
            "asset": normalized_asset,
            "arkham_event_found": (
                latest_event is not None
            ),
            "arkham_event": (
                self._event_to_dict(
                    latest_event
                )
                if latest_event
                else None
            ),
            "snapshot_id": (
                snapshot.snapshot_id
            ),
            "snapshot_quality": (
                snapshot.quality.to_dict()
            ),
            "snapshot": snapshot.to_dict(),
            "facts": [
                fact.to_dict()
                for fact in facts
            ],
            "evidence_graph": {
                "summary": (
                    evidence_graph.summary()
                ),
                "nodes": [
                    self._node_to_dict(
                        node
                    )
                    for node
                    in evidence_graph.nodes.values()
                ],
                "edges": [
                    self._edge_to_dict(
                        edge
                    )
                    for edge
                    in evidence_graph.edges
                ],
            },
            "decision": decision,
            "trade": trade_payload,
            "change": change,
            "mode": "Alpha decision support",
            "production_influence": False,
        }

    @staticmethod
    def _build_change(
        previous_state: Optional[Dict[str, Any]],
        current_trade: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not previous_state:
            return {
                "available": False,
                "reason": "first_analysis",
            }

        previous_trade = (
            previous_state.get("payload")
            or {}
        )

        previous_readiness = float(
            previous_trade.get(
                "trade_readiness"
            )
            or 0.0
        )

        current_readiness = float(
            current_trade.get(
                "trade_readiness"
            )
            or 0.0
        )

        previous_confidence = float(
            previous_trade.get(
                "confidence"
            )
            or 0.0
        )

        current_confidence = float(
            current_trade.get(
                "confidence"
            )
            or 0.0
        )

        previous_missing = set(
            previous_trade.get(
                "missing_confirmations"
            )
            or []
        )

        current_missing = set(
            current_trade.get(
                "missing_confirmations"
            )
            or []
        )

        return {
            "available": True,
            "previous_analyzed_at": (
                previous_state.get(
                    "analyzed_at"
                )
            ),
            "previous_status": (
                previous_trade.get("status")
            ),
            "current_status": (
                current_trade.get("status")
            ),
            "status_changed": (
                previous_trade.get("status")
                != current_trade.get("status")
            ),
            "previous_bias": (
                previous_trade.get("bias")
            ),
            "current_bias": (
                current_trade.get("bias")
            ),
            "bias_changed": (
                previous_trade.get("bias")
                != current_trade.get("bias")
            ),
            "readiness_change": round(
                current_readiness
                - previous_readiness,
                1,
            ),
            "confidence_change": round(
                current_confidence
                - previous_confidence,
                1,
            ),
            "new_confirmations": sorted(
                previous_missing
                - current_missing
            ),
            "lost_confirmations": sorted(
                current_missing
                - previous_missing
            ),
        }

    def _load_latest_event(
        self,
        asset: str,
    ) -> Optional[MarketEvent]:
        cutoff = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                hours=self.arkham_max_age_hours
            )
        )

        with sqlite3.connect(
            DB_PATH
        ) as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                """
                SELECT
                    source,
                    event_type,
                    asset,
                    amount_usd,
                    from_entity,
                    to_entity,
                    network,
                    tx_hash,
                    timestamp
                FROM events
                WHERE UPPER(asset) = ?
                  AND LOWER(source) = 'arkham'
                  AND timestamp >= ?
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
                """,
                (
                    asset,
                    cutoff.replace(
                        tzinfo=None
                    ).isoformat(),
                ),
            ).fetchone()

        if row is None:
            return None

        timestamp = self._parse_datetime(
            row["timestamp"]
        )

        return MarketEvent(
            source=row["source"] or "arkham",
            event_type=(
                row["event_type"]
                or "whale_transfer"
            ),
            asset=row["asset"] or asset,
            amount_usd=float(
                row["amount_usd"]
                or 0.0
            ),
            from_entity=row["from_entity"],
            to_entity=row["to_entity"],
            network=row["network"],
            tx_hash=row["tx_hash"],
            timestamp=timestamp,
            raw={
                "loaded_from": "events",
                "historical_event": True,
            },
        )

    @staticmethod
    def _event_to_dict(
        event: MarketEvent,
    ) -> Dict[str, Any]:
        return {
            "source": event.source,
            "event_type": event.event_type,
            "asset": event.asset,
            "amount_usd": event.amount_usd,
            "from_entity": event.from_entity,
            "to_entity": event.to_entity,
            "network": event.network,
            "tx_hash": event.tx_hash,
            "timestamp": (
                event.timestamp.isoformat()
                if event.timestamp
                else None
            ),
        }

    @staticmethod
    def _node_to_dict(
        node: Any,
    ) -> Dict[str, Any]:
        return {
            "id": node.id,
            "fact_type": node.fact_type,
            "title": node.title,
            "direction": node.direction,
            "confidence": node.confidence,
            "strength": node.strength,
            "source": node.source,
            "weight": node.weight,
            "metadata": dict(
                node.metadata
            ),
        }

    @staticmethod
    def _edge_to_dict(
        edge: Any,
    ) -> Dict[str, Any]:
        return {
            "source": edge.source,
            "target": edge.target,
            "relation": edge.relation,
            "strength": edge.strength,
        }

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:
        if isinstance(
            value,
            datetime,
        ):
            result = value
        else:
            raw = str(
                value or ""
            ).strip()

            if not raw:
                return datetime.now(
                    timezone.utc
                )

            result = datetime.fromisoformat(
                raw.replace(
                    "Z",
                    "+00:00",
                )
            )

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result.astimezone(
            timezone.utc
        )

    @staticmethod
    def _normalize_asset(
        asset: str,
    ) -> str:
        value = str(
            asset or ""
        ).strip().upper()

        value = value.replace(
            "/USDT",
            "",
        )

        value = value.replace(
            "-USDT",
            "",
        )

        value = value.replace(
            "_USDT",
            "",
        )

        if value.endswith(
            "USDT"
        ):
            value = value[:-4]

        if not value:
            raise ValueError(
                "asset cannot be empty."
            )

        if not value.replace(
            "-",
            "",
        ).isalnum():
            raise ValueError(
                "asset contains unsupported characters."
            )

        return value
