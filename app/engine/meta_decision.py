from app.engine.adaptive_weights import get_adaptive_weights
from app.engine.context_learning import get_context_stats
from app.engine.dynamic_confidence import calculate_dynamic_confidence
from app.engine.module_learning import get_module_learning_stats
from app.engine.pattern_confidence import calculate_pattern_confidence


def get_context_score(market_regime, market_heat, wallet_behaviour):
    rows = get_context_stats()

    for row in rows:
        if (
            row["market_regime"] == market_regime
            and row["market_heat"] == market_heat
            and row["wallet_behaviour"] == wallet_behaviour
        ):
            if row["predictions"] < 10:
                return 50
            return row["accuracy"]

    return 50


def get_module_score():
    rows = get_module_learning_stats()

    valid = [
        row["accuracy"]
        for row in rows
        if row["predictions"] >= 10
    ]

    if not valid:
        return 50

    return round(sum(valid) / len(valid), 1)


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

    context_score = get_context_score(
        market_regime,
        market_heat,
        wallet_behaviour.get("behaviour", "Unknown"),
    )

    module_score = get_module_score()

    weights = get_adaptive_weights()

    base_weight = weights.get("Decision Engine", 1.0)

    dynamic_weight = (
        weights.get("Probability Engine", 1.0)
        + weights.get("Campaign Detector", 1.0)
        + weights.get("Wallet Behaviour", 1.0)
    ) / 3

    pattern_weight = weights.get("Scenario Engine", 1.0)
    context_weight = 0.20
    module_weight = 0.15

    total_weight = (
        base_weight
        + dynamic_weight
        + pattern_weight
        + context_weight
        + module_weight
    )

    final = round(
        (
            base * base_weight
            + dynamic_score * dynamic_weight
            + pattern_score * pattern_weight
            + context_score * context_weight
            + module_score * module_weight
        ) / total_weight,
        1,
    )

    contributors = [
        {
            "name": "Base AI Decision",
            "score": base,
            "weight": round(base_weight, 2),
            "impact": round(base * base_weight, 1),
        },
        {
            "name": "Dynamic Confidence",
            "score": dynamic_score,
            "weight": round(dynamic_weight, 2),
            "impact": round(dynamic_score * dynamic_weight, 1),
        },
        {
            "name": "Pattern Confidence",
            "score": pattern_score,
            "weight": round(pattern_weight, 2),
            "impact": round(pattern_score * pattern_weight, 1),
        },
        {
            "name": "Context Learning",
            "score": context_score,
            "weight": context_weight,
            "impact": round(context_score * context_weight, 1),
        },
        {
            "name": "Module Learning",
            "score": module_score,
            "weight": module_weight,
            "impact": round(module_score * module_weight, 1),
        },
    ]

    return {
        "base": base,
        "dynamic": dynamic_score,
        "pattern": pattern_score,
        "context": context_score,
        "module_learning": module_score,
        "final": final,
        "weights": {
            "base": round(base_weight, 2),
            "dynamic": round(dynamic_weight, 2),
            "pattern": round(pattern_weight, 2),
            "context": context_weight,
            "module_learning": module_weight,
        },
        "contributors": contributors,
    }


def format_meta_decision(data):
    weights = data.get("weights", {})
    contributors = data.get("contributors", [])

    lines = [
        f"Base AI: {data['base']}/100 (w x{weights.get('base', 1.0)})",
        f"Dynamic: {data['dynamic']}/100 (w x{weights.get('dynamic', 1.0)})",
        f"Pattern: {data['pattern']}/100 (w x{weights.get('pattern', 1.0)})",
        f"Context: {data['context']}/100 (w x{weights.get('context', 0.2)})",
        f"Module Learning: {data['module_learning']}/100 (w x{weights.get('module_learning', 0.15)})",
        "────────────",
        f"Meta Score: {data['final']}/100",
        "",
        "Why:",
    ]

    for c in contributors:
        lines.append(
            f"• {c['name']}: "
            f"{c['score']}/100 × {c['weight']} = {c['impact']}"
        )

    return "\n".join(lines)
