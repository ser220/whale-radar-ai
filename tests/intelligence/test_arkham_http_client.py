from app.intelligence.arkham.config import (
    ArkhamConfig,
)

from app.intelligence.arkham.http_client import (
    ArkhamHttpClient,
)


class MockResponse:

    def json(self):
        return [
            {
                "id": "api-event-001",
                "amount_usd": 20000000,
            }
        ]


class MockTransport:

    def __init__(self):
        self.called = False
        self.headers = None

    def get(
        self,
        url,
        headers,
        timeout,
    ):
        self.called = True
        self.headers = headers
        return MockResponse()


def test_http_client_returns_api_payload():

    transport = MockTransport()

    client = ArkhamHttpClient(
        config=ArkhamConfig(
            api_key="test-key"
        ),
        transport=transport,
    )

    events = client.fetch_whale_events()

    assert transport.called is True

    assert (
        transport.headers["Authorization"]
        == "Bearer test-key"
    )

    assert (
        events[0]["id"]
        == "api-event-001"
    )


def test_missing_api_key_rejected():

    transport = MockTransport()

    client = ArkhamHttpClient(
        config=ArkhamConfig(),
        transport=transport,
    )

    try:
        client.fetch_whale_events()

    except ValueError:
        assert True

    else:
        raise AssertionError(
            "Expected missing API key error"
        )
