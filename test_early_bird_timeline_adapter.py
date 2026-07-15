"""Offline tests for mapping real Early Bird artifacts into Timeline v1."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
import unittest

from app.domain.candle import Candle
from app.intelligence.early_bird import (
    EarlyBirdCandidateBuilder,
    EarlyBirdEngine,
    EarlyBirdExplainer,
    EarlyBirdFactorValue,
    EmergingSituationEngine,
    EmergingStage,
    FactorAvailability,
)
from app.intelligence.early_bird.scanner import (
    EarlyBirdScanner,
    EarlyBirdScanItem,
)
from app.intelligence.timeline import (
    EarlyBirdTimelineAdapter,
    EarlyBirdTimelineResult,
    build_timelines_from_scan,
    deterministic_run_local_ids,
    format_early_bird_timeline,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 15, 0, tzinfo=UTC)
INTERVAL = timedelta(minutes=15)


def candles(asset, count=100):
    base = 100.0 + len(asset)
    result = []
    for index in range(count):
        price = base + index * (0.01 if asset != "BTC" else 0.005)
        volume = 100.0 if index < count - 1 else 400.0
        result.append(
            Candle(
                timestamp=NOW - INTERVAL * (count - index),
                open=price,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=volume,
            )
        )
    return result


class FakeCandleSource:
    def source_name(self):
        return "fake-public-candles"

    def get_candles(self, asset, interval, start_time, end_time=None, limit=1000):
        del interval, start_time, end_time, limit
        return candles(asset.upper().replace("USDT", ""))


def scan(assets=("BTC", "ETH")):
    return EarlyBirdScanner(candle_source=FakeCandleSource()).scan(
        assets,
        timeframe="15m",
        candle_count=100,
        limit=10,
        timestamp=NOW,
    )


def artifacts(item):
    explanation = EarlyBirdExplainer().explain(
        item.assessment,
        item.build_result,
    )
    emerging = EmergingSituationEngine().evaluate(
        item.assessment,
        item.build_result,
        explanation,
    )
    return explanation, emerging


def make_status_item():
    values = (
        EarlyBirdFactorValue(
            "whale_activity",
            FactorAvailability.MISSING,
            reason="No webhook input.",
        ),
        EarlyBirdFactorValue(
            "open_interest_change",
            FactorAvailability.UNSUPPORTED,
            reason="No OI delta source.",
        ),
        EarlyBirdFactorValue(
            "funding_divergence",
            FactorAvailability.STALE,
            observed_at=NOW - timedelta(hours=3),
            source="historical-funding",
            quality=40,
            reason="Outside freshness window.",
        ),
        EarlyBirdFactorValue(
            "volume_expansion",
            FactorAvailability.AVAILABLE,
            score=0,
            observed_at=NOW,
            source="fake-public-candles",
            quality=80,
        ),
        EarlyBirdFactorValue(
            "relative_strength",
            FactorAvailability.AVAILABLE,
            score=55,
            observed_at=NOW,
            source="fake-public-candles",
            quality=80,
        ),
        EarlyBirdFactorValue(
            "liquidity_event",
            FactorAvailability.ERROR,
            reason="Measurement failed.",
        ),
        EarlyBirdFactorValue(
            "structure_event",
            FactorAvailability.AVAILABLE,
            score=35,
            observed_at=NOW,
            source="fake-public-candles",
            quality=80,
        ),
        EarlyBirdFactorValue(
            "momentum_shift",
            FactorAvailability.AVAILABLE,
            score=45,
            observed_at=NOW,
            source="fake-public-candles",
            quality=80,
        ),
    )
    build_result = EarlyBirdCandidateBuilder().build(
        values,
        candidate_id="candidate-link",
        asset="LINK",
        observed_at=NOW,
        source="fake-public-candles",
        fast_event_ids=("fast-1",),
        observation_ids=("observation-1",),
        metadata={"timeframe": "15m"},
    )
    assessment = EarlyBirdEngine().rank_candidates(
        (build_result.candidate,),
        timestamp=NOW,
    )[0]
    return EarlyBirdScanItem(
        assessment=assessment,
        build_result=build_result,
        symbol="LINK",
        timeframe="15m",
        scanned_at=NOW,
    )


def create_result(item=None, stage=None):
    scan_item = item or make_status_item()
    explanation, emerging = artifacts(scan_item)
    if stage is not None:
        emerging = replace(emerging, stage=stage)
    return EarlyBirdTimelineAdapter().create_timeline(
        scan_item=scan_item,
        explanation=explanation,
        emerging_situation=emerging,
        timeline_id="timeline-link",
        entry_id="entry-link-1",
    )


class AdapterCreationTests(unittest.TestCase):
    def test_valid_timeline_has_exactly_one_entry_and_version_one(self):
        result = create_result()
        self.assertEqual(1, result.timeline.version)
        self.assertEqual(1, len(result.timeline.entries))
        self.assertEqual("LINK", result.timeline.asset)

    def test_stage_is_copied_exactly_without_inference(self):
        result = create_result(stage=EmergingStage.EXHAUSTED)
        self.assertIs(result.timeline.current_stage, EmergingStage.EXHAUSTED)
        self.assertIs(result.timeline.entries[0].stage, EmergingStage.EXHAUSTED)

    def test_available_measured_zero_and_non_available_mapping(self):
        dna = create_result().timeline.entries[0].dna
        self.assertEqual(0.0, dna.volume_expansion)
        self.assertIsNone(dna.whale_activity)
        self.assertIsNone(dna.funding_divergence)
        self.assertIsNone(dna.open_interest_change)
        self.assertIsNone(dna.liquidity_event)
        self.assertEqual("MISSING", dna.factor_availability["whale_activity"])
        self.assertEqual("STALE", dna.factor_availability["funding_divergence"])
        self.assertEqual("UNSUPPORTED", dna.factor_availability["open_interest_change"])
        self.assertEqual("ERROR", dna.factor_availability["liquidity_event"])
        self.assertEqual("AVAILABLE", dna.factor_availability["volume_expansion"])

    def test_assessment_emergence_and_candidate_scores_are_copied(self):
        item = make_status_item()
        explanation, emerging = artifacts(item)
        result = EarlyBirdTimelineAdapter().create_timeline(
            scan_item=item,
            explanation=explanation,
            emerging_situation=emerging,
            timeline_id="timeline-link",
            entry_id="entry-link",
        )
        dna = result.timeline.entries[0].dna
        candidate = item.build_result.candidate
        assessment = item.assessment
        self.assertEqual(assessment.opportunity_score, dna.opportunity)
        self.assertEqual(assessment.priority_score, dna.priority)
        self.assertEqual(assessment.maturity_score, dna.maturity)
        self.assertEqual(emerging.emergence_score, dna.emergence)
        self.assertEqual(emerging.horizon_score, dna.horizon)
        self.assertEqual(emerging.detection_confidence, dna.detection_confidence)
        self.assertEqual(candidate.data_completeness_score, dna.completeness)
        self.assertEqual(candidate.quality, dna.quality)
        self.assertEqual(candidate.freshness_score, dna.freshness)

    def test_entry_copies_factors_and_keeps_expectations_empty(self):
        result = create_result()
        entry = result.timeline.entries[0]
        self.assertEqual(
            result.emerging_situation.supporting_factors,
            entry.supporting_factors,
        )
        self.assertEqual(
            result.emerging_situation.limiting_factors,
            entry.limiting_factors,
        )
        self.assertEqual((), entry.expected_events)
        self.assertEqual((), entry.missing_expected_events)
        self.assertEqual((), entry.unexpected_events)
        self.assertNotIn("whale_activity", entry.missing_expected_events)

    def test_observed_events_are_descriptive_source_references(self):
        entry = create_result().timeline.entries[0]
        self.assertIn("fast_event:fast-1", entry.observed_events)
        self.assertIn("observation:observation-1", entry.observed_events)
        self.assertIn("measured_factor:volume_expansion", entry.observed_events)
        self.assertNotIn("measured_factor:whale_activity", entry.observed_events)

    def test_source_ids_and_metadata_are_preserved(self):
        item = make_status_item()
        result = create_result(item)
        entry = result.timeline.entries[0]
        self.assertEqual(item.assessment.assessment_id, entry.source_assessment_id)
        self.assertEqual(item.assessment.candidate_id, entry.source_candidate_id)
        self.assertIsNone(entry.source_situation_id)
        self.assertEqual("15m", entry.dna.metadata["timeframe"])
        self.assertEqual(("fast-1",), entry.dna.metadata["source_event_ids"])
        self.assertEqual(
            ("observation-1",),
            entry.dna.metadata["source_observation_ids"],
        )

    def test_transition_reason_is_deterministic_and_descriptive(self):
        first = create_result(stage=EmergingStage.SEED)
        second = create_result(stage=EmergingStage.SEED)
        expected = "Initial Early Bird assessment classified the situation as SEED."
        self.assertEqual(expected, first.timeline.entries[0].transition_reason)
        self.assertEqual(expected, second.timeline.entries[0].transition_reason)

    def test_explicit_timestamp_is_normalized_to_utc(self):
        item = make_status_item()
        explanation, emerging = artifacts(item)
        plus_two = timezone(timedelta(hours=2))
        timestamp = datetime(2026, 7, 15, 17, 0, tzinfo=plus_two)
        result = EarlyBirdTimelineAdapter().create_timeline(
            scan_item=item,
            explanation=explanation,
            emerging_situation=emerging,
            timeline_id="timeline-link",
            entry_id="entry-link",
            timestamp=timestamp,
        )
        self.assertEqual(NOW, result.created_at)


class IdentityAndImmutabilityTests(unittest.TestCase):
    def test_asset_mismatch_is_rejected(self):
        item = make_status_item()
        explanation, emerging = artifacts(item)
        mismatched = SimpleNamespace(
            assessment=item.assessment,
            build_result=item.build_result,
            symbol="ETH",
            timeframe=item.timeframe,
            scanned_at=item.scanned_at,
        )
        with self.assertRaises(ValueError):
            EarlyBirdTimelineAdapter().create_timeline(
                scan_item=mismatched,
                explanation=explanation,
                emerging_situation=emerging,
                timeline_id="timeline",
                entry_id="entry",
            )

    def test_assessment_and_candidate_identity_mismatches_are_rejected(self):
        item = make_status_item()
        explanation, emerging = artifacts(item)
        with self.assertRaises(ValueError):
            EarlyBirdTimelineAdapter().create_timeline(
                scan_item=item,
                explanation=explanation,
                emerging_situation=replace(
                    emerging,
                    source_assessment_id="different",
                ),
                timeline_id="timeline",
                entry_id="entry",
            )
        with self.assertRaises(ValueError):
            EarlyBirdTimelineAdapter().create_timeline(
                scan_item=item,
                explanation=explanation,
                emerging_situation=replace(
                    emerging,
                    source_candidate_id="different",
                ),
                timeline_id="timeline",
                entry_id="entry",
            )

    def test_explanation_identity_mismatch_is_rejected(self):
        item = make_status_item()
        explanation, emerging = artifacts(item)
        metadata = dict(explanation.metadata)
        metadata["assessment_id"] = "different"
        with self.assertRaises(ValueError):
            EarlyBirdTimelineAdapter().create_timeline(
                scan_item=item,
                explanation=replace(explanation, metadata=metadata),
                emerging_situation=emerging,
                timeline_id="timeline",
                entry_id="entry",
            )

    def test_result_is_immutable_and_metadata_is_frozen(self):
        result = create_result()
        self.assertIsInstance(result.metadata, MappingProxyType)
        with self.assertRaises(FrozenInstanceError):
            result.created_at = NOW + timedelta(1)
        with self.assertRaises(TypeError):
            result.metadata["x"] = 1

    def test_result_serialization_round_trip(self):
        result = create_result()
        restored = EarlyBirdTimelineResult.from_dict(result.to_dict())
        self.assertEqual(restored, result)
        self.assertIs(restored.timeline.current_stage, result.timeline.current_stage)

    def test_result_rejects_inconsistent_timestamp(self):
        result = create_result()
        with self.assertRaises(ValueError):
            replace(result, created_at=result.created_at + timedelta(seconds=1))

    def test_inputs_are_not_mutated(self):
        item = make_status_item()
        explanation, emerging = artifacts(item)
        before = (
            item.assessment.to_dict(),
            item.build_result.to_dict(),
            explanation.to_dict(),
            emerging.to_dict(),
        )
        EarlyBirdTimelineAdapter().create_timeline(
            scan_item=item,
            explanation=explanation,
            emerging_situation=emerging,
            timeline_id="timeline",
            entry_id="entry",
        )
        after = (
            item.assessment.to_dict(),
            item.build_result.to_dict(),
            explanation.to_dict(),
            emerging.to_dict(),
        )
        self.assertEqual(before, after)

    def test_result_has_no_trade_or_direction_fields(self):
        names = {item.name for item in fields(EarlyBirdTimelineResult)}
        self.assertFalse(names & {"trade", "buy", "sell", "direction", "execution"})


class BatchAndFormatterTests(unittest.TestCase):
    def test_run_local_ids_are_deterministic(self):
        item = make_status_item()
        first = deterministic_run_local_ids(item)
        second = deterministic_run_local_ids(item)
        self.assertEqual(first, second)
        self.assertIn("link", first[0])
        self.assertTrue(first[1].endswith(":initial"))

    def test_batch_builds_every_ranked_success(self):
        scan_result = scan(("BTC", "ETH"))
        batch = build_timelines_from_scan(scan_result)
        self.assertEqual(2, len(batch.results))
        self.assertEqual(tuple(item.symbol for item in scan_result.items), batch.top_assets)
        self.assertEqual({}, dict(batch.errors))
        self.assertEqual(2, sum(batch.stage_distribution.values()))

    def test_one_construction_failure_does_not_abort_batch(self):
        class FailingAdapter(EarlyBirdTimelineAdapter):
            def create_timeline(self, **kwargs):
                if kwargs["scan_item"].symbol == "BTC":
                    raise RuntimeError("fixture construction failure")
                return super().create_timeline(**kwargs)

        batch = build_timelines_from_scan(
            scan(("BTC", "ETH")),
            adapter=FailingAdapter(),
        )
        self.assertEqual(("ETH",), batch.top_assets)
        self.assertIn("BTC", batch.errors)

    def test_formatter_contains_timeline_scores_and_availability(self):
        output = format_early_bird_timeline(create_result())
        self.assertIn("Asset: LINK", output)
        self.assertIn("Version: 1", output)
        self.assertIn("Opportunity:", output)
        self.assertIn("Whale Activity: MISSING", output)
        self.assertIn("Open Interest Change: UNSUPPORTED", output)
        self.assertIn("Initial Early Bird assessment", output)

    def test_formatter_contains_no_trade_language(self):
        output = format_early_bird_timeline(create_result()).lower()
        for token in (" buy", " sell", "take profit", "stop loss"):
            self.assertNotIn(token, output)

    def test_demo_is_import_safe(self):
        module = importlib.import_module("run_early_bird_timeline_demo")
        self.assertTrue(callable(module.main))
        self.assertTrue(callable(module.build_parser))


class DependencyBoundaryTests(unittest.TestCase):
    def test_adapter_has_no_forbidden_imports(self):
        path = Path("app/intelligence/timeline/early_bird_adapter.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        forbidden = (
            "telegram",
            "database",
            "repository",
            "pipeline",
            "decision",
            "market_state",
            "experts",
            "scanner",
            "provider",
            "exchange",
            "requests",
            "httpx",
            "socket",
        )
        self.assertFalse(
            any(part in name.lower() for name in imports for part in forbidden),
            imports,
        )

    def test_demo_has_no_import_time_execution_or_write_calls(self):
        path = Path("run_early_bird_timeline_demo.py")
        source = path.read_text(encoding="utf-8")
        self.assertIn('if __name__ == "__main__":', source)
        self.assertNotIn("open(", source)
        self.assertNotIn("telegram", source.lower())
        self.assertNotIn("database", source.lower())


if __name__ == "__main__":
    unittest.main()
