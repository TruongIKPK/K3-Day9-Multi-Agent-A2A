"""Unit tests for PolicyAgent rules engine"""

import unittest
from core.models import OrderContext, PaymentContext, DeliveryContext
from agents.policy_agent import PolicyAgent


class TestPolicyAgent(unittest.TestCase):
    def test_canceled_order_paid_policy(self):
        agent = PolicyAgent()
        order_ctx = OrderContext(
            order_id="ord_1",
            customer_id="cust_1",
            order_status="canceled",
            item_total_brl=100.0,
            freight_total_brl=15.0
        )
        payment_ctx = PaymentContext(
            order_id="ord_1",
            payment_total_brl=115.0,
            payment_count=1
        )
        delivery_ctx = DeliveryContext(order_id="ord_1")

        decision = agent.run_with_retry((order_ctx, payment_ctx, delivery_ctx))
        self.assertEqual(decision.primary_issue, "canceled_order_paid")
        self.assertEqual(decision.recommended_refund_brl, 115.0)
        self.assertEqual(decision.case_status, "action_required")


if __name__ == "__main__":
    unittest.main()
