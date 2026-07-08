from app.engine.institutional_leaders import get_institutional_leaders


def build_market_snapshot():
    leaders = get_institutional_leaders(20)

    if not leaders:
        return {
            "leaders": [],
            "market_score": 0,
            "market_state": "No data",
        }

    avg_score = sum(x["score"] for x in leaders) / len(leaders)

    if avg_score >= 85:
        state = "🔥 Institutional Risk-On"

    elif avg_score >= 70:
        state = "🟢 Strong Participation"

    elif avg_score >= 55:
        state = "🟡 Neutral"

    elif avg_score >= 40:
        state = "🟠 Weak"

    else:
        state = "🔴 Risk-Off"

    return {
        "leaders": leaders,
        "market_score": round(avg_score),
        "market_state": state,
    }
