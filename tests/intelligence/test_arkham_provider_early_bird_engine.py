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

from app.intelligence.early_bird.engine import (
    EarlyBirdEngine,
)


class MockCollector:

    def collect(self):

        return [
            ArkhamWhaleEvent(
                event_id="arkham-engine-001",
                chain=ArkhamChain.ETHEREUM,
                event_type=(
                    ArkhamEventType.CEX_WITHDRAWAL
                ),
                direction=(
                    ArkhamFlowDirection.OUTFLOW
                ),
                asset="ETH",
                amount_usd=100_000_000,
                source_entity="Binance",
                destination_entity="Unknown Wallet",
                observed_at=datetime.now(
                    timezone.utc
                ),
            )
        ]


def test_arkham_candidate_reaches_early_bird_engine():

    runtime = ArkhamRuntime(
        collector=MockCollector()
    )

    provider = ArkhamCandidateProvider(
        runtime=runtime
    )

    candidates = (
        provider.collect_candidates()
    )

    engine = EarlyBirdEngine()

    assessments = (
        engine.rank_candidates(
            candidates
        )
    )

    assert len(assessments) == 1

    assessment = assessments[0]

    assert (
        assessment.asset
        == "ETH"
    )

    assert (
        assessment.rank
        == 1
    )

    assert (
        assessment.source_event_ids[0]
        == "arkham-engine-001"
    )
