"""Plain-text terminal formatting for Early Bird scan results."""

from typing import Iterable

from app.intelligence.early_bird.availability import FactorAvailability
from app.intelligence.early_bird.scanner.scanner import EarlyBirdScanResult


def _names(values: Iterable[str]) -> str:
    normalized = tuple(values)
    return ", ".join(normalized) if normalized else "none"


def _visible_assessment_warnings(item):
    warnings = tuple(item.assessment.warnings)
    whale_value = item.build_result.factor_values["whale_activity"]
    if whale_value.availability is not FactorAvailability.AVAILABLE:
        warnings = tuple(
            warning
            for warning in warnings
            if warning
            != "No whale activity is present in this whale-first assessment."
        )
    return warnings


def format_scan_result(result: EarlyBirdScanResult) -> str:
    """Format a scan without Telegram markup or trading instructions."""

    if not isinstance(result, EarlyBirdScanResult):
        raise TypeError("result must be an EarlyBirdScanResult")

    lines = [
        "Early Bird Scanner — experimental read-only output",
        "Scanned at: {0}".format(result.completed_at.isoformat()),
        "Timeframe: {0}".format(result.timeframe),
        "Successful: {0} | Failed: {1}".format(
            len(result.successful_assets),
            len(result.failed_assets),
        ),
    ]

    if not result.items:
        lines.extend(("", "No successful candidates."))

    for item in result.items:
        assessment = item.assessment
        build_result = item.build_result
        lines.extend(
            (
                "",
                "{0}. {1}".format(assessment.rank, item.symbol),
                "   Opportunity: {0:.2f}".format(assessment.opportunity_score),
                "   Priority: {0:.2f}".format(assessment.priority_score),
                "   Maturity: {0:.2f}".format(assessment.maturity_score),
                "   Quality: {0:.2f}".format(assessment.quality),
                "   Available factors: {0}".format(
                    _names(build_result.available_factors)
                ),
                "   Missing factors: {0}".format(
                    _names(build_result.missing_factors)
                ),
                "   Stale factors: {0}".format(
                    _names(build_result.stale_factors)
                ),
                "   Unsupported factors: {0}".format(
                    _names(build_result.unsupported_factors)
                ),
                "   Error factors: {0}".format(
                    _names(build_result.error_factors)
                ),
                "   Reasons: {0}".format(
                    " | ".join(assessment.reasons[:3]) or "none"
                ),
                "   Warnings: {0}".format(
                    " | ".join(
                        tuple(build_result.warnings)
                        + _visible_assessment_warnings(item)
                    )
                    or "none"
                ),
            )
        )

    if result.failed_assets:
        lines.extend(("", "Failed assets:"))
        lines.extend(
            "- {0}: {1}".format(asset, result.errors[asset])
            for asset in result.failed_assets
        )
    return "\n".join(lines)
