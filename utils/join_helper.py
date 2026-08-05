"""
Join Helper Utility
Joins relational Olist tables by claimed_order_id.
"""

from typing import Dict, Any, List
import pandas as pd
from utils.csv_loader import OlistCSVLoader


class OlistJoinHelper:
    def __init__(self, loader: OlistCSVLoader):
        self.loader = loader

    def fetch_order_details(self, order_id: str) -> Dict[str, Any]:
        """Query order, items, and payments for a given order_id."""
        df_orders = self.loader.get_orders()
        df_items = self.loader.get_order_items()
        df_payments = self.loader.get_order_payments()

        order_rows = df_orders[df_orders["order_id"] == order_id]
        item_rows = df_items[df_items["order_id"] == order_id]
        payment_rows = df_payments[df_payments["order_id"] == order_id]

        return {
            "order": order_rows.to_dict(orient="records"),
            "items": item_rows.to_dict(orient="records"),
            "payments": payment_rows.to_dict(orient="records"),
        }
