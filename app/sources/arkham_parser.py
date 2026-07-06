from app.models.event import MarketEvent
from app.engine.normalizer import normalize_entity, normalize_asset


def parse_arkham_payload(payload: dict) -> MarketEvent:
    asset = (
        payload.get("asset")
        or payload.get("token")
        or payload.get("symbol")
    )

    amount_usd = (
        payload.get("amount_usd")
        or payload.get("usd_value")
        or payload.get("valueUsd")
        or payload.get("value_usd")
        or 0
    )

    from_entity = (
        payload.get("from_entity")
        or payload.get("from")
        or payload.get("fromLabel")
        or payload.get("from_name")
    )

    to_entity = (
        payload.get("to_entity")
        or payload.get("to")
        or payload.get("toLabel")
        or payload.get("to_name")
    )

    return MarketEvent(
        source="Arkham",
        event_type=payload.get("event_type", "transfer"),
        asset=normalize_asset(asset),
        amount_usd=float(amount_usd or 0),
        from_entity=normalize_entity(from_entity),
        to_entity=normalize_entity(to_entity),
        network=payload.get("network") or payload.get("chain"),
        tx_hash=payload.get("tx_hash") or payload.get("txHash"),
        raw=payload,
    )
