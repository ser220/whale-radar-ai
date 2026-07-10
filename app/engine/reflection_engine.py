from typing import Any, Dict, List, Optional


def build_ai_reflection(
    module_intelligence: Dict[str, Dict[str, Any]],
    outcome_v2: Dict[str, Any],
    lifecycle: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert lifecycle and module evaluations into structured AI reflection.

    Shadow mode only:
    - does not update learning tables;
    - does not change adaptive weights;
    - does not influence production decisions.
    """

    reflections: List[Dict[str, Any]] = []

    for module, evaluation in module_intelligence.items():
        score = _clamp(evaluation.get("score"))
        metrics = evaluation.get("metrics") or {}

        if module == "Probability Engine":
            reflection = _reflect_probability(
                score=score,
                metrics=metrics,
            )

        elif module == "Campaign Detector":
            reflection = _reflect_campaign(
                score=score,
                metrics=metrics,
            )

        elif module == "Wallet Behaviour":
            reflection = _reflect_wallet_behaviour(
                score=score,
                metrics=metrics,
            )

        elif module == "Scenario Engine":
            reflection = _reflect_scenario(
                score=score,
                metrics=metrics,
            )

        elif module == "Risk Engine":
            reflection = _reflect_risk(
                score=score,
                metrics=metrics,
            )

        elif module == "Decision Engine":
            reflection = _reflect_decision(
                score=score,
                metrics=metrics,
                outcome_v2=outcome_v2,
                lifecycle=lifecycle,
            )

        else:
            reflection = {
                "assessment": "No specialized reflection rule.",
                "lesson": evaluation.get(
                    "reason",
                    "No lesson available.",
                ),
                "recommendation": (
                    "Continue collecting validated outcomes."
                ),
                "suggested_weight_change": 0.0,
            }

        reflections.append({
            "module": module,
            "score": score,
            "status": _status(score),
            "assessment": reflection["assessment"],
            "lesson": reflection["lesson"],
            "recommendation": reflection["recommendation"],
            "suggested_weight_change": reflection[
                "suggested_weight_change"
            ],
            "mode": "Shadow only",
        })

    overall_score = _clamp(
        outcome_v2.get("score")
    )

    strongest = max(
        reflections,
        key=lambda item: item["score"],
        default=None,
    )

    weakest = min(
        reflections,
        key=lambda item: item["score"],
        default=None,
    )

    return {
        "overall_outcome_score": overall_score,
        "overall_quality": outcome_v2.get(
            "label",
            "Unknown",
        ),
        "lifecycle_state": lifecycle.get(
            "state",
            "Unknown",
        ),
        "reflections": reflections,
        "strongest_module": (
            strongest["module"]
            if strongest
            else None
        ),
        "weakest_module": (
            weakest["module"]
            if weakest
            else None
        ),
        "summary": _build_summary(
            overall_score=overall_score,
            strongest=strongest,
            weakest=weakest,
        ),
        "mode": "Shadow only",
    }


def format_ai_reflection(
    data: Dict[str, Any],
) -> str:
    lines = [
        "🪞 <b>AI Reflection</b>",
        "<i>Shadow only — no automatic changes applied</i>",
        "",
        f"Outcome V2: {data['overall_outcome_score']}/100",
        f"Quality: {data['overall_quality']}",
        f"Lifecycle State: {data['lifecycle_state']}",
        "",
    ]

    for item in data.get("reflections", []):
        change = item["suggested_weight_change"]

        if change > 0:
            change_text = f"+{change:.2f}"
        else:
            change_text = f"{change:.2f}"

        lines.extend([
            f"<b>{item['module']}</b>",
            f"Score: {item['score']}/100",
            f"Status: {item['status']}",
            f"Assessment: {item['assessment']}",
            f"Lesson: {item['lesson']}",
            f"Recommendation: {item['recommendation']}",
            (
                "Suggested Weight Change: "
                f"{change_text}"
            ),
            "",
        ])

    lines.extend([
        "────────────",
        f"Strongest Module: {data['strongest_module']}",
        f"Weakest Module: {data['weakest_module']}",
        f"Summary: {data['summary']}",
        "Mode: Shadow only",
    ])

    return "\n".join(lines)


def _reflect_probability(
    score: float,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    strength = _clamp(
        metrics.get("direction_strength")
    )
    dominance = _clamp(
        metrics.get("direction_dominance")
    )

    if score >= 75:
        return {
            "assessment": (
                "The predicted direction received strong "
                "market confirmation."
            ),
            "lesson": (
                f"Directional strength reached {strength}% "
                f"and dominance reached {dominance}%."
            ),
            "recommendation": (
                "Keep the current probability logic under observation."
            ),
            "suggested_weight_change": 0.03,
        }

    if score >= 45:
        return {
            "assessment": (
                "The predicted direction received partial confirmation."
            ),
            "lesson": (
                "Price moved in the expected direction, "
                "but the move was not dominant enough."
            ),
            "recommendation": (
                "Require additional market confirmation before "
                "assigning very high probability."
            ),
            "suggested_weight_change": 0.0,
        }

    return {
        "assessment": (
            "The predicted direction received weak confirmation."
        ),
        "lesson": (
            f"Expected-direction progress was only {strength}% "
            f"with {dominance}% directional dominance."
        ),
        "recommendation": (
            "Reduce confidence when favorable excursion is weak "
            "relative to adverse excursion."
        ),
        "suggested_weight_change": -0.03,
    }


def _reflect_campaign(
    score: float,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    progress = _clamp(
        metrics.get("target_progress_percent")
    )
    target_touched = bool(
        metrics.get("target_touched")
    )

    if target_touched or score >= 75:
        return {
            "assessment": (
                "The detected institutional campaign produced "
                "a meaningful market continuation."
            ),
            "lesson": (
                f"Campaign progress reached {progress}% "
                f"and target touch was {target_touched}."
            ),
            "recommendation": (
                "Preserve the current campaign classification rules."
            ),
            "suggested_weight_change": 0.03,
        }

    if progress >= 40:
        return {
            "assessment": (
                "The campaign produced a partial price response."
            ),
            "lesson": (
                "Institutional activity affected price, "
                "but continuation remained incomplete."
            ),
            "recommendation": (
                "Keep campaign detection, but reduce projected "
                "continuation confidence."
            ),
            "suggested_weight_change": 0.0,
        }

    return {
        "assessment": (
            "The detected campaign produced little continuation."
        ),
        "lesson": (
            f"Only {progress}% of the projected path was completed."
        ),
        "recommendation": (
            "Require stronger repetition, volume, or source "
            "confirmation before labeling a strong campaign."
        ),
        "suggested_weight_change": -0.03,
    }


def _reflect_wallet_behaviour(
    score: float,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    mfe = _number(
        metrics.get("mfe_percent")
    )
    mae = _number(
        metrics.get("mae_percent")
    )
    favorable = bool(
        metrics.get("current_favorable")
    )

    if score >= 75:
        return {
            "assessment": (
                "Wallet-flow interpretation was strongly confirmed."
            ),
            "lesson": (
                f"MFE {mfe}% clearly exceeded MAE {mae}%."
            ),
            "recommendation": (
                "Continue using the current wallet-behaviour mapping."
            ),
            "suggested_weight_change": 0.03,
        }

    if score >= 45:
        return {
            "assessment": (
                "Wallet behaviour received mixed confirmation."
            ),
            "lesson": (
                f"MFE was {mfe}% versus MAE {mae}%; "
                f"current state favorable: {favorable}."
            ),
            "recommendation": (
                "Combine wallet behaviour with liquidity and "
                "market-regime confirmation."
            ),
            "suggested_weight_change": 0.0,
        }

    return {
        "assessment": (
            "Wallet-flow interpretation was not confirmed strongly."
        ),
        "lesson": (
            f"Adverse movement {mae}% exceeded favorable "
            f"movement {mfe}%."
        ),
        "recommendation": (
            "Do not treat exchange flow alone as sufficient "
            "directional confirmation."
        ),
        "suggested_weight_change": -0.03,
    }


def _reflect_scenario(
    score: float,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    progress = _clamp(
        metrics.get("target_progress_percent")
    )
    target_touched = bool(
        metrics.get("target_touched")
    )

    if target_touched or score >= 75:
        return {
            "assessment": (
                "The primary scenario was substantially realized."
            ),
            "lesson": (
                f"Scenario progress reached {progress}%."
            ),
            "recommendation": (
                "Keep this scenario structure as a validated pattern."
            ),
            "suggested_weight_change": 0.03,
        }

    if progress >= 40:
        return {
            "assessment": (
                "The primary scenario was only partially realized."
            ),
            "lesson": (
                f"The market completed {progress}% "
                "of the projected path."
            ),
            "recommendation": (
                "Increase probability assigned to alternative scenarios."
            ),
            "suggested_weight_change": 0.0,
        }

    return {
        "assessment": (
            "The primary scenario did not develop as expected."
        ),
        "lesson": (
            f"Scenario completion remained at {progress}%."
        ),
        "recommendation": (
            "Lower primary-scenario confidence and improve "
            "alternative-scenario weighting."
        ),
        "suggested_weight_change": -0.03,
    }


def _reflect_risk(
    score: float,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    mae = _number(
        metrics.get("mae_percent")
    )
    stop_touched = metrics.get(
        "stop_touched"
    )

    if score >= 75:
        return {
            "assessment": (
                "Risk remained well controlled."
            ),
            "lesson": (
                f"MAE was limited to {mae}% "
                f"and stop touched was {stop_touched}."
            ),
            "recommendation": (
                "Preserve the current risk thresholds."
            ),
            "suggested_weight_change": 0.03,
        }

    if score >= 50:
        return {
            "assessment": (
                "Risk was acceptable but not optimal."
            ),
            "lesson": (
                f"MAE reached {mae}%."
            ),
            "recommendation": (
                "Review entry timing or stop placement, "
                "but do not penalize the risk model heavily."
            ),
            "suggested_weight_change": 0.0,
        }

    return {
        "assessment": (
            "Risk control was weak."
        ),
        "lesson": (
            f"MAE reached {mae}% and stop touched "
            f"was {stop_touched}."
        ),
        "recommendation": (
            "Tighten risk filters or delay entry until "
            "market confirmation."
        ),
        "suggested_weight_change": -0.03,
    }


def _reflect_decision(
    score: float,
    metrics: Dict[str, Any],
    outcome_v2: Dict[str, Any],
    lifecycle: Dict[str, Any],
) -> Dict[str, Any]:
    progress = _clamp(
        outcome_v2.get("target_progress_percent")
    )
    mfe = _number(
        outcome_v2.get("mfe_percent")
    )
    mae = _number(
        outcome_v2.get("mae_percent")
    )

    if score >= 75:
        return {
            "assessment": (
                "The final trading decision was useful."
            ),
            "lesson": (
                f"Outcome score was {score}; "
                f"MFE {mfe}% exceeded MAE {mae}%."
            ),
            "recommendation": (
                "Retain the decision framework for similar contexts."
            ),
            "suggested_weight_change": 0.03,
        }

    if score >= 45:
        return {
            "assessment": (
                "The decision was partially useful."
            ),
            "lesson": (
                f"Target progress reached {progress}%, "
                "but execution quality remained incomplete."
            ),
            "recommendation": (
                "Review timing, confirmation requirements, "
                "and target realism."
            ),
            "suggested_weight_change": 0.0,
        }

    return {
        "assessment": (
            "The final decision had low practical value."
        ),
        "lesson": (
            f"Outcome score was {score}; target progress "
            f"was only {progress}% and lifecycle state was "
            f"{lifecycle.get('state')}."
        ),
        "recommendation": (
            "Reduce urgency and require stronger confirmation "
            "before issuing a high-conviction trade action."
        ),
        "suggested_weight_change": -0.03,
    }


def _build_summary(
    overall_score: float,
    strongest: Optional[Dict[str, Any]],
    weakest: Optional[Dict[str, Any]],
) -> str:
    if overall_score >= 75:
        prefix = (
            "The forecast was broadly successful."
        )
    elif overall_score >= 45:
        prefix = (
            "The forecast produced partial value."
        )
    else:
        prefix = (
            "The forecast produced weak lifecycle performance."
        )

    if not strongest or not weakest:
        return prefix

    return (
        f"{prefix} The strongest component was "
        f"{strongest['module']} ({strongest['score']}/100), "
        f"while the weakest was "
        f"{weakest['module']} ({weakest['score']}/100)."
    )


def _status(
    score: float,
) -> str:
    if score >= 75:
        return "Strong ✅"

    if score >= 60:
        return "Acceptable 🟢"

    if score >= 40:
        return "Mixed 🟡"

    return "Weak ❌"


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
