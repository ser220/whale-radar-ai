from typing import Optional

from app.models.event import MarketEvent
from app.sources.arkham import ArkhamAdapter


class SourceManager:
    def __init__(self):
        self.adapters = {}

    def register(self, adapter):
        self.adapters[adapter.source_name] = adapter

    def parse(self, source_name: str, payload: dict) -> Optional[MarketEvent]:
        adapter = self.adapters.get(source_name)

        if not adapter:
            return None

        return adapter.parse(payload)


source_manager = SourceManager()
source_manager.register(ArkhamAdapter())
