import unittest

from app.intelligence.nansen.client import (
    NansenClient,
)


class FakeNansenClient(NansenClient):

    def get_smart_money_netflow(
        self,
        chain: str,
    ):
        return [
            {
                "token_symbol": "BNB",
                "chain": chain,
                "net_flow_7d_usd": 310380,
            }
        ]


class TestNansenClient(unittest.TestCase):

    def test_client_boundary_returns_payload(self):

        client = FakeNansenClient()

        result = client.get_smart_money_netflow(
            "bsc",
        )

        self.assertEqual(
            result[0]["token_symbol"],
            "BNB",
        )

        self.assertEqual(
            result[0]["chain"],
            "bsc",
        )


if __name__ == "__main__":
    unittest.main()
