import unittest
from datetime import datetime, timezone

from app.intelligence.nansen.models import (
    SmartMoneyObservation,
)


class TestSmartMoneyObservation(unittest.TestCase):

    def build_observation(self):
        return SmartMoneyObservation(
            asset="bnb",
            chain="BSC",
            net_flow_24h_usd=-6400,
            net_flow_7d_usd=310380,
            net_flow_30d_usd=403325,
            trader_count=139,
            market_cap_usd=78_700_000_000,
            observed_at=datetime(
                2026,
                8,
                4,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )

    def test_asset_and_chain_are_normalized(self):
        obs = self.build_observation()

        self.assertEqual(
            obs.asset,
            "BNB",
        )

        self.assertEqual(
            obs.chain,
            "bsc",
        )

    def test_is_immutable(self):
        obs = self.build_observation()

        with self.assertRaises(Exception):
            obs.asset = "ETH"

    def test_negative_net_flow_is_allowed(self):
        obs = self.build_observation()

        self.assertEqual(
            obs.net_flow_24h_usd,
            -6400,
        )

    def test_market_cap_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            SmartMoneyObservation(
                asset="BNB",
                chain="bsc",
                net_flow_24h_usd=0,
                net_flow_7d_usd=0,
                net_flow_30d_usd=0,
                trader_count=1,
                market_cap_usd=-1,
                observed_at=datetime.now(timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
