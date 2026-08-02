"""Exchange adapter registry."""



class ExchangeAdapterRegistry:
    """
    Registry for exchange execution adapters.

    Maps exchange name to concrete adapter.
    """

    def __init__(self) -> None:

        self._adapters = {}


    def register(
        self,
        exchange: str,
        adapter,
    ) -> None:

        if not isinstance(
            exchange,
            str,
        ):
            raise TypeError(
                "exchange must be string"
            )

        name = exchange.strip().upper()

        if not name:
            raise ValueError(
                "exchange must not be empty"
            )

        if adapter is None:
            raise ValueError(
                "adapter must not be None"
            )

        self._adapters[name] = adapter


    def get(
        self,
        exchange: str,
    ):

        if not isinstance(
            exchange,
            str,
        ):
            raise TypeError(
                "exchange must be string"
            )

        name = exchange.strip().upper()

        if name not in self._adapters:
            raise ValueError(
                f"exchange '{name}' not registered"
            )

        return self._adapters[name]


__all__ = [
    "ExchangeAdapterRegistry",
]
