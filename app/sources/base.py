from typing import Optional
from app.models.event import MarketEvent


class SourceAdapter:
    source_name = "base"

    def parse(self, payload: dict) -> Optional[MarketEvent]:
        raise NotImplementedError
