"""
Delivery Agent
Responsible for comparing delivery dates against estimated dates and seller handoff limits.
"""

from agents.base_agent import BaseAgent
from core.models import OrderContext, DeliveryContext


class DeliveryAgent(BaseAgent):
    def __init__(self, tracer=None):
        super().__init__("DeliveryAgent", tracer=tracer)

    def execute(self, order_ctx: OrderContext) -> DeliveryContext:
        delivered_cust = order_ctx.delivered_customer_date
        estimated = order_ctx.estimated_delivery_date
        delivered_carrier = order_ctx.delivered_carrier_date

        def is_valid_date(val):
            return isinstance(val, str) and bool(val.strip()) and val != "nan"

        is_delivered_after_estimate = False
        if is_valid_date(delivered_cust) and is_valid_date(estimated) and str(delivered_cust) > str(estimated):
            is_delivered_after_estimate = True

        is_carrier_received_after_limit = order_ctx.is_seller_late

        return DeliveryContext(
            order_id=order_ctx.order_id,
            delivered_carrier_date=delivered_carrier,
            delivered_customer_date=delivered_cust,
            estimated_delivery_date=estimated,
            is_delivered_after_estimate=is_delivered_after_estimate,
            is_carrier_received_after_limit=is_carrier_received_after_limit,
            evidence_ids=order_ctx.evidence_ids
        )
