def calculate_confidence(score_data: dict) -> dict:
    score = score_data.get("score", 0)
    cluster = score_data.get("cluster", {})

    confidence = score

    count = cluster.get("count", 1)
    total_usd = cluster.get("total_usd", 0)

    if count >= 3:
        confidence += 10

    if total_usd >= 100_000_000:
        confidence += 10

    if total_usd >= 250_000_000:
        confidence += 10

    confidence = max(0, min(confidence, 100))

    if confidence >= 85:
        label = "Very High"
    elif confidence >= 70:
        label = "High"
    elif confidence >= 50:
        label = "Medium"
    else:
        label = "Low"

    return {
        "value": confidence,
        "label": label,
    }
