from datetime import datetime, timezone

from app.intelligence.arkham.runtime import (
    ArkhamRuntime,
)

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)

from app.intelligence.arkham.enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)


class MockCollector:

    def collect(self):

        return [
            ArkhamWhaleEvent(
                event_id="runtime-001",
                chain=ArkhamChain.ETHEREUM,
                event_type=(
                    ArkhamEventType.CEX_WITHDRAWAL
                ),
                direction=(
                    ArkhamFlowDirection.OUTFLOW
                ),
                asset="ETH",
                amount_usd=50_000_000,
                source_entity="Binance",
                destination_entity="Unknown Wallet",
                observed_at=datetime.now(
                    timezone.utc
                ),
            )
        ]


def test_arkham_runtime_builds_candidates():

    runtime = ArkhamRuntime(
        collector=MockCollector()
    )

    candidates = runtime.run_once()

    assert len(candidates) == 1

    candidate = candidates[0]

    assert (
        candidate.asset
        == "ETH"
    )

    assert (
        candidate.source
        == "arkham"
    )

    assert (
        candidate.metadata["amount_usd"]
        == 50_000_000
    )
