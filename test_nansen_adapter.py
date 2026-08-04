import unittest

from app.intelligence.nansen.adapter import (
    NansenIntelligenceAdapter,
)


class TestNansenIntelligenceAdapter(unittest.TestCase):

    def test_maps_nansen_payload_to_observation(self):

        payload = {
            "token_symbol": "bnb",
            "chain": "BSC",
            "net_flow_24h_usd": -6400,
            "net_flow_7d_usd": 310380,
            "net_flow_30d_usd": 403325,
            "trader_count": 139,
            "market_cap_usd": 78_700_000_000,
        }

        observation = (
            NansenIntelligenceAdapter()
            .to_smart_money_observation(payload)
        )

        self.assertEqual(
            observation.asset,
            "BNB",
        )

        self.assertEqual(
            observation.chain,
            "bsc",
        )

        self.assertEqual(
            observation.net_flow_7d_usd,
            310380,
        )

        self.assertEqual(
            observation.trader_count,
            139,
        )


if __name__ == "__main__":
    unittest.main()
