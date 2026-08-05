"""Unit tests for Verifier Agent and OutputValidator"""

import pytest
from core.models import FinalOutput, Assessment, AffectedEntities, RootCauseAnalysis, FinancialResolution
from utils.validation import OutputValidator


def test_output_validator_bounds():
    out = FinalOutput(
        case_id="EC_001",
        assessment=Assessment(primary_issue="canceled_order_paid", case_status="action_required", confidence=0.95),
        affected_entities=AffectedEntities(order_ids=["ord_1"], item_ids=["ord_1:1"], seller_ids=["sel_1"], payment_ids=["ord_1:1"]),
        root_cause_analysis=RootCauseAnalysis(ranked_causes=[], responsible_parties=[]),
        evidence_ids=["order:ord_1"],
        financial_resolution=FinancialResolution(item_total_brl=100.0, freight_total_brl=15.0, payment_total_brl=115.0, recommended_refund_brl=115.0),
        resolution_actions=["issue_full_refund"]
    )
    v_res = OutputValidator.validate(out)
    assert v_res.is_valid is True
