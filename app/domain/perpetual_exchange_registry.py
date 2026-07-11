from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple


VALID_LAYERS = {
    "execution",
    "hot_backup",
    "intelligence",
}


@dataclass(frozen=True)
class PerpetualExchange:
    key: str
    name: str
    layer: str
    initial_weight: float

    enabled: bool = True
    execution_priority: int = 999
    aliases: Tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        key = str(
            self.key or ""
        ).strip().lower()

        name = str(
            self.name or ""
        ).strip()

        layer = str(
            self.layer or ""
        ).strip().lower()

        if not key:
            raise ValueError(
                "Exchange key cannot be empty."
            )

        if not name:
            raise ValueError(
                "Exchange name cannot be empty."
            )

        if layer not in VALID_LAYERS:
            raise ValueError(
                f"Unsupported exchange layer: {layer}"
            )

        weight = float(
            self.initial_weight
        )

        if not 0.0 <= weight <= 1.0:
            raise ValueError(
                "initial_weight must be between 0 and 1."
            )

        object.__setattr__(
            self,
            "key",
            key,
        )

        object.__setattr__(
            self,
            "name",
            name,
        )

        object.__setattr__(
            self,
            "layer",
            layer,
        )

        object.__setattr__(
            self,
            "initial_weight",
            weight,
        )

        object.__setattr__(
            self,
            "execution_priority",
            max(
                int(self.execution_priority),
                1,
            ),
        )

        normalized_aliases = tuple(
            sorted({
                str(alias)
                .strip()
                .lower()
                for alias in self.aliases
                if str(alias).strip()
            })
        )

        object.__setattr__(
            self,
            "aliases",
            normalized_aliases,
        )

    @property
    def is_execution(self) -> bool:
        return self.layer == "execution"

    @property
    def is_hot_backup(self) -> bool:
        return self.layer == "hot_backup"

    @property
    def is_intelligence(self) -> bool:
        return self.layer == "intelligence"

    def to_dict(self) -> Dict:
        return asdict(self)


EXCHANGES: Dict[str, PerpetualExchange] = {
    "okx": PerpetualExchange(
        key="okx",
        name="OKX",
        layer="execution",
        initial_weight=1.00,
        execution_priority=1,
        aliases=(
            "okex",
        ),
        notes=(
            "Primary perpetual execution market."
        ),
    ),

    "binance": PerpetualExchange(
        key="binance",
        name="Binance",
        layer="execution",
        initial_weight=1.00,
        execution_priority=2,
        aliases=(
            "binance-futures",
            "binance-usdm",
        ),
        notes=(
            "Primary execution and broad market reference."
        ),
    ),

    "gate": PerpetualExchange(
        key="gate",
        name="Gate.io",
        layer="execution",
        initial_weight=0.95,
        execution_priority=3,
        aliases=(
            "gateio",
            "gate.io",
        ),
        notes=(
            "Primary altcoin perpetual execution market."
        ),
    ),

    "bybit": PerpetualExchange(
        key="bybit",
        name="Bybit",
        layer="hot_backup",
        initial_weight=0.90,
        execution_priority=4,
        aliases=(),
        notes=(
            "Hot standby when an execution source is unavailable."
        ),
    ),

    "bitget": PerpetualExchange(
        key="bitget",
        name="Bitget",
        layer="intelligence",
        initial_weight=0.85,
        aliases=(),
        notes=(
            "Large derivatives-market confirmation source."
        ),
    ),

    "hyperliquid": PerpetualExchange(
        key="hyperliquid",
        name="Hyperliquid",
        layer="intelligence",
        initial_weight=0.85,
        aliases=(
            "hl",
        ),
        notes=(
            "Independent on-chain perpetual confirmation source."
        ),
    ),

    "deribit": PerpetualExchange(
        key="deribit",
        name="Deribit",
        layer="intelligence",
        initial_weight=0.80,
        aliases=(),
        notes=(
            "Institutional derivatives and options context."
        ),
    ),

    "coinbase": PerpetualExchange(
        key="coinbase",
        name="Coinbase",
        layer="intelligence",
        initial_weight=0.75,
        aliases=(
            "coinbase-intl",
            "coinbase-international",
        ),
        notes=(
            "Regulated and institutional market confirmation."
        ),
    ),

    "kraken": PerpetualExchange(
        key="kraken",
        name="Kraken",
        layer="intelligence",
        initial_weight=0.75,
        aliases=(
            "kraken-futures",
        ),
        notes=(
            "Regulated derivatives-market confirmation."
        ),
    ),
}


class PerpetualExchangeRegistry:
    """
    Central registry for perpetual-market data sources.

    Initial weights are static bootstrap values.
    They will later be replaced or adjusted by the
    Exchange Reliability Engine.
    """

    def all(
        self,
        enabled_only: bool = True,
    ) -> List[PerpetualExchange]:
        exchanges = list(
            EXCHANGES.values()
        )

        if enabled_only:
            exchanges = [
                exchange
                for exchange in exchanges
                if exchange.enabled
            ]

        return sorted(
            exchanges,
            key=lambda exchange: (
                self._layer_priority(
                    exchange.layer
                ),
                exchange.execution_priority,
                exchange.name,
            ),
        )

    def get(
        self,
        value: str,
    ) -> Optional[PerpetualExchange]:
        normalized = str(
            value or ""
        ).strip().lower()

        if not normalized:
            return None

        if normalized in EXCHANGES:
            return EXCHANGES[
                normalized
            ]

        for exchange in EXCHANGES.values():
            if normalized in exchange.aliases:
                return exchange

        return None

    def by_layer(
        self,
        layer: str,
        enabled_only: bool = True,
    ) -> List[PerpetualExchange]:
        normalized = str(
            layer or ""
        ).strip().lower()

        if normalized not in VALID_LAYERS:
            raise ValueError(
                f"Unsupported exchange layer: {normalized}"
            )

        return [
            exchange
            for exchange in self.all(
                enabled_only=enabled_only
            )
            if exchange.layer == normalized
        ]

    def execution(
        self,
    ) -> List[PerpetualExchange]:
        return self.by_layer(
            "execution"
        )

    def hot_backup(
        self,
    ) -> List[PerpetualExchange]:
        return self.by_layer(
            "hot_backup"
        )

    def intelligence(
        self,
    ) -> List[PerpetualExchange]:
        return self.by_layer(
            "intelligence"
        )

    def active_execution_set(
        self,
        available_keys: List[str],
        required_count: int = 3,
    ) -> List[PerpetualExchange]:
        """
        Returns available execution markets.

        If fewer than required_count primary execution
        markets are available, fills missing slots with
        available hot-backup exchanges.
        """
        available = {
            str(key)
            .strip()
            .lower()
            for key in available_keys
        }

        selected = [
            exchange
            for exchange in self.execution()
            if exchange.key in available
        ]

        missing = max(
            int(required_count)
            - len(selected),
            0,
        )

        if missing:
            backups = [
                exchange
                for exchange in self.hot_backup()
                if exchange.key in available
            ]

            selected.extend(
                backups[:missing]
            )

        return selected

    def weights(
        self,
        enabled_only: bool = True,
    ) -> Dict[str, float]:
        return {
            exchange.key: (
                exchange.initial_weight
            )
            for exchange in self.all(
                enabled_only=enabled_only
            )
        }

    def keys(
        self,
        enabled_only: bool = True,
    ) -> List[str]:
        return [
            exchange.key
            for exchange in self.all(
                enabled_only=enabled_only
            )
        ]

    @staticmethod
    def _layer_priority(
        layer: str,
    ) -> int:
        return {
            "execution": 1,
            "hot_backup": 2,
            "intelligence": 3,
        }.get(
            layer,
            99,
        )


def format_perpetual_exchange_registry(
    registry: Optional[
        PerpetualExchangeRegistry
    ] = None,
) -> str:
    registry = (
        registry
        or PerpetualExchangeRegistry()
    )

    lines = [
        "🌐 <b>Perpetual Exchange Network</b>",
        "",
        "<b>Execution Markets</b>",
    ]

    for exchange in registry.execution():
        lines.append(
            f"• {exchange.name} "
            f"— weight {exchange.initial_weight:.2f}"
        )

    lines.extend([
        "",
        "<b>Hot Backup</b>",
    ])

    for exchange in registry.hot_backup():
        lines.append(
            f"• {exchange.name} "
            f"— weight {exchange.initial_weight:.2f}"
        )

    lines.extend([
        "",
        "<b>Market Intelligence</b>",
    ])

    for exchange in registry.intelligence():
        lines.append(
            f"• {exchange.name} "
            f"— weight {exchange.initial_weight:.2f}"
        )

    lines.extend([
        "",
        (
            "Weights: bootstrap values only"
        ),
        (
            "Future control: Exchange Reliability Engine"
        ),
    ])

    return "\n".join(
        lines
    )
