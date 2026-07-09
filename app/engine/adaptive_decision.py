from app.engine.dynamic_confidence import calculate_dynamic_confidence


def build_adaptive_decision_shadow(
    probability: dict,
    ai_decision: dict,
    campaign: dict = None,
    wallet_behaviour: dict = None,
    scenario: list = None,
) -> dict:
    dynamic = calculate_dynamic_confidence(
        probability=probability,
        campaign=campaign or {},
        wallet_behaviour=wallet_behaviour or {},
        scenario=scenario or [],
        ai_decision=ai_decision,
    )

    difference = dynamic["difference"]

    if abs(difference) < 1:
        verdict = "No meaningful difference"
    elif difference > 0:
        verdict = "Adaptive model is more confident"
    else:
        verdict = "Adaptive model is less confident"

    return {
        "base_confidence": dynamic["old"],
        "adaptive_confidence": dynamic["confidence"],
        "difference": difference,
        "verdict": verdict,
    }


def format_adaptive_decision_shadow(data: dict) -> str:
    return (
        f"Current Confidence: {data['base_confidence']}/100\n"
        f"Adaptive Confidence: {data['adaptive_confidence']}/100\n"
        f"Difference: {data['difference']:+.1f}\n"
        f"Mode: Shadow only\n"
        f"Verdict: {data['verdict']}"
    )
