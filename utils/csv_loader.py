"""
CSV Loader Utility for Olist Dataset
Loads pandas DataFrames offline without DB.
"""

from typing import Dict
import pandas as pd
from core.config import DATA_PATH


class OlistCSVLoader:
    def __init__(self, data_dir=DATA_PATH):
        self.data_dir = data_dir
        self._cache: Dict[str, pd.DataFrame] = {}

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Lazy load and cache CSV tables."""
        if table_name not in self._cache:
            file_path = self.data_dir / f"{table_name}.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"CSV dataset file not found: {file_path}")
            self._cache[table_name] = pd.read_csv(file_path, dtype=str)
        return self._cache[table_name]

    def get_orders(self) -> pd.DataFrame:
        return self.load_table("olist_orders_dataset")

    def get_order_items(self) -> pd.DataFrame:
        return self.load_table("olist_order_items_dataset")

    def get_order_payments(self) -> pd.DataFrame:
        return self.load_table("olist_order_payments_dataset")

    def get_order_reviews(self) -> pd.DataFrame:
        return self.load_table("olist_order_reviews_dataset")

    def get_sellers(self) -> pd.DataFrame:
        return self.load_table("olist_sellers_dataset")
