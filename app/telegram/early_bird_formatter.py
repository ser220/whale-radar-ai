"""Telegram HTML formatter for read-only Early Bird previews."""

from html import escape
from typing import Any, List

from app.intelligence.early_bird.scanner import (
    EarlyBirdScanResult,
)


SEPARATOR = "━━━━━━━━━━━━━━━━━━"


def _score(value: Any) -> str:
    if value is None:
        return "N/A"

    try:
        return "{0:.2f}".format(float(value))
    except (TypeError, ValueError):
        return "N/A"


def _availability(
    item: Any,
    factor_name: str,
) -> str:
    factor = item.build_result.factor_values.get(
        factor_name
    )

    if factor is None:
        return "UNAVAILABLE"

    return factor.availability.value


def _warnings(item: Any) -> List[str]:
    values = tuple(
        str(value).strip()
        for value in item.assessment.warnings
        if str(value).strip()
    )

    return list(values)


def format_early_bird_shadow_preview(
    scan: EarlyBirdScanResult,
) -> str:
    """Format one Early Bird scan as a read-only Telegram preview."""

    if not isinstance(scan, EarlyBirdScanResult):
        raise TypeError(
            "scan must be an EarlyBirdScanResult"
        )

    lines = [
        "🧪 <b>Early Bird Live Test</b>",
        "<b>SHADOW / READ-ONLY</b>",
        "Production influence: NO",
        SEPARATOR,
        "Scanned at: {0}".format(
            escape(scan.completed_at.isoformat())
        ),
        "Timeframe: {0}".format(
            escape(scan.timeframe)
        ),
        "Successful: {0}".format(
            len(scan.successful_assets)
        ),
        "Failed: {0}".format(
            len(scan.failed_assets)
        ),
    ]

    for item in scan.items:
        assessment = item.assessment
        candidate = item.build_result.candidate

        lines.extend(
            [
                "",
                SEPARATOR,
                "<b>{0}. {1}</b>".format(
                    assessment.rank,
                    escape(item.symbol),
                ),
                "Opportunity: {0}".format(
                    _score(
                        assessment.opportunity_score
                    )
                ),
                "Priority: {0}".format(
                    _score(
                        assessment.priority_score
                    )
                ),
                "Maturity: {0}".format(
                    _score(
                        assessment.maturity_score
                    )
                ),
                "Quality: {0}".format(
                    _score(
                        assessment.quality
                    )
                ),
                "Funding: {0}".format(
                    _availability(
                        item,
                        "funding_divergence",
                    )
                ),
                "OI change: {0}".format(
                    _availability(
                        item,
                        "open_interest_change",
                    )
                ),
            ]
        )

        warnings = _warnings(item)

        if warnings:
            lines.append(
                "Warnings: {0}".format(
                    escape(" | ".join(warnings))
                )
            )

    if scan.errors:
        lines.extend(
            [
                "",
                SEPARATOR,
                "<b>Failures</b>",
            ]
        )

        for asset in sorted(scan.errors):
            lines.append(
                "{0}: {1}".format(
                    escape(asset),
                    escape(scan.errors[asset]),
                )
            )

    lines.extend(
        [
            "",
            SEPARATOR,
            "<i>Test output only. No trade action.</i>",
        ]
    )

    return "\n".join(lines)


__all__ = [
    "format_early_bird_shadow_preview",
]
