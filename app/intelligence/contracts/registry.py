"""A small in-memory registry for future expert implementations."""

from typing import Any, Dict, Tuple

from app.intelligence.contracts._validation import required_string


class ExpertRegistry:
    """Register expert objects by their public ``expert_name`` attribute."""

    def __init__(self) -> None:
        self._experts: Dict[str, Any] = {}

    def register(self, expert: Any, *, replace: bool = False) -> None:
        expert_name = required_string(getattr(expert, "expert_name", None), "expert.expert_name")
        if expert_name in self._experts and not replace:
            raise ValueError(f"expert already registered: {expert_name}")
        self._experts[expert_name] = expert

    def get(self, expert_name: str) -> Any:
        return self._experts[expert_name]

    def get_all(self) -> Tuple[Any, ...]:
        return tuple(self._experts.values())

    def contains(self, expert_name: str) -> bool:
        return expert_name in self._experts
