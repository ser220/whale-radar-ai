from inspect import signature
from typing import get_type_hints, Optional

from app.decision.query import DecisionQueryService
from app.decision.repository import DecisionRepository


def test_decision_query_service_constructor_type_hints_resolve(
) -> None:
    type_hints = get_type_hints(
        DecisionQueryService.__init__
    )
    parameters = signature(
        DecisionQueryService.__init__
    ).parameters

    assert type_hints["repository"] == Optional[
        DecisionRepository
    ]
    assert parameters["repository"].default is None
    assert type_hints["return"] is type(None)
