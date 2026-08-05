"""Unit tests for domain extraction agents"""

import unittest
from core.models import CaseInput, CustomerRequest
from utils.csv_loader import OlistCSVLoader
from agents.order_agent import OrderAgent


class TestDomainAgents(unittest.TestCase):
    def test_order_agent_execution(self):
        loader = OlistCSVLoader()
        agent = OrderAgent(loader)
        case_in = CaseInput(
            case_id="EC_001",
            opened_at="2018-10-18T00:00:00-03:00",
            customer_request=CustomerRequest(
                language="vi",
                message="Test message",
                claimed_order_id="e2a03ccf5ea816036608b2d8c3ab8e60"
            )
        )
        res = agent.run_with_retry(case_in)
        self.assertEqual(res.order_id, "e2a03ccf5ea816036608b2d8c3ab8e60")
        self.assertTrue(len(res.evidence_ids) > 0)


if __name__ == "__main__":
    unittest.main()
