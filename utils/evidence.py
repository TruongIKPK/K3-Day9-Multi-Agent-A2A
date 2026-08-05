"""
Evidence Generator Utility
Generates deterministic evidence IDs based on dataset specifications with issue filtering.
"""

from typing import List, Optional


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
    def filter_relevant_evidence(
        order_id: str,
        item_ids: List[str],
        seller_ids: List[str],
        payment_ids: List[str],
        primary_issue: str,
        cause_code: str,
        responsible_party_id: Optional[str] = None
    ) -> List[str]:
        """Filters evidence IDs to match exact dispute requirements and avoid false positives."""
        evidences = [EvidenceBuilder.build_order_evidence(order_id)]

        # Add item evidence if applicable
        if primary_issue not in ("canceled_order_paid", "unavailable_order_paid"):
            for iid in item_ids[:5]:
                parts = iid.split(":")
                seq = parts[-1]
                evidences.append(EvidenceBuilder.build_item_evidence(order_id, seq))

        # Add payment evidence
        for pid in payment_ids[:5]:
            parts = pid.split(":")
            seq = parts[-1]
            evidences.append(EvidenceBuilder.build_payment_evidence(order_id, seq))

        # Add seller evidence ONLY if seller is responsible
        if primary_issue == "late_delivery_seller" and responsible_party_id and responsible_party_id != "UNKNOWN_SELLER":
            evidences.append(EvidenceBuilder.build_seller_evidence(responsible_party_id))

        # Add policy evidence
        evidences.append(EvidenceBuilder.build_policy_evidence(cause_code))

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for item in evidences:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped[:10]

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
