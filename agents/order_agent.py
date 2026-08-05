"""
Order Agent
Responsible for querying order details, items, sellers, and handoff deadlines.
Does NOT execute business rules or payment math.
"""

import pandas as pd
from agents.base_agent import BaseAgent
from core.models import CaseInput, OrderContext
from utils.csv_loader import OlistCSVLoader
from utils.join_helper import OlistJoinHelper
from utils.evidence import EvidenceBuilder


class OrderAgent(BaseAgent):
    def __init__(self, loader: OlistCSVLoader, tracer=None):
        super().__init__("OrderAgent", tracer=tracer)
        self.join_helper = OlistJoinHelper(loader)

    def execute(self, case_input: CaseInput) -> OrderContext:
        order_id = case_input.customer_request.claimed_order_id
        details = self.join_helper.fetch_order_details(order_id)

        orders = details["order"]
        if not orders:
            raise ValueError(f"Order ID {order_id} not found in dataset.")

        order_row = orders[0]
        items = details["items"]

        item_ids = []
        seller_ids = []
        shipping_limits = []
        item_prices = []
        freights = []
        evidence_ids = [EvidenceBuilder.build_order_evidence(order_id)]

        item_total = 0.0
        freight_total = 0.0
        is_seller_late = False

        def clean_str(val):
            if val is None or pd.isna(val) or not isinstance(val, str) or val == "nan":
                return None
            return val

        delivered_carrier = clean_str(order_row.get("order_delivered_carrier_date"))

        for item in items:
            item_seq = item["order_item_id"]
            seller_id = item["seller_id"]
            ship_limit = clean_str(item.get("shipping_limit_date"))
            price = float(item["price"])
            freight = float(item["freight_value"])

            item_key = f"{order_id}:{item_seq}"
            item_ids.append(item_key)
            seller_ids.append(seller_id)
            if ship_limit:
                shipping_limits.append(ship_limit)
            item_prices.append(price)
            freights.append(freight)

            item_total += price
            freight_total += freight

            evidence_ids.append(EvidenceBuilder.build_item_evidence(order_id, item_seq))
            evidence_ids.append(EvidenceBuilder.build_seller_evidence(seller_id))

            if delivered_carrier and ship_limit and delivered_carrier > ship_limit:
                is_seller_late = True

        return OrderContext(
            order_id=order_id,
            customer_id=order_row["customer_id"],
            order_status=order_row["order_status"],
            purchase_timestamp=clean_str(order_row.get("order_purchase_timestamp")),
            approved_at=clean_str(order_row.get("order_approved_at")),
            delivered_carrier_date=delivered_carrier,
            delivered_customer_date=clean_str(order_row.get("order_delivered_customer_date")),
            estimated_delivery_date=clean_str(order_row.get("order_estimated_delivery_date")),
            item_ids=item_ids,
            seller_ids=list(set(seller_ids)),
            shipping_limit_dates=shipping_limits,
            item_prices=item_prices,
            freight_values=freights,
            item_total_brl=round(item_total, 2),
            freight_total_brl=round(freight_total, 2),
            is_seller_late=is_seller_late,
            evidence_ids=EvidenceBuilder.sanitize_evidence_list(evidence_ids)
        )
