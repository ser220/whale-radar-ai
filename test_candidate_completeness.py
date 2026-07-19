import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from app.intelligence.candidate_completeness import (
    CandidateCompletenessEvaluator,
    CandidateCompletenessPolicy,
    CandidateCompletenessRecord,
    CandidateCompletenessStatus,
    ProviderCompletenessRecord,
    ProviderCompletenessStatus,
)


class TestProviderCompletenessRecord(unittest.TestCase):
    def test_record_normalizes_provider_name_and_time(self) -> None:
        local_time = datetime(
            2026,
            7,
            19,
            9,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        )

        record = ProviderCompletenessRecord(
            provider_name="  binance  ",
            status=ProviderCompletenessStatus.PARTIAL,
            checked_at=local_time,
            missing_fields=(" open_interest ", "", "funding_rate"),
        )

        self.assertEqual(record.provider_name, "binance")
        self.assertEqual(record.checked_at.tzinfo, timezone.utc)
        self.assertEqual(
            record.missing_fields,
            ("open_interest", "funding_rate"),
        )

    def test_record_is_immutable(self) -> None:
        record = ProviderCompletenessRecord(
            provider_name="binance",
            status=ProviderCompletenessStatus.AVAILABLE,
            checked_at=datetime.now(timezone.utc),
        )

        with self.assertRaises(FrozenInstanceError):
            record.provider_name = "okx"

    def test_record_rejects_empty_provider_name(self) -> None:
        with self.assertRaises(ValueError):
            ProviderCompletenessRecord(
                provider_name="   ",
                status=ProviderCompletenessStatus.MISSING,
                checked_at=datetime.now(timezone.utc),
            )

    def test_record_rejects_naive_datetime(self) -> None:
        with self.assertRaises(ValueError):
            ProviderCompletenessRecord(
                provider_name="binance",
                status=ProviderCompletenessStatus.AVAILABLE,
                checked_at=datetime(2026, 7, 19, 9, 0),
            )

    def test_record_rejects_mutable_missing_fields(self) -> None:
        with self.assertRaises(TypeError):
            ProviderCompletenessRecord(
                provider_name="binance",
                status=ProviderCompletenessStatus.PARTIAL,
                checked_at=datetime.now(timezone.utc),
                missing_fields=["open_interest"],
            )


class TestCandidateCompletenessRecord(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime.now(timezone.utc)
        self.provider = ProviderCompletenessRecord(
            provider_name="binance",
            status=ProviderCompletenessStatus.AVAILABLE,
            checked_at=self.now,
        )

    def test_record_preserves_required_fields(self) -> None:
        record = CandidateCompletenessRecord(
            candidate_id="candidate_001",
            provider_records=(self.provider,),
            status=CandidateCompletenessStatus.COMPLETE,
            evaluated_at=self.now,
        )

        self.assertEqual(record.candidate_id, "candidate_001")
        self.assertEqual(record.provider_records, (self.provider,))
        self.assertIs(
            record.status,
            CandidateCompletenessStatus.COMPLETE,
        )
        self.assertEqual(record.evaluated_at, self.now)

    def test_record_rejects_empty_candidate_id(self) -> None:
        with self.assertRaises(ValueError):
            CandidateCompletenessRecord(
                candidate_id="   ",
                provider_records=(self.provider,),
                status=CandidateCompletenessStatus.COMPLETE,
                evaluated_at=self.now,
            )

    def test_record_rejects_empty_provider_records(self) -> None:
        with self.assertRaises(ValueError):
            CandidateCompletenessRecord(
                candidate_id="candidate_001",
                provider_records=(),
                status=CandidateCompletenessStatus.INCOMPLETE,
                evaluated_at=self.now,
            )

    def test_record_rejects_mutable_provider_records(self) -> None:
        with self.assertRaises(TypeError):
            CandidateCompletenessRecord(
                candidate_id="candidate_001",
                provider_records=[self.provider],
                status=CandidateCompletenessStatus.COMPLETE,
                evaluated_at=self.now,
            )

    def test_record_rejects_duplicate_providers(self) -> None:
        duplicate = ProviderCompletenessRecord(
            provider_name="binance",
            status=ProviderCompletenessStatus.MISSING,
            checked_at=self.now,
        )

        with self.assertRaises(ValueError):
            CandidateCompletenessRecord(
                candidate_id="candidate_001",
                provider_records=(self.provider, duplicate),
                status=CandidateCompletenessStatus.PARTIAL,
                evaluated_at=self.now,
            )

    def test_record_rejects_naive_evaluated_at(self) -> None:
        with self.assertRaises(ValueError):
            CandidateCompletenessRecord(
                candidate_id="candidate_001",
                provider_records=(self.provider,),
                status=CandidateCompletenessStatus.COMPLETE,
                evaluated_at=datetime(2026, 7, 19, 9, 0),
            )


class TestCandidateCompletenessPolicy(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime.now(timezone.utc)

    def build_provider(
        self,
        name: str,
        status: ProviderCompletenessStatus,
    ) -> ProviderCompletenessRecord:
        return ProviderCompletenessRecord(
            provider_name=name,
            status=status,
            checked_at=self.now,
        )

    def test_all_available_is_complete(self) -> None:
        records = (
            self.build_provider(
                "binance",
                ProviderCompletenessStatus.AVAILABLE,
            ),
            self.build_provider(
                "okx",
                ProviderCompletenessStatus.AVAILABLE,
            ),
        )

        result = CandidateCompletenessPolicy.evaluate_status(records)

        self.assertIs(result, CandidateCompletenessStatus.COMPLETE)

    def test_all_missing_is_incomplete(self) -> None:
        records = (
            self.build_provider(
                "binance",
                ProviderCompletenessStatus.MISSING,
            ),
            self.build_provider(
                "okx",
                ProviderCompletenessStatus.MISSING,
            ),
        )

        result = CandidateCompletenessPolicy.evaluate_status(records)

        self.assertIs(result, CandidateCompletenessStatus.INCOMPLETE)

    def test_mixed_statuses_are_partial(self) -> None:
        records = (
            self.build_provider(
                "binance",
                ProviderCompletenessStatus.AVAILABLE,
            ),
            self.build_provider(
                "okx",
                ProviderCompletenessStatus.MISSING,
            ),
        )

        result = CandidateCompletenessPolicy.evaluate_status(records)

        self.assertIs(result, CandidateCompletenessStatus.PARTIAL)

    def test_provider_partial_makes_candidate_partial(self) -> None:
        records = (
            self.build_provider(
                "binance",
                ProviderCompletenessStatus.AVAILABLE,
            ),
            self.build_provider(
                "okx",
                ProviderCompletenessStatus.PARTIAL,
            ),
        )

        result = CandidateCompletenessPolicy.evaluate_status(records)

        self.assertIs(result, CandidateCompletenessStatus.PARTIAL)

    def test_policy_rejects_empty_records(self) -> None:
        with self.assertRaises(ValueError):
            CandidateCompletenessPolicy.evaluate_status(())


class TestCandidateCompletenessEvaluator(unittest.TestCase):
    def test_evaluator_builds_record_from_policy(self) -> None:
        now = datetime.now(timezone.utc)

        records = (
            ProviderCompletenessRecord(
                provider_name="binance",
                status=ProviderCompletenessStatus.AVAILABLE,
                checked_at=now,
            ),
            ProviderCompletenessRecord(
                provider_name="okx",
                status=ProviderCompletenessStatus.MISSING,
                checked_at=now,
                missing_fields=("open_interest",),
            ),
        )

        result = CandidateCompletenessEvaluator.evaluate(
            candidate_id="candidate_001",
            provider_records=records,
            evaluated_at=now,
        )

        self.assertEqual(result.candidate_id, "candidate_001")
        self.assertEqual(result.provider_records, records)
        self.assertIs(
            result.status,
            CandidateCompletenessStatus.PARTIAL,
        )
        self.assertEqual(result.evaluated_at, now)

    def test_evaluator_uses_current_utc_time_by_default(self) -> None:
        provider = ProviderCompletenessRecord(
            provider_name="binance",
            status=ProviderCompletenessStatus.AVAILABLE,
            checked_at=datetime.now(timezone.utc),
        )

        result = CandidateCompletenessEvaluator.evaluate(
            candidate_id="candidate_001",
            provider_records=(provider,),
        )

        self.assertEqual(result.evaluated_at.tzinfo, timezone.utc)
        self.assertIs(
            result.status,
            CandidateCompletenessStatus.COMPLETE,
        )


if __name__ == "__main__":
    unittest.main()
