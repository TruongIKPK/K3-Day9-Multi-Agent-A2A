"""Unit tests for PolicyAgent rules engine"""

import pytest
from core.models import OrderContext, PaymentContext, DeliveryContext
from agents.policy_agent import PolicyAgent


def test_canceled_order_paid_policy():
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
    assert decision.primary_issue == "canceled_order_paid"
    assert decision.recommended_refund_brl == 115.0
    assert decision.case_status == "action_required"
