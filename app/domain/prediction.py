from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Prediction:
    id: Optional[int]
    asset: str
    direction: str
    entry_price: float
    target_price: float
    expected_move: float = 0.0
    eta: str = ""
    created_at: Optional[str] = None
    current_price: Optional[float] = None
    actual_move: Optional[float] = None
    target_hit: bool = False
    outcome_checked: bool = False
    accuracy: Optional[float] = None
    checked_at: Optional[str] = None
    ai_snapshot: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.asset = str(self.asset or "").upper().strip()
        self.direction = str(self.direction or "").lower().strip()

        if self.direction not in {"bullish", "bearish"}:
            raise ValueError(
                "Prediction direction must be 'bullish' or 'bearish'."
            )

        self.entry_price = float(self.entry_price)
        self.target_price = float(self.target_price)
        self.expected_move = float(self.expected_move or 0.0)

        if self.entry_price <= 0:
            raise ValueError("Prediction entry_price must be greater than zero.")

        if self.target_price <= 0:
            raise ValueError("Prediction target_price must be greater than zero.")

        if self.current_price is not None:
            self.current_price = float(self.current_price)

        if self.actual_move is not None:
            self.actual_move = float(self.actual_move)

        if self.accuracy is not None:
            self.accuracy = float(self.accuracy)

        self.target_hit = bool(self.target_hit)
        self.outcome_checked = bool(self.outcome_checked)

        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

        if not isinstance(self.ai_snapshot, dict):
            self.ai_snapshot = {}

    @property
    def is_open(self) -> bool:
        return not self.outcome_checked

    @property
    def is_closed(self) -> bool:
        return self.outcome_checked

    @property
    def bias(self) -> str:
        return self.direction

    def calculate_current_move(self) -> Optional[float]:
        if self.current_price is None:
            return None

        move = (
            (self.current_price - self.entry_price)
            / self.entry_price
            * 100
        )

        return round(move, 4)

    def direction_is_correct(self) -> Optional[bool]:
        if self.current_price is None:
            return None

        if self.direction == "bullish":
            return self.current_price > self.entry_price

        return self.current_price < self.entry_price

    def target_is_reached(self) -> Optional[bool]:
        if self.current_price is None:
            return None

        if self.direction == "bullish":
            return self.current_price >= self.target_price

        return self.current_price <= self.target_price

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
