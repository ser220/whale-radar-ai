from app.engine.dynamic_confidence import calculate_dynamic_confidence
from app.engine.pattern_confidence import calculate_pattern_confidence
from app.engine.adaptive_weights import get_adaptive_weights


def build_meta_decision(
    asset,
    direction,
    probability,
    campaign,
    wallet_behaviour,
    market_regime,
    market_heat,
    market_scenarios,
    ai_decision,
):
    dynamic = calculate_dynamic_confidence(
        probability=probability,
        campaign=campaign,
        wallet_behaviour=wallet_behaviour,
        scenario=market_scenarios,
        ai_decision=ai_decision,
    )

    pattern = calculate_pattern_confidence(
        asset=asset,
        direction=direction,
        market_regime=market_regime,
        market_heat=market_heat,
        wallet_behaviour=wallet_behaviour.get("behaviour", "Unknown"),
        current_confidence=ai_decision["overall_confidence"],
    )

    base = ai_decision["overall_confidence"]
    dynamic_score = dynamic["confidence"]
    pattern_score = pattern["pattern"]
    weights = get_adaptive_weights()

    base_weight = weights.get("Decision Engine", 1.0)

    dynamic_weight = (
        weights.get("Probability Engine", 1.0)
        + weights.get("Campaign Detector", 1.0)
        + weights.get("Wallet Behaviour", 1.0)
    ) / 3

    pattern_weight = weights.get("Scenario Engine", 1.0)

    total_weight = base_weight + dynamic_weight + pattern_weight

    final = round(
        (
            base * base_weight
            + dynamic_score * dynamic_weight
            + pattern_score * pattern_weight
        ) / total_weight,
        1,
    )

    return {
        "base": base,
        "dynamic": dynamic_score,
        "pattern": pattern_score,
        "final": final,
        "weights": {
            "base": round(base_weight, 2),
            "dynamic": round(dynamic_weight, 2),
            "pattern": round(pattern_weight, 2),
        },
    }

def format_meta_decision(data):
    weights = data.get("weights", {})

    return (
        f"Base AI: {data['base']}/100 "
        f"(w x{weights.get('base', 1.0)})\n"
        f"Dynamic: {data['dynamic']}/100 "
        f"(w x{weights.get('dynamic', 1.0)})\n"
        f"Pattern: {data['pattern']}/100 "
        f"(w x{weights.get('pattern', 1.0)})\n"
        f"────────────\n"
        f"Meta Score: {data['final']}/100"
    )
