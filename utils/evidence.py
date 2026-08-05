"""
Evidence Generator Utility
Generates deterministic evidence IDs based on dataset specifications.
"""

from typing import List


class EvidenceBuilder:
    @staticmethod
    def build_order_evidence(order_id: str) -> str:
        return f"order:{order_id}"

    @staticmethod
    def build_item_evidence(order_id: str, item_id: str) -> str:
        return f"item:{order_id}:{item_id}"

    @staticmethod
    def build_payment_evidence(order_id: str, payment_seq: str) -> str:
        return f"payment:{order_id}:{payment_seq}"

    @staticmethod
    def build_seller_evidence(seller_id: str) -> str:
        return f"seller:{seller_id}"

    @staticmethod
    def build_policy_evidence(cause_code: str) -> str:
        return f"policy:{cause_code}"

    @staticmethod
    def sanitize_evidence_list(evidence_ids: List[str], max_limit: int = 10) -> List[str]:
        """Deduplicates while preserving order and truncates to max limit."""
        seen = set()
        deduped = []
        for eid in evidence_ids:
            if eid not in seen:
                seen.add(eid)
                deduped.append(eid)
        return deduped[:max_limit]
