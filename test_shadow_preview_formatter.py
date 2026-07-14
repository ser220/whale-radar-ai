import unittest

from app.telegram.analyze_formatter import (
    format_analyze_result,
    format_shadow_intelligence,
    is_shadow_preview_enabled,
)


def analyze_result(**overrides):
    result = {
        "asset": "BTC",
        "trade": {
            "asset": "BTC",
            "status": "WATCH",
            "bias": "NEUTRAL",
            "trade_readiness": 50,
            "confidence": 60,
            "institutional_score": 70,
            "hypothesis_stability": 80,
            "market_velocity": "NORMAL",
            "eta": "15 min",
            "risk": "LOW",
            "action": "Wait for confirmation.",
            "reasons": [],
            "missing_confirmations": [],
        },
        "snapshot_quality": {"overall": 90},
        "arkham_event_found": False,
        "change": {"available": False},
    }
    result.update(overrides)
    return result


class ShadowPreviewFormatterTests(unittest.TestCase):
    def test_shadow_unavailable(self):
        text = format_shadow_intelligence(None)

        self.assertIn("🧠 <b>Shadow Intelligence</b>", text)
        self.assertIn("Unavailable", text)
        self.assertIn("━━━━━━━━━━━━━━━━━━", text)
        self.assertNotIn("Experimental", text)

    def test_single_expert(self):
        text = format_shadow_intelligence(
            {
                "opinions": {
                    "legacy_intelligence": {
                        "direction": "BULLISH",
                        "confidence": 78.25,
                    }
                }
            }
        )

        self.assertIn("<b>Legacy Expert</b>", text)
        self.assertIn("Direction: BULLISH", text)
        self.assertIn("Confidence: 78.2%", text)
        self.assertNotIn("<b>Trend Expert</b>", text)
        self.assertIn("<b>Agreement:</b> Unavailable", text)
        self.assertIn("<b>Shadow Status:</b> Experimental", text)

    def test_two_experts(self):
        text = format_shadow_intelligence(
            {
                "opinions": {
                    "legacy_intelligence": {
                        "direction": "BULLISH",
                        "confidence": 80,
                    },
                    "trend_expert": {
                        "direction": "NEUTRAL",
                        "confidence": 65,
                    },
                },
                "agreement": "MEDIUM",
            }
        )

        self.assertIn("<b>Legacy Expert</b>", text)
        self.assertIn("<b>Trend Expert</b>", text)
        self.assertEqual(text.count("Direction:"), 2)
        self.assertEqual(text.count("Confidence:"), 2)

    def test_agreement_formatting(self):
        opinions = {
            "legacy_intelligence": {
                "direction": "NEUTRAL",
                "confidence": 50,
            }
        }

        for supplied, expected in (
            ("HIGH", "High"),
            ("medium", "Medium"),
            ("Low", "Low"),
            ("unsupported", "Unavailable"),
        ):
            with self.subTest(supplied=supplied):
                text = format_shadow_intelligence(
                    {
                        "opinions": opinions,
                        "agreement": supplied,
                    }
                )
                self.assertIn(
                    "<b>Agreement:</b> {0}".format(expected),
                    text,
                )

    def test_decision_like_shadow_fields_are_ignored(self):
        text = format_shadow_intelligence(
            {
                "opinions": {
                    "trend_expert": {
                        "direction": "BUY",
                        "confidence": 101,
                        "recommendation": "BUY",
                        "tp": 100,
                        "sl": 90,
                    }
                },
                "action": "SELL",
            }
        )

        self.assertIn("Direction: Unavailable", text)
        self.assertIn("Confidence: Unavailable", text)
        for forbidden in ("BUY", "SELL", "recommendation", "tp", "sl"):
            self.assertNotIn(forbidden, text)

    def test_feature_disabled_keeps_legacy_formatting_identical(self):
        result = analyze_result(
            shadow_intelligence={
                "opinions": {
                    "legacy_intelligence": {
                        "direction": "BULLISH",
                        "confidence": 80,
                    }
                }
            }
        )

        existing = format_analyze_result(result)
        explicitly_disabled = format_analyze_result(
            result,
            shadow_enabled=False,
        )

        self.assertEqual(explicitly_disabled, existing)
        self.assertNotIn("Shadow Intelligence", existing)
        self.assertTrue(existing.endswith("No automatic execution."))

    def test_feature_enabled_appends_preview(self):
        result = analyze_result(
            shadow_intelligence={
                "opinions": {
                    "legacy_intelligence": {
                        "direction": "BEARISH",
                        "confidence": 72,
                    },
                    "trend_expert": {
                        "direction": "BEARISH",
                        "confidence": 81,
                    },
                },
                "agreement": "HIGH",
            }
        )

        text = format_analyze_result(
            result,
            shadow_enabled=True,
        )

        self.assertIn("Mode: Alpha decision support", text)
        self.assertIn("🧠 <b>Shadow Intelligence</b>", text)
        self.assertIn("<b>Agreement:</b> High", text)

    def test_enabled_without_payload_displays_unavailable(self):
        text = format_analyze_result(
            analyze_result(),
            shadow_enabled=True,
        )

        self.assertIn("🧠 <b>Shadow Intelligence</b>\nUnavailable", text)

    def test_feature_flag_is_explicit_opt_in(self):
        for value in ("1", "true", "YES", "on", "enabled", True):
            with self.subTest(value=value):
                self.assertTrue(is_shadow_preview_enabled(value))

        for value in (None, "", "0", "false", "off", False, object()):
            with self.subTest(value=value):
                self.assertFalse(is_shadow_preview_enabled(value))


if __name__ == "__main__":
    unittest.main()
