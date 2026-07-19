from datetime import datetime, timezone

from app.intelligence.candidate_resolution.enums import (
    CandidateResolutionReason,
)

from app.intelligence.candidate_resolution.models import (
    CandidateResolutionRecord,
)

from app.intelligence.candidate_resolution.policy import (
    CandidateResolutionPolicy,
)


class CandidateResolver:

    def resolve(
        self,
        *,
        candidate_a_id: str,
        candidate_b_id: str,
        identity_match: bool,
        time_window_match: bool,
    ) -> CandidateResolutionRecord:

        resolution_type = (
            CandidateResolutionPolicy.resolve_type(
                same_identity=identity_match,
                same_time_window=time_window_match,
            )
        )

        if resolution_type.value == "exact_match":
            reason = (
                CandidateResolutionReason.SAME_IDENTITY
            )

        elif resolution_type.value == "merge_allowed":
            reason = (
                CandidateResolutionReason.SAME_IDENTITY
            )

        else:
            reason = (
                CandidateResolutionReason.INSUFFICIENT_MATCH
            )

        canonical_id = min(
            candidate_a_id,
            candidate_b_id,
        )

        merged_ids = ()

        if resolution_type.value != "keep_separate":
            merged_ids = (
                candidate_a_id,
                candidate_b_id,
            )

        return CandidateResolutionRecord(
            canonical_candidate_id=canonical_id,
            merged_candidate_ids=merged_ids,
            resolution_type=resolution_type,
            reason=reason,
            resolved_at=datetime.now(
                timezone.utc
            ),
        )
