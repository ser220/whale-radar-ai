from datetime import datetime, timezone

from app.decision.contracts import (
    DecisionRecord,
    DecisionType,
    DecisionState,
    DecisionContractVersion,
)

from app.decision.lifecycle import (
    DecisionLifecycle,
)

from app.execution.paper import (
    PaperTrade,
)

from app.execution.paper.decision_executor import (
    PaperDecisionExecutor,
)


def build_decision() -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision-001",
        candidate_reference="candidate-001",
        intelligence_reference="early_bird:candidate-001",
        decision_type=DecisionType.LONG,
        decision_state=DecisionState.CREATED,
        confidence=0.85,
        created_at=datetime.now(
            timezone.utc
        ),
        contract_version=DecisionContractVersion.V1,
    )


def test_approved_decision_executes_to_paper_trade():

    decision = build_decision()

    approved = (
        DecisionLifecycle.approve(
            decision
        )
    )

    trade = (
        PaperDecisionExecutor()
        .execute(
            decision=approved,
            symbol="BTCUSDT",
            price=65000.0,
            quantity=0.01,
        )
    )

    assert isinstance(
        trade,
        PaperTrade,
    )

    assert trade.symbol == "BTCUSDT"
    assert trade.side == "LONG"
    assert trade.entry_price == 65000.0
    assert trade.quantity == 0.01
    assert trade.status == "OPEN"
