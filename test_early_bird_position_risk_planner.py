from app.intelligence.early_bird.perpetual_position_preparation import (
    PerpetualPositionPreparation,
)

from app.intelligence.early_bird.position_risk_planner import (
    PositionRiskPlanner,
)


def test_reversal_gets_reduced_risk():

    preparation = PerpetualPositionPreparation(
        asset="HYPE",
        direction="SHORT",
        entry_mode="LIMIT",
        risk_allocation=5.0,
        leverage_limit=5,
        dca_allowed=False,
        reason="reversal setup",
    )

    result = PositionRiskPlanner().plan(
        preparation,
        confidence=90.0,
        risk_score=20.0,
        news_risk=15.0,
        setup_type="REVERSAL",
    )

    assert result.risk_mode == "REDUCED"
    assert result.max_leverage <= 3



def test_high_news_risk_restricted():

    preparation = PerpetualPositionPreparation(
        asset="BTC",
        direction="LONG",
        entry_mode="LIMIT",
        risk_allocation=5.0,
        leverage_limit=5,
        dca_allowed=True,
        reason="trend",
    )

    result = PositionRiskPlanner().plan(
        preparation,
        confidence=85.0,
        risk_score=20.0,
        news_risk=90.0,
        setup_type="CONTINUATION",
    )

    assert result.risk_mode == "RESTRICTED"
