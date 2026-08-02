"""Bridge from Early Bird market sweep into shadow pipeline."""

from typing import Any, Callable


def process_market_sweep_shadow(
    result: Any,
    *,
    process_fn: Callable[..., Any],
):
    if not callable(process_fn):
        raise TypeError(
            "process_fn must be callable"
        )

    if not hasattr(result, "items"):
        raise TypeError(
            "result must provide items"
        )

    outputs = []

    for item in result.items:
        asset = item.asset

        payload = {
            "quality": item.quality,
        }

        outputs.append(
            process_fn(
                asset=asset,
                payload=payload,
            )
        )

    return outputs


__all__ = [
    "process_market_sweep_shadow",
]
