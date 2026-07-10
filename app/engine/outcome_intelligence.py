from app.domain.prediction_lifecycle import PredictionLifecycle


def calculate_outcome_score(
    direction: str,
    entry_price: float,
    target_price: float,
    current_price: float,
    expected_move: float = 0,
    eta: str = "",
) -> dict:
    direction = (direction or "").lower()

    if not entry_price or not current_price:
        return {
            "score": 0,
            "direction_score": 0,
            "target_score": 0,
            "move_score": 0,
            "label": "Invalid data",
            "reason": "Missing entry or current price.",
        }

    if direction == "bearish":
        actual_move = ((current_price - entry_price) / entry_price) * 100
        target_hit = current_price <= target_price
        direction_correct = current_price < entry_price

    elif direction == "bullish":
        actual_move = ((current_price - entry_price) / entry_price) * 100
        target_hit = current_price >= target_price
        direction_correct = current_price > entry_price

    else:
        actual_move = 0
        target_hit = False
        direction_correct = False

    direction_score = 40 if direction_correct else 0
    target_score = 40 if target_hit else 0

    if expected_move:
        progress = min(abs(actual_move) / abs(expected_move), 1)
        move_score = round(progress * 20, 1)
    else:
        move_score = 0

    score = round(direction_score + target_score + move_score, 1)

    if score >= 85:
        label = "Excellent"
    elif score >= 70:
        label = "Good"
    elif score >= 50:
        label = "Partial"
    else:
        label = "Weak"

    return {
        "score": score,
        "direction_score": direction_score,
        "target_score": target_score,
        "move_score": move_score,
        "actual_move": round(actual_move, 2),
        "target_hit": target_hit,
        "direction_correct": direction_correct,
        "label": label,
        "reason": "Shadow scoring only. Does not affect learning yet.",
    }


def format_outcome_score(data: dict) -> str:
    return (
        f"Outcome Score: {data['score']}/100\n"
        f"Quality: {data['label']}\n"
        f"Direction Score: {data['direction_score']}/40\n"
        f"Target Score: {data['target_score']}/40\n"
        f"Move Score: {data['move_score']}/20\n"
        f"Actual Move: {data.get('actual_move', 0)}%\n"
        f"Target Hit: {data.get('target_hit')}\n"
        f"Direction Correct: {data.get('direction_correct')}\n"
        f"Mode: Shadow only"
    )
def calculate_outcome_score_v2(
    lifecycle: PredictionLifecycle,
) -> dict:
    direction_score = 0.0
    target_score = 0.0
    progress_score = 0.0
    mfe_score = 0.0
    mae_score = 0.0
    risk_score = 0.0

    current_move = lifecycle.current_move_percent

    if lifecycle.direction == "bullish":
        direction_correct = current_move > 0
    else:
        direction_correct = current_move < 0

    if direction_correct:
        direction_score = 25.0

    if lifecycle.target_touched:
        target_score = 25.0

    progress_score = round(
        min(
            max(lifecycle.target_progress_percent, 0.0),
            100.0,
        )
        / 100
        * 15,
        1,
    )

    expected_move = (
        abs(
            (
                lifecycle.target_price
                - lifecycle.entry_price
            )
            / lifecycle.entry_price
            * 100
        )
    )

    if expected_move > 0:
        mfe_ratio = min(
            lifecycle.mfe_percent / expected_move,
            1.0,
        )
        mfe_score = round(mfe_ratio * 15, 1)

    if lifecycle.mae_percent <= 0.5:
        mae_score = 10.0
    elif lifecycle.mae_percent <= 1.0:
        mae_score = 8.0
    elif lifecycle.mae_percent <= 2.0:
        mae_score = 6.0
    elif lifecycle.mae_percent <= 4.0:
        mae_score = 3.0
    else:
        mae_score = 0.0

    if lifecycle.stop_touched is None:
        risk_score = 5.0
    elif lifecycle.stop_touched is False:
        risk_score = 10.0
    else:
        risk_score = 0.0

    score = round(
        direction_score
        + target_score
        + progress_score
        + mfe_score
        + mae_score
        + risk_score,
        1,
    )

    if score >= 90:
        label = "Excellent"
    elif score >= 75:
        label = "Strong"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Partial"
    else:
        label = "Weak"

    return {
        "score": score,
        "label": label,
        "direction_score": direction_score,
        "target_score": target_score,
        "progress_score": progress_score,
        "mfe_score": mfe_score,
        "mae_score": mae_score,
        "risk_score": risk_score,
        "direction_correct": direction_correct,
        "target_touched": lifecycle.target_touched,
        "stop_touched": lifecycle.stop_touched,
        "target_progress_percent": (
            lifecycle.target_progress_percent
        ),
        "mfe_percent": lifecycle.mfe_percent,
        "mae_percent": lifecycle.mae_percent,
        "current_move_percent": current_move,
        "state": lifecycle.state,
        "mode": "Shadow only",
    }


def format_outcome_score_v2(data: dict) -> str:
    return (
        f"Outcome V2 Score: {data['score']}/100\n"
        f"Quality: {data['label']}\n"
        f"Direction: {data['direction_score']}/25\n"
        f"Target Touch: {data['target_score']}/25\n"
        f"Target Progress: {data['progress_score']}/15\n"
        f"MFE Quality: {data['mfe_score']}/15\n"
        f"MAE Quality: {data['mae_score']}/10\n"
        f"Risk Control: {data['risk_score']}/10\n"
        f"────────────\n"
        f"MFE: {data['mfe_percent']}%\n"
        f"MAE: {data['mae_percent']}%\n"
        f"Progress: {data['target_progress_percent']}%\n"
        f"State: {data['state']}\n"
        f"Mode: {data['mode']}"
    )
