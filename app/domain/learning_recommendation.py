from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


ALLOWED_STATUSES = {
    "pending",
    "approved",
    "rejected",
    "applied",
    "expired",
}


@dataclass
class LearningRecommendation:
    module: str
    current_weight: float
    suggested_change: float
    reason: str

    confidence: float = 0.0
    sample_count: int = 1
    average_module_score: Optional[float] = None

    prediction_id: Optional[int] = None
    recommendation_id: Optional[int] = None

    status: str = "pending"
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    applied_at: Optional[str] = None

    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.module = str(self.module or "").strip()
        self.reason = str(self.reason or "").strip()
        self.status = str(self.status or "pending").lower().strip()

        if not self.module:
            raise ValueError("module cannot be empty.")

        if not self.reason:
            raise ValueError("reason cannot be empty.")

        if self.status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Unsupported recommendation status: {self.status}"
            )

        self.current_weight = float(self.current_weight)
        self.suggested_change = float(self.suggested_change)
        self.confidence = float(self.confidence or 0.0)
        self.sample_count = int(self.sample_count or 0)

        if self.current_weight <= 0:
            raise ValueError(
                "current_weight must be greater than zero."
            )

        if self.sample_count < 0:
            raise ValueError(
                "sample_count cannot be negative."
            )

        self.confidence = max(
            0.0,
            min(100.0, self.confidence),
        )

        if self.average_module_score is not None:
            self.average_module_score = max(
                0.0,
                min(
                    100.0,
                    float(self.average_module_score),
                ),
            )

        if not isinstance(self.evidence, dict):
            self.evidence = {}

        if self.created_at is None:
            self.created_at = datetime.now(
                timezone.utc
            ).isoformat()

    @property
    def suggested_weight(self) -> float:
        value = self.current_weight + self.suggested_change

        return round(
            max(0.10, min(2.00, value)),
            4,
        )

    @property
    def change_percent(self) -> float:
        if self.current_weight == 0:
            return 0.0

        return round(
            self.suggested_change
            / self.current_weight
            * 100,
            2,
        )

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_approved(self) -> bool:
        return self.status == "approved"

    @property
    def is_applied(self) -> bool:
        return self.status == "applied"

    @property
    def direction(self) -> str:
        if self.suggested_change > 0:
            return "increase"

        if self.suggested_change < 0:
            return "decrease"

        return "hold"

    def approve(self) -> None:
        self.status = "approved"
        self.reviewed_at = datetime.now(
            timezone.utc
        ).isoformat()

    def reject(self) -> None:
        self.status = "rejected"
        self.reviewed_at = datetime.now(
            timezone.utc
        ).isoformat()

    def mark_applied(self) -> None:
        self.status = "applied"

        now = datetime.now(
            timezone.utc
        ).isoformat()

        if self.reviewed_at is None:
            self.reviewed_at = now

        self.applied_at = now

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)

        data.update({
            "suggested_weight": self.suggested_weight,
            "change_percent": self.change_percent,
            "direction": self.direction,
        })

        return data
