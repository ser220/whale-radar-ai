from app.intelligence.candidate_resolution.enums import (
    CandidateResolutionType,
)


class CandidateResolutionPolicy:

    @staticmethod
    def resolve_type(
        *,
        same_identity: bool,
        same_time_window: bool,
    ) -> CandidateResolutionType:

        if same_identity and same_time_window:
            return (
                CandidateResolutionType.EXACT_MATCH
            )

        if same_identity:
            return (
                CandidateResolutionType.MERGE_ALLOWED
            )

        return (
            CandidateResolutionType.KEEP_SEPARATE
        )
