import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app.agents.fridge_agent import FridgeAgent, _fallback_parse
from app.schemas import FridgeParseResponse, FridgeParsedItem


class FakeStructuredClient:
    def __init__(self, response):
        self._response = response
        self.enabled = True

    def generate(self, **kwargs):
        return self._response


class FridgeAgentTest(unittest.TestCase):
    def test_fallback_parse_supports_korean_quantities_and_weekend(self):
        response = _fallback_parse("시금치 한 봉지 이번 주말, 새우 200g 내일")

        self.assertEqual(len(response.items), 2)
        self.assertEqual(response.items[0].name, "시금치")
        self.assertEqual(response.items[0].quantity, 1.0)
        self.assertEqual(response.items[0].unit, "봉지")
        self.assertEqual(response.items[1].name, "새우")
        self.assertEqual(response.items[1].quantity, 200.0)
        self.assertEqual(response.items[1].unit, "g")

    def test_fallback_parse_supports_next_weekday(self):
        response = _fallback_parse("우유 두 팩 다음 주 화요일")

        self.assertEqual(len(response.items), 1)
        self.assertEqual(response.items[0].name, "우유")
        self.assertEqual(response.items[0].quantity, 2.0)
        self.assertEqual(response.items[0].unit, "팩")
        self.assertIsNotNone(response.items[0].expiry_date)
        self.assertGreaterEqual(response.items[0].expiry_date, date.today() + timedelta(days=1))

    def test_agent_falls_back_when_llm_response_is_suspicious(self):
        suspicious_response = FridgeParseResponse(
            items=[
                FridgeParsedItem(
                    name="123e4567-e89b-12d3-a456-426614174000",
                    normalized_name="123e4567-e89b-12d3-a456-426614174000",
                    quantity=1.0,
                    unit="개",
                    expiry_date=date.today() - timedelta(days=10),
                )
            ]
        )
        agent = FridgeAgent()
        with patch("app.agents.fridge_agent.structured_client", FakeStructuredClient(suspicious_response)):
            response = agent.parse("시금치 1봉지 내일, 새우 200g 오늘")

        self.assertEqual([item.name for item in response.items], ["시금치", "새우"])
        self.assertEqual(response.items[0].normalized_name, "시금치")
        self.assertEqual(response.items[1].normalized_name, "새우")


if __name__ == "__main__":
    unittest.main()
