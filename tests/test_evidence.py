"""Unit tests for EvidenceBuilder utility"""

import unittest
from utils.evidence import EvidenceBuilder


class TestEvidence(unittest.TestCase):
    def test_evidence_syntax(self):
        self.assertEqual(EvidenceBuilder.build_order_evidence("ord1"), "order:ord1")
        self.assertEqual(EvidenceBuilder.build_item_evidence("ord1", "1"), "item:ord1:1")
        self.assertEqual(EvidenceBuilder.build_payment_evidence("ord1", "1"), "payment:ord1:1")
        self.assertEqual(EvidenceBuilder.build_seller_evidence("sel1"), "seller:sel1")
        self.assertEqual(EvidenceBuilder.build_policy_evidence("RC_1"), "policy:RC_1")

    def test_sanitize_evidence(self):
        evs = ["order:1", "item:1:1", "order:1", "seller:1"]
        san = EvidenceBuilder.sanitize_evidence_list(evs, max_limit=10)
        self.assertEqual(len(san), 3)
        self.assertEqual(san, ["order:1", "item:1:1", "seller:1"])


if __name__ == "__main__":
    unittest.main()
