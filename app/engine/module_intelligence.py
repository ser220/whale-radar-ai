from typing import Any, Dict, Optional


PASS_THRESHOLD = 60.0


def evaluate_module_intelligence(
    outcome_v2: Dict[str, Any],
    lifecycle: Dict[str, Any],
    ai_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Module-specific evaluation based on PredictionLifecycle.

    Shadow mode only:
    - does not update module_learning;
    - does not influence Meta Decision;
    - evaluates every module by its own responsibility.
    """

    snapshot = ai_snapshot or {}

    entry_price = _positive_number(
        lifecycle.get("entry_price")
    )
    target_price = _positive_number(
        lifecycle.get("target_price")
    )

    mfe = max(
        _number(lifecycle.get("mfe_percent")),
        0.0,
    )
    mae = max(
        _number(lifecycle.get("mae_percent")),
        0.0,
    )
    progress = _clamp(
        lifecycle.get("target_progress_percent")
    )

    current_move = _number(
        lifecycle.get("current_move_percent")
    )

    target_touched = bool(
        lifecycle.get("target_touched")
    )
    stop_touched = lifecycle.get("stop_touched")

    expected_move = _expected_move_percent(
        entry_price=entry_price,
        target_price=target_price,
    )

    direction_strength = _ratio_score(
        numerator=mfe,
        denominator=expected_move,
    )

    direction_dominance = _direction_dominance(
        mfe=mfe,
        mae=mae,
    )

    favorable_current = _current_is_favorable(
        direction=lifecycle.get("direction"),
        current_move=current_move,
    )

    probability_score = round(
        direction_strength * 0.60
        + direction_dominance * 0.40,
        1,
    )

    wallet_score = round(
        direction_dominance * 0.55
        + direction_strength * 0.30
        + (15.0 if favorable_current else 0.0),
        1,
    )

    campaign_score = round(
        progress * 0.60
        + direction_dominance * 0.20
        + (20.0 if target_touched else 0.0),
        1,
    )

    scenario_score = round(
        progress * 0.70
        + direction_strength * 0.15
        + (15.0 if target_touched else 0.0),
        1,
    )

    risk_score = _calculate_risk_score(
        mae=mae,
        stop_touched=stop_touched,
    )

    decision_score = _clamp(
        outcome_v2.get("score")
    )

    return {
        "Probability Engine": _result(
            score=probability_score,
            reason=(
                f"Favorable excursion reached "
                f"{round(direction_strength, 1)}% of the expected move; "
                f"directional dominance was "
                f"{round(direction_dominance, 1)}%."
            ),
            metrics={
                "direction_strength": round(
                    direction_strength,
                    1,
                ),
                "direction_dominance": round(
                    direction_dominance,
                    1,
                ),
                "mfe_percent": round(mfe, 4),
                "mae_percent": round(mae, 4),
            },
        ),

        "Campaign Detector": _result(
            score=campaign_score,
            reason=(
                f"Campaign produced {round(progress, 2)}% "
                f"target progress; target touched: "
                f"{target_touched}."
            ),
            metrics={
                "target_progress_percent": round(
                    progress,
                    2,
                ),
                "target_touched": target_touched,
                "campaign_confidence": _extract_confidence(
                    snapshot.get("campaign")
                ),
            },
        ),

        "Wallet Behaviour": _result(
            score=wallet_score,
            reason=(
                f"Wallet-flow direction produced "
                f"MFE {round(mfe, 4)}% versus "
                f"MAE {round(mae, 4)}%; "
                f"latest price remains favorable: "
                f"{favorable_current}."
            ),
            metrics={
                "mfe_percent": round(mfe, 4),
                "mae_percent": round(mae, 4),
                "direction_dominance": round(
                    direction_dominance,
                    1,
                ),
                "current_favorable": favorable_current,
            },
        ),

        "Scenario Engine": _result(
            score=scenario_score,
            reason=(
                f"Primary scenario completed "
                f"{round(progress, 2)}% of the projected path; "
                f"target touched: {target_touched}."
            ),
            metrics={
                "target_progress_percent": round(
                    progress,
                    2,
                ),
                "direction_strength": round(
                    direction_strength,
                    1,
                ),
                "target_touched": target_touched,
            },
        ),

        "Risk Engine": _result(
            score=risk_score,
            reason=(
                f"Maximum adverse excursion was "
                f"{round(mae, 4)}%; "
                f"stop touched: {stop_touched}."
            ),
            metrics={
                "mae_percent": round(mae, 4),
                "stop_touched": stop_touched,
            },
        ),

        "Decision Engine": _result(
            score=decision_score,
            reason=(
                f"Overall lifecycle Outcome V2 score was "
                f"{round(decision_score, 1)}/100."
            ),
            metrics={
                "outcome_v2_score": round(
                    decision_score,
                    1,
                ),
                "state": lifecycle.get("state"),
                "target_touched": target_touched,
            },
        ),
    }


def format_module_intelligence(
    results: Dict[str, Dict[str, Any]],
) -> str:
    lines = [
        "🧠 <b>Module Intelligence</b>",
        "<i>Shadow only — production learning is unchanged</i>",
        "",
    ]

    for module, data in results.items():
        status = (
            "PASS ✅"
            if data["passed"]
            else "FAIL ❌"
        )

        lines.extend([
            f"<b>{module}</b>",
            f"Score: {data['score']}/100",
            f"Status: {status}",
            f"Reason: {data['reason']}",
            "",
        ])

    return "\n".join(lines).strip()


def _calculate_risk_score(
    mae: float,
    stop_touched: Any,
) -> float:
    if stop_touched is True:
        return 0.0

    if mae <= 0.5:
        base = 100.0
    elif mae <= 1.0:
        base = 85.0
    elif mae <= 2.0:
        base = 70.0
    elif mae <= 3.0:
        base = 55.0
    elif mae <= 5.0:
        base = 30.0
    else:
        base = 10.0

    if stop_touched is None:
        base -= 5.0

    return _clamp(base)


def _direction_dominance(
    mfe: float,
    mae: float,
) -> float:
    total = mfe + mae

    if total <= 0:
        return 0.0

    return _clamp(
        mfe / total * 100
    )


def _ratio_score(
    numerator: float,
    denominator: float,
) -> float:
    if denominator <= 0:
        return 0.0

    return _clamp(
        numerator / denominator * 100
    )


def _expected_move_percent(
    entry_price: float,
    target_price: float,
) -> float:
    if entry_price <= 0 or target_price <= 0:
        return 0.0

    return abs(
        (target_price - entry_price)
        / entry_price
        * 100
    )


def _current_is_favorable(
    direction: Any,
    current_move: float,
) -> bool:
    normalized = str(
        direction or ""
    ).lower().strip()

    if normalized == "bullish":
        return current_move > 0

    if normalized == "bearish":
        return current_move < 0

    return False


def _extract_confidence(
    value: Any,
) -> Any:
    if isinstance(value, dict):
        return value.get("confidence")

    return None


def _result(
    score: float,
    reason: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    normalized = round(
        _clamp(score),
        1,
    )

    return {
        "score": normalized,
        "passed": normalized >= PASS_THRESHOLD,
        "threshold": PASS_THRESHOLD,
        "reason": reason,
        "metrics": metrics,
        "mode": "Shadow only",
    }


def _positive_number(
    value: Any,
) -> float:
    number = _number(value)

    return number if number > 0 else 0.0


def _number(
    value: Any,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(
    value: Any,
) -> float:
    return max(
        0.0,
        min(
            100.0,
            _number(value),
        ),
    )
