from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.domain.prediction import Prediction


@dataclass
class PredictionLifecycle:
    prediction_id: int
    asset: str
    direction: str

    entry_price: float
    target_price: float
    latest_price: float

    highest_price: float
    lowest_price: float

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    stop_price: Optional[float] = None

    highest_at: Optional[str] = None
    lowest_at: Optional[str] = None
    target_touched_at: Optional[str] = None
    stop_touched_at: Optional[str] = None

    def __post_init__(self) -> None:
        self.asset = str(self.asset or "").upper().strip()
        self.direction = str(self.direction or "").lower().strip()

        if self.direction not in {"bullish", "bearish"}:
            raise ValueError(
                "Lifecycle direction must be 'bullish' or 'bearish'."
            )

        self.entry_price = float(self.entry_price)
        self.target_price = float(self.target_price)
        self.latest_price = float(self.latest_price)
        self.highest_price = float(self.highest_price)
        self.lowest_price = float(self.lowest_price)

        if self.entry_price <= 0:
            raise ValueError("entry_price must be greater than zero.")

        if self.target_price <= 0:
            raise ValueError("target_price must be greater than zero.")

        if self.latest_price <= 0:
            raise ValueError("latest_price must be greater than zero.")

        if self.highest_price <= 0 or self.lowest_price <= 0:
            raise ValueError(
                "highest_price and lowest_price must be greater than zero."
            )

        if self.highest_price < self.lowest_price:
            raise ValueError(
                "highest_price cannot be lower than lowest_price."
            )

        if self.stop_price is not None:
            self.stop_price = float(self.stop_price)

            if self.stop_price <= 0:
                raise ValueError("stop_price must be greater than zero.")

        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    @classmethod
    def from_prediction(
        cls,
        prediction: Prediction,
        latest_price: Optional[float] = None,
        highest_price: Optional[float] = None,
        lowest_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> "PredictionLifecycle":
        price = (
            latest_price
            if latest_price is not None
            else prediction.current_price
        )

        if price is None:
            price = prediction.entry_price

        return cls(
            prediction_id=prediction.id or 0,
            asset=prediction.asset,
            direction=prediction.direction,
            entry_price=prediction.entry_price,
            target_price=prediction.target_price,
            latest_price=price,
            highest_price=(
                highest_price
                if highest_price is not None
                else max(prediction.entry_price, price)
            ),
            lowest_price=(
                lowest_price
                if lowest_price is not None
                else min(prediction.entry_price, price)
            ),
            created_at=prediction.created_at,
            stop_price=stop_price,
        )

    @property
    def current_move_percent(self) -> float:
        move = (
            (self.latest_price - self.entry_price)
            / self.entry_price
            * 100
        )
        return round(move, 4)

    @property
    def favorable_price(self) -> float:
        if self.direction == "bullish":
            return self.highest_price

        return self.lowest_price

    @property
    def adverse_price(self) -> float:
        if self.direction == "bullish":
            return self.lowest_price

        return self.highest_price

    @property
    def mfe_percent(self) -> float:
        if self.direction == "bullish":
            move = (
                (self.highest_price - self.entry_price)
                / self.entry_price
                * 100
            )
        else:
            move = (
                (self.entry_price - self.lowest_price)
                / self.entry_price
                * 100
            )

        return round(max(move, 0.0), 4)

    @property
    def mae_percent(self) -> float:
        if self.direction == "bullish":
            move = (
                (self.entry_price - self.lowest_price)
                / self.entry_price
                * 100
            )
        else:
            move = (
                (self.highest_price - self.entry_price)
                / self.entry_price
                * 100
            )

        return round(max(move, 0.0), 4)

    @property
    def target_touched(self) -> bool:
        if self.direction == "bullish":
            return self.highest_price >= self.target_price

        return self.lowest_price <= self.target_price

    @property
    def stop_touched(self) -> Optional[bool]:
        if self.stop_price is None:
            return None

        if self.direction == "bullish":
            return self.lowest_price <= self.stop_price

        return self.highest_price >= self.stop_price

    @property
    def target_progress_percent(self) -> float:
        required_move = abs(self.target_price - self.entry_price)

        if required_move == 0:
            return 100.0

        favorable_move = abs(self.favorable_price - self.entry_price)

        progress = favorable_move / required_move * 100

        return round(min(max(progress, 0.0), 100.0), 2)

    @property
    def age_hours(self) -> Optional[float]:
        if not self.created_at:
            return None

        try:
            created = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )

            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            hours = (now - created).total_seconds() / 3600

            return round(max(hours, 0.0), 2)

        except (TypeError, ValueError):
            return None

    @property
    def state(self) -> str:
        target = self.target_touched
        stop = self.stop_touched

        if target and stop:
            return "TARGET_AND_STOP_TOUCHED"

        if target:
            return "TARGET_TOUCHED"

        if stop:
            return "STOP_TOUCHED"

        return "OPEN"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)

        data.update({
            "state": self.state,
            "age_hours": self.age_hours,
            "current_move_percent": self.current_move_percent,
            "favorable_price": self.favorable_price,
            "adverse_price": self.adverse_price,
            "mfe_percent": self.mfe_percent,
            "mae_percent": self.mae_percent,
            "target_touched": self.target_touched,
            "stop_touched": self.stop_touched,
            "target_progress_percent": self.target_progress_percent,
        })

        return data
