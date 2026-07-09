from app.engine.adaptive_weights import get_adaptive_weights


def calculate_dynamic_confidence(
    probability: dict,
    campaign: dict,
    wallet_behaviour: dict,
    scenario: list,
    ai_decision: dict,
):
    weights = get_adaptive_weights()

    probability_score = max(
        probability.get("bearish", 0),
        probability.get("bullish", 0),
    )

    campaign_score = campaign.get("confidence", 50)

    wallet_score = (
        95
        if wallet_behaviour.get("confidence") == "Very High"
        else 70
    )

    scenario_score = (
        scenario[0]["probability"]
        if scenario else 50
    )

    decision_score = ai_decision.get("overall_confidence", 50)

    weighted = (
        probability_score * weights["Probability Engine"] +
        campaign_score * weights["Campaign Detector"] +
        wallet_score * weights["Wallet Behaviour"] +
        scenario_score * weights["Scenario Engine"] +
        decision_score * weights["Decision Engine"]
    )

    total_weight = (
        weights["Probability Engine"] +
        weights["Campaign Detector"] +
        weights["Wallet Behaviour"] +
        weights["Scenario Engine"] +
        weights["Decision Engine"]
    )

    confidence = round(weighted / total_weight, 1)

    return {
        "confidence": confidence,
        "old": decision_score,
        "difference": round(confidence - decision_score, 1),
    }


def format_dynamic_confidence(data):
    return (
        f"Current: {data['old']}/100\n"
        f"Dynamic: {data['confidence']}/100\n"
        f"Difference: {data['difference']:+.1f}"
    )
