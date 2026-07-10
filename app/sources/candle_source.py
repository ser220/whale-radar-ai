from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.candle import Candle


class CandleSource(ABC):
    @abstractmethod
    def get_candles(
        self,
        asset: str,
        interval: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Candle]:
        raise NotImplementedError

    @abstractmethod
    def source_name(self) -> str:
        raise NotImplementedError
