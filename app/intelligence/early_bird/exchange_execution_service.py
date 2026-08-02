"""Exchange execution service."""

from app.intelligence.early_bird.exchange_adapter_registry import (
    ExchangeAdapterRegistry,
)


class ExchangeExecutionService:
    """
    Orchestration service between execution request
    and exchange adapter.
    """

    def __init__(
        self,
        registry=None,
    ) -> None:

        self.registry = (
            registry
            if registry is not None
            else ExchangeAdapterRegistry()
        )


    def execute(
        self,
        request,
    ):

        adapter = self.registry.get(
            request.exchange
        )

        return adapter.submit(
            request
        )


__all__ = [
    "ExchangeExecutionService",
]
