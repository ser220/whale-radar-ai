from html import escape
from typing import Any, Dict, List


STATUS_STYLE = {
    "NO_TRADE": ("⚫", "NO TRADE"),
    "WATCH": ("⚪", "WATCH"),
    "PREPARE": ("🟠", "PREPARE"),
    "READY": ("🔵", "READY"),
    "ACTION": ("🟢", "ACTION"),
}


def _number(
    value: Any,
    digits: int = 1,
) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "0.0"


def _progress_bar(
    value: Any,
    size: int = 10,
) -> str:
    try:
        score = max(
            0.0,
            min(float(value), 100.0),
        )
    except (TypeError, ValueError):
        score = 0.0

    filled = round(
        score / 100.0 * size
    )

    return (
        "█" * filled
        + "░" * (size - filled)
    )


def _top_reasons(
    reasons: List[Any],
    limit: int = 3,
) -> List[str]:
    return [
        escape(str(item))
        for item in reasons[:limit]
        if item
    ]


def format_analyze_result(
    result: Dict[str, Any],
) -> str:
    trade = result.get("trade") or {}
    quality = (
        result.get("snapshot_quality")
        or {}
    )

    asset = escape(
        str(
            trade.get("asset")
            or result.get("asset")
            or "UNKNOWN"
        )
    )

    status = str(
        trade.get("status")
        or "NO_TRADE"
    ).upper()

    icon, status_label = (
        STATUS_STYLE.get(
            status,
            ("⚪", status),
        )
    )

    bias = escape(
        str(
            trade.get("bias")
            or "NEUTRAL"
        )
    )

    readiness = float(
        trade.get(
            "trade_readiness"
        )
        or 0.0
    )

    confidence = _number(
        trade.get("confidence")
    )

    institutional_score = _number(
        trade.get(
            "institutional_score"
        )
    )

    stability = _number(
        trade.get(
            "hypothesis_stability"
        )
    )

    velocity = escape(
        str(
            trade.get(
                "market_velocity"
            )
            or "UNKNOWN"
        )
    )

    eta = escape(
        str(
            trade.get("eta")
            or "UNKNOWN"
        )
    )

    risk = escape(
        str(
            trade.get("risk")
            or "UNKNOWN"
        )
    )

    action = escape(
        str(
            trade.get("action")
            or "No action available."
        )
    )

    snapshot_quality = _number(
        quality.get("overall")
    )

    remaining = max(
        0.0,
        90.0 - readiness,
    )

    lines = [
        "🧠 <b>Whale Radar Alpha</b>",
        "<i>Live decision support</i>",
        "",
        f"<b>{asset}</b>",
        f"{icon} <b>{status_label} {bias}</b>",
        "",
        "<b>Trade Readiness</b>",
        (
            f"<code>{_progress_bar(readiness)}</code> "
            f"<b>{readiness:.1f}/100</b>"
        ),
    ]

    if status != "ACTION":
        lines.append(
            f"Distance to ACTION: "
            f"{remaining:.1f} pts"
        )

    lines.extend([
        "",
        f"<b>Confidence:</b> {confidence}%",
        (
            "<b>Institutional Score:</b> "
            f"{institutional_score}/100"
        ),
        (
            "<b>Hypothesis Stability:</b> "
            f"{stability}%"
        ),
        f"<b>Risk:</b> {risk}",
        f"<b>Velocity:</b> {velocity}",
        f"<b>ETA to Action:</b> {eta}",
        "",
        "<b>Action</b>",
        action,
    ])

    reasons = _top_reasons(
        trade.get("reasons") or []
    )

    if reasons:
        lines.extend([
            "",
            "<b>Top Evidence</b>",
        ])

        for item in reasons:
            lines.append(
                f"• {item}"
            )

    missing = [
        escape(str(item))
        for item in (
            trade.get(
                "missing_confirmations"
            )
            or []
        )[:4]
        if item
    ]

    change = result.get("change") or {}

    if change.get("available"):
        readiness_change = float(
            change.get("readiness_change")
            or 0.0
        )

        confidence_change = float(
            change.get("confidence_change")
            or 0.0
        )

        new_confirmations = [
            escape(str(item))
            for item in (
                change.get(
                    "new_confirmations"
                )
                or []
            )
        ]

        lost_confirmations = [
            escape(str(item))
            for item in (
                change.get(
                    "lost_confirmations"
                )
                or []
            )
        ]

        has_meaningful_change = any([
            bool(
                change.get(
                    "status_changed"
                )
            ),
            bool(
                change.get(
                    "bias_changed"
                )
            ),
            abs(readiness_change) >= 0.1,
            abs(confidence_change) >= 0.1,
            bool(new_confirmations),
            bool(lost_confirmations),
        ])

        if has_meaningful_change:
            lines.extend([
                "",
                "🔄 <b>Since Last Analysis</b>",
            ])

            if change.get(
                "status_changed"
            ):
                lines.append(
                    "Status: "
                    f"{escape(str(change.get('previous_status') or 'UNKNOWN'))}"
                    " → "
                    f"{escape(str(change.get('current_status') or 'UNKNOWN'))}"
                )

            if change.get(
                "bias_changed"
            ):
                lines.append(
                    "Bias: "
                    f"{escape(str(change.get('previous_bias') or 'UNKNOWN'))}"
                    " → "
                    f"{escape(str(change.get('current_bias') or 'UNKNOWN'))}"
                )

            if abs(readiness_change) >= 0.1:
                sign = (
                    "+"
                    if readiness_change > 0
                    else ""
                )

                lines.append(
                    "Readiness: "
                    f"{sign}{readiness_change:.1f}"
                )

            if abs(confidence_change) >= 0.1:
                sign = (
                    "+"
                    if confidence_change > 0
                    else ""
                )

                lines.append(
                    "Confidence: "
                    f"{sign}{confidence_change:.1f}%"
                )

            for item in new_confirmations:
                lines.append(
                    f"✅ Confirmed: {item}"
                )

            for item in lost_confirmations:
                lines.append(
                    f"⚠️ Lost: {item}"
                )

    if missing:
        lines.extend([
            "",
            "<b>Waiting For</b>",
        ])

        for item in missing:
            lines.append(
                f"• {item}"
            )

    lines.extend([
        "",
        (
            "<b>Snapshot Quality:</b> "
            f"{snapshot_quality}%"
        ),
        (
            "<b>Arkham Event:</b> "
            + (
                "active"
                if result.get(
                    "arkham_event_found"
                )
                else "not found"
            )
        ),
        "",
        "Mode: Alpha decision support",
        "No automatic execution.",
    ])

    return "\n".join(lines)
