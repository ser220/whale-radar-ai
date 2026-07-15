"""Focused offline tests for PS-3 Step 3 Early Bird explainability."""

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path
import re
import unittest

from app.intelligence.early_bird import (
    EarlyBirdCandidateBuilder,
    EarlyBirdEngine,
    EarlyBirdExplainer,
    EarlyBirdExplanation,
    EarlyBirdFactorValue,
    FactorAvailability,
    format_explanation,
    format_explanations,
)
from app.intelligence.early_bird.builder import CANONICAL_FACTOR_NAMES


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 20, 0, tzinfo=UTC)

DEFAULT_SCORES = {
    "volume_expansion": 70.0,
    "relative_strength": 50.0,
    "structure_event": 20.0,
    "momentum_shift": 10.0,
}

DEFAULT_STATUSES = {
    "whale_activity": FactorAvailability.MISSING,
    "open_interest_change": FactorAvailability.UNSUPPORTED,
    "funding_divergence": FactorAvailability.MISSING,
    "liquidity_event": FactorAvailability.UNSUPPORTED,
}


def make_build_result(asset="BTC", scores=None, statuses=None):
    measured_scores = dict(DEFAULT_SCORES)
    measured_scores.update(scores or {})
    availability = dict(DEFAULT_STATUSES)
    availability.update(statuses or {})
    values = []
    for factor_name in CANONICAL_FACTOR_NAMES:
        status = availability.get(factor_name, FactorAvailability.AVAILABLE)
        if status is FactorAvailability.AVAILABLE:
            values.append(
                EarlyBirdFactorValue(
                    factor_name,
                    status,
                    score=measured_scores.get(factor_name, 0.0),
                    observed_at=NOW,
                    source="offline-test",
                    quality=90.0,
                )
            )
        else:
            values.append(
                EarlyBirdFactorValue(
                    factor_name,
                    status,
                    reason="Offline availability fixture.",
                )
            )
    return EarlyBirdCandidateBuilder().build(
        values,
        candidate_id="explain:{0}".format(asset.lower()),
        asset=asset,
        observed_at=NOW,
        source="offline-explainability-test",
    )


def make_pair(asset="BTC", rank=1, scores=None, statuses=None):
    build_result = make_build_result(asset, scores=scores, statuses=statuses)
    assessment = EarlyBirdEngine().evaluate_candidate(
        build_result.candidate,
        timestamp=NOW,
    )
    return replace(assessment, rank=rank), build_result


def explanation(asset="BTC", rank=1, scores=None, statuses=None):
    assessment, build_result = make_pair(
        asset,
        rank=rank,
        scores=scores,
        statuses=statuses,
    )
    return EarlyBirdExplainer().explain(assessment, build_result)


class ExplanationModelTests(unittest.TestCase):
    def test_model_is_immutable(self):
        result = explanation()
        with self.assertRaises(FrozenInstanceError):
            result.priority_score = 0
        with self.assertRaises(TypeError):
            result.factor_breakdown["volume_expansion"]["raw_score"] = 0

    def test_serialization_round_trip(self):
        original = explanation()
        restored = EarlyBirdExplanation.from_dict(original.to_dict())
        self.assertEqual(original, restored)

    def test_model_contains_required_scores_and_groups(self):
        result = explanation()
        self.assertEqual("BTC", result.asset)
        self.assertGreater(result.priority_score, 0)
        self.assertEqual(
            ("whale_activity", "funding_divergence"),
            result.missing_factors,
        )
        self.assertEqual(
            ("open_interest_change", "liquidity_event"),
            result.unsupported_factors,
        )


class ContributionTests(unittest.TestCase):
    def test_breakdown_has_raw_weight_weighted_and_percent(self):
        item = explanation().factor_breakdown["volume_expansion"]
        self.assertEqual(70.0, item["raw_score"])
        self.assertEqual(0.15, item["weight"])
        self.assertEqual(10.5, item["weighted_contribution"])
        self.assertGreater(item["contribution_percent"], 0)

    def test_positive_contribution_percentages_sum_to_100(self):
        result = explanation()
        total = sum(
            item["contribution_percent"]
            for item in result.factor_breakdown.values()
        )
        self.assertAlmostEqual(100.0, total, places=5)
        self.assertEqual(100.0, result.metadata["contribution_percent_total"])

    def test_missing_factors_are_excluded_from_breakdown(self):
        result = explanation()
        self.assertNotIn("whale_activity", result.factor_breakdown)
        self.assertNotIn("funding_divergence", result.factor_breakdown)

    def test_unsupported_and_error_factors_are_excluded(self):
        result = explanation(
            statuses={
                "funding_divergence": FactorAvailability.ERROR,
            }
        )
        self.assertNotIn("funding_divergence", result.factor_breakdown)
        self.assertNotIn("open_interest_change", result.factor_breakdown)
        self.assertEqual(("funding_divergence",), result.error_factors)

    def test_top_factors_have_deterministic_contribution_order(self):
        result = explanation()
        self.assertEqual(
            (
                "volume_expansion",
                "relative_strength",
                "structure_event",
                "momentum_shift",
            ),
            result.top_positive_factors,
        )

    def test_zero_contributions_are_explicit_not_invented(self):
        result = explanation(scores={name: 0.0 for name in DEFAULT_SCORES})
        self.assertEqual((), result.top_positive_factors)
        self.assertEqual(
            0.0,
            sum(
                item["contribution_percent"]
                for item in result.factor_breakdown.values()
            ),
        )
        self.assertTrue(result.metadata["zero_contribution_basis"])


class ExplanationLogicTests(unittest.TestCase):
    def test_explanations_are_deterministic(self):
        first = explanation()
        second = explanation()
        self.assertEqual(first, second)

    def test_highest_contributor_is_explained(self):
        result = explanation()
        self.assertIn(
            "Highest measured contributor is Volume Expansion",
            result.why_ranked_here[0],
        )

    def test_missing_and_immature_evidence_explain_limitations(self):
        result = explanation()
        text = " ".join(result.why_not_higher)
        self.assertIn("Whale Activity is missing", text)
        self.assertIn("Funding Divergence is missing", text)
        self.assertIn("structure evidence is still immature", text)
        self.assertIn("momentum contribution remains weak", text)

    def test_explainer_does_not_change_scores_or_contributions(self):
        assessment, build_result = make_pair()
        assessment_before = assessment.to_dict()
        candidate_before = build_result.candidate.to_dict()
        result = EarlyBirdExplainer().explain(assessment, build_result)
        self.assertEqual(assessment_before, assessment.to_dict())
        self.assertEqual(candidate_before, build_result.candidate.to_dict())
        self.assertEqual(assessment.opportunity_score, result.opportunity_score)
        self.assertEqual(assessment.priority_score, result.priority_score)
        self.assertEqual(assessment.maturity_score, result.maturity_score)

    def test_adjacent_comparison_reports_only_measured_deficits(self):
        previous_assessment, previous_build = make_pair(
            "LINK",
            rank=1,
            scores={"volume_expansion": 90.0, "relative_strength": 60.0},
        )
        current_assessment, current_build = make_pair(
            "BTC",
            rank=2,
            scores={"volume_expansion": 50.0, "relative_strength": 40.0},
        )
        result = EarlyBirdExplainer().explain(
            current_assessment,
            current_build,
            previous_assessment=previous_assessment,
            previous_build_result=previous_build,
        )
        comparison = tuple(
            item for item in result.why_not_higher if "Compared with LINK" in item
        )
        self.assertTrue(comparison)
        self.assertIn("Volume Expansion", comparison[0])
        self.assertFalse(any("Funding Divergence" in item for item in comparison))

    def test_non_adjacent_comparison_is_rejected(self):
        previous_assessment, previous_build = make_pair("LINK", rank=1)
        current_assessment, current_build = make_pair("BTC", rank=3)
        with self.assertRaises(ValueError):
            EarlyBirdExplainer().explain(
                current_assessment,
                current_build,
                previous_assessment=previous_assessment,
                previous_build_result=previous_build,
            )

    def test_ranked_helper_compares_each_asset_with_immediate_predecessor(self):
        first = make_pair("LINK", rank=1, scores={"volume_expansion": 90.0})
        second = make_pair("BTC", rank=2, scores={"volume_expansion": 60.0})
        third = make_pair("ETH", rank=3, scores={"volume_expansion": 30.0})
        results = EarlyBirdExplainer().explain_ranked((third, first, second))
        self.assertEqual(("LINK", "BTC", "ETH"), tuple(item.asset for item in results))
        self.assertIsNone(results[0].metadata["previous_asset"])
        self.assertEqual("LINK", results[1].metadata["previous_asset"])
        self.assertEqual("BTC", results[2].metadata["previous_asset"])

    def test_false_absence_whale_warning_is_removed(self):
        result = explanation()
        self.assertFalse(
            any("No whale activity is present" in warning for warning in result.warnings)
        )
        self.assertTrue(any("whale_activity' is missing" in warning for warning in result.warnings))


class FormatterAndBoundaryTests(unittest.TestCase):
    def test_plain_formatter_contains_scores_contributions_and_limitations(self):
        output = format_explanation(explanation("LINK"))
        self.assertIn("LINK", output)
        self.assertIn("Opportunity:", output)
        self.assertIn("Priority:", output)
        self.assertIn("Maturity:", output)
        self.assertIn("Contribution:", output)
        self.assertIn("Volume Expansion:", output)
        self.assertIn("Missing:", output)
        self.assertIn("Why ranked here:", output)
        self.assertIn("Why not higher:", output)

    def test_multiple_formatter_preserves_supplied_order(self):
        output = format_explanations((explanation("LINK"), explanation("BTC")))
        self.assertLess(output.index("LINK"), output.index("BTC"))

    def test_output_contains_no_trade_language(self):
        output = format_explanation(explanation()).lower()
        forbidden = ("buy", "sell", "long", "short", "entry", "tp", "sl")
        for word in forbidden:
            with self.subTest(word=word):
                self.assertIsNone(re.search(r"\b{0}\b".format(word), output))

    def test_runtime_dependency_boundary(self):
        tree = ast.parse(
            Path("app/intelligence/early_bird/explain.py").read_text(
                encoding="utf-8"
            )
        )
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        application_imports = tuple(
            name for name in imports if name.startswith("app.")
        )
        self.assertEqual(
            (
                "app.intelligence.early_bird.builder",
                "app.intelligence.early_bird.models",
            ),
            application_imports,
        )
        forbidden = (
            "telegram",
            "database",
            "repository",
            "provider",
            "network",
            "decision",
            "market_state",
            "expert",
        )
        self.assertFalse(
            any(token in name.lower() for token in forbidden for name in imports)
        )


if __name__ == "__main__":
    unittest.main()
