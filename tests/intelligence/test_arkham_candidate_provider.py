from datetime import datetime, timezone

from app.intelligence.arkham.provider import (
    ArkhamCandidateProvider,
)

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
                event_id="provider-001",
                chain=ArkhamChain.ETHEREUM,
                event_type=(
                    ArkhamEventType.CEX_WITHDRAWAL
                ),
                direction=(
                    ArkhamFlowDirection.OUTFLOW
                ),
                asset="ETH",
                amount_usd=75_000_000,
                source_entity="Coinbase",
                destination_entity="Unknown Wallet",
                observed_at=datetime.now(
                    timezone.utc
                ),
            )
        ]


def test_arkham_candidate_provider():

    runtime = ArkhamRuntime(
        collector=MockCollector()
    )

    provider = ArkhamCandidateProvider(
        runtime=runtime
    )

    candidates = (
        provider.collect_candidates()
    )

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
        == 75_000_000
    )
