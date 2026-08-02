from app.intelligence.early_bird.exchange_execution_service import (
    ExchangeExecutionService,
)


class DummyAdapter:

    def __init__(self):
        self.called = False


    def submit(self, request):

        self.called = True

        return "SUBMITTED"



def test_execution_service_routes_request():

    adapter = DummyAdapter()

    service = ExchangeExecutionService()

    service.registry.register(
        "OKX",
        adapter,
    )

    request = type(
        "Request",
        (),
        {
            "exchange": "OKX"
        }
    )()

    result = service.execute(
        request
    )

    assert result == "SUBMITTED"
    assert adapter.called is True



def test_unknown_exchange():

    service = ExchangeExecutionService()

    request = type(
        "Request",
        (),
        {
            "exchange": "UNKNOWN"
        }
    )()

    try:

        service.execute(
            request
        )

    except ValueError as exc:
        assert "exchange" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
