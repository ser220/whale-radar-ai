def calculate_self_confidence(
    meta_decision: dict,
    pattern_confidence: dict,
    context_score: float,
    module_score: float,
) -> dict:
    meta_score = meta_decision.get("final", 50)

    pattern_seen = pattern_confidence.get("seen", 0)

    confidence = 50
    reasons = []

    if meta_score >= 85:
        confidence += 10
        reasons.append("Meta score is strong.")
    elif meta_score < 70:
        confidence -= 10
        reasons.append("Meta score is not strong enough.")

    if pattern_seen >= 20:
        confidence += 15
        reasons.append("Pattern memory has enough historical samples.")
    elif pattern_seen >= 10:
        confidence += 8
        reasons.append("Pattern memory has moderate history.")
    else:
        confidence -= 10
        reasons.append("Pattern memory is still limited.")

    if context_score >= 80:
        confidence += 10
        reasons.append("Context learning supports the setup.")
    elif context_score <= 50:
        confidence -= 5
        reasons.append("Context learning is still insufficient.")

    if module_score >= 80:
        confidence += 10
        reasons.append("Module learning reliability is strong.")
    elif module_score <= 50:
        confidence -= 10
        reasons.append("Module learning reliability is weak or immature.")

    confidence = max(0, min(100, round(confidence, 1)))

    if confidence >= 85:
        label = "High Trust"
    elif confidence >= 70:
        label = "Medium-High Trust"
    elif confidence >= 55:
        label = "Medium Trust"
    else:
        label = "Low / Early Learning Trust"

    return {
        "score": confidence,
        "label": label,
        "reasons": reasons,
    }


def format_self_confidence(data: dict) -> str:
    lines = [
        f"Self Confidence: {data['score']}/100",
        f"AI Trust: {data['label']}",
        "",
        "Reasons:",
    ]

    for reason in data.get("reasons", []):
        lines.append(f"• {reason}")

    return "\n".join(lines)
