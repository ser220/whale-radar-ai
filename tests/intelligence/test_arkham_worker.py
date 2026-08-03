from datetime import datetime, timezone

from app.intelligence.arkham.worker import (
    ArkhamWorker,
)

from app.intelligence.arkham.collector import (
    ArkhamCollector,
)

from app.intelligence.arkham.store import (
    ArkhamEventStore,
)


class MockCollector:

    def __init__(self):
        self.called = False

    def collect(self):
        self.called = True
        return ["event"]


def test_worker_runs_collection():

    collector = MockCollector()

    worker = ArkhamWorker(
        collector=collector,
    )

    result = worker.run_once()

    assert collector.called is True

    assert result == [
        "event"
    ]
